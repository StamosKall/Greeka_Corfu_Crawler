#!/usr/bin/env python3
"""
Individual Hotelling's Law Analysis Maps
Creates 4 separate, clear images for each analysis type
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.cluster import DBSCAN, KMeans
from sklearn.neighbors import NearestNeighbors
import seaborn as sns
from collections import Counter, defaultdict
import os
import osmnx as ox
import warnings
warnings.filterwarnings('ignore')

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_distances(coordinates):
    """Calculate distance matrix between all hotel pairs"""
    coords_array = np.array(coordinates)
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate the great circle distance between two points on earth (in km)"""
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371
        return c * r
    
    n = len(coordinates)
    distance_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i+1, n):
            dist = haversine_distance(coordinates[i][0], coordinates[i][1], 
                                    coordinates[j][0], coordinates[j][1])
            distance_matrix[i][j] = dist
            distance_matrix[j][i] = dist
    
    return distance_matrix

def calculate_competition_metrics(hotels_data, distance_matrix, max_distance_km=2.0):
    """Calculate competition metrics following Hotelling's Law principles"""
    
    coordinates = []
    star_ratings = []
    hotel_names = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                coordinates.append([lat, lon])
                star_ratings.append(hotel.get('star_rating', ''))
                hotel_names.append(hotel['name'])
            except (ValueError, TypeError):
                continue
    
    n_hotels = len(coordinates)
    competition_metrics = []
    
    for i in range(n_hotels):
        competitors_within_range = []
        competitor_ratings = []
        
        for j in range(n_hotels):
            if i != j and distance_matrix[i][j] <= max_distance_km:
                competitors_within_range.append(j)
                competitor_ratings.append(star_ratings[j])
        
        competition_intensity = len(competitors_within_range)
        
        own_rating = star_ratings[i]
        similar_rating_competitors = sum(1 for rating in competitor_ratings 
                                       if rating == own_rating and rating != '')
        
        avg_distance_to_competitors = (
            np.mean([distance_matrix[i][j] for j in competitors_within_range]) 
            if competitors_within_range else float('inf')
        )
        
        if len(competitors_within_range) >= 2:
            competitor_distances = []
            for j in competitors_within_range:
                for k in competitors_within_range:
                    if j < k:
                        competitor_distances.append(distance_matrix[j][k])
            clustering_coefficient = np.mean(competitor_distances) if competitor_distances else 0
        else:
            clustering_coefficient = 0
        
        competition_metrics.append({
            'hotel_index': i,
            'hotel_name': hotel_names[i],
            'star_rating': own_rating,
            'coordinates': coordinates[i],
            'competition_intensity': competition_intensity,
            'similar_rating_competitors': similar_rating_competitors,
            'avg_distance_to_competitors': avg_distance_to_competitors,
            'clustering_coefficient': clustering_coefficient,
            'competitors': competitors_within_range
        })
    
    return competition_metrics

