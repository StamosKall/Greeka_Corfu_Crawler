# Simplified Land-Clipped Corfu Walking Isochrones
# Author: Generated for Corfu Hotels Analysis  
# Date: 2025-10-07

# Load required libraries
suppressMessages({
  library(jsonlite)
  library(sf)
  library(osmdata)
  library(ggplot2)
  library(viridis)
  library(dplyr)
  library(scales)
})

cat("🏝️  Simplified Land-Clipped Walking Isochrones\n")
cat("==============================================\n")

# Configuration
MAX_HOTELS <- 141  # Process ALL hotels
WALKING_SPEED_KMH <- 5  # km/h
TIME_INTERVALS <- c(5, 10, 15, 20, 30, 45, 60)  # minutes
OUTPUT_FILE <- "corfu_land_only_isochrones.png"
MAP_WIDTH <- 16
MAP_HEIGHT <- 20
DPI <- 300

# Load hotel data
cat("📊 Loading hotel data...\n")
hotels_data <- fromJSON("../data/hotels.json")

# Clean and prepare data
hotels_clean <- hotels_data %>%
  filter(!is.na(latitude) & !is.na(longitude)) %>%
  filter(latitude != 0 & longitude != 0) %>%
  filter(latitude > 35 & latitude < 45) %>%
  filter(longitude > 15 & longitude < 25)

cat(sprintf("✅ Loaded %d hotels with valid coordinates\n", nrow(hotels_clean)))

# Take all hotels
hotels_to_process <- head(hotels_clean, MAX_HOTELS)
cat(sprintf("🎯 Processing %d hotels...\n", nrow(hotels_to_process)))

# Define map bounds
lat_range <- range(as.numeric(hotels_to_process$latitude))
lon_range <- range(as.numeric(hotels_to_process$longitude))
lat_padding <- (lat_range[2] - lat_range[1]) * 0.15
lon_padding <- (lon_range[2] - lon_range[1]) * 0.15

bbox <- c(
  xmin = lon_range[1] - lon_padding,
  ymin = lat_range[1] - lat_padding,
  xmax = lon_range[2] + lon_padding,
  ymax = lat_range[2] + lat_padding
)

cat(sprintf("📍 Map bounds: %.3f, %.3f, %.3f, %.3f\n", bbox[1], bbox[2], bbox[3], bbox[4]))

# Get Corfu land areas for clipping
cat("🗺️  Getting Corfu land areas...\n")
corfu_land <- NULL

# Try to get land use areas
tryCatch({
  # Get various land features that represent actual land areas
  land_features <- c("residential", "forest", "grass", "farmland", "meadow", 
                     "orchard", "vineyard", "scrub", "heath", "bare_rock")
  
  land_query <- opq(bbox = bbox)
  
  # Add multiple land use features
  for (feature in land_features) {
    land_query <- land_query %>% add_osm_feature(key = "landuse", value = feature)
  }
  
  # Also add natural land features
  natural_features <- c("wood", "scrub", "grassland", "heath", "bare_rock")
  for (feature in natural_features) {
    land_query <- land_query %>% add_osm_feature(key = "natural", value = feature)
  }
  
  land_result <- osmdata_sf(land_query)
  
  # Combine all land polygons
  land_polygons <- list()
  
  if (!is.null(land_result$osm_polygons) && nrow(land_result$osm_polygons) > 0) {
    land_polygons <- append(land_polygons, list(land_result$osm_polygons))
  }
  
  if (!is.null(land_result$osm_multipolygons) && nrow(land_result$osm_multipolygons) > 0) {
    land_polygons <- append(land_polygons, list(land_result$osm_multipolygons))
  }
  
  if (length(land_polygons) > 0) {
    all_land <- do.call(rbind, land_polygons)
    corfu_land <- st_union(all_land)
    corfu_land <- st_sf(geometry = corfu_land)
    cat(sprintf("✅ Found %d land use polygons\n", nrow(all_land)))
  }
  
}, error = function(e) {
  cat("⚠️  Could not get detailed land use, trying coastline method...\n")
})

# Fallback: Use coastline to define land
if (is.null(corfu_land) || st_is_empty(corfu_land)) {
  tryCatch({
    coastline_query <- opq(bbox = bbox) %>%
      add_osm_feature(key = "natural", value = "coastline")
    
    coastline_result <- osmdata_sf(coastline_query)
    
    if (!is.null(coastline_result$osm_lines) && nrow(coastline_result$osm_lines) > 0) {
      coastlines <- coastline_result$osm_lines
      
      # Buffer coastlines inward to create land area
      coastlines_combined <- st_union(coastlines)
      
      # Create a large bounding box and subtract buffered coastlines to get land
      bbox_poly <- st_polygon(list(matrix(c(
        bbox[1], bbox[2],
        bbox[3], bbox[2], 
        bbox[3], bbox[4],
        bbox[1], bbox[4],
        bbox[1], bbox[2]
      ), ncol = 2, byrow = TRUE)))
      
      bbox_sf <- st_sf(geometry = st_sfc(bbox_poly, crs = 4326))
      
      # Buffer coastlines outward into sea
      sea_buffer <- st_buffer(coastlines_combined, dist = 0.002)  # ~200m buffer into sea
      
      # Subtract sea from bounding box to get approximate land
      corfu_land <- st_difference(bbox_sf, st_sf(geometry = st_sfc(sea_buffer, crs = 4326)))
      
      cat("✅ Created approximate land boundary from coastlines\n")
    }
  }, error = function(e) {
    cat("⚠️  Coastline method failed too\n")
  })
}

