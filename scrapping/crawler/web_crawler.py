import requests
import time
import threading
import logging
from urllib.parse import urlparse
from typing import Dict, List, Optional
from fake_useragent import UserAgent
from robots_checker import RobotsChecker
from content_extractor import ContentExtractor
from url_queue import URLQueue, URLItem
from storage import DataStorage

class WebCrawler:
    def __init__(self, config: Dict):
        self.config = config
        self.robots_checker = RobotsChecker()
        self.url_queue = URLQueue(max_queue_size=config.get('max_queue_size', 10000))
        self.storage = DataStorage(storage_dir=config.get('storage_dir', 'data'))
        self.ua = UserAgent()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Disable urllib3 SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'pages_failed': 0,
            'links_found': 0,
            'images_found': 0,
            'domains_crawled': set(),
            'start_time': None
        }
        
        # Rate limiting
        self.default_delay = config.get('default_delay', 1.0)
        self.max_retries = config.get('max_retries', 3)
        self.request_timeout = config.get('request_timeout', 30)
        
        # Threading
        self.num_workers = config.get('num_workers', 4)
        self.workers = []
        self.stop_event = threading.Event()
    
    def load_seed_urls(self, seed_file: str) -> bool:
        try:
            import json
            with open(seed_file, 'r', encoding='utf-8') as f:
                seed_data = json.load(f)
            
            added_count = self.url_queue.add_seed_urls(seed_data)
            self.logger.info(f"Loaded {added_count} seed URLs from {seed_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading seed URLs: {e}")
            return False
    
    def fetch_page(self, url: str) -> Optional[str]:
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        for attempt in range(self.max_retries):
            try:
                # Check robots.txt
                if not self.robots_checker.can_crawl(url, user_agent='*'):
                    self.logger.warning(f"Robots.txt disallows crawling: {url}")
                    return None
                
                # Check domain rate limiting
                if not self.url_queue.can_access_domain(url):
                    time.sleep(0.1)  # Brief wait before retrying
                    continue
                
                self.logger.debug(f"Attempting to fetch: {url} (attempt {attempt + 1})")
                
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=self.request_timeout,
                    allow_redirects=True,
                    verify=False  # Skip SSL verification for problematic sites
                )
                
                # Mark domain as accessed
                self.url_queue.mark_domain_accessed(url)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' in content_type:
                        self.logger.debug(f"Successfully fetched HTML from: {url}")
                        return response.text
                    else:
                        self.logger.warning(f"Non-HTML content type: {content_type} for {url}")
                        return None
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.exceptions.SSLError as e:
                self.logger.warning(f"SSL Error for {url} (attempt {attempt + 1}): {e}")
                # Try with HTTP instead of HTTPS
                if url.startswith('https://') and attempt == 0:
                    url = url.replace('https://', 'http://')
                    self.logger.info(f"Retrying with HTTP: {url}")
                    continue
                    
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection Error for {url} (attempt {attempt + 1}): {e}")
                
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"Timeout for {url} (attempt {attempt + 1}): {e}")
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed for {url} (attempt {attempt + 1}): {e}")
                
            except Exception as e:
                self.logger.error(f"Unexpected error for {url} (attempt {attempt + 1}): {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def process_url(self, url_item: URLItem) -> bool:
        try:
            self.logger.info(f"Crawling: {url_item.url} (depth: {url_item.depth})")
            
            # Fetch page content
            html_content = self.fetch_page(url_item.url)
            if not html_content:
                return False
            
            # Extract content
            extractor = ContentExtractor(url_item.url)
            content = extractor.parse_html(html_content)
            
            # Save content
            self.storage.save_page_content(content, url_item)
            
            # Also save as JSON if enabled
            if self.config.get('save_json', True):
                self.storage.save_page_json(content, url_item)
            
            # Update statistics
            self.stats['pages_crawled'] += 1
            self.stats['links_found'] += len(content.links)
            self.stats['images_found'] += len(content.image_urls)
            domain = urlparse(url_item.url).netloc
            self.stats['domains_crawled'].add(domain)
            
            # Add new URLs to queue - infinite mode
            if self.config.get('infinite_crawl', False) or url_item.depth < max_depth:
                new_urls_added = 0
                for link in content.links:
                    # Create new URL item
                    new_depth = url_item.depth + 1
                    if not self.config.get('infinite_crawl', False) and new_depth > max_depth:
                        continue
                        
                    new_url_item = URLItem(
                        url=link,
                        category=url_item.category,
                        country=url_item.country,
                        priority=max(1, url_item.priority - 1),  # Decrease priority
                        depth=new_depth,
                        parent_url=url_item.url
                    )
                    
                    if self.url_queue.add_url(new_url_item):
                        new_urls_added += 1
                
                if new_urls_added > 0:
                    self.logger.info(f"Added {new_urls_added} new URLs to queue")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing {url_item.url}: {e}")
            return False
    
    def worker_thread(self, worker_id: int):
        self.logger.info(f"Worker {worker_id} started")
        
        while not self.stop_event.is_set():
            try:
                # Get URL from queue
                url_item = self.url_queue.get_url(timeout=1.0)
                if not url_item:
                    continue
                
                # Process the URL
                success = self.process_url(url_item)
                
                # Mark as completed
                self.url_queue.mark_completed(url_item.url, success)
                
                if not success:
                    self.stats['pages_failed'] += 1
                
                # Brief pause to prevent overwhelming servers
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                time.sleep(1)
        
        self.logger.info(f"Worker {worker_id} stopped")
    
    def start_crawling(self):
        self.stats['start_time'] = time.time()
        self.logger.info("Starting web crawler...")
        
        # Start worker threads
        for i in range(self.num_workers):
            worker = threading.Thread(target=self.worker_thread, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        try:
            # Monitor progress
            while not self.stop_event.is_set():
                time.sleep(10)  # Report every 10 seconds
                
                stats = self.url_queue.get_stats()
                elapsed = time.time() - self.stats['start_time']
                
                self.logger.info(
                    f"Progress - Queue: {stats['queue_size']}, "
                    f"Visited: {stats['visited_count']}, "
                    f"Failed: {stats['failed_count']}, "
                    f"Elapsed: {elapsed:.1f}s"
                )
                
                # Update storage stats periodically
                self.storage.update_crawl_stats(
                    pages_crawled=self.stats['pages_crawled'],
                    pages_failed=self.stats['pages_failed'],
                    links_found=self.stats['links_found'],
                    images_found=self.stats['images_found'],
                    domains=len(self.stats['domains_crawled'])
                )
                
                # In infinite mode, don't stop when queue is empty
                if not self.config.get('infinite_crawl', False) and self.url_queue.is_empty():
                    break
                    
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, stopping crawler...")
        
        finally:
            self.stop_crawling()
    
    def stop_crawling(self):
        self.logger.info("Stopping crawler...")
        self.stop_event.set()
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        # Final statistics
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        self.logger.info("Crawler stopped. Final statistics:")
        self.logger.info(f"Pages crawled: {self.stats['pages_crawled']}")
        self.logger.info(f"Pages failed: {self.stats['pages_failed']}")
        self.logger.info(f"Links found: {self.stats['links_found']}")
        self.logger.info(f"Images found: {self.stats['images_found']}")
        self.logger.info(f"Domains crawled: {len(self.stats['domains_crawled'])}")
        self.logger.info(f"Total time: {elapsed:.1f} seconds")
        
        # Export final data if requested
        if self.config.get('export_on_stop', False):
            export_file = f"crawl_export_{int(time.time())}.json"
            self.storage.export_to_json(export_file)
    
    def get_crawl_stats(self) -> Dict:
        queue_stats = self.url_queue.get_stats()
        storage_stats = self.storage.get_stats()
        
        return {
            'queue': queue_stats,
            'storage': storage_stats,
            'session': self.stats
        }
