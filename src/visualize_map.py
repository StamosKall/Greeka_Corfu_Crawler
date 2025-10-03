#!/usr/bin/env python3
"""
Visualization script for Greeka Corfu hotels coordinates.
Creates a map showing all hotel locations.
"""

import json
import folium
from folium import plugins
import pandas as pd
import webbrowser
import os

def create_hotels_map(json_file: str = "../data/hotels.json", html_file: str = "../data/corfu_hotels_map.html"):
    """
    Create an interactive map showing all hotel locations
    
    Args:
        json_file: Path to the JSON hotel data file
        html_file: Output HTML file for the map
    """
    
    # Load hotel data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            hotels = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found. Please run the crawler first.")
        return
    
    # Filter hotels with coordinates
    hotels_with_coords = [
        hotel for hotel in hotels 
        if hotel.get('latitude') and hotel.get('longitude')
    ]
    
    print(f"Creating map for {len(hotels_with_coords)} hotels with coordinates...")
    
    if not hotels_with_coords:
        print("No hotels with coordinates found!")
        return
    
    # Calculate center point (average of all coordinates)
    lats = [float(hotel['latitude']) for hotel in hotels_with_coords]
    lons = [float(hotel['longitude']) for hotel in hotels_with_coords]
    
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    print(f"Map center: {center_lat:.6f}, {center_lon:.6f}")
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Add tile layers
    folium.TileLayer('cartodb positron').add_to(m)
    folium.TileLayer('OpenStreetMap').add_to(m)
    
    # Color mapping for star ratings
    def get_color(star_rating):
        if not star_rating:
            return 'gray'
        rating = int(star_rating)
        color_map = {
            1: 'red',
            2: 'orange', 
            3: 'yellow',
            4: 'lightgreen',
            5: 'green'
        }
        return color_map.get(rating, 'blue')
    
    # Add markers for each hotel
    for hotel in hotels_with_coords:
        lat = float(hotel['latitude'])
        lon = float(hotel['longitude'])
        
        # Create popup content
        popup_content = f"""
        <div style="width: 300px;">
            <h4>{hotel['name']}</h4>
            <p><strong>Address:</strong> {hotel['address']}</p>
            <p><strong>Star Rating:</strong> {hotel['star_rating'] or 'N/A'} ⭐</p>
            <p><strong>Review Score:</strong> {hotel['review_score'] or 'N/A'}/5.0</p>
            <p><strong>Reviews:</strong> {hotel['number_of_reviews'] or 'N/A'}</p>
            <p><strong>Phone:</strong> {hotel['phone_number'] or 'N/A'}</p>
            <p><strong>Coordinates:</strong> {lat:.6f}, {lon:.6f}</p>
            {f'<p><a href="{hotel["official_website"]}" target="_blank">Official Website</a></p>' if hotel.get('official_website') else ''}
            <p><a href="{hotel['detail_url']}" target="_blank">View on Greeka</a></p>
        </div>
        """
        
        # Add marker
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=350),
            tooltip=hotel['name'],
            icon=folium.Icon(
                color=get_color(hotel.get('star_rating')),
                icon='bed',
                prefix='fa'
            )
        ).add_to(m)
    
    # Add a marker cluster for better performance with many markers
    marker_cluster = plugins.MarkerCluster().add_to(m)
    
    # Add statistics box
    stats_html = f"""
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 250px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>Corfu Hotels Statistics</h4>
    <p><strong>Total Hotels:</strong> {len(hotels_with_coords)}</p>
    <p><strong>With Coordinates:</strong> {len(hotels_with_coords)}/{len(hotels)}</p>
    <p><strong>Coverage:</strong> {(len(hotels_with_coords)/len(hotels)*100):.1f}%</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(stats_html))
    
    # Add legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <h4>Star Ratings</h4>
    <p><i class="fa fa-map-marker" style="color:green"></i> 5 Stars</p>
    <p><i class="fa fa-map-marker" style="color:lightgreen"></i> 4 Stars</p>
    <p><i class="fa fa-map-marker" style="color:yellow"></i> 3 Stars</p>
    <p><i class="fa fa-map-marker" style="color:orange"></i> 2 Stars</p>
    <p><i class="fa fa-map-marker" style="color:red"></i> 1 Star</p>
    <p><i class="fa fa-map-marker" style="color:gray"></i> No Rating</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    m.save(html_file)
    print(f"Map saved to {html_file}")
    
    # Try to open in browser
    try:
        webbrowser.open(f'file://{os.path.abspath(html_file)}')
        print(f"Map opened in browser!")
    except:
        print(f"Could not open browser automatically. Please open {html_file} manually.")

def create_coordinate_summary():
    """Create a detailed coordinate summary"""
    try:
        with open("../data/hotels.json", 'r', encoding='utf-8') as f:
            hotels = json.load(f)
    except FileNotFoundError:
        print("Error: data/hotels.json not found. Please run the crawler first.")
        return
    
    # Create summary report
    print("\n=== COORDINATE EXTRACTION SUMMARY ===")
    
    with_coords = [h for h in hotels if h.get('latitude') and h.get('longitude')]
    without_coords = [h for h in hotels if not (h.get('latitude') and h.get('longitude'))]
    
    print(f"Hotels with coordinates: {len(with_coords)}/{len(hotels)} ({len(with_coords)/len(hotels)*100:.1f}%)")
    print(f"Hotels without coordinates: {len(without_coords)}")
    
    if without_coords:
        print("\nHotels missing coordinates:")
        for hotel in without_coords:
            print(f"  - {hotel['name']}")
    
    # Coordinate ranges
    if with_coords:
        lats = [float(h['latitude']) for h in with_coords]
        lons = [float(h['longitude']) for h in with_coords]
        
        print(f"\nCoordinate ranges:")
        print(f"  Latitude: {min(lats):.6f} to {max(lats):.6f}")
        print(f"  Longitude: {min(lons):.6f} to {max(lons):.6f}")
        print(f"  Center point: {sum(lats)/len(lats):.6f}, {sum(lons)/len(lons):.6f}")
    
    # Save coordinate data to CSV for analysis
    if with_coords:
        coord_data = []
        for hotel in with_coords:
            coord_data.append({
                'name': hotel['name'],
                'latitude': float(hotel['latitude']),
                'longitude': float(hotel['longitude']),
                'address': hotel['address'],
                'star_rating': hotel.get('star_rating', ''),
                'detail_url': hotel['detail_url']
            })
        
        df = pd.DataFrame(coord_data)
        df.to_csv('../data/hotel_coordinates.csv', index=False)
        print(f"\nCoordinate data saved to data/hotel_coordinates.csv")

if __name__ == "__main__":
    # Install required packages if not available
    try:
        import folium
        import pandas as pd
    except ImportError:
        print("Installing required packages...")
        import subprocess
        import sys
        subprocess.run([sys.executable, "-m", "pip", "install", "folium", "pandas"])
        import folium
        import pandas as pd
    
    create_coordinate_summary()
    create_hotels_map()
    
    print("\n" + "="*60)
    print("🗺️  VISUALIZATION COMPLETE!")
    print("Files created:")
    print("  - data/corfu_hotels_map.html (Interactive map)")
    print("  - data/hotel_coordinates.csv (Coordinate data)")
    print("="*60)