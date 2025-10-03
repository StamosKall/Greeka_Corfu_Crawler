#!/usr/bin/env python3
"""
Same-Star Rating Clustering Analysis
Analyzes whether hotels with the same star rating cluster together or avoid each other
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import mannwhitneyu, ttest_ind
from sklearn.cluster import DBSCAN
import seaborn as sns
from collections import defaultdict, Counter
import pandas as pd
import os
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
    r = 6371  # Radius of earth in kilometers
    return c * r

def analyze_same_star_clustering(hotels_data):
    """Analyze clustering patterns for hotels with same star ratings"""
    
    # Extract hotel data with star ratings
    hotels_by_rating = defaultdict(list)
    all_hotels = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude') and hotel.get('star_rating'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                rating = hotel['star_rating'].strip()
                
                if rating:  # Only include hotels with actual ratings
                    hotel_info = {
                        'name': hotel['name'],
                        'lat': lat,
                        'lon': lon,
                        'rating': rating,
                        'coordinates': [lat, lon]
                    }
                    hotels_by_rating[rating].append(hotel_info)
                    all_hotels.append(hotel_info)
            except (ValueError, TypeError):
                continue
    
    print(f"Hotels by Star Rating:")
    for rating, hotels in hotels_by_rating.items():
        print(f"  {rating} stars: {len(hotels)} hotels")
    
    return hotels_by_rating, all_hotels

def calculate_same_star_distances(hotels_by_rating):
    """Calculate distances between hotels of the same star rating"""
    
    same_star_distances = {}
    same_star_stats = {}
    
    for rating, hotels in hotels_by_rating.items():
        if len(hotels) < 2:
            continue
            
        distances = []
        hotel_pairs = []
        
        # Calculate all pairwise distances within same rating
        for i in range(len(hotels)):
            for j in range(i+1, len(hotels)):
                hotel1 = hotels[i]
                hotel2 = hotels[j]
                
                distance = calculate_haversine_distance(
                    hotel1['lat'], hotel1['lon'],
                    hotel2['lat'], hotel2['lon']
                )
                
                distances.append(distance)
                hotel_pairs.append((hotel1['name'], hotel2['name'], distance))
        
        same_star_distances[rating] = distances
        same_star_stats[rating] = {
            'min_distance': min(distances),
            'max_distance': max(distances),
            'avg_distance': np.mean(distances),
            'median_distance': np.median(distances),
            'std_distance': np.std(distances),
            'total_pairs': len(distances),
            'closest_pair': min(hotel_pairs, key=lambda x: x[2]),
            'furthest_pair': max(hotel_pairs, key=lambda x: x[2])
        }
    
    return same_star_distances, same_star_stats

def calculate_cross_star_distances(hotels_by_rating):
    """Calculate distances between hotels of different star ratings"""
    
    cross_star_distances = {}
    
    ratings = list(hotels_by_rating.keys())
    
    for i, rating1 in enumerate(ratings):
        for j, rating2 in enumerate(ratings):
            if i >= j:  # Avoid duplicates and same-rating comparisons
                continue
                
            distances = []
            hotels1 = hotels_by_rating[rating1]
            hotels2 = hotels_by_rating[rating2]
            
            # Calculate distances between different rating groups
            for hotel1 in hotels1:
                for hotel2 in hotels2:
                    distance = calculate_haversine_distance(
                        hotel1['lat'], hotel1['lon'],
                        hotel2['lat'], hotel2['lon']
                    )
                    distances.append(distance)
            
            key = f"{rating1}★ vs {rating2}★"
            cross_star_distances[key] = {
                'distances': distances,
                'avg_distance': np.mean(distances),
                'median_distance': np.median(distances),
                'min_distance': min(distances),
                'total_comparisons': len(distances)
            }
    
    return cross_star_distances

def create_same_star_clustering_visualization(hotels_by_rating, same_star_stats, output_file='same_star_clustering.png'):
    """Create visualization showing same-star clustering patterns"""
    
    # Create figure with multiple subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # Subplot 1: Geographic map with star rating colors
    colors_by_rating = {
        '1': 'darkred', '2': 'red', '3': 'orange', 
        '4': 'green', '5': 'darkgreen'
    }
    
    for rating, hotels in hotels_by_rating.items():
        if len(hotels) > 0:
            lats = [h['lat'] for h in hotels]
            lons = [h['lon'] for h in hotels]
            color = colors_by_rating.get(rating, 'gray')
            
            ax1.scatter(lons, lats, c=color, s=100, alpha=0.7, 
                       label=f'{rating}★ ({len(hotels)} hotels)', 
                       edgecolors='white', linewidth=1)
    
    ax1.set_title('Hotels by Star Rating - Geographic Distribution', 
                  fontsize=16, fontweight='bold')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: Average distances between same-star hotels
    ratings = list(same_star_stats.keys())
    avg_distances = [same_star_stats[r]['avg_distance'] for r in ratings]
    
    bars = ax2.bar(ratings, avg_distances, color=['darkred', 'red', 'orange', 'green', 'darkgreen'][:len(ratings)], alpha=0.7)
    ax2.set_title('Average Distance Between Same-Star Hotels', fontsize=16, fontweight='bold')
    ax2.set_xlabel('Star Rating')
    ax2.set_ylabel('Average Distance (km)')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, distance in zip(bars, avg_distances):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{distance:.1f} km', ha='center', va='bottom', fontweight='bold')
    
    # Subplot 3: Distribution of same-star distances (box plot)
    same_star_distances_list = []
    rating_labels = []
    
    for rating in ratings:
        if rating in same_star_stats and same_star_stats[rating]['total_pairs'] > 0:
            # Create distance data for this rating
            distances = []
            hotels = hotels_by_rating[rating]
            for i in range(len(hotels)):
                for j in range(i+1, len(hotels)):
                    dist = calculate_haversine_distance(
                        hotels[i]['lat'], hotels[i]['lon'],
                        hotels[j]['lat'], hotels[j]['lon']
                    )
                    distances.append(dist)
            same_star_distances_list.append(distances)
            rating_labels.append(f'{rating}★')
    
    if same_star_distances_list:
        ax3.boxplot(same_star_distances_list, labels=rating_labels)
        ax3.set_title('Distance Distribution Between Same-Star Hotels', fontsize=16, fontweight='bold')
        ax3.set_ylabel('Distance (km)')
        ax3.grid(True, alpha=0.3)
    
    # Subplot 4: Nearest neighbor analysis
    nearest_distances = []
    rating_nearest = []
    
    for rating, hotels in hotels_by_rating.items():
        if len(hotels) > 1:
            for hotel in hotels:
                min_distance = float('inf')
                for other_hotel in hotels:
                    if hotel != other_hotel:
                        dist = calculate_haversine_distance(
                            hotel['lat'], hotel['lon'],
                            other_hotel['lat'], other_hotel['lon']
                        )
                        min_distance = min(min_distance, dist)
                
                if min_distance != float('inf'):
                    nearest_distances.append(min_distance)
                    rating_nearest.append(rating)
    
    # Create histogram of nearest neighbor distances by rating
    rating_colors = {'1': 'darkred', '2': 'red', '3': 'orange', '4': 'green', '5': 'darkgreen'}
    
    for rating in set(rating_nearest):
        rating_distances = [d for d, r in zip(nearest_distances, rating_nearest) if r == rating]
        ax4.hist(rating_distances, bins=10, alpha=0.6, 
                label=f'{rating}★ hotels', color=rating_colors.get(rating, 'gray'))
    
    ax4.set_title('Nearest Same-Star Neighbor Distances', fontsize=16, fontweight='bold')
    ax4.set_xlabel('Distance to Nearest Same-Star Hotel (km)')
    ax4.set_ylabel('Number of Hotels')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    print(f"Same-star clustering visualization saved: {output_file}")

def generate_same_star_analysis_report(same_star_stats, cross_star_distances):
    """Generate comprehensive report on same-star clustering patterns"""
    
    print("\n" + "="*80)
    print("SAME-STAR RATING CLUSTERING ANALYSIS")
    print("="*80)
    
    print(f"\n📊 DISTANCE ANALYSIS BY STAR RATING:")
    print("-" * 60)
    
    for rating, stats in same_star_stats.items():
        print(f"\n⭐ {rating}-STAR HOTELS:")
        print(f"   • Number of hotel pairs: {stats['total_pairs']}")
        print(f"   • Average distance: {stats['avg_distance']:.2f} km")
        print(f"   • Median distance: {stats['median_distance']:.2f} km")
        print(f"   • Min distance: {stats['min_distance']:.2f} km")
        print(f"   • Max distance: {stats['max_distance']:.2f} km")
        print(f"   • Closest pair: {stats['closest_pair'][0][:40]}... & {stats['closest_pair'][1][:40]}... ({stats['closest_pair'][2]:.2f} km)")
    
    print(f"\n🔄 CROSS-RATING COMPARISONS:")
    print("-" * 60)
    
    for comparison, data in cross_star_distances.items():
        print(f"\n{comparison}:")
        print(f"   • Average distance: {data['avg_distance']:.2f} km")
        print(f"   • Median distance: {data['median_distance']:.2f} km")
        print(f"   • Min distance: {data['min_distance']:.2f} km")
    
    # Analysis of clustering vs. avoidance
    print(f"\n🎯 CLUSTERING vs. AVOIDANCE ANALYSIS:")
    print("-" * 60)
    
    # Compare same-star vs cross-star distances
    same_star_averages = {rating: stats['avg_distance'] for rating, stats in same_star_stats.items()}
    cross_star_averages = {comp: data['avg_distance'] for comp, data in cross_star_distances.items()}
    
    overall_same_star_avg = np.mean(list(same_star_averages.values()))
    overall_cross_star_avg = np.mean(list(cross_star_averages.values()))
    
    print(f"\nOverall Patterns:")
    print(f"• Average distance between SAME-star hotels: {overall_same_star_avg:.2f} km")
    print(f"• Average distance between DIFFERENT-star hotels: {overall_cross_star_avg:.2f} km")
    
    if overall_same_star_avg < overall_cross_star_avg:
        clustering_behavior = "CLUSTERING"
        print(f"• 🎯 RESULT: Hotels with same star rating tend to CLUSTER together")
        print(f"• 📈 Same-star hotels are {overall_cross_star_avg - overall_same_star_avg:.2f} km closer on average")
        print(f"• 💡 INTERPRETATION: Hotels compete directly with similar-quality competitors")
    else:
        clustering_behavior = "AVOIDANCE"
        print(f"• 🎯 RESULT: Hotels with same star rating tend to AVOID each other")
        print(f"• 📈 Same-star hotels are {overall_same_star_avg - overall_cross_star_avg:.2f} km further apart on average")
        print(f"• 💡 INTERPRETATION: Hotels differentiate by avoiding direct quality competition")
    
    # Individual rating analysis
    print(f"\nBy Star Rating:")
    for rating in sorted(same_star_stats.keys()):
        stats = same_star_stats[rating]
        if stats['avg_distance'] < 15:  # Arbitrary threshold for "close"
            tendency = "CLUSTER together"
        else:
            tendency = "SPREAD apart"
        print(f"• {rating}★ hotels: {stats['avg_distance']:.1f} km avg → tend to {tendency}")
    
    # Statistical significance test (if enough data)
    if len(same_star_averages) > 2:
        # Simple comparison of variance
        same_star_variance = np.var(list(same_star_averages.values()))
        print(f"\nVariability in same-star distances: {same_star_variance:.2f}")
        if same_star_variance < 10:
            print("• Low variability → Consistent clustering patterns across ratings")
        else:
            print("• High variability → Different strategies by rating level")
    
    return {
        'clustering_behavior': clustering_behavior,
        'same_star_avg': overall_same_star_avg,
        'cross_star_avg': overall_cross_star_avg,
        'rating_patterns': same_star_averages
    }

def main():
    """Main function to analyze same-star clustering patterns"""
    print("Starting Same-Star Rating Clustering Analysis...")
    
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
    
    # Analyze same-star clustering
    hotels_by_rating, all_hotels = analyze_same_star_clustering(hotels_data)
    
    if not hotels_by_rating:
        print("No hotels with star ratings found!")
        return
    
    # Calculate distances
    print("\nCalculating same-star distances...")
    same_star_distances, same_star_stats = calculate_same_star_distances(hotels_by_rating)
    
    print("Calculating cross-star distances...")
    cross_star_distances = calculate_cross_star_distances(hotels_by_rating)
    
    # Create output directory
    output_dir = 'data' if os.path.exists('data') else '../data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create visualization
    output_file = os.path.join(output_dir, 'same_star_clustering_analysis.png')
    create_same_star_clustering_visualization(hotels_by_rating, same_star_stats, output_file)
    
    # Generate analysis report
    analysis_results = generate_same_star_analysis_report(same_star_stats, cross_star_distances)
    
    # Save detailed results
    results_file = os.path.join(output_dir, 'same_star_analysis_results.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': analysis_results,
            'same_star_statistics': same_star_stats,
            'cross_star_comparisons': cross_star_distances,
            'hotels_by_rating_count': {rating: len(hotels) for rating, hotels in hotels_by_rating.items()}
        }, f, indent=2, default=str)
    
    print(f"\n🎯 SAME-STAR ANALYSIS COMPLETE!")
    print(f"📁 Files created:")
    print(f"   📊 Visualization: {os.path.basename(output_file)}")
    print(f"   📋 Results: {os.path.basename(results_file)}")
    print(f"   🎯 Main Finding: Hotels show {analysis_results['clustering_behavior']} behavior with same-star ratings")

if __name__ == "__main__":
    main()