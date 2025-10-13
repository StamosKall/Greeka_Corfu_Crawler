# Complete Corfu Walking Isochrones Map with Island Background
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
  library(dodgr)
  library(concaveman)
  library(lwgeom)
  library(scales)
  library(RColorBrewer)
})

cat("🏝️  Complete Corfu Walking Isochrones Map Generator\n")
cat("=================================================\n")

# Configuration
MAX_HOTELS <- 141  # Process ALL hotels
WALKING_SPEED_KMH <- 5  # km/h
TIME_INTERVALS <- c(5, 10, 15, 20, 30, 45, 60)  # minutes
OUTPUT_FILE <- "corfu_complete_walking_isochrones.png"
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

# Take all hotels (or limit if specified)
hotels_to_process <- head(hotels_clean, MAX_HOTELS)
cat(sprintf("🎯 Processing %d hotels...\n", nrow(hotels_to_process)))

# Define map bounds with padding
lat_range <- range(as.numeric(hotels_to_process$latitude))
lon_range <- range(as.numeric(hotels_to_process$longitude))
lat_padding <- (lat_range[2] - lat_range[1]) * 0.1
lon_padding <- (lon_range[2] - lon_range[1]) * 0.1

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
tryCatch({
  # Try to get Corfu administrative boundary
  corfu_query <- opq(bbox = bbox) %>%
    add_osm_feature(key = "place", value = "island") %>%
    add_osm_feature(key = "name", value = "Corfu")
  
  corfu_osm <- osmdata_sf(corfu_query)
  
  if (!is.null(corfu_osm$osm_multipolygons) && nrow(corfu_osm$osm_multipolygons) > 0) {
    corfu_boundary <- corfu_osm$osm_multipolygons
    cat("✅ Found Corfu island boundary\n")
  } else if (!is.null(corfu_osm$osm_polygons) && nrow(corfu_osm$osm_polygons) > 0) {
    corfu_boundary <- corfu_osm$osm_polygons
    cat("✅ Found Corfu island boundary (polygons)\n")
  }
}, error = function(e) {
  cat("⚠️  Could not get Corfu boundary, trying coastline...\n")
})

# If no island boundary, try coastline
if (is.null(corfu_boundary)) {
  tryCatch({
    coastline_query <- opq(bbox = bbox) %>%
      add_osm_feature(key = "natural", value = "coastline")
    
    coastline_osm <- osmdata_sf(coastline_query)
    
    if (!is.null(coastline_osm$osm_lines) && nrow(coastline_osm$osm_lines) > 0) {
      # Convert coastline to polygon
      coastline_combined <- st_union(coastline_osm$osm_lines)
      coastline_poly <- st_polygonize(coastline_combined)
      
      if (length(coastline_poly) > 0) {
        corfu_boundary <- st_sf(geometry = coastline_poly)
        cat("✅ Created boundary from coastline\n")
      }
    }
  }, error = function(e) {
    cat("⚠️  Could not get coastline either\n")
  })
}

# Get walking network
cat("🚶 Downloading walking network...\n")
tryCatch({
  walking_net <- opq(bbox = bbox) %>%
    add_osm_feature(key = "highway", 
                   value = c("footway", "path", "pedestrian", "steps", "track", 
                            "residential", "tertiary", "secondary", "primary", "living_street")) %>%
    osmdata_sf()
  
  if (!is.null(walking_net$osm_lines)) {
    walking_roads <- walking_net$osm_lines
    cat(sprintf("✅ Walking network downloaded: %d segments\n", nrow(walking_roads)))
  } else {
    stop("No walking network found")
  }
}, error = function(e) {
  cat("❌ Error downloading walking network:", e$message, "\n")
  stop("Cannot proceed without walking network")
})

# Convert to dodgr graph
cat("🔗 Building routing graph...\n")
tryCatch({
  walking_graph <- weight_streetnet(walking_roads, wt_profile = "foot")
  cat("✅ Routing graph built successfully\n")
}, error = function(e) {
  cat("❌ Error building graph:", e$message, "\n")
  stop("Cannot proceed without routing graph")
})

# Function to create isochrones for a hotel
create_hotel_isochrones <- function(hotel_row, graph, time_intervals) {
  hotel_coords <- c(hotel_row$longitude, hotel_row$latitude)
  isochrones <- list()
  
  for (time_min in time_intervals) {
    tryCatch({
      # Calculate walking distance in meters
      max_distance <- (WALKING_SPEED_KMH * 1000 * time_min) / 60
      
      # Find reachable points
      iso_points <- dodgr_isochrones(graph, from = hotel_coords, tlim = max_distance)
      
      if (!is.null(iso_points) && nrow(iso_points) > 3) {
        # Convert to sf points
        points_sf <- st_as_sf(iso_points, coords = c("lon", "lat"), crs = 4326)
        
        # Create concave hull (isochrone boundary)
        if (nrow(points_sf) >= 3) {
          hull <- concaveman(points_sf, concavity = 2, length_threshold = 0.1)
          
          if (!is.null(hull) && nrow(hull) > 0) {
            hull$time_min <- time_min
            hull$hotel_id <- hotel_row$name
            hull$hotel_lat <- hotel_row$latitude
            hull$hotel_lon <- hotel_row$longitude
            isochrones[[as.character(time_min)]] <- hull
          }
        }
      }
    }, error = function(e) {
      # Silently continue on error
    })
  }
  
  if (length(isochrones) > 0) {
    return(do.call(rbind, isochrones))
  } else {
    return(NULL)
  }
}

