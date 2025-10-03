#!/usr/bin/env python3
"""
All Hotels Walking Isochrones Map Generator
===========================================
Creates a comprehensive static map showing walking distance isochrones 
for all hotels in the Corfu dataset.

Author: AI Assistant
Date: October 2025
"""

import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon
import contextily as ctx
from matplotlib.patches import Patch
import warnings
warnings.filterwarnings('ignore')

class AllHotelsWalkingIsochroneMap:
    def __init__(self):
        """Initialize the map generator"""
        self.hotels_data = []
        self.isochrone_data = []
        self.corfu_bounds = None
        
        # Define walking time colors (from light to dark)
        self.walking_colors = {
            5: '#E8F5E8',   # Very light green (5 min)
            10: '#C8E6C9',  # Light green (10 min) 
            15: '#A5D6A7',  # Medium light green (15 min)
            30: '#81C784',  # Medium green (30 min)
            60: '#66BB6A'   # Darker green (60 min)
        }
        
        # Define alpha transparency for overlapping zones
        self.alpha_value = 0.6
        
    def load_hotels_data(self):
        """Load the original hotels data"""
        hotels_file = '../data/hotels.json'
        try:
            with open(hotels_file, 'r', encoding='utf-8') as f:
                self.hotels_data = json.load(f)
            print(f"📊 Loaded {len(self.hotels_data)} hotels from {hotels_file}")
        except Exception as e:
            print(f"❌ Error loading hotels data: {e}")
            return False
        return True
    
    def load_all_isochrones(self):
        """Load isochrone data from all processed hotels"""
        isochrones_dir = 'hotel_isochrones'
        
        if not os.path.exists(isochrones_dir):
            print(f"❌ Isochrones directory not found: {isochrones_dir}")
            return False
        
        # Get all hotel folders
        hotel_folders = [f for f in os.listdir(isochrones_dir) 
                        if os.path.isdir(os.path.join(isochrones_dir, f)) 
                        and not f.startswith('.')]
        
        print(f"🔍 Found {len(hotel_folders)} hotel folders")
        
        loaded_count = 0
        for hotel_folder in hotel_folders:
            analysis_file = os.path.join(isochrones_dir, hotel_folder, 'analysis_data.json')
            
            if os.path.exists(analysis_file):
                try:
                    with open(analysis_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Extract walking isochrones if they exist
                    if 'walking_isochrones' in data:
                        hotel_info = {
                            'hotel_code': hotel_folder,
                            'hotel_name': data.get('hotel_info', {}).get('name', 'Unknown'),
                            'location': data.get('hotel_info', {}).get('location', 'Unknown'),
                            'coordinates': data.get('hotel_info', {}).get('coordinates', {}),
                            'walking_isochrones': data['walking_isochrones']
                        }
                        self.isochrone_data.append(hotel_info)
                        loaded_count += 1
                        
                except Exception as e:
                    print(f"⚠️  Error loading {analysis_file}: {e}")
        
        print(f"✅ Loaded walking isochrones for {loaded_count} hotels")
        return loaded_count > 0
    
    def get_corfu_bounds(self):
        """Calculate map bounds from all hotel coordinates"""
        if not self.isochrone_data:
            return None
        
        lats = []
        lons = []
        
        for hotel in self.isochrone_data:
            coords = hotel.get('coordinates', {})
            if coords.get('lat') and coords.get('lon'):
                lats.append(float(coords['lat']))
                lons.append(float(coords['lon']))
        
        if not lats or not lons:
            return None
        
        # Add padding around the bounds
        lat_padding = (max(lats) - min(lats)) * 0.1
        lon_padding = (max(lons) - min(lons)) * 0.1
        
        bounds = {
            'min_lat': min(lats) - lat_padding,
            'max_lat': max(lats) + lat_padding,
            'min_lon': min(lons) - lon_padding,
            'max_lon': max(lons) + lon_padding
        }
        
        return bounds
    
    def polygon_from_coords(self, coords_list):
        """Convert coordinate list to Shapely Polygon"""
        if not coords_list or len(coords_list) < 3:
            return None
        
        try:
            # Ensure polygon is closed
            if coords_list[0] != coords_list[-1]:
                coords_list.append(coords_list[0])
            
            return Polygon(coords_list)
        except Exception as e:
            print(f"⚠️  Error creating polygon: {e}")
            return None
    
    def create_comprehensive_map(self):
        """Create the comprehensive walking isochrones map"""
        if not self.isochrone_data:
            print("❌ No isochrone data available")
            return None
        
        # Get map bounds
        bounds = self.get_corfu_bounds()
        if not bounds:
            print("❌ Could not determine map bounds")
            return None
        
        print("🗺️  Creating comprehensive walking isochrones map...")
        
        # Create figure with high DPI for quality
        fig, ax = plt.subplots(figsize=(20, 16), dpi=300)
        ax.set_facecolor('#f0f8ff')  # Light blue background
        
        # Set map bounds
        ax.set_xlim(bounds['min_lon'], bounds['max_lon'])
        ax.set_ylim(bounds['min_lat'], bounds['max_lat'])
        
        # Track statistics
        total_zones = 0
        hotels_plotted = 0
        
        # Plot isochrones for each hotel
        for hotel in self.isochrone_data:
            coords = hotel.get('coordinates', {})
            if not coords.get('lat') or not coords.get('lon'):
                continue
            
            hotel_lat = float(coords['lat'])
            hotel_lon = float(coords['lon'])
            walking_isochrones = hotel.get('walking_isochrones', {})
            
            # Plot walking zones from largest to smallest (60, 30, 15, 10, 5)
            for time_minutes in [60, 30, 15, 10, 5]:
                time_key = f"{time_minutes}_min"
                
                if time_key in walking_isochrones:
                    zone_coords = walking_isochrones[time_key]
                    
                    if zone_coords and len(zone_coords) > 0:
                        # Convert to polygon
                        polygon = self.polygon_from_coords(zone_coords)
                        
                        if polygon and polygon.is_valid:
                            # Get coordinates for plotting
                            x_coords = [coord[1] for coord in zone_coords]  # longitude
                            y_coords = [coord[0] for coord in zone_coords]  # latitude
                            
                            # Plot filled polygon
                            ax.fill(x_coords, y_coords, 
                                   color=self.walking_colors[time_minutes],
                                   alpha=self.alpha_value,
                                   edgecolor='none',
                                   linewidth=0)
                            
                            total_zones += 1
            
            # Plot hotel location
            ax.scatter(hotel_lon, hotel_lat, 
                      c='red', s=8, alpha=0.8, 
                      edgecolors='darkred', linewidth=0.3,
                      zorder=1000)
            
            hotels_plotted += 1
        
        # Add basemap (OpenStreetMap tiles)
        try:
            # Convert bounds to Web Mercator for contextily
            ax.set_aspect('equal')
            ctx.add_basemap(ax, crs='EPSG:4326', 
                           source=ctx.providers.OpenStreetMap.Mapnik,
                           alpha=0.7, zorder=0)
        except Exception as e:
            print(f"⚠️  Could not add basemap: {e}")
            # Add grid instead
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Create custom legend
        legend_elements = [
            Patch(facecolor=self.walking_colors[5], alpha=self.alpha_value, 
                  label='5 minutes walk'),
            Patch(facecolor=self.walking_colors[10], alpha=self.alpha_value, 
                  label='10 minutes walk'),
            Patch(facecolor=self.walking_colors[15], alpha=self.alpha_value, 
                  label='15 minutes walk'),
            Patch(facecolor=self.walking_colors[30], alpha=self.alpha_value, 
                  label='30 minutes walk'),
            Patch(facecolor=self.walking_colors[60], alpha=self.alpha_value, 
                  label='60 minutes walk'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='red', markersize=8, 
                      label=f'Hotels ({hotels_plotted})')
        ]
        
        ax.legend(handles=legend_elements, 
                 loc='upper left', 
                 bbox_to_anchor=(0.02, 0.98),
                 fontsize=11,
                 framealpha=0.9,
                 fancybox=True,
                 shadow=True)
        
        # Add title and labels
        plt.title('Walking Distance Isochrones for All Corfu Hotels\n'
                 f'Comprehensive Analysis of {hotels_plotted} Hotels with {total_zones} Walking Zones',
                 fontsize=18, fontweight='bold', pad=20)
        
        plt.xlabel('Longitude', fontsize=12, fontweight='bold')
        plt.ylabel('Latitude', fontsize=12, fontweight='bold')
        
        # Add statistics text box
        stats_text = f"""Walking Accessibility Analysis
• Hotels Analyzed: {hotels_plotted}
• Total Walking Zones: {total_zones}
• Time Intervals: 5, 10, 15, 30, 60 minutes
• Network: OpenStreetMap pedestrian paths
• Analysis Date: October 2025"""
        
        ax.text(0.02, 0.02, stats_text,
               transform=ax.transAxes,
               bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.9),
               fontsize=9, verticalalignment='bottom')
        
        # Improve layout
        plt.tight_layout()
        
        # Save the map
        output_file = 'all_hotels_walking_isochrones_map.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        print(f"✅ Map saved as: {output_file}")
        print(f"📊 Statistics:")
        print(f"   • Hotels plotted: {hotels_plotted}")
        print(f"   • Total walking zones: {total_zones}")
        print(f"   • Map dimensions: 20x16 inches at 300 DPI")
        
        return output_file
    
    def generate_summary_report(self):
        """Generate a summary report of the walking accessibility analysis"""
        if not self.isochrone_data:
            return
        
        print("\n" + "="*60)
        print("WALKING ACCESSIBILITY SUMMARY REPORT")
        print("="*60)
        
        # Analyze walking zones coverage
        zone_counts = {5: 0, 10: 0, 15: 0, 30: 0, 60: 0}
        hotels_with_zones = 0
        
        for hotel in self.isochrone_data:
            walking_isochrones = hotel.get('walking_isochrones', {})
            has_zones = False
            
            for time_minutes in [5, 10, 15, 30, 60]:
                time_key = f"{time_minutes}_min"
                if time_key in walking_isochrones and walking_isochrones[time_key]:
                    zone_counts[time_minutes] += 1
                    has_zones = True
            
            if has_zones:
                hotels_with_zones += 1
        
        print(f"📊 Total Hotels Analyzed: {len(self.isochrone_data)}")
        print(f"🚶 Hotels with Walking Zones: {hotels_with_zones}")
        print(f"📈 Walking Zone Coverage:")
        
        for time_minutes, count in zone_counts.items():
            percentage = (count / len(self.isochrone_data)) * 100 if self.isochrone_data else 0
            print(f"   • {time_minutes:2d} minute zones: {count:3d} hotels ({percentage:5.1f}%)")
        
        print("\n🗺️  Map Features:")
        print(f"   • High resolution: 300 DPI")
        print(f"   • Interactive legend with zone colors")
        print(f"   • OpenStreetMap basemap integration")
        print(f"   • Transparent overlays for zone visibility")
        print(f"   • Hotel locations marked in red")
        
        print("="*60)

def main():
    """Main execution function"""
    print("🗺️  All Hotels Walking Isochrones Map Generator")
    print("=" * 60)
    
    # Create map generator
    generator = AllHotelsWalkingIsochroneMap()
    
    # Load data
    if not generator.load_hotels_data():
        print("❌ Failed to load hotels data")
        return
    
    if not generator.load_all_isochrones():
        print("❌ Failed to load isochrone data") 
        return
    
    # Generate the comprehensive map
    output_file = generator.create_comprehensive_map()
    
    if output_file:
        # Generate summary report
        generator.generate_summary_report()
        
        print(f"\n🎉 SUCCESS! Walking isochrones map created")
        print(f"📁 Output file: {output_file}")
        print(f"🔍 Check the generated image for comprehensive walking accessibility analysis")
    else:
        print("❌ Failed to create the map")

if __name__ == "__main__":
    main()