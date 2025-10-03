#!/usr/bin/env python3
"""
Hotelling's Law Analysis for Corfu Hotels
Analyzes spatial competition patterns and clustering behavior of hotels
Creates visualizations showing proximity-based clustering and competition zones
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

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_distances(coordinates):
    """Calculate distance matrix between all hotel pairs"""
    # Convert coordinates to numpy array
    coords_array = np.array(coordinates)
    
    # Calculate pairwise distances using Haversine formula for geographic coordinates
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate the great circle distance between two points on earth (in km)"""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Radius of earth in kilometers
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

def analyze_clustering_patterns(coordinates, min_samples=3, eps_range=[0.5, 1.0, 1.5, 2.0]):
    """Analyze different clustering patterns using DBSCAN"""
    results = {}
    
    for eps in eps_range:
        # DBSCAN clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='haversine')
        coords_rad = np.radians(coordinates)  # Convert to radians for haversine
        cluster_labels = dbscan.fit_predict(coords_rad)
        
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        results[eps] = {
            'labels': cluster_labels,
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'silhouette_score': 0  # Could add silhouette analysis
        }
    
    return results

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
        # Find competitors within max_distance_km
        competitors_within_range = []
        competitor_ratings = []
        
        for j in range(n_hotels):
            if i != j and distance_matrix[i][j] <= max_distance_km:
                competitors_within_range.append(j)
                competitor_ratings.append(star_ratings[j])
        
        # Calculate competition intensity
        competition_intensity = len(competitors_within_range)
        
        # Calculate rating competition (similar star ratings = higher competition)
        own_rating = star_ratings[i]
        similar_rating_competitors = sum(1 for rating in competitor_ratings 
                                       if rating == own_rating and rating != '')
        
        # Calculate average distance to competitors
        avg_distance_to_competitors = (
            np.mean([distance_matrix[i][j] for j in competitors_within_range]) 
            if competitors_within_range else float('inf')
        )
        
        # Calculate clustering coefficient (how clustered this hotel is)
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

def create_hotelling_analysis_map(hotels_data, competition_metrics, output_file='hotelling_analysis_map.png'):
    """Create comprehensive Hotelling's Law analysis visualization"""
    
    # Extract data for plotting
    latitudes = [metric['coordinates'][0] for metric in competition_metrics]
    longitudes = [metric['coordinates'][1] for metric in competition_metrics]
    competition_intensities = [metric['competition_intensity'] for metric in competition_metrics]
    
    # Create figure with multiple subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # 1. Competition Intensity Heat Map
    scatter1 = ax1.scatter(longitudes, latitudes, 
                          c=competition_intensities, 
                          s=[50 + intensity * 20 for intensity in competition_intensities],
                          cmap='Reds', alpha=0.7, edgecolors='black', linewidth=0.5)
    ax1.set_title('Hotel Competition Intensity\n(Hotelling\'s Law - Spatial Competition)', 
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.grid(True, alpha=0.3)
    cbar1 = plt.colorbar(scatter1, ax=ax1)
    cbar1.set_label('Number of Competitors within 2km')
    
    # 2. Clustering Analysis with DBSCAN
    coordinates = np.array([[lat, lon] for lat, lon in zip(latitudes, longitudes)])
    dbscan = DBSCAN(eps=0.01, min_samples=3)  # Adjust eps for geographic coordinates
    cluster_labels = dbscan.fit_predict(coordinates)
    
    # Create color map for clusters
    unique_labels = set(cluster_labels)
    colors = plt.cm.Set1(np.linspace(0, 1, len(unique_labels)))
    
    for label, color in zip(unique_labels, colors):
        if label == -1:
            # Noise points (isolated hotels)
            mask = cluster_labels == label
            ax2.scatter(np.array(longitudes)[mask], np.array(latitudes)[mask], 
                       c='black', marker='x', s=100, alpha=0.7, label='Isolated Hotels')
        else:
            mask = cluster_labels == label
            ax2.scatter(np.array(longitudes)[mask], np.array(latitudes)[mask],
                       c=[color], s=100, alpha=0.7, label=f'Cluster {label + 1}')
    
    ax2.set_title('Hotel Clustering Analysis\n(Geographic Clustering Patterns)', 
                  fontsize=14, fontweight='bold')
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. Star Rating Competition Map
    star_ratings_numeric = []
    colors_by_rating = []
    rating_color_map = {'5': 'darkgreen', '4': 'green', '3': 'orange', 
                       '2': 'red', '1': 'darkred', '': 'gray'}
    
    for metric in competition_metrics:
        rating = metric['star_rating']
        similar_competitors = metric['similar_rating_competitors']
        star_ratings_numeric.append(similar_competitors)
        colors_by_rating.append(rating_color_map.get(rating, 'gray'))
    
    scatter3 = ax3.scatter(longitudes, latitudes,
                          c=star_ratings_numeric,
                          s=[60 + count * 30 for count in star_ratings_numeric],
                          cmap='coolwarm', alpha=0.7, edgecolors='black', linewidth=0.5)
    ax3.set_title('Rating-Based Competition\n(Similar Star Rating Competition)', 
                  fontsize=14, fontweight='bold')
    ax3.set_xlabel('Longitude')
    ax3.set_ylabel('Latitude')
    ax3.grid(True, alpha=0.3)
    cbar3 = plt.colorbar(scatter3, ax=ax3)
    cbar3.set_label('Similar Rating Competitors')
    
    # 4. Distance to Competitors Analysis
    avg_distances = [metric['avg_distance_to_competitors'] if metric['avg_distance_to_competitors'] != float('inf') 
                    else 5.0 for metric in competition_metrics]  # Cap infinite distances
    
    scatter4 = ax4.scatter(longitudes, latitudes,
                          c=avg_distances,
                          s=80, cmap='viridis_r', alpha=0.7, 
                          edgecolors='black', linewidth=0.5)
    ax4.set_title('Average Distance to Competitors\n(Spatial Distribution Pattern)', 
                  fontsize=14, fontweight='bold')
    ax4.set_xlabel('Longitude')
    ax4.set_ylabel('Latitude')
    ax4.grid(True, alpha=0.3)
    cbar4 = plt.colorbar(scatter4, ax=ax4)
    cbar4.set_label('Average Distance (km)')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"Hotelling's Law analysis map saved as: {output_file}")

