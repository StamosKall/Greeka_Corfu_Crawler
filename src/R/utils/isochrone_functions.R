# Isochrone Generation Utilities
# ===============================
# Functions for creating walking distance isochrones
# Author: Reorganized from multiple R scripts
# Date: 2025

# Constants
WALKING_SPEED_KMH <- 5  # Average walking speed in km/h

# Create simple circular isochrone (buffer method)
create_circular_isochrone <- function(center_lat, center_lon, time_minutes,
                                    walking_speed = WALKING_SPEED_KMH) {
  # Calculate walking distance in meters
  walking_distance_km <- (walking_speed * time_minutes) / 60
  walking_distance_m <- walking_distance_km * 1000

  # Create center point
  center_point <- sf::st_sfc(sf::st_point(c(center_lon, center_lat)), crs = 4326)

  # Project to UTM for accurate distance calculation
  center_projected <- sf::st_transform(center_point, crs = 32634)  # UTM zone 34N

  # Create buffer
  isochrone_projected <- sf::st_buffer(center_projected, dist = walking_distance_m)

  # Transform back to WGS84
  sf::st_transform(isochrone_projected, crs = 4326)
}

# Create network-based isochrone
create_network_isochrone <- function(center_lat, center_lon, time_minutes,
                                   network_sf, walking_speed = WALKING_SPEED_KMH) {
  if (is.null(network_sf) || nrow(network_sf) == 0) {
    # Fallback to circular isochrone
    return(create_circular_isochrone(center_lat, center_lon, time_minutes, walking_speed))
  }

  tryCatch({
    # Calculate maximum walking distance
    max_distance_km <- (time_minutes / 60) * walking_speed

    # Create center point
    center_point <- sf::st_sfc(sf::st_point(c(center_lon, center_lat)), crs = 4326)

    # Find nearby network segments
    center_buffer <- sf::st_buffer(
      sf::st_transform(center_point, 3857),
      dist = max_distance_km * 1000
    )
    center_buffer_wgs84 <- sf::st_transform(center_buffer, 4326)

    # Get network segments within buffer
    nearby_segments <- sf::st_filter(network_sf, center_buffer_wgs84)

    if (nrow(nearby_segments) > 0) {
      # Create convex hull around nearby segments
      segment_points <- sf::st_cast(nearby_segments, "POINT")
      if (nrow(segment_points) >= 3) {
        hull <- sf::st_convex_hull(sf::st_union(segment_points))
        return(hull)
      }
    }

    # Fallback to circular if network method fails
    return(create_circular_isochrone(center_lat, center_lon, time_minutes, walking_speed))

  }, error = function(e) {
    # On error, use circular isochrone
    return(create_circular_isochrone(center_lat, center_lon, time_minutes, walking_speed))
  })
}

# Create isochrones for multiple hotels
create_hotel_isochrones <- function(hotels_sf, time_intervals, network_sf = NULL,
                                  method = "circular", walking_speed = WALKING_SPEED_KMH,
                                  verbose = TRUE) {

  if (verbose) {
    cat(sprintf("🚶 Creating isochrones for %d hotels using %s method...\n",
                nrow(hotels_sf), method))
  }

  all_isochrones <- list()
  isochrone_id <- 1

  for (i in 1:nrow(hotels_sf)) {
    hotel <- hotels_sf[i, ]
    hotel_coords <- sf::st_coordinates(hotel)
    hotel_lon <- hotel_coords[1]
    hotel_lat <- hotel_coords[2]

    if (verbose && i %% 10 == 0) {
      cat(sprintf("   Processing hotel %d/%d...\n", i, nrow(hotels_sf)))
    }

    for (time_min in time_intervals) {
      # Create isochrone based on method
      if (method == "network" && !is.null(network_sf)) {
        isochrone <- create_network_isochrone(
          hotel_lat, hotel_lon, time_min, network_sf, walking_speed
        )
      } else {
        isochrone <- create_circular_isochrone(
          hotel_lat, hotel_lon, time_min, walking_speed
        )
      }

      if (!is.null(isochrone)) {
        # Create data frame with attributes
        isochrone_df <- data.frame(
          id = isochrone_id,
          hotel_id = i,
          hotel_name = hotel$name,
          time_min = time_min,
          geometry = isochrone
        )

        all_isochrones[[isochrone_id]] <- sf::st_sf(isochrone_df)
        isochrone_id <- isochrone_id + 1
      }
    }
  }

  if (length(all_isochrones) == 0) {
    if (verbose) cat("❌ No isochrones created\n")
    return(NULL)
  }

  # Combine all isochrones
  combined_isochrones <- do.call(rbind, all_isochrones)

  if (verbose) {
    cat(sprintf("✅ Created %d isochrone zones from %d hotels\n",
                nrow(combined_isochrones), nrow(hotels_sf)))
  }

  return(combined_isochrones)
}

