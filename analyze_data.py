#!/usr/bin/env python3
"""
Data analysis script for Greeka Corfu hotels crawler results.
"""

import json
import csv
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List

def analyze_hotel_data(json_file: str = "hotels.json", csv_file: str = "hotels.csv"):
    """
    Analyze the crawled hotel data and generate insights.
    
    Args:
        json_file: Path to the JSON output file
        csv_file: Path to the CSV output file
    """
    
    # Load data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            hotels = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found. Please run the crawler first.")
        return
    
    print("=== GREEKA CORFU HOTELS DATA ANALYSIS ===\n")
    
    # Basic statistics
    total_hotels = len(hotels)
    print(f"📊 BASIC STATISTICS")
    print(f"Total hotels: {total_hotels}")
    
    # Data completeness analysis
    print(f"\n📈 DATA COMPLETENESS")
    fields = ['name', 'official_website', 'address', 'star_rating', 
              'review_score', 'number_of_reviews', 'phone_number', 
              'latitude', 'longitude']
    
    completeness = {}
    for field in fields:
        filled = sum(1 for h in hotels if h.get(field, '').strip())
        percentage = (filled / total_hotels) * 100 if total_hotels > 0 else 0
        completeness[field] = {'count': filled, 'percentage': percentage}
        print(f"  {field.replace('_', ' ').title()}: {filled}/{total_hotels} ({percentage:.1f}%)")
    
    # Star rating distribution
    print(f"\n⭐ STAR RATING DISTRIBUTION")
    star_ratings = [h.get('star_rating', '') for h in hotels if h.get('star_rating', '').strip()]
    if star_ratings:
        star_counter = Counter(star_ratings)
        for stars, count in sorted(star_counter.items()):
            print(f"  {stars} stars: {count} hotels")
    else:
        print("  No star rating data available")
    
    # Review score analysis
    print(f"\n📝 REVIEW SCORES")
    review_scores = [float(h.get('review_score', '0')) for h in hotels 
                    if h.get('review_score', '').strip() and h.get('review_score', '0') != '0']
    
    if review_scores:
        avg_score = sum(review_scores) / len(review_scores)
        min_score = min(review_scores)
        max_score = max(review_scores)
        print(f"  Average review score: {avg_score:.2f}/5.0")
        print(f"  Minimum score: {min_score:.1f}/5.0")
        print(f"  Maximum score: {max_score:.1f}/5.0")
        print(f"  Hotels with reviews: {len(review_scores)}")
    else:
        print("  No review score data available")
    
    # Location analysis
    print(f"\n📍 LOCATION DISTRIBUTION")
    locations = []
    for hotel in hotels:
        address = hotel.get('address', '')
        if address:
            # Extract location name from address
            parts = address.split(',')
            if len(parts) >= 2:
                location = parts[-2].strip()  # Usually the location is second to last
                locations.append(location)
    
    if locations:
        location_counter = Counter(locations)
        print("  Top locations:")
        for location, count in location_counter.most_common(10):
            print(f"    {location}: {count} hotels")
    else:
        print("  No location data available")
    
    # Website availability
    print(f"\n🌐 WEBSITE AVAILABILITY")
    with_website = sum(1 for h in hotels if h.get('official_website', '').strip())
    without_website = total_hotels - with_website
    print(f"  Hotels with official website: {with_website} ({(with_website/total_hotels)*100:.1f}%)")
    print(f"  Hotels without official website: {without_website} ({(without_website/total_hotels)*100:.1f}%)")
    
    # Phone number analysis
    print(f"\n📞 CONTACT INFORMATION")
    with_phone = sum(1 for h in hotels if h.get('phone_number', '').strip())
    print(f"  Hotels with phone numbers: {with_phone}/{total_hotels} ({(with_phone/total_hotels)*100:.1f}%)")
    
    # Coordinate availability
    print(f"\n🗺️  GEOGRAPHIC DATA")
    with_coords = sum(1 for h in hotels if h.get('latitude', '').strip() and h.get('longitude', '').strip())
    print(f"  Hotels with coordinates: {with_coords}/{total_hotels} ({(with_coords/total_hotels)*100:.1f}%)")
    
    # Data quality score
    print(f"\n🏆 OVERALL DATA QUALITY SCORE")
    total_possible = len(fields) * total_hotels
    total_filled = sum(completeness[field]['count'] for field in fields)
    quality_score = (total_filled / total_possible) * 100 if total_possible > 0 else 0
    
    print(f"  Quality Score: {quality_score:.1f}%")
    if quality_score >= 80:
        print("  📈 EXCELLENT - High data completeness")
    elif quality_score >= 60:
        print("  📊 GOOD - Moderate data completeness")
    elif quality_score >= 40:
        print("  📉 FAIR - Some data gaps present")
    else:
        print("  📋 NEEDS IMPROVEMENT - Significant data gaps")
    
    # Top hotels by review score
    print(f"\n🏅 TOP RATED HOTELS")
    hotels_with_scores = [h for h in hotels 
                         if h.get('review_score', '').strip() and h.get('review_score', '0') != '0']
    
    if hotels_with_scores:
        sorted_hotels = sorted(hotels_with_scores, 
                             key=lambda x: float(x.get('review_score', '0')), 
                             reverse=True)
        
        print("  Top 5 highest rated hotels:")
        for i, hotel in enumerate(sorted_hotels[:5], 1):
            name = hotel.get('name', 'Unknown')
            score = hotel.get('review_score', 'N/A')
            reviews = hotel.get('number_of_reviews', 'N/A')
            print(f"    {i}. {name}")
            print(f"       Score: {score}/5.0 ({reviews} reviews)")
    else:
        print("  No review data available for ranking")
    
    # Sample hotel data
    print(f"\n🏨 SAMPLE HOTEL DATA")
    if hotels:
        sample_hotel = hotels[0]
        print("  Example hotel record:")
        for key, value in sample_hotel.items():
            if value:
                print(f"    {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n" + "="*50)
    print("Analysis complete! Check hotels.csv and hotels.json for full data.")

def create_summary_report():
    """Create a markdown summary report"""
    try:
        with open("hotels.json", 'r', encoding='utf-8') as f:
            hotels = json.load(f)
    except FileNotFoundError:
        print("Error: hotels.json not found. Please run the crawler first.")
        return
    
    from datetime import datetime
    
    report = f"""# Greeka Corfu Hotels - Data Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Hotels:** {len(hotels)}

## Data Completeness

| Field | Count | Percentage |
|-------|-------|------------|
"""
    
    fields = ['name', 'official_website', 'address', 'star_rating', 
              'review_score', 'number_of_reviews', 'phone_number', 
              'latitude', 'longitude']
    
    for field in fields:
        filled = sum(1 for h in hotels if h.get(field, '').strip())
        percentage = (filled / len(hotels)) * 100 if hotels else 0
        report += f"| {field.replace('_', ' ').title()} | {filled}/{len(hotels)} | {percentage:.1f}% |\n"
    
    # Add top locations
    locations = []
    for hotel in hotels:
        address = hotel.get('address', '')
        if address:
            parts = address.split(',')
            if len(parts) >= 2:
                location = parts[-2].strip()
                locations.append(location)
    
    if locations:
        location_counter = Counter(locations)
        report += f"\n## Top Locations\n\n"
        for location, count in location_counter.most_common(5):
            report += f"- **{location}**: {count} hotels\n"
    
    # Save report
    with open("analysis_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Summary report saved to analysis_report.md")

if __name__ == "__main__":
    analyze_hotel_data()
    create_summary_report()