# Network-Based Walking Isochrones with Land Clipping
# ====================================================
# Creates realistic isochrones based on actual walking network
# Uses road network routing instead of circular buffers
# Author: Network-aware isochrones
# Date: 2025

# Load shared utilities
if (file.exists("utils/load_utils.R")) {
  source("utils/load_utils.R")
} else if (file.exists("../utils/load_utils.R")) {
  source("../utils/load_utils.R")
}

# Additional required libraries
if (!require(lwgeom)) install.packages("lwgeom")
if (!require(dodgr)) install.packages("dodgr")
if (!require(concaveman)) install.packages("concaveman")

library(lwgeom)
library(dodgr)
library(concaveman)

cat("🏝️  Creating Network-Based Walking Isochrones (Realistic Polygons)\n")
cat("==================================================================\n\n")

# Configuration
CONFIG <- list(
  max_hotels = 30,  # Start with 30 for faster processing
  time_intervals = c(5, 10, 15, 30),
  walking_speed_kmh = 5,
  data_file = "../../data/hotels.json",
  output_file = "../../data/network_isochrones_map.png",
  map_width = 16,
  map_height = 20,
  dpi = 300
)

# Step 1: Load hotel data
cat("📊 Step 1: Loading hotel data...\n")
hotels <- load_hotel_data(file_path = CONFIG$data_file, verbose = FALSE)
hotels <- head(hotels, CONFIG$max_hotels)
cat(sprintf("✅ Processing %d hotels\n\n", nrow(hotels)))

# Step 2: Convert to spatial features
cat("📍 Step 2: Converting to spatial features...\n")
hotels_sf <- hotels_to_sf(hotels)
cat("✅ Created spatial features\n\n")

# Step 3: Get Corfu land boundary
cat("🗺️  Step 3: Getting Corfu land boundary...\n")
bbox <- calculate_bbox(hotels, padding_percent = 0.15)
corfu_land <- get_corfu_boundary(bbox, verbose = FALSE)
cat("✅ Land boundary obtained\n\n")

# Step 4: Download walking network
cat("🚶 Step 4: Downloading detailed walking network...\n")
cat("   This will take a few moments...\n")

network_sf <- get_walking_network(bbox, verbose = FALSE)

if (is.null(network_sf) || nrow(network_sf) == 0) {
  stop("❌ Failed to download walking network")
}

cat(sprintf("✅ Downloaded %d network segments\n\n", nrow(network_sf)))

# Step 5: Create network graph for routing
cat("🔗 Step 5: Building routing graph from network...\n")

# Convert network to dodgr format
tryCatch({
  # Extract coordinates and create graph
  graph <- dodgr::weight_streetnet(network_sf, wt_profile = "foot")

  if (is.null(graph) || nrow(graph) == 0) {
    stop("Graph creation failed")
  }

  cat(sprintf("✅ Created routing graph with %d edges\n\n", nrow(graph)))
}, error = function(e) {
  cat(sprintf("❌ Error creating graph: %s\n", e$message))
  cat("   Falling back to network-aware buffer method\n\n")
  graph <- NULL
})

# Step 6: Create network-based isochrones
cat("🎯 Step 6: Creating network-based isochrones...\n")
cat("   This creates realistic walking zones along roads\n")

all_isochrones <- list()
isochrone_count <- 0

for (i in 1:nrow(hotels_sf)) {
  hotel <- hotels_sf[i, ]
  hotel_coords <- sf::st_coordinates(hotel)
  hotel_lon <- hotel_coords[1]
  hotel_lat <- hotel_coords[2]

  if (i %% 5 == 0 || i == 1) {
    cat(sprintf("   Processing hotel %d/%d...\n", i, nrow(hotels_sf)))
  }

  for (time_min in CONFIG$time_intervals) {
    # Calculate walking distance in meters
    walking_distance_m <- (CONFIG$walking_speed_kmh * 1000 * time_min) / 60

    tryCatch({
      if (!is.null(graph)) {
        # Method 1: Use dodgr for network routing
        center_point <- c(hotel_lon, hotel_lat)

        # Calculate isochrone using dodgr
        iso_points <- dodgr::dodgr_isochrones(
          graph,
          from = center_point,
          tlim = time_min * 60  # Convert to seconds
        )

        if (!is.null(iso_points) && nrow(iso_points) > 3) {
          # Create concave hull (realistic shape)
          iso_sf <- sf::st_as_sf(iso_points, coords = c("lon", "lat"), crs = 4326)
          iso_hull <- concaveman::concaveman(iso_sf, concavity = 2)

          isochrone_count <- isochrone_count + 1
          iso_df <- data.frame(
            id = isochrone_count,
            hotel_id = i,
            hotel_name = hotel$name,
            time_min = time_min,
            geometry = sf::st_geometry(iso_hull)
          )
          all_isochrones[[isochrone_count]] <- sf::st_sf(iso_df)
        }
      } else {
        # Method 2: Network-aware buffer (fallback)
        center_point <- sf::st_sfc(sf::st_point(c(hotel_lon, hotel_lat)), crs = 4326)

        # Find network segments within walking distance
        center_buffer <- sf::st_buffer(
          sf::st_transform(center_point, 3857),
          dist = walking_distance_m * 1.5  # Slightly larger for network
        )
        center_buffer_wgs84 <- sf::st_transform(center_buffer, 4326)

        nearby_segments <- sf::st_filter(network_sf, center_buffer_wgs84)

        if (nrow(nearby_segments) > 0) {
          # Extract points from network segments
          segment_points <- sf::st_cast(nearby_segments, "POINT")

          if (nrow(segment_points) >= 3) {
            # Create concave hull around network points
            iso_hull <- concaveman::concaveman(segment_points, concavity = 2)

            isochrone_count <- isochrone_count + 1
            iso_df <- data.frame(
              id = isochrone_count,
              hotel_id = i,
              hotel_name = hotel$name,
              time_min = time_min,
              geometry = sf::st_geometry(iso_hull)
            )
            all_isochrones[[isochrone_count]] <- sf::st_sf(iso_df)
          }
        }
      }
    }, error = function(e) {
      # Silent failure for individual isochrones
    })
  }
}

