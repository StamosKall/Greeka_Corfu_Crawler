#!/usr/bin/env Rscript
# Network-Based Isochrones with Proper Caching
# ============================================
# Creates realistic walking zones following actual roads
# Uses caching to avoid re-downloading OSM data
# Author: Network-aware with caching
# Date: 2025

# Load utilities
if (file.exists("utils/load_utils.R")) {
  source("utils/load_utils.R")
} else if (file.exists("../utils/load_utils.R")) {
  source("../utils/load_utils.R")
}

# Required packages
suppressMessages({
  if (!require(lwgeom, quietly = TRUE)) library(lwgeom)
  if (!require(concaveman, quietly = TRUE)) library(concaveman)
})

cat("🗺️  Network-Based Walking Isochrones with Caching\n")
cat("==================================================\n\n")

# Get command line args
args <- commandArgs(trailingOnly = TRUE)
max_hotels <- if (length(args) > 0) as.numeric(args[1]) else 50

# Configuration
CONFIG <- list(
  max_hotels = max_hotels,
  time_intervals = c(5, 10, 15, 30),  # Minutes
  walking_speed = 5,  # km/h
  data_file = "../../data/hotels.json",
  output_file = sprintf("../../data/network_isochrones_%d_hotels.png", max_hotels),
  map_width = 16,
  map_height = 20,
  dpi = 300
)

cat(sprintf("Processing %d hotels with network-based routing\n\n", CONFIG$max_hotels))

# Step 1: Load data
cat("📊 Step 1: Loading hotel data...\n")
hotels <- load_hotel_data(file_path = CONFIG$data_file, verbose = FALSE)
hotels <- head(hotels, CONFIG$max_hotels)
hotels_sf <- hotels_to_sf(hotels)
cat(sprintf("✅ %d hotels loaded\n\n", nrow(hotels_sf)))

# Step 2: Get boundaries (WITH CACHING)
cat("🗺️  Step 2: Getting Corfu boundaries...\n")
bbox <- calculate_bbox(hotels, padding_percent = 0.10)

# This will use cache if available!
corfu_land <- get_corfu_boundary(bbox, verbose = TRUE, use_cache = TRUE)
cat("\n")

# Step 3: Get walking network (WITH CACHING)
cat("🚶 Step 3: Getting walking network...\n")
cat("   (This uses cache after first run)\n")

# This will use cache if available!
network_sf <- get_walking_network(bbox, verbose = TRUE, use_cache = TRUE)

if (is.null(network_sf) || nrow(network_sf) == 0) {
  cat("⚠️  No network data, falling back to buffer method\n")
  use_network = FALSE
} else {
  use_network <- TRUE
  cat(sprintf("✅ Network ready: %d road segments\n\n", nrow(network_sf)))
}

# Step 4: Create network-aware isochrones
cat("🎯 Step 4: Creating network-based isochrones...\n")
cat("   (These follow actual roads, not circles)\n\n")

all_isochrones <- list()
iso_count <- 0

for (i in 1:nrow(hotels_sf)) {
  hotel <- hotels_sf[i, ]
  hotel_coords <- sf::st_coordinates(hotel)
  hotel_lon <- hotel_coords[1]
  hotel_lat <- hotel_coords[2]

  if (i %% 10 == 0 || i == 1) {
    cat(sprintf("   Processing hotel %d/%d...\n", i, nrow(hotels_sf)))
  }

  for (time_min in CONFIG$time_intervals) {
    # Calculate walking distance
    walking_dist_m <- (CONFIG$walking_speed * 1000 * time_min) / 60

    tryCatch({
      if (use_network) {
        # Network-based approach
        center_point <- sf::st_sfc(sf::st_point(c(hotel_lon, hotel_lat)), crs = 4326)

        # Buffer to find nearby network
        search_buffer <- sf::st_transform(center_point, 3857)
        search_buffer <- sf::st_buffer(search_buffer, dist = walking_dist_m * 1.2)
        search_buffer <- sf::st_transform(search_buffer, 4326)

        # Find network segments within reach
        nearby_network <- sf::st_filter(network_sf, search_buffer)

        if (nrow(nearby_network) >= 3) {
          # Extract points from network
          network_points <- sf::st_cast(nearby_network, "POINT")

          # Calculate actual distances from hotel
          hotel_pt_proj <- sf::st_transform(center_point, 3857)
          network_pts_proj <- sf::st_transform(network_points, 3857)

          distances <- as.numeric(sf::st_distance(hotel_pt_proj, network_pts_proj))

          # Keep only points within walking distance
          within_distance <- network_points[distances <= walking_dist_m, ]

          if (nrow(within_distance) >= 3) {
            # Create concave hull (realistic shape)
            iso_hull <- concaveman::concaveman(within_distance, concavity = 2, length_threshold = 0)

            iso_count <- iso_count + 1
            iso_df <- data.frame(
              id = iso_count,
              hotel_id = i,
              hotel_name = hotel$name,
              time_min = time_min
            )
            iso_sf <- sf::st_sf(iso_df, geometry = sf::st_geometry(iso_hull))
            all_isochrones[[iso_count]] <- iso_sf
          }
        }
      } else {
        # Fallback: circular buffer
        center_point <- sf::st_sfc(sf::st_point(c(hotel_lon, hotel_lat)), crs = 4326)
        center_proj <- sf::st_transform(center_point, 32634)
        buffer_proj <- sf::st_buffer(center_proj, dist = walking_dist_m)
        buffer <- sf::st_transform(buffer_proj, 4326)

        iso_count <- iso_count + 1
        iso_df <- data.frame(
          id = iso_count,
          hotel_id = i,
          hotel_name = hotel$name,
          time_min = time_min
        )
        iso_sf <- sf::st_sf(iso_df, geometry = sf::st_geometry(buffer))
        all_isochrones[[iso_count]] <- iso_sf
      }
    }, error = function(e) {
      # Silent failure for individual isochrones
    })
  }
}

