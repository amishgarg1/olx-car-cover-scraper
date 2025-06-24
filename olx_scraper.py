# olx_scraper.py - Enhanced version with all improvements
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import random
import argparse
import os
from urllib.parse import urljoin

class OLXScraper:
    """Enhanced OLX scraper with pagination, delays, and better error handling"""
    
    def __init__(self, base_url="https://www.olx.in", delay_range=(2, 5)):
        self.base_url = base_url
        self.delay_range = delay_range
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        
    def random_delay(self):
        """Add random delay between requests"""
        time.sleep(random.uniform(*self.delay_range))
        
    def get_page(self, url):
        """Fetch page with error handling"""
        self.random_delay()
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
            
    def scrape_listings(self, initial_url, max_pages=None):
        """
        Scrape listings with pagination support
        
        Args:
            initial_url (str): Starting URL for search
            max_pages (int): Maximum number of pages to scrape (None for all)
            
        Returns:
            list: Collection of scraped listings
        """
        listings = []
        current_url = initial_url
        page_count = 0
        
        while current_url and (max_pages is None or page_count < max_pages):
            print(f"Scraping page {page_count + 1}: {current_url}")
            response = self.get_page(current_url)
            
            if not response:
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            page_listings = self.parse_listings(soup)
            listings.extend(page_listings)
            
            # Find next page link if it exists
            next_page = soup.find('a', {'data-cy': 'page-link-next'})
            current_url = urljoin(self.base_url, next_page['href']) if next_page else None
            page_count += 1
            
        return listings
        
    def parse_listings(self, soup):
        """Parse listings from page HTML"""
        listings = []
        
        for item in soup.find_all('div', {'data-cy': 'l-card'}):
            try:
                title = item.find('h6').get_text(strip=True) if item.find('h6') else None
                price = item.find('p', {'data-testid': 'ad-price'}).get_text(strip=True) if item.find('p', {'data-testid': 'ad-price'}) else None
                location = item.find_all('p')[-1].get_text(strip=True) if item.find_all('p') else None
                url = urljoin(self.base_url, item.find('a')['href']) if item.find('a') else None
                image = item.find('img')['src'] if item.find('img') and 'src' in item.find('img').attrs else None
                time_posted = item.find('p', {'color': 'text-global-muted'}).get_text(strip=True) if item.find('p', {'color': 'text-global-muted'}) else None
                
                if not title:
                    continue
                    
                listings.append({
                    'title': title,
                    'price': price,
                    'location': location,
                    'url': url,
                    'image_url': image,
                    'time_posted': time_posted,
                    'scraped_at': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"Error parsing listing: {e}")
                continue
                
        return listings
        
    def save_results(self, data, filename, output_dir="results"):
        """Save results to JSON file"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filepath

def main():
    parser = argparse.ArgumentParser(description="OLX Car Covers Scraper")
    parser.add_argument('--query', default="car-cover", help="Search query for OLX")
    parser.add_argument('--pages', type=int, default=3, help="Maximum number of pages to scrape")
    parser.add_argument('--output', default="olx_car_covers.json", help="Output filename")
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = OLXScraper()
    
    # Build search URL
    search_url = f"https://www.olx.in/items/q-{args.query}"
    
    # Run scraping
    print(f"Starting OLX scrape for '{args.query}'")
    listings = scraper.scrape_listings(search_url, max_pages=args.pages)
    print(f"Found {len(listings)} listings")
    
    # Save results
    output_path = scraper.save_results(listings, args.output)
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()
