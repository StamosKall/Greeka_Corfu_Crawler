# Smooth Density-Based Isochrones - Reference Style
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

cat("🌊 Smooth Density-Based Isochrones (Reference Style)\n")
cat("=====================================================\n")

# Configuration
MAX_HOTELS <- 141  # Process ALL hotels
WALKING_SPEED_KMH <- 5  # km/h
TIME_INTERVALS <- c(5, 10, 15, 20, 30, 45, 60)  # minutes
OUTPUT_FILE <- "corfu_smooth_density_isochrones.png"
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

# Get Corfu coastline
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

# Convert hotels to coordinates
hotels_coords <- data.frame(
  lon = as.numeric(hotels_to_process$longitude),
  lat = as.numeric(hotels_to_process$latitude),
  name = hotels_to_process$name
)

# Create multiple layers for each time interval to achieve smooth gradients
cat("🎨 Creating smooth gradient layers...\n")

# Function to create walking zones around each hotel
create_smooth_zones <- function(hotel_coords, time_intervals) {
  all_zones <- list()
  
  for (i in 1:nrow(hotel_coords)) {
    hotel <- hotel_coords[i, ]
    
    for (time_min in time_intervals) {
      # Calculate walking distance in degrees (rough approximation)
      walking_distance_km <- (WALKING_SPEED_KMH * time_min) / 60
      walking_distance_deg <- walking_distance_km / 111  # Rough conversion
      
      # Create multiple concentric zones for smooth gradient effect
      n_rings <- 20  # More rings = smoother gradient
      
      for (ring in 1:n_rings) {
        ring_distance <- (walking_distance_deg * ring) / n_rings
        alpha_value <- 1 - (ring / n_rings)  # Fade out towards edges
        
        # Create points in a circle
        angles <- seq(0, 2*pi, length.out = 60)
        circle_points <- data.frame(
          lon = hotel$lon + ring_distance * cos(angles),
          lat = hotel$lat + ring_distance * sin(angles),
          time_min = time_min,
          hotel_id = i,
          ring = ring,
          alpha = alpha_value * 0.1,  # Low alpha for smooth blending
          hotel_name = hotel$name
        )
        
        all_zones[[paste(i, time_min, ring, sep = "_")]] <- circle_points
      }
    }
    
    if (i %% 20 == 0) {
      cat(sprintf("  Progress: %d/%d hotels processed\n", i, nrow(hotel_coords)))
    }
  }
  
  return(do.call(rbind, all_zones))
}

# Create smooth zones
smooth_zones <- create_smooth_zones(hotels_coords, TIME_INTERVALS)
cat(sprintf("✅ Created %d smooth gradient zones\n", nrow(smooth_zones)))

# Convert hotels to sf points
hotels_sf <- st_as_sf(hotels_coords, coords = c("lon", "lat"), crs = 4326)

# Create the smooth map like your reference
cat("🎨 Creating smooth gradient map...\n")

# Color palette - exactly like reference
time_colors <- c(
  "5" = "#08306b",   # Darkest blue (center)
  "10" = "#08519c",  # Dark blue
  "15" = "#3182bd",  # Medium blue
  "20" = "#6baed6",  # Light blue
  "30" = "#9ecae1",  # Very light blue
  "45" = "#c6dbef",  # Pale blue
  "60" = "#deebf7"   # Very pale blue (outer)
)

# Start building the plot
p <- ggplot()

