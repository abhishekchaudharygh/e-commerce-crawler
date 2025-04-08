from crawler.base_crawler import Crawler
from bs4 import BeautifulSoup
import re
import json
import logging

class TatacliqCrawler(Crawler):
    """Site-specific crawler for tatacliq.com"""
    
    def __init__(self, domain, max_urls=1000, concurrency=5):
        super().__init__(domain, max_urls, concurrency)
        # Updated TataCliq-specific product URL patterns
        self.tatacliq_product_patterns = [
            r'/p-\d+',  # Product detail pages typically follow this pattern
            r'pdp/',     # Product detail page URL path
            r'-p-\d+',   # Another common pattern
            r'/product-details/',  # Product details path
        ]
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def process_url(self, session, url: str):
        """Override to add site-specific logic for TataCliq"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Got status {response.status} for {url}")
                    return
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # TataCliq specific product URL detection
                for pattern in self.tatacliq_product_patterns:
                    if re.search(pattern, url):
                        self.logger.info(f"TataCliq product detected via pattern: {url}")
                        self.product_urls.add(url)
                        break
                
                # Check for product identifier in page metadata
                if self._check_product_metadata(soup):
                    self.logger.info(f"TataCliq product detected via metadata: {url}")
                    self.product_urls.add(url)
                
                # Check for product scripts with product data
                if self._check_product_scripts(html):
                    self.logger.info(f"TataCliq product detected via scripts: {url}")
                    self.product_urls.add(url)
                
                # Extract all links for further crawling
                links = self.extract_links(soup, url)
                for link in links:
                    if self.should_crawl(link):
                        self.frontier.add(link)
        
        except Exception as e:
            self.logger.error(f"Error processing {url}: {str(e)}")
    
    def _check_product_metadata(self, soup):
        """Check for TataCliq product metadata"""
        # Look for product structured data
        product_meta = soup.find('meta', {'property': 'og:type', 'content': 'product'})
        if product_meta:
            return True
            
        # Look for price elements which are common on product pages
        price_elements = soup.find_all(['span', 'div'], class_=lambda c: c and ('price' in c.lower() if c else False))
        if len(price_elements) > 1:
            return True
            
        # Look for Add to Bag/Cart buttons
        cart_buttons = soup.find_all(['button', 'a'], string=lambda s: s and ('add to' in s.lower() if s else False))
        if cart_buttons:
            return True
            
        return False
    
    def _check_product_scripts(self, html):
        """Check for product data in scripts"""
        # TataCliq often stores product data in JavaScript
        script_patterns = [
            r'"productId"\s*:\s*"[^"]+',
            r'"product"\s*:\s*{',
            r'productDetails',
            r'pdpPageData'
        ]
        
        for pattern in script_patterns:
            if re.search(pattern, html):
                return True
                
        return False
    
    def extract_links(self, soup, base_url):
        """Override to add TataCliq-specific link extraction"""
        links = super().extract_links(soup, base_url)
        
        # Extract links from product cards
        product_cards = soup.find_all(['div', 'a'], class_=lambda c: c and ('product' in c.lower() if c else False))
        for card in product_cards:
            link = card.get('href')
            if not link and card.name == 'div':
                link_tag = card.find('a')
                if link_tag:
                    link = link_tag.get('href')
            
            if link:
                abs_url = self._normalize_url(base_url, link)
                links.append(abs_url)
                
        return links
    
    def _normalize_url(self, base_url, href):
        """Normalize TataCliq URLs"""
        if href.startswith('//'):
            return f"https:{href}"
        if href.startswith('/'):
            domain = self.domain.rstrip('/')
            return f"{domain}{href}"
        if not href.startswith('http'):
            domain = self.domain.rstrip('/')
            return f"{domain}/{href.lstrip('/')}"
        return href
    
    def should_crawl(self, url: str) -> bool:
        """Override to add TataCliq-specific crawling rules"""
        # First apply the standard rules
        if not super().should_crawl(url):
            return False
        
        # TataCliq-specific exclusions
        excluded_paths = [
            '/login', 
            '/register', 
            '/wishlist', 
            '/cart',
            '/checkout',
            '/account',
            '/help',
            '/policy',
            '/about',
            '/terms',
            '/logout',
            '/customer-service'
        ]
        
        for path in excluded_paths:
            if path in url:
                return False
                
        return True