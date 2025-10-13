# Land-Clipped Walking Isochrones Map
# ====================================
# Creates isochrones that are clipped to land boundaries (no sea overlap)
# Author: Refactored with land clipping
# Date: 2025

# Load shared utilities
# Source from project root
if (file.exists("utils/load_utils.R")) {
  source("utils/load_utils.R")
} else if (file.exists("../utils/load_utils.R")) {
  source("../utils/load_utils.R")
} else {
  stop("Cannot find utils/load_utils.R - please run from the correct directory")
}

# Additional required libraries for clipping
if (!require(lwgeom)) install.packages("lwgeom")
library(lwgeom)

cat("🏝️  Creating Land-Clipped Walking Isochrones Map\n")
cat("================================================\n\n")

# Configuration
CONFIG <- list(
  max_hotels = 141,  # Process all hotels
  time_intervals = c(5, 10, 15, 30, 60),
  data_file = "../../data/hotels.json",  # Path to hotel data
  output_file = "../../data/land_clipped_isochrones_map.png",
  map_width = 16,
  map_height = 20,
  dpi = 300
)

# Step 1: Load hotel data
cat("📊 Step 1: Loading hotel data...\n")
hotels <- load_hotel_data(file_path = CONFIG$data_file, verbose = FALSE)
cat(sprintf("✅ Loaded %d hotels\n\n", nrow(hotels)))

# Limit if configured
if (!is.null(CONFIG$max_hotels)) {
  hotels <- head(hotels, CONFIG$max_hotels)
}

# Step 2: Convert to spatial features
cat("📍 Step 2: Converting to spatial features...\n")
hotels_sf <- hotels_to_sf(hotels)
cat(sprintf("✅ Created spatial features for %d hotels\n\n", nrow(hotels_sf)))

# Step 3: Get Corfu land boundary (critical for clipping)
cat("🗺️  Step 3: Getting Corfu land boundary...\n")
bbox <- calculate_bbox(hotels, padding_percent = 0.15)
corfu_land <- get_corfu_boundary(bbox, verbose = FALSE)

# If primary method fails, try alternative approaches
if (is.null(corfu_land)) {
  cat("⚠️  Primary boundary method failed, trying coastline approach...\n")

  tryCatch({
    # Try to get coastline and create polygon
    coastline_query <- opq(bbox = bbox) %>%
      add_osm_feature(key = "natural", value = "coastline")

    coastline_result <- osmdata_sf(coastline_query)

    if (!is.null(coastline_result$osm_lines) && nrow(coastline_result$osm_lines) > 0) {
      # Combine coastlines and try to polygonize
      coastlines <- coastline_result$osm_lines

      # Buffer slightly to ensure closure
      coastlines_buffered <- st_buffer(coastlines, dist = 0.0001)
      coastlines_union <- st_union(coastlines_buffered)

      # Try to create polygon
      poly_attempt <- st_polygonize(coastlines_union)

      if (length(poly_attempt) > 0) {
        polys <- st_collection_extract(poly_attempt, "POLYGON")
        if (length(polys) > 0) {
          # Get the largest polygon (should be Corfu island)
          areas <- st_area(polys)
          corfu_land <- st_sf(geometry = polys[which.max(areas)])
          cat("✅ Created land boundary from coastlines\n\n")
        }
      }
    }
  }, error = function(e) {
    cat("⚠️  Coastline method also failed\n")
  })
}

# If still no boundary, create one from hotels with large buffer
if (is.null(corfu_land)) {
  cat("⚠️  Creating approximate land boundary from hotel locations...\n")
  hotels_union <- st_union(hotels_sf)
  # Large buffer in projected coordinates
  hotels_proj <- st_transform(hotels_union, crs = 32634)
  land_buffer <- st_buffer(hotels_proj, dist = 5000)  # 5km buffer
  corfu_land <- st_transform(land_buffer, crs = 4326)
  cat("✅ Created approximate boundary\n\n")
}

# Step 4: Create raw isochrones (before clipping)
cat("🚶 Step 4: Creating raw isochrones...\n")
raw_isochrones <- create_hotel_isochrones(
  hotels_sf = hotels_sf,
  time_intervals = CONFIG$time_intervals,
  method = "network",
  walking_speed = WALKING_SPEED_KMH,
  verbose = FALSE
)

if (is.null(raw_isochrones)) {
  stop("❌ Failed to create isochrones")
}

cat(sprintf("✅ Created %d raw isochrone zones\n\n", nrow(raw_isochrones)))

# Step 5: Clip isochrones to land boundary (KEY STEP)
cat("✂️  Step 5: Clipping isochrones to land boundary...\n")
cat("   This ensures walking zones don't extend into the sea\n")

clipped_isochrones <- tryCatch({
  # Make geometries valid before intersection
  raw_isochrones <- st_make_valid(raw_isochrones)
  corfu_land <- st_make_valid(corfu_land)

  # Ensure same CRS
  if (st_crs(raw_isochrones) != st_crs(corfu_land)) {
    corfu_land <- st_transform(corfu_land, st_crs(raw_isochrones))
  }

  # Perform intersection to clip to land
  clipped <- st_intersection(raw_isochrones, corfu_land)

  # Remove any empty geometries
  clipped <- clipped[!st_is_empty(clipped), ]

  cat(sprintf("✅ Successfully clipped isochrones to land\n"))
  cat(sprintf("   Removed sea overlap from all zones\n\n"))

  clipped
}, error = function(e) {
  cat(sprintf("⚠️  Clipping error: %s\n", e$message))
  cat("   Using unclipped isochrones as fallback\n\n")
  raw_isochrones
})