# Create smooth density-based isochrones
create_smooth_isochrones <- function(hotels_sf, time_intervals,
                                   resolution = 100, walking_speed = WALKING_SPEED_KMH) {
  # Get bounding box
  bbox <- sf::st_bbox(hotels_sf)

  # Create grid
  x_seq <- seq(bbox["xmin"], bbox["xmax"], length.out = resolution)
  y_seq <- seq(bbox["ymin"], bbox["ymax"], length.out = resolution)
  grid <- expand.grid(lon = x_seq, lat = y_seq)

  # Calculate minimum distance to any hotel for each grid point
  hotel_coords <- sf::st_coordinates(hotels_sf)

  grid$min_distance <- apply(grid, 1, function(point) {
    min(sqrt((hotel_coords[, 1] - point["lon"])^2 +
             (hotel_coords[, 2] - point["lat"])^2)) * 111  # Rough conversion to km
  })

  # Convert distance to walking time
  grid$walking_time <- (grid$min_distance / walking_speed) * 60

  # Create contours for each time interval
  contours <- list()
  for (time_min in time_intervals) {
    grid_subset <- grid[grid$walking_time <= time_min, ]
    if (nrow(grid_subset) > 3) {
      points_sf <- sf::st_as_sf(grid_subset, coords = c("lon", "lat"), crs = 4326)
      hull <- sf::st_convex_hull(sf::st_union(points_sf))

      contour_df <- data.frame(
        time_min = time_min,
        geometry = hull
      )
      contours[[as.character(time_min)]] <- sf::st_sf(contour_df)
    }
  }

  if (length(contours) > 0) {
    return(do.call(rbind, contours))
  } else {
    return(NULL)
  }
}

# Create polygon-based isochrones with land clipping
create_polygon_isochrones <- function(hotels_sf, land_boundary, time_intervals,
                                    walking_speed = WALKING_SPEED_KMH) {
  isochrones <- create_hotel_isochrones(
    hotels_sf, time_intervals,
    method = "circular",
    walking_speed = walking_speed,
    verbose = FALSE
  )

  if (!is.null(isochrones) && !is.null(land_boundary)) {
    # Clip isochrones to land boundary
    tryCatch({
      isochrones_clipped <- sf::st_intersection(isochrones, land_boundary)
      return(isochrones_clipped)
    }, error = function(e) {
      # Return unclipped if intersection fails
      return(isochrones)
    })
  }

  return(isochrones)
}

# Merge overlapping isochrones for the same time interval
merge_isochrones_by_time <- function(isochrones_sf) {
  time_intervals <- unique(isochrones_sf$time_min)
  merged_list <- list()

  for (time_min in time_intervals) {
    time_subset <- isochrones_sf[isochrones_sf$time_min == time_min, ]
    if (nrow(time_subset) > 0) {
      # Union all geometries for this time interval
      merged_geom <- sf::st_union(time_subset)

      merged_df <- data.frame(
        time_min = time_min,
        hotel_count = nrow(time_subset),
        geometry = merged_geom
      )
      merged_list[[as.character(time_min)]] <- sf::st_sf(merged_df)
    }
  }

  if (length(merged_list) > 0) {
    return(do.call(rbind, merged_list))
  } else {
    return(NULL)
  }
}