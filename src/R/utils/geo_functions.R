# Geographic and Spatial Utilities for Corfu Analysis
# ====================================================
# Shared geographic functions for maps and spatial analysis
# Author: Reorganized from multiple R scripts
# Date: 2025

# Function to get Corfu island boundary from OpenStreetMap (with caching)
get_corfu_boundary <- function(bbox = NULL, verbose = TRUE, use_cache = TRUE) {
  if (verbose) cat("🗺️  Getting Corfu island boundary...\n")

  # Default Corfu bbox if not provided
  if (is.null(bbox)) {
    bbox <- c(19.3, 39.3, 20.2, 39.9)
  }

  # Try cache first
  if (use_cache && exists("generate_cache_key")) {
    cache_key <- generate_cache_key(bbox, "boundary")
    cached_data <- load_from_cache(cache_key, verbose = verbose)
    if (!is.null(cached_data)) {
      return(cached_data)
    }
  }

  boundary <- NULL

  # Try Method 1: Administrative boundary
  tryCatch({
    corfu_query <- osmdata::opq(bbox = bbox) %>%
      osmdata::add_osm_feature(key = "admin_level", value = "8") %>%
      osmdata::add_osm_feature(key = "name:en", value = "Corfu")

    result <- osmdata::osmdata_sf(corfu_query)

    if (!is.null(result$osm_multipolygons) && nrow(result$osm_multipolygons) > 0) {
      boundary <- result$osm_multipolygons[1, ]
      if (verbose) cat("✅ Found Corfu administrative boundary\n")
      # Save to cache
      if (use_cache && exists("save_to_cache")) {
        save_to_cache(boundary, cache_key, verbose = verbose)
      }
      return(boundary)
    }
  }, error = function(e) {
    if (verbose) cat("⚠️  Admin boundary method failed, trying alternative...\n")
  })

  # Try Method 2: By Greek name
  tryCatch({
    corfu_query <- osmdata::opq(bbox = bbox) %>%
      osmdata::add_osm_feature(key = "name", value = "Κέρκυρα") %>%
      osmdata::add_osm_feature(key = "admin_level", value = "7")

    result <- osmdata::osmdata_sf(corfu_query)

    if (!is.null(result$osm_multipolygons) && nrow(result$osm_multipolygons) > 0) {
      boundary <- result$osm_multipolygons[1, ]
      if (verbose) cat("✅ Found Corfu boundary by Greek name\n")
      return(boundary)
    }
  }, error = function(e) {
    if (verbose) cat("⚠️  Greek name method failed\n")
  })

  # Try Method 3: Coastline approach
  tryCatch({
    coastline_query <- osmdata::opq(bbox = bbox) %>%
      osmdata::add_osm_feature(key = "natural", value = "coastline")

    coastline_result <- osmdata::osmdata_sf(coastline_query)

    if (!is.null(coastline_result$osm_lines) && nrow(coastline_result$osm_lines) > 0) {
      coastlines_combined <- sf::st_union(coastline_result$osm_lines)
      coastlines_poly <- sf::st_polygonize(coastlines_combined)

      if (length(coastlines_poly) > 0) {
        polys <- sf::st_collection_extract(coastlines_poly, "POLYGON")
        if (length(polys) > 0) {
          areas <- sf::st_area(polys)
          boundary <- polys[which.max(areas)]
          if (verbose) cat("✅ Created boundary from coastlines\n")
          return(boundary)
        }
      }
    }
  }, error = function(e) {
    if (verbose) cat("⚠️  Coastline method failed\n")
  })

  if (verbose) cat("❌ Could not retrieve Corfu boundary\n")
  return(NULL)
}

