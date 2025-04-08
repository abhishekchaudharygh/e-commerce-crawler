from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs

class ProductIdentifier:
    """Identifies if a URL is a product page using multiple heuristics"""
    
    def __init__(self):
        # Common URL patterns for product pages
        self.product_url_patterns = [
            r'/product/',
            r'/p/',
            r'/item/',
            r'/products/',
            r'/pd/',
            r'/buy/',
            r'/shop/'
        ]
        
        # Common query parameters for product identification
        self.product_query_params = [
            'product',
            'productId',
            'pid',
            'itemId',
            'sku',
            'productCode'
        ]
        
        # Elements that commonly appear on product pages
        self.product_indicators = [
            'add to cart',
            'add to bag',
            'buy now',
            'product details',
            'product description',
            'specifications',
            'shipping',
            'size chart'
        ]
    
    def is_product_page(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        """
        Determine if the given URL and content represent a product page
        using multiple identification methods
        """
        # Method 1: URL pattern analysis
        if self._check_url_pattern(url):
            return True
        
        # Method 2: HTML content analysis
        if self._check_page_content(html, soup):
            return True
        
        # Method 3: Schema.org and metadata analysis
        if self._check_metadata(soup):
            return True
            
        return False
    
    def _check_url_pattern(self, url: str) -> bool:
        """Check if URL matches common product URL patterns"""
        # Check URL path patterns
        for pattern in self.product_url_patterns:
            if re.search(pattern, url):
                return True
        
        # Check URL query parameters
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        for param in self.product_query_params:
            if param in query_params:
                return True
        
        return False
    
    def _check_page_content(self, html: str, soup: BeautifulSoup) -> bool:
        """Analyze page content for product indicators"""
        # Convert to lowercase for case-insensitive matching
        html_lower = html.lower()
        
        # Check for product indicators in text
        indicator_count = 0
        for indicator in self.product_indicators:
            if indicator in html_lower:
                indicator_count += 1
                
                # If we find multiple indicators, it's likely a product page
                if indicator_count >= 2:
                    return True
        
        # Look for price elements
        price_elements = soup.find_all(['span', 'div', 'p'], 
                                      attrs={'class': re.compile(r'price|cost|mrp|amount', re.I)})
        if price_elements and indicator_count > 0:
            return True
            
        # Look for quantity selectors or size options
        qty_elements = soup.find_all(['select', 'input', 'div'], 
                                   attrs={'class': re.compile(r'qty|quantity|size|option', re.I)})
        if qty_elements and indicator_count > 0:
            return True
            
        return False
    
    def _check_metadata(self, soup: BeautifulSoup) -> bool:
        """Check for product metadata and schema.org markup"""
        # Check for schema.org Product type
        schema = soup.find('script', type='application/ld+json')
        if schema and schema.string and '"@type"' in schema.string:
            if '"Product"' in schema.string or '"product"' in schema.string.lower():
                return True
        
        # Check Open Graph meta tags
        og_type = soup.find('meta', {'property': 'og:type'})
        if og_type and og_type.get('content') == 'product':
            return True
            
        # Check product-related meta tags
        product_meta_tags = soup.find_all('meta', {'property': re.compile(r'product:|og:price')})
        if product_meta_tags:
            return True
            
        return False