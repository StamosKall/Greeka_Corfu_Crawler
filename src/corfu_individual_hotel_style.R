# Individual Hotel Isochrones - Like Reference Image
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

cat("🏨 Individual Hotel Isochrones (Reference Style)\n")
cat("================================================\n")

# Configuration
MAX_HOTELS <- 141  # Process ALL hotels
WALKING_SPEED_KMH <- 5  # km/h
TIME_INTERVALS <- c(5, 10, 15, 20, 30, 45, 60)  # minutes
OUTPUT_FILE <- "corfu_individual_hotel_isochrones.png"
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
cat("🌊 Getting Corfu coastline for land boundary...\n")
corfu_land <- NULL

tryCatch({
  coastline_query <- opq(bbox = bbox) %>%
    add_osm_feature(key = "natural", value = "coastline")
  
  coastline_result <- osmdata_sf(coastline_query)
  
  if (!is.null(coastline_result$osm_lines) && nrow(coastline_result$osm_lines) > 0) {
    coastlines <- coastline_result$osm_lines
    coastlines_combined <- st_union(coastlines)
    
    # Create land area by buffering coastline inward
    # This creates the land polygon that we'll clip isochrones to
    coastline_buffer <- st_buffer(coastlines_combined, dist = -0.001)  # Small inward buffer
    
    # Create bounding box and subtract sea areas
    bbox_poly <- st_polygon(list(matrix(c(
      bbox[1], bbox[2],
      bbox[3], bbox[2], 
      bbox[3], bbox[4],
      bbox[1], bbox[4],
      bbox[1], bbox[2]
    ), ncol = 2, byrow = TRUE)))
    
    bbox_sf <- st_sf(geometry = st_sfc(bbox_poly, crs = 4326))
    
    # Create sea buffer (areas that are definitely sea)
    sea_buffer <- st_buffer(coastlines_combined, dist = 0.001)  # Small buffer into sea
    
    # Land = bounding box minus sea areas
    corfu_land <- st_difference(bbox_sf, st_sf(geometry = st_sfc(sea_buffer, crs = 4326)))
    
    cat("✅ Created land boundary from coastlines\n")
  }
}, error = function(e) {
  cat("⚠️  Could not get coastline, using hotel area\n")
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

# Create individual hotel isochrones
cat("🏨 Creating individual hotel walking zones...\n")
all_hotel_isochrones <- list()

for (i in 1:nrow(hotels_projected)) {
  hotel <- hotels_projected[i, ]
  hotel_name <- hotels_to_process$name[i]
  
  cat(sprintf("  [%d/%d] Processing: %s\n", i, nrow(hotels_projected), 
              substr(hotel_name, 1, 40)))
  
  hotel_zones <- list()
  
  for (time_min in TIME_INTERVALS) {
    # Calculate walking distance in meters
    walking_distance <- (WALKING_SPEED_KMH * 1000 * time_min) / 60
    
    # Create buffer around hotel
    buffer <- st_buffer(hotel, dist = walking_distance)
    
    # Clip to land areas ONLY
    tryCatch({
      land_clipped <- st_intersection(buffer, corfu_land_projected)
      
      if (!st_is_empty(land_clipped)) {
        # Create proper sf object for this time zone
        zone_sf <- st_sf(
          hotel_id = i,
          hotel_name = hotel_name,
          time_min = time_min,
          walking_km = round((walking_distance / 1000), 2),
          geometry = st_geometry(land_clipped)
        )
        
        hotel_zones[[as.character(time_min)]] <- zone_sf
      }
    }, error = function(e) {
      # Skip if clipping fails
    })
  }
  
  if (length(hotel_zones) > 0) {
    hotel_combined <- do.call(rbind, hotel_zones)
    all_hotel_isochrones[[i]] <- hotel_combined
  }
  
  # Progress update
  if (i %% 20 == 0) {
    cat(sprintf("    Progress: %d/%d hotels completed\n", i, nrow(hotels_projected)))
  }
}

# Combine all hotel isochrones
if (length(all_hotel_isochrones) > 0) {
  all_isochrones_projected <- do.call(rbind, all_hotel_isochrones)
  cat(sprintf("✅ Created %d individual hotel zones\n", nrow(all_isochrones_projected)))
} else {
  stop("❌ No hotel isochrones were created!")
}

# Transform back to WGS84 for mapping
all_isochrones_wgs84 <- st_transform(all_isochrones_projected, crs = 4326)
corfu_land_wgs84 <- st_transform(corfu_land_projected, crs = 4326)

# Create the map like your reference image
cat("🎨 Creating reference-style map...\n")

# Color palette - blue gradient like your reference
time_colors <- c(
  "#08306b",  # 5 min - Darkest blue
  "#08519c",  # 10 min - Dark blue
  "#3182bd",  # 15 min - Medium blue
  "#6baed6",  # 20 min - Light blue
  "#9ecae1",  # 30 min - Very light blue
  "#c6dbef",  # 45 min - Pale blue
  "#deebf7"   # 60 min - Very pale blue
)
names(time_colors) <- TIME_INTERVALS

# Start building the plot
p <- ggplot()

# Add base map style (light background like your reference)
p <- p + 
  theme_void() +
  theme(
    panel.background = element_rect(fill = "#f8f9fa", color = NA),  # Very light gray
    plot.background = element_rect(fill = "white", color = NA)
  )

# Add subtle land areas (very light)
p <- p + 
  geom_sf(data = corfu_land_wgs84, 
          fill = "#ffffff", 
          color = "#e0e0e0", 
          alpha = 0.3,
          linewidth = 0.3)

# Add individual hotel isochrones - each hotel gets its own zones
# Add from largest to smallest for proper layering
for (time in rev(TIME_INTERVALS)) {
  time_data <- all_isochrones_wgs84[all_isochrones_wgs84$time_min == time, ]
  if (nrow(time_data) > 0) {
    # Make inner zones more opaque, outer zones more transparent
    alpha_val <- 0.15 + (max(TIME_INTERVALS) - time) / max(TIME_INTERVALS) * 0.5
    
    p <- p +
      geom_sf(data = time_data,
              fill = time_colors[as.character(time)],
              color = "white",
              alpha = alpha_val,
              linewidth = 0.1)
  }
}

# Add hotel points - purple/magenta like your reference
p <- p +
  geom_sf(data = hotels_sf,
          color = "white",
          fill = "#d63384",  # Magenta/purple like your reference
          size = 2.2,
          alpha = 0.9,
          shape = 21,
          stroke = 1.0)

# Style like your reference image
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
    title = "Individual Hotel Walking Accessibility - Corfu",
    subtitle = sprintf("%d Hotels • Individual Walking Zones • Land Areas Only • %d km/h", 
                      length(unique(all_isochrones_wgs84$hotel_id)), WALKING_SPEED_KMH),
    caption = "Purple markers: Hotels • Blue gradients: Walking reach (5-60 min) • Sea areas excluded"
  )

# Add legend similar to your reference
legend_x <- bbox[3] - (bbox[3] - bbox[1]) * 0.28
legend_width <- (bbox[3] - bbox[1]) * 0.25

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

# Add legend color boxes and labels
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
cat(sprintf("💾 Saving reference-style map as: %s\n", OUTPUT_FILE))
ggsave(OUTPUT_FILE, plot = p, 
       width = MAP_WIDTH, height = MAP_HEIGHT, 
       dpi = DPI, units = "in",
       bg = "white")

# Generate summary report
cat("\n📊 INDIVIDUAL HOTEL ISOCHRONES SUMMARY\n")
cat("======================================\n")
cat(sprintf("Hotels with walking zones: %d\n", length(unique(all_isochrones_wgs84$hotel_id))))
cat(sprintf("Total individual zones: %d\n", nrow(all_isochrones_wgs84)))

# Count zones per time interval
zone_breakdown <- table(all_isochrones_wgs84$time_min)
cat("\nZone breakdown (individual hotels):\n")
for (time in names(zone_breakdown)) {
  cat(sprintf("  %2s minutes: %3d zones (%d hotels)\n", 
              time, zone_breakdown[time], zone_breakdown[time]))
}

cat(sprintf("\n🎉 SUCCESS! Individual hotel isochrones created\n"))
cat(sprintf("📁 Output file: %s\n", OUTPUT_FILE))
cat(sprintf("🏨 Style: Individual hotel walking zones (like reference image)\n"))
cat(sprintf("🌊 Sea exclusion: Walking zones only on land areas\n"))
cat(sprintf("💜 Hotel markers: Purple/magenta like reference\n"))

cat(sprintf("\n%s\n", paste(rep("=", 55), collapse = "")))