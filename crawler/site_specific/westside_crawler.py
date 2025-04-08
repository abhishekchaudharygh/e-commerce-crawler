from crawler.base_crawler import Crawler
import re
from bs4 import BeautifulSoup

class WestsideCrawler(Crawler):
    """Site-specific crawler for westside.com"""
    
    def __init__(self, domain, max_urls=1000, concurrency=5):
        super().__init__(domain, max_urls, concurrency)
        # Westside-specific product patterns
        self.westside_product_patterns = [
            r'/product/',
            r'/[^/]+/[^/]+/[a-zA-Z0-9-]+-[0-9]+\.html',  # Product URL pattern with ID
            r'/[^/]+/[^/]+/[^/]+\?productid=',  # Product with ID in query parameter
        ]
    
    async def process_url(self, session, url: str):
        """Override to add site-specific logic for Westside"""
        await super().process_url(session, url)
        
        # Westside specific product URL detection
        for pattern in self.westside_product_patterns:
            if re.search(pattern, url):
                self.logger.info(f"Westside product detected via pattern: {url}")
                self.product_urls.add(url)
                break
    
    def extract_links(self, soup: BeautifulSoup, base_url: str):
        """Override to handle Westside-specific link extraction"""
        links = super().extract_links(soup, base_url)
        
        # Additional extraction for Westside's product grid
        product_elements = soup.find_all('div', class_=lambda c: c and ('product-item' in c or 'product-tile' in c))
        for product in product_elements:
            link_tag = product.find('a')
            if link_tag and link_tag.get('href'):
                href = link_tag['href']
                # Some Westside links might use data attributes
                if not href or href == '#':
                    href = link_tag.get('data-product-url', '')
                if href:
                    absolute_url = self._normalize_url(base_url, href)
                    links.append(absolute_url)
        
        return links
    
    def _normalize_url(self, base_url: str, href: str):
        """Fix potential Westside URL peculiarities"""
        if href.startswith('//'):
            return f"https:{href}"
        if href.startswith('/'):
            domain = self.domain.rstrip('/')
            return f"{domain}{href}"
        if not (href.startswith('http://') or href.startswith('https://')):
            domain = self.domain.rstrip('/')
            return f"{domain}/{href.lstrip('/')}"
        return href
    
    def should_crawl(self, url: str) -> bool:
        """Override to add Westside-specific crawling rules"""
        if not super().should_crawl(url):
            return False
            
        # Westside-specific exclusions
        excluded_paths = [
            '/login', 
            '/register', 
            '/wishlist', 
            '/checkout',
            '/search',
            '/cart',
            '/customer',
            '/store-locator'
        ]
        
        for path in excluded_paths:
            if path in url:
                return False
                
        return True