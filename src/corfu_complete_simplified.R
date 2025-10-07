# Simplified Complete Corfu Walking Isochrones Map
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
  library(RColorBrewer)
})

cat("🏝️  Simplified Corfu Walking Isochrones Map Generator\n")
cat("====================================================\n")

# Configuration
MAX_HOTELS <- 141  # Process ALL hotels
WALKING_SPEED_KMH <- 5  # km/h
TIME_INTERVALS <- c(5, 10, 15, 20, 30, 45, 60)  # minutes
OUTPUT_FILE <- "corfu_complete_walking_isochrones_simplified.png"
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
  filter(latitude > 35 & latitude < 45) %>%  # Reasonable bounds for Greece
  filter(longitude > 15 & longitude < 25)

cat(sprintf("✅ Loaded %d hotels with valid coordinates\n", nrow(hotels_clean)))

# Take all hotels
hotels_to_process <- head(hotels_clean, MAX_HOTELS)
cat(sprintf("🎯 Processing %d hotels...\n", nrow(hotels_to_process)))

# Define map bounds with padding
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

# Get Corfu island boundary for background
cat("🗺️  Getting Corfu island boundary...\n")
corfu_boundary <- NULL

# Try multiple approaches to get the island shape
tryCatch({
  # Method 1: Try administrative boundary
  corfu_admin <- opq(bbox = bbox) %>%
    add_osm_feature(key = "admin_level", value = "8") %>%
    add_osm_feature(key = "name:en", value = "Corfu")
  
  corfu_result <- osmdata_sf(corfu_admin)
  
  if (!is.null(corfu_result$osm_multipolygons) && nrow(corfu_result$osm_multipolygons) > 0) {
    corfu_boundary <- corfu_result$osm_multipolygons[1, ]
    cat("✅ Found Corfu administrative boundary\n")
  }
}, error = function(e) {
  cat("⚠️  Method 1 failed, trying method 2...\n")
})

if (is.null(corfu_boundary)) {
  tryCatch({
    # Method 2: Try coastline and create polygon
    coastline_query <- opq(bbox = bbox) %>%
      add_osm_feature(key = "natural", value = "coastline")
    
    coastline_result <- osmdata_sf(coastline_query)
    
    if (!is.null(coastline_result$osm_lines) && nrow(coastline_result$osm_lines) > 0) {
      # Combine all coastline segments
      coastlines <- coastline_result$osm_lines
      coastlines_combined <- st_union(coastlines)
      
      # Try to create polygon from coastlines
      coastlines_poly <- st_polygonize(coastlines_combined)
      
      if (length(coastlines_poly) > 0) {
        # Take the largest polygon
        polys <- st_collection_extract(coastlines_poly, "POLYGON")
        if (length(polys) > 0) {
          areas <- st_area(polys)
          largest_poly <- polys[which.max(areas)]
          corfu_boundary <- st_sf(geometry = largest_poly)
          cat("✅ Created boundary from coastlines\n")
        }
      }
    }
  }, error = function(e) {
    cat("⚠️  Method 2 failed, trying method 3...\n")
  })
}

if (is.null(corfu_boundary)) {
  tryCatch({
    # Method 3: Get land areas
    land_query <- opq(bbox = bbox) %>%
      add_osm_feature(key = "natural", value = "land")
    
    land_result <- osmdata_sf(land_query)
    
    if (!is.null(land_result$osm_multipolygons) && nrow(land_result$osm_multipolygons) > 0) {
      corfu_boundary <- land_result$osm_multipolygons
      cat("✅ Found land areas\n")
    } else if (!is.null(land_result$osm_polygons) && nrow(land_result$osm_polygons) > 0) {
      corfu_boundary <- land_result$osm_polygons
      cat("✅ Found land polygons\n")
    }
  }, error = function(e) {
    cat("⚠️  Method 3 failed, will use hotel points for reference\n")
  })
}

# Simple circular buffer approach for isochrones
cat("🚶 Creating walking isochrones using buffer method...\n")

# Convert hotels to sf points
hotels_sf <- st_as_sf(hotels_to_process, 
                     coords = c("longitude", "latitude"), 
                     crs = 4326)

# Transform to a projected coordinate system for accurate distance calculations
# Using UTM zone 34N which covers Greece
hotels_projected <- st_transform(hotels_sf, crs = 32634)

# Create isochrones as circular buffers (simplified approach)
all_isochrones <- list()

for (i in 1:nrow(hotels_projected)) {
  hotel <- hotels_projected[i, ]
  
  for (time_min in TIME_INTERVALS) {
    # Calculate walking distance in meters
    walking_distance <- (WALKING_SPEED_KMH * 1000 * time_min) / 60
    
    # Create circular buffer
    buffer <- st_buffer(hotel, dist = walking_distance)
    
    # Add attributes
    buffer$time_min <- time_min
    buffer$hotel_name <- hotels_to_process$name[i]
    buffer$hotel_id <- i
    
    all_isochrones[[paste(i, time_min, sep = "_")]] <- buffer
  }
  
  if (i %% 20 == 0) {
    cat(sprintf("  Progress: %d/%d hotels processed\n", i, nrow(hotels_projected)))
  }
}

