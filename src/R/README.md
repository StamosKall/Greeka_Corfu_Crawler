# R Code Reorganization Guide

## 📁 New Structure

The R code has been reorganized to eliminate duplicate functionality and improve maintainability:

```
src/
├── R/
│   ├── utils/                     # Shared utility modules
│   │   ├── load_utils.R          # Main loader for all utilities
│   │   ├── data_loader.R         # Hotel data loading functions
│   │   ├── geo_functions.R       # Geographic and spatial utilities
│   │   ├── isochrone_functions.R # Isochrone generation functions
│   │   └── map_styling.R         # Map styling and visualization
│   │
│   ├── examples/                  # Refactored example scripts
│   │   └── walking_isochrones_simplified.R
│   │
│   └── legacy/                    # Original scripts (to be migrated)
│       ├── corfu_complete_simplified.R
│       ├── corfu_final_polished.R
│       ├── corfu_individual_hotel_style.R
│       └── ...
```

## 🔧 Shared Utilities

### 1. **data_loader.R**
- `load_hotel_data()` - Load and clean hotel JSON data
- `hotels_to_sf()` - Convert hotels to spatial features
- `filter_by_stars()` - Filter hotels by star rating
- `calculate_bbox()` - Calculate bounding box with padding
- `get_hotel_stats()` - Get summary statistics

### 2. **geo_functions.R**
- `get_corfu_boundary()` - Get Corfu island boundary from OSM
- `get_walking_network()` - Download walking network data
- `calculate_haversine_distance()` - Calculate distances between points
- `calculate_distance_matrix()` - Create distance matrix for all hotels
- `project_to_utm()` / `project_to_wgs84()` - Coordinate transformations

### 3. **isochrone_functions.R**
- `create_circular_isochrone()` - Simple buffer-based isochrones
- `create_network_isochrone()` - Network-aware isochrones
- `create_hotel_isochrones()` - Batch isochrone generation
- `create_smooth_isochrones()` - Density-based smooth isochrones
- `merge_isochrones_by_time()` - Merge overlapping zones

### 4. **map_styling.R**
- `get_walking_colors()` - Color palettes for walking times
- `get_star_color()` - Colors for hotel star ratings
- `create_base_theme()` - Consistent map theming
- `create_isochrone_map()` - Complete isochrone map generation
- `save_map()` - High-quality map export

## 📝 How to Use

### Quick Start

```r
# Load all utilities
source("R/utils/load_utils.R")

# Load hotel data
hotels <- load_hotel_data()

# Create spatial features
hotels_sf <- hotels_to_sf(hotels)

# Get Corfu boundary
boundary <- get_corfu_boundary()

# Create isochrones
isochrones <- create_hotel_isochrones(
  hotels_sf,
  time_intervals = c(5, 10, 15, 30),
  method = "circular"
)

# Generate map
map <- create_isochrone_map(hotels_sf, isochrones, boundary)

# Save
save_map(map, "my_map.png")
```

### Migration Guide

To update existing scripts:

1. **Replace data loading:**
   ```r
   # Old way
   hotels_data <- fromJSON("../data/hotels.json")
   hotels_clean <- hotels_data %>% filter(...)

   # New way
   source("R/utils/load_utils.R")
   hotels_clean <- load_hotel_data()
   ```

2. **Replace boundary fetching:**
   ```r
   # Old way (complex OSM queries)
   # New way
   boundary <- get_corfu_boundary()
   ```

3. **Replace isochrone creation:**
   ```r
   # Old way (manual loops)
   # New way
   isochrones <- create_hotel_isochrones(hotels_sf, time_intervals)
   ```

## 🎯 Benefits

1. **No Duplication**: Common functions defined once
2. **Consistent**: Same data loading and processing everywhere
3. **Maintainable**: Fix bugs in one place
4. **Testable**: Utilities can be tested independently
5. **Reusable**: Easy to create new analyses
6. **Documented**: Clear function purposes and parameters

## 🚀 Next Steps

1. Migrate remaining scripts to use utilities
2. Add unit tests for utility functions
3. Create more specialized analysis functions
4. Document function parameters with roxygen2
5. Consider creating an R package structure

## 📚 Examples

See `R/examples/walking_isochrones_simplified.R` for a complete refactored script using the new utilities.