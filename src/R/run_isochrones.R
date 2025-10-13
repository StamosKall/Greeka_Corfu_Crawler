#!/usr/bin/env Rscript
# Simple Runner Script for Isochrone Maps
# ========================================
# Usage: Rscript run_isochrones.R [num_hotels]
# Example: Rscript run_isochrones.R 50

# Get command line arguments
args <- commandArgs(trailingOnly = TRUE)
max_hotels <- if (length(args) > 0) as.numeric(args[1]) else 141

cat("🗺️  Corfu Hotels Isochrone Map Generator\n")
cat("========================================\n\n")
cat(sprintf("Processing %d hotels...\n\n", max_hotels))

# Load utilities
source("utils/load_utils.R")

# Additional packages
if (!require(lwgeom)) {
  renv::install("lwgeom", prompt = FALSE)
  library(lwgeom)
}

# Configuration
CONFIG <- list(
  max_hotels = max_hotels,
  time_intervals = c(5, 10, 15, 30, 60),
  data_file = "../../data/hotels.json",
  output_file = sprintf("../../data/isochrones_%d_hotels.png", max_hotels),
  map_width = 16,
  map_height = 20,
  dpi = 300
)

# Step 1: Load data
cat("📊 Step 1: Loading hotel data...\n")
hotels <- load_hotel_data(file_path = CONFIG$data_file, verbose = FALSE)
hotels <- head(hotels, CONFIG$max_hotels)
hotels_sf <- hotels_to_sf(hotels)
cat(sprintf("✅ Loaded %d hotels\n\n", nrow(hotels_sf)))

# Step 2: Get geographic data
cat("🗺️  Step 2: Getting Corfu boundaries and network...\n")
bbox <- calculate_bbox(hotels, padding_percent = 0.15)

# Use caching for faster subsequent runs
corfu_land <- get_corfu_boundary(bbox, verbose = TRUE, use_cache = TRUE)
cat("\n")

# Step 3: Create isochrones
cat("🚶 Step 3: Creating walking isochrones...\n")
isochrones <- create_hotel_isochrones(
  hotels_sf = hotels_sf,
  time_intervals = CONFIG$time_intervals,
  method = "circular",
  verbose = FALSE
)
cat(sprintf("✅ Created %d isochrone zones\n\n", nrow(isochrones)))

# Step 4: Clip to land
cat("✂️  Step 4: Clipping to land boundaries...\n")
clipped_isochrones <- tryCatch({
  isochrones <- sf::st_make_valid(isochrones)
  if (!is.null(corfu_land)) {
    corfu_land <- sf::st_make_valid(corfu_land)
    clipped <- sf::st_intersection(isochrones, corfu_land)
    clipped <- clipped[!sf::st_is_empty(clipped), ]
    cat("✅ Clipped to coastline\n\n")
    clipped
  } else {
    cat("⚠️  No land boundary, using unclipped\n\n")
    isochrones
  }
}, error = function(e) {
  cat("⚠️  Clipping failed, using unclipped\n\n")
  isochrones
})

# Step 5: Create map
cat("🎨 Step 5: Creating map...\n")

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

# Add isochrones
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

# Add hotels
p <- p + ggplot2::geom_sf(data = hotels_sf,
                          color = "#8B0000",
                          fill = "#FF4444",
                          size = 2.2,
                          alpha = 0.85,
                          shape = 21,
                          stroke = 0.6)

# Labels
p <- p + ggplot2::labs(
  title = "Land-Clipped Walking Distance Isochrones",
  subtitle = sprintf("Corfu Hotels • %d Hotels • Land-Clipped to Coastline",
                    nrow(hotels_sf)),
  caption = paste("Generated on", Sys.Date(),
                 "• Walking Speed: 5 km/h • Clipped at coastline • Data: OpenStreetMap")
)

# Coordinate limits
p <- p + ggplot2::coord_sf(
  xlim = c(bbox["xmin"], bbox["xmax"]),
  ylim = c(bbox["ymin"], bbox["ymax"]),
  expand = FALSE
)

cat("✅ Map created\n\n")

# Step 6: Save
cat("💾 Step 6: Saving map...\n")
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
cat(sprintf("Isochrones: %d\n", nrow(clipped_isochrones)))
cat(sprintf("Output: %s\n", CONFIG$output_file))
cat(sprintf("Resolution: %d x %d inches @ %d DPI\n",
           CONFIG$map_width, CONFIG$map_height, CONFIG$dpi))

# Check cache
if (exists("cache_info")) {
  cat("\n📦 Cache Status:\n")
  cache_info()
}

cat("\n✨ Done!\n")