def create_map1_competition_intensity(competition_metrics, output_file='map1_competition_intensity.png'):
    """Create Map 1: Competition Intensity Heat Map"""
    
    latitudes = [metric['coordinates'][0] for metric in competition_metrics]
    longitudes = [metric['coordinates'][1] for metric in competition_metrics]
    competition_intensities = [metric['competition_intensity'] for metric in competition_metrics]
    
    # Create figure with larger size for clarity
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    try:
        # Download Corfu boundary
        corfu = ox.geocode_to_gdf("Corfu, Greece")
        corfu.boundary.plot(ax=ax, color='navy', linewidth=3, alpha=0.8)
        bounds = corfu.total_bounds
        ax.set_xlim(bounds[0] - 0.01, bounds[2] + 0.01)
        ax.set_ylim(bounds[1] - 0.01, bounds[3] + 0.01)
    except:
        print("Using simplified boundaries...")
    
    # Competition intensity scatter plot
    scatter = ax.scatter(longitudes, latitudes, 
                        c=competition_intensities, 
                        s=[100 + intensity * 25 for intensity in competition_intensities],
                        cmap='Reds', alpha=0.8, edgecolors='white', linewidth=1.5)
    
    # Styling
    ax.set_title('Hotel Competition Intensity Map\n(Hotelling\'s Law - Spatial Competition)', 
                fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Longitude', fontsize=16, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.4, linestyle='--')
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('Number of Competitors within 2km', fontsize=14, fontweight='bold')
    cbar.ax.tick_params(labelsize=12)
    
    # Add statistics text box
    stats_text = f"""Competition Statistics:
• Total Hotels: {len(competition_metrics)}
• Avg Competitors: {np.mean(competition_intensities):.1f}
• Max Competition: {max(competition_intensities)} competitors
• High Competition Areas: {sum(1 for x in competition_intensities if x >= 5)} hotels"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8),
            fontsize=12, verticalalignment='top', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    print(f"Map 1 saved: {output_file}")

def create_map2_clustering_analysis(competition_metrics, output_file='map2_clustering_analysis.png'):
    """Create Map 2: Geographic Clustering Patterns"""
    
    latitudes = [metric['coordinates'][0] for metric in competition_metrics]
    longitudes = [metric['coordinates'][1] for metric in competition_metrics]
    coordinates = np.array([[lat, lon] for lat, lon in zip(latitudes, longitudes)])
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    try:
        # Download Corfu boundary
        corfu = ox.geocode_to_gdf("Corfu, Greece")
        corfu.boundary.plot(ax=ax, color='navy', linewidth=3, alpha=0.8)
        bounds = corfu.total_bounds
        ax.set_xlim(bounds[0] - 0.01, bounds[2] + 0.01)
        ax.set_ylim(bounds[1] - 0.01, bounds[3] + 0.01)
    except:
        print("Using simplified boundaries...")
    
    # DBSCAN clustering
    dbscan = DBSCAN(eps=0.015, min_samples=3)
    cluster_labels = dbscan.fit_predict(coordinates)
    
    # Create color map for clusters
    unique_labels = set(cluster_labels)
    n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
    n_noise = list(cluster_labels).count(-1)
    
    # Use a color palette with enough colors
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_labels)))
    
    for label, color in zip(unique_labels, colors):
        if label == -1:
            # Noise points (isolated hotels)
            mask = cluster_labels == label
            ax.scatter(np.array(longitudes)[mask], np.array(latitudes)[mask], 
                      c='black', marker='X', s=150, alpha=0.9, 
                      label=f'Isolated Hotels ({n_noise})', linewidth=2)
        else:
            mask = cluster_labels == label
            cluster_size = np.sum(mask)
            ax.scatter(np.array(longitudes)[mask], np.array(latitudes)[mask],
                      c=[color], s=120, alpha=0.8, 
                      label=f'Cluster {label + 1} ({cluster_size} hotels)',
                      edgecolors='white', linewidth=1)
    
    ax.set_title('Hotel Geographic Clustering Patterns\n(DBSCAN Clustering Analysis)', 
                fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Longitude', fontsize=16, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.4, linestyle='--')
    
    # Legend with better positioning
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10, framealpha=0.9)
    
    # Add statistics text box
    clustering_rate = ((len(coordinates) - n_noise) / len(coordinates)) * 100
    stats_text = f"""Clustering Statistics:
• Total Clusters: {n_clusters}
• Hotels in Clusters: {len(coordinates) - n_noise}
• Isolated Hotels: {n_noise}
• Clustering Rate: {clustering_rate:.1f}%"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgreen", alpha=0.8),
            fontsize=12, verticalalignment='top', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    print(f"Map 2 saved: {output_file}")

def create_map3_rating_competition(competition_metrics, output_file='map3_rating_competition.png'):
    """Create Map 3: Star Rating Competition Analysis"""
    
    latitudes = [metric['coordinates'][0] for metric in competition_metrics]
    longitudes = [metric['coordinates'][1] for metric in competition_metrics]
    star_ratings_numeric = [metric['similar_rating_competitors'] for metric in competition_metrics]
    star_ratings = [metric['star_rating'] for metric in competition_metrics]
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    try:
        # Download Corfu boundary
        corfu = ox.geocode_to_gdf("Corfu, Greece")
        corfu.boundary.plot(ax=ax, color='navy', linewidth=3, alpha=0.8)
        bounds = corfu.total_bounds
        ax.set_xlim(bounds[0] - 0.01, bounds[2] + 0.01)
        ax.set_ylim(bounds[1] - 0.01, bounds[3] + 0.01)
    except:
        print("Using simplified boundaries...")
    
    # Rating-based competition scatter plot
    scatter = ax.scatter(longitudes, latitudes,
                        c=star_ratings_numeric,
                        s=[120 + count * 40 for count in star_ratings_numeric],
                        cmap='coolwarm', alpha=0.8, edgecolors='white', linewidth=1.5)
    
    ax.set_title('Star Rating Competition Analysis\n(Similar Rating Competitors)', 
                fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Longitude', fontsize=16, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.4, linestyle='--')
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('Number of Similar Rating Competitors', fontsize=14, fontweight='bold')
    cbar.ax.tick_params(labelsize=12)
    
    # Calculate rating statistics
    rating_stats = defaultdict(list)
    for metric in competition_metrics:
        rating = metric['star_rating'] if metric['star_rating'] else 'No Rating'
        rating_stats[rating].append(metric['similar_rating_competitors'])
    
    # Add statistics text box
    stats_text = "Rating Competition:\n"
    for rating, competitions in rating_stats.items():
        if competitions:
            avg_comp = np.mean(competitions)
            stats_text += f"• {rating} Stars: {avg_comp:.1f} avg\n"
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8),
            fontsize=12, verticalalignment='top', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    print(f"Map 3 saved: {output_file}")

