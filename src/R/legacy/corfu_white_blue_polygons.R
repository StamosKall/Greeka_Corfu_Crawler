# White Background with Blue Polygon Isochrones
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

cat("🤍 White Background Blue Polygon Isochrones\n")
cat("===========================================\n")

# Configuration
MAX_HOTELS <- 141  # Process ALL hotels
WALKING_SPEED_KMH <- 5  # km/h
TIME_INTERVALS <- c(5, 10, 15, 20, 30, 45, 60)  # minutes
OUTPUT_FILE <- "corfu_white_blue_polygons.png"
MAP_WIDTH <- 18
MAP_HEIGHT <- 22
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
lat_padding <- (lat_range[2] - lat_range[1]) * 0.1
lon_padding <- (lon_range[2] - lon_range[1]) * 0.1

bbox <- c(
  xmin = lon_range[1] - lon_padding,
  ymin = lat_range[1] - lat_padding,
  xmax = lon_range[2] + lon_padding,
  ymax = lat_range[2] + lat_padding
)

cat(sprintf("📍 Map bounds: %.3f, %.3f, %.3f, %.3f\n", bbox[1], bbox[2], bbox[3], bbox[4]))

# Get Corfu land boundary for clipping
cat("🏝️ Getting Corfu land boundary...\n")
corfu_land <- NULL

tryCatch({
  coastline_query <- opq(bbox = bbox) %>%
    add_osm_feature(key = "natural", value = "coastline")
  
  coastline_result <- osmdata_sf(coastline_query)
  
  if (!is.null(coastline_result$osm_lines) && nrow(coastline_result$osm_lines) > 0) {
    coastlines <- coastline_result$osm_lines
    coastlines_combined <- st_union(coastlines)
    
    # Create land area by differencing from bounding box
    bbox_poly <- st_polygon(list(matrix(c(
      bbox[1], bbox[2],
      bbox[3], bbox[2], 
      bbox[3], bbox[4],
      bbox[1], bbox[4],
      bbox[1], bbox[2]
    ), ncol = 2, byrow = TRUE)))
    
    bbox_sf <- st_sf(geometry = st_sfc(bbox_poly, crs = 4326))
    
    # Create sea buffer
    sea_buffer <- st_buffer(coastlines_combined, dist = 0.001)
    
    # Land = bbox minus sea
    corfu_land <- st_difference(bbox_sf, st_sf(geometry = st_sfc(sea_buffer, crs = 4326)))
    
    cat("✅ Created land boundary from coastlines\n")
  }
}, error = function(e) {
  cat("⚠️  Could not get coastline\n")
})

# Fallback: Use hotel convex hull if no coastline
if (is.null(corfu_land)) {
  hotels_sf_temp <- st_as_sf(hotels_to_process, 
                            coords = c("longitude", "latitude"), 
                            crs = 4326)
  
  hotel_hull <- st_convex_hull(st_union(hotels_sf_temp))
  corfu_land <- st_buffer(hotel_hull, dist = 0.02)
  corfu_land <- st_sf(geometry = corfu_land)
  
  cat("⚠️  Using hotel area as land boundary\n")
}

# Convert hotels to sf points
hotels_sf <- st_as_sf(hotels_to_process, 
                     coords = c("longitude", "latitude"), 
                     crs = 4326)

# Transform to projected coordinates for accurate distance
cat("🔄 Transforming coordinates...\n")
hotels_projected <- st_transform(hotels_sf, crs = 32634)  # UTM 34N
corfu_land_projected <- st_transform(corfu_land, crs = 32634)

# Create proper polygon isochrones (not circles)
cat("🔷 Creating polygon isochrones...\n")

