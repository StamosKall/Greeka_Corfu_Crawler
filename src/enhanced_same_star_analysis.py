#!/usr/bin/env python3
"""
Enhanced Same-Star Distance Analysis with Heat Maps
Creates detailed visualizations of distance patterns between same-star hotels
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from collections import defaultdict
import pandas as pd
import os
import osmnx as ox
import warnings
warnings.filterwarnings('ignore')

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on earth (in km)"""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371
    return c * r

def create_enhanced_same_star_maps(hotels_data, output_dir):
    """Create enhanced visualizations for same-star distance analysis"""
    
    # Extract hotel data by rating
    hotels_by_rating = defaultdict(list)
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude') and hotel.get('star_rating'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                rating = hotel['star_rating'].strip()
                
                if rating:
                    hotels_by_rating[rating].append({
                        'name': hotel['name'],
                        'lat': lat,
                        'lon': lon,
                        'rating': rating
                    })
            except (ValueError, TypeError):
                continue
    
    # Create individual maps for each star rating
    colors_by_rating = {'1': 'darkred', '2': 'red', '3': 'orange', '4': 'green', '5': 'darkgreen'}
    
    for rating, hotels in hotels_by_rating.items():
        if len(hotels) < 2:
            continue
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
        
        # Left plot: Geographic distribution with connection lines
        try:
            corfu = ox.geocode_to_gdf("Corfu, Greece")
            corfu.boundary.plot(ax=ax1, color='navy', linewidth=2, alpha=0.6)
            bounds = corfu.total_bounds
            ax1.set_xlim(bounds[0] - 0.01, bounds[2] + 0.01)
            ax1.set_ylim(bounds[1] - 0.01, bounds[3] + 0.01)
        except:
            pass
        
        # Plot hotel locations
        lats = [h['lat'] for h in hotels]
        lons = [h['lon'] for h in hotels]
        color = colors_by_rating.get(rating, 'gray')
        
        ax1.scatter(lons, lats, c=color, s=150, alpha=0.8, 
                   edgecolors='white', linewidth=2, zorder=5)
        
        # Draw connection lines for closest pairs (distance < 5km)
        close_pairs = []
        for i in range(len(hotels)):
            for j in range(i+1, len(hotels)):
                distance = calculate_haversine_distance(
                    hotels[i]['lat'], hotels[i]['lon'],
                    hotels[j]['lat'], hotels[j]['lon']
                )
                if distance < 5.0:  # Only show close pairs
                    ax1.plot([hotels[i]['lon'], hotels[j]['lon']], 
                            [hotels[i]['lat'], hotels[j]['lat']], 
                            color=color, alpha=0.4, linewidth=1, zorder=1)
                    close_pairs.append((i, j, distance))
        
        # Add hotel names for the closest ones
        if close_pairs:
            closest_pair = min(close_pairs, key=lambda x: x[2])
            i, j, dist = closest_pair
            ax1.annotate(f'{hotels[i]["name"][:20]}...', 
                        (hotels[i]['lon'], hotels[i]['lat']),
                        xytext=(5, 5), textcoords='offset points', 
                        fontsize=8, alpha=0.8)
            ax1.annotate(f'{hotels[j]["name"][:20]}...', 
                        (hotels[j]['lon'], hotels[j]['lat']),
                        xytext=(5, 5), textcoords='offset points', 
                        fontsize=8, alpha=0.8)
        
        ax1.set_title(f'{rating}-Star Hotels Geographic Distribution\n'
                     f'{len(hotels)} hotels, {len(close_pairs)} close pairs (<5km)', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlabel('Longitude')
        ax1.set_ylabel('Latitude')
        ax1.grid(True, alpha=0.3)
        
        # Right plot: Distance distribution histogram
        distances = []
        for i in range(len(hotels)):
            for j in range(i+1, len(hotels)):
                distance = calculate_haversine_distance(
                    hotels[i]['lat'], hotels[i]['lon'],
                    hotels[j]['lat'], hotels[j]['lon']
                )
                distances.append(distance)
        
        ax2.hist(distances, bins=15, color=color, alpha=0.7, edgecolor='white')
        ax2.axvline(np.mean(distances), color='red', linestyle='--', linewidth=2, 
                   label=f'Average: {np.mean(distances):.1f} km')
        ax2.axvline(np.median(distances), color='blue', linestyle='--', linewidth=2, 
                   label=f'Median: {np.median(distances):.1f} km')
        
        ax2.set_title(f'{rating}-Star Hotels Distance Distribution\n'
                     f'Between all {len(hotels)} hotels ({len(distances)} pairs)', 
                     fontsize=14, fontweight='bold')
        ax2.set_xlabel('Distance (km)')
        ax2.set_ylabel('Number of Hotel Pairs')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_text = f"""Statistics for {rating}★ Hotels:
• Min distance: {min(distances):.2f} km
• Max distance: {max(distances):.2f} km  
• Std deviation: {np.std(distances):.2f} km
• Close pairs (<2km): {sum(1 for d in distances if d < 2.0)}
• Very close (<1km): {sum(1 for d in distances if d < 1.0)}"""
        
        ax2.text(0.98, 0.98, stats_text, transform=ax2.transAxes,
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8),
                fontsize=10, verticalalignment='top', horizontalalignment='right')
        
        plt.tight_layout()
        output_file = os.path.join(output_dir, f'{rating}_star_detailed_analysis.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.show()
        print(f"Created detailed analysis for {rating}-star hotels: {os.path.basename(output_file)}")

def create_comparison_heatmap(hotels_data, output_file):
    """Create a heatmap comparing distances between different star rating combinations"""
    
    # Extract hotels by rating
    hotels_by_rating = defaultdict(list)
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude') and hotel.get('star_rating'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                rating = hotel['star_rating'].strip()
                
                if rating:
                    hotels_by_rating[rating].append({
                        'name': hotel['name'],
                        'lat': lat,
                        'lon': lon,
                        'rating': rating
                    })
            except (ValueError, TypeError):
                continue
    
    # Calculate average distances between all rating combinations
    ratings = sorted(hotels_by_rating.keys())
    distance_matrix = np.zeros((len(ratings), len(ratings)))
    
    for i, rating1 in enumerate(ratings):
        for j, rating2 in enumerate(ratings):
            distances = []
            
            if i == j:
                # Same rating - calculate internal distances
                hotels = hotels_by_rating[rating1]
                for k in range(len(hotels)):
                    for l in range(k+1, len(hotels)):
                        dist = calculate_haversine_distance(
                            hotels[k]['lat'], hotels[k]['lon'],
                            hotels[l]['lat'], hotels[l]['lon']
                        )
                        distances.append(dist)
            else:
                # Different ratings - calculate cross distances
                hotels1 = hotels_by_rating[rating1]
                hotels2 = hotels_by_rating[rating2]
                for hotel1 in hotels1:
                    for hotel2 in hotels2:
                        dist = calculate_haversine_distance(
                            hotel1['lat'], hotel1['lon'],
                            hotel2['lat'], hotel2['lon']
                        )
                        distances.append(dist)
            
            if distances:
                distance_matrix[i][j] = np.mean(distances)
            else:
                distance_matrix[i][j] = np.nan
    
    # Create heatmap
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Create labels
    labels = [f'{r}★' for r in ratings]
    
    # Create heatmap
    im = ax.imshow(distance_matrix, cmap='RdYlBu_r', aspect='equal')
    
    # Set ticks and labels
    ax.set_xticks(range(len(ratings)))
    ax.set_yticks(range(len(ratings)))
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_yticklabels(labels, fontsize=12)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Average Distance (km)', fontsize=12, fontweight='bold')
    
    # Add text annotations
    for i in range(len(ratings)):
        for j in range(len(ratings)):
            if not np.isnan(distance_matrix[i][j]):
                text = f'{distance_matrix[i][j]:.1f}'
                ax.text(j, i, text, ha="center", va="center", 
                       color="white" if distance_matrix[i][j] > np.nanmean(distance_matrix) else "black",
                       fontsize=11, fontweight='bold')
    
    ax.set_title('Average Distances Between Hotel Star Rating Groups\n'
                'Diagonal = Same-star distances, Off-diagonal = Cross-star distances', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('To Star Rating', fontsize=14, fontweight='bold')
    ax.set_ylabel('From Star Rating', fontsize=14, fontweight='bold')
    
    # Add interpretation text
    diagonal_avg = np.nanmean([distance_matrix[i][i] for i in range(len(ratings))])
    off_diagonal_avg = np.nanmean([distance_matrix[i][j] for i in range(len(ratings)) 
                                  for j in range(len(ratings)) if i != j])
    
    interpretation = f"""Key Insights:
• Same-star average: {diagonal_avg:.1f} km
• Cross-star average: {off_diagonal_avg:.1f} km
• {'Same-star hotels are CLOSER' if diagonal_avg < off_diagonal_avg else 'Same-star hotels are FURTHER'}
• Difference: {abs(diagonal_avg - off_diagonal_avg):.1f} km"""
    
    ax.text(1.15, 0.5, interpretation, transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9),
            fontsize=11, verticalalignment='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    print(f"Distance comparison heatmap saved: {os.path.basename(output_file)}")

def main():
    """Main function to create enhanced same-star analysis"""
    print("Creating Enhanced Same-Star Distance Analysis...")
    
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
    
    # Create enhanced maps for each star rating
    print("\nCreating detailed analysis for each star rating...")
    create_enhanced_same_star_maps(hotels_data, output_dir)
    
    # Create comparison heatmap
    print("\nCreating distance comparison heatmap...")
    heatmap_file = os.path.join(output_dir, 'star_rating_distance_heatmap.png')
    create_comparison_heatmap(hotels_data, heatmap_file)
    
    print(f"\n🎯 ENHANCED ANALYSIS COMPLETE!")
    print(f"📁 Created detailed maps for each star rating")
    print(f"📊 Created comprehensive distance heatmap")

if __name__ == "__main__":
    main()