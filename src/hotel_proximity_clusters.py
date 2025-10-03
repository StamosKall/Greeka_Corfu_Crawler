#!/usr/bin/env python3
"""
Hotel Proximity Clustering Analysis - Heat Map Style
Creates the color-coded proximity map you requested where nearby hotels get different colors
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import seaborn as sns
from matplotlib.colors import ListedColormap
import osmnx as ox
import warnings
warnings.filterwarnings('ignore')

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_proximity_clustering_map(hotels_data, output_file='hotel_proximity_clusters.png'):
    """Create the proximity-based clustering map with different colors for nearby hotels"""
    
    # Extract coordinates and prepare data
    coordinates = []
    hotel_names = []
    star_ratings = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                coordinates.append([lat, lon])
                hotel_names.append(hotel['name'][:30] + '...' if len(hotel['name']) > 30 else hotel['name'])
                star_ratings.append(hotel.get('star_rating', ''))
            except (ValueError, TypeError):
                continue
    
    coordinates = np.array(coordinates)
    
    # Get real Corfu map boundaries
    print("Downloading Corfu map data...")
    try:
        # Download Corfu administrative boundary
        corfu = ox.geocode_to_gdf("Corfu, Greece")
        
        # Get the boundary
        bounds = corfu.total_bounds  # minx, miny, maxx, maxy
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(24, 20))
        
        # Plot 1: DBSCAN Clustering with different eps values
        eps_values = [0.008, 0.015, 0.025]  # Different clustering sensitivities
        colors = ['viridis', 'plasma', 'coolwarm']
        
        for i, (eps, cmap_name) in enumerate(zip(eps_values, colors)):
            ax = [ax1, ax2, ax3][i]
            
            # Apply DBSCAN clustering
            dbscan = DBSCAN(eps=eps, min_samples=2)
            cluster_labels = dbscan.fit_predict(coordinates)
            
            # Count clusters and noise
            n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            n_noise = list(cluster_labels).count(-1)
            
            # Plot Corfu boundary
            corfu.boundary.plot(ax=ax, color='navy', linewidth=2, alpha=0.6)
            
            # Create custom colormap for clusters
            unique_labels = set(cluster_labels)
            if len(unique_labels) > 1:
                cmap = plt.cm.get_cmap(cmap_name, len(unique_labels))
                
                # Plot each cluster with different colors
                for label in unique_labels:
                    if label == -1:
                        # Noise points (isolated hotels) - black
                        mask = cluster_labels == label
                        ax.scatter(coordinates[mask, 1], coordinates[mask, 0], 
                                 c='black', marker='x', s=120, alpha=0.8, 
                                 label=f'Isolated ({n_noise} hotels)', linewidth=2)
                    else:
                        # Clustered points
                        mask = cluster_labels == label
                        cluster_coords = coordinates[mask]
                        cluster_size = np.sum(mask)
                        
                        # Use different sizes based on cluster size
                        size = 80 + cluster_size * 15
                        ax.scatter(cluster_coords[:, 1], cluster_coords[:, 0],
                                 c=[cmap(label)], s=size, alpha=0.8,
                                 label=f'Cluster {label+1} ({cluster_size} hotels)',
                                 edgecolors='white', linewidth=1)
            
            ax.set_title(f'Hotel Proximity Clusters (eps={eps})\n'
                        f'{n_clusters} clusters, {n_noise} isolated hotels', 
                        fontsize=16, fontweight='bold')
            ax.set_xlabel('Longitude', fontsize=12)
            ax.set_ylabel('Latitude', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.set_xlim(bounds[0] - 0.01, bounds[2] + 0.01)
            ax.set_ylim(bounds[1] - 0.01, bounds[3] + 0.01)
        
        # Plot 4: Heat Density Map
        corfu.boundary.plot(ax=ax4, color='navy', linewidth=2, alpha=0.6)
        
        # Create density-based heat map
        from scipy.stats import gaussian_kde
        
        # Calculate point density
        xy = coordinates.T
        kde = gaussian_kde(xy)
        density = kde(xy)
        
        # Plot with density-based colors
        scatter = ax4.scatter(coordinates[:, 1], coordinates[:, 0], 
                            c=density, s=100, cmap='hot', alpha=0.8,
                            edgecolors='white', linewidth=1)
        
        ax4.set_title('Hotel Density Heat Map\n(Warmer colors = Higher hotel density)', 
                     fontsize=16, fontweight='bold')
        ax4.set_xlabel('Longitude', fontsize=12)
        ax4.set_ylabel('Latitude', fontsize=12)
        ax4.grid(True, alpha=0.3)
        
        # Add colorbar for density
        cbar = plt.colorbar(scatter, ax=ax4)
        cbar.set_label('Hotel Density', fontsize=12)
        
        ax4.set_xlim(bounds[0] - 0.01, bounds[2] + 0.01)
        ax4.set_ylim(bounds[1] - 0.01, bounds[3] + 0.01)
        
        # Add main title
        fig.suptitle('Corfu Hotels - Proximity Clustering Analysis\n'
                    'Different Colors Show Hotels That Are Near Each Other', 
                    fontsize=20, fontweight='bold', y=0.95)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.show()
        
        print(f"Proximity clustering map saved as: {output_file}")
        
        # Return clustering results for the optimal eps
        optimal_eps = 0.015
        dbscan_optimal = DBSCAN(eps=optimal_eps, min_samples=2)
        optimal_clusters = dbscan_optimal.fit_predict(coordinates)
        
        return optimal_clusters, coordinates, hotel_names
        
    except Exception as e:
        print(f"Error downloading map data: {e}")
        print("Creating simplified clustering map...")
        
        # Fallback: Simple clustering without map
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
        
        # DBSCAN clustering
        dbscan = DBSCAN(eps=0.015, min_samples=2)
        cluster_labels = dbscan.fit_predict(coordinates)
        
        # Plot clusters
        unique_labels = set(cluster_labels)
        colors = plt.cm.Set1(np.linspace(0, 1, len(unique_labels)))
        
        for label, color in zip(unique_labels, colors):
            if label == -1:
                mask = cluster_labels == label
                ax1.scatter(coordinates[mask, 1], coordinates[mask, 0], 
                           c='black', marker='x', s=100, alpha=0.7, label='Isolated')
            else:
                mask = cluster_labels == label
                ax1.scatter(coordinates[mask, 1], coordinates[mask, 0],
                           c=[color], s=100, alpha=0.7, label=f'Cluster {label + 1}')
        
        ax1.set_title('Hotel Proximity Clusters', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Longitude')
        ax1.set_ylabel('Latitude')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Density plot
        from scipy.stats import gaussian_kde
        xy = coordinates.T
        kde = gaussian_kde(xy)
        density = kde(xy)
        
        scatter = ax2.scatter(coordinates[:, 1], coordinates[:, 0], 
                            c=density, s=100, cmap='hot', alpha=0.8)
        ax2.set_title('Hotel Density', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Longitude')
        ax2.set_ylabel('Latitude')
        plt.colorbar(scatter, ax=ax2)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.show()
        
        return cluster_labels, coordinates, hotel_names

def analyze_clustering_results(cluster_labels, coordinates, hotel_names):
    """Analyze and report clustering results"""
    print("\n" + "="*80)
    print("HOTEL PROXIMITY CLUSTERING RESULTS")
    print("="*80)
    
    # Basic cluster statistics
    unique_labels = set(cluster_labels)
    n_clusters = len(unique_labels) - (1 if -1 in cluster_labels else 0)
    n_noise = list(cluster_labels).count(-1)
    
    print(f"\n📊 CLUSTERING SUMMARY:")
    print(f"Total Clusters Found: {n_clusters}")
    print(f"Hotels in Clusters: {len(coordinates) - n_noise}")
    print(f"Isolated Hotels: {n_noise}")
    print(f"Clustering Rate: {((len(coordinates) - n_noise) / len(coordinates) * 100):.1f}%")
    
    # Analyze each cluster
    print(f"\n🏨 CLUSTER DETAILS:")
    cluster_stats = {}
    
    for label in unique_labels:
        if label != -1:  # Skip noise points
            mask = cluster_labels == label
            cluster_coords = coordinates[mask]
            cluster_hotels = [hotel_names[i] for i in range(len(hotel_names)) if mask[i]]
            
            # Calculate cluster center and spread
            center_lat = np.mean(cluster_coords[:, 0])
            center_lon = np.mean(cluster_coords[:, 1])
            
            # Calculate distances from center
            distances = []
            for coord in cluster_coords:
                dist = np.sqrt((coord[0] - center_lat)**2 + (coord[1] - center_lon)**2) * 111  # Rough km conversion
                distances.append(dist)
            
            cluster_stats[label] = {
                'size': len(cluster_hotels),
                'center': (center_lat, center_lon),
                'max_spread_km': max(distances),
                'hotels': cluster_hotels
            }
            
            print(f"\n  Cluster {label + 1}: {len(cluster_hotels)} hotels")
            print(f"    Center: {center_lat:.4f}, {center_lon:.4f}")
            print(f"    Max spread: {max(distances):.2f} km")
            print(f"    Hotels: {', '.join(cluster_hotels[:3])}{'...' if len(cluster_hotels) > 3 else ''}")
    
    # Hotelling's Law implications
    print(f"\n🎯 HOTELLING'S LAW IMPLICATIONS:")
    if n_clusters > 5 and (len(coordinates) - n_noise) / len(coordinates) > 0.7:
        print("✅ STRONG clustering behavior detected!")
        print("   - Hotels clearly prefer to locate near competitors")
        print("   - Multiple competition zones identified")
        print("   - Supports Hotelling's Law of spatial competition")
    elif n_clusters > 2:
        print("⚠️  MODERATE clustering detected")
        print("   - Some evidence of spatial competition")
        print("   - Mixed strategy of clustering and dispersion")
    else:
        print("❌ LIMITED clustering detected")
        print("   - Hotels tend to avoid direct spatial competition")
        print("   - Suggests market differentiation strategy")
    
    return cluster_stats

def main():
    """Main function to run proximity clustering analysis"""
    print("Starting Hotel Proximity Clustering Analysis...")
    
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
    import os
    output_dir = 'data' if os.path.exists('data') else '../data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create proximity clustering map
    output_file = os.path.join(output_dir, 'hotel_proximity_clusters.png')
    cluster_labels, coordinates, hotel_names = create_proximity_clustering_map(hotels_data, output_file)
    
    # Analyze clustering results
    cluster_stats = analyze_clustering_results(cluster_labels, coordinates, hotel_names)
    
    # Save results
    results_file = os.path.join(output_dir, 'proximity_clustering_results.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'cluster_statistics': cluster_stats,
            'summary': {
                'total_hotels': len(coordinates),
                'n_clusters': len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0),
                'isolated_hotels': list(cluster_labels).count(-1),
                'clustering_rate': ((len(coordinates) - list(cluster_labels).count(-1)) / len(coordinates))
            }
        }, f, indent=2, default=str)
    
    print(f"\n🎯 ANALYSIS COMPLETE!")
    print(f"📁 Files created:")
    print(f"   📊 Proximity Map: {os.path.basename(output_file)}")
    print(f"   📋 Clustering Results: {os.path.basename(results_file)}")

if __name__ == "__main__":
    main()