if (length(all_isochrones) == 0) {
  stop("❌ No isochrones created")
}

# Combine all isochrones
isochrones_sf <- do.call(rbind, all_isochrones)
cat(sprintf("✅ Created %d network-based isochrone zones\n\n", nrow(isochrones_sf)))

# Step 7: Clip to land boundary
cat("✂️  Step 7: Clipping isochrones to land...\n")

clipped_isochrones <- tryCatch({
  isochrones_sf <- sf::st_make_valid(isochrones_sf)

  if (!is.null(corfu_land)) {
    corfu_land <- sf::st_make_valid(corfu_land)
    clipped <- sf::st_intersection(isochrones_sf, corfu_land)
    clipped <- clipped[!sf::st_is_empty(clipped), ]
    cat("✅ Clipped to land boundary\n\n")
    clipped
  } else {
    cat("⚠️  No land boundary, using unclipped\n\n")
    isochrones_sf
  }
}, error = function(e) {
  cat("⚠️  Clipping failed, using unclipped\n\n")
  isochrones_sf
})

# Step 8: Create map
cat("🎨 Step 8: Creating map...\n")

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
    plot.subtitle = ggplot2::element_text(size = 14, hjust = 0.5, color = "gray40",
                                          margin = ggplot2::margin(b = 20)),
    plot.caption = ggplot2::element_text(size = 11, hjust = 0.5, color = "gray50",
                                         margin = ggplot2::margin(t = 15)),
    legend.position = "right",
    legend.title = ggplot2::element_text(size = 13, face = "bold"),
    legend.text = ggplot2::element_text(size = 11),
    legend.key.size = ggplot2::unit(1.2, "cm"),
    plot.background = ggplot2::element_rect(fill = "white", color = NA),
    panel.background = ggplot2::element_rect(fill = "#e6f3ff", color = NA),
    plot.margin = ggplot2::margin(25, 25, 25, 25)
  )

# Add land
if (!is.null(corfu_land)) {
  p <- p + ggplot2::geom_sf(data = corfu_land,
                            fill = "#f0f0e8",
                            color = "#8b8b7a",
                            size = 0.8,
                            alpha = 0.9)
}

# Add isochrones (largest to smallest)
for (time_min in rev(sort(unique(clipped_isochrones$time_min)))) {
  iso_subset <- clipped_isochrones[clipped_isochrones$time_min == time_min, ]

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

# Add hotel points
p <- p + ggplot2::geom_sf(data = hotels_sf,
                          color = "#8B0000",
                          fill = "#FF4444",
                          size = 2.2,
                          alpha = 0.85,
                          shape = 21,
                          stroke = 0.6)

# Labels
p <- p + ggplot2::labs(
  title = "Network-Based Walking Distance Isochrones",
  subtitle = sprintf("Realistic Walking Zones Along Roads • %d Hotels • Land-Clipped",
                    nrow(hotels_sf)),
  caption = paste("Generated on", Sys.Date(),
                 "• Isochrones follow actual road network (not circular)",
                 "\n✂️ Clipped to coastline • Data: OpenStreetMap")
)

# Coordinate limits
p <- p + ggplot2::coord_sf(
  xlim = c(bbox["xmin"], bbox["xmax"]),
  ylim = c(bbox["ymin"], bbox["ymax"]),
  expand = FALSE
)

cat("✅ Map created\n\n")

# Step 9: Save
cat("💾 Step 9: Saving map...\n")
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
cat(sprintf("Network segments: %d\n", nrow(network_sf)))
cat(sprintf("Isochrones: %d\n", nrow(clipped_isochrones)))
cat(sprintf("Method: %s\n", if (!is.null(graph)) "dodgr routing" else "network-aware buffer"))
cat("\n✨ Network-based isochrone map complete!\n")
cat("   Polygons follow actual walking paths, not circular buffers.\n")