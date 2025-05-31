#!/usr/bin/env python3
"""
Scrapy-based Web Scraper CLI
A command-line tool to scrape multiple URLs using Scrapy and save content as markdown files.

Usage:
    python scrapy_web_scraper.py <urls_file> [--output-dir <dir>] [--delay <seconds>] [--concurrent <num>]

Example:
    python scrapy_web_scraper.py urls.txt --output-dir scraped_content --delay 1 --concurrent 5
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from scrapy.utils.project import get_project_settings
import html2text


class WebScraperSpider(Spider):
    """Scrapy spider for scraping multiple URLs and converting to markdown."""
    
    name = 'web_scraper'
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 5,
        'DOWNLOAD_DELAY': 1,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': False,
        'TELNETCONSOLE_ENABLED': False,
        'DOWNLOAD_TIMEOUT': 30,
    }
    
    def __init__(self, urls: List[str], output_dir: str, *args, **kwargs):
        super(WebScraperSpider, self).__init__(*args, **kwargs)
        self.start_urls = urls
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize HTML to Markdown converter
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = False
        self.html2text.body_width = 0  # Don't wrap lines
        self.html2text.skip_internal_links = False
        
        # Link extractor for finding all links
        self.link_extractor = LinkExtractor()
        
        # Results storage
        self.results = []
    
    def start_requests(self):
        """Generate initial requests for all URLs."""
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                errback=self.handle_error,
                dont_filter=True,
                meta={'original_url': url}
            )
    
    def parse(self, response: Response) -> Dict[str, Any]:
        """Parse the response and extract content."""
        self.logger.info(f"Parsing: {response.url}")
        
        # Extract metadata
        title = self._extract_title(response)
        description = self._extract_description(response)
        
        # Extract all links
        links = [link.url for link in self.link_extractor.extract_links(response)]
        
        # Extract images
        images = response.css('img::attr(src)').getall()
        images = [response.urljoin(img) for img in images]
        
        # Extract main content
        main_content = self._extract_main_content(response)
        
        # Convert to markdown
        markdown_content = self._html_to_markdown(main_content, response)
        
        # Prepare result
        result = {
            'url': response.url,
            'original_url': response.meta.get('original_url', response.url),
            'title': title,
            'description': description,
            'content': markdown_content,
            'links': links,
            'images': images,
            'scraped_at': datetime.now().isoformat(),
            'status_code': response.status,
            'success': True,
            'error': None
        }
        
        # Save to file
        self._save_markdown(result)
        self.results.append(result)
        
        yield result
    
    def handle_error(self, failure):
        """Handle request failures."""
        request = failure.request
        self.logger.error(f"Failed to scrape {request.url}: {failure.value}")
        
        result = {
            'url': request.url,
            'original_url': request.meta.get('original_url', request.url),
            'title': 'Error',
            'description': '',
            'content': '',
            'links': [],
            'images': [],
            'scraped_at': datetime.now().isoformat(),
            'status_code': None,
            'success': False,
            'error': str(failure.value)
        }
        
        self.results.append(result)
        yield result
    
    def _extract_title(self, response: Response) -> str:
        """Extract page title from various sources."""
        # Try standard title tag
        title = response.css('title::text').get()
        if title:
            return title.strip()
        
        # Try Open Graph title
        og_title = response.css('meta[property="og:title"]::attr(content)').get()
        if og_title:
            return og_title.strip()
        
        # Try h1 tag
        h1 = response.css('h1::text').get()
        if h1:
            return h1.strip()
        
        return 'Untitled'
    
    def _extract_description(self, response: Response) -> str:
        """Extract page description from meta tags."""
        # Try meta description
        description = response.css('meta[name="description"]::attr(content)').get()
        if description:
            return description.strip()
        
        # Try Open Graph description
        og_description = response.css('meta[property="og:description"]::attr(content)').get()
        if og_description:
            return og_description.strip()
        
        return ''
    
    def _extract_main_content(self, response: Response) -> str:
        """Extract main content from the page."""
        # Try to find main content areas
        main_selectors = [
            'main',
            'article',
            '[role="main"]',
            '#content',
            '.content',
            '#main',
            '.main',
            'div.post',
            'div.entry-content'
        ]
        
        for selector in main_selectors:
            main_element = response.css(selector).get()
            if main_element:
                return main_element
        
        # Fallback to body content
        body = response.css('body').get()
        if body:
            # Remove script and style tags
            body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL | re.IGNORECASE)
            body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL | re.IGNORECASE)
            return body
        
        return response.text
    
    def _html_to_markdown(self, html_content: str, response: Response) -> str:
        """Convert HTML content to markdown."""
        try:
            # Convert HTML to markdown
            markdown = self.html2text.handle(html_content)
            
            # Clean up excessive newlines
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)
            
            # Add title at the top if available
            title = self._extract_title(response)
            if title and title != 'Untitled':
                markdown = f"# {title}\n\n{markdown}"
            
            return markdown.strip()
        except Exception as e:
            self.logger.error(f"Error converting HTML to markdown: {e}")
            return f"Error converting content: {str(e)}"
    
    def _save_markdown(self, result: Dict[str, Any]) -> Optional[Path]:
        """Save scraped content as markdown file."""
        if not result['success']:
            return None
        
        # Create filename from URL
        filename = self._sanitize_filename(result['url']) + '.md'
        filepath = self.output_dir / filename
        
        # Prepare markdown content with frontmatter
        markdown_content = f"""---
