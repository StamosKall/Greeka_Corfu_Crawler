#!/usr/bin/env python3
"""
Simple Corfu Geographic Map Generator
Creates a static geographic map of Corfu island with hotel distribution
Styled like the ATTIKH NUTS3 reference map
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import Counter
import matplotlib.patches as patches

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_star_color_intensity(star_rating, count=1):
    """Get color intensity based on star rating and count (similar to reference heatmap)"""
    # Color scheme similar to the reference map (yellow to red gradient)
    base_colors = {
        '5': '#8B0000',  # Dark Red
        '4': '#CD5C5C',  # Indian Red
        '3': '#FF6347',  # Tomato
        '2': '#FFA500',  # Orange
        '1': '#FFD700',  # Gold
        '': '#FFFFE0'    # Light Yellow
    }
    return base_colors.get(str(star_rating), '#FFFFE0')

def create_corfu_shape(center_lon, center_lat, width, height):
    """Create a simplified Corfu island shape"""
    # Create a more realistic Corfu shape (elongated north-south)
    angles = np.linspace(0, 2*np.pi, 50)
    
    # Make it more island-like with irregular coastline
    radius_variations = []
    for i, angle in enumerate(angles):
        base_radius = 1.0
        # Add some coastal irregularities
        if i < 10:  # Northern part - wider
            variation = 1.2 + 0.3 * np.sin(angle * 3)
        elif i < 25:  # Eastern coast - more irregular
            variation = 0.8 + 0.4 * np.sin(angle * 5)
        elif i < 35:  # Southern part - narrower
            variation = 0.6 + 0.2 * np.sin(angle * 4)
        else:  # Western coast - smoother
            variation = 1.0 + 0.3 * np.sin(angle * 2)
        radius_variations.append(base_radius * variation)
    
    # Convert to coordinates
    x_coords = center_lon + np.array(radius_variations) * np.cos(angles) * width
    y_coords = center_lat + np.array(radius_variations) * np.sin(angles) * height
    
    return list(zip(x_coords, y_coords))

def create_corfu_geographic_map(hotels_data, output_file='corfu_geographic_styled_map.png'):
    """Create a geographic-style map similar to the reference ATTIKH map"""
    
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
                colors.append(get_star_color_intensity(star_rating))
                    
            except (ValueError, TypeError):
                continue
    
    if not latitudes:
        print("No valid coordinates found!")
        return
    
    # Create figure with similar proportions to reference
    fig, ax = plt.subplots(1, 1, figsize=(10, 14))
    
    # Set background color (light blue for sea)
    ax.set_facecolor('#E6F3FF')
    
    # Calculate center and bounds
    center_lat = np.mean(latitudes)
    center_lon = np.mean(longitudes)
    lat_range = max(latitudes) - min(latitudes)
    lon_range = max(longitudes) - min(longitudes)
    
    # Create Corfu island shape
    island_shape = create_corfu_shape(center_lon, center_lat, lon_range * 0.6, lat_range * 0.8)
    
    # Draw the island
    island_poly = patches.Polygon(island_shape, facecolor='#FFFACD', edgecolor='#8B4513', 
                                 linewidth=2, alpha=0.9, zorder=1)
    ax.add_patch(island_poly)
    
    # Set map bounds with padding
    padding = 0.15
    ax.set_xlim(min(longitudes) - lon_range * padding, max(longitudes) + lon_range * padding)
    ax.set_ylim(min(latitudes) - lat_range * padding, max(latitudes) + lat_range * padding)
    
    # Plot hotels with varying sizes and colors
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
    scatter = ax.scatter(longitudes, latitudes, c=colors, s=sizes, alpha=0.8, 
                        edgecolors='black', linewidth=0.5, zorder=5)
    
    # Add title similar to reference
    ax.text(0.5, 0.98, 'Detailed Hotel Distribution in CORFU\nIonian Islands (EL62)', 
            transform=ax.transAxes, fontsize=16, fontweight='bold', ha='center', va='top')
    
    # Count statistics
    star_counts = Counter(star_ratings)
    total_hotels = len(latitudes)
    
    # Create statistics box similar to reference
    stats_text = "Region Statistics\n"
    stats_text += f"CORFU: EL62\n"
    stats_text += f"Hotels in Region: {total_hotels}\n"
    stats_text += f"Geocoded: {total_hotels}\n"
    
    # Get unique locations
    locations = set()
    for hotel in hotels_data:
        if hotel.get('address'):
            # Extract location from address
            parts = hotel['address'].split(',')
            if len(parts) > 1:
                location = parts[1].strip()
                if location and location != 'Corfu':
                    locations.add(location)
    
    stats_text += f"Sub-regions: {len(locations)}\n"
    stats_text += f"With Hotels: {len(locations)}"
    
    # Add statistics box
    props = dict(boxstyle='round', facecolor='lightblue', alpha=0.9, edgecolor='black')
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props, fontfamily='monospace')
    
    # Add some location labels for major areas
    if len(latitudes) > 10:
        # Group hotels by approximate regions
        north_hotels = [(lat, lon) for lat, lon in zip(latitudes, longitudes) if lat > center_lat + lat_range * 0.2]
        south_hotels = [(lat, lon) for lat, lon in zip(latitudes, longitudes) if lat < center_lat - lat_range * 0.2]
        
        if north_hotels:
            north_lat = np.mean([h[0] for h in north_hotels])
            north_lon = np.mean([h[1] for h in north_hotels])
            ax.annotate('Northern Corfu', (north_lon, north_lat), xytext=(10, 10), 
                       textcoords='offset points', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        if south_hotels:
            south_lat = np.mean([h[0] for h in south_hotels])
            south_lon = np.mean([h[1] for h in south_hotels])
            ax.annotate('Southern Corfu', (south_lon, south_lat), xytext=(10, -20), 
                       textcoords='offset points', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Create legend similar to reference
    legend_elements = []
    legend_labels = []
    
    for rating in ['5', '4', '3', '2', '1']:
        count = star_counts.get(rating, 0)
        if count > 0:
            color = get_star_color_intensity(rating)
            legend_elements.append(plt.Circle((0,0), 1, facecolor=color, alpha=0.8, edgecolor='black'))
            legend_labels.append(f"{rating}★: {count} hotels")
    
    # Add no rating if exists
    no_rating_count = star_counts.get('', 0)
    if no_rating_count > 0:
        legend_elements.append(plt.Circle((0,0), 1, facecolor=get_star_color_intensity(''), alpha=0.8, edgecolor='black'))
        legend_labels.append(f"No Rating: {no_rating_count} hotels")
    
    # Add legend
    legend = ax.legend(legend_elements, legend_labels, loc='lower right', 
                      title='Hotel Star Ratings', title_fontsize=12, fontsize=10,
                      frameon=True, fancybox=True, shadow=True)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_alpha(0.9)
    
    # Add colorbar similar to reference
    from matplotlib.colors import LinearSegmentedColormap
    colors_list = ['#FFFFE0', '#FFD700', '#FFA500', '#FF6347', '#CD5C5C', '#8B0000']
    n_bins = 100
    cmap = LinearSegmentedColormap.from_list('hotels', colors_list, N=n_bins)
    
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=max(star_counts.values())))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8, aspect=30, pad=0.08)
    cbar.set_label('Number of Hotels', rotation=270, labelpad=20, fontsize=12, fontweight='bold')
    
    # Set axis labels
    ax.set_xlabel('Longitude', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Add hotel location indicator
    ax.text(0.98, 0.02, '● Hotel Locations', transform=ax.transAxes, 
           fontsize=10, ha='right', va='bottom',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Set equal aspect ratio
    ax.set_aspect('equal', adjustable='box')
    
    # Remove top and right spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Save the map
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.show()
    
    print(f"Geographic-styled map saved as: {output_file}")
    print(f"Total hotels plotted: {len(latitudes)}")
    print(f"Star rating distribution: {dict(star_counts)}")

def main():
    """Main function to create geographic-styled map"""
    print("Creating ATTIKH-style geographic map of Corfu with hotel distribution...")
    
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
    
    # Create the geographic-styled map
    output_file = os.path.join(output_dir, 'corfu_geographic_styled_map.png')
    create_corfu_geographic_map(hotels_data, output_file)
    
    print(f"\n🗺️ GEOGRAPHIC-STYLED MAP CREATED!")
    print(f"📁 File saved at: {os.path.abspath(output_file)}")
    print(f"📊 Style: Similar to your ATTIKH NUTS3 reference map")
    print(f"🏨 Features: Island outline, hotel distribution, color-coded by star rating")

if __name__ == "__main__":
    main()