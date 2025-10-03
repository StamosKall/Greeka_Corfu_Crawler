#!/usr/bin/env python3
"""
Simplified All Hotels Walking Isochrones Map Generator
=====================================================
Creates a static map showing walking distance isochrones for all hotels
by recalculating them using OSMnx and the existing network.

Author: AI Assistant
Date: October 2025
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import networkx as nx
from shapely.geometry import Point, Polygon
import geopandas as gpd
from matplotlib.patches import Patch
import warnings
warnings.filterwarnings('ignore')

# Configure OSMnx
ox.settings.use_cache = True
ox.settings.log_console = False

class SimplifiedWalkingIsochroneMap:
    def __init__(self):
        """Initialize the map generator"""
        self.hotels_data = []
        self.walk_network = None
        self.corfu_bounds = None
        
        # Walking time intervals (minutes)
        self.time_intervals = [5, 10, 15, 30, 60]
        
        # Walking colors (light to dark green)
        self.walking_colors = {
            5: '#E8F5E8',   # Very light green
            10: '#C8E6C9',  # Light green
            15: '#A5D6A7',  # Medium light green
            30: '#81C784',  # Medium green
            60: '#66BB6A'   # Darker green
        }
        
        self.alpha_value = 0.5
        
    def load_hotels_data(self):
        """Load hotels data with coordinates"""
        hotels_file = '../data/hotels.json'
        try:
            with open(hotels_file, 'r', encoding='utf-8') as f:
                all_hotels = json.load(f)
            
            # Filter hotels with valid coordinates
            self.hotels_data = []
            for hotel in all_hotels:
                if hotel.get('latitude') and hotel.get('longitude'):
                    try:
                        lat = float(hotel['latitude'])
                        lon = float(hotel['longitude'])
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            self.hotels_data.append({
                                'name': hotel.get('name', 'Unknown'),
                                'lat': lat,
                                'lon': lon,
                                'rating': hotel.get('rating', ''),
                                'location': hotel.get('location', '')
                            })
                    except (ValueError, TypeError):
                        continue
            
            print(f"📊 Loaded {len(self.hotels_data)} hotels with valid coordinates")
            return len(self.hotels_data) > 0
            
        except Exception as e:
            print(f"❌ Error loading hotels data: {e}")
            return False
    
    def initialize_walking_network(self):
        """Initialize walking network for Corfu"""
        print("🚶 Initializing walking network for Corfu...")
        
        try:
            # Get Corfu boundaries
            place_name = "Corfu, Greece"
            
            # Download walking network (includes pedestrian paths)
            self.walk_network = ox.graph_from_place(
                place_name, 
                network_type='walk',
                simplify=True
            )
            
            # Add travel speeds and times
            self.walk_network = ox.add_edge_speeds(self.walk_network)
            self.walk_network = ox.add_edge_travel_times(self.walk_network)
            
            node_count = len(self.walk_network.nodes())
            edge_count = len(self.walk_network.edges())
            
            print(f"✅ Walking network loaded: {node_count} nodes, {edge_count} edges")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing walking network: {e}")
            return False
    
    def calculate_walking_isochrone(self, center_lat, center_lon, time_minutes):
        """Calculate walking isochrone for a given time"""
        try:
            # Find nearest network node to hotel
            center_node = ox.nearest_nodes(self.walk_network, center_lon, center_lat)
            
            # Calculate travel times from center node
            trip_times = nx.single_source_dijkstra_path_length(
                self.walk_network, center_node, cutoff=time_minutes*60, weight='travel_time'
            )
            
            # Get nodes within time limit
            reachable_nodes = [node for node, time in trip_times.items() 
                             if time <= time_minutes * 60]
            
            if len(reachable_nodes) < 3:
                return None
            
            # Get coordinates of reachable nodes
            node_coords = []
            for node in reachable_nodes:
                node_data = self.walk_network.nodes[node]
                node_coords.append([node_data['y'], node_data['x']])  # lat, lon
            
            # Create convex hull around reachable nodes
            if len(node_coords) >= 3:
                gdf = gpd.GeoDataFrame(
                    geometry=[Point(coord[1], coord[0]) for coord in node_coords],
                    crs='EPSG:4326'
                )
                
                # Create convex hull
                hull = gdf.unary_union.convex_hull
                
                if hull.geom_type == 'Polygon':
                    # Extract coordinates
                    coords = list(hull.exterior.coords)
                    return coords
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error calculating isochrone: {e}")
            return None
    
    def get_map_bounds(self):
        """Calculate map bounds from hotel coordinates"""
        if not self.hotels_data:
            return None
        
        lats = [hotel['lat'] for hotel in self.hotels_data]
        lons = [hotel['lon'] for hotel in self.hotels_data]
        
        # Add padding
        lat_padding = (max(lats) - min(lats)) * 0.1
        lon_padding = (max(lons) - min(lons)) * 0.1
        
        return {
            'min_lat': min(lats) - lat_padding,
            'max_lat': max(lats) + lat_padding,
            'min_lon': min(lons) - lon_padding,
            'max_lon': max(lons) + lon_padding
        }
    
    def create_walking_isochrones_map(self):
        """Create comprehensive walking isochrones map"""
        if not self.hotels_data or not self.walk_network:
            print("❌ Missing required data")
            return None
        
        print("🗺️  Creating walking isochrones map for all hotels...")
        
        # Get map bounds
        bounds = self.get_map_bounds()
        if not bounds:
            print("❌ Could not determine map bounds")
            return None
        
        # Create figure
        fig, ax = plt.subplots(figsize=(20, 16), dpi=300)
        ax.set_facecolor('#f0f8ff')
        
        # Set bounds
        ax.set_xlim(bounds['min_lon'], bounds['max_lon'])
        ax.set_ylim(bounds['min_lat'], bounds['max_lat'])
        
        # Statistics
        total_isochrones = 0
        hotels_processed = 0
        
        # Process all hotels
        hotels_to_process = self.hotels_data
        
        print(f"🎯 Processing all {len(hotels_to_process)} hotels...")
        
        for i, hotel in enumerate(hotels_to_process):
            print(f"  [{i+1}/{len(hotels_to_process)}] Processing {hotel['name'][:50]}...")
            
            hotel_lat = hotel['lat']
            hotel_lon = hotel['lon']
            
            # Calculate isochrones for each time interval (largest to smallest)
            for time_minutes in reversed(self.time_intervals):
                isochrone_coords = self.calculate_walking_isochrone(
                    hotel_lat, hotel_lon, time_minutes
                )
                
                if isochrone_coords and len(isochrone_coords) >= 3:
                    # Extract x, y coordinates for plotting
                    x_coords = [coord[1] for coord in isochrone_coords]  # longitude
                    y_coords = [coord[0] for coord in isochrone_coords]  # latitude
                    
                    # Plot filled polygon
                    ax.fill(x_coords, y_coords,
                           color=self.walking_colors[time_minutes],
                           alpha=self.alpha_value,
                           edgecolor='none',
                           linewidth=0)
                    
                    total_isochrones += 1
            
            # Plot hotel location
            ax.scatter(hotel_lon, hotel_lat,
                      c='red', s=12, alpha=0.9,
                      edgecolors='darkred', linewidth=0.5,
                      zorder=1000)
            
            hotels_processed += 1
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Create legend
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
                      label=f'Hotels ({hotels_processed})')
        ]
        
        ax.legend(handles=legend_elements,
                 loc='upper left',
                 bbox_to_anchor=(0.02, 0.98),
                 fontsize=12,
                 framealpha=0.9,
                 fancybox=True,
                 shadow=True)
        
        # Add title
        plt.title(f'Walking Distance Isochrones for Corfu Hotels\n'
                 f'Analysis of {hotels_processed} Hotels with {total_isochrones} Walking Zones',
                 fontsize=18, fontweight='bold', pad=20)
        
        plt.xlabel('Longitude', fontsize=12, fontweight='bold')
        plt.ylabel('Latitude', fontsize=12, fontweight='bold')
        
        # Add statistics box
        stats_text = f"""Walking Accessibility Analysis
