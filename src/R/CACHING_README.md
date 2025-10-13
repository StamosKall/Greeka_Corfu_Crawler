# OSM Data Caching System

## Overview

The R utilities now include automatic caching of OpenStreetMap data to avoid repeated downloads. This significantly speeds up subsequent map generations.

## Features

### Cached Data Types

1. **Corfu Island Boundary** - Land boundary polygon
2. **Walking Network** - Road network segments for routing
3. **Other OSM Data** - Any geographic data can be cached

### Cache Location

- Cache directory: `data/osm_cache/`
- Files stored as `.rds` (R binary format)
- Automatic creation of cache directory

## Usage

### Automatic Caching (Default)

All geo functions use caching by default:

```r
# This will cache on first run, use cache on subsequent runs
boundary <- get_corfu_boundary(bbox)
network <- get_walking_network(bbox)
```

### Disable Caching

```r
# Disable cache for fresh download
boundary <- get_corfu_boundary(bbox, use_cache = FALSE)
network <- get_walking_network(bbox, use_cache = FALSE)
```

### Manual Cache Management

```r
# Check cache status
cache_info()

# Clear all cache
clear_cache()

# Clear specific type
clear_cache("boundary")
clear_cache("network")
```

## Benefits

### Speed Improvements

- **First Run**: 30-60 seconds (downloads from OSM)
- **Subsequent Runs**: <1 second (loads from cache)
- **Network Savings**: Reduces API calls to OpenStreetMap

### Storage

- Boundary data: ~50-200 KB
- Network data: ~500 KB - 5 MB (depending on area)
- Total cache size typically < 10 MB

## Cache Keys

Cache files are named using MD5 hashes of:
- Data type (boundary, network, etc.)
- Bounding box coordinates

Example: `network_19.3_39.3_20.2_39.9.rds`

## Implementation

### In Utility Functions

```r
# Pattern used in geo_functions.R
get_walking_network <- function(bbox, use_cache = TRUE) {
  # Try cache first
  if (use_cache) {
    cache_key <- generate_cache_key(bbox, "network")
    cached_data <- load_from_cache(cache_key)
    if (!is.null(cached_data)) {
      return(cached_data)
    }
  }

  # Download from OSM
  network <- download_osm_network(bbox)

  # Save to cache
  if (use_cache) {
    save_to_cache(network, cache_key)
  }

  return(network)
}
```

## Cache Invalidation

Cache files do NOT expire automatically. Clear cache to force fresh downloads:

- When OSM data is updated
- When bounding box changes
- For testing purposes

## Troubleshooting

### Cache Not Working

1. Check cache directory exists: `data/osm_cache/`
2. Check file permissions
3. Verify digest package installed

### Corrupted Cache

```r
# Clear and rebuild
clear_cache()
# Re-run your analysis
```

### Large Cache Size

```r
# Check what's cached
cache_info()

# Remove old/unused caches
clear_cache()
```

## Future Enhancements

Potential improvements:
- Cache expiration (TTL)
- Compression for large files
- Cache statistics tracking
- Partial cache invalidation