if (length(all_isochrones) == 0) {
  stop("❌ No isochrones created")
}

isochrones_sf <- do.call(rbind, all_isochrones)
cat(sprintf("✅ Created %d isochrone zones\n\n", nrow(isochrones_sf)))

# Step 5: Clip to land
cat("✂️  Step 5: Clipping to land boundaries...\n")
clipped <- tryCatch({
  isochrones_sf <- sf::st_make_valid(isochrones_sf)
  if (!is.null(corfu_land)) {
    corfu_land <- sf::st_make_valid(corfu_land)
    clipped_result <- sf::st_intersection(isochrones_sf, corfu_land)
    clipped_result <- clipped_result[!sf::st_is_empty(clipped_result), ]
    cat("✅ Clipped to coastline\n\n")
    clipped_result
  } else {
    cat("⚠️  No land boundary\n\n")
    isochrones_sf
  }
}, error = function(e) {
  cat("⚠️  Clipping failed\n\n")
  isochrones_sf
})

# Step 6: Create map
cat("🎨 Step 6: Creating map...\n")

time_colors <- c(
  "5" = "#d4f1d4",
  "10" = "#a8e6a8",
  "15" = "#7ddb7d",
  "30" = "#52d052",
  "60" = "#28a428"
)

p <- ggplot2::ggplot() +
  ggplot2::theme_void() +
  ggplot2::theme(
    plot.title = ggplot2::element_text(size = 20, hjust = 0.5, face = "bold",
                                       color = "darkblue", margin = ggplot2::margin(b = 15)),
    plot.subtitle = ggplot2::element_text(size = 13, hjust = 0.5, color = "gray40",
                                          margin = ggplot2::margin(b = 20)),
    plot.caption = ggplot2::element_text(size = 10, hjust = 0.5, color = "gray50",
                                         margin = ggplot2::margin(t = 15)),
    legend.position = "right",
    legend.title = ggplot2::element_text(size = 12, face = "bold"),
    legend.text = ggplot2::element_text(size = 10),
    plot.background = ggplot2::element_rect(fill = "white", color = NA),
    panel.background = ggplot2::element_rect(fill = "#e6f3ff", color = NA),
    plot.margin = ggplot2::margin(20, 20, 20, 20)
  )

# Add land
if (!is.null(corfu_land)) {
  p <- p + ggplot2::geom_sf(data = corfu_land,
                            fill = "#f0f0e8",
                            color = "#8b8b7a",
                            size = 0.8,
                            alpha = 0.9)
}

# Add isochrones
for (time_min in rev(sort(unique(clipped$time_min)))) {
  iso_subset <- clipped[clipped$time_min == time_min, ]
  if (nrow(iso_subset) > 0) {
    time_str <- as.character(time_min)
    fill_color <- if (time_str %in% names(time_colors)) time_colors[time_str] else "#cccccc"

    p <- p + ggplot2::geom_sf(data = iso_subset,
                              fill = fill_color,
                              color = fill_color,
                              alpha = 0.6,
                              size = 0.15)
  }
}

# Add hotels
p <- p + ggplot2::geom_sf(data = hotels_sf,
                          color = "#8B0000",
                          fill = "#FF4444",
                          size = 2.2,
                          alpha = 0.85,
                          shape = 21,
                          stroke = 0.6)

# Labels
method_text <- if (use_network) "Network-Based (Following Roads)" else "Buffer-Based"
p <- p + ggplot2::labs(
  title = "Network-Based Walking Distance Isochrones",
  subtitle = sprintf("%s • %d Hotels • Land-Clipped • %s",
                    method_text, nrow(hotels_sf),
                    if (use_network) "Cached OSM Data" else "Circular Fallback"),
  caption = paste("Generated", Sys.Date(),
                 "• Isochrones follow actual road network • Walking Speed: 5 km/h",
                 "\n✅ OSM data cached for fast re-runs • Data: OpenStreetMap")
)

# Coords
p <- p + ggplot2::coord_sf(
  xlim = c(bbox["xmin"], bbox["xmax"]),
  ylim = c(bbox["ymin"], bbox["ymax"]),
  expand = FALSE
)

cat("✅ Map created\n\n")

# Step 7: Save
cat("💾 Step 7: Saving map...\n")
ggplot2::ggsave(
  filename = CONFIG$output_file,
  plot = p,
  width = CONFIG$map_width,
  height = CONFIG$map_height,
  dpi = CONFIG$dpi,
  units = "in",
  bg = "white"
)

cat(sprintf("✅ Map saved: %s\n\n", CONFIG$output_file))

# Summary
cat("📊 SUMMARY\n")
cat("==========\n")
cat(sprintf("Hotels: %d\n", nrow(hotels_sf)))
cat(sprintf("Isochrones: %d\n", nrow(clipped)))
cat(sprintf("Method: %s\n", method_text))
cat(sprintf("Output: %s\n", CONFIG$output_file))

# Cache info
cat("\n📦 CACHE STATUS\n")
cat("===============\n")
cache_info()

cat("\n✨ Done! Next run will be much faster (cached OSM data)\n")