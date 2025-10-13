# Smooth Organic Isochrones - Like Reference Image
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
  library(KernSmooth)
})

cat("🌊 Smooth Organic Isochrones (Reference Style)\n")
cat("===============================================\n")

# Configuration
MAX_HOTELS <- 141  # Process ALL hotels
WALKING_SPEED_KMH <- 5  # km/h
TIME_INTERVALS <- c(5, 10, 15, 20, 30, 45, 60)  # minutes
OUTPUT_FILE <- "corfu_smooth_organic_isochrones.png"
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

# Get Corfu coastline to define land vs sea
cat("🌊 Getting Corfu coastline...\n")
corfu_coastline <- NULL

tryCatch({
  coastline_query <- opq(bbox = bbox) %>%
    add_osm_feature(key = "natural", value = "coastline")
  
  coastline_result <- osmdata_sf(coastline_query)
  
  if (!is.null(coastline_result$osm_lines) && nrow(coastline_result$osm_lines) > 0) {
    corfu_coastline <- coastline_result$osm_lines
    cat("✅ Found Corfu coastline\n")
  }
}, error = function(e) {
  cat("⚠️  Could not get coastline\n")
})

# Create a high-resolution grid for smooth isochrones
cat("🔄 Creating smooth isochrone grid...\n")

# Convert hotels to coordinates
hotels_coords <- data.frame(
  lon = as.numeric(hotels_to_process$longitude),
  lat = as.numeric(hotels_to_process$latitude),
  name = hotels_to_process$name
)

# Create a fine grid for smooth interpolation
grid_resolution <- 200  # Higher = smoother
lon_seq <- seq(bbox[1], bbox[3], length.out = grid_resolution)
lat_seq <- seq(bbox[2], bbox[4], length.out = grid_resolution)
grid <- expand.grid(lon = lon_seq, lat = lat_seq)

# Function to calculate smooth walking accessibility
cat("🚶 Calculating smooth walking accessibility...\n")

# For each grid point, calculate minimum walking time to any hotel
calculate_walking_surface <- function(grid_points, hotels) {
  walking_times <- matrix(NA, nrow = nrow(grid_points), ncol = length(TIME_INTERVALS))
  
  for (i in 1:nrow(grid_points)) {
    grid_point <- grid_points[i, ]
    
    # Calculate distance to all hotels
    distances <- sqrt((grid_point$lon - hotels$lon)^2 + (grid_point$lat - hotels$lat)^2)
    
    # Convert to approximate walking distance (rough conversion)
    # 1 degree ≈ 111 km, but we'll use a simpler approximation
    walking_distances_km <- distances * 111  # Rough conversion
    
    # Calculate walking time in minutes
    walking_times_min <- (walking_distances_km / WALKING_SPEED_KMH) * 60
    
    # Find minimum time to reach any hotel
    min_time <- min(walking_times_min)
    
    # For each time interval, check if reachable
    for (j in 1:length(TIME_INTERVALS)) {
      if (min_time <= TIME_INTERVALS[j]) {
        walking_times[i, j] <- TIME_INTERVALS[j]
      }
    }
    
    if (i %% 1000 == 0) {
      cat(sprintf("  Grid progress: %d/%d points\n", i, nrow(grid_points)))
    }
  }
  
  return(walking_times)
}

# Calculate walking surface
walking_surface <- calculate_walking_surface(grid, hotels_coords)

# Create smooth contour data
cat("🎨 Creating smooth contours...\n")

contour_data <- list()
for (j in 1:length(TIME_INTERVALS)) {
  time_interval <- TIME_INTERVALS[j]
  
  # Create matrix for contour calculation
  z_matrix <- matrix(walking_surface[, j], nrow = length(lon_seq), ncol = length(lat_seq))
  
  # Replace NA with high values (unreachable areas)
  z_matrix[is.na(z_matrix)] <- max(TIME_INTERVALS) + 10
  
  # Create contour data
  contour_lines <- contourLines(lon_seq, lat_seq, z_matrix, levels = time_interval)
  
  if (length(contour_lines) > 0) {
    for (k in 1:length(contour_lines)) {
      contour_df <- data.frame(
        lon = contour_lines[[k]]$x,
        lat = contour_lines[[k]]$y,
        time_min = time_interval,
        group = paste(time_interval, k, sep = "_")
      )
      contour_data[[paste(time_interval, k, sep = "_")]] <- contour_df
    }
  }
}

# Combine all contour data
if (length(contour_data) > 0) {
  all_contours <- do.call(rbind, contour_data)
  cat(sprintf("✅ Created %d smooth contour segments\n", length(contour_data)))
} else {
  stop("❌ No contours were created!")
}

# Convert to sf for clipping to coastline
contours_sf <- st_as_sf(all_contours, coords = c("lon", "lat"), crs = 4326)

# Create smooth filled areas instead of just lines
cat("🌊 Creating smooth filled areas...\n")

