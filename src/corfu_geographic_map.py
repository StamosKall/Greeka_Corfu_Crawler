#!/usr/bin/env python3
"""
Corfu Geographic Map Generator
Creates a static geographic map of Corfu island with hotel distribution
Similar to the ATTIKH NUTS3 map style
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import requests
import os
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
from collections import Counter

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_star_color(star_rating):
    """Get color based on star rating with a color scheme similar to the reference map"""
    star_colors = {
        '5': '#8B0000',  # Dark Red (highest density color from reference)
        '4': '#DC143C',  # Crimson
        '3': '#FF6347',  # Tomato  
        '2': '#FFA500',  # Orange
        '1': '#FFD700',  # Gold
        '': '#90EE90'    # Light Green (lowest density from reference)
    }
    return star_colors.get(str(star_rating), '#90EE90')

def create_corfu_outline():
    """Create a simple outline of Corfu island based on coordinate bounds"""
    # These are approximate coordinates for Corfu's outline
    # In a real implementation, you'd use actual geographic boundary data
    corfu_outline = np.array([
        [19.62, 39.78],  # North
        [19.65, 39.77],
        [19.70, 39.75],
        [19.75, 39.73],
        [19.80, 39.70],
        [19.85, 39.68],
        [19.88, 39.65],
        [19.90, 39.62],
        [19.92, 39.58],  # East coast
        [19.90, 39.55],
        [19.88, 39.52],
        [19.85, 39.50],
        [19.82, 39.48],
        [19.78, 39.46],
        [19.75, 39.45],  # South
        [19.70, 39.46],
        [19.65, 39.48],
        [19.62, 39.50],
        [19.60, 39.53],
        [19.58, 39.56],
        [19.60, 39.60],
        [19.62, 39.65],
        [19.63, 39.70],
        [19.62, 39.75],  # Back to north
        [19.62, 39.78]
    ])
    return corfu_outline

def create_geographic_corfu_map(hotels_data, output_file='corfu_geographic_map.png'):
    """Create a geographic-style map of Corfu similar to the reference image"""
    
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
    
    # Create the figure with the same style as reference
    fig, ax = plt.subplots(1, 1, figsize=(12, 16))
    
    # Set background color similar to reference (light blue for water)
    ax.set_facecolor('#E6F3FF')
    
    # Create Corfu island shape (simplified)
    corfu_outline = create_corfu_outline()
    
    # Fill the island with light yellow/cream color
    island_poly = plt.Polygon(corfu_outline, facecolor='#FFFACD', edgecolor='#8B4513', linewidth=2, alpha=0.8)
    ax.add_patch(island_poly)
    
    # Calculate map bounds
    lat_min, lat_max = min(latitudes), max(latitudes)
    lon_min, lon_max = min(longitudes), max(longitudes)
    
    # Add some padding
    lat_padding = (lat_max - lat_min) * 0.1
    lon_padding = (lon_max - lon_min) * 0.1
    
    ax.set_xlim(lon_min - lon_padding, lon_max + lon_padding)
    ax.set_ylim(lat_min - lat_padding, lat_max + lat_padding)
    
    # Plot hotels as circles with sizes based on star rating
    sizes = []
    for rating in star_ratings:
        if rating == '5':
            sizes.append(150)
        elif rating == '4':
            sizes.append(120)
        elif rating == '3':
            sizes.append(90)
        elif rating == '2':
            sizes.append(60)
        elif rating == '1':
            sizes.append(40)
        else:
            sizes.append(70)
    
    # Create scatter plot
    scatter = ax.scatter(longitudes, latitudes, c=colors, s=sizes, alpha=0.8, 
                        edgecolors='white', linewidth=1.5, zorder=5)
    
    # Set labels similar to reference
    ax.set_xlabel('Longitude', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
    
    # Create title similar to reference
    ax.set_title('Detailed Hotel Distribution in CORFU\n(Ionian Islands, Greece)', 
                fontsize=16, fontweight='bold', pad=20)
    
    # Add grid (subtle)
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Count hotels by star rating
    star_counts = Counter(star_ratings)
    total_hotels = len(latitudes)
    hotels_with_ratings = sum(star_counts[k] for k in star_counts if k != '')
    hotels_no_rating = star_counts.get('', 0)
    
    # Create statistics box similar to reference
    stats_text = f"Region Statistics\n"
    stats_text += f"CORFU Island\n"
    stats_text += f"Hotels in Region: {total_hotels}\n"
    stats_text += f"Geocoded: {total_hotels}\n"
    stats_text += f"Sub-regions: {len(set(h.get('address', '').split(',')[-1].strip() for h in hotels_data if h.get('address')))}\n"
    stats_text += f"With Hotels: {len(set(h.get('address', '').split(',')[-1].strip() for h in hotels_data if h.get('address')))}"
    
    # Add statistics box
    props = dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props, fontfamily='monospace')
    
    # Create color bar legend similar to reference
    # Create custom legend
    legend_elements = []
    legend_labels = []
    
    for rating in ['5', '4', '3', '2', '1', '']:
        count = star_counts.get(rating, 0)
        if count > 0:
            color = get_star_color(rating)
            rating_label = f"{rating} Stars" if rating else "No Rating"
            legend_elements.append(plt.Circle((0,0), 1, facecolor=color, alpha=0.8, edgecolor='white'))
            legend_labels.append(f"{rating_label}: {count}")
    
    # Add legend
    legend = ax.legend(legend_elements, legend_labels, loc='lower right', 
                      title='Hotel Star Ratings', title_fontsize=12, fontsize=10)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('black')
    legend.get_frame().set_alpha(0.9)
    
    # Add colorbar similar to reference (showing hotel density)
    # Create a simple colorbar showing the color scale
    sm = plt.cm.ScalarMappable(cmap='Reds', norm=plt.Normalize(vmin=0, vmax=25))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.02)
    cbar.set_label('Number of Hotels', rotation=270, labelpad=20, fontsize=12)
    
    # Add some location labels (you could enhance this with actual place names)
    # Add a few key locations if we have hotel clusters
    if len(latitudes) > 10:
        # Find hotel clusters
        lat_mean = np.mean(latitudes)
        lon_mean = np.mean(longitudes)
        
        # Add a marker for the center
        ax.plot(lon_mean, lat_mean, 'k*', markersize=15, zorder=10)
        ax.annotate('Corfu Center', (lon_mean, lat_mean), xytext=(5, 5), 
                   textcoords='offset points', fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    # Add small islands around Corfu (decorative)
    small_islands = [
        ([19.55, 19.56, 19.56, 19.55], [39.65, 39.65, 39.66, 39.66]),
        ([19.95, 19.96, 19.96, 19.95], [39.70, 39.70, 39.71, 39.71])
    ]
    
    for island_x, island_y in small_islands:
        island = plt.Polygon(list(zip(island_x, island_y)), facecolor='#FFFACD', 
                           edgecolor='#8B4513', linewidth=1, alpha=0.6)
        ax.add_patch(island)
    
    # Set aspect ratio to be equal
    ax.set_aspect('equal', adjustable='box')
    
    # Remove tick marks but keep labels
    ax.tick_params(length=0)
    
    # Add hotel location indicator similar to reference
    ax.text(0.98, 0.02, '● Hotel Locations', transform=ax.transAxes, 
           fontsize=10, ha='right', va='bottom',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Save with high DPI similar to reference
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.show()
    
    print(f"Geographic map saved as: {output_file}")
    print(f"Total hotels plotted: {len(latitudes)}")
    print(f"Star rating distribution: {dict(star_counts)}")

def main():
    """Main function to create geographic map"""
    print("Creating geographic map of Corfu with hotel distribution...")
    
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
    
    # Create the geographic map
    output_file = os.path.join(output_dir, 'corfu_geographic_map.png')
    create_geographic_corfu_map(hotels_data, output_file)
    
    print(f"\n🗺️ GEOGRAPHIC MAP CREATED!")
    print(f"📁 File saved at: {os.path.abspath(output_file)}")
    print(f"📊 Style: Similar to ATTIKH NUTS3 reference map")
    print(f"🏨 Features: Island outline, hotel locations, star rating colors")

if __name__ == "__main__":
    main()