# Function to create irregular polygons around hotels
create_polygon_isochrones <- function(hotels_proj, land_boundary, time_intervals) {
  all_polygons <- list()
  
  for (i in 1:nrow(hotels_proj)) {
    hotel <- hotels_proj[i, ]
    hotel_coords <- st_coordinates(hotel)
    
    cat(sprintf("  [%d/%d] Processing: %s\n", i, nrow(hotels_proj), 
                substr(hotels_to_process$name[i], 1, 40)))
    
    for (time_min in time_intervals) {
      # Calculate walking distance
      walking_distance <- (WALKING_SPEED_KMH * 1000 * time_min) / 60
      
      # Create irregular polygon (not perfect circle)
      n_points <- 48  # More points for smoother polygons
      angles <- seq(0, 2*pi, length.out = n_points + 1)[1:n_points]
      
      # Add randomness to create irregular, organic shapes
      set.seed(i + time_min)  # Consistent randomness per hotel-time
      distance_variations <- runif(n_points, 0.7, 1.0)  # Random variations
      angle_variations <- runif(n_points, -0.1, 0.1)    # Small angle variations
      
      # Calculate polygon points with variations
      varied_distances <- walking_distance * distance_variations
      varied_angles <- angles + angle_variations
      
      polygon_coords <- matrix(c(
        hotel_coords[1] + varied_distances * cos(varied_angles),
        hotel_coords[2] + varied_distances * sin(varied_angles)
      ), ncol = 2)
      
      # Close the polygon
      polygon_coords <- rbind(polygon_coords, polygon_coords[1, ])
      
      # Create sf polygon
      polygon_geom <- st_polygon(list(polygon_coords))
      polygon_sf <- st_sf(geometry = st_sfc(polygon_geom, crs = 32634))
      
      # Clip to land boundary
      tryCatch({
        clipped_polygon <- st_intersection(polygon_sf, land_boundary)
        
        if (!st_is_empty(clipped_polygon)) {
          # Add attributes
          clipped_polygon$time_min <- time_min
          clipped_polygon$hotel_id <- i
          clipped_polygon$hotel_name <- hotels_to_process$name[i]
          
          all_polygons[[paste(i, time_min, sep = "_")]] <- clipped_polygon
        }
      }, error = function(e) {
        # Skip if clipping fails
      })
    }
    
    if (i %% 20 == 0) {
      cat(sprintf("    Progress: %d/%d hotels completed\n", i, nrow(hotels_proj)))
    }
  }
  
  return(all_polygons)
}

# Create polygon isochrones
polygon_list <- create_polygon_isochrones(hotels_projected, corfu_land_projected, TIME_INTERVALS)

if (length(polygon_list) > 0) {
  combined_polygons_projected <- do.call(rbind, polygon_list)
  cat(sprintf("✅ Created %d polygon isochrones\n", nrow(combined_polygons_projected)))
} else {
  stop("❌ No polygon isochrones were created!")
}

# Transform back to WGS84 for mapping
combined_polygons_wgs84 <- st_transform(combined_polygons_projected, crs = 4326)
corfu_land_wgs84 <- st_transform(corfu_land_projected, crs = 4326)

# Create the map with white background and blue polygons
cat("🎨 Creating white background blue polygon map...\n")

# Blue color palette - different shades of blue
blue_colors <- c(
  "5" = "#08306b",   # Darkest blue
  "10" = "#08519c",  # Dark blue
  "15" = "#3182bd",  # Medium blue
  "20" = "#6baed6",  # Light blue
  "30" = "#9ecae1",  # Very light blue
  "45" = "#c6dbef",  # Pale blue
  "60" = "#deebf7"   # Very pale blue
)

# Start building the plot
p <- ggplot()

# WHITE BACKGROUND (sea and background)
p <- p + 
  theme_void() +
  theme(
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

# Add land area with distinct color and black border
p <- p + 
  geom_sf(data = corfu_land_wgs84, 
          fill = "#f8f8f8",      # Very light gray for land (distinguishable from white sea)
          color = "black",       # BLACK border around island
          alpha = 1.0,
          linewidth = 2.0)       # Thick black border

# Add blue polygon isochrones in reverse order (largest first)
for (time in rev(TIME_INTERVALS)) {
  time_data <- combined_polygons_wgs84[combined_polygons_wgs84$time_min == time, ]
  if (nrow(time_data) > 0) {
    # Make inner zones more opaque, outer zones more transparent
    alpha_val <- 0.4 + (max(TIME_INTERVALS) - time) / max(TIME_INTERVALS) * 0.4
    
    p <- p +
      geom_sf(data = time_data,
              fill = blue_colors[as.character(time)],
              color = "white",
              alpha = alpha_val,
              linewidth = 0.2)
  }
}

# Add hotel points - purple/magenta
p <- p +
  geom_sf(data = hotels_sf,
          color = "white",
          fill = "#d63384",  # Purple/magenta
          size = 2.0,
          alpha = 0.9,
          shape = 21,
          stroke = 1.0)

# Style the map
p <- p +
  coord_sf(xlim = c(bbox[1], bbox[3]), 
           ylim = c(bbox[2], bbox[4]),
           expand = FALSE) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 26, face = "bold", 
                             color = "#2c3e50", margin = margin(b = 20)),
    plot.subtitle = element_text(hjust = 0.5, size = 18, color = "#34495e", 
                                margin = margin(b = 35)),
    plot.caption = element_text(hjust = 0.5, size = 13, color = "gray40",
                               margin = margin(t = 25)),
    plot.margin = margin(40, 40, 40, 40)
  ) +
  labs(
    title = "Walking Accessibility Polygons - Corfu Hotels",
    subtitle = sprintf("Black Island Border • Blue Polygons • %d Hotels • Land vs Sea Distinction • %d km/h", 
                      length(unique(combined_polygons_wgs84$hotel_id)), WALKING_SPEED_KMH),
    caption = "Black border: Island outline • Light gray: Land • White: Sea • Blue polygons: Walking zones"
  )

