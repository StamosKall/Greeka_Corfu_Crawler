#!/usr/bin/env python3
"""
Static Map Generator Suite for Corfu Hotels
Runs all static map generators and creates a comprehensive overview
"""

import json
import matplotlib.pyplot as plt
import os
import subprocess
import sys

def check_file_exists(filepath):
    """Check if a file exists and return its size"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        return True, size
    return False, 0

def run_script(script_name):
    """Run a Python script and return success status"""
    try:
        result = subprocess.run([
            "C:/Users/stama/AppData/Local/Microsoft/WindowsApps/python3.13.exe", 
            script_name
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✓ {script_name} completed successfully")
            return True
        else:
            print(f"✗ {script_name} failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ {script_name} timed out")
        return False
    except Exception as e:
        print(f"✗ {script_name} error: {e}")
        return False

def load_hotel_data(json_file):
    """Load hotel data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_overview_report(hotels_data, output_dir):
    """Create an overview report of all generated maps"""
    
    # Count statistics
    total_hotels = len(hotels_data)
    hotels_with_coords = sum(1 for h in hotels_data if h.get('latitude') and h.get('longitude'))
    
    star_counts = {}
    review_scores = []
    
    for hotel in hotels_data:
        if hotel.get('latitude') and hotel.get('longitude'):
            star_rating = hotel.get('star_rating', 'No Rating')
            if not star_rating:
                star_rating = 'No Rating'
            star_counts[star_rating] = star_counts.get(star_rating, 0) + 1
            
            try:
                score = float(hotel.get('review_score', 0))
                if score > 0:
                    review_scores.append(score)
            except (ValueError, TypeError):
                pass
    
    # Check which files were created
    generated_files = []
    file_checks = [
        ('corfu_hotels_static_map.png', 'Basic Static Map'),
        ('corfu_hotels_density_map.png', 'Density Heat Map'),
        ('corfu_hotels_stats.png', 'Statistics Visualization'),
    ]
    
    for filename, description in file_checks:
        filepath = os.path.join(output_dir, filename)
        exists, size = check_file_exists(filepath)
        if exists:
            size_mb = size / (1024 * 1024)
            generated_files.append(f"✓ {description}: {filename} ({size_mb:.2f} MB)")
        else:
            generated_files.append(f"✗ {description}: {filename} (not found)")
    
    # Create report
    report = f"""
CORFU HOTELS STATIC MAP GENERATION REPORT
==========================================

DATASET OVERVIEW:
- Total hotels in dataset: {total_hotels}
- Hotels with coordinates: {hotels_with_coords}
- Coverage: {(hotels_with_coords/total_hotels)*100:.1f}%

STAR RATING DISTRIBUTION:
"""
    
    for rating in ['5', '4', '3', '2', '1', 'No Rating']:
        count = star_counts.get(rating, 0)
        if count > 0:
            percentage = (count / hotels_with_coords) * 100
            report += f"- {rating} Star{'s' if rating != '1' else ''}: {count} hotels ({percentage:.1f}%)\n"
    
    if review_scores:
        avg_score = sum(review_scores) / len(review_scores)
        report += f"\nREVIEW STATISTICS:\n"
        report += f"- Hotels with review scores: {len(review_scores)}\n"
        report += f"- Average review score: {avg_score:.2f}\n"
        report += f"- Score range: {min(review_scores):.1f} - {max(review_scores):.1f}\n"
    
    report += f"\nGENERATED FILES:\n"
    for file_info in generated_files:
        report += f"{file_info}\n"
    
    report += f"""
FILE LOCATIONS:
All files are saved in: {os.path.abspath(output_dir)}

USAGE INSTRUCTIONS:
1. Basic Static Map: Shows all hotels color-coded by star rating
2. Density Heat Map: Shows hotel concentration areas in Corfu
3. Statistics Visualization: Shows detailed analytics and distributions

The static map files can be used for:
- Presentations and reports
- Web development (as background maps)
- Print materials
- Tourism planning
- Academic research

Generated on: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}
"""
    
    # Save report
    report_file = os.path.join(output_dir, 'static_maps_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "="*60)
    print(report)
    print(f"Full report saved as: {report_file}")

def main():
    """Main function to run all static map generators"""
    print("CORFU HOTELS STATIC MAP GENERATOR SUITE")
    print("="*50)
    
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
    
    # Determine output directory
    output_dir = 'data' if os.path.exists('data') else '../data'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print("\nGenerating static maps...")
    
    # Run all generators
    scripts_to_run = [
        'simple_static_map.py',
        'advanced_static_maps.py'
    ]
    
    success_count = 0
    for script in scripts_to_run:
        if os.path.exists(script):
            print(f"\nRunning {script}...")
            if run_script(script):
                success_count += 1
        else:
            print(f"✗ {script} not found")
    
    print(f"\nCompleted {success_count}/{len(scripts_to_run)} scripts successfully")
    
    # Create overview report
    print("\nGenerating overview report...")
    create_overview_report(hotels_data, output_dir)
    
    print("\n" + "="*60)
    print("STATIC MAP GENERATION COMPLETE!")
    print(f"Check the '{output_dir}' directory for all generated files.")

if __name__ == "__main__":
    main()