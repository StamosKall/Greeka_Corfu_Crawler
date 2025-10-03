#!/usr/bin/env python3
"""
Simple Static Map Generator for Corfu Hotels
Creates a static map image using matplotlib only
"""

import json
import matplotlib.pyplot as plt
import os

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_star_color(star_rating):
    """Get color based on star rating"""
    star_colors = {
        '5': '#2E7D32',  # Dark Green
        '4': '#66BB6A',  # Light Green
        '3': '#FFF176',  # Yellow
        '2': '#FFB74D',  # Orange
        '1': '#E57373',  # Red
        '': '#9E9E9E'    # Gray
    }
    return star_colors.get(str(star_rating), '#9E9E9E')

def create_simple_static_map(hotels_data, output_file='corfu_hotels_map.png'):
    """Create a simple static map using matplotlib"""
    
    # Extract coordinates and prepare data
    latitudes = []
    longitudes = []
    colors = []
    star_ratings = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                latitudes.append(lat)
                longitudes.append(lon)
                
                star_rating = hotel.get('star_rating', '')
                star_ratings.append(star_rating)
                colors.append(get_star_color(star_rating))
                    
            except (ValueError, TypeError):
                continue
    
    if not latitudes:
        print("No valid coordinates found!")
        return
    
    # Create the plot
    plt.figure(figsize=(16, 12))
    
    # Plot hotels with different sizes based on star rating
    sizes = []
    for rating in star_ratings:
        if rating == '5':
            sizes.append(120)
        elif rating == '4':
            sizes.append(100)
        elif rating == '3':
            sizes.append(80)
        elif rating == '2':
            sizes.append(60)
        elif rating == '1':
            sizes.append(50)
        else:
            sizes.append(70)
    
    # Create scatter plot
    plt.scatter(longitudes, latitudes, c=colors, s=sizes, alpha=0.8, 
               edgecolors='white', linewidth=1.5)
    
    # Set map bounds with padding
    lat_min, lat_max = min(latitudes), max(latitudes)
    lon_min, lon_max = min(longitudes), max(longitudes)
    
    lat_padding = (lat_max - lat_min) * 0.05
    lon_padding = (lon_max - lon_min) * 0.05
    
    plt.xlim(lon_min - lon_padding, lon_max + lon_padding)
    plt.ylim(lat_min - lat_padding, lat_max + lat_padding)
    
    # Customize the plot
    plt.xlabel('Longitude', fontsize=14, fontweight='bold')
    plt.ylabel('Latitude', fontsize=14, fontweight='bold')
    plt.title('Corfu Hotels Static Map\nColor & Size Coded by Star Rating', 
              fontsize=18, fontweight='bold', pad=20)
    
    # Add subtle grid
    plt.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
    
    # Create custom legend with proper colors and sizes
    legend_elements = [
        plt.scatter([], [], c='#2E7D32', s=120, label='5 Stars', alpha=0.8, edgecolors='white', linewidth=1.5),
        plt.scatter([], [], c='#66BB6A', s=100, label='4 Stars', alpha=0.8, edgecolors='white', linewidth=1.5),
        plt.scatter([], [], c='#FFF176', s=80, label='3 Stars', alpha=0.8, edgecolors='white', linewidth=1.5),
        plt.scatter([], [], c='#FFB74D', s=60, label='2 Stars', alpha=0.8, edgecolors='white', linewidth=1.5),
        plt.scatter([], [], c='#E57373', s=50, label='1 Star', alpha=0.8, edgecolors='white', linewidth=1.5),
        plt.scatter([], [], c='#9E9E9E', s=70, label='No Rating', alpha=0.8, edgecolors='white', linewidth=1.5)
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', fontsize=12, 
              title='Hotel Star Ratings', title_fontsize=14)
    
    # Calculate and display statistics
    star_counts = {}
    for rating in star_ratings:
        rating_key = rating if rating else 'No Rating'
        star_counts[rating_key] = star_counts.get(rating_key, 0) + 1
    
    # Create statistics text
    stats_lines = [f'Total Hotels: {len(latitudes)}']
    for rating in ['5', '4', '3', '2', '1', 'No Rating']:
        count = star_counts.get(rating, 0)
        if count > 0:
            stats_lines.append(f'{rating} Star{"s" if rating != "1" else ""}: {count}')
    
    stats_text = '\n'.join(stats_lines)
    
    # Add statistics box
    plt.text(0.99, 0.01, stats_text, transform=plt.gca().transAxes, 
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9),
             verticalalignment='bottom', horizontalalignment='right', 
             fontsize=11, fontfamily='monospace')
    
    # Set background color
    plt.gca().set_facecolor('#f8f9fa')
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    
    print(f"Static map saved as: {output_file}")
    print(f"Total hotels plotted: {len(latitudes)}")
    print(f"Star rating distribution: {star_counts}")
    
    # Show the plot
    plt.show()

def main():
    """Main function to create static map"""
    print("Creating static map for Corfu hotels...")
    
    # Load hotel data
    json_file = 'data/hotels.json'
    try:
        hotels_data = load_hotel_data(json_file)
        print(f"Loaded {len(hotels_data)} hotels from {json_file}")
    except FileNotFoundError:
        print(f"Error: Could not find {json_file}")
        # Try alternative path
        json_file = '../data/hotels.json'
        try:
            hotels_data = load_hotel_data(json_file) 
            print(f"Loaded {len(hotels_data)} hotels from {json_file}")
        except FileNotFoundError:
            print(f"Error: Could not find hotels.json in current or parent directory")
            return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file}")
        return
    
    # Create output directory
    output_dir = 'data' if os.path.exists('data') else '../data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create static map
    output_file = os.path.join(output_dir, 'corfu_hotels_static_map.png')
    create_simple_static_map(hotels_data, output_file)
    
    print(f"\nStatic map created successfully!")
    print(f"File saved at: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()