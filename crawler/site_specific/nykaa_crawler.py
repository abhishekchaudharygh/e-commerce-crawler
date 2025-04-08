from crawler.base_crawler import Crawler
import re
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse

class NykaaCrawler(Crawler):
    """Site-specific crawler for nykaafashion.com"""
    
    def __init__(self, domain, max_urls=1000, concurrency=5):
        super().__init__(domain, max_urls, concurrency)
        # Updated Nykaa-specific product patterns
        self.nykaa_product_patterns = [
            r'/prod/',             # Common product pattern
            r'/products/',         # Products path
            r'productId=',         # Product ID query parameter
            r'/p/\d+',             # Product with numeric ID
            r'/fashion/[^/]+/p/',  # Category path structure leading to product
            r'-p\d+$',             # Product ID at end of URL
        ]
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def process_url(self, session, url: str):
        """Override to add site-specific logic for Nykaa Fashion"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"Got status {response.status} for {url}")
                    return
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Nykaa-specific product URL detection based on URL pattern
                for pattern in self.nykaa_product_patterns:
                    if re.search(pattern, url):
                        self.logger.info(f"Nykaa Fashion product detected via pattern: {url}")
                        self.product_urls.add(url)
                        break
                
                # Check for product page indicators in content
                if self._is_product_page(soup, html):
                    self.logger.info(f"Nykaa Fashion product detected via content: {url}")
                    self.product_urls.add(url)
                
                # Extract all links for further crawling
                links = self.extract_links(soup, url)
                for link in links:
                    if self.should_crawl(link):
                        self.frontier.add(link)
        
        except Exception as e:
            self.logger.error(f"Error processing {url}: {str(e)}")
    
    def _is_product_page(self, soup, html):
        """Determine if the page is a product page based on content"""
        # Check for add to bag/cart buttons
        add_buttons = soup.find_all(['button', 'a'], 
                                 string=lambda s: s and ('add to' in s.lower() if s else False))
        if add_buttons:
            return True
        
        # Check for price elements
        price_elements = soup.find_all(['div', 'span'], 
                                    attrs={'class': lambda c: c and 
                                          ('price' in c.lower() or 'mrp' in c.lower() if c else False)})
        if len(price_elements) > 1:
            return True
        
        # Check for size selectors (common on product pages)
        size_selectors = soup.find_all(['div', 'ul'], 
                                    attrs={'class': lambda c: c and 
                                          ('size' in c.lower() if c else False)})
        if size_selectors:
            return True
            
        # Check for product schema
        if 'itemprop="product"' in html or '"@type":"Product"' in html:
            return True
            
        return False
    
    def extract_links(self, soup: BeautifulSoup, base_url: str):
        """Override to handle Nykaa-specific link extraction"""
        links = super().extract_links(soup, base_url)
        
        # For Nykaa, also extract product links from their catalog grid
        # Get all product cards/tiles from various possible class names
        product_elements = soup.find_all(['div', 'li', 'article'], class_=lambda c: c and any(
            term in (c.lower() if c else '') for term in 
            ['product-card', 'plp-card', 'product-tile', 'product-box', 'product-item']
        ))
        
        for element in product_elements:
            # Try to find link elements within the product card
            link_tag = element.find('a')
            if link_tag and link_tag.get('href'):
                href = link_tag['href']
                absolute_url = self._normalize_url(base_url, href)
                links.append(absolute_url)
                
            # Sometimes links are stored in data attributes
            for attr in ['data-url', 'data-href', 'data-product-url']:
                if element.has_attr(attr):
                    href = element[attr]
                    absolute_url = self._normalize_url(base_url, href)
                    links.append(absolute_url)
        
        return links
    
    def _normalize_url(self, base_url: str, href: str):
        """Normalize Nykaa URLs which might have special formats"""
        if not href:
            return None
            
        if href.startswith('//'):
            return f"https:{href}"
            
        if href.startswith('/'):
            parsed_base = urlparse(base_url)
            domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
            return f"{domain}{href}"
            
        if not href.startswith('http'):
            return urljoin(base_url, href)
            
        return href
    
    def should_crawl(self, url: str) -> bool:
        """Override to add Nykaa-specific crawling rules"""
        # First apply the standard rules
        if not url or not super().should_crawl(url):
            return False
        
        # Nykaa-specific exclusions
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
            '/customer-service',
            '/privacy'
        ]
        
        for path in excluded_paths:
            if path in url:
                return False
        
        # Prioritize category and product pages
        priority_paths = [
            '/category/',
            '/products/',
            '/fashion/',
            '/prod/',
            '/collection/',
            '/brands/'
        ]
        
        for path in priority_paths:
            if path in url:
                return True
                
        return True