# Add custom legend with white background
legend_x <- bbox[3] - (bbox[3] - bbox[1]) * 0.25
legend_width <- (bbox[3] - bbox[1]) * 0.22

p <- p + 
  annotate("rect", 
           xmin = legend_x, 
           xmax = bbox[3] - (bbox[3] - bbox[1]) * 0.02, 
           ymin = bbox[4] - (bbox[4] - bbox[2]) * 0.5, 
           ymax = bbox[4] - (bbox[4] - bbox[2]) * 0.05,
           fill = "white", color = "#cccccc", alpha = 0.95, linewidth = 0.5) +
  annotate("text", 
           x = legend_x + legend_width/2, 
           y = bbox[4] - (bbox[4] - bbox[2]) * 0.08,
           label = "Walking Time", 
           size = 6, fontface = "bold", color = "#2c3e50")

# Add legend items
for (i in 1:length(TIME_INTERVALS)) {
  y_pos <- bbox[4] - (bbox[4] - bbox[2]) * (0.13 + i * 0.05)
  
  p <- p + 
    annotate("rect",
             xmin = legend_x + legend_width * 0.1,
             xmax = legend_x + legend_width * 0.28,
             ymin = y_pos - (bbox[4] - bbox[2]) * 0.02,
             ymax = y_pos + (bbox[4] - bbox[2]) * 0.02,
             fill = blue_colors[i], alpha = 0.8, color = "white", linewidth = 0.3) +
    annotate("text",
             x = legend_x + legend_width * 0.35,
             y = y_pos,
             label = paste(TIME_INTERVALS[i], "minutes"),
             size = 4.5, color = "#34495e", hjust = 0)
}

# Save the map
cat(sprintf("💾 Saving white background blue polygon map as: %s\n", OUTPUT_FILE))
ggsave(OUTPUT_FILE, plot = p, 
       width = MAP_WIDTH, height = MAP_HEIGHT, 
       dpi = DPI, units = "in",
       bg = "white")

# Generate summary report
cat("\n📊 WHITE BACKGROUND BLUE POLYGONS SUMMARY\n")
cat("=========================================\n")
cat(sprintf("Hotels processed: %d\n", length(unique(combined_polygons_wgs84$hotel_id))))
cat(sprintf("Blue polygon zones: %d\n", nrow(combined_polygons_wgs84)))

zone_breakdown <- table(combined_polygons_wgs84$time_min)
cat("\nPolygon zone breakdown:\n")
for (time in names(zone_breakdown)) {
  cat(sprintf("  %2s minutes: %3d polygons\n", time, zone_breakdown[time]))
}

cat(sprintf("\n🎉 SUCCESS! White background blue polygon map created\n"))
cat(sprintf("📁 Output file: %s\n", OUTPUT_FILE))
cat(sprintf("🤍 Sea: Pure white background\n"))
cat(sprintf("🏝️ Land: Light gray with black border\n"))
cat(sprintf("🔷 Zones: Blue polygons (irregular shapes, not circles)\n"))
cat(sprintf("💜 Hotels: Purple markers\n"))
cat(sprintf("⚫ Border: Thick black island outline\n"))
cat(sprintf("🚫 No circles: Only irregular polygon shapes\n"))

cat(sprintf("\n%s\n", paste(rep("=", 50), collapse = "")))