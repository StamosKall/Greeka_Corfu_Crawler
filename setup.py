#!/usr/bin/env python3
"""
Project setup script for Greeka Corfu Hotels Crawler.
This script helps set up the project environment and dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected.")
        print("This project requires Python 3.8 or higher.")
        print("Please upgrade Python and try again.")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected (compatible)")
        return True

def create_virtual_environment():
    """Create a virtual environment"""
    venv_path = Path("venv")
    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return True
    
    return run_command(f"{sys.executable} -m venv venv", 
                      "Creating virtual environment")

def get_activation_command():
    """Get the appropriate activation command for the current OS"""
    if platform.system() == "Windows":
        return "venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"

def install_dependencies():
    """Install required dependencies"""
    if platform.system() == "Windows":
        pip_cmd = "venv\\Scripts\\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    return run_command(f"{pip_cmd} install -r requirements.txt", 
                      "Installing dependencies")

def test_crawler():
    """Test if the crawler can be imported and run basic checks"""
    print("🔄 Testing crawler import...")
    try:
        if platform.system() == "Windows":
            python_cmd = "venv\\Scripts\\python"
        else:
            python_cmd = "venv/bin/python"
        
        test_code = """
import requests
from bs4 import BeautifulSoup
from crawler import GreekaHotelCrawler
print("All imports successful!")
crawler = GreekaHotelCrawler()
print("Crawler initialized successfully!")
"""
        
        result = subprocess.run([python_cmd, "-c", test_code], 
                              capture_output=True, text=True, check=True)
        print("✅ Crawler test completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Crawler test failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def display_usage_instructions():
    """Display usage instructions"""
    activation_cmd = get_activation_command()
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY! 🎉")
    print("="*60)
    print("\n📋 NEXT STEPS:")
    print(f"1. Activate the virtual environment:")
    if platform.system() == "Windows":
        print(f"   {activation_cmd}")
    else:
        print(f"   {activation_cmd}")
    
    print(f"\n2. Run the crawler:")
    print(f"   python crawler.py")
    
    print(f"\n3. Analyze the results:")
    print(f"   python analyze_data.py")
    
    print(f"\n4. Test a single hotel:")
    print(f"   python test_single_hotel.py <hotel_url>")
    
    print(f"\n📁 OUTPUT FILES:")
    print(f"   - hotels.csv (Excel-compatible data)")
    print(f"   - hotels.json (JSON format data)")
    print(f"   - crawler.log (Execution log)")
    print(f"   - analysis_report.md (Data analysis report)")
    
    print(f"\n🔧 CONFIGURATION:")
    print(f"   Edit config.ini to customize crawler behavior")
    
    print(f"\n📚 DOCUMENTATION:")
    print(f"   Check README.md for detailed instructions")
    
    print(f"\n🚀 GITHUB ACTIONS:")
    print(f"   Push to GitHub to automatically run the crawler via Actions")
    print("="*60)

def main():
    """Main setup function"""
    print("🏗️  GREEKA CORFU HOTELS CRAWLER - PROJECT SETUP")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Failed to create virtual environment. Exiting.")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Exiting.")
        sys.exit(1)
    
    # Test crawler
    if not test_crawler():
        print("⚠️  Crawler test failed, but setup is mostly complete.")
        print("You may need to troubleshoot import issues.")
    
    # Display usage instructions
    display_usage_instructions()

if __name__ == "__main__":
    main()