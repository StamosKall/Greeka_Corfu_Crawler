# Corfu Hotels Analysis - Utility Loader
# =======================================
# Load all shared utility functions
# Author: Reorganized code structure
# Date: 2025

# Get the directory of this script
utils_dir <- if (exists("utils_dir") && !is.null(utils_dir)) {
  utils_dir
} else {
  # Try to detect the utils directory
  if (file.exists("R/utils/load_utils.R")) {
    "R/utils"
  } else if (file.exists("utils/load_utils.R")) {
    "utils"
  } else if (file.exists("../R/utils/load_utils.R")) {
    "../R/utils"
  } else {
    dirname(sys.frame(1)$ofile)
  }
}

# Load all utility modules
cat("📦 Loading Corfu Hotels Analysis utilities...\n")

# Load required libraries first
suppressMessages({
  # Core packages
  if (!require(jsonlite)) install.packages("jsonlite")
  if (!require(sf)) install.packages("sf")
  if (!require(ggplot2)) install.packages("ggplot2")
  if (!require(dplyr)) install.packages("dplyr")

  # Spatial packages
  if (!require(osmdata)) install.packages("osmdata")

  library(jsonlite)
  library(sf)
  library(ggplot2)
  library(dplyr)
  library(osmdata)
})

# Install digest package for caching (if needed)
if (!require(digest, quietly = TRUE)) {
  install.packages("digest")
  library(digest)
}

# Source utility files
tryCatch({
  source(file.path(utils_dir, "cache_functions.R"))
  cat("  ✅ Loaded cache_functions.R\n")
}, error = function(e) {
  cat("  ⚠️  Could not load cache_functions.R:", e$message, "\n")
})

tryCatch({
  source(file.path(utils_dir, "data_loader.R"))
  cat("  ✅ Loaded data_loader.R\n")
}, error = function(e) {
  cat("  ⚠️  Could not load data_loader.R:", e$message, "\n")
})

tryCatch({
  source(file.path(utils_dir, "geo_functions.R"))
  cat("  ✅ Loaded geo_functions.R\n")
}, error = function(e) {
  cat("  ⚠️  Could not load geo_functions.R:", e$message, "\n")
})

tryCatch({
  source(file.path(utils_dir, "isochrone_functions.R"))
  cat("  ✅ Loaded isochrone_functions.R\n")
}, error = function(e) {
  cat("  ⚠️  Could not load isochrone_functions.R:", e$message, "\n")
})

tryCatch({
  source(file.path(utils_dir, "map_styling.R"))
  cat("  ✅ Loaded map_styling.R\n")
}, error = function(e) {
  cat("  ⚠️  Could not load map_styling.R:", e$message, "\n")
})

cat("✨ All utilities loaded successfully!\n\n")

# Export common constants
WALKING_SPEED_KMH <- 5
DEFAULT_TIME_INTERVALS <- c(5, 10, 15, 20, 30, 45, 60)
DEFAULT_OUTPUT_DIR <- "../data"

# Helper function to check if all utilities are loaded
check_utils_loaded <- function() {
  functions_to_check <- c(
    "load_hotel_data",
    "get_corfu_boundary",
    "create_circular_isochrone",
    "create_isochrone_map"
  )

  all_loaded <- all(sapply(functions_to_check, exists))

  if (all_loaded) {
    cat("✅ All utility functions are available\n")
  } else {
    missing <- functions_to_check[!sapply(functions_to_check, exists)]
    cat("⚠️  Missing functions:", paste(missing, collapse = ", "), "\n")
  }

  return(all_loaded)
}