#!/usr/bin/env python3
"""
Test script to extract data from a single hotel page for debugging purposes.
"""

import sys
from crawler import GreekaHotelCrawler
import json

def test_single_hotel(url: str):
    """Test extraction from a single hotel URL"""
    crawler = GreekaHotelCrawler()
    
    print(f"Testing URL: {url}")
    print("=" * 50)
    
    # Fetch the page
    soup = crawler.get_page(url)
    if not soup:
        print("Failed to fetch the page")
        return
    
    # Extract hotel details
    hotel = crawler.extract_hotel_details(soup, url)
    
    # Print results
    print(f"Name: {hotel.name}")
    print(f"Official Website: {hotel.official_website}")
    print(f"Address: {hotel.address}")
    print(f"Star Rating: {hotel.star_rating}")
    print(f"Review Score: {hotel.review_score}")
    print(f"Number of Reviews: {hotel.number_of_reviews}")
    print(f"Phone Number: {hotel.phone_number}")
    print(f"Latitude: {hotel.latitude}")
    print(f"Longitude: {hotel.longitude}")
    print(f"Detail URL: {hotel.detail_url}")
    
    # Save as JSON for detailed inspection
    import json
    from dataclasses import asdict
    
    with open('test_hotel.json', 'w', encoding='utf-8') as f:
        json.dump(asdict(hotel), f, indent=2, ensure_ascii=False)
    
    print("\nDetails saved to test_hotel.json")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_single_hotel.py <hotel_url>")
        print("Example: python test_single_hotel.py https://www.greeka.com/ionian/corfu/hotels/location-agios-stefanos-avliotes/delfino-blu/")
        sys.exit(1)
    
    test_single_hotel(sys.argv[1])