import urllib.request
import urllib.error
from typing import Optional, List, Dict, Tuple
from bs4 import BeautifulSoup


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
    url = "https://tr.wikipedia.org/wiki/Recep_Tayyip_Erdo%C4%9Fan"
    html = fetch_html(url)
    if html:
        title = get_page_title(html)
        if title:
            print(f"Page title: {title}")
        else:
            print("Title not found")
        
        content_elements, links = parse_article_content(html)
        print(f"\nFound {len(content_elements)} content elements and {len(links)} links")
        
        # Write to file
        filename = f"{title.replace(' ', '_')}.txt"
        write_content_to_file(title, content_elements, links, filename)
        print(f"\nContent written to: {filename}")
        
        # Show first 3 content elements
        for element in content_elements[:3]:
            if element['type'] == 'heading':
                print(f"\nH{element['level']}: {element['text']}")
            else:
                print(f"\nParagraph: {element['text'][:100]}...")
        
        # Show first 5 links
        print(f"\nFirst 5 links:")
        for link in links[:5]:
            print(f"- {link}")
    else:
        print("Failed to fetch HTML content")


if __name__ == "__main__":
    main()
