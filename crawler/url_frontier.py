from collections import deque
from typing import Set

class URLFrontier:
    """Manages the queue of URLs to be crawled and ensures uniqueness"""
    
    def __init__(self):
        self.queue = deque()
        self.seen_urls = set()
    
    def add(self, url: str):
        """Add a URL to the frontier if not already seen"""
        # Normalize URL by removing trailing slash if present
        normalized_url = url.rstrip('/')
        
        if normalized_url not in self.seen_urls:
            self.queue.append(normalized_url)
            self.seen_urls.add(normalized_url)
    
    def get(self) -> str:
        """Get the next URL from the frontier"""
        return self.queue.popleft()
    
    def is_empty(self) -> bool:
        """Check if the frontier is empty"""
        return len(self.queue) == 0
    
    def size(self) -> int:
        """Get the number of URLs in the queue"""
        return len(self.queue)