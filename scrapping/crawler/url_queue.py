import queue
import threading
from urllib.parse import urlparse
from typing import Set, Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict
import time

@dataclass
class URLItem:
    url: str
    category: str
    country: str
    priority: int = 1
    depth: int = 0
    parent_url: Optional[str] = None
    retry_count: int = 0

class URLQueue:
    def __init__(self, max_queue_size: int = 10000):
        self.queue = queue.PriorityQueue(maxsize=max_queue_size)
        self.visited: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.failed: Set[str] = set()
        self.domain_counts: Dict[str, int] = defaultdict(int)
        self.category_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        
        # Rate limiting per domain
        self.domain_last_access: Dict[str, float] = {}
        self.domain_delays: Dict[str, float] = {}
        
    def add_url(self, url_item: URLItem) -> bool:
        with self.lock:
            if url_item.url in self.visited or url_item.url in self.in_progress:
                return False
            
            if url_item.url in self.failed and url_item.retry_count >= 3:
                return False
            
            try:
                # Priority: negative for higher priority (lower number = higher priority)
                priority = (-url_item.priority, url_item.depth, url_item.url)
                self.queue.put((priority, url_item))
                self.in_progress.add(url_item.url)
                
                # Update counts
                domain = urlparse(url_item.url).netloc
                self.domain_counts[domain] += 1
                self.category_counts[url_item.category] += 1
                
                return True
            except queue.Full:
                return False
    
    def get_url(self, timeout: Optional[float] = None) -> Optional[URLItem]:
        try:
            priority, url_item = self.queue.get(timeout=timeout)
            return url_item
        except queue.Empty:
            return None
    
    def mark_completed(self, url: str, success: bool = True):
        with self.lock:
            if url in self.in_progress:
                self.in_progress.remove(url)
            
            if success:
                self.visited.add(url)
                if url in self.failed:
                    self.failed.remove(url)
            else:
                self.failed.add(url)
    
    def add_seed_urls(self, seed_data: Dict) -> int:
        added_count = 0
        
        for category_data in seed_data.get('seeds', []):
            category = category_data.get('category', 'unknown')
            
            for url_info in category_data.get('urls', []):
                url_item = URLItem(
                    url=url_info.get('url'),
                    category=category,
                    country=url_info.get('country', 'unknown'),
                    priority=2 if category == 'news' else 1,  # News gets higher priority
                    depth=0
                )
                
                if self.add_url(url_item):
                    added_count += 1
        
        return added_count
    
    def get_domain_rate_limit(self, url: str) -> float:
        domain = urlparse(url).netloc
        
        # Default delays based on site type
        if any(keyword in domain.lower() for keyword in ['news', 'times', 'express']):
            return 1.0  # 1 second between requests for news sites
        elif any(keyword in domain.lower() for keyword in ['gov', 'edu']):
            return 2.0  # 2 seconds for government/educational
        else:
            return 0.5  # 0.5 seconds for other sites
    
    def can_access_domain(self, url: str) -> bool:
        domain = urlparse(url).netloc
        current_time = time.time()
        
        # Check if we need to wait for this domain
        if domain in self.domain_last_access:
            elapsed = current_time - self.domain_last_access[domain]
            delay = self.domain_delays.get(domain, self.get_domain_rate_limit(url))
            
            if elapsed < delay:
                return False
        
        return True
    
    def mark_domain_accessed(self, url: str):
        domain = urlparse(url).netloc
        self.domain_last_access[domain] = time.time()
        if domain not in self.domain_delays:
            self.domain_delays[domain] = self.get_domain_rate_limit(url)
    
    def get_stats(self) -> Dict:
        with self.lock:
            return {
                'queue_size': self.queue.qsize(),
                'visited_count': len(self.visited),
                'in_progress_count': len(self.in_progress),
                'failed_count': len(self.failed),
                'domain_counts': dict(self.domain_counts),
                'category_counts': dict(self.category_counts)
            }
    
    def is_empty(self) -> bool:
        return self.queue.empty()
    
    def retry_failed_url(self, url: str):
        with self.lock:
            if url in self.failed:
                self.failed.remove(url)
                # Note: You would need to reconstruct the URLItem to retry
                # This is a simplified version
