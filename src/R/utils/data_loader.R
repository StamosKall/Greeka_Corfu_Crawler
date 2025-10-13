# Data Loading Utilities for Corfu Hotels Analysis
# =================================================
# Shared functions for loading and preparing hotel data
# Author: Reorganized from multiple R scripts
# Date: 2025

# Function to load and clean hotel data
load_hotel_data <- function(file_path = "../data/hotels.json", verbose = TRUE) {
  if (verbose) cat("📊 Loading hotel data...\n")

  # Check if file exists
  if (!file.exists(file_path)) {
    stop(paste("❌ Hotel data file not found:", file_path))
  }

  # Load JSON data
  hotels_raw <- jsonlite::fromJSON(file_path, flatten = TRUE)

  # Clean and validate data
  hotels_clean <- hotels_raw %>%
    dplyr::filter(!is.na(latitude) & !is.na(longitude)) %>%
    dplyr::filter(latitude != "" & longitude != "") %>%
    dplyr::mutate(
      lat = as.numeric(latitude),
      lon = as.numeric(longitude)
    ) %>%
    dplyr::filter(!is.na(lat) & !is.na(lon)) %>%
    dplyr::filter(lat > 35 & lat < 45) %>%  # Reasonable bounds for Greece
    dplyr::filter(lon > 15 & lon < 25) %>%
    dplyr::filter(lat >= 39.3 & lat <= 39.9) %>%  # Corfu specific bounds
    dplyr::filter(lon >= 19.3 & lon <= 20.2)

  if (verbose) {
    cat(sprintf("✅ Loaded %d hotels with valid coordinates\n", nrow(hotels_clean)))
    cat(sprintf("   Filtered out %d hotels with invalid data\n",
                nrow(hotels_raw) - nrow(hotels_clean)))
  }

  return(hotels_clean)
}

# Function to convert hotels to sf object
hotels_to_sf <- function(hotels_data, coords = c("lon", "lat"), crs = 4326) {
  sf::st_as_sf(hotels_data,
               coords = coords,
               crs = crs,
               remove = FALSE)
}

# Function to get hotels within a specific star rating
filter_by_stars <- function(hotels_data, star_ratings) {
  if (is.null(star_ratings) || length(star_ratings) == 0) {
    return(hotels_data)
  }

  hotels_data %>%
    dplyr::filter(star_rating %in% star_ratings)
}

# Function to get hotels within geographic bounds
filter_by_bounds <- function(hotels_data, lat_min, lat_max, lon_min, lon_max) {
  hotels_data %>%
    dplyr::filter(lat >= lat_min & lat <= lat_max) %>%
    dplyr::filter(lon >= lon_min & lon <= lon_max)
}

# Function to calculate bounding box with padding
calculate_bbox <- function(hotels_data, padding_percent = 0.15) {
  lat_range <- range(hotels_data$lat, na.rm = TRUE)
  lon_range <- range(hotels_data$lon, na.rm = TRUE)

  lat_padding <- (lat_range[2] - lat_range[1]) * padding_percent
  lon_padding <- (lon_range[2] - lon_range[1]) * padding_percent

  bbox <- c(
    xmin = lon_range[1] - lon_padding,
    ymin = lat_range[1] - lat_padding,
    xmax = lon_range[2] + lon_padding,
    ymax = lat_range[2] + lat_padding
  )

  return(bbox)
}

# Function to get hotel summary statistics
get_hotel_stats <- function(hotels_data, verbose = TRUE) {
  stats <- list(
    total = nrow(hotels_data),
    with_ratings = sum(!is.na(hotels_data$star_rating)),
    by_stars = table(hotels_data$star_rating, useNA = "ifany"),
    lat_range = range(hotels_data$lat, na.rm = TRUE),
    lon_range = range(hotels_data$lon, na.rm = TRUE),
    with_reviews = sum(!is.na(hotels_data$review_score))
  )

  if (verbose) {
    cat("\n📈 Hotel Statistics:\n")
    cat(sprintf("   Total hotels: %d\n", stats$total))
    cat(sprintf("   Hotels with ratings: %d\n", stats$with_ratings))
    cat(sprintf("   Hotels with reviews: %d\n", stats$with_reviews))
    cat("   Distribution by stars:\n")
    for (i in seq_along(stats$by_stars)) {
      cat(sprintf("      %s stars: %d\n",
                  names(stats$by_stars)[i],
                  stats$by_stars[i]))
    }
  }

  return(stats)
}