# Function to get walking network from OSM (with caching)
get_walking_network <- function(bbox, verbose = TRUE, use_cache = TRUE) {
  if (verbose) cat("🚶 Downloading walking network...\n")

  # Try cache first
  if (use_cache && exists("generate_cache_key")) {
    cache_key <- generate_cache_key(bbox, "network")
    cached_data <- load_from_cache(cache_key, verbose = verbose)
    if (!is.null(cached_data)) {
      if (verbose) cat(sprintf("✅ Walking network from cache: %d segments\n",
                              nrow(cached_data)))
      return(cached_data)
    }
  }

  tryCatch({
    query <- osmdata::opq(bbox = bbox) %>%
      osmdata::add_osm_feature(
        key = "highway",
        value = c("primary", "secondary", "tertiary", "residential",
                 "footway", "path", "steps", "pedestrian", "living_street",
                 "track", "unclassified", "service")
      )

    network <- osmdata::osmdata_sf(query)

    if (!is.null(network$osm_lines) && nrow(network$osm_lines) > 0) {
      if (verbose) cat(sprintf("✅ Walking network downloaded: %d segments\n",
                              nrow(network$osm_lines)))
      # Save to cache
      if (use_cache && exists("save_to_cache")) {
        save_to_cache(network$osm_lines, cache_key, verbose = verbose)
      }
      return(network$osm_lines)
    } else {
      if (verbose) cat("❌ No network data found\n")
      return(NULL)
    }
  }, error = function(e) {
    if (verbose) cat(sprintf("❌ Error downloading network: %s\n", e$message))
    return(NULL)
  })
}

# Calculate haversine distance between two points
calculate_haversine_distance <- function(lat1, lon1, lat2, lon2) {
  # Earth radius in kilometers
  R <- 6371

  # Convert to radians
  lat1_rad <- lat1 * pi / 180
  lat2_rad <- lat2 * pi / 180
  delta_lat <- (lat2 - lat1) * pi / 180
  delta_lon <- (lon2 - lon1) * pi / 180

  # Haversine formula
  a <- sin(delta_lat/2) * sin(delta_lat/2) +
       cos(lat1_rad) * cos(lat2_rad) *
       sin(delta_lon/2) * sin(delta_lon/2)
  c <- 2 * atan2(sqrt(a), sqrt(1-a))
  d <- R * c

  return(d)
}

# Calculate distance matrix between all hotels
calculate_distance_matrix <- function(hotels_data) {
  n <- nrow(hotels_data)
  dist_matrix <- matrix(0, n, n)

  for (i in 1:n) {
    for (j in 1:n) {
      if (i != j) {
        dist_matrix[i, j] <- calculate_haversine_distance(
          hotels_data$lat[i], hotels_data$lon[i],
          hotels_data$lat[j], hotels_data$lon[j]
        )
      }
    }
  }

  rownames(dist_matrix) <- hotels_data$name
  colnames(dist_matrix) <- hotels_data$name

  return(dist_matrix)
}

# Transform coordinates to projected CRS for accurate distance calculations
project_to_utm <- function(sf_object, zone = 34) {
  # UTM zone 34N covers Greece
  utm_crs <- paste0("+proj=utm +zone=", zone, " +datum=WGS84")
  sf::st_transform(sf_object, crs = utm_crs)
}

# Transform back to WGS84
project_to_wgs84 <- function(sf_object) {
  sf::st_transform(sf_object, crs = 4326)
}

# Create buffer around points (for simple isochrones)
create_buffer_meters <- function(points, distance_meters, projected_crs = 32634) {
  points_proj <- sf::st_transform(points, crs = projected_crs)
  buffer_proj <- sf::st_buffer(points_proj, dist = distance_meters)
  sf::st_transform(buffer_proj, crs = 4326)
}

# Find nearest neighbors
find_nearest_hotels <- function(hotel_index, distance_matrix, n = 5) {
  distances <- distance_matrix[hotel_index, ]
  distances[hotel_index] <- Inf  # Exclude self
  nearest_indices <- order(distances)[1:n]

  data.frame(
    index = nearest_indices,
    distance_km = distances[nearest_indices]
  )
}

# Calculate centroid of hotels
calculate_centroid <- function(hotels_data) {
  mean_lat <- mean(hotels_data$lat, na.rm = TRUE)
  mean_lon <- mean(hotels_data$lon, na.rm = TRUE)

  list(lat = mean_lat, lon = mean_lon)
}

# Check if point is within boundary
point_in_boundary <- function(point_lat, point_lon, boundary_sf) {
  if (is.null(boundary_sf)) return(TRUE)

  point <- sf::st_sfc(sf::st_point(c(point_lon, point_lat)), crs = 4326)
  sf::st_within(point, boundary_sf, sparse = FALSE)[1, 1]
}