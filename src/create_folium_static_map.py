#!/usr/bin/env python3
"""
Simple Static Map Generator using Folium for Corfu Hotels
Creates a static map image by taking a screenshot of a folium map
"""

import json
import folium
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_star_color(star_rating):
    """Get color based on star rating"""
    star_colors = {
        '5': 'green',
        '4': 'lightgreen', 
        '3': 'yellow',
        '2': 'orange',
        '1': 'red',
        '': 'gray'
    }
    return star_colors.get(str(star_rating), 'gray')

def create_folium_static_map(hotels_data, output_file='corfu_hotels_folium_map.html', 
                           screenshot_file='corfu_hotels_static.png'):
    """Create a static map using folium and take a screenshot"""
    
    # Calculate center point
    latitudes = []
    longitudes = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                latitudes.append(lat)
                longitudes.append(lon)
            except (ValueError, TypeError):
                continue
    
    if not latitudes:
        print("No valid coordinates found!")
        return
    
    center_lat = sum(latitudes) / len(latitudes)
    center_lon = sum(longitudes) / len(longitudes)
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Add hotels to map
    star_counts = {}
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                star_rating = hotel.get('star_rating', '')
                color = get_star_color(star_rating)
                
                # Count star ratings
                rating_key = star_rating if star_rating else 'No Rating'
                star_counts[rating_key] = star_counts.get(rating_key, 0) + 1
                
                # Create popup content
                popup_text = f"""
                <b>{hotel['name']}</b><br>
                Star Rating: {star_rating if star_rating else 'Not Rated'}<br>
                Address: {hotel.get('address', 'N/A')}<br>
                Review Score: {hotel.get('review_score', 'N/A')}<br>
                Reviews: {hotel.get('number_of_reviews', 'N/A')}
                """
                
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    popup=folium.Popup(popup_text, max_width=300),
                    color='black',
                    weight=1,
                    fillColor=color,
                    fillOpacity=0.7
                ).add_to(m)
                
            except (ValueError, TypeError):
                continue
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>Star Ratings</h4>
    <p><i class="fa fa-circle" style="color:green"></i> 5 Stars</p>
    <p><i class="fa fa-circle" style="color:lightgreen"></i> 4 Stars</p>
    <p><i class="fa fa-circle" style="color:yellow"></i> 3 Stars</p>
    <p><i class="fa fa-circle" style="color:orange"></i> 2 Stars</p>
    <p><i class="fa fa-circle" style="color:red"></i> 1 Star</p>
    <p><i class="fa fa-circle" style="color:gray"></i> No Rating</p>
    </div>
    '''
    
    # Add statistics
    stats_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: 100px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>Corfu Hotels Statistics</h4>
    <p><strong>Total Hotels:</strong> {len(latitudes)}</p>
    <p><strong>Coverage:</strong> 100%</p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    m.get_root().html.add_child(folium.Element(stats_html))
    
    # Save the map
    m.save(output_file)
    print(f"Interactive map saved as: {output_file}")
    print(f"Total hotels plotted: {len(latitudes)}")
    print(f"Star rating distribution: {star_counts}")
    
    return output_file

def take_screenshot_with_selenium(html_file, screenshot_file, width=1200, height=800):
    """Take a screenshot of the HTML file using Selenium"""
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"--window-size={width},{height}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the HTML file
        file_path = f"file:///{os.path.abspath(html_file)}"
        driver.get(file_path)
        
        # Wait for the map to load
        time.sleep(5)
        
        # Take screenshot
        driver.save_screenshot(screenshot_file)
        driver.quit()
        
        print(f"Screenshot saved as: {screenshot_file}")
        return True
        
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        print("Make sure you have Chrome and chromedriver installed")
        return False

def main():
    """Main function to create static maps"""
    print("Creating static map for Corfu hotels using Folium...")
    
    # Load hotel data
    json_file = '../data/hotels.json'
    try:
        hotels_data = load_hotel_data(json_file)
        print(f"Loaded {len(hotels_data)} hotels from {json_file}")
    except FileNotFoundError:
        print(f"Error: Could not find {json_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file}")
        return
    
    # Create output directory
    output_dir = '../data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create folium map
    html_file = f'{output_dir}/corfu_hotels_folium_map.html'
    screenshot_file = f'{output_dir}/corfu_hotels_static.png'
    
    folium_file = create_folium_static_map(hotels_data, html_file, screenshot_file)
    
    # Try to take screenshot (optional - requires selenium and chromedriver)
    print("\nAttempting to create static PNG image...")
    success = take_screenshot_with_selenium(html_file, screenshot_file)
    
    if not success:
        print("Screenshot failed. You can:")
        print("1. Open the HTML file in a browser and take a manual screenshot")
        print("2. Install selenium and chromedriver for automatic screenshots")
        print("3. Use the matplotlib version instead")
    
    print(f"\nFiles created in: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    main()