def create_map4_distance_analysis(competition_metrics, output_file='map4_distance_analysis.png'):
    """Create Map 4: Distance to Competitors Analysis"""
    
    latitudes = [metric['coordinates'][0] for metric in competition_metrics]
    longitudes = [metric['coordinates'][1] for metric in competition_metrics]
    avg_distances = [metric['avg_distance_to_competitors'] if metric['avg_distance_to_competitors'] != float('inf') 
                    else 5.0 for metric in competition_metrics]
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    try:
        # Download Corfu boundary
        corfu = ox.geocode_to_gdf("Corfu, Greece")
        corfu.boundary.plot(ax=ax, color='navy', linewidth=3, alpha=0.8)
        bounds = corfu.total_bounds
        ax.set_xlim(bounds[0] - 0.01, bounds[2] + 0.01)
        ax.set_ylim(bounds[1] - 0.01, bounds[3] + 0.01)
    except:
        print("Using simplified boundaries...")
    
    # Distance analysis scatter plot
    scatter = ax.scatter(longitudes, latitudes,
                        c=avg_distances,
                        s=120, cmap='viridis_r', alpha=0.8, 
                        edgecolors='white', linewidth=1.5)
    
    ax.set_title('Average Distance to Competitors\n(Spatial Distribution Patterns)', 
                fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Longitude', fontsize=16, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.4, linestyle='--')
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('Average Distance to Competitors (km)', fontsize=14, fontweight='bold')
    cbar.ax.tick_params(labelsize=12)
    
    # Calculate distance statistics
    valid_distances = [d for d in avg_distances if d != 5.0]
    min_dist = min(valid_distances) if valid_distances else 0
    max_dist = max(valid_distances) if valid_distances else 0
    avg_dist = np.mean(valid_distances) if valid_distances else 0
    
    # Add statistics text box
    stats_text = f"""Distance Statistics:
• Min Distance: {min_dist:.2f} km
• Avg Distance: {avg_dist:.2f} km
• Max Distance: {max_dist:.2f} km
• Isolated Hotels: {avg_distances.count(5.0)}"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightcoral", alpha=0.8),
            fontsize=12, verticalalignment='top', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    print(f"Map 4 saved: {output_file}")

def main():
    """Main function to create all 4 individual maps"""
    print("Creating Individual Hotelling's Law Analysis Maps...")
    
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
    
    # Extract coordinates and calculate distances
    coordinates = []
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                coordinates.append([lat, lon])
            except (ValueError, TypeError):
                continue
    
    print(f"Analyzing {len(coordinates)} hotels with valid coordinates...")
    
    # Calculate distance matrix
    print("Calculating distance matrix...")
    distance_matrix = calculate_distances(coordinates)
    
    # Analyze competition metrics
    print("Analyzing competition patterns...")
    competition_metrics = calculate_competition_metrics(hotels_data, distance_matrix)
    
    # Create output directory
    output_dir = 'data' if os.path.exists('data') else '../data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create individual maps
    print("\nCreating Map 1: Competition Intensity...")
    create_map1_competition_intensity(competition_metrics, 
                                     os.path.join(output_dir, 'map1_competition_intensity.png'))
    
    print("\nCreating Map 2: Clustering Analysis...")
    create_map2_clustering_analysis(competition_metrics, 
                                   os.path.join(output_dir, 'map2_clustering_analysis.png'))
    
    print("\nCreating Map 3: Rating Competition...")
    create_map3_rating_competition(competition_metrics, 
                                  os.path.join(output_dir, 'map3_rating_competition.png'))
    
    print("\nCreating Map 4: Distance Analysis...")
    create_map4_distance_analysis(competition_metrics, 
                                 os.path.join(output_dir, 'map4_distance_analysis.png'))
    
    print(f"\n🎯 ALL 4 INDIVIDUAL MAPS CREATED!")
    print(f"📁 Location: {output_dir}/")
    print(f"📊 Files:")
    print(f"   🔥 map1_competition_intensity.png - Competition heat map")
    print(f"   🌍 map2_clustering_analysis.png - Geographic clusters")
    print(f"   ⭐ map3_rating_competition.png - Star rating competition")
    print(f"   📏 map4_distance_analysis.png - Distance patterns")

if __name__ == "__main__":
    main()