# Add very light background
p <- p + 
  theme_void() +
  theme(
    panel.background = element_rect(fill = "#fafbfc", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

# Add smooth gradient zones - largest first for proper layering
for (time in rev(TIME_INTERVALS)) {
  time_data <- smooth_zones[smooth_zones$time_min == time, ]
  if (nrow(time_data) > 0) {
    p <- p +
      geom_point(data = time_data,
                aes(x = lon, y = lat),
                color = time_colors[as.character(time)],
                alpha = time_data$alpha,
                size = 2.5)
  }
}

# Add additional smooth layer using geom_smooth or stat_density_2d for extra smoothness
# Create a summary dataset for density plotting
hotel_density_data <- data.frame()
for (time in TIME_INTERVALS) {
  for (i in 1:nrow(hotels_coords)) {
    hotel <- hotels_coords[i, ]
    walking_distance_km <- (WALKING_SPEED_KMH * time) / 60
    walking_distance_deg <- walking_distance_km / 111
    
    # Create a denser set of points for this hotel-time combination
    n_points <- 100
    angles <- runif(n_points, 0, 2*pi)
    distances <- runif(n_points, 0, walking_distance_deg)
    
    density_points <- data.frame(
      lon = hotel$lon + distances * cos(angles),
      lat = hotel$lat + distances * sin(angles),
      time_min = time,
      hotel_id = i
    )
    
    hotel_density_data <- rbind(hotel_density_data, density_points)
  }
}

# Add density-based smooth contours
p <- p +
  stat_density_2d_filled(data = hotel_density_data,
                         aes(x = lon, y = lat, fill = factor(time_min)),
                         alpha = 0.3,
                         contour_var = "ndensity",
                         bins = 8) +
  scale_fill_manual(values = time_colors,
                   name = "Walking Time",
                   labels = paste(names(time_colors), "min"),
                   guide = "none")  # Hide this legend, we'll make a custom one

# Add coastline for reference
if (!is.null(corfu_coastline)) {
  p <- p + 
    geom_sf(data = corfu_coastline, 
            color = "white", 
            linewidth = 1.5,
            alpha = 0.9)
}

# Add hotel points on top - purple like reference
p <- p +
  geom_sf(data = hotels_sf,
          color = "white",
          fill = "#d63384",  # Purple/magenta like reference
          size = 2.8,
          alpha = 0.95,
          shape = 21,
          stroke = 1.5)

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
    legend.position = "none"  # We'll add custom legend
  ) +
  labs(
    title = "Smooth Walking Accessibility - Corfu Hotels",
    subtitle = sprintf("Organic Flow Gradients • %d Hotels • Smooth Transitions • %d km/h", 
                      nrow(hotels_coords), WALKING_SPEED_KMH),
    caption = "Purple markers: Hotels • Blue gradients: Smooth walking accessibility zones"
  )

# Add custom legend box
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
             fill = time_colors[i], alpha = 0.8, color = "white", linewidth = 0.3) +
    annotate("text",
             x = legend_x + legend_width * 0.35,
             y = y_pos,
             label = paste(TIME_INTERVALS[i], "minutes"),
             size = 4.5, color = "#34495e", hjust = 0)
}

# Save the map
cat(sprintf("💾 Saving smooth density map as: %s\n", OUTPUT_FILE))
ggsave(OUTPUT_FILE, plot = p, 
       width = MAP_WIDTH, height = MAP_HEIGHT, 
       dpi = DPI, units = "in",
       bg = "white")

# Generate summary report
cat("\n📊 SMOOTH DENSITY ISOCHRONES SUMMARY\n")
cat("====================================\n")
cat(sprintf("Hotels processed: %d\n", nrow(hotels_coords)))
cat(sprintf("Smooth gradient zones: %d\n", nrow(smooth_zones)))
cat(sprintf("Density points: %d\n", nrow(hotel_density_data)))

cat(sprintf("\n🎉 SUCCESS! Smooth density isochrones created\n"))
cat(sprintf("📁 Output file: %s\n", OUTPUT_FILE))
cat(sprintf("🌊 Style: Smooth, organic, flowing gradients\n"))
cat(sprintf("💜 Hotel markers: Purple dots like reference\n"))
cat(sprintf("🎨 Effect: Natural gradient flow with smooth transitions\n"))

cat(sprintf("\n%s\n", paste(rep("=", 55), collapse = "")))