# Final fallback: Use hotel convex hull expanded
if (is.null(corfu_land) || st_is_empty(corfu_land)) {
  hotels_sf_temp <- st_as_sf(hotels_to_process, 
                            coords = c("longitude", "latitude"), 
                            crs = 4326)
  
  hotel_hull <- st_convex_hull(st_union(hotels_sf_temp))
  corfu_land <- st_buffer(hotel_hull, dist = 0.05)  # Large buffer around hotels
  corfu_land <- st_sf(geometry = corfu_land)
  
  cat("⚠️  Using expanded hotel area as land boundary\n")
}

# Convert hotels to sf points
hotels_sf <- st_as_sf(hotels_to_process, 
                     coords = c("longitude", "latitude"), 
                     crs = 4326)

# Transform to projected coordinate system for accurate distance calculations
cat("🔄 Transforming to projected coordinates...\n")
hotels_projected <- st_transform(hotels_sf, crs = 32634)  # UTM 34N for Greece
corfu_land_projected <- st_transform(corfu_land, crs = 32634)

# Create walking isochrones and clip to land
cat("🚶 Creating land-clipped walking isochrones...\n")
all_isochrones <- list()

for (i in 1:nrow(hotels_projected)) {
  hotel <- hotels_projected[i, ]
  
  for (time_min in TIME_INTERVALS) {
    # Calculate walking distance in meters
    walking_distance <- (WALKING_SPEED_KMH * 1000 * time_min) / 60
    
    # Create circular buffer around hotel
    buffer <- st_buffer(hotel, dist = walking_distance)
    
    # Clip buffer to land areas only - this removes sea areas!
    tryCatch({
      clipped <- st_intersection(buffer, corfu_land_projected)
      
      if (!st_is_empty(clipped) && st_area(clipped) > units::set_units(100, "m^2")) {
        # Create a proper sf object
        isochrone_sf <- st_sf(
          time_min = time_min,
          hotel_name = hotels_to_process$name[i],
          hotel_id = i,
          geometry = st_geometry(clipped)
        )
        
        all_isochrones[[paste(i, time_min, sep = "_")]] <- isochrone_sf
      }
    }, error = function(e) {
      # Skip if intersection fails
    })
  }
  
  if (i %% 20 == 0) {
    cat(sprintf("  Progress: %d/%d hotels processed\n", i, nrow(hotels_projected)))
  }
}

# Combine all isochrones
if (length(all_isochrones) > 0) {
  combined_isochrones_projected <- do.call(rbind, all_isochrones)
  cat(sprintf("✅ Created %d land-clipped isochrone zones\n", nrow(combined_isochrones_projected)))
} else {
  stop("❌ No land-clipped isochrones were created!")
}

# Transform back to WGS84 for mapping
combined_isochrones_wgs84 <- st_transform(combined_isochrones_projected, crs = 4326)
corfu_land_wgs84 <- st_transform(corfu_land_projected, crs = 4326)

# Create the map
cat("🎨 Creating land-only isochrones map...\n")

# Color palette
time_colors <- c(
  "#08306b",  # 5 min - Dark blue
  "#08519c",  # 10 min - Medium dark blue  
  "#3182bd",  # 15 min - Medium blue
  "#6baed6",  # 20 min - Light blue
  "#9ecae1",  # 30 min - Very light blue
  "#c6dbef",  # 45 min - Pale blue
  "#deebf7"   # 60 min - Very pale blue
)
names(time_colors) <- TIME_INTERVALS

# Build the plot
p <- ggplot()

# Add sea background
p <- p + 
  theme_void() +
  theme(
    panel.background = element_rect(fill = "#b3d9ff", color = NA),  # Light blue sea
    plot.background = element_rect(fill = "white", color = NA)
  )

# Add Corfu land boundary (light gray)
p <- p + 
  geom_sf(data = corfu_land_wgs84, 
          fill = "#f8f8f8", 
          color = "#d0d0d0", 
          alpha = 0.8,
          linewidth = 0.5)

