# Final Polished Corfu Walking Isochrones Map
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

cat("🏝️  Final Polished Corfu Walking Isochrones Map\n")
cat("===============================================\n")

# Configuration
MAX_HOTELS <- 141  # Process ALL hotels
WALKING_SPEED_KMH <- 5  # km/h
TIME_INTERVALS <- c(5, 10, 15, 20, 30, 45, 60)  # minutes
OUTPUT_FILE <- "corfu_final_walking_isochrones.png"
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
cat("🗺️  Getting Corfu island shape...\n")
corfu_boundary <- NULL

# Try to get coastline and create the island shape
tryCatch({
  coastline_query <- opq(bbox = bbox) %>%
    add_osm_feature(key = "natural", value = "coastline")
  
  coastline_result <- osmdata_sf(coastline_query)
  
  if (!is.null(coastline_result$osm_lines) && nrow(coastline_result$osm_lines) > 0) {
    coastlines <- coastline_result$osm_lines
    coastlines_combined <- st_union(coastlines)
    coastlines_poly <- st_polygonize(coastlines_combined)
    
    if (length(coastlines_poly) > 0) {
      polys <- st_collection_extract(coastlines_poly, "POLYGON")
      if (length(polys) > 0) {
        areas <- st_area(polys)
        largest_poly <- polys[which.max(areas)]
        corfu_boundary <- st_sf(name = "Corfu", geometry = largest_poly)
        cat("✅ Created Corfu island boundary from coastlines\n")
      }
    }
  }
}, error = function(e) {
  cat("⚠️  Could not create island boundary\n")
})

# Create isochrones using buffer method
cat("🚶 Creating walking isochrones...\n")

# Convert hotels to sf points
hotels_sf <- st_as_sf(hotels_to_process, 
                     coords = c("longitude", "latitude"), 
                     crs = 4326)

# Transform to projected coordinate system for accurate distance calculations
hotels_projected <- st_transform(hotels_sf, crs = 32634)

# Create isochrones as circular buffers
all_isochrones <- list()