def generate_statistics_report(competition_metrics, distance_matrix):
    """Generate comprehensive statistics report for Hotelling's Law analysis"""
    
    print("\n" + "="*80)
    print("HOTELLING'S LAW ANALYSIS - CORFU HOTELS")
    print("="*80)
    
    # Basic statistics
    n_hotels = len(competition_metrics)
    competition_intensities = [m['competition_intensity'] for m in competition_metrics]
    avg_distances = [m['avg_distance_to_competitors'] for m in competition_metrics 
                    if m['avg_distance_to_competitors'] != float('inf')]
    
    print(f"\n📊 BASIC STATISTICS:")
    print(f"Total Hotels Analyzed: {n_hotels}")
    print(f"Average Competitors per Hotel (within 2km): {np.mean(competition_intensities):.2f}")
    print(f"Max Competition Intensity: {max(competition_intensities)} competitors")
    print(f"Hotels with No Nearby Competitors: {sum(1 for x in competition_intensities if x == 0)}")
    print(f"Average Distance to Nearest Competitors: {np.mean(avg_distances):.2f} km")
    
    # Hotelling's Law Evidence
    print(f"\n🏨 HOTELLING'S LAW EVIDENCE:")
    
    # Clustering tendency
    isolated_hotels = sum(1 for x in competition_intensities if x == 0)
    clustered_hotels = n_hotels - isolated_hotels
    clustering_percentage = (clustered_hotels / n_hotels) * 100
    
    print(f"Hotels in Clusters (have nearby competitors): {clustered_hotels} ({clustering_percentage:.1f}%)")
    print(f"Isolated Hotels: {isolated_hotels} ({100-clustering_percentage:.1f}%)")
    
    # Competition intensity distribution
    high_competition = sum(1 for x in competition_intensities if x >= 5)
    medium_competition = sum(1 for x in competition_intensities if 2 <= x < 5)
    low_competition = sum(1 for x in competition_intensities if 1 <= x < 2)
    
    print(f"\n📈 COMPETITION INTENSITY DISTRIBUTION:")
    print(f"High Competition Areas (5+ competitors): {high_competition} hotels")
    print(f"Medium Competition Areas (2-4 competitors): {medium_competition} hotels")
    print(f"Low Competition Areas (1 competitor): {low_competition} hotels")
    print(f"No Competition (isolated): {isolated_hotels} hotels")
    
    # Star rating competition analysis
    star_rating_competition = defaultdict(list)
    for metric in competition_metrics:
        rating = metric['star_rating'] if metric['star_rating'] else 'No Rating'
        star_rating_competition[rating].append(metric['similar_rating_competitors'])
    
    print(f"\n⭐ STAR RATING COMPETITION:")
    for rating, competitions in star_rating_competition.items():
        avg_competition = np.mean(competitions)
        print(f"{rating} Star Hotels: {avg_competition:.2f} avg similar-rating competitors")
    
    # Geographic clustering hotspots
    high_competition_hotels = [m for m in competition_metrics if m['competition_intensity'] >= 4]
    if high_competition_hotels:
        print(f"\n🔥 COMPETITION HOTSPOTS:")
        for hotel in high_competition_hotels[:5]:  # Top 5 most competitive locations
            lat, lon = hotel['coordinates']
            print(f"  • {hotel['hotel_name'][:50]}... ({hotel['competition_intensity']} competitors)")
            print(f"    Location: {lat:.4f}, {lon:.4f}")
    
    # Distance analysis
    print(f"\n📏 DISTANCE ANALYSIS:")
    print(f"Shortest Distance Between Hotels: {np.min(distance_matrix[distance_matrix > 0]):.3f} km")
    print(f"Longest Distance Between Hotels: {np.max(distance_matrix):.2f} km")
    print(f"Average Distance Between All Hotels: {np.mean(distance_matrix[distance_matrix > 0]):.2f} km")
    
    # Hotelling's Law conclusions
    print(f"\n🎯 HOTELLING'S LAW CONCLUSIONS:")
    if clustering_percentage > 60:
        print("✅ STRONG EVIDENCE for Hotelling's Law:")
        print("   - High clustering tendency suggests spatial competition")
        print("   - Hotels tend to locate near competitors")
    elif clustering_percentage > 40:
        print("⚠️  MODERATE EVIDENCE for Hotelling's Law:")
        print("   - Some clustering present but not dominant")
        print("   - Mixed strategy of clustering and differentiation")
    else:
        print("❌ WEAK EVIDENCE for Hotelling's Law:")
        print("   - Hotels tend to be more spatially dispersed")
        print("   - Suggests differentiation strategy over direct competition")
    
    if np.mean(avg_distances) < 1.0:
        print("   - Very close competitor proximity supports competition theory")
    elif np.mean(avg_distances) < 2.0:
        print("   - Moderate competitor proximity supports clustering tendency")
    else:
        print("   - Large competitor distances suggest market differentiation")
    
    return {
        'total_hotels': n_hotels,
        'clustering_percentage': clustering_percentage,
        'avg_competition_intensity': np.mean(competition_intensities),
        'avg_distance_to_competitors': np.mean(avg_distances),
        'hotelling_evidence_strength': 'Strong' if clustering_percentage > 60 else ('Moderate' if clustering_percentage > 40 else 'Weak')
    }

def main():
    """Main function to run Hotelling's Law analysis"""
    print("Starting Hotelling's Law Analysis for Corfu Hotels...")
    
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
    
    # Extract coordinates
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
    
    # Generate visualization
    print("Creating Hotelling's Law analysis map...")
    output_file = os.path.join(output_dir, 'hotelling_analysis_map.png')
    create_hotelling_analysis_map(hotels_data, competition_metrics, output_file)
    
    # Generate statistics report
    stats = generate_statistics_report(competition_metrics, distance_matrix)
    
    # Save detailed results
    results_file = os.path.join(output_dir, 'hotelling_analysis_results.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary_statistics': stats,
            'competition_metrics': competition_metrics,
            'analysis_parameters': {
                'max_competition_distance_km': 2.0,
                'total_hotels_analyzed': len(coordinates)
            }
        }, f, indent=2, default=str)
    
    print(f"\n🎯 ANALYSIS COMPLETE!")
    print(f"📁 Files created:")
    print(f"   📊 Visualization: {os.path.basename(output_file)}")
    print(f"   📋 Detailed Results: {os.path.basename(results_file)}")
    print(f"   📍 Evidence Strength: {stats['hotelling_evidence_strength']}")

if __name__ == "__main__":
    main()