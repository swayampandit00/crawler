# Infinite Web Crawler

A comprehensive web crawler that runs infinitely, discovering and crawling URLs automatically from seed URLs. Respects robots.txt, implements rate limiting, and extracts structured content from websites.

## Features

- **🚀 Infinite Crawling**: Automatically discovers and crawls URLs indefinitely
- **📰 Seed URLs**: Loads 150+ seed URLs from news, social media, government sites
- **🤖 Robots.txt Compliance**: Respects website crawling rules
- **⚡ Rate Limiting**: Implements domain-specific crawl delays
- **🔄 Multi-threaded**: Parallel crawling with 8 workers by default
- **📊 Content Extraction**: Extracts titles, meta tags, text, links, images, and headings
- **💾 Data Storage**: SQLite database + JSON export options
- **⚙️ Configurable**: JSON-based configuration system
- **📈 Statistics**: Real-time crawl statistics and reporting
- **🎯 One-Click Start**: Just run `run.py` to start infinite crawling

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. The crawler is ready to use!

## Usage

### 🚀 Quick Start (Recommended)

```bash
python run.py
```

This will start infinite crawling with all seed URLs automatically!

### Advanced Usage

```bash
# Use main script with custom configuration
python main.py --config config.json --seeds seed.json

# Set number of workers
python main.py --workers 8

# Set maximum crawl depth (for non-infinite mode)
python main.py --max-depth 3

# Custom output directory
python main.py --output /path/to/output

# Dry run (load seeds but don't crawl)
python main.py --dry-run

# Show statistics only
python main.py --stats
```

## Configuration

The crawler uses `config.json` for configuration:

```json
{
  "max_queue_size": 50000,
  "max_depth": 999,
  "num_workers": 8,
  "default_delay": 0.5,
  "max_retries": 3,
  "request_timeout": 30,
  "storage_dir": "data",
  "save_json": true,
  "export_on_stop": false,
  "infinite_crawl": true
}
```

### Configuration Options

- `max_queue_size`: Maximum URLs in queue (default: 50000)
- `max_depth`: Maximum crawl depth (999 = infinite)
- `num_workers`: Number of parallel worker threads (default: 8)
- `default_delay`: Default delay between requests in seconds (default: 0.5)
- `max_retries`: Maximum retry attempts for failed requests (default: 3)
- `request_timeout`: HTTP request timeout in seconds (default: 30)
- `storage_dir`: Directory for storing data (default: "data")
- `save_json`: Save individual pages as JSON files (default: true)
- `export_on_stop`: Export all data to JSON on crawler stop (default: false)
- `infinite_crawl`: Enable infinite crawling mode (default: true)

## Seed URLs

The crawler automatically loads 150+ seed URLs from `seed.json` organized by categories:

### Categories

- **News** (36 URLs): The Hindu, Indian Express, Times of India, NDTV, BBC, CNN, Reuters, Guardian, NYTimes, Washington Post, Al Jazeera, Fox News, NBC News, France24
- **Portals & Jobs** (30 URLs): India.gov.in, JustDial, Sulekha, IndiaMart, Naukri, Monster, Indeed, Shine, Freshersworld, TimesJobs, OLX, Quikr, MagicBricks, 99Acres, MakeMyTrip, IRCTC, LinkedIn, Yelp, TripAdvisor, Booking, Expedia
- **Social Media** (30 URLs): Facebook, Instagram, Twitter/X, YouTube, LinkedIn, Snapchat, Reddit, Quora, Telegram, WhatsApp, Pinterest, Tumblr, Discord, Twitch, Threads, WeChat, VK, TikTok
- **Entertainment** (30 URLs): Hotstar, JioCinema, SonyLIV, Zee5, MXPlayer, Voot, BookMyShow, Gaana, JioSaavn, Netflix, Prime Video, Hulu, Disney+, Paramount+, Peacock, Vimeo, Dailymotion, Spotify, YouTube Music, Flickr, DeviantArt, IMDb, SoundCloud, Shazam, RottenTomatoes, Letterboxd
- **Government** (30 URLs): India.gov.in, MyGov, RBI, SEBI, Income Tax, GST, Parivahan, UIDAI, Digital India, Data.gov.in, ECI, USA.gov, Gov.uk, Canada.ca, Australia.gov.au, NHS.uk, Whitehouse.gov, NASA, UN, WHO

## Output

The crawler generates:

1. **SQLite Database** (`data/crawler.db`):
   - `pages`: Crawled page content
   - `links`: Discovered links
   - `images`: Found image URLs
   - `headings`: Page headings
   - `crawl_stats`: Daily crawl statistics

2. **JSON Files** (`data/json_exports/`):
   - Individual page JSON files (if enabled)
   - Complete export file on crawler stop

3. **Log File** (`crawler.log`):
   - Detailed crawling logs

## Crawler Workflow

1. **🌱 Seed URLs**: Load 150+ starting URLs from seed file
2. **📋 Queue Management**: URLs are queued with priority and depth tracking
3. **🤖 Robots.txt Check**: Verify crawling permissions before each request
4. **⏱️ Rate Limiting**: Respect domain-specific crawl delays
5. **📥 Content Fetching**: Download HTML content with proper headers
6. **🔍 Content Extraction**: Parse and extract structured data
7. **🔗 Link Discovery**: Find and queue new URLs (infinite mode)
8. **💾 Data Storage**: Save extracted content to database and JSON
9. **📊 Statistics**: Track crawl progress and performance

## Rate Limiting

The crawler implements intelligent rate limiting:

- **News sites**: 0.5 seconds delay
- **Social media**: 1.0 seconds delay
- **Government sites**: 2.0 seconds delay
- **Default**: 0.3 seconds delay

Domain-specific delays from robots.txt are also respected.

## Example Output

```
🚀 Starting Infinite Web Crawler
==================================================
Workers: 8
Max Depth: 999 (Infinite)
Storage: data
==================================================
✅ Loaded 150 seed URLs

🕷️  Starting infinite crawl...
Press Ctrl+C to stop

2024-01-01 12:00:00 - INFO - Worker 0 started
2024-01-01 12:00:01 - INFO - Crawling: https://thehindu.com (depth: 0)
2024-01-01 12:00:02 - INFO - Added 45 new URLs to queue
2024-01-01 12:00:10 - INFO - Progress - Queue: 125, Visited: 5, Failed: 0, Elapsed: 10.0s
```

## 🛠️ Troubleshooting

### Common Issues

1. **High Failed Count**: 
   - Check internet connection
   - Some sites may block crawlers
   - Increase `default_delay` in config
   - Check `crawler.log` for detailed error messages

2. **Memory Usage**: Reduce `max_queue_size` if running out of memory

3. **Timeouts**: Increase `request_timeout` for slow sites

4. **Rate Limiting**: If getting blocked, increase delays in config

### Performance Tips

- Use SSD storage for better database performance
- Monitor network bandwidth usage
- Adjust `num_workers` based on your system capacity
- Use `--dry-run` to test configuration before full crawl

## 📊 Understanding Statistics

When you stop the crawler, you'll see final statistics:

```
📊 Final Statistics:
   Pages crawled: 1250
   Pages failed: 142
   Links found: 15420
   Images found: 8900
   Domains crawled: 45
```

- **Pages crawled**: Successfully downloaded and processed
- **Pages failed**: Requests that failed (network issues, blocks, etc.)
- **Links found**: Total unique links discovered
- **Images found**: Total image URLs found
- **Domains crawled**: Number of different websites crawled

## License

This project is open source. See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
