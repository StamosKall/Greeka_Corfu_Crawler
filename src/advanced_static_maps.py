#!/usr/bin/env python3
"""
Advanced Static Map Generator for Corfu Hotels
Creates multiple static maps with different visualizations
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import Counter

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_star_color(star_rating):
    """Get color based on star rating"""
    star_colors = {
        '5': '#1B5E20',  # Dark Green
        '4': '#4CAF50',  # Green
        '3': '#FFEB3B',  # Yellow
        '2': '#FF9800',  # Orange
        '1': '#F44336',  # Red
        '': '#757575'    # Gray
    }
    return star_colors.get(str(star_rating), '#757575')

def create_density_map(hotels_data, output_file='corfu_hotels_density_map.png'):
    """Create a density heat map of hotels"""
    
    # Extract coordinates
    latitudes = []
    longitudes = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
                latitudes.append(lat)
                longitudes.append(lon)
            except (ValueError, TypeError):
                continue
    
    if not latitudes:
        print("No valid coordinates found!")
        return
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # Density heat map
    hb = ax1.hexbin(longitudes, latitudes, gridsize=20, cmap='YlOrRd', alpha=0.7)
    ax1.set_xlabel('Longitude', fontsize=12)
    ax1.set_ylabel('Latitude', fontsize=12)
    ax1.set_title('Hotel Density Heat Map', fontsize=14, fontweight='bold')
    cb = plt.colorbar(hb, ax=ax1)
    cb.set_label('Number of Hotels', fontsize=12)
    
    # Scatter plot with star ratings
    colors = []
    sizes = []
    star_ratings = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            try:
                lat = float(hotel['latitude'])
                lon = float(hotel['longitude'])
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
    
    scatter = ax2.scatter(longitudes, latitudes, c=colors, s=sizes, alpha=0.7, 
                         edgecolors='white', linewidth=0.5)
    ax2.set_xlabel('Longitude', fontsize=12)
    ax2.set_ylabel('Latitude', fontsize=12)
    ax2.set_title('Hotels by Star Rating', fontsize=14, fontweight='bold')
    
    # Legend for scatter plot
    legend_elements = [
        plt.scatter([], [], c='#1B5E20', s=100, label='5 Stars', alpha=0.7, edgecolors='white'),
        plt.scatter([], [], c='#4CAF50', s=80, label='4 Stars', alpha=0.7, edgecolors='white'),
        plt.scatter([], [], c='#FFEB3B', s=60, label='3 Stars', alpha=0.7, edgecolors='white'),
        plt.scatter([], [], c='#FF9800', s=40, label='2 Stars', alpha=0.7, edgecolors='white'),
        plt.scatter([], [], c='#F44336', s=30, label='1 Star', alpha=0.7, edgecolors='white'),
        plt.scatter([], [], c='#757575', s=50, label='No Rating', alpha=0.7, edgecolors='white')
    ]
    ax2.legend(handles=legend_elements, loc='upper left', fontsize=10)
    
    # Add grids
    ax1.grid(True, alpha=0.3)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"Density map saved as: {output_file}")

def create_statistics_visualization(hotels_data, output_file='corfu_hotels_stats.png'):
    """Create statistical visualizations"""
    
    # Prepare data
    star_ratings = []
    review_scores = []
    review_counts = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            star_ratings.append(hotel.get('star_rating', 'No Rating'))
            
            try:
                score = float(hotel.get('review_score', 0))
                review_scores.append(score if score > 0 else None)
            except (ValueError, TypeError):
                review_scores.append(None)
            
            try:
                count = int(hotel.get('number_of_reviews', 0))
                review_counts.append(count if count > 0 else 0)
            except (ValueError, TypeError):
                review_counts.append(0)
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Star rating distribution
    star_counter = Counter(star_ratings)
    ratings = list(star_counter.keys())
    counts = list(star_counter.values())
    colors = [get_star_color(r if r != 'No Rating' else '') for r in ratings]
    
    bars = ax1.bar(ratings, counts, color=colors, alpha=0.8, edgecolor='black')
    ax1.set_xlabel('Star Rating', fontsize=12)
    ax1.set_ylabel('Number of Hotels', fontsize=12)
    ax1.set_title('Hotel Distribution by Star Rating', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add count labels on bars
    for bar, count in zip(bars, counts):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    # 2. Review score distribution
    valid_scores = [score for score in review_scores if score is not None]
    if valid_scores:
        ax2.hist(valid_scores, bins=20, color='skyblue', alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Review Score', fontsize=12)
        ax2.set_ylabel('Number of Hotels', fontsize=12)
        ax2.set_title('Review Score Distribution', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.axvline(np.mean(valid_scores), color='red', linestyle='--', 
                   label=f'Average: {np.mean(valid_scores):.2f}')
        ax2.legend()
    
    # 3. Review count distribution
    non_zero_counts = [count for count in review_counts if count > 0]
    if non_zero_counts:
        ax3.hist(non_zero_counts, bins=30, color='lightgreen', alpha=0.7, edgecolor='black')
        ax3.set_xlabel('Number of Reviews', fontsize=12)
        ax3.set_ylabel('Number of Hotels', fontsize=12)
        ax3.set_title('Review Count Distribution', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.set_yscale('log')  # Log scale due to wide range
    
    # 4. Star rating vs Review score scatter
    star_numeric = []
    corresponding_scores = []
    
    for i, (rating, score) in enumerate(zip(star_ratings, review_scores)):
        if rating.isdigit() and score is not None:
            star_numeric.append(int(rating))
            corresponding_scores.append(score)
    
    if star_numeric and corresponding_scores:
        ax4.scatter(star_numeric, corresponding_scores, alpha=0.6, s=30)
        ax4.set_xlabel('Star Rating', fontsize=12)
        ax4.set_ylabel('Review Score', fontsize=12)
        ax4.set_title('Star Rating vs Review Score', fontsize=14, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # Add trend line
        if len(star_numeric) > 1:
            z = np.polyfit(star_numeric, corresponding_scores, 1)
            p = np.poly1d(z)
            ax4.plot(star_numeric, p(star_numeric), "r--", alpha=0.8, 
                    label=f'Trend line')
            ax4.legend()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"Statistics visualization saved as: {output_file}")

def main():
    """Main function to create advanced visualizations"""
    print("Creating advanced visualizations for Corfu hotels...")
    
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
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file}")
        return
    
    # Create output directory
    output_dir = 'data' if os.path.exists('data') else '../data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create visualizations
    print("\n1. Creating density map...")
    create_density_map(hotels_data, os.path.join(output_dir, 'corfu_hotels_density_map.png'))
    
    print("\n2. Creating statistics visualization...")
    create_statistics_visualization(hotels_data, os.path.join(output_dir, 'corfu_hotels_stats.png'))
    
    print(f"\nAll visualizations created successfully!")
    print(f"Files saved in: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    main()