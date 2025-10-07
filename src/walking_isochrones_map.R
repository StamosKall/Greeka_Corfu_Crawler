# Walking Isochrones Map Generator in R
# =====================================
# Creates a comprehensive static map showing walking distance isochrones 
# for all hotels in the Corfu dataset using R spatial packages.
#
# Author: AI Assistant  
# Date: October 2025

# Load required libraries
suppressMessages({
  library(jsonlite)
  library(sf)
  library(ggplot2)
  library(dplyr)
  library(osmdata)
  library(dodgr)
  library(concaveman)
  library(RColorBrewer)
  library(scales)
  library(gridExtra)
  library(lwgeom)
})

# Configuration
WALKING_SPEED_KMH <- 5  # Average walking speed
TIME_INTERVALS <- c(5, 10, 15, 30, 60)  # Minutes

# Color palette for walking times (light to dark green)
WALKING_COLORS <- c(
  "5" = "#E8F5E8",   # Very light green
  "10" = "#C8E6C9",  # Light green  
  "15" = "#A5D6A7",  # Medium light green
  "30" = "#81C784",  # Medium green
  "60" = "#66BB6A"   # Darker green
)

cat("🚶 Walking Isochrones Map Generator in R\n")
cat("==========================================\n")

# Function to load hotel data
load_hotels_data <- function() {
  cat("📊 Loading hotel data...\n")
  
  # Load hotels JSON
  hotels_file <- "../data/hotels.json"
  
  if (!file.exists(hotels_file)) {
    cat("❌ Hotels file not found:", hotels_file, "\n")
    return(NULL)
  }
  
  hotels_data <- fromJSON(hotels_file, flatten = TRUE)
  
  # Filter hotels with valid coordinates
  valid_hotels <- hotels_data %>%
    filter(!is.na(latitude) & !is.na(longitude)) %>%
    filter(latitude != "" & longitude != "") %>%
    mutate(
      lat = as.numeric(latitude),
      lon = as.numeric(longitude)
    ) %>%
    filter(!is.na(lat) & !is.na(lon)) %>%
    filter(lat >= -90 & lat <= 90 & lon >= -180 & lon <= 180)
  
  cat("✅ Loaded", nrow(valid_hotels), "hotels with valid coordinates\n")
  return(valid_hotels)
}

# Function to get Corfu boundary
get_corfu_boundary <- function() {
  cat("🗺️  Getting Corfu boundary...\n")
  
  tryCatch({
    # Get Corfu administrative boundary
    corfu_query <- opq(bbox = c(19.3, 39.3, 20.2, 39.9)) %>%
      add_osm_feature(key = "name", value = "Κέρκυρα") %>%
      add_osm_feature(key = "admin_level", value = "7")
    
    corfu_boundary <- osmdata_sf(corfu_query)
    
    if (!is.null(corfu_boundary$osm_multipolygons) && nrow(corfu_boundary$osm_multipolygons) > 0) {
      boundary_sf <- corfu_boundary$osm_multipolygons[1,]
      cat("✅ Corfu boundary loaded\n")
      return(boundary_sf)
    } else {
      cat("⚠️  Using hotels bounding box instead\n")
      return(NULL)  
    }
  }, error = function(e) {
    cat("⚠️  Error getting boundary, using hotels bbox:", e$message, "\n")
    return(NULL)
  })
}

# Function to get walking network for Corfu
get_walking_network <- function(bbox) {
  cat("🚶 Downloading walking network...\n")
  
  tryCatch({
    # Download street network for walking
    query <- opq(bbox = bbox) %>%
      add_osm_feature(key = "highway", 
                      value = c("primary", "secondary", "tertiary", "residential", 
                               "footway", "path", "steps", "pedestrian", "living_street",
                               "track", "unclassified", "service"))
    
    network <- osmdata_sf(query)
    
    if (!is.null(network$osm_lines) && nrow(network$osm_lines) > 0) {
      cat("✅ Walking network downloaded:", nrow(network$osm_lines), "segments\n")
      return(network$osm_lines)
    } else {
      cat("❌ No network data found\n")
      return(NULL)
    }
  }, error = function(e) {
    cat("❌ Error downloading network:", e$message, "\n")
    return(NULL)
  })
}

