# Simplified Walking Isochrones Map using Shared Utilities
# =========================================================
# Example of refactored code using the new utility modules
# Author: Refactored version
# Date: 2025

# Load shared utilities
source("../utils/load_utils.R")

# Configuration (can override defaults)
CONFIG <- list(
  max_hotels = 30,  # Process first 30 hotels for demo
  walking_speed = WALKING_SPEED_KMH,
  time_intervals = c(5, 10, 15, 30),
  output_file = "walking_isochrones_refactored.png",
  color_style = "gradient",
  map_width = 14,
  map_height = 10,
  dpi = 300
)

# Main function using utilities
create_walking_map <- function(config = CONFIG) {
  cat("🏝️  Creating Walking Isochrones Map (Refactored Version)\n")
  cat("=========================================================\n")

  # Step 1: Load hotel data using utility
  hotels_data <- load_hotel_data(verbose = TRUE)

  # Limit hotels if specified
  if (!is.null(config$max_hotels) && config$max_hotels < nrow(hotels_data)) {
    hotels_data <- head(hotels_data, config$max_hotels)
    cat(sprintf("📍 Limited to first %d hotels\n", config$max_hotels))
  }

  # Step 2: Convert to spatial object
  hotels_sf <- hotels_to_sf(hotels_data)

  # Step 3: Get map boundary
  bbox <- calculate_bbox(hotels_data, padding_percent = 0.1)
  corfu_boundary <- get_corfu_boundary(bbox, verbose = TRUE)

  # Step 4: Get walking network (optional)
  walking_network <- get_walking_network(bbox, verbose = TRUE)

  # Step 5: Create isochrones using utility
  isochrones <- create_hotel_isochrones(
    hotels_sf,
    time_intervals = config$time_intervals,
    network_sf = walking_network,
    method = if (!is.null(walking_network)) "network" else "circular",
    walking_speed = config$walking_speed,
    verbose = TRUE
  )

  if (is.null(isochrones)) {
    cat("❌ Failed to create isochrones\n")
    return(FALSE)
  }

  # Step 6: Create map using styling utilities
  map_plot <- create_isochrone_map(
    hotels_sf = hotels_sf,
    isochrones_sf = isochrones,
    corfu_boundary = corfu_boundary,
    title = "Walking Distance Isochrones - Corfu Hotels",
    subtitle = sprintf("%d Hotels • %d Time Zones • Refactored Version",
                      nrow(hotels_sf), length(config$time_intervals)),
    color_style = config$color_style
  )

  # Step 7: Add legend
  map_plot <- add_walking_legend(map_plot, config$time_intervals, config$color_style)

  # Step 8: Save map
  save_map(
    plot = map_plot,
    filename = config$output_file,
    width = config$map_width,
    height = config$map_height,
    dpi = config$dpi
  )

  # Print summary
  cat("\n📊 SUMMARY\n")
  cat("===========\n")
  stats <- get_hotel_stats(hotels_data, verbose = FALSE)
  cat(sprintf("Total hotels processed: %d\n", stats$total))
  cat(sprintf("Total isochrone zones: %d\n", nrow(isochrones)))
  cat(sprintf("Average zones per hotel: %.1f\n",
              nrow(isochrones) / nrow(hotels_sf)))

  cat("\n✅ Map creation completed successfully!\n")
  return(TRUE)
}

# Execute if run directly
if (!interactive()) {
  tryCatch({
    success <- create_walking_map(CONFIG)
    if (!success) {
      cat("❌ Map creation failed\n")
      quit(status = 1)
    }
  }, error = function(e) {
    cat("❌ Error:", e$message, "\n")
    quit(status = 1)
  })
} else {
  cat("\n📌 Run create_walking_map() to generate the map\n")
  cat("   Customize CONFIG list to change parameters\n\n")
}