# Process all hotels
cat("🎯 Processing hotels for isochrones...\n")
all_isochrones <- list()
processed_count <- 0

for (i in 1:nrow(hotels_to_process)) {
  hotel <- hotels_to_process[i, ]
  cat(sprintf("  [%d/%d] Processing: %s\n", i, nrow(hotels_to_process), 
              substr(hotel$name, 1, 50)))
  
  hotel_iso <- create_hotel_isochrones(hotel, walking_graph, TIME_INTERVALS)
  
  if (!is.null(hotel_iso)) {
    all_isochrones[[i]] <- hotel_iso
    processed_count <- processed_count + 1
  }
  
  # Progress indicator
  if (i %% 10 == 0) {
    cat(sprintf("    Progress: %d/%d hotels processed\n", i, nrow(hotels_to_process)))
  }
}

# Combine all isochrones
if (length(all_isochrones) > 0) {
  combined_isochrones <- do.call(rbind, all_isochrones)
  cat(sprintf("✅ Created %d isochrone zones from %d hotels\n", 
              nrow(combined_isochrones), processed_count))
} else {
  stop("❌ No isochrones were created!")
}

# Prepare hotel points for plotting
hotels_sf <- st_as_sf(hotels_to_process, 
                     coords = c("longitude", "latitude"), 
                     crs = 4326)

# Create the map
cat("🗺️  Creating complete map...\n")

# Set up the base plot
p <- ggplot()

# Add Corfu island boundary if available
if (!is.null(corfu_boundary)) {
  p <- p + 
    geom_sf(data = corfu_boundary, 
            fill = "lightgray", 
            color = "darkgray", 
            alpha = 0.3,
            size = 0.5)
  cat("✅ Added Corfu island boundary\n")
}

# Create custom color palette for time intervals
time_colors <- c(
  "5" = "#2E8B57",    # Sea Green
  "10" = "#3CB371",   # Medium Sea Green  
  "15" = "#66CDAA",   # Medium Aquamarine
  "20" = "#7FFFD4",   # Aquamarine
  "30" = "#87CEEB",   # Sky Blue
  "45" = "#87CEFA",   # Light Sky Blue
  "60" = "#B0E0E6"    # Powder Blue
)

# Add isochrones with gradient effect
p <- p +
  geom_sf(data = combined_isochrones,
          aes(fill = factor(time_min)),
          alpha = 0.6,
          color = "white",
          size = 0.2) +
  scale_fill_manual(values = time_colors,
                   name = "Walking Time\n(minutes)",
                   guide = guide_legend(override.aes = list(alpha = 0.8)))

# Add hotel points
p <- p +
  geom_sf(data = hotels_sf,
          color = "red",
          size = 1.2,
          alpha = 0.9)

# Styling and theming
p <- p +
  coord_sf(xlim = c(bbox[1], bbox[3]), 
           ylim = c(bbox[2], bbox[4]),
           expand = FALSE) +
  theme_void() +
  theme(
    plot.title = element_text(hjust = 0.5, size = 20, face = "bold", margin = margin(b = 20)),
    plot.subtitle = element_text(hjust = 0.5, size = 14, color = "gray40", margin = margin(b = 30)),
    legend.position = "right",
    legend.title = element_text(size = 12, face = "bold"),
    legend.text = element_text(size = 10),
    legend.key.size = unit(0.8, "cm"),
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "aliceblue", color = NA),
    plot.margin = margin(20, 20, 20, 20)
  ) +
  labs(
    title = "Walking Distance Isochrones for All Corfu Hotels",
    subtitle = sprintf("Analysis of %d Hotels with %d Walking Time Zones • Walking Speed: %d km/h", 
                      processed_count, nrow(combined_isochrones), WALKING_SPEED_KMH),
    caption = sprintf("Generated on %s • Data: OpenStreetMap", Sys.Date())
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
cat(sprintf("Hotels processed: %d\n", processed_count))
cat(sprintf("Total walking zones: %d\n", nrow(combined_isochrones)))
cat(sprintf("Average zones per hotel: %.1f\n", nrow(combined_isochrones) / processed_count))

zone_breakdown <- table(combined_isochrones$time_min)
cat("\nZone breakdown:\n")
for (time in names(zone_breakdown)) {
  cat(sprintf("%8s minutes: %3d zones\n", time, zone_breakdown[time]))
}

cat(sprintf("\n🎉 SUCCESS! Complete Corfu walking isochrones map created\n"))
cat(sprintf("📁 Output file: %s\n", OUTPUT_FILE))
cat(sprintf("📐 Resolution: %d x %d inches at %d DPI\n", MAP_WIDTH, MAP_HEIGHT, DPI))

cat(sprintf("\n%s\n", paste(rep("=", 50), collapse = "")))