import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
import logging
import re
from bs4 import BeautifulSoup
from typing import Set, List
from .url_frontier import URLFrontier
from .product_identifier import ProductIdentifier

class Crawler:
    """Base crawler implementation for e-commerce websites"""
    
    def __init__(self, domain: str, max_urls: int = 1000, concurrency: int = 5):
        self.domain = domain
        self.max_urls = max_urls
        self.concurrency = concurrency
        self.frontier = URLFrontier()
        self.visited_urls = set()
        self.product_urls = set()
        self.product_identifier = ProductIdentifier()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def crawl(self) -> List[str]:
        """Main crawling method that coordinates the process"""
        self.logger.info(f"Starting crawl for {self.domain}")
        
        # Add the root URL to start crawling
        self.frontier.add(self.domain)
        
        # Create session for all requests
        async with aiohttp.ClientSession(
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            tasks = []
            for _ in range(self.concurrency):
                tasks.append(asyncio.create_task(self.worker(session)))
            
            # Wait for all workers to complete
            await asyncio.gather(*tasks)
        
        self.logger.info(f"Crawl complete for {self.domain}. Found {len(self.product_urls)} product URLs")
        return list(self.product_urls)
    
    async def worker(self, session: aiohttp.ClientSession):
        """Worker that processes URLs from the frontier"""
        while not self.frontier.is_empty():
            # Check if we've reached the maximum URLs to process
            if len(self.visited_urls) >= self.max_urls:
                break
            
            url = self.frontier.get()
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            self.visited_urls.add(url)
            
            try:
                await self.process_url(session, url)
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error processing {url}: {str(e)}")
    
    async def process_url(self, session: aiohttp.ClientSession, url: str):
        """Process a single URL: fetch, parse, and extract links"""
        self.logger.debug(f"Processing: {url}")
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Got status {response.status} for {url}")
                    return
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Check if this is a product page
                if self.product_identifier.is_product_page(url, html, soup):
                    self.logger.info(f"Found product URL: {url}")
                    self.product_urls.add(url)
                
                # Extract all links for further crawling
                links = self.extract_links(soup, url)
                for link in links:
                    if self.should_crawl(link):
                        self.frontier.add(link)
        
        except aiohttp.ClientError as e:
            self.logger.error(f"Request error for {url}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error processing {url}: {str(e)}")
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract and normalize all links from the page"""
        links = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            # Skip empty href and JavaScript links
            if not href or href.startswith('javascript:'):
                continue
            
            # Convert relative URL to absolute
            absolute_url = urljoin(base_url, href)
            links.append(absolute_url)
        
        return links
    
    def should_crawl(self, url: str) -> bool:
        """Determine if a URL should be crawled"""
        # Only crawl URLs from the same domain
        parsed_url = urlparse(url)
        parsed_domain = urlparse(self.domain)
        
        # Check if domains match
        if parsed_url.netloc != parsed_domain.netloc:
            return False
        
        # Skip URLs with fragments (#)
        if parsed_url.fragment:
            return False
        
        # Skip common non-product extensions
        if url.endswith(('.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.svg')):
            return False
        
        return True