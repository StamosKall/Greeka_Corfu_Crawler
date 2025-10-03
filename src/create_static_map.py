#!/usr/bin/env python3
"""
Static Map Generator for Corfu Hotels
Creates a static map image showing all hotel locations from the hotels.json file
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
import requests
from PIL import Image
from io import BytesIO

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

def create_static_map_matplotlib(hotels_data, output_file='corfu_hotels_static_map.png'):
    """Create a static map using matplotlib"""
    
    # Extract coordinates and prepare data
    latitudes = []
    longitudes = []
    colors = []
    names = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                latitudes.append(lat)
                longitudes.append(lon)
                colors.append(get_star_color(hotel.get('star_rating', '')))
                names.append(hotel['name'])
            except (ValueError, TypeError):
                continue
    
    if not latitudes:
        print("No valid coordinates found!")
        return
    
    # Create the plot
    plt.figure(figsize=(15, 12))
    
    # Plot hotels
    scatter = plt.scatter(longitudes, latitudes, c=colors, s=60, alpha=0.7, edgecolors='black', linewidth=0.5)
    
    # Set map bounds with some padding
    lat_min, lat_max = min(latitudes), max(latitudes)
    lon_min, lon_max = min(longitudes), max(longitudes)
    
    lat_padding = (lat_max - lat_min) * 0.1
    lon_padding = (lon_max - lon_min) * 0.1
    
    plt.xlim(lon_min - lon_padding, lon_max + lon_padding)
    plt.ylim(lat_min - lat_padding, lat_max + lat_padding)
    
    # Add labels and title
    plt.xlabel('Longitude', fontsize=12)
    plt.ylabel('Latitude', fontsize=12)
    plt.title('Corfu Hotels Static Map\nColor-coded by Star Rating', fontsize=16, fontweight='bold')
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Create legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='5 Stars'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', markersize=10, label='4 Stars'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', markersize=10, label='3 Stars'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=10, label='2 Stars'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='1 Star'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label='No Rating')
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    # Add statistics box
    total_hotels = len([h for h in hotels_data if h.get('latitude') and h.get('longitude')])
    stats_text = f'Total Hotels: {total_hotels}\nWith Coordinates: {len(latitudes)}'
    
    plt.text(0.02, 0.02, stats_text, transform=plt.gca().transAxes, 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
             verticalalignment='bottom', fontsize=10)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"Static map saved as: {output_file}")
    print(f"Total hotels plotted: {len(latitudes)}")

def create_enhanced_static_map(hotels_data, output_file='corfu_hotels_enhanced_map.png'):
    """Create an enhanced static map with better visualization"""
    
    # Extract coordinates and prepare data
    latitudes = []
    longitudes = []
    colors = []
    sizes = []
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
                
                # Size based on star rating
                if star_rating == '5':
                    sizes.append(100)
                elif star_rating == '4':
                    sizes.append(80)
                elif star_rating == '3':
                    sizes.append(60)
                elif star_rating == '2':
                    sizes.append(40)
                elif star_rating == '1':
                    sizes.append(30)
                else:
                    sizes.append(50)
                    
            except (ValueError, TypeError):
                continue
    
    if not latitudes:
        print("No valid coordinates found!")
        return
    
    # Create the plot with subplots for better layout
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # Main map
    scatter = ax1.scatter(longitudes, latitudes, c=colors, s=sizes, alpha=0.7, 
                         edgecolors='black', linewidth=0.5)
    
    # Set map bounds with padding
    lat_min, lat_max = min(latitudes), max(latitudes)
    lon_min, lon_max = min(longitudes), max(longitudes)
    
    lat_padding = (lat_max - lat_min) * 0.05
    lon_padding = (lon_max - lon_min) * 0.05
    
    ax1.set_xlim(lon_min - lon_padding, lon_max + lon_padding)
    ax1.set_ylim(lat_min - lat_padding, lat_max + lat_padding)
    
    ax1.set_xlabel('Longitude', fontsize=12)
    ax1.set_ylabel('Latitude', fontsize=12)
    ax1.set_title('Corfu Hotels Distribution Map', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Legend for main map
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=12, label='5 Stars'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', markersize=10, label='4 Stars'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', markersize=8, label='3 Stars'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=6, label='2 Stars'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=5, label='1 Star'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=7, label='No Rating')
    ]
    ax1.legend(handles=legend_elements, loc='upper left')
    
    # Statistics and distribution chart
    star_counts = {}
    for rating in star_ratings:
        rating = rating if rating else 'No Rating'
        star_counts[rating] = star_counts.get(rating, 0) + 1
    
    # Bar chart
    ratings = list(star_counts.keys())
    counts = list(star_counts.values())
    bar_colors = [get_star_color(r if r != 'No Rating' else '') for r in ratings]
    
    ax2.bar(ratings, counts, color=bar_colors, alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Star Rating', fontsize=12)
    ax2.set_ylabel('Number of Hotels', fontsize=12)
    ax2.set_title('Hotel Distribution by Star Rating', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add count labels on bars
    for i, count in enumerate(counts):
        ax2.text(i, count + 0.5, str(count), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"Enhanced static map saved as: {output_file}")
    print(f"Total hotels plotted: {len(latitudes)}")
    print(f"Star rating distribution: {star_counts}")

def main():
    """Main function to create static maps"""
    print("Creating static maps for Corfu hotels...")
    
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
    import os
    output_dir = '../data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create basic static map
    print("\n1. Creating basic static map...")
    create_static_map_matplotlib(hotels_data, f'{output_dir}/corfu_hotels_static_map.png')
    
    # Create enhanced static map
    print("\n2. Creating enhanced static map...")
    create_enhanced_static_map(hotels_data, f'{output_dir}/corfu_hotels_enhanced_map.png')
    
    print("\nStatic maps created successfully!")
    print("Files saved in:", os.path.abspath(output_dir))

if __name__ == "__main__":
    main()