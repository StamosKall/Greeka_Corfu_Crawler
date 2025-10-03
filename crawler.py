#!/usr/bin/env python3
"""
Greeka Corfu Hotels Crawler

A web crawler that extracts hotel information from Greeka's Corfu hotels listing page.
Collects hotel details including name, rating, reviews, contact info, and coordinates.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import sys
from dataclasses import dataclass, asdict


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Hotel:
    """Data class to represent a hotel with all extracted information"""
    name: str = ""
    official_website: str = ""
    address: str = ""
    star_rating: str = ""
    review_score: str = ""
    number_of_reviews: str = ""
    phone_number: str = ""
    latitude: str = ""
    longitude: str = ""
    detail_url: str = ""


class GreekaHotelCrawler:
    """Main crawler class for extracting Greeka Corfu hotel data"""
    
    def __init__(self):
        self.base_url = "https://www.greeka.com"
        self.main_listing_url = "https://www.greeka.com/ionian/corfu/hotels/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.hotels: List[Hotel] = []
        
    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch a web page and return BeautifulSoup object
        
        Args:
            url: URL to fetch
            retries: Number of retry attempts
            
        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(retries):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Add delay to be respectful to the server
                time.sleep(1)
                
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.RequestException as e:
                logger.warning(f"Error fetching {url}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
                
        return None
    
    def extract_hotel_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract all hotel detail page links from the main listing page
        
        Args:
            soup: BeautifulSoup object of the main listing page
            
        Returns:
            List of hotel detail page URLs
        """
        hotel_links = []
        
        # Look for hotel links - these typically contain '/hotels/' in the path
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            
            # Check if this is a hotel detail link (exclude pagination and main listing)
            if ('/hotels/' in href and 
                href != '/ionian/corfu/hotels/' and 
                not href.endswith('/hotels/') and
                '/hotels/location-' in href):  # More specific filter for actual hotel pages
                
                # Convert relative URLs to absolute
                full_url = urljoin(self.base_url, href)
                
                # Avoid duplicates
                if full_url not in hotel_links:
                    hotel_links.append(full_url)
                    
        logger.info(f"Found {len(hotel_links)} hotel links on this page")
        return hotel_links
    
    def get_all_hotel_links(self) -> List[str]:
        """
        Get all hotel links from all pages (handle pagination)
        
        Returns:
            List of all hotel detail page URLs across all pages
        """
        all_hotel_links = []
        page_num = 1
        
        while True:
            if page_num == 1:
                page_url = self.main_listing_url
            else:
                page_url = f"{self.main_listing_url.rstrip('/')}/{page_num}/"
            
            logger.info(f"Fetching page {page_num}: {page_url}")
            soup = self.get_page(page_url)
            
            if not soup:
                logger.error(f"Failed to fetch page {page_num}")
                break
            
            # Extract hotel links from this page
            page_hotel_links = self.extract_hotel_links(soup)
            
            if not page_hotel_links:
                logger.info(f"No hotel links found on page {page_num}, stopping pagination")
                break
            
            # Add new links (avoid duplicates)
            new_links = [link for link in page_hotel_links if link not in all_hotel_links]
            all_hotel_links.extend(new_links)
            
            logger.info(f"Added {len(new_links)} new hotel links from page {page_num}")
            
            # Check if there's a next page
            next_page_links = soup.find_all('a', href=True)
            has_next_page = False
            
            for link in next_page_links:
                href = link.get('href', '')
                if f'/hotels/{page_num + 1}/' in href or f'page={page_num + 1}' in href:
                    has_next_page = True
                    break
            
            if not has_next_page:
                logger.info(f"No next page found after page {page_num}")
                break
                
            page_num += 1
            
            # Safety limit to prevent infinite loops
            if page_num > 20:
                logger.warning("Reached maximum page limit (20), stopping")
                break
        
        logger.info(f"Found total of {len(all_hotel_links)} unique hotel links across all pages")
        return all_hotel_links
    
    def convert_dms_to_decimal(self, dms_string: str) -> float:
        """
        Convert DMS (Degrees, Minutes, Seconds) format to decimal degrees
        Example: "39°40'22.7\"N" -> 39.672972
        """
        try:
            # Remove any extra spaces and normalize
            dms_string = dms_string.strip()
            
            # Pattern for DMS format like "39°40'22.7\"N" or "19°42'59.5\"E"
            dms_pattern = r"(\d+)°(\d+)'([\d.]+)\"([NSEW])"
            match = re.match(dms_pattern, dms_string)
            
            if match:
                degrees = int(match.group(1))
                minutes = int(match.group(2))
                seconds = float(match.group(3))
                direction = match.group(4)
                
                # Convert to decimal
                decimal = degrees + minutes/60 + seconds/3600
                
                # Apply direction (negative for South and West)
                if direction in ['S', 'W']:
                    decimal = -decimal
                
                return decimal
        except (ValueError, AttributeError):
            pass
        
        return None

    def extract_coordinates_from_map(self, soup: BeautifulSoup) -> tuple:
        """
        Extract latitude and longitude from map embed or JavaScript
        Enhanced to handle Greek coordinate formats and various map types
        
        Args:
            soup: BeautifulSoup object of hotel detail page
            
        Returns:
            Tuple of (latitude, longitude) or ("", "")
        """
        
        # Method 1: Look for DMS coordinates in text (like "39°40'22.7\"N 19°42'59.5\"E")
        page_text = soup.get_text()
        dms_pattern = r'(\d+°\d+[\'\u2032][\d.]+[\"\u2033][NS])\s+(\d+°\d+[\'\u2032][\d.]+[\"\u2033][EW])'
        dms_match = re.search(dms_pattern, page_text)
        
        if dms_match:
            lat_dms = dms_match.group(1)
            lon_dms = dms_match.group(2)
            
            # Convert DMS to decimal
            lat_decimal = self.convert_dms_to_decimal(lat_dms)
            lon_decimal = self.convert_dms_to_decimal(lon_dms)
            
            if lat_decimal is not None and lon_decimal is not None:
                logger.info(f"Found DMS coordinates: {lat_dms} {lon_dms} -> {lat_decimal}, {lon_decimal}")
                return str(lat_decimal), str(lon_decimal)
        
        # Method 2: Look for coordinates in coordinate display elements
        coord_elements = soup.find_all(['div', 'span', 'p'], string=re.compile(r'\d+°\d+'))
        for element in coord_elements:
            text = element.get_text()
            dms_match = re.search(dms_pattern, text)
            if dms_match:
                lat_dms = dms_match.group(1)
                lon_dms = dms_match.group(2)
                
                lat_decimal = self.convert_dms_to_decimal(lat_dms)
                lon_decimal = self.convert_dms_to_decimal(lon_dms)
                
                if lat_decimal is not None and lon_decimal is not None:
                    return str(lat_decimal), str(lon_decimal)
        
        # Method 3: Look for Google Maps iframe
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            
            if 'google.com/maps' in src or 'maps.google' in src:
                # Extract coordinates from Google Maps URL
                coord_patterns = [
                    r'[?&]q=([0-9.-]+),([0-9.-]+)',  # ?q=lat,lon
                    r'!2d([0-9.-]+)!3d([0-9.-]+)',   # !2dlon!3dlat
                    r'center=([0-9.-]+),([0-9.-]+)', # center=lat,lon
                    r'[?&]ll=([0-9.-]+),([0-9.-]+)', # ?ll=lat,lon
                    r'@([0-9.-]+),([0-9.-]+)',       # @lat,lon
                ]
                
                for pattern in coord_patterns:
                    coord_match = re.search(pattern, src)
                    if coord_match:
                        if '!2d' in pattern:  # This pattern is lon,lat
                            return coord_match.group(2), coord_match.group(1)
                        else:  # Other patterns are lat,lon
                            return coord_match.group(1), coord_match.group(2)
        
        # Method 4: Look for coordinates in JavaScript variables and JSON-LD
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                script_content = script.string
                
                # First check for JSON-LD structured data (most reliable)
                if '"@type":"GeoCoordinates"' in script_content:
                    lat_match = re.search(r'"latitude"\s*:\s*"([0-9.-]+)"', script_content)
                    lng_match = re.search(r'"longitude"\s*:\s*"([0-9.-]+)"', script_content)
                    if lat_match and lng_match:
                        logger.info("Found coordinates in JSON-LD structured data")
                        return lat_match.group(1), lng_match.group(1)
                
                # Check for locationData array pattern
                if 'locationData' in script_content and '$(' in script_content:
                    # Look for patterns like: locationData[0] and locationData[1]
                    # This suggests coordinates are stored in a data attribute
                    pass  # Will be handled by data attribute method
                
                # Look for various coordinate patterns in JS
                patterns = [
                    r'lat["\']?\s*[:=]\s*([0-9.-]+)',
                    r'lng["\']?\s*[:=]\s*([0-9.-]+)',
                    r'latitude["\']?\s*[:=]\s*([0-9.-]+)',
                    r'longitude["\']?\s*[:=]\s*([0-9.-]+)',
                    r'center\s*[:=]\s*\[\s*([0-9.-]+)\s*,\s*([0-9.-]+)\s*\]',  # center: [lat, lon]
                    r'LatLng\s*\(\s*([0-9.-]+)\s*,\s*([0-9.-]+)\s*\)',  # LatLng(lat, lon)
                ]
                
                # Try center pattern first (most reliable)
                center_match = re.search(patterns[4], script_content)
                if center_match:
                    return center_match.group(1), center_match.group(2)
                
                latlng_match = re.search(patterns[5], script_content)
                if latlng_match:
                    return latlng_match.group(1), latlng_match.group(2)
                
                # Try individual lat/lng patterns
                lat_match = re.search(patterns[0] + '|' + patterns[2], script_content)
                lng_match = re.search(patterns[1] + '|' + patterns[3], script_content)
                
                if lat_match and lng_match:
                    lat = lat_match.group(1) if lat_match.group(1) else lat_match.group(2)
                    lng = lng_match.group(1) if lng_match.group(1) else lng_match.group(2)
                    if lat and lng:
                        return lat, lng
        
        # Method 5: Look for coordinates in data attributes
        elements_with_coords = soup.find_all(attrs={'data-lat': True, 'data-lng': True})
        for element in elements_with_coords:
            lat = element.get('data-lat')
            lng = element.get('data-lng')
            if lat and lng:
                return lat, lng
        
        # Look for data-map attribute (Greeka specific)
        map_elements = soup.find_all(attrs={'data-map': True})
        for element in map_elements:
            data_map = element.get('data-map')
            if data_map:
                try:
                    # data-map might be a JSON array like "[lat, lng]"
                    import json
                    coords = json.loads(data_map)
                    if isinstance(coords, list) and len(coords) >= 2:
                        return str(coords[0]), str(coords[1])
                except (json.JSONDecodeError, ValueError):
                    # Try parsing as comma-separated values
                    if ',' in data_map:
                        parts = data_map.split(',')
                        if len(parts) >= 2:
                            try:
                                lat = float(parts[0].strip())
                                lng = float(parts[1].strip())
                                return str(lat), str(lng)
                            except ValueError:
                                pass
        
        # Method 6: Look for coordinates in meta tags
        meta_tags = soup.find_all('meta', attrs={'property': re.compile(r'geo|location', re.I)})
        for meta in meta_tags:
            content = meta.get('content', '')
            coord_match = re.search(r'([0-9.-]+),\s*([0-9.-]+)', content)
            if coord_match:
                return coord_match.group(1), coord_match.group(2)
        
        # Method 7: Look in all script tags for any coordinate-like patterns
        for script in scripts:
            if script.string:
                # Look for any decimal coordinate patterns (lat/lon for Corfu area)
                # Corfu is approximately: Lat 39.6-39.8, Lon 19.6-20.2
                corfu_coord_pattern = r'(39\.[0-9]+)[,\s]+(19\.[0-9]+|20\.[0-9]+)'
                coord_match = re.search(corfu_coord_pattern, script.string)
                if coord_match:
                    return coord_match.group(1), coord_match.group(2)
        
        return "", ""
    
    def extract_hotel_details(self, soup: BeautifulSoup, url: str) -> Hotel:
        """
        Extract hotel details from a hotel detail page
        
        Args:
            soup: BeautifulSoup object of hotel detail page
            url: URL of the hotel detail page
            
        Returns:
            Hotel object with extracted data
        """
        hotel = Hotel(detail_url=url)
        
        try:
            # Extract hotel name - usually in h1 or title
            name_element = soup.find('h1') or soup.find('title')
            if name_element:
                hotel.name = name_element.get_text(strip=True)
                # Clean up title tags
                if 'title' in name_element.name.lower():
                    hotel.name = re.sub(r'\s*-\s*Greeka.*', '', hotel.name)
            
            # Extract star rating - look for star symbols or rating indicators
            star_elements = soup.find_all(['span', 'div'], class_=re.compile(r'star|rating', re.I))
            for element in star_elements:
                text = element.get_text(strip=True)
                star_match = re.search(r'(\d+)\s*star', text, re.I)
                if star_match:
                    hotel.star_rating = star_match.group(1)
                    break
            
            # Look for star symbols (★)
            if not hotel.star_rating:
                star_text = soup.get_text()
                star_count = star_text.count('★')
                if star_count > 0:
                    hotel.star_rating = str(star_count)
            
            # Extract review score and number of reviews
            review_elements = soup.find_all(['span', 'div'], string=re.compile(r'\d+(\.\d+)?\s*/\s*[5|10]'))
            for element in review_elements:
                text = element.get_text(strip=True)
                score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*([5|10])', text)
                if score_match:
                    score = float(score_match.group(1))
                    scale = int(score_match.group(2))
                    # Normalize to 5-point scale
                    if scale == 10:
                        score = score / 2
                    hotel.review_score = f"{score:.1f}"
                    break
            
            # Extract number of reviews
            review_count_elements = soup.find_all(['span', 'div'], string=re.compile(r'\d+\s*(review|rating)', re.I))
            for element in review_count_elements:
                text = element.get_text(strip=True)
                count_match = re.search(r'(\d+)', text)
                if count_match:
                    hotel.number_of_reviews = count_match.group(1)
                    break
            
            # Extract phone number
            phone_elements = soup.find_all(['a', 'span', 'div'], href=re.compile(r'^tel:'))
            for element in phone_elements:
                if element.name == 'a':
                    phone = element.get('href', '').replace('tel:', '')
                else:
                    phone = element.get_text(strip=True)
                
                if phone:
                    hotel.phone_number = phone
                    break
            
            # Also look for phone numbers in text
            if not hotel.phone_number:
                phone_patterns = [
                    r'(?:tel|phone)[:\s]*([+]?[\d\s\-\(\)]+)',
                    r'([+]?[\d\s\-\(\)]{10,})',  # Generic phone pattern
                ]
                
                text_content = soup.get_text()
                for pattern in phone_patterns:
                    phone_match = re.search(pattern, text_content, re.I)
                    if phone_match:
                        phone = re.sub(r'[^\d+\-\(\)\s]', '', phone_match.group(1))
                        if len(phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 10:
                            hotel.phone_number = phone.strip()
                            break
            
            # Extract official website
            website_links = soup.find_all('a', href=True)
            for link in website_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # Skip Greeka's own links and common non-hotel sites
                if (href.startswith('http') and 
                    'greeka.com' not in href and 
                    any(keyword in text for keyword in ['website', 'official', 'visit', 'book']) and
                    not any(skip in href for skip in ['facebook', 'twitter', 'instagram', 'booking.com', 'tripadvisor'])):
                    hotel.official_website = href
                    break
            
            # Extract address/location
            address_selectors = [
                '[class*="address"]', '[class*="location"]', '[class*="contact"]',
                '[id*="address"]', '[id*="location"]'
            ]
            
            for selector in address_selectors:
                address_element = soup.select_one(selector)
                if address_element:
                    address_text = address_element.get_text(strip=True)
                    if len(address_text) > 10:  # Reasonable address length
                        hotel.address = address_text
                        break
            
            # If no address found, look for location in text content
            if not hotel.address:
                # Look for common Greek location patterns
                text_content = soup.get_text()
                location_match = re.search(r'(Corfu[^.]*(?:Greece|Kerkyra)[^.]*)', text_content, re.I)
                if location_match:
                    hotel.address = location_match.group(1).strip()
            
            # Extract coordinates
            hotel.latitude, hotel.longitude = self.extract_coordinates_from_map(soup)
            
            logger.info(f"Extracted details for: {hotel.name}")
            
        except Exception as e:
            logger.error(f"Error extracting details from {url}: {e}")
        
        return hotel
    
    def crawl_hotels(self):
        """Main crawling method that orchestrates the entire process"""
        logger.info("Starting Greeka Corfu hotels crawling...")
        
        # Step 1: Get all hotel links from all pages (with pagination)
        logger.info("Extracting hotel links from all pages...")
        hotel_links = self.get_all_hotel_links()
        
        if not hotel_links:
            logger.warning("No hotel links found")
            return
        
        # Step 2: Process each hotel
        logger.info(f"Processing {len(hotel_links)} hotels...")
        
        for i, hotel_url in enumerate(hotel_links, 1):
            logger.info(f"Processing hotel {i}/{len(hotel_links)}: {hotel_url}")
            
            hotel_soup = self.get_page(hotel_url)
            if hotel_soup:
                hotel = self.extract_hotel_details(hotel_soup, hotel_url)
                self.hotels.append(hotel)
                
                # Log coordinate extraction success
                if hotel.latitude and hotel.longitude:
                    logger.info(f"[OK] Coordinates found: {hotel.latitude}, {hotel.longitude}")
                else:
                    logger.warning(f"[MISSING] No coordinates found for: {hotel.name}")
            else:
                logger.warning(f"Skipping hotel due to fetch failure: {hotel_url}")
            
            # Add delay between requests to be respectful
            time.sleep(2)
        
        logger.info(f"Crawling completed. Extracted {len(self.hotels)} hotels.")
    
    def save_to_csv(self, filename: str = "hotels.csv"):
        """Save hotel data to CSV file"""
        if not self.hotels:
            logger.warning("No hotel data to save")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'name', 'official_website', 'address', 'star_rating',
                    'review_score', 'number_of_reviews', 'phone_number',
                    'latitude', 'longitude', 'detail_url'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for hotel in self.hotels:
                    writer.writerow(asdict(hotel))
            
            logger.info(f"Hotel data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def save_to_json(self, filename: str = "hotels.json"):
        """Save hotel data to JSON file"""
        if not self.hotels:
            logger.warning("No hotel data to save")
            return
        
        try:
            hotel_data = [asdict(hotel) for hotel in self.hotels]
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(hotel_data, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"Hotel data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def print_summary(self):
        """Print a summary of the crawled data"""
        if not self.hotels:
            print("No hotels found.")
            return
        
        print(f"\n=== CRAWLING SUMMARY ===")
        print(f"Total hotels found: {len(self.hotels)}")
        
        # Count fields with data
        fields_with_data = {
            'name': sum(1 for h in self.hotels if h.name),
            'official_website': sum(1 for h in self.hotels if h.official_website),
            'address': sum(1 for h in self.hotels if h.address),
            'star_rating': sum(1 for h in self.hotels if h.star_rating),
            'review_score': sum(1 for h in self.hotels if h.review_score),
            'number_of_reviews': sum(1 for h in self.hotels if h.number_of_reviews),
            'phone_number': sum(1 for h in self.hotels if h.phone_number),
            'coordinates': sum(1 for h in self.hotels if h.latitude and h.longitude),
        }
        
        print("\nData completeness:")
        for field, count in fields_with_data.items():
            percentage = (count / len(self.hotels)) * 100
            print(f"  {field}: {count}/{len(self.hotels)} ({percentage:.1f}%)")
        
        print("\nSample hotels:")
        for i, hotel in enumerate(self.hotels[:3]):
            print(f"  {i+1}. {hotel.name or 'Unknown'}")
            if hotel.star_rating:
                print(f"     Rating: {hotel.star_rating} stars")
            if hotel.review_score:
                print(f"     Reviews: {hotel.review_score}/5")
            if hotel.address:
                print(f"     Location: {hotel.address[:50]}...")


def main():
    """Main function to run the crawler"""
    crawler = GreekaHotelCrawler()
    
    try:
        # Run the crawling process
        crawler.crawl_hotels()
        
        # Save results
        crawler.save_to_csv()
        crawler.save_to_json()
        
        # Print summary
        crawler.print_summary()
        
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()