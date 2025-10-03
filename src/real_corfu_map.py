#!/usr/bin/env python3
"""
Real Corfu Map Generator with Hotels
Creates an actual geographical map of Corfu island with hotel locations
"""

import json
import folium
import os
from folium import plugins

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_star_color(star_rating):
    """Get color based on star rating"""
    star_colors = {
        '5': 'darkgreen',
        '4': 'green', 
        '3': 'orange',
        '2': 'red',
        '1': 'darkred',
        '': 'gray'
    }
    return star_colors.get(str(star_rating), 'gray')

def create_real_corfu_map(hotels_data, output_file='real_corfu_hotels_map.html'):
    """Create a real geographical map of Corfu with hotels"""
    
    # Extract coordinates to find the bounds
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
    
    # Calculate center of Corfu based on hotel locations
    center_lat = sum(latitudes) / len(latitudes)
    center_lon = sum(longitudes) / len(longitudes)
    
    print(f"Map center: {center_lat:.4f}, {center_lon:.4f}")
    
    # Create the base map of Corfu with satellite/terrain view
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles=None  # We'll add custom tiles
    )
    
    # Add different map layers
    # 1. OpenStreetMap (default)
    folium.TileLayer(
        'openstreetmap',
        name='Street Map',
        control=True
    ).add_to(m)
    
    # 2. Satellite view
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite View',
        overlay=False,
        control=True
    ).add_to(m)
    
    # 3. Terrain view
    folium.TileLayer(
        tiles='https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png',
        attr='Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap contributors',
        name='Terrain',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add hotels to the map
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
                
                # Create detailed popup content
                popup_html = f"""
                <div style="width: 300px;">
                    <h4 style="color: #2c3e50; margin-bottom: 10px;">{hotel['name']}</h4>
                    <p><strong>⭐ Rating:</strong> {star_rating if star_rating else 'Not Rated'} stars</p>
                    <p><strong>📍 Location:</strong> {hotel.get('address', 'N/A')}</p>
                    <p><strong>📞 Phone:</strong> {hotel.get('phone_number', 'N/A')}</p>
                    <p><strong>🌟 Review Score:</strong> {hotel.get('review_score', 'N/A')}</p>
                    <p><strong>💬 Reviews:</strong> {hotel.get('number_of_reviews', 'N/A')}</p>
                    {f'<p><strong>🌐 Website:</strong> <a href="{hotel["official_website"]}" target="_blank">Visit</a></p>' if hotel.get('official_website') else ''}
                </div>
                """
                
                # Add marker with custom icon
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=350),
                    tooltip=f"{hotel['name']} ({star_rating} stars)" if star_rating else hotel['name'],
                    icon=folium.Icon(
                        color=color,
                        icon='bed',
                        prefix='fa',
                        icon_color='white'
                    )
                ).add_to(m)
                
            except (ValueError, TypeError):
                continue
    
    # Add marker clustering for better performance
    marker_cluster = plugins.MarkerCluster(
        name='Hotel Clusters',
        control=True
    )
    
    # Add clustered markers (alternative view)
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                star_rating = hotel.get('star_rating', '')
                color = get_star_color(star_rating)
                
                popup_html = f"""
                <div style="width: 250px;">
                    <h4>{hotel['name']}</h4>
                    <p>⭐ {star_rating if star_rating else 'Not Rated'}</p>
                    <p>📍 {hotel.get('address', 'N/A')}</p>
                </div>
                """
                
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    popup=folium.Popup(popup_html, max_width=300),
                    color='white',
                    weight=2,
                    fillColor=color,
                    fillOpacity=0.8
                ).add_to(marker_cluster)
                
            except (ValueError, TypeError):
                continue
    
    marker_cluster.add_to(m)
    
    # Add a custom legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 180px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 15px; box-shadow: 3px 3px 3px rgba(0,0,0,0.3);">
    <h4 style="margin-top:0; color: #2c3e50;">🏨 Hotel Star Ratings</h4>
    <p><i class="fa fa-bed" style="color:darkgreen"></i> 5 Stars ({star_counts.get('5', 0)} hotels)</p>
    <p><i class="fa fa-bed" style="color:green"></i> 4 Stars ({star_counts.get('4', 0)} hotels)</p>
    <p><i class="fa fa-bed" style="color:orange"></i> 3 Stars ({star_counts.get('3', 0)} hotels)</p>
    <p><i class="fa fa-bed" style="color:red"></i> 2 Stars ({star_counts.get('2', 0)} hotels)</p>
    <p><i class="fa fa-bed" style="color:darkred"></i> 1 Star ({star_counts.get('1', 0)} hotels)</p>
    <p><i class="fa fa-bed" style="color:gray"></i> No Rating ({star_counts.get('No Rating', 0)} hotels)</p>
    </div>
    '''
    
    # Add statistics box
    stats_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 250px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 15px; box-shadow: 3px 3px 3px rgba(0,0,0,0.3);">
    <h4 style="margin-top:0; color: #2c3e50;">📊 Corfu Hotels Map</h4>
    <p><strong>🏨 Total Hotels:</strong> {len(latitudes)}</p>
    <p><strong>📍 Coverage:</strong> {len(latitudes)}/{len(hotels_data)} ({(len(latitudes)/len(hotels_data)*100):.1f}%)</p>
    <p><strong>🗺️ View:</strong> Switch map layers using the control</p>
    </div>
    '''
    
    # Add the HTML elements to the map
    m.get_root().html.add_child(folium.Element(legend_html))
    m.get_root().html.add_child(folium.Element(stats_html))
    
    # Add layer control to switch between map types
    folium.LayerControl(position='topright').add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen(
        position='topleft',
        title='Enter fullscreen',
        title_cancel='Exit fullscreen',
        force_separate_button=True
    ).add_to(m)
    
    # Add measure control for distances
    plugins.MeasureControl(
        position='bottomleft',
        primary_length_unit='kilometers',
        secondary_length_unit='miles',
        primary_area_unit='sqkilometers',
        secondary_area_unit='acres'
    ).add_to(m)
    
    # Fit map to show all hotels
    if len(latitudes) > 1:
        sw = [min(latitudes), min(longitudes)]
        ne = [max(latitudes), max(longitudes)]
        m.fit_bounds([sw, ne], padding=(20, 20))
    
    # Save the map
    m.save(output_file)
    print(f"Real Corfu map saved as: {output_file}")
    print(f"Total hotels plotted: {len(latitudes)}")
    print(f"Star rating distribution: {star_counts}")
    
    return output_file, m