url: {result['url']}
title: {result.get('title', 'Untitled')}
description: {result.get('description', '')}
scraped_at: {result['scraped_at']}
status_code: {result.get('status_code', 'N/A')}
---

{result['content']}

---

## Metadata

- **URL**: {result['url']}
- **Scraped At**: {result['scraped_at']}
- **Links Found**: {len(result.get('links', []))}
- **Images Found**: {len(result.get('images', []))}
"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            self.logger.info(f"Saved: {filepath.name}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save {filename}: {str(e)}")
            return None
    
    def _sanitize_filename(self, url: str) -> str:
        """Create a safe filename from a URL."""
        parsed = urlparse(url)
        
        # Create filename from domain and path
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/')
        
        if path:
            filename = f"{domain}_{path}".replace('/', '_')
        else:
            filename = domain
        
        # Remove invalid characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        filename = re.sub(r'[^\w\s-]', '_', filename)
        filename = re.sub(r'[-\s]+', '-', filename)
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename.strip('-_')
    
    def closed(self, reason):
        """Called when the spider is closed."""
        self.logger.info(f"Spider closed: {reason}")
        
        # Print summary
        successful = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - successful
        
        print(f"\nScraping complete!")
        print(f"Successfully scraped and saved: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {len(self.results)}")


def read_urls_from_file(filepath: str) -> List[str]:
    """Read URLs from a text file (one per line)."""
    urls = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    # Add protocol if missing
                    if not line.startswith(('http://', 'https://')):
                        line = 'https://' + line
                    urls.append(line)
    except Exception as e:
        raise ValueError(f"Failed to read URLs file: {str(e)}")
    
    return urls


def run_scrapy_crawler(urls: List[str], output_dir: str, settings: Dict[str, Any]):
    """Run the Scrapy crawler with given URLs and settings."""
    # Create process with custom settings
    process = CrawlerProcess(settings)
    
    # Run the spider
    process.crawl(
        WebScraperSpider,
        urls=urls,
        output_dir=output_dir
    )
    
    # Start the crawling process
    process.start()


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Scrapy-based web scraper CLI - Scrape multiple URLs and save as markdown files',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'urls_file',
        help='Path to text file containing URLs (one per line)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='scraped_content',
        help='Output directory for markdown files (default: scraped_content)'
    )
    
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--concurrent', '-c',
        type=int,
        default=5,
        help='Number of concurrent requests (default: 5)'
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=30,
        help='Request timeout in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--user-agent', '-ua',
        help='Custom user agent string'
    )
    
    parser.add_argument(
        '--ignore-robots-txt',
        action='store_true',
        help='Ignore robots.txt restrictions'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Read URLs
    try:
        urls = read_urls_from_file(args.urls_file)
        if not urls:
            print("No URLs found in the input file.")
            return
        print(f"Found {len(urls)} URLs to scrape")
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Prepare Scrapy settings
    settings = {
        'DOWNLOAD_DELAY': args.delay,
        'CONCURRENT_REQUESTS': args.concurrent,
        'DOWNLOAD_TIMEOUT': args.timeout,
        'LOG_LEVEL': args.log_level,
        'ROBOTSTXT_OBEY': not args.ignore_robots_txt,
    }
    
    if args.user_agent:
        settings['USER_AGENT'] = args.user_agent
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Run the crawler
    print("\nStarting Scrapy crawler...")
    try:
        run_scrapy_crawler(urls, args.output_dir, settings)
    except Exception as e:
        print(f"Error running crawler: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()