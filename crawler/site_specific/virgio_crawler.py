from crawler.base_crawler import Crawler
import re
from bs4 import BeautifulSoup

class VirgioCrawler(Crawler):
    """Site-specific crawler for virgio.com"""
    
    async def process_url(self, session, url: str):
        """Override to add site-specific logic for Virgio"""
        await super().process_url(session, url)
        
        # Additional site-specific product detection for Virgio
        if re.search(r'/collection/|/category/', url) and re.search(r'-p\d+$', url):
            self.product_urls.add(url)