def create_static_image_from_folium(html_file, png_file):
    """Try to create a static PNG from the folium map"""
    try:
        import selenium
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import time
        
        # Setup Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1400,1000")
        
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the HTML file
        file_path = f"file:///{os.path.abspath(html_file).replace(chr(92), '/')}"
        driver.get(file_path)
        
        # Wait for the map to load completely
        time.sleep(8)
        
        # Take screenshot
        driver.save_screenshot(png_file)
        driver.quit()
        
        print(f"Static image saved as: {png_file}")
        return True
        
    except ImportError:
        print("Selenium not available. Install with: pip install selenium")
        print("Also need to install ChromeDriver")
        return False
    except Exception as e:
        print(f"Error creating static image: {e}")
        return False

def main():
    """Main function to create real Corfu map"""
    print("Creating real geographical map of Corfu with hotels...")
    
    # Load hotel data
    json_file = 'data/hotels.json'
    try:
        hotels_data = load_hotel_data(json_file)
        print(f"Loaded {len(hotels_data)} hotels from {json_file}")
    except FileNotFoundError:
        json_file = '../data/hotels.json'
        try:
            hotels_data = load_hotel_data(json_file) 
            print(f"Loaded {len(hotels_data)} hotels from {json_file}")
        except FileNotFoundError:
            print(f"Error: Could not find hotels.json")
            return
    
    # Create output directory
    output_dir = 'data' if os.path.exists('data') else '../data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the real map
    html_file = os.path.join(output_dir, 'real_corfu_hotels_map.html')
    png_file = os.path.join(output_dir, 'real_corfu_hotels_map.png')
    
    map_file, folium_map = create_real_corfu_map(hotels_data, html_file)
    
    # Try to create static image
    print(f"\nAttempting to create static PNG image...")
    success = create_static_image_from_folium(html_file, png_file)
    
    if not success:
        print("Could not create static PNG. The HTML map is fully functional though!")
        print("You can open it in any web browser to see the real Corfu map.")
    
    print(f"\n🗺️  REAL CORFU MAP CREATED!")
    print(f"📁 Location: {os.path.abspath(output_dir)}")
    print(f"🌐 Interactive HTML: {os.path.basename(html_file)}")
    if success:
        print(f"🖼️  Static PNG: {os.path.basename(png_file)}")
    
    print(f"\n📖 Instructions:")
    print(f"1. Open '{html_file}' in your web browser")
    print(f"2. Use the layer control (top-right) to switch between:")
    print(f"   - Street Map (default)")
    print(f"   - Satellite View")
    print(f"   - Terrain View")
    print(f"3. Click on hotel markers for detailed information")
    print(f"4. Use fullscreen button for better viewing")
    print(f"5. Measure distances using the measurement tool")

if __name__ == "__main__":
    main()