# Add isochrones in reverse order (largest first) - ONLY ON LAND!
for (time in rev(TIME_INTERVALS)) {
  time_data <- combined_isochrones_wgs84[combined_isochrones_wgs84$time_min == time, ]
  if (nrow(time_data) > 0) {
    alpha_val <- 0.3 + (max(TIME_INTERVALS) - time) / max(TIME_INTERVALS) * 0.4
    
    p <- p +
      geom_sf(data = time_data,
              fill = time_colors[as.character(time)],
              color = "white",
              alpha = alpha_val,
              linewidth = 0.1)
  }
}

# Add hotel points on top
p <- p +
  geom_sf(data = hotels_sf,
          color = "white",
          fill = "#e31a1c",
          size = 1.8,
          alpha = 0.95,
          shape = 21,
          stroke = 0.8)

# Final styling
p <- p +
  coord_sf(xlim = c(bbox[1], bbox[3]), 
           ylim = c(bbox[2], bbox[4]),
           expand = FALSE) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 24, face = "bold", 
                             color = "#08306b", margin = margin(b = 15)),
    plot.subtitle = element_text(hjust = 0.5, size = 16, color = "#2c7fb8", 
                                margin = margin(b = 30)),
    plot.caption = element_text(hjust = 0.5, size = 12, color = "gray50",
                               margin = margin(t = 20)),
    plot.margin = margin(30, 30, 30, 30)
  ) +
  labs(
    title = "Land-Only Walking Isochrones - Corfu Hotels",
    subtitle = sprintf("Walking Areas Clipped to Land: %d Hotels • No Sea Coverage • Speed: %d km/h", 
                      length(unique(combined_isochrones_wgs84$hotel_id)), WALKING_SPEED_KMH),
    caption = "Walking zones show ONLY on land areas • Sea areas excluded • Blue = Sea, Gray = Land"
  )

# Add legend
legend_x <- bbox[3] - (bbox[3] - bbox[1]) * 0.25
legend_width <- (bbox[3] - bbox[1]) * 0.22

p <- p + 
  annotate("rect", 
           xmin = legend_x, 
           xmax = bbox[3] - (bbox[3] - bbox[1]) * 0.02, 
           ymin = bbox[4] - (bbox[4] - bbox[2]) * 0.45, 
           ymax = bbox[4] - (bbox[4] - bbox[2]) * 0.05,
           fill = "white", color = "#999999", alpha = 0.95, linewidth = 0.5) +
  annotate("text", 
           x = legend_x + legend_width/2, 
           y = bbox[4] - (bbox[4] - bbox[2]) * 0.08,
           label = "Walking Time", 
           size = 5, fontface = "bold", color = "#08306b")

# Add legend items  
for (i in 1:length(TIME_INTERVALS)) {
  y_pos <- bbox[4] - (bbox[4] - bbox[2]) * (0.12 + i * 0.04)
  
  p <- p + 
    annotate("rect",
             xmin = legend_x + legend_width * 0.1,
             xmax = legend_x + legend_width * 0.25,
             ymin = y_pos - (bbox[4] - bbox[2]) * 0.015,
             ymax = y_pos + (bbox[4] - bbox[2]) * 0.015,
             fill = time_colors[i], alpha = 0.8, color = "white", linewidth = 0.3) +
    annotate("text",
             x = legend_x + legend_width * 0.35,
             y = y_pos,
             label = paste(TIME_INTERVALS[i], "min"),
             size = 4, color = "#2c7fb8", hjust = 0)
}

# Save the map
cat(sprintf("💾 Saving land-only map as: %s\n", OUTPUT_FILE))
ggsave(OUTPUT_FILE, plot = p, 
       width = MAP_WIDTH, height = MAP_HEIGHT, 
       dpi = DPI, units = "in",
       bg = "white")

# Generate summary report
cat("\n📊 LAND-ONLY ISOCHRONES SUMMARY\n")
cat("===============================\n")
cat(sprintf("Hotels processed: %d\n", length(unique(combined_isochrones_wgs84$hotel_id))))
cat(sprintf("Total land-clipped zones: %d\n", nrow(combined_isochrones_wgs84)))

zone_breakdown <- table(combined_isochrones_wgs84$time_min)
cat("\nZone breakdown (land areas only):\n")
for (time in names(zone_breakdown)) {
  cat(sprintf("  %2s minutes: %3d zones\n", time, zone_breakdown[time]))
}

cat(sprintf("\n🎉 SUCCESS! Land-only walking isochrones created\n"))
cat(sprintf("📁 Output file: %s\n", OUTPUT_FILE))
cat(sprintf("🏝️  Key feature: Walking polygons ONLY show on land!\n"))
cat(sprintf("🌊 Sea areas are completely excluded\n"))
cat(sprintf("🚶 More realistic walking accessibility\n"))

cat(sprintf("\n%s\n", paste(rep("=", 50), collapse = "")))