# Combine all isochrones
combined_isochrones <- do.call(rbind, all_isochrones)
cat(sprintf("✅ Created %d isochrone zones from %d hotels\n", 
            nrow(combined_isochrones), nrow(hotels_projected)))

# Transform back to WGS84 for mapping
combined_isochrones_wgs84 <- st_transform(combined_isochrones, crs = 4326)
hotels_wgs84 <- st_transform(hotels_projected, crs = 4326)

# Create the map
cat("🗺️  Creating complete map...\n")

# Set up the base plot
p <- ggplot()

# Add Corfu island boundary if available
if (!is.null(corfu_boundary)) {
  p <- p + 
    geom_sf(data = corfu_boundary, 
            fill = "lightblue", 
            color = "darkblue", 
            alpha = 0.3,
            size = 0.8)
  cat("✅ Added Corfu island background\n")
}

# Create beautiful gradient color scheme
time_colors <- c(
  "5" = "#1a9850",    # Dark Green
  "10" = "#66bd63",   # Medium Green  
  "15" = "#a6d96a",   # Light Green
  "20" = "#d9ef8b",   # Yellow Green
  "30" = "#fee08b",   # Light Orange
  "45" = "#fdae61",   # Orange
  "60" = "#f46d43"    # Red Orange
)

# Add isochrones with beautiful transparency gradient
# Add largest zones first (60 min) so smaller zones appear on top
for (time in rev(TIME_INTERVALS)) {
  time_data <- combined_isochrones_wgs84[combined_isochrones_wgs84$time_min == time, ]
  if (nrow(time_data) > 0) {
    alpha_val <- 0.15 + (max(TIME_INTERVALS) - time) / max(TIME_INTERVALS) * 0.35
    p <- p +
      geom_sf(data = time_data,
              fill = time_colors[as.character(time)],
              color = "white",
              alpha = alpha_val,
              size = 0.1)
  }
}

# Add hotel points on top
p <- p +
  geom_sf(data = hotels_wgs84,
          color = "darkred",
          fill = "red",
          size = 1.5,
          alpha = 0.9,
          shape = 21,
          stroke = 0.5)

# Create custom legend
legend_data <- data.frame(
  time = TIME_INTERVALS,
  color = time_colors[as.character(TIME_INTERVALS)]
)

# Styling and theming
p <- p +
  coord_sf(xlim = c(bbox[1], bbox[3]), 
           ylim = c(bbox[2], bbox[4]),
           expand = FALSE) +
  theme_void() +
  theme(
    plot.title = element_text(hjust = 0.5, size = 22, face = "bold", 
                             color = "darkblue", margin = margin(b = 10)),
    plot.subtitle = element_text(hjust = 0.5, size = 14, color = "gray40", 
                                margin = margin(b = 25)),
    legend.position = "right",
    legend.title = element_text(size = 12, face = "bold"),
    legend.text = element_text(size = 10),
    legend.key.size = unit(1.0, "cm"),
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "#f0f8ff", color = NA),
    plot.margin = margin(25, 25, 25, 25),
    legend.margin = margin(0, 0, 0, 20)
  ) +
  labs(
    title = "Walking Distance Isochrones for All Corfu Hotels",
    subtitle = sprintf("Complete Analysis of %d Hotels • Walking Speed: %d km/h • %d Time Zones", 
                      nrow(hotels_projected), WALKING_SPEED_KMH, length(TIME_INTERVALS)),
    caption = sprintf("Generated on %s • Red dots = Hotels • Colored areas = Walking reach zones • Data: OpenStreetMap", 
                      Sys.Date())
  )

# Add manual legend for time intervals
p <- p + 
  scale_fill_manual(
    name = "Walking Time\n(minutes)",
    values = time_colors,
    labels = paste(TIME_INTERVALS, "min"),
    guide = guide_legend(
      override.aes = list(alpha = 0.7, size = 3),
      title.position = "top",
      label.position = "right"
    )
  )

# Save the map
cat(sprintf("💾 Saving map as: %s\n", OUTPUT_FILE))
ggsave(OUTPUT_FILE, plot = p, 
       width = MAP_WIDTH, height = MAP_HEIGHT, 
       dpi = DPI, units = "in",
       bg = "white")

# Generate summary report
cat("\n📊 COMPLETE SUMMARY REPORT\n")
cat("==========================\n")
cat(sprintf("Hotels processed: %d\n", nrow(hotels_projected)))
cat(sprintf("Total walking zones: %d\n", nrow(combined_isochrones_wgs84)))
cat(sprintf("Average zones per hotel: %.1f\n", nrow(combined_isochrones_wgs84) / nrow(hotels_projected)))

zone_breakdown <- table(combined_isochrones_wgs84$time_min)
cat("\nZone breakdown:\n")
for (time in names(zone_breakdown)) {
  cat(sprintf("%8s minutes: %3d zones\n", time, zone_breakdown[time]))
}

cat(sprintf("\n🎉 SUCCESS! Complete Corfu walking isochrones map created\n"))
cat(sprintf("📁 Output file: %s\n", OUTPUT_FILE))
cat(sprintf("📐 Resolution: %d x %d inches at %d DPI\n", MAP_WIDTH, MAP_HEIGHT, DPI))

cat(sprintf("\n%s\n", paste(rep("=", 55), collapse = "")))