#!/usr/bin/env python3
"""
Website Detection Script for Greeka Corfu Hotels
This script revisits all hotel pages to find official websites that might have been missed.
"""

import json
import requests
from bs4 import BeautifulSoup
import time
import logging
import re
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Optional
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../data/website_detection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebsiteDetector:
    """Detects official websites from hotel pages"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.found_websites = 0
        self.updated_hotels = []
        
    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch a web page and return BeautifulSoup object"""
        for attempt in range(retries):
            try:
                logger.debug(f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                time.sleep(1)  # Be respectful
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.RequestException as e:
                logger.warning(f"Error fetching {url}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
                time.sleep(2 ** attempt)
                
        return None
    
    def is_valid_hotel_website(self, url: str, hotel_name: str = "") -> bool:
        """
        Check if a URL is likely a valid hotel website
        """
        if not url or not url.startswith(('http://', 'https://')):
            return False
            
        # Parse URL
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
        except:
            return False
        
        # Skip common non-hotel sites
        skip_domains = [
            'greeka.com', 'booking.com', 'tripadvisor.com', 'expedia.com',
            'hotels.com', 'agoda.com', 'airbnb.com', 'hostelworld.com',
            'facebook.com', 'instagram.com', 'twitter.com', 'youtube.com',
            'google.com', 'maps.google.com', 'gmail.com', 'yahoo.com',
            'wikipedia.org', 'wikitravel.org', 'foursquare.com',
            'yelp.com', 'zomato.com', 'opentable.com'
        ]
        
        for skip_domain in skip_domains:
            if skip_domain in domain:
                return False
        
        # Skip URLs that look like booking/review platforms
        booking_patterns = [
            'book', 'reservation', 'reserve', 'availability', 'rates',
            'review', 'rating', 'compare', 'search', 'find'
        ]
        
        for pattern in booking_patterns:
            if pattern in domain and any(platform in domain for platform in ['booking', 'travel', 'hotel', 'reservation']):
                return False
        
        # Positive indicators for hotel websites
        hotel_indicators = [
            # Domain indicators
            'hotel', 'resort', 'villa', 'apartment', 'studios', 'rooms',
            'accommodation', 'lodge', 'inn', 'suites', 'boutique',
            # Greek hotel indicators
            'xenodoxeio', 'diamerisma', 'villa', 'studios'
        ]
        
        # Check domain for hotel indicators
        domain_score = sum(1 for indicator in hotel_indicators if indicator in domain)
        
        # Check if hotel name keywords appear in domain (if we have the hotel name)
        name_score = 0
        if hotel_name:
            # Extract meaningful words from hotel name
            name_words = re.findall(r'\b\w{4,}\b', hotel_name.lower())
            name_words = [w for w in name_words if w not in ['hotel', 'apartments', 'corfu', 'studios', 'rooms']]
            
            for word in name_words:
                if word in domain:
                    name_score += 2  # Strong indicator
        
        # Score the URL
        total_score = domain_score + name_score
        
        # Additional checks for likely hotel websites
        if any(ext in domain for ext in ['.gr', '.com', '.eu', '.net']):
            total_score += 1
        
        logger.debug(f"URL scoring: {url} -> domain_score={domain_score}, name_score={name_score}, total={total_score}")
        
        return total_score >= 2
    
    def extract_websites_from_page(self, soup: BeautifulSoup, hotel_name: str = "") -> List[str]:
        """
        Extract potential hotel websites from a page
        """
        websites = []
        
        # Method 1: Look for links with website-related text
        website_keywords = [
            'official website', 'hotel website', 'website', 'official site',
            'visit website', 'book direct', 'direct booking', 'hotel site',
            'official page', 'home page', 'main site', 'book online',
            # Greek keywords
            'επισημο site', 'ιστοσελιδα', 'κρατηση'
        ]
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').strip()
            text = link.get_text(strip=True).lower()
            title = link.get('title', '').lower()
            
            # Skip if no href
            if not href:
                continue
                
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin('https://www.greeka.com', href)
            
            # Check if link text suggests it's a hotel website
            is_website_link = any(keyword in text for keyword in website_keywords)
            is_website_title = any(keyword in title for keyword in website_keywords)
            
            if is_website_link or is_website_title:
                if self.is_valid_hotel_website(href, hotel_name):
                    websites.append(href)
                    logger.info(f"Found website link by text: {href} (text: '{text}')")
        
        # Method 2: Look for websites in structured data (JSON-LD)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Look for website/URL fields
                    url_fields = ['url', 'sameAs', 'website']
                    for field in url_fields:
                        if field in data:
                            url_value = data[field]
                            if isinstance(url_value, str):
                                if self.is_valid_hotel_website(url_value, hotel_name):
                                    websites.append(url_value)
                                    logger.info(f"Found website in JSON-LD {field}: {url_value}")
                            elif isinstance(url_value, list):
                                for url in url_value:
                                    if isinstance(url, str) and self.is_valid_hotel_website(url, hotel_name):
                                        websites.append(url)
                                        logger.info(f"Found website in JSON-LD {field} array: {url}")
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Method 3: Look for contact sections with website links
        contact_sections = soup.find_all(['div', 'section'], class_=re.compile(r'contact|info|details', re.I))
        for section in contact_sections:
            section_links = section.find_all('a', href=True)
            for link in section_links:
                href = link.get('href', '').strip()
                if href and href.startswith(('http://', 'https://')):
                    if self.is_valid_hotel_website(href, hotel_name):
                        websites.append(href)
                        logger.info(f"Found website in contact section: {href}")
        
        # Method 4: Look for external links that might be hotel websites
        external_links = []
        for link in links:
            href = link.get('href', '').strip()
            if href and href.startswith(('http://', 'https://')) and 'greeka.com' not in href:
                external_links.append(href)
        
        # Score external links
        for href in external_links:
            if self.is_valid_hotel_website(href, hotel_name):
                websites.append(href)
                logger.debug(f"Found potential website: {href}")
        
        # Remove duplicates and return
        return list(set(websites))
    
    def detect_websites_for_hotel(self, hotel: Dict) -> Optional[str]:
        """
        Detect website for a single hotel
        """
        hotel_name = hotel.get('name', '')
        detail_url = hotel.get('detail_url', '')
        
        if not detail_url:
            logger.warning(f"No detail URL for hotel: {hotel_name}")
            return None
        
        logger.info(f"Checking website for: {hotel_name}")
        
        # Get the hotel page
        soup = self.get_page(detail_url)
        if not soup:
            logger.warning(f"Could not fetch page for: {hotel_name}")
            return None
        
        # Extract potential websites
        websites = self.extract_websites_from_page(soup, hotel_name)
        
        if websites:
            # Return the first (most likely) website
            website = websites[0]
            logger.info(f"✓ Found website for {hotel_name}: {website}")
            return website
        else:
            logger.info(f"✗ No website found for: {hotel_name}")
            return None
    
    def update_hotel_websites(self, input_file: str = "../data/hotels.json", output_file: str = "../data/hotels_updated.json"):
        """
        Update hotel data with detected websites
        """
        # Load existing hotel data
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                hotels = json.load(f)
        except FileNotFoundError:
            logger.error(f"File {input_file} not found. Please run the crawler first.")
            return
        
        logger.info(f"Starting website detection for {len(hotels)} hotels...")
        
        # Track statistics
        hotels_with_existing_websites = sum(1 for h in hotels if h.get('official_website'))
        hotels_without_websites = [h for h in hotels if not h.get('official_website')]
        
        logger.info(f"Hotels with existing websites: {hotels_with_existing_websites}")
        logger.info(f"Hotels without websites: {len(hotels_without_websites)}")
        
        # Process hotels without websites
        for i, hotel in enumerate(hotels_without_websites, 1):
            logger.info(f"Processing hotel {i}/{len(hotels_without_websites)}: {hotel.get('name', 'Unknown')}")
            
            website = self.detect_websites_for_hotel(hotel)
            
            if website:
                # Find the hotel in the original list and update it
                for original_hotel in hotels:
                    if original_hotel.get('detail_url') == hotel.get('detail_url'):
                        original_hotel['official_website'] = website
                        self.updated_hotels.append(original_hotel)
                        self.found_websites += 1
                        break
            
            # Add delay between requests
            time.sleep(2)
        
        # Save updated data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hotels, f, indent=2, ensure_ascii=False)
        
        # Also update the original CSV file
        self.save_to_csv(hotels, "../data/hotels_updated.csv")
        
        # Print summary
        self.print_summary(hotels)
        
        return hotels
    
    def save_to_csv(self, hotels: List[Dict], filename: str):
        """Save updated data to CSV"""
        import csv
        
        fieldnames = [
            'name', 'official_website', 'address', 'star_rating',
            'review_score', 'number_of_reviews', 'phone_number',
            'latitude', 'longitude', 'detail_url'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for hotel in hotels:
                    row = {field: hotel.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            logger.info(f"Updated CSV data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
    
    def print_summary(self, hotels: List[Dict]):
        """Print detection summary"""
        total_hotels = len(hotels)
        hotels_with_websites = sum(1 for h in hotels if h.get('official_website'))
        
        print(f"\n=== WEBSITE DETECTION SUMMARY ===")
        print(f"Total hotels processed: {total_hotels}")
        print(f"Websites found in this run: {self.found_websites}")
        print(f"Total hotels with websites: {hotels_with_websites}/{total_hotels} ({hotels_with_websites/total_hotels*100:.1f}%)")
        
        if self.updated_hotels:
            print(f"\nNewly found websites:")
            for hotel in self.updated_hotels:
                print(f"  ✓ {hotel['name']}")
                print(f"    Website: {hotel['official_website']}")
                print(f"    URL: {hotel['detail_url']}")
                print()

def main():
    """Main function"""
    detector = WebsiteDetector()
    
    try:
        updated_hotels = detector.update_hotel_websites()
        
        if updated_hotels:
            print(f"\n🎉 Website detection completed!")
            print(f"📁 Updated files created:")
            print(f"   - data/hotels_updated.json")
            print(f"   - data/hotels_updated.csv") 
            print(f"📊 Check data/website_detection.log for detailed logs")
        
    except KeyboardInterrupt:
        logger.info("Website detection interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()