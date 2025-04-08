# E-commerce Product URL Crawler

A scalable and robust web crawler designed to discover product URLs across various e-commerce websites.

## Project Overview

This project implements an asynchronous web crawler that efficiently discovers product URLs on e-commerce websites. The crawler uses multiple intelligent heuristics to identify product pages and can handle differences in URL structures across different platforms.

### Features

- **Multi-domain Support**: Process multiple e-commerce domains with a single command
- **Asynchronous Processing**: Utilizes async/await for high-performance crawling
- **Intelligent Product Detection**: Uses multiple strategies to identify product pages
- **Site-specific Customization**: Custom crawlers for specific e-commerce platforms
- **Incremental Saving**: Saves results after each domain to prevent data loss
- **Detailed Metadata**: Tracks performance metrics and crawl statistics
- **SSL Verification Options**: Flexible SSL certificate verification for different environments
- **Robust Error Handling**: Continues crawling even when errors are encountered

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/am-agrawal/ecommerce-product-crawler.git
cd ecommerce-product-crawler

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
