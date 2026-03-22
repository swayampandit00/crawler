#!/usr/bin/env python3
"""
Web Crawler Main Entry Point
A comprehensive web crawler that respects robots.txt, implements rate limiting,
and extracts structured content from websites.
"""

import json
import argparse
import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_crawler import WebCrawler

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration file: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Web Crawler - Crawl websites and extract content')
    parser.add_argument('--config', '-c', default='config.json', 
                       help='Configuration file path (default: config.json)')
    parser.add_argument('--seeds', '-s', default='seed.json', 
                       help='Seed URLs file path (default: seed.json)')
    parser.add_argument('--workers', '-w', type=int, 
                       help='Number of worker threads (overrides config)')
    parser.add_argument('--max-depth', '-d', type=int, 
                       help='Maximum crawl depth (overrides config)')
    parser.add_argument('--output', '-o', 
                       help='Output directory for data (overrides config)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Load configuration and seeds but do not start crawling')
    parser.add_argument('--stats', action='store_true', 
                       help='Show crawl statistics and exit')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.workers:
        config['num_workers'] = args.workers
    if args.max_depth:
        config['max_depth'] = args.max_depth
    if args.output:
        config['storage_dir'] = args.output
    
    # Validate seed file exists
    if not os.path.exists(args.seeds):
        print(f"Seed file {args.seeds} not found!")
        sys.exit(1)
    
    print("=== Web Crawler Configuration ===")
    print(f"Config file: {args.config}")
    print(f"Seed file: {args.seeds}")
    print(f"Workers: {config['num_workers']}")
    print(f"Max depth: {config['max_depth']}")
    print(f"Storage dir: {config['storage_dir']}")
    print(f"Max queue size: {config['max_queue_size']}")
    print(f"Default delay: {config['default_delay']}s")
    print(f"Max retries: {config['max_retries']}")
    print(f"Request timeout: {config['request_timeout']}s")
    print("=" * 35)
    
    # Initialize crawler
    crawler = WebCrawler(config)
    
    # Load seed URLs
    if not crawler.load_seed_urls(args.seeds):
        print("Failed to load seed URLs!")
        sys.exit(1)
    
    # Show initial stats
    stats = crawler.get_crawl_stats()
    print(f"\nLoaded {stats['queue']['queue_size']} URLs into queue")
    
    # Show detailed statistics if requested
    if args.stats:
        print("\n=== Crawler Statistics ===")
        print(f"Queue size: {stats['queue']['queue_size']}")
        print(f"Visited: {stats['queue']['visited_count']}")
        print(f"In progress: {stats['queue']['in_progress_count']}")
        print(f"Failed: {stats['queue']['failed_count']}")
        print("\nCategory counts:")
        for category, count in stats['queue']['category_counts'].items():
            print(f"  {category}: {count}")
        print("\nDomain counts:")
        for domain, count in list(stats['queue']['domain_counts'].items())[:10]:
            print(f"  {domain}: {count}")
        if len(stats['queue']['domain_counts']) > 10:
            print(f"  ... and {len(stats['queue']['domain_counts']) - 10} more domains")
        return
    
    # Dry run mode
    if args.dry_run:
        print("\nDry run mode - not starting crawler")
        print(f"Ready to crawl {stats['queue']['queue_size']} URLs")
        return
    
    # Start crawling
    try:
        print(f"\nStarting crawler with {config['num_workers']} workers...")
        print("Press Ctrl+C to stop crawling\n")
        
        crawler.start_crawling()
        
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    except Exception as e:
        print(f"\nCrawler error: {e}")
        sys.exit(1)
    
    # Show final statistics
    final_stats = crawler.get_crawl_stats()
    print("\n=== Final Statistics ===")
    print(f"Pages crawled: {final_stats['session']['pages_crawled']}")
    print(f"Pages failed: {final_stats['session']['pages_failed']}")
    print(f"Links found: {final_stats['session']['links_found']}")
    print(f"Images found: {final_stats['session']['images_found']}")
    print(f"Domains crawled: {len(final_stats['session']['domains_crawled'])}")
    
    if final_stats['storage']:
        print(f"\nStorage Statistics:")
        print(f"Total pages in database: {final_stats['storage']['total_pages']}")
        if final_stats['storage'].get('today'):
            today = final_stats['storage']['today']
            print(f"Today's crawl: {today['pages_crawled']} pages, {today['pages_failed']} failed")

if __name__ == "__main__":
    main()
