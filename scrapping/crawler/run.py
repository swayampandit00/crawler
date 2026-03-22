#!/usr/bin/env python3
"""
Simple infinite crawler runner - just run this file to start crawling
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_crawler import WebCrawler

def main():
    # Configuration for infinite crawling
    config = {
        "max_queue_size": 50000,
        "max_depth": 999,  # Effectively infinite
        "num_workers": 4,
        "default_delay": 1.0,
        "max_retries": 2,
        "request_timeout": 15,
        "storage_dir": "data",
        "save_json": True,
        "export_on_stop": False,
        "infinite_crawl": True,
        "user_agent_rotation": True,
        "respect_robots_txt": True,
        "crawl_delay": {
            "news": 1.0,
            "social_media": 2.0,
            "government": 3.0,
            "default": 1.0
        }
    }
    
    print("🚀 Starting Infinite Web Crawler")
    print("=" * 50)
    print(f"Workers: {config['num_workers']}")
    print(f"Max Depth: {config['max_depth']} (Infinite)")
    print(f"Storage: {config['storage_dir']}")
    print("=" * 50)
    
    # Initialize crawler
    crawler = WebCrawler(config)
    
    # Load seed URLs
    seed_file = os.path.join(os.path.dirname(__file__), 'seed.json')
    if not crawler.load_seed_urls(seed_file):
        print(f"❌ Failed to load seed URLs from: {seed_file}")
        return
    
    # Show initial stats
    stats = crawler.get_crawl_stats()
    print(f"✅ Loaded {stats['queue']['queue_size']} seed URLs")
    print("\n🕷️  Starting infinite crawl...")
    print("Press Ctrl+C to stop\n")
    
    try:
        crawler.start_crawling()
    except KeyboardInterrupt:
        print("\n⏹️  Crawler stopped by user")
    
    # Show final statistics
    final_stats = crawler.get_crawl_stats()
    print("\n📊 Final Statistics:")
    print(f"   Pages crawled: {final_stats['session']['pages_crawled']}")
    print(f"   Pages failed: {final_stats['session']['pages_failed']}")
    print(f"   Links found: {final_stats['session']['links_found']}")
    print(f"   Images found: {final_stats['session']['images_found']}")
    print(f"   Domains crawled: {len(final_stats['session']['domains_crawled'])}")

if __name__ == "__main__":
    main()
