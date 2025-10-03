#!/usr/bin/env python3
"""
Hotel Isochrone Analysis Generator
Creates isochrone maps for each hotel showing 5, 10, 15, 30, and 60 minute travel times
by driving and walking, plus calculates time to nearest beach.
Uses OpenStreetMap data via OSMnx and routing services.
"""

import json
import os
import requests
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
import osmnx as ox
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic
import folium
from folium import plugins
import warnings
warnings.filterwarnings('ignore')

# Configure OSMnx (updated for newer versions)
try:
    ox.settings.log_console = True
    ox.settings.use_cache = True
except AttributeError:
    # Fallback for older versions
    pass

class HotelIsochroneAnalyzer:
    def __init__(self, hotels_data, output_base_dir="hotel_isochrones"):
        self.hotels_data = hotels_data
        self.output_base_dir = output_base_dir
        self.processed_hotels = []
        self.beach_locations = []
        
        # Create output directory
        Path(self.output_base_dir).mkdir(exist_ok=True)
        
        # Time intervals in minutes
        self.time_intervals = [5, 10, 15, 30, 60]
        
        # Load/initialize Corfu road networks
        self.drive_graph = None
        self.walk_graph = None
        
    def initialize_networks(self):
        """Initialize road networks for Corfu"""
        print("🗺️  Initializing road networks for Corfu...")
        
        try:
            # Download drive network (for cars)
            print("📍 Downloading driving network...")
            self.drive_graph = ox.graph_from_place("Corfu, Greece", network_type='drive')
            print(f"✅ Drive network: {len(self.drive_graph.nodes)} nodes, {len(self.drive_graph.edges)} edges")
            
            # Download walk network (for pedestrians)
            print("📍 Downloading walking network...")
            self.walk_graph = ox.graph_from_place("Corfu, Greece", network_type='walk')
            print(f"✅ Walk network: {len(self.walk_graph.nodes)} nodes, {len(self.walk_graph.edges)} edges")
            
        except Exception as e:
            print(f"❌ Error downloading networks: {e}")
            print("🔄 Trying with bounding box approach...")
            
            # Fallback: use bounding box
            north, south, east, west = 39.8, 39.3, 20.2, 19.3  # Corfu approximate bounds
            
            try:
                self.drive_graph = ox.graph_from_bbox(north, south, east, west, network_type='drive')
                self.walk_graph = ox.graph_from_bbox(north, south, east, west, network_type='walk')
                print("✅ Networks initialized with bounding box")
            except Exception as e2:
                print(f"❌ Fallback failed: {e2}")
                return False
        
        return True
    
    def load_beach_locations(self):
        """Load or create beach locations in Corfu"""
        print("🏖️  Loading beach locations...")
        
        # Major beaches in Corfu with approximate coordinates
        self.beach_locations = [
            {"name": "Paleokastritsa Beach", "lat": 39.6742, "lon": 19.7113},
            {"name": "Glyfada Beach", "lat": 39.5682, "lon": 19.8297}, 
            {"name": "Sidari Beach", "lat": 39.7906, "lon": 19.7064},
            {"name": "Kavos Beach", "lat": 39.3859, "lon": 20.1129},
            {"name": "Barbati Beach", "lat": 39.7132, "lon": 19.8626},
            {"name": "Dassia Beach", "lat": 39.6831, "lon": 19.8486},
            {"name": "Kasssiopi Beach", "lat": 39.7972, "lon": 19.8879},
            {"name": "Agios Gordios Beach", "lat": 39.5497, "lon": 19.8501},
            {"name": "Messonghi Beach", "lat": 39.4813, "lon": 19.9300},
            {"name": "Roda Beach", "lat": 39.7912, "lon": 19.7878},
            {"name": "Acharavi Beach", "lat": 39.7939, "lon": 19.8179},
            {"name": "Ipsos Beach", "lat": 39.7042, "lon": 19.8377},
            {"name": "Benitses Beach", "lat": 39.5860, "lon": 19.9167},
            {"name": "Moraitika Beach", "lat": 39.4813, "lon": 19.9300},
            {"name": "Arillas Beach", "lat": 39.7431, "lon": 19.6648}
        ]
        
        print(f"✅ Loaded {len(self.beach_locations)} beach locations")
    
    def generate_hotel_code(self, hotel_name):
        """Generate a short code for hotel folder name"""
        # Remove common words and create short code
        name = hotel_name.lower()
        exclude_words = ['hotel', 'apartments', 'villa', 'resort', 'suites', 'in', 'the', 'and', 'of']
        
        words = name.split()
        filtered_words = [w for w in words if w not in exclude_words and len(w) > 2]
        
        if not filtered_words:
            filtered_words = words[:2]  # Fallback to first 2 words
        
        # Take first 2-3 significant words and create code
        code_parts = filtered_words[:3]
        code = ''.join([word[:3] for word in code_parts])
        
        # Clean code
        code = ''.join(c for c in code if c.isalnum())[:12]  # Max 12 chars
        return code.upper()
    
    def calculate_isochrones_networkx(self, center_lat, center_lon, graph, travel_times, speed_kmh):
        """Calculate isochrones using NetworkX and actual road networks"""
        isochrones = {}
        
        try:
            # Find nearest node to hotel
            center_node = ox.nearest_nodes(graph, center_lon, center_lat)
            
            # Calculate travel time to all nodes
            travel_speeds_ms = speed_kmh * 1000 / 3600  # Convert km/h to m/s
            
            for travel_time_min in travel_times:
                travel_time_sec = travel_time_min * 60
                max_distance_m = travel_speeds_ms * travel_time_sec
                
                # Get subgraph within travel distance
                subgraph = nx.ego_graph(graph, center_node, radius=max_distance_m, distance='length')
                
                # Extract coordinates of reachable nodes
                reachable_points = []
                for node in subgraph.nodes():
                    if 'y' in graph.nodes[node] and 'x' in graph.nodes[node]:
                        reachable_points.append([graph.nodes[node]['x'], graph.nodes[node]['y']])
                
                if len(reachable_points) > 3:
                    # Create approximate polygon around reachable points
                    from scipy.spatial import ConvexHull
                    try:
                        hull = ConvexHull(reachable_points)
                        hull_points = [reachable_points[i] for i in hull.vertices]
                        isochrones[travel_time_min] = hull_points
                    except:
                        # Fallback: create circle
                        circle_points = self.create_circle_points(center_lon, center_lat, max_distance_m / 1000)
                        isochrones[travel_time_min] = circle_points
                else:
                    # Fallback: create circle
                    circle_points = self.create_circle_points(center_lon, center_lat, max_distance_m / 1000)
                    isochrones[travel_time_min] = circle_points
                    
        except Exception as e:
            print(f"⚠️  NetworkX calculation failed: {e}, using circle approximation")
            # Fallback to circular approximation
            for travel_time_min in travel_times:
                max_distance_km = speed_kmh * (travel_time_min / 60)
                circle_points = self.create_circle_points(center_lon, center_lat, max_distance_km)
                isochrones[travel_time_min] = circle_points
        
        return isochrones
    
    def create_circle_points(self, center_lon, center_lat, radius_km, num_points=36):
        """Create circular approximation for isochrone"""
        points = []
        for i in range(num_points):
            angle = 2 * np.pi * i / num_points
            # Approximate coordinate offset (rough conversion)
            lat_offset = (radius_km / 111.32) * np.cos(angle)  # 1 degree lat ≈ 111.32 km
            lon_offset = (radius_km / (111.32 * np.cos(np.radians(center_lat)))) * np.sin(angle)
            
            points.append([center_lon + lon_offset, center_lat + lat_offset])
        
        return points
    
    def calculate_time_to_nearest_beach(self, hotel_lat, hotel_lon):
        """Calculate travel time to nearest beach by driving and walking"""
        nearest_beach = None
        min_drive_time = float('inf')
        min_walk_time = float('inf')
        
        # Simple distance-based calculation (can be improved with actual routing)
        for beach in self.beach_locations:
            distance_km = geodesic((hotel_lat, hotel_lon), (beach['lat'], beach['lon'])).kilometers
            
            # Estimate travel times (rough approximation)
            drive_time_min = distance_km / 50 * 60  # Assume 50 km/h average driving speed
            walk_time_min = distance_km / 5 * 60    # Assume 5 km/h walking speed
            
            if drive_time_min < min_drive_time:
                min_drive_time = drive_time_min
                nearest_beach = beach
                min_walk_time = walk_time_min
        
        return {
            'nearest_beach': nearest_beach['name'] if nearest_beach else 'Unknown',
            'drive_time_minutes': round(min_drive_time, 1),
            'walk_time_minutes': round(min_walk_time, 1),
            'distance_km': round(geodesic((hotel_lat, hotel_lon), 
                                        (nearest_beach['lat'], nearest_beach['lon'])).kilometers, 2) if nearest_beach else 0
        }
    
    def create_isochrone_map(self, hotel_info, drive_isochrones, walk_isochrones, beach_info, output_dir):
        """Create interactive isochrone map for a hotel"""
        
        # Create folium map centered on hotel
        m = folium.Map(
            location=[hotel_info['lat'], hotel_info['lon']], 
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Color schemes for isochrones
        drive_colors = {'5': '#FF0000', '10': '#FF6600', '15': '#FFCC00', '30': '#66FF00', '60': '#00FF00'}
        walk_colors = {'5': '#0000FF', '10': '#0066FF', '15': '#00CCFF', '30': '#66FFFF', '60': '#CCFFFF'}
        
        # Add driving isochrones
        for time_min, points in drive_isochrones.items():
            if points:
                # Convert to lat, lon format for folium
                folium_points = [[p[1], p[0]] for p in points]  # Swap lon, lat to lat, lon
                
                folium.Polygon(
                    locations=folium_points,
                    popup=f'Driving: {time_min} minutes',
                    color=drive_colors.get(str(time_min), '#FF0000'),
                    weight=2,
                    fill=True,
                    fillColor=drive_colors.get(str(time_min), '#FF0000'),
                    fillOpacity=0.3
                ).add_to(m)
        
        # Add walking isochrones
        for time_min, points in walk_isochrones.items():
            if points:
                folium_points = [[p[1], p[0]] for p in points]
                
                folium.Polygon(
                    locations=folium_points,
                    popup=f'Walking: {time_min} minutes',
                    color=walk_colors.get(str(time_min), '#0000FF'),
                    weight=2,
                    fill=True,
                    fillColor=walk_colors.get(str(time_min), '#0000FF'),
                    fillOpacity=0.2
                ).add_to(m)
        
        # Add hotel marker
        folium.Marker(
            [hotel_info['lat'], hotel_info['lon']],
            popup=f"<b>{hotel_info['name']}</b><br>"
                  f"Rating: {hotel_info.get('rating', 'N/A')} stars<br>"
                  f"Nearest beach: {beach_info['nearest_beach']}<br>"
                  f"Drive to beach: {beach_info['drive_time_minutes']} min<br>"
                  f"Walk to beach: {beach_info['walk_time_minutes']} min",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Add beach locations
        for beach in self.beach_locations:
            folium.CircleMarker(
                [beach['lat'], beach['lon']],
                popup=f"🏖️ {beach['name']}",
                radius=5,
                color='blue',
                fillColor='lightblue',
                fillOpacity=0.7
            ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Isochrone Legend</b></p>
        <p><b>Driving Times:</b></p>
        <p><i style="color:#FF0000">█</i> 5 minutes</p>
        <p><i style="color:#FF6600">█</i> 10 minutes</p>
        <p><i style="color:#FFCC00">█</i> 15 minutes</p>
        <p><i style="color:#66FF00">█</i> 30 minutes</p>
        <p><i style="color:#00FF00">█</i> 60 minutes</p>
        <p><b>Walking Times:</b></p>
        <p><i style="color:#0000FF">█</i> 5-60 minutes</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        map_file = os.path.join(output_dir, 'isochrone_map.html')
        m.save(map_file)
        
        return map_file
    
    def create_static_map(self, hotel_info, drive_isochrones, walk_isochrones, beach_info, output_dir):
        """Create static matplotlib version of isochrone map"""
        
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Plot isochrones
        drive_colors = {5: '#FF0000', 10: '#FF6600', 15: '#FFCC00', 30: '#66FF00', 60: '#00FF00'}
        walk_colors = {5: '#0000FF', 10: '#0066FF', 15: '#00CCFF', 30: '#66FFFF', 60: '#CCFFFF'}
        
        # Plot driving isochrones
        for time_min, points in drive_isochrones.items():
            if points and len(points) > 2:
                lons, lats = zip(*points)
                ax.fill(lons, lats, color=drive_colors.get(time_min, '#FF0000'), 
                       alpha=0.3, label=f'Drive {time_min}min')
                ax.plot(lons, lats, color=drive_colors.get(time_min, '#FF0000'), linewidth=2)
        
        # Plot walking isochrones  
        for time_min, points in walk_isochrones.items():
            if points and len(points) > 2:
                lons, lats = zip(*points)
                ax.fill(lons, lats, color=walk_colors.get(time_min, '#0000FF'), 
                       alpha=0.2, label=f'Walk {time_min}min')
                ax.plot(lons, lats, color=walk_colors.get(time_min, '#0000FF'), 
                       linewidth=1, linestyle='--')
        
        # Plot hotel
        ax.plot(hotel_info['lon'], hotel_info['lat'], 'ro', markersize=12, 
               markeredgecolor='white', markeredgewidth=2, label='Hotel')
        
        # Plot beaches
        for beach in self.beach_locations:
            ax.plot(beach['lon'], beach['lat'], 'bs', markersize=6, alpha=0.7)
        
        # Formatting
        ax.set_xlabel('Longitude', fontsize=12)
        ax.set_ylabel('Latitude', fontsize=12)
        ax.set_title(f'Isochrone Analysis: {hotel_info["name"]}\n'
                    f'Nearest Beach: {beach_info["nearest_beach"]} '
                    f'({beach_info["drive_time_minutes"]}min drive)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        static_file = os.path.join(output_dir, 'isochrone_static.png')
        plt.savefig(static_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return static_file
    
    def process_hotel(self, hotel):
        """Process a single hotel and generate its isochrone analysis"""
        
        if not hotel.get('latitude') or not hotel.get('longitude'):
            print(f"⚠️  Skipping {hotel['name']} - missing coordinates")
            return None
        
        try:
            lat = float(hotel['latitude'])
            lon = float(hotel['longitude'])
        except (ValueError, TypeError):
            print(f"⚠️  Skipping {hotel['name']} - invalid coordinates")
            return None
        
        hotel_info = {
            'name': hotel['name'],
            'lat': lat,
            'lon': lon,
            'rating': hotel.get('star_rating', ''),
            'code': self.generate_hotel_code(hotel['name'])
        }
        
        print(f"🏨 Processing: {hotel_info['name']} ({hotel_info['code']})")
        
        # Create hotel output directory
        hotel_dir = os.path.join(self.output_base_dir, hotel_info['code'])
        Path(hotel_dir).mkdir(exist_ok=True)
        
        # Calculate isochrones
        print("🚗 Calculating driving isochrones...")
        drive_isochrones = self.calculate_isochrones_networkx(
            lat, lon, self.drive_graph, self.time_intervals, speed_kmh=50
        )
        
        print("🚶 Calculating walking isochrones...")  
        walk_isochrones = self.calculate_isochrones_networkx(
            lat, lon, self.walk_graph, self.time_intervals, speed_kmh=5
        )
        
        # Calculate beach distances
        print("🏖️  Calculating beach distances...")
        beach_info = self.calculate_time_to_nearest_beach(lat, lon)
        
        # Create maps
        print("🗺️  Creating interactive map...")
        interactive_map = self.create_isochrone_map(hotel_info, drive_isochrones, walk_isochrones, beach_info, hotel_dir)
        
        print("📊 Creating static map...")
        static_map = self.create_static_map(hotel_info, drive_isochrones, walk_isochrones, beach_info, hotel_dir)
        
        # Save analysis data
        analysis_data = {
            'hotel_info': hotel_info,
            'beach_analysis': beach_info,
            'isochrone_summary': {
                'drive_areas_calculated': len(drive_isochrones),
                'walk_areas_calculated': len(walk_isochrones),
                'time_intervals': self.time_intervals
            },
            'files_created': {
                'interactive_map': os.path.basename(interactive_map),
                'static_map': os.path.basename(static_map)
            }
        }
        
        # Save JSON data
        json_file = os.path.join(hotel_dir, 'analysis_data.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        print(f"✅ Completed: {hotel_info['name']}")
        print(f"📁 Files saved in: {hotel_dir}")
        print("-" * 60)
        
        return analysis_data
    
    def run_analysis(self, limit=None):
        """Run isochrone analysis for all hotels"""
        
        print("🚀 Starting Hotel Isochrone Analysis")
        print("=" * 60)
        
        # Initialize networks and beaches
        if not self.initialize_networks():
            print("❌ Failed to initialize networks. Exiting.")
            return
        
        self.load_beach_locations()
        
        # Filter hotels with coordinates
        valid_hotels = []
        for hotel in self.hotels_data:
            if hotel.get('latitude') and hotel.get('longitude'):
                valid_hotels.append(hotel)
        
        print(f"📊 Found {len(valid_hotels)} hotels with coordinates")
        print(f"🎯 Processing all {len(valid_hotels)} hotels")
        
        # Process each hotel
        results = []
        for i, hotel in enumerate(valid_hotels, 1):
            try:
                print(f"\n📍 [{i}/{len(valid_hotels)}] Processing hotel...")
                result = self.process_hotel(hotel)
                if result:
                    results.append(result)
                    
                # Small delay to avoid overwhelming services
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing {hotel.get('name', 'Unknown')}: {e}")
                continue
        
        # Generate summary report
        self.generate_summary_report(results)
        
        print(f"\n🎯 ANALYSIS COMPLETE!")
        print(f"✅ Successfully processed: {len(results)} hotels")
        print(f"📁 Results saved in: {self.output_base_dir}/")
        
        return results
    
    def generate_summary_report(self, results):
        """Generate summary report of all analyses"""
        
        if not results:
            return
        
        # Create summary data
        summary_data = {
            'analysis_overview': {
                'total_hotels_processed': len(results),
                'analysis_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'time_intervals_analyzed': self.time_intervals
            },
            'beach_accessibility': [],
            'hotel_summaries': []
        }
        
        # Collect beach accessibility data
        for result in results:
            beach_data = result['beach_analysis']
            summary_data['beach_accessibility'].append({
                'hotel_name': result['hotel_info']['name'],
                'hotel_code': result['hotel_info']['code'],
                'nearest_beach': beach_data['nearest_beach'],
                'drive_time_minutes': beach_data['drive_time_minutes'],
                'walk_time_minutes': beach_data['walk_time_minutes'],
                'distance_km': beach_data['distance_km']
            })
            
            summary_data['hotel_summaries'].append({
                'name': result['hotel_info']['name'],
                'code': result['hotel_info']['code'],
                'rating': result['hotel_info']['rating'],
                'coordinates': [result['hotel_info']['lat'], result['hotel_info']['lon']]
            })
        
        # Calculate statistics
        drive_times = [b['drive_time_minutes'] for b in summary_data['beach_accessibility']]
        walk_times = [b['walk_time_minutes'] for b in summary_data['beach_accessibility']]
        
        summary_data['statistics'] = {
            'average_drive_to_beach_minutes': round(np.mean(drive_times), 1),
            'average_walk_to_beach_minutes': round(np.mean(walk_times), 1),
            'shortest_drive_to_beach_minutes': round(min(drive_times), 1),
            'longest_drive_to_beach_minutes': round(max(drive_times), 1),
            'hotels_within_15min_drive': sum(1 for t in drive_times if t <= 15),
            'hotels_within_60min_walk': sum(1 for t in walk_times if t <= 60)
        }
        
        # Save summary
        summary_file = os.path.join(self.output_base_dir, 'ANALYSIS_SUMMARY.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        # Create summary report
        report_file = os.path.join(self.output_base_dir, 'SUMMARY_REPORT.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Hotel Isochrone Analysis Summary Report\n\n")
            f.write(f"**Analysis Date:** {summary_data['analysis_overview']['analysis_date']}\n\n")
            f.write(f"**Hotels Processed:** {len(results)}\n\n")
            f.write(f"## Beach Accessibility Statistics\n\n")
            f.write(f"- **Average drive to beach:** {summary_data['statistics']['average_drive_to_beach_minutes']} minutes\n")
            f.write(f"- **Average walk to beach:** {summary_data['statistics']['average_walk_to_beach_minutes']} minutes\n")
            f.write(f"- **Shortest drive to beach:** {summary_data['statistics']['shortest_drive_to_beach_minutes']} minutes\n")
            f.write(f"- **Hotels within 15min drive to beach:** {summary_data['statistics']['hotels_within_15min_drive']}\n")
            f.write(f"- **Hotels within 60min walk to beach:** {summary_data['statistics']['hotels_within_60min_walk']}\n\n")
            f.write(f"## Hotel Directory\n\n")
            
            for hotel in summary_data['hotel_summaries']:
                f.write(f"- **{hotel['name']}** (`{hotel['code']}`) - {hotel['rating']} stars\n")
        
        print(f"📋 Summary report saved: {report_file}")

def main():
    """Main function to run hotel isochrone analysis"""
    
    print("🗺️  Hotel Isochrone Analysis Generator")
    print("=" * 50)
    
    # Load hotel data
    json_file = 'data/hotels.json'
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            hotels_data = json.load(f)
        print(f"📊 Loaded {len(hotels_data)} hotels from {json_file}")
    except FileNotFoundError:
        json_file = '../data/hotels.json'
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                hotels_data = json.load(f)
            print(f"📊 Loaded {len(hotels_data)} hotels from {json_file}")
        except FileNotFoundError:
            print(f"❌ Error: Could not find hotels.json")
            return
    
    # Create analyzer
    analyzer = HotelIsochroneAnalyzer(hotels_data)
    
    # Run analysis for all hotels
    
    results = analyzer.run_analysis()  # Process all hotels
    
    if results:
        print(f"\n🎉 SUCCESS! Generated isochrone maps for {len(results)} hotels")
        print(f"📁 Check the 'hotel_isochrones' folder for results")
    else:
        print(f"\n❌ No hotels were successfully processed")

if __name__ == "__main__":
    main()