• Hotels Analyzed: {hotels_processed}
• Total Walking Zones: {total_isochrones}
• Time Intervals: 5, 10, 15, 30, 60 minutes
• Network: OpenStreetMap pedestrian paths
• Analysis: Real-time isochrone calculation"""
        
        ax.text(0.02, 0.02, stats_text,
               transform=ax.transAxes,
               bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.9),
               fontsize=10, verticalalignment='bottom')
        
        # Save map
        plt.tight_layout()
        output_file = 'walking_isochrones_all_141_hotels.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        
        print(f"✅ Map saved as: {output_file}")
        print(f"📊 Final Statistics:")
        print(f"   • Hotels processed: {hotels_processed}")
        print(f"   • Total walking zones: {total_isochrones}")
        print(f"   • Average zones per hotel: {total_isochrones/hotels_processed:.1f}")
        
        return output_file

def main():
    """Main execution function"""
    print("🚶 Simplified Walking Isochrones Map Generator")
    print("=" * 60)
    
    # Create generator
    generator = SimplifiedWalkingIsochroneMap()
    
    # Load hotel data
    if not generator.load_hotels_data():
        print("❌ Failed to load hotel data")
        return
    
    # Initialize walking network
    if not generator.initialize_walking_network():
        print("❌ Failed to initialize walking network")
        return
    
    # Create map
    output_file = generator.create_walking_isochrones_map()
    
    if output_file:
        print(f"\n🎉 SUCCESS! Walking isochrones map created")
        print(f"📁 Output file: {output_file}")
    else:
        print("❌ Failed to create map")

if __name__ == "__main__":
    main()