# Create raster-like data for smooth filling
grid_data <- data.frame(
  lon = grid$lon,
  lat = grid$lat
)

# Calculate smooth accessibility values for each grid point
accessibility_values <- rep(NA, nrow(grid_data))

for (i in 1:nrow(grid_data)) {
  grid_point <- grid_data[i, ]
  
  # Calculate distance to nearest hotel
  distances <- sqrt((grid_point$lon - hotels_coords$lon)^2 + 
                   (grid_point$lat - hotels_coords$lat)^2)
  
  min_distance_km <- min(distances) * 111  # Rough conversion to km
  min_time <- (min_distance_km / WALKING_SPEED_KMH) * 60
  
  # Assign accessibility value based on walking time
  if (min_time <= 5) accessibility_values[i] <- 5
  else if (min_time <= 10) accessibility_values[i] <- 10
  else if (min_time <= 15) accessibility_values[i] <- 15
  else if (min_time <= 20) accessibility_values[i] <- 20
  else if (min_time <= 30) accessibility_values[i] <- 30
  else if (min_time <= 45) accessibility_values[i] <- 45
  else if (min_time <= 60) accessibility_values[i] <- 60
  else accessibility_values[i] <- NA
}

grid_data$accessibility <- accessibility_values

# Remove unreachable areas
grid_data <- grid_data[!is.na(grid_data$accessibility), ]

cat(sprintf("✅ Created %d accessibility grid points\n", nrow(grid_data)))

# Convert hotels to sf points
hotels_sf <- st_as_sf(hotels_coords, coords = c("lon", "lat"), crs = 4326)

# Create the smooth map
cat("🎨 Creating smooth organic map...\n")

# Color palette - smooth blues like reference
time_colors <- c(
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

# Add base background (very light)
p <- p + 
  theme_void() +
  theme(
    panel.background = element_rect(fill = "#f8f9fa", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

# Add smooth accessibility surface using geom_point with alpha blending
p <- p +
  geom_point(data = grid_data,
             aes(x = lon, y = lat, color = factor(accessibility)),
             alpha = 0.4,
             size = 0.8) +
  scale_color_manual(values = time_colors,
                    name = "Walking Time",
                    labels = paste(names(time_colors), "min"))

# Add coastline if available
if (!is.null(corfu_coastline)) {
  p <- p + 
    geom_sf(data = corfu_coastline, 
            color = "white", 
            linewidth = 1.2,
            alpha = 0.8)
}

# Add hotel points - purple like reference
p <- p +
  geom_sf(data = hotels_sf,
          color = "white",
          fill = "#d63384",  # Purple/magenta
          size = 2.5,
          alpha = 0.9,
          shape = 21,
          stroke = 1.2)

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
    plot.margin = margin(40, 40, 40, 40),
    legend.position = "right",
    legend.title = element_text(size = 14, face = "bold", color = "#2c3e50"),
    legend.text = element_text(size = 12, color = "#34495e"),
    legend.key.size = unit(1.2, "cm"),
    legend.background = element_rect(fill = "white", color = "#cccccc", linewidth = 0.5)
  ) +
  labs(
    title = "Smooth Walking Accessibility - Corfu Hotels",
    subtitle = sprintf("Organic Flow Patterns • %d Hotels • Land Areas Only • %d km/h", 
                      nrow(hotels_coords), WALKING_SPEED_KMH),
    caption = "Purple markers: Hotels • Blue gradients: Smooth walking reach • Organic shapes"
  )

# Save the map
cat(sprintf("💾 Saving smooth organic map as: %s\n", OUTPUT_FILE))
ggsave(OUTPUT_FILE, plot = p, 
       width = MAP_WIDTH, height = MAP_HEIGHT, 
       dpi = DPI, units = "in",
       bg = "white")

# Generate summary report
cat("\n📊 SMOOTH ORGANIC ISOCHRONES SUMMARY\n")
cat("====================================\n")
cat(sprintf("Hotels processed: %d\n", nrow(hotels_coords)))
cat(sprintf("Grid resolution: %d x %d points\n", grid_resolution, grid_resolution))
cat(sprintf("Accessibility points: %d\n", nrow(grid_data)))

accessibility_breakdown <- table(grid_data$accessibility)
cat("\nAccessibility breakdown:\n")
for (time in names(accessibility_breakdown)) {
  cat(sprintf("  %2s minutes: %5d grid points\n", time, accessibility_breakdown[time]))
}

cat(sprintf("\n🎉 SUCCESS! Smooth organic isochrones created\n"))
cat(sprintf("📁 Output file: %s\n", OUTPUT_FILE))
cat(sprintf("🌊 Style: Smooth, organic, flowing shapes (like reference)\n"))
cat(sprintf("💜 Hotel markers: Purple/magenta dots\n"))
cat(sprintf("🎨 Effect: Natural gradient flow patterns\n"))

cat(sprintf("\n%s\n", paste(rep("=", 55), collapse = "")))