for (i in 1:nrow(hotels_projected)) {
  hotel <- hotels_projected[i, ]
  
  for (time_min in TIME_INTERVALS) {
    walking_distance <- (WALKING_SPEED_KMH * 1000 * time_min) / 60
    buffer <- st_buffer(hotel, dist = walking_distance)
    
    buffer$time_min <- time_min
    buffer$hotel_name <- hotels_to_process$name[i]
    buffer$hotel_id <- i
    buffer$time_label <- paste(time_min, "min")
    
    all_isochrones[[paste(i, time_min, sep = "_")]] <- buffer
  }
  
  if (i %% 25 == 0) {
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

# Create the final polished map
cat("🎨 Creating final polished map...\n")

# Beautiful blue-green color palette like your reference
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

# Start building the plot
p <- ggplot()

# Add ocean/sea background
p <- p + 
  theme_void() +
  theme(
    panel.background = element_rect(fill = "#e6f3ff", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

# Add Corfu island boundary if available
if (!is.null(corfu_boundary)) {
  p <- p + 
    geom_sf(data = corfu_boundary, 
            fill = "#f0f0f0", 
            color = "#d0d0d0", 
            alpha = 0.8,
            size = 0.8)
  cat("✅ Added Corfu island background\n")
}

# Add isochrones in reverse order (largest first) for proper layering
for (time in rev(TIME_INTERVALS)) {
  time_data <- combined_isochrones_wgs84[combined_isochrones_wgs84$time_min == time, ]
  if (nrow(time_data) > 0) {
    # Calculate alpha based on time (further = more transparent)
    alpha_val <- 0.20 + (max(TIME_INTERVALS) - time) / max(TIME_INTERVALS) * 0.45
    
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
          color = "white",
          fill = "#d73027",
          size = 1.8,
          alpha = 0.95,
          shape = 21,
          stroke = 0.8)

# Apply final styling
p <- p +
  coord_sf(xlim = c(bbox[1], bbox[3]), 
           ylim = c(bbox[2], bbox[4]),
           expand = FALSE) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 24, face = "bold", 
                             color = "#08306b", margin = margin(b = 15)),
    plot.subtitle = element_text(hjust = 0.5, size = 16, color = "#2c7fb8", 
                                margin = margin(b = 30)),
    plot.caption = element_text(hjust = 0.5, size = 11, color = "gray50",
                               margin = margin(t = 20)),
    plot.margin = margin(30, 30, 30, 30),
    legend.position = "right",
    legend.title = element_text(size = 14, face = "bold", color = "#08306b"),
    legend.text = element_text(size = 12, color = "#2c7fb8"),
    legend.key.size = unit(1.2, "cm"),
    legend.margin = margin(0, 0, 0, 30),
    legend.background = element_rect(fill = "white", color = "#d0d0d0", size = 0.5),
    legend.key = element_rect(color = "white")
  ) +
  labs(
    title = "Walking Distance Analysis - Corfu Hotels",
    subtitle = sprintf("Complete Coverage: %d Hotels • %d Walking Time Zones • Speed: %d km/h", 
                      nrow(hotels_projected), length(TIME_INTERVALS), WALKING_SPEED_KMH),
    caption = sprintf("Generated %s • Red circles: Hotel locations • Blue gradients: Walking reach areas • Data: OpenStreetMap", 
                      format(Sys.Date(), "%B %d, %Y"))
  )

# Create manual legend
legend_df <- data.frame(
  time = TIME_INTERVALS,
  time_label = paste(TIME_INTERVALS, "minutes"),
  color = time_colors
)

# Add discrete legend
p <- p + 
  annotate("rect", 
           xmin = bbox[3] - (bbox[3] - bbox[1]) * 0.25, 
           xmax = bbox[3] - (bbox[3] - bbox[1]) * 0.02, 
           ymin = bbox[4] - (bbox[4] - bbox[2]) * 0.45, 
           ymax = bbox[4] - (bbox[4] - bbox[2]) * 0.05,
           fill = "white", color = "#d0d0d0", alpha = 0.9) +
  annotate("text", 
           x = bbox[3] - (bbox[3] - bbox[1]) * 0.135, 
           y = bbox[4] - (bbox[4] - bbox[2]) * 0.08,
           label = "Walking Time", 
           size = 5, fontface = "bold", color = "#08306b")

# Add legend items
for (i in 1:length(TIME_INTERVALS)) {
  y_pos <- bbox[4] - (bbox[4] - bbox[2]) * (0.12 + i * 0.04)
  
  p <- p + 
    annotate("rect",
             xmin = bbox[3] - (bbox[3] - bbox[1]) * 0.22,
             xmax = bbox[3] - (bbox[3] - bbox[1]) * 0.19,
             ymin = y_pos - (bbox[4] - bbox[2]) * 0.015,
             ymax = y_pos + (bbox[4] - bbox[2]) * 0.015,
             fill = time_colors[i], alpha = 0.8, color = "white") +
    annotate("text",
             x = bbox[3] - (bbox[3] - bbox[1]) * 0.16,
             y = y_pos,
             label = paste(TIME_INTERVALS[i], "min"),
             size = 4, color = "#2c7fb8", hjust = 0)
}

# Save the final map
cat(sprintf("💾 Saving final polished map as: %s\n", OUTPUT_FILE))
ggsave(OUTPUT_FILE, plot = p, 
       width = MAP_WIDTH, height = MAP_HEIGHT, 
       dpi = DPI, units = "in",
       bg = "white")

# Generate final summary report
cat("\n📊 FINAL SUMMARY REPORT\n")
cat("=======================\n")
cat(sprintf("Hotels processed: %d\n", nrow(hotels_projected)))
cat(sprintf("Total walking zones: %d\n", nrow(combined_isochrones_wgs84)))
cat(sprintf("Time intervals: %s minutes\n", paste(TIME_INTERVALS, collapse = ", ")))

zone_breakdown <- table(combined_isochrones_wgs84$time_min)
cat("\nDetailed zone breakdown:\n")
for (time in names(zone_breakdown)) {
  cat(sprintf("  %2s minutes: %3d zones (%.1f%% coverage)\n", 
              time, zone_breakdown[time], 
              zone_breakdown[time] / nrow(hotels_projected) * 100))
}

cat(sprintf("\n🎉 SUCCESS! Final polished Corfu walking isochrones map created\n"))
cat(sprintf("📁 Output file: %s\n", OUTPUT_FILE))
cat(sprintf("📐 High resolution: %d x %d inches at %d DPI\n", MAP_WIDTH, MAP_HEIGHT, DPI))
cat(sprintf("🗺️  Map style: Blue gradient isochrones with Corfu island background\n"))

cat(sprintf("\n%s\n", paste(rep("=", 60), collapse = "")))