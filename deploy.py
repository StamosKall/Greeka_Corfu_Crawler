#!/usr/bin/env python3
"""
Deployment helper script for Greeka Corfu Hotels Crawler.
This script helps with quick deployment and testing.
"""

import subprocess
import sys
import os
from datetime import datetime
import json

def run_crawler_with_report():
    """Run the crawler and generate a comprehensive report"""
    print("🚀 Running Greeka Corfu Hotels Crawler...")
    print("="*50)
    
    start_time = datetime.now()
    
    # Run the crawler
    try:
        result = subprocess.run([sys.executable, "crawler.py"], 
                              capture_output=True, text=True, check=True)
        print("✅ Crawler completed successfully!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Crawler failed!")
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False
    
    end_time = datetime.now()
    execution_time = end_time - start_time
    
    # Generate analysis report
    try:
        result = subprocess.run([sys.executable, "analyze_data.py"], 
                              capture_output=True, text=True, check=True)
        print("\n✅ Data analysis completed!")
    except subprocess.CalledProcessError as e:
        print("\n⚠️ Data analysis failed!")
        print(f"Error: {e}")
    
    # Display summary
    print(f"\n📊 EXECUTION SUMMARY")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total execution time: {execution_time}")
    
    # Check output files
    files_created = []
    for filename in ["hotels.csv", "hotels.json", "crawler.log", "analysis_report.md"]:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            files_created.append(f"  ✅ {filename} ({size:,} bytes)")
        else:
            files_created.append(f"  ❌ {filename} (missing)")
    
    print(f"\n📁 OUTPUT FILES:")
    for file_info in files_created:
        print(file_info)
    
    # Display data stats if available
    try:
        with open("hotels.json", 'r', encoding='utf-8') as f:
            hotels = json.load(f)
        
        print(f"\n📈 DATA STATISTICS:")
        print(f"  Total hotels found: {len(hotels)}")
        
        # Count fields with data
        with_website = sum(1 for h in hotels if h.get('official_website', '').strip())
        with_rating = sum(1 for h in hotels if h.get('star_rating', '').strip())
        with_reviews = sum(1 for h in hotels if h.get('review_score', '').strip())
        
        print(f"  Hotels with official website: {with_website}")
        print(f"  Hotels with star rating: {with_rating}")
        print(f"  Hotels with review scores: {with_reviews}")
        
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"\n⚠️ Unable to load hotel data for statistics")
    
    print(f"\n🎉 Deployment completed successfully!")
    return True

def quick_test():
    """Run a quick test of the crawler functionality"""
    print("🧪 Running quick functionality test...")
    
    test_url = "https://www.greeka.com/ionian/corfu/hotels/location-agios-stefanos-avliotes/delfino-blu/"
    
    try:
        result = subprocess.run([sys.executable, "test_single_hotel.py", test_url], 
                              capture_output=True, text=True, check=True)
        print("✅ Single hotel test passed!")
        print("Sample output:")
        lines = result.stdout.split('\n')
        for line in lines[:10]:  # Show first 10 lines
            if line.strip():
                print(f"  {line}")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Single hotel test failed!")
        print(f"Error: {e}")
        return False

def validate_requirements():
    """Validate that all requirements are met"""
    print("🔍 Validating requirements...")
    
    # Check Python packages
    required_packages = ["requests", "beautifulsoup4", "lxml"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    # Check required files
    required_files = ["crawler.py", "requirements.txt", "README.md"]
    missing_files = []
    
    for filename in required_files:
        if os.path.exists(filename):
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename} (missing)")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All requirements validated!")
    return True

def main():
    """Main deployment function"""
    print("🚀 GREEKA CORFU HOTELS CRAWLER - DEPLOYMENT HELPER")
    print("="*60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            if not validate_requirements():
                sys.exit(1)
            if not quick_test():
                sys.exit(1)
        
        elif command == "validate":
            if not validate_requirements():
                sys.exit(1)
        
        elif command == "run":
            if not validate_requirements():
                sys.exit(1)
            if not run_crawler_with_report():
                sys.exit(1)
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, validate, run")
            sys.exit(1)
    
    else:
        # Default: run full deployment
        if not validate_requirements():
            sys.exit(1)
        if not run_crawler_with_report():
            sys.exit(1)

if __name__ == "__main__":
    main()