# Function to create isochrone using distance-based approach
create_distance_isochrone <- function(center_lat, center_lon, time_minutes, hotels_sf) {
  tryCatch({
    # Convert time to distance (km)
    max_distance_km <- (time_minutes / 60) * WALKING_SPEED_KMH
    
    # Create center point
    center_point <- st_sfc(st_point(c(center_lon, center_lat)), crs = 4326)
    
    # Simple circular approximation (can be improved with actual routing)
    # Create circular buffer around hotel
    # Transform to projected CRS for accurate distance calculation
    center_projected <- st_transform(center_point, crs = 3857)  # Web Mercator
    
    # Create buffer in meters
    buffer_m <- max_distance_km * 1000
    isochrone_projected <- st_buffer(center_projected, dist = buffer_m)
    
    # Transform back to WGS84
    isochrone <- st_transform(isochrone_projected, crs = 4326)
    
    return(isochrone)
    
  }, error = function(e) {
    cat("⚠️  Error creating isochrone:", e$message, "\n")
    return(NULL)
  })
}

# Function to create advanced isochrone with road network consideration
create_network_isochrone <- function(center_lat, center_lon, time_minutes, network_sf) {
  tryCatch({
    # Convert time to distance
    max_distance_km <- (time_minutes / 60) * WALKING_SPEED_KMH
    
    # Create center point
    center_point <- st_sfc(st_point(c(center_lon, center_lat)), crs = 4326)
    
    if (!is.null(network_sf) && nrow(network_sf) > 0) {
      # Find nearby network segments
      center_buffer <- st_buffer(st_transform(center_point, 3857), dist = max_distance_km * 1000)
      center_buffer_wgs84 <- st_transform(center_buffer, 4326)
      
      # Get network segments within buffer
      nearby_segments <- st_filter(network_sf, center_buffer_wgs84)
      
      if (nrow(nearby_segments) > 0) {
        # Create convex hull around nearby segments
        segment_points <- st_cast(nearby_segments, "POINT")
        if (nrow(segment_points) >= 3) {
          hull <- st_convex_hull(st_union(segment_points))
          return(hull)
        }
      }
    }
    
    # Fallback to circular buffer
    center_projected <- st_transform(center_point, crs = 3857)
    buffer_m <- max_distance_km * 1000
    isochrone_projected <- st_buffer(center_projected, dist = buffer_m)
    isochrone <- st_transform(isochrone_projected, crs = 4326)
    
    return(isochrone)
    
  }, error = function(e) {
    cat("⚠️  Error creating network isochrone:", e$message, "\n")
    return(NULL)
  })
}

# Main function to create walking isochrones map
create_walking_isochrones_map <- function() {
  # Load hotel data
  hotels_data <- load_hotels_data()
  if (is.null(hotels_data)) {
    cat("❌ Failed to load hotel data\n")
    return(FALSE)
  }
  
  # Convert to sf object
  hotels_sf <- st_as_sf(hotels_data, 
                        coords = c("lon", "lat"), 
                        crs = 4326)
  
  # Get map bounds
  bbox <- st_bbox(hotels_sf)
  expanded_bbox <- c(
    bbox[1] - 0.05,  # xmin
    bbox[2] - 0.05,  # ymin  
    bbox[3] + 0.05,  # xmax
    bbox[4] + 0.05   # ymax
  )
  
  cat("📍 Map bounds:", paste(round(expanded_bbox, 3), collapse = ", "), "\n")
  
  # Get Corfu boundary (optional)
  corfu_boundary <- get_corfu_boundary()
  
  # Get walking network
  walking_network <- get_walking_network(expanded_bbox)
  
  # Limit hotels for processing (adjust as needed)
  # For demonstration, process first 30 hotels
  hotels_to_process <- hotels_sf[1:min(30, nrow(hotels_sf)), ]
  
  cat("🎯 Processing", nrow(hotels_to_process), "hotels...\n")
  
  # Create isochrones for each hotel and time interval
  all_isochrones <- list()
  isochrone_counter <- 0
  
  for (i in 1:nrow(hotels_to_process)) {
    hotel <- hotels_to_process[i, ]
    hotel_coords <- st_coordinates(hotel)
    hotel_lon <- hotel_coords[1]
    hotel_lat <- hotel_coords[2]
    
    cat(sprintf("  [%d/%d] Processing: %s\n", 
                i, nrow(hotels_to_process), 
                substr(hotel$name, 1, 50)))
    
    for (time_min in TIME_INTERVALS) {
      # Create isochrone
      if (!is.null(walking_network)) {
        isochrone <- create_network_isochrone(hotel_lat, hotel_lon, time_min, walking_network)
      } else {
        isochrone <- create_distance_isochrone(hotel_lat, hotel_lon, time_min, hotels_sf)
      }
      
      if (!is.null(isochrone)) {
        isochrone_counter <- isochrone_counter + 1
        
        # Store isochrone data
        isochrone_df <- data.frame(
          id = isochrone_counter,
          hotel_id = i,
          hotel_name = hotel$name,
          time_min = time_min,
          geometry = isochrone
        )
        
        all_isochrones[[isochrone_counter]] <- st_sf(isochrone_df)
      }
    }
  }
  
  if (length(all_isochrones) == 0) {
    cat("❌ No isochrones created\n")
    return(FALSE)
  }
  
  # Combine all isochrones
  isochrones_sf <- do.call(rbind, all_isochrones)
  
  cat("✅ Created", nrow(isochrones_sf), "isochrone zones\n")
  
  # Create the map
  cat("🗺️  Creating map...\n")
  
  # Base map
  p <- ggplot() +
    theme_void() +
    theme(
      plot.title = element_text(size = 16, hjust = 0.5, face = "bold"),
      plot.subtitle = element_text(size = 12, hjust = 0.5),
      legend.position = "bottom",
      legend.title = element_text(size = 12, face = "bold"),
      legend.text = element_text(size = 10),
      panel.background = element_rect(fill = "#f0f8ff", color = NA),
      plot.background = element_rect(fill = "white", color = NA)
    )
  
  # Add Corfu boundary if available
  if (!is.null(corfu_boundary)) {
    p <- p + geom_sf(data = corfu_boundary, 
                     fill = "#f5f5f5", 
                     color = "#cccccc", 
                     size = 0.5,
                     alpha = 0.3)
  }
  
  # Add isochrones (largest to smallest)
  for (time_min in rev(TIME_INTERVALS)) {
    isochrones_subset <- isochrones_sf[isochrones_sf$time_min == time_min, ]
    
    if (nrow(isochrones_subset) > 0) {
      p <- p + geom_sf(data = isochrones_subset,
                       fill = WALKING_COLORS[[as.character(time_min)]],
                       color = WALKING_COLORS[[as.character(time_min)]],
                       alpha = 0.6,
                       size = 0.2)
    }
  }
  
  # Add hotel points
  p <- p + geom_sf(data = hotels_to_process,
                   color = "red",
                   fill = "red", 
                   size = 1.5,
                   alpha = 0.8) +
          coord_sf(xlim = c(expanded_bbox[1], expanded_bbox[3]),
                   ylim = c(expanded_bbox[2], expanded_bbox[4])) +
          labs(
            title = "Walking Distance Isochrones for Corfu Hotels",
            subtitle = sprintf("Analysis of %d Hotels with %d Walking Zones", 
                              nrow(hotels_to_process), nrow(isochrones_sf)),
            caption = paste("Generated on", Sys.Date(), "• Walking Speed: 5 km/h • Data: OpenStreetMap")
          )
  
  # Create custom legend
  legend_data <- data.frame(
    time = factor(TIME_INTERVALS, levels = TIME_INTERVALS),
    color = WALKING_COLORS[as.character(TIME_INTERVALS)],
    label = paste(TIME_INTERVALS, "min walk")
  )
  
  # Add manual legend
  p <- p + 
    scale_color_manual(
      name = "Walking Time",
      values = setNames(legend_data$color, legend_data$label),
      labels = legend_data$label
    ) +
    guides(
      color = guide_legend(
        title = "Walking Time Zones",
        override.aes = list(size = 4, alpha = 0.8)
      )
    )
  
  # Save the map
  output_file <- "walking_isochrones_corfu_hotels_R.png"
  
  ggsave(output_file, 
         plot = p,
         width = 16, 
         height = 12, 
         dpi = 300,
         bg = "white")
  
  cat("✅ Map saved as:", output_file, "\n")
  
  # Print summary
  cat("\n📊 SUMMARY REPORT\n")
  cat("==================\n")
  cat("Hotels processed:", nrow(hotels_to_process), "\n")
  cat("Total walking zones:", nrow(isochrones_sf), "\n")
  cat("Average zones per hotel:", round(nrow(isochrones_sf) / nrow(hotels_to_process), 1), "\n")
  
  # Zone counts by time
  zone_counts <- table(isochrones_sf$time_min)
  cat("\nZone breakdown:\n")
  for (time_min in TIME_INTERVALS) {
    count <- ifelse(as.character(time_min) %in% names(zone_counts), 
                   zone_counts[as.character(time_min)], 0)
    cat(sprintf("  %2d minutes: %3d zones\n", time_min, count))
  }
  
  cat("\n🎉 SUCCESS! Walking isochrones map created in R\n")
  
  return(TRUE)
}

# Execute the main function
tryCatch({
  result <- create_walking_isochrones_map()
  if (!result) {
    cat("❌ Failed to create walking isochrones map\n")
  }
}, error = function(e) {
  cat("❌ Unexpected error:", e$message, "\n")
  cat("Traceback:\n")
  traceback()
})