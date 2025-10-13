# Caching Functions for OSM Data
# ===============================
# Avoid re-downloading OSM data by caching to disk
# Author: Added for performance
# Date: 2025

# Create cache directory with absolute path
get_cache_dir <- function() {
  # Try to find the project root
  script_dir <- getwd()

  # Look for data directory
  possible_paths <- c(
    "../../data/osm_cache",
    "../../../data/osm_cache",
    "data/osm_cache",
    file.path(dirname(dirname(script_dir)), "data", "osm_cache")
  )

  for (path in possible_paths) {
    abs_path <- normalizePath(path, mustWork = FALSE)
    parent_dir <- dirname(abs_path)
    if (dir.exists(parent_dir) || dir.exists(dirname(parent_dir))) {
      if (!dir.exists(abs_path)) {
        dir.create(abs_path, recursive = TRUE, showWarnings = FALSE)
      }
      if (dir.exists(abs_path)) {
        return(abs_path)
      }
    }
  }

  # Fallback: create in temp directory
  temp_cache <- file.path(tempdir(), "osm_cache")
  dir.create(temp_cache, recursive = TRUE, showWarnings = FALSE)
  return(temp_cache)
}

CACHE_DIR <- get_cache_dir()

# Generate cache key from bbox
generate_cache_key <- function(bbox, data_type = "boundary") {
  # Create a unique hash based on bbox and type
  key_string <- paste(data_type, paste(bbox, collapse = "_"), sep = "_")
  key_hash <- digest::digest(key_string, algo = "md5")
  return(key_hash)
}

# Save sf object to cache
save_to_cache <- function(data, cache_key, verbose = TRUE) {
  if (is.null(data)) return(FALSE)

  cache_file <- file.path(CACHE_DIR, paste0(cache_key, ".rds"))

  tryCatch({
    saveRDS(data, cache_file)
    if (verbose) cat(sprintf("💾 Cached data saved: %s\n", cache_key))
    return(TRUE)
  }, error = function(e) {
    if (verbose) cat(sprintf("⚠️  Cache save failed: %s\n", e$message))
    return(FALSE)
  })
}

# Load sf object from cache
load_from_cache <- function(cache_key, verbose = TRUE) {
  cache_file <- file.path(CACHE_DIR, paste0(cache_key, ".rds"))

  if (file.exists(cache_file)) {
    tryCatch({
      data <- readRDS(cache_file)
      if (verbose) cat(sprintf("📦 Loaded from cache: %s\n", cache_key))
      return(data)
    }, error = function(e) {
      if (verbose) cat(sprintf("⚠️  Cache load failed: %s\n", e$message))
      return(NULL)
    })
  }

  return(NULL)
}

# Check if cache exists
cache_exists <- function(cache_key) {
  cache_file <- file.path(CACHE_DIR, paste0(cache_key, ".rds"))
  return(file.exists(cache_file))
}

# Clear cache (optional)
clear_cache <- function(data_type = NULL, verbose = TRUE) {
  if (is.null(data_type)) {
    # Clear all cache
    cache_files <- list.files(CACHE_DIR, pattern = "\\.rds$", full.names = TRUE)
  } else {
    # Clear specific type
    cache_files <- list.files(CACHE_DIR, pattern = paste0("^", data_type),
                             full.names = TRUE)
  }

  if (length(cache_files) > 0) {
    file.remove(cache_files)
    if (verbose) cat(sprintf("🗑️  Cleared %d cache files\n", length(cache_files)))
  } else {
    if (verbose) cat("✓ No cache files to clear\n")
  }
}

# Get cache info
cache_info <- function() {
  cache_files <- list.files(CACHE_DIR, pattern = "\\.rds$", full.names = TRUE)

  if (length(cache_files) == 0) {
    cat("📁 Cache is empty\n")
    return(invisible(NULL))
  }

  info <- data.frame(
    file = basename(cache_files),
    size_kb = file.size(cache_files) / 1024,
    modified = file.mtime(cache_files)
  )

  cat(sprintf("📁 Cache directory: %s\n", CACHE_DIR))
  cat(sprintf("📦 Cached files: %d\n", nrow(info)))
  cat(sprintf("💾 Total size: %.1f KB\n\n", sum(info$size_kb)))

  print(info)
  return(invisible(info))
}