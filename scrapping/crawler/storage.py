import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict
from content_extractor import ExtractedContent
from url_queue import URLItem

class DataStorage:
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        self.db_path = os.path.join(storage_dir, "crawler.db")
        self.json_dir = os.path.join(storage_dir, "json_exports")
        
        # Create directories
        os.makedirs(storage_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Pages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    meta_description TEXT,
                    meta_keywords TEXT,
                    text_content TEXT,
                    canonical_url TEXT,
                    category TEXT,
                    country TEXT,
                    crawl_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    word_count INTEGER,
                    link_count INTEGER,
                    image_count INTEGER,
                    status TEXT DEFAULT 'success'
                )
            ''')
            
            # Links table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_url TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_url) REFERENCES pages (url)
                )
            ''')
            
            # Images table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_url TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (page_url) REFERENCES pages (url)
                )
            ''')
            
            # Headings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS headings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_url TEXT NOT NULL,
                    heading_level TEXT NOT NULL,
                    heading_text TEXT NOT NULL,
                    FOREIGN KEY (page_url) REFERENCES pages (url)
                )
            ''')
            
            # Crawl stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crawl_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE DEFAULT CURRENT_DATE,
                    pages_crawled INTEGER DEFAULT 0,
                    pages_failed INTEGER DEFAULT 0,
                    total_links_found INTEGER DEFAULT 0,
                    total_images_found INTEGER DEFAULT 0,
                    unique_domains INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
    
    def save_page_content(self, content: ExtractedContent, url_item: URLItem) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert page data
                cursor.execute('''
                    INSERT OR REPLACE INTO pages 
                    (url, title, meta_description, meta_keywords, text_content, 
                     canonical_url, category, country, word_count, link_count, image_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    content.url,
                    content.title,
                    content.meta_description,
                    content.meta_keywords,
                    content.text_content,
                    content.canonical_url,
                    url_item.category,
                    url_item.country,
                    len(content.text_content.split()) if content.text_content else 0,
                    len(content.links),
                    len(content.image_urls)
                ))
                
                # Insert links
                for link in content.links:
                    cursor.execute('''
                        INSERT OR IGNORE INTO links (source_url, target_url)
                        VALUES (?, ?)
                    ''', (content.url, link))
                
                # Insert images
                for img_url in content.image_urls:
                    cursor.execute('''
                        INSERT OR IGNORE INTO images (page_url, image_url)
                        VALUES (?, ?)
                    ''', (content.url, img_url))
                
                # Insert headings
                for level, headings in content.headings.items():
                    for heading in headings:
                        cursor.execute('''
                            INSERT INTO headings (page_url, heading_level, heading_text)
                            VALUES (?, ?, ?)
                        ''', (content.url, level, heading))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error saving page content: {e}")
            return False
    
    def save_page_json(self, content: ExtractedContent, url_item: URLItem):
        """Save page content as JSON file"""
        try:
            # Create filename from URL
            safe_url = content.url.replace('https://', '').replace('http://', '').replace('/', '_')
            filename = f"{safe_url}.json"
            filepath = os.path.join(self.json_dir, filename)
            
            # Prepare data for JSON
            data = {
                'url': content.url,
                'title': content.title,
                'meta_description': content.meta_description,
                'meta_keywords': content.meta_keywords,
                'text_content': content.text_content,
                'canonical_url': content.canonical_url,
                'category': url_item.category,
                'country': url_item.country,
                'crawl_date': datetime.now().isoformat(),
                'links': content.links,
                'image_urls': content.image_urls,
                'headings': content.headings,
                'word_count': len(content.text_content.split()) if content.text_content else 0,
                'link_count': len(content.links),
                'image_count': len(content.image_urls)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving JSON: {e}")
    
    def update_crawl_stats(self, pages_crawled: int = 0, pages_failed: int = 0, 
                         links_found: int = 0, images_found: int = 0, domains: int = 0):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if today's stats exist
                cursor.execute('''
                    SELECT pages_crawled, pages_failed, total_links_found, total_images_found, unique_domains
                    FROM crawl_stats WHERE date = DATE('now')
                ''')
                
                result = cursor.fetchone()
                
                if result:
                    # Update existing stats
                    cursor.execute('''
                        UPDATE crawl_stats 
                        SET pages_crawled = pages_crawled + ?,
                            pages_failed = pages_failed + ?,
                            total_links_found = total_links_found + ?,
                            total_images_found = total_images_found + ?,
                            unique_domains = unique_domains + ?
                        WHERE date = DATE('now')
                    ''', (pages_crawled, pages_failed, links_found, images_found, domains))
                else:
                    # Insert new stats for today
                    cursor.execute('''
                        INSERT INTO crawl_stats 
                        (pages_crawled, pages_failed, total_links_found, total_images_found, unique_domains)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (pages_crawled, pages_failed, links_found, images_found, domains))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error updating crawl stats: {e}")
    
    def get_crawled_urls(self) -> List[str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT url FROM pages')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting crawled URLs: {e}")
            return []
    
    def get_stats(self) -> Dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total pages
                cursor.execute('SELECT COUNT(*) FROM pages')
                total_pages = cursor.fetchone()[0]
                
                # Pages by category
                cursor.execute('''
                    SELECT category, COUNT(*) FROM pages 
                    WHERE category IS NOT NULL GROUP BY category
                ''')
                by_category = dict(cursor.fetchall())
                
                # Pages by country
                cursor.execute('''
                    SELECT country, COUNT(*) FROM pages 
                    WHERE country IS NOT NULL GROUP BY country
                ''')
                by_country = dict(cursor.fetchall())
                
                # Today's stats
                cursor.execute('''
                    SELECT pages_crawled, pages_failed, total_links_found, 
                           total_images_found, unique_domains
                    FROM crawl_stats WHERE date = DATE('now')
                ''')
                today_stats = cursor.fetchone()
                
                return {
                    'total_pages': total_pages,
                    'by_category': by_category,
                    'by_country': by_country,
                    'today': {
                        'pages_crawled': today_stats[0] if today_stats else 0,
                        'pages_failed': today_stats[1] if today_stats else 0,
                        'links_found': today_stats[2] if today_stats else 0,
                        'images_found': today_stats[3] if today_stats else 0,
                        'domains': today_stats[4] if today_stats else 0
                    }
                }
                
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def export_to_json(self, output_file: str):
        """Export all data to a single JSON file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all pages with their data
                cursor.execute('''
                    SELECT url, title, meta_description, meta_keywords, text_content,
                           canonical_url, category, country, crawl_date, word_count,
                           link_count, image_count
                    FROM pages
                ''')
                
                pages = []
                for row in cursor.fetchall():
                    page_data = {
                        'url': row[0],
                        'title': row[1],
                        'meta_description': row[2],
                        'meta_keywords': row[3],
                        'text_content': row[4],
                        'canonical_url': row[5],
                        'category': row[6],
                        'country': row[7],
                        'crawl_date': row[8],
                        'word_count': row[9],
                        'link_count': row[10],
                        'image_count': row[11]
                    }
                    
                    # Get links for this page
                    cursor.execute('SELECT target_url FROM links WHERE source_url = ?', (row[0],))
                    page_data['links'] = [link[0] for link in cursor.fetchall()]
                    
                    # Get images for this page
                    cursor.execute('SELECT image_url FROM images WHERE page_url = ?', (row[0],))
                    page_data['images'] = [img[0] for img in cursor.fetchall()]
                    
                    # Get headings for this page
                    cursor.execute('SELECT heading_level, heading_text FROM headings WHERE page_url = ?', (row[0],))
                    headings = {}
                    for level, text in cursor.fetchall():
                        if level not in headings:
                            headings[level] = []
                        headings[level].append(text)
                    page_data['headings'] = headings
                    
                    pages.append(page_data)
                
                # Save to file
                export_data = {
                    'export_date': datetime.now().isoformat(),
                    'total_pages': len(pages),
                    'pages': pages
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                print(f"Exported {len(pages)} pages to {output_file}")
                
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
