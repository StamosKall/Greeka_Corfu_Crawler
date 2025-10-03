#!/usr/bin/env python3
"""
Debug script to inspect HTML structure for coordinate extraction
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_coordinates(url: str):
    """Debug coordinate extraction from a hotel page"""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    print(f"Debugging coordinates for: {url}")
    print("=" * 80)
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("1. Looking for iframes...")
        iframes = soup.find_all('iframe')
        for i, iframe in enumerate(iframes):
            src = iframe.get('src', '')
            print(f"   iframe {i+1}: {src[:100]}...")
            if 'google' in src.lower() or 'map' in src.lower():
                print(f"      >>> POTENTIAL MAP IFRAME: {src}")
        
        print(f"\n2. Looking for DMS coordinates in text...")
        page_text = soup.get_text()
        dms_patterns = [
            r'\d+°\d+[\'\u2032][\d.]+[\"\u2033][NS]\s+\d+°\d+[\'\u2032][\d.]+[\"\u2033][EW]',
            r'\d+°\d+\'\d+\.*\d*"[NS]\s+\d+°\d+\'\d+\.*\d*"[EW]'
        ]
        
        for pattern in dms_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"   Found DMS coordinates: {matches}")
        
        print(f"\n3. Looking for decimal coordinates...")
        # Corfu area coordinates
        decimal_patterns = [
            r'(39\.[0-9]+)[,\s]+(19\.[0-9]+|20\.[0-9]+)',
            r'lat["\']?\s*[:=]\s*([0-9.-]+)',
            r'lng["\']?\s*[:=]\s*([0-9.-]+)'
        ]
        
        for pattern in decimal_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"   Pattern '{pattern}' found: {matches}")
        
        print(f"\n4. Checking JavaScript content...")
        scripts = soup.find_all('script')
        for i, script in enumerate(scripts):
            if script.string and ('lat' in script.string.lower() or 'lng' in script.string.lower() or 'coord' in script.string.lower()):
                print(f"   Script {i+1} contains coordinate-related content:")
                lines = script.string.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['lat', 'lng', 'coord', 'map', 'center']):
                        print(f"      {line.strip()}")
        
        print(f"\n5. Looking for data attributes...")
        elements_with_data = soup.find_all(attrs=re.compile(r'data-.*'))
        coord_data = []
        for element in elements_with_data:
            for attr, value in element.attrs.items():
                if any(keyword in attr.lower() for keyword in ['lat', 'lng', 'coord']):
                    coord_data.append(f"{attr}={value}")
        
        if coord_data:
            print(f"   Found coordinate data attributes: {coord_data}")
        else:
            print("   No coordinate data attributes found")
        
        print(f"\n6. Looking for meta tags...")
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            for attr in ['property', 'name', 'content']:
                value = meta.get(attr, '')
                if any(keyword in value.lower() for keyword in ['geo', 'lat', 'lng', 'coord', 'location']):
                    print(f"   Meta tag: {meta}")
        
        print(f"\n7. Looking for map-related divs...")
        map_divs = soup.find_all(['div', 'section'], attrs={'class': re.compile(r'map', re.I)})
        for div in map_divs:
            print(f"   Map div found: {div.get('class')} - {div.get('id')}")
            if div.get_text(strip=True):
                text_preview = div.get_text(strip=True)[:100]
                print(f"      Text: {text_preview}...")
        
        # Look for specific coordinate patterns in the visible text
        print(f"\n8. Looking for coordinates in visible text...")
        visible_text = soup.get_text()
        coordinate_indicators = [
            'coordinate', 'συντεταγμένες', 'location', 'θέση', 
            '°', '′', '″', 'N', 'E', 'latitude', 'longitude'
        ]
        
        lines = visible_text.split('\n')
        for line in lines:
            line = line.strip()
            if any(indicator in line for indicator in coordinate_indicators) and len(line) < 200:
                print(f"   Coordinate-related line: {line}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with the Delfino Blu hotel
    debug_coordinates("https://www.greeka.com/ionian/corfu/hotels/location-agios-stefanos-avliotes/delfino-blu/")