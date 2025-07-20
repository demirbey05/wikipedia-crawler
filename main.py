import urllib.request
import urllib.error
import os
import json
from typing import Optional, List, Dict, Tuple, Set
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm


def fetch_html(url: str, timeout: int = 30) -> Optional[str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            html_content = response.read().decode('utf-8')
            return html_content
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except UnicodeDecodeError:
        print("Error: Unable to decode response as UTF-8")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def get_page_title(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, 'html.parser')
    title_element = soup.find('span', class_='mw-page-title-main')
    if title_element:
        return title_element.get_text().strip()
    return None


def parse_article_content(html: str) -> Tuple[List[Dict], List[str]]:
    soup = BeautifulSoup(html, 'html.parser')
    content_div = soup.find('div', class_='mw-content-ltr')
    
    if not content_div:
        return [], []
    
    content_elements = []
    links = []
    
    # Get all direct p children of mw-content-ltr
    p_elements = content_div.find_all('p', recursive=False)
    
    # Get all h1-h6 elements within 2 levels of mw-content-ltr
    h_elements = []
    for level in range(1, 7):
        # Direct children
        h_elements.extend(content_div.find_all(f'h{level}', recursive=False))
        # One level deep
        for child in content_div.children:
            if hasattr(child, 'find_all'):
                h_elements.extend(child.find_all(f'h{level}', recursive=False))
    
    # Combine and sort by document order
    all_elements = p_elements + h_elements
    all_elements.sort(key=lambda x: list(soup.descendants).index(x))
    
    for element in all_elements:
        if element.name.startswith('h'):
            content_elements.append({
                'type': 'heading',
                'level': int(element.name[1]),
                'text': element.get_text().strip()
            })
        elif element.name == 'p':
            # Extract links from this paragraph
            p_links = element.find_all('a')
            for link in p_links:
                href = link.get('href', '')
                if href:
                    links.append(href)
            
            # Get text content (including text around <a> tags)
            text = element.get_text().strip()
            if text:
                content_elements.append({
                    'type': 'paragraph',
                    'text': text
                })
    
    return content_elements, links


class WebCrawler:
    def __init__(self, data_dir: str = "data", max_files: int = 50):
        self.data_dir = data_dir
        self.max_files = max_files
        self.visited_urls: Set[str] = set()
        self.file_count = 0
        self.pending_urls: List[str] = []
        
        os.makedirs(data_dir, exist_ok=True)
        self.load_visited_urls()
    
    def load_visited_urls(self) -> None:
        visited_file = os.path.join(self.data_dir, "visited_urls.json")
        if os.path.exists(visited_file):
            try:
                with open(visited_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.visited_urls = set(data.get('visited', []))
                    self.file_count = data.get('file_count', 0)
            except Exception as e:
                print(f"Error loading visited URLs: {e}")
    
    def save_visited_urls(self) -> None:
        visited_file = os.path.join(self.data_dir, "visited_urls.json")
        try:
            with open(visited_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'visited': list(self.visited_urls),
                    'file_count': self.file_count
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving visited URLs: {e}")
    
    def normalize_url(self, url: str, base_url: str = "") -> Optional[str]:
        if not url:
            return None
        
        if url.startswith('#'):
            return None
        
        if url.startswith('/'):
            if base_url:
                parsed_base = urlparse(base_url)
                return f"{parsed_base.scheme}://{parsed_base.netloc}{url}"
        
        if url.startswith('http'):
            return url
        
        return None
    
    def should_crawl(self, url: str) -> bool:
        if url in self.visited_urls:
            return False
        
        if self.file_count >= self.max_files:
            return False
        
        parsed = urlparse(url)
        if parsed.netloc and 'wikipedia.org' in parsed.netloc:
            return True
        
        return False
    
    def crawl_url(self, url: str) -> bool:
        if not self.should_crawl(url):
            return False
        
        html = fetch_html(url)
        if not html:
            return False
        
        title = get_page_title(html)
        if not title:
            title = f"page_{self.file_count + 1}"
        
        content_elements, links = parse_article_content(html)
        
        self.file_count += 1
        filename = os.path.join(self.data_dir, f"{self.file_count:03d}_{title.replace(' ', '_').replace('/', '_')}.txt")
        write_content_to_file(title, content_elements, links, filename)
        
        self.visited_urls.add(url)
        
        for link in links:
            normalized_link = self.normalize_url(link, url)
            if normalized_link and normalized_link not in self.visited_urls:
                self.pending_urls.append(normalized_link)
        
        self.save_visited_urls()
        return True
    
    def crawl_all(self, start_urls: List[str]) -> None:
        self.pending_urls.extend(start_urls)
        
        with tqdm(total=self.max_files, desc="Crawling pages", unit="pages") as pbar:
            pbar.update(self.file_count)
            
            while self.pending_urls and self.file_count < self.max_files:
                url = self.pending_urls.pop(0)
                if self.crawl_url(url):
                    pbar.update(1)
                    pbar.set_postfix_str(f"Queue: {len(self.pending_urls)}")
        
        print(f"\nCrawling completed. Files created: {self.file_count}")
        if self.file_count >= self.max_files:
            print(f"Reached maximum file limit of {self.max_files}")


def write_content_to_file(title: str, content_elements: List[Dict], links: List[str], filename: str) -> None:
    # Filter out headings that have no paragraphs after them
    filtered_elements = []
    
    for i, element in enumerate(content_elements):
        if element['type'] == 'heading':
            # Check if there's a paragraph after this heading
            has_paragraph_after = False
            for j in range(i + 1, len(content_elements)):
                next_element = content_elements[j]
                if next_element['type'] == 'paragraph':
                    has_paragraph_after = True
                    break
                elif next_element['type'] == 'heading':
                    break
            
            if has_paragraph_after:
                filtered_elements.append(element)
        else:
            filtered_elements.append(element)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Title: {title}\n")
        f.write("=" * 50 + "\n\n")
        
        for element in filtered_elements:
            if element['type'] == 'heading':
                f.write(f"{'#' * element['level']} {element['text']}\n\n")
            else:
                f.write(f"{element['text']}\n\n")


def main():
    max_files = int(os.environ.get("MAX_FILES", "50"))
    crawler = WebCrawler(data_dir="data", max_files=max_files)
    
    start_urls_env = os.environ.get("START_URLS", "https://tr.wikipedia.org/wiki/Recep_Tayyip_Erdo%C4%9Fan")
    start_urls = [url.strip() for url in start_urls_env.split(",") if url.strip()]
    
    print(f"Starting web crawling with max {crawler.max_files} files")
    print(f"Start URLs: {start_urls}")
    print(f"Already visited {len(crawler.visited_urls)} URLs")
    print(f"Current file count: {crawler.file_count}")
    
    crawler.crawl_all(start_urls)


if __name__ == "__main__":
    main()
