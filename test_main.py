import pytest
from main import fetch_html, get_page_title, parse_article_content


class TestPageTitleExtraction:
    urls = [
        "https://tr.wikipedia.org/wiki/Recep_Tayyip_Erdo%C4%9Fan",
        "https://tr.wikipedia.org/wiki/Mustafa_Kemal_Atat%C3%BCrk",
        "https://tr.wikipedia.org/wiki/T%C3%BCrkiye",
        "https://tr.wikipedia.org/wiki/Python",
    ]
    
    expected_titles = [
        "Recep Tayyip Erdoğan",
        "Mustafa Kemal Atatürk", 
        "Türkiye",
        "Python",
    ]
    
    @pytest.mark.parametrize("url,expected_title", zip(urls, expected_titles))
    def test_page_title_extraction(self, url, expected_title):
        html = fetch_html(url)
        assert html is not None, f"Failed to fetch HTML from {url}"
        
        title = get_page_title(html)
        assert title is not None, f"Failed to extract title from {url}"
        assert title == expected_title, f"Expected '{expected_title}', got '{title}'"
    
    def test_invalid_url(self):
        html = fetch_html("https://thisdoesnotexist12345.invalid")
        assert html is None
    
    def test_no_title_element(self):
        html = "<html><body><p>No title here</p></body></html>"
        title = get_page_title(html)
        assert title is None


class TestContentParsing:
    def test_parse_article_content(self):
        url = "https://tr.wikipedia.org/wiki/T%C3%BCrkiye"
        html = fetch_html(url)
        assert html is not None
        
        content_elements, links = parse_article_content(html)
        assert len(content_elements) > 0
        assert len(links) > 0
        
        # Check that we have both paragraphs and headings
        has_paragraph = any(el['type'] == 'paragraph' for el in content_elements)
        has_heading = any(el['type'] == 'heading' for el in content_elements)
        assert has_paragraph
        assert has_heading
        
        # Check that links are extracted
        assert all(isinstance(link, str) for link in links)
    
    def test_empty_content(self):
        html = "<html><body><div>No content div</div></body></html>"
        content_elements, links = parse_article_content(html)
        assert content_elements == []
        assert links == []