# Quick Start Guide - Isochrone Maps

## 🚀 Running the Scripts

### **Simple Method** (Recommended)

From the project root:

```bash
cd src/R
Rscript run_isochrones.R
```

Process different numbers of hotels:

```bash
# Process 50 hotels (faster)
Rscript run_isochrones.R 50

# Process all 141 hotels
Rscript run_isochrones.R 141

# Process 10 hotels (testing)
Rscript run_isochrones.R 10
```

### **Using Examples Directory**

```bash
cd src/R
Rscript examples/land_clipped_isochrones.R
```

### **Make Script Executable** (Optional)

```bash
chmod +x run_isochrones.R
./run_isochrones.R 50
```

## 📁 Output

Maps are saved to: `data/isochrones_<N>_hotels.png`

For example:
- `data/isochrones_50_hotels.png`
- `data/isochrones_141_hotels.png`

## 🎯 Configuration

Edit `run_isochrones.R` to customize:

```r
CONFIG <- list(
  max_hotels = 141,
  time_intervals = c(5, 10, 15, 30, 60),  # Walking times in minutes
  map_width = 16,
  map_height = 20,
  dpi = 300  # Resolution
)
```

## ⚡ Performance

### First Run
- Downloads OSM data (30-60 seconds)
- Creates cache
- Generates map

### Subsequent Runs
- Uses cached OSM data (<1 second)
- Only regenerates map
- Much faster!

### Speed Tips

1. **Start small**: Test with 10-20 hotels first
2. **Use cache**: Let the first run complete to build cache
3. **Adjust DPI**: Lower DPI = faster (try 150 for drafts)

## 🗂️ Cache Management

### Check cache status:

```r
source("utils/load_utils.R")
cache_info()
```

### Clear cache:

```r
clear_cache()  # Clear all
clear_cache("boundary")  # Clear boundary only
clear_cache("network")  # Clear network only
```

## 🎨 Map Features

Generated maps include:
- ✅ Land boundaries (beige)
- ✅ Sea (light blue)
- ✅ Walking zones (green gradient)
- ✅ Hotel locations (red dots)
- ✅ Clipped at coastline (no sea overlap)

## 🔧 Troubleshooting

### "File not found" errors

Make sure you're in the `src/R` directory:
```bash
cd src/R
pwd  # Should show .../src/R
```

### Missing packages

```bash
Rscript install_dependencies.R
```

### Slow OSM downloads

- First run is slow (normal)
- Subsequent runs use cache (fast)
- Check internet connection

### Cache not working

```r
# Verify digest package
install.packages("digest")

# Check cache directory
dir.exists("../../data/osm_cache")
```

## 📊 Example Session

```bash
# Navigate to R directory
cd /path/to/Greeka_Corfu_Crawler/src/R

# Install dependencies (first time only)
Rscript install_dependencies.R

# Generate map with 30 hotels
Rscript run_isochrones.R 30

# View the output
open ../../data/isochrones_30_hotels.png

# Generate full map
Rscript run_isochrones.R 141

# Check cache
Rscript -e "source('utils/load_utils.R'); cache_info()"
```

## 🎓 Advanced Usage

### Custom Time Intervals

Edit the script to change walking times:

```r
time_intervals = c(5, 10, 20, 45)  # Custom times
```

### Different Colors

Modify the `time_colors` in the script:

```r
time_colors <- c(
  "5" = "#ff0000",   # Red
  "10" = "#00ff00",  # Green
  "15" = "#0000ff"   # Blue
)
```

### Multiple Maps

Run multiple times with different parameters:

```bash
Rscript run_isochrones.R 50
Rscript run_isochrones.R 100
Rscript run_isochrones.R 141
```

## 📞 Need Help?

- Check `README.md` for project overview
- Check `CACHING_README.md` for cache details
- Review `examples/` for code samples