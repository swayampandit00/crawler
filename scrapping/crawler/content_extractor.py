from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

@dataclass
class ExtractedContent:
    url: str
    title: str
    meta_description: str
    meta_keywords: str
    text_content: str
    links: List[str]
    image_urls: List[str]
    headings: Dict[str, List[str]]
    canonical_url: Optional[str] = None

class ContentExtractor:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.soup = None
    
    def parse_html(self, html_content: str) -> ExtractedContent:
        self.soup = BeautifulSoup(html_content, 'lxml')
        
        return ExtractedContent(
            url=self.base_url,
            title=self._extract_title(),
            meta_description=self._extract_meta_description(),
            meta_keywords=self._extract_meta_keywords(),
            text_content=self._extract_text_content(),
            links=self._extract_links(),
            image_urls=self._extract_images(),
            headings=self._extract_headings(),
            canonical_url=self._extract_canonical_url()
        )
    
    def _extract_title(self) -> str:
        if self.soup.title:
            return self.soup.title.get_text().strip()
        return ""
    
    def _extract_meta_description(self) -> str:
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()
        
        # Try property="og:description" as fallback
        og_desc = self.soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()
        
        return ""
    
    def _extract_meta_keywords(self) -> str:
        meta_keywords = self.soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            return meta_keywords.get('content').strip()
        return ""
    
    def _extract_text_content(self) -> str:
        # Remove script and style elements
        for script in self.soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text from main content areas first
        main_content = ""
        for tag in ['main', 'article', 'div[class*="content"]', 'div[class*="article"]']:
            element = self.soup.find(tag)
            if element:
                main_content = element.get_text(separator=' ', strip=True)
                break
        
        # Fallback to body if no main content found
        if not main_content:
            main_content = self.soup.get_text(separator=' ', strip=True)
        
        # Clean up extra whitespace
        return re.sub(r'\s+', ' ', main_content).strip()
    
    def _extract_links(self) -> List[str]:
        links = []
        base_domain = urlparse(self.base_url).netloc
        
        for link in self.soup.find_all('a', href=True):
            href = link['href'].strip()
            
            # Skip empty links, anchors, javascript, and mailto
            if (not href or href.startswith('#') or 
                href.startswith('javascript:') or href.startswith('mailto:')):
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(self.base_url, href)
            
            # Only include HTTP/HTTPS links
            if absolute_url.startswith(('http://', 'https://')):
                links.append(absolute_url)
        
        return list(set(links))  # Remove duplicates
    
    def _extract_images(self) -> List[str]:
        image_urls = []
        
        for img in self.soup.find_all('img', src=True):
            src = img['src'].strip()
            if not src:
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(self.base_url, src)
            
            if absolute_url.startswith(('http://', 'https://')):
                image_urls.append(absolute_url)
        
        return list(set(image_urls))
    
    def _extract_headings(self) -> Dict[str, List[str]]:
        headings = {
            'h1': [],
            'h2': [],
            'h3': [],
            'h4': [],
            'h5': [],
            'h6': []
        }
        
        for level in headings.keys():
            for heading in self.soup.find_all(level):
                text = heading.get_text().strip()
                if text:
                    headings[level].append(text)
        
        return headings
    
    def _extract_canonical_url(self) -> Optional[str]:
        canonical = self.soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            return canonical.get('href')
        return None
    
    def get_page_metadata(self) -> Dict:
        if not self.soup:
            return {}
        
        metadata = {
            'title': self._extract_title(),
            'meta_description': self._extract_meta_description(),
            'meta_keywords': self._extract_meta_keywords(),
            'canonical_url': self._extract_canonical_url(),
            'word_count': len(self._extract_text_content().split()),
            'link_count': len(self._extract_links()),
            'image_count': len(self._extract_images()),
            'has_forms': bool(self.soup.find('form')),
            'has_tables': bool(self.soup.find('table')),
        }
        
        return metadata
