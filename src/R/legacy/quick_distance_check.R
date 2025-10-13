# Quick Hotel Distance Calculator
# For spot-checking specific hotel distances and validating isochrone accuracy

library(jsonlite)
library(geosphere)
library(dplyr)

# Load hotel data
hotels_data <- fromJSON("../data/hotels.json")
hotels_df <- as.data.frame(hotels_data)
hotels_df$latitude <- as.numeric(hotels_df$latitude)
hotels_df$longitude <- as.numeric(hotels_df$longitude)

# Remove invalid coordinates
hotels_df <- hotels_df[!is.na(hotels_df$latitude) & !is.na(hotels_df$longitude), ]

cat(sprintf("Loaded %d hotels with valid coordinates\n\n", nrow(hotels_df)))

# Function to find hotel by name (partial match)
find_hotel <- function(search_name) {
  matches <- grep(search_name, hotels_df$name, ignore.case = TRUE)
  if(length(matches) == 0) {
    cat("No hotels found matching:", search_name, "\n")
    return(NULL)
  }
  if(length(matches) > 1) {
    cat("Multiple matches found:\n")
    for(i in 1:length(matches)) {
      cat(sprintf("%d. %s\n", i, hotels_df$name[matches[i]]))
    }
    return(matches)
  }
  return(matches[1])
}

# Function to calculate precise distance
calculate_distance <- function(hotel1_idx, hotel2_idx) {
  h1 <- hotels_df[hotel1_idx, ]
  h2 <- hotels_df[hotel2_idx, ]
  
  # Haversine distance (great circle)
  dist_km <- distHaversine(c(h1$longitude, h1$latitude), 
                          c(h2$longitude, h2$latitude)) / 1000
  
  # Also calculate simple Euclidean for comparison
  euclidean_km <- sqrt((h1$latitude - h2$latitude)^2 + 
                       (h1$longitude - h2$longitude)^2) * 111.32  # rough km per degree
  
  cat(sprintf("Distance between:\n"))
  cat(sprintf("  %s (%.6f, %.6f)\n", h1$name, h1$latitude, h1$longitude))
  cat(sprintf("  %s (%.6f, %.6f)\n", h2$name, h2$latitude, h2$longitude))
  cat(sprintf("Haversine distance: %.3f km\n", dist_km))
  cat(sprintf("Euclidean approximation: %.3f km\n", euclidean_km))
  
  return(dist_km)
}

# Function to validate isochrone coverage
validate_isochrones <- function(center_hotel, time_minutes = 15, walking_speed = 5) {
  max_distance <- (walking_speed * time_minutes) / 60  # km
  
  center_idx <- find_hotel(center_hotel)
  if(is.null(center_idx) || length(center_idx) > 1) return(NULL)
  
  center <- hotels_df[center_idx, ]
  
  # Find all hotels within walking distance
  distances <- sapply(1:nrow(hotels_df), function(i) {
    if(i == center_idx) return(0)
    distHaversine(c(center$longitude, center$latitude),
                 c(hotels_df$longitude[i], hotels_df$latitude[i])) / 1000
  })
  
  within_range <- which(distances <= max_distance & distances > 0)
  
  cat(sprintf("Validation for %d-minute walk from: %s\n", time_minutes, center$name))
  cat(sprintf("Maximum walking distance: %.2f km\n", max_distance))
  cat(sprintf("Hotels within range: %d\n", length(within_range)))
  
  if(length(within_range) > 0) {
    cat("\nHotels reachable by walking:\n")
    for(i in within_range) {
      walking_time <- (distances[i] / walking_speed) * 60
      cat(sprintf("  - %s: %.2f km (%.1f min walk)\n", 
                  hotels_df$name[i], distances[i], walking_time))
    }
  }
  
  return(list(center = center, within_range = within_range, distances = distances[within_range]))
}

# Example usage and tests
cat("=== HOTEL POSITION VERIFICATION TOOL ===\n\n")

# Test with some example hotels
cat("1. Testing distance calculations:\n")
cat("-" %s% "-\n", rep("-", 40))

# Find a few hotels for testing
sample_indices <- c(1, 2, 5, 10)
for(i in 1:(length(sample_indices)-1)) {
  for(j in (i+1):length(sample_indices)) {
    dist <- calculate_distance(sample_indices[i], sample_indices[j])
    cat("\n")
  }
}

cat("\n2. Isochrone validation examples:\n")
cat("-" %s% "-\n", rep("-", 40))

# Test isochrones for a few central hotels
test_hotels <- c("Corfu", "Paleokastritsa", "Sidari")
for(hotel_search in test_hotels) {
  cat("\n")
  validate_isochrones(hotel_search, 15, 5)
  cat("\n")
}

# Quick coordinate validation
cat("\n3. Coordinate sanity checks:\n")
cat("-" %s% "-\n", rep("-", 40))

# Check for reasonable coordinate ranges
lat_range <- range(hotels_df$latitude)
lon_range <- range(hotels_df$longitude)

cat(sprintf("Latitude range: %.6f to %.6f\n", lat_range[1], lat_range[2]))
cat(sprintf("Longitude range: %.6f to %.6f\n", lon_range[1], lon_range[2]))

# Corfu approximate bounds check
corfu_lat_range <- c(39.35, 39.80)
corfu_lon_range <- c(19.30, 20.15)

outliers_lat <- hotels_df[hotels_df$latitude < corfu_lat_range[1] | 
                         hotels_df$latitude > corfu_lat_range[2], ]
outliers_lon <- hotels_df[hotels_df$longitude < corfu_lon_range[1] | 
                         hotels_df$longitude > corfu_lon_range[2], ]

if(nrow(outliers_lat) > 0) {
  cat("\nPotential latitude outliers:\n")
  for(i in 1:nrow(outliers_lat)) {
    cat(sprintf("  - %s: lat %.6f\n", outliers_lat$name[i], outliers_lat$latitude[i]))
  }
}

if(nrow(outliers_lon) > 0) {
  cat("\nPotential longitude outliers:\n")
  for(i in 1:nrow(outliers_lon)) {
    cat(sprintf("  - %s: lon %.6f\n", outliers_lon$name[i], outliers_lon$longitude[i]))
  }
}

if(nrow(outliers_lat) == 0 && nrow(outliers_lon) == 0) {
  cat("✅ All coordinates appear to be within reasonable Corfu bounds\n")
}

cat("\n=== INTERACTIVE FUNCTIONS AVAILABLE ===\n")
cat("Use these functions to check specific hotels:\n")
cat("- find_hotel('hotel_name'): Find hotel index by name\n")
cat("- calculate_distance(idx1, idx2): Get distance between two hotels\n")
cat("- validate_isochrones('hotel_name', minutes, speed): Check walking coverage\n")
cat("\nExample: calculate_distance(1, 5)\n")
cat("Example: validate_isochrones('Corfu Palace', 20, 5)\n")