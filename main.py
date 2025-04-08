import asyncio
import argparse
import json
import logging
import os
from datetime import datetime, timezone
from crawler.base_crawler import Crawler
from crawler.site_specific.virgio_crawler import VirgioCrawler
from crawler.site_specific.tatacliq_crawler import TatacliqCrawler
from crawler.site_specific.nykaa_crawler import NykaaCrawler
from crawler.site_specific.westside_crawler import WestsideCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    parser = argparse.ArgumentParser(description='E-commerce product URL crawler')
    parser.add_argument('--domains', nargs='+', 
                        default=[
                            "https://www.virgio.com/",
                            "https://www.tatacliq.com/",
                            "https://nykaafashion.com/",
                            "https://www.westside.com/"
                        ],
                        help='List of domains to crawl')
    parser.add_argument('--output', default='output/product_urls.json', 
                        help='Output file path')
    parser.add_argument('--max-urls', type=int, default=1000, 
                        help='Maximum URLs to process per domain')
    parser.add_argument('--concurrency', type=int, default=5, 
                        help='Number of concurrent requests per domain')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Try to load existing results if available
    results = {}
    if os.path.exists(args.output):
        try:
            with open(args.output, 'r') as f:
                results = json.load(f)
            print(f"Loaded existing results from {args.output}")
        except json.JSONDecodeError:
            print(f"Could not parse existing file {args.output}, starting fresh")
    
    # Define site-specific crawlers
    crawler_map = {
        "https://www.virgio.com/": VirgioCrawler,
        "https://www.tatacliq.com/": TatacliqCrawler,
        "https://nykaafashion.com/": NykaaCrawler,
        "https://www.westside.com/": WestsideCrawler
    }
    
    # Add metadata to results
    if "metadata" not in results:
        results["metadata"] = {}
    
    results["metadata"]["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    results["metadata"]["total_domains"] = len(args.domains)
    
    for domain in args.domains:
        print(f"Starting crawl for: {domain}")
        
        # Use site-specific crawler if available, otherwise use base crawler
        crawler_class = crawler_map.get(domain, Crawler)
        crawler = crawler_class(domain, max_urls=args.max_urls, concurrency=args.concurrency)
        
        # Track start time for this domain
        start_time = datetime.now(timezone.utc)
        
        # Perform the crawl
        product_urls = await crawler.crawl()
        
        # Calculate duration
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Store results and metadata for this domain
        results[domain] = sorted(product_urls)
        
        # Update domain-specific metadata
        if "domain_metadata" not in results:
            results["domain_metadata"] = {}
        
        results["domain_metadata"][domain] = {
            "crawl_date": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "product_count": len(product_urls),
            "duration_seconds": duration
        }
        
        print(f"Found {len(product_urls)} product URLs for {domain} in {duration:.2f} seconds")
        
        # Save results incrementally after each domain
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Saved intermediate results to {args.output}")
    
    # Final update to metadata
    results["metadata"]["completion_time"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    results["metadata"]["total_products"] = sum(len(urls) for domain, urls in results.items() 
                                             if domain not in ["metadata", "domain_metadata"])
    
    # Save final results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Crawling complete. Final results saved to {args.output}")
    print(f"Total product URLs found: {results['metadata']['total_products']}")

if __name__ == "__main__":
    asyncio.run(main())