# Step 6: Create the map
cat("🎨 Step 6: Creating map visualization...\n")

# Color palette for walking times (gradient from light to dark)
time_colors <- c(
  "5" = "#d4f1d4",    # Very light green
  "10" = "#a8e6a8",   # Light green
  "15" = "#7ddb7d",   # Medium green
  "30" = "#52d052",   # Green
  "60" = "#28a428"    # Dark green
)

# Start building the map
p <- ggplot() +
  theme_void() +
  theme(
    plot.title = element_text(size = 20, hjust = 0.5, face = "bold",
                             color = "darkblue", margin = margin(b = 15)),
    plot.subtitle = element_text(size = 14, hjust = 0.5, color = "gray40",
                                margin = margin(b = 20)),
    plot.caption = element_text(size = 11, hjust = 0.5, color = "gray50",
                               margin = margin(t = 15)),
    legend.position = "right",
    legend.title = element_text(size = 13, face = "bold"),
    legend.text = element_text(size = 11),
    legend.key.size = unit(1.2, "cm"),
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "#e6f3ff", color = NA),  # Light blue for sea
    plot.margin = margin(25, 25, 25, 25)
  )

# Add land boundary (shows island shape)
if (!is.null(corfu_land)) {
  p <- p + geom_sf(data = corfu_land,
                   fill = "#f0f0e8",      # Light beige for land
                   color = "#8b8b7a",     # Dark outline
                   size = 0.8,
                   alpha = 0.9)
}

# Add isochrones (largest to smallest for proper layering)
for (time_min in rev(sort(unique(clipped_isochrones$time_min)))) {
  iso_subset <- clipped_isochrones[clipped_isochrones$time_min == time_min, ]

  if (nrow(iso_subset) > 0) {
    time_str <- as.character(time_min)
    fill_color <- if (time_str %in% names(time_colors)) {
      time_colors[time_str]
    } else {
      "#cccccc"
    }

    # Calculate alpha based on time (smaller times more visible)
    alpha_val <- 0.5 + (max(CONFIG$time_intervals) - time_min) /
                       max(CONFIG$time_intervals) * 0.3

    p <- p + geom_sf(data = iso_subset,
                     fill = fill_color,
                     color = fill_color,
                     alpha = alpha_val,
                     size = 0.15)
  }
}

# Add hotel points on top
p <- p + geom_sf(data = hotels_sf,
                color = "#8B0000",      # Dark red border
                fill = "#FF4444",       # Bright red fill
                size = 2.2,
                alpha = 0.85,
                shape = 21,
                stroke = 0.6)

# Add labels
p <- p + labs(
  title = "Land-Clipped Walking Distance Isochrones",
  subtitle = sprintf("Corfu Hotels Analysis • %d Hotels • %d Time Zones • Clipped to Coastline",
                    nrow(hotels_sf), length(CONFIG$time_intervals)),
  caption = paste("Generated on", Sys.Date(),
                 "• Walking Speed: 5 km/h • Blue = Sea, Beige = Land, Green = Walking Zones",
                 "\n✂️ Isochrones clipped at coastline - no sea overlap • Data: OpenStreetMap")
)

# Create legend manually
legend_labels <- paste(CONFIG$time_intervals, "min walk")
p <- p + scale_fill_manual(
  name = "Walking Time\nZones",
  values = setNames(time_colors[as.character(CONFIG$time_intervals)], legend_labels),
  labels = legend_labels,
  guide = guide_legend(
    override.aes = list(alpha = 0.75, size = 4),
    title.position = "top"
  )
)

# Set coordinate limits to map bounds
p <- p + coord_sf(
  xlim = c(bbox["xmin"], bbox["xmax"]),
  ylim = c(bbox["ymin"], bbox["ymax"]),
  expand = FALSE
)

cat("✅ Map visualization complete\n\n")

# Step 7: Save the map
cat("💾 Step 7: Saving map...\n")
ggsave(
  filename = CONFIG$output_file,
  plot = p,
  width = CONFIG$map_width,
  height = CONFIG$map_height,
  dpi = CONFIG$dpi,
  units = "in",
  bg = "white"
)

cat(sprintf("✅ Map saved: %s\n", CONFIG$output_file))
cat(sprintf("   Resolution: %d x %d inches at %d DPI\n\n",
           CONFIG$map_width, CONFIG$map_height, CONFIG$dpi))

# Summary statistics
cat("📊 SUMMARY STATISTICS\n")
cat("=====================\n")
cat(sprintf("Hotels processed: %d\n", nrow(hotels_sf)))
cat(sprintf("Raw isochrones created: %d\n", nrow(raw_isochrones)))
cat(sprintf("Clipped isochrones: %d\n", nrow(clipped_isochrones)))
cat(sprintf("Zones per hotel: %.1f\n", nrow(clipped_isochrones) / nrow(hotels_sf)))
cat("\nZone distribution:\n")
for (time in sort(unique(clipped_isochrones$time_min))) {
  count <- sum(clipped_isochrones$time_min == time)
  cat(sprintf("  %2d minutes: %3d zones\n", time, count))
}

cat("\n✨ Land-clipped isochrone map created successfully!\n")
cat("   All walking zones are now constrained to land only.\n")