import urllib.robotparser
import urllib.request
import time
from urllib.parse import urlparse
from typing import Dict, Optional

class RobotsChecker:
    def __init__(self):
        self.parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self.last_checked: Dict[str, float] = {}
        self.cache_duration = 3600  # 1 hour cache
    
    def _get_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _get_robots_url(self, domain: str) -> str:
        return f"{domain}/robots.txt"
    
    def _is_cache_valid(self, domain: str) -> bool:
        if domain not in self.last_checked:
            return False
        return time.time() - self.last_checked[domain] < self.cache_duration
    
    def _fetch_robots_txt(self, domain: str) -> Optional[urllib.robotparser.RobotFileParser]:
        try:
            robots_url = self._get_robots_url(domain)
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(robots_url)
            
            # Use request method instead of read to avoid comparison error
            try:
                req = urllib.request.Request(robots_url)
                req.add_header('User-Agent', '*')
                response = urllib.request.urlopen(req, timeout=10)
                parser.parse(response.read().decode('utf-8', errors='ignore').splitlines())
            except Exception as e:
                print(f"Failed to fetch robots.txt for {domain}: {e}")
                # Continue without robots.txt
                return None
            
            if parser.mtime > 0:  # Successfully parsed
                self.parsers[domain] = parser
                self.last_checked[domain] = time.time()
                return parser
        except Exception as e:
            print(f"Failed to fetch robots.txt for {domain}: {e}")
        
        return None
    
    def can_crawl(self, url: str, user_agent: str = "*") -> bool:
        domain = self._get_domain(url)
        
        # Check cache first
        if not self._is_cache_valid(domain):
            self._fetch_robots_txt(domain)
        
        # If we have a parser, use it
        if domain in self.parsers:
            return self.parsers[domain].can_fetch(user_agent, url)
        
        # Default to allow if no robots.txt found or accessible
        return True
    
    def get_crawl_delay(self, url: str, user_agent: str = "*") -> Optional[float]:
        domain = self._get_domain(url)
        
        if not self._is_cache_valid(domain):
            self._fetch_robots_txt(domain)
        
        if domain in self.parsers:
            return self.parsers[domain].crawl_delay(user_agent)
        
        return None
