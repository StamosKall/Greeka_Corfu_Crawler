# Greeka Corfu Hotels Crawler & Geographic Map Generator

A comprehensive web crawler and mapping system that extracts hotel information from Greeka's Corfu hotels listing page and generates high-quality geographic maps showing hotel distribution across Corfu island.

## 🚀 Features

### 🕷️ **Web Crawling**
- **Comprehensive Data Extraction**: Extracts hotel name, star rating, review scores, contact information, and coordinates
- **Advanced Coordinate Extraction**: 99.3% success rate extracting precise latitude/longitude coordinates from map data
- **Website Detection Enhancement**: Automatically detects and validates official hotel websites
- **Robust Error Handling**: Handles network failures, missing data, and parsing errors gracefully
- **Respectful Crawling**: Implements delays and retry logic to avoid overwhelming the target server

### 🗺️ **Geographic Mapping**
- **Real Corfu Island Map**: Uses OpenStreetMap data for accurate geographic boundaries
- **Professional Cartography**: Publication-ready maps with proper styling and legends
- **Hotel Distribution Visualization**: Color-coded by star rating with size variations
- **Interactive & Static Formats**: Both PNG images and HTML interactive maps
- **Strategic Info Positioning**: Statistics and legends positioned in sea areas

### 📊 **Data Analysis**
- **Comprehensive Statistics**: Detailed analysis of hotel distribution and ratings
- **Data Quality Reporting**: Coverage analysis and validation metrics
- **Multiple Output Formats**: CSV, JSON, and visual map formats
- **Detailed Logging**: Complete audit trail of all operations

## Data Fields Extracted

For each hotel, the crawler attempts to extract:

| Field | Description | Example |
|-------|-------------|---------|
| **name** | Hotel name | "Delfino Blu Boutique Hotel" |
| **official_website** | Hotel's official website URL | "https://www.delfinoblu.gr/" |
| **address** | Hotel address/location | "Agios Stefanos Avliotes, Corfu, Greece" |
| **star_rating** | Hotel star rating (1-5) | "4" |
| **review_score** | Average review score out of 5 | "4.2" |
| **number_of_reviews** | Total number of reviews | "87" |
| **phone_number** | Hotel contact phone number | "+30 26630 51012" |
| **latitude** | Geographic latitude coordinate | "39.7912" |
| **longitude** | Geographic longitude coordinate | "19.6858" |
| **detail_url** | URL of the hotel's detail page | "https://www.greeka.com/ionian/corfu/hotels/..." |

## 📁 Project Structure

```
Greeka_Corfu_Crawler/
├── src/                            # Source code
│   ├── crawler.py                  # Main hotel data crawler
│   ├── detect_websites.py          # Website detection enhancement  
│   ├── analyze_data.py             # Data analysis and reporting
│   ├── visualize_map.py            # Basic map visualization
│   ├── ultimate_corfu_map.py       # 🌟 Ultimate map generator with real OSM data
│   └── cache/                      # Cached data for performance
├── data/                           # Data files and outputs
│   ├── hotels.csv                  # Hotel dataset (CSV format)
│   ├── hotels.json                 # Hotel dataset (JSON format)
│   ├── ultimate_corfu_map.png      # 🗺️ High-quality Corfu map with hotels
│   ├── corfu_hotels_map.html       # Interactive HTML map (backup)
│   └── real_corfu_hotels_map.html  # Real geographic HTML map (backup)
├── config/                         # Configuration files
│   └── config.ini                  # Configuration settings
├── docs/                           # Documentation
│   ├── WEBSITE_DETECTION_RESULTS.md
│   └── CLEANUP_SUMMARY.md
├── .github/                        # GitHub Actions
│   └── workflows/
│       └── crawler.yml             # Automated workflow
├── requirements.txt                # Python dependencies
├── setup.py                        # Package setup
├── README.md                       # This file
├── LICENSE                         # License information
└── .gitignore                      # Git ignore patterns
```

## 🚀 Quick Start

### 1. **Installation**
```bash
# Clone the repository
git clone https://github.com/StamosKall/Greeka_Corfu_Crawler.git
cd Greeka_Corfu_Crawler

# Install dependencies
pip install -r requirements.txt
```

### 2. **Run Hotel Data Crawler**
```bash
# Crawl hotel data from Greeka
cd src
python crawler.py

# Output: hotels.json and hotels.csv in data/ directory
```

### 3. **Generate Ultimate Corfu Map**
```bash
# Create high-quality geographic map
python ultimate_corfu_map.py

# Output: ultimate_corfu_map.png in data/ directory
```

### 4. **Additional Tools**
```bash
# Analyze data quality and statistics
python analyze_data.py

# Detect and validate hotel websites  
python detect_websites.py

# Generate basic visualizations
python visualize_map.py
```

## 🗺️ Map Generation Features

### **Ultimate Corfu Map (`ultimate_corfu_map.py`)**
- **Real Geographic Data**: Downloads actual Corfu boundaries from OpenStreetMap
- **Street Network**: Includes real roads and paths
- **Professional Styling**: Publication-ready cartographic design
- **Smart Positioning**: Info boxes positioned in sea areas only
- **High Resolution**: 300 DPI PNG suitable for printing
- **Color Coding**: Hotels colored by star rating (🔴 5-star to 🟡 1-star)
- **Size Variations**: Marker sizes reflect hotel quality

### **Map Components**
- **📊 Statistics Box** (Bottom-Left): Hotel counts, data source info
- **🏨 Legend** (Top-Right): Star rating distribution with counts
- **🏝️ Island Shape**: Accurate Corfu coastline and geography  
- **🌊 Sea Background**: Blue background representing Ionian Sea
- **📍 Hotel Markers**: 141 hotels plotted with precise coordinates

## 🔧 How the System Works

### **Data Extraction Pipeline**
1. **Web Crawling**: Scrapes hotel data from Greeka.com
2. **Coordinate Extraction**: 99.3% success rate getting GPS coordinates
3. **Data Validation**: Cleans and validates all extracted information
4. **Geographic Mapping**: Overlays hotels on real Corfu map

### **Technology Stack**
- **Web Scraping**: `requests`, `beautifulsoup4`, `lxml`
- **Geographic Data**: `osmnx`, `geopandas` (OpenStreetMap integration)
- **Visualization**: `matplotlib`, `numpy` (cartographic rendering)
- **Data Processing**: `pandas`, `json` (data manipulation)
- **Caching**: Smart caching system for improved performance

## 📊 Results & Performance

### **Dataset Overview**
- **🏨 Total Hotels**: 142 hotels discovered
- **📍 Geocoding Success**: 141/142 hotels (99.3% coverage)
- **⭐ Star Rating Distribution**:
  - 5⭐ Hotels: 0 (0%)
  - 4⭐ Hotels: 25 (17.7%)
  - 3⭐ Hotels: 30 (21.3%)
  - 2⭐ Hotels: 12 (8.5%)
  - 1⭐ Hotels: 1 (0.7%)
  - No Rating: 73 (51.8%)

### **Data Quality Metrics**
- **📞 Phone Numbers**: High extraction rate
- **🌐 Websites**: Official website detection and validation
- **📮 Addresses**: Complete location information
- **⭐ Reviews**: Review scores and counts where available
- **🗺️ Coordinates**: Precise GPS coordinates for mapping

### **Geographic Coverage**
- **🏝️ Island-wide**: Hotels distributed across entire Corfu
- **🏖️ Beach Areas**: Major tourist destinations covered
- **🏔️ Mountain Regions**: Interior and hillside locations included
- **🏘️ Town Centers**: Urban hotel concentrations mapped

## 🛠️ System Requirements

### **Prerequisites**
- Python 3.10 or higher
- Internet connection for data crawling and map generation
- ~100MB disk space for dependencies and data

### **Dependencies**
- `requests` - HTTP client for web scraping
- `beautifulsoup4` - HTML parsing and extraction
- `lxml` - Fast XML/HTML parser
- `matplotlib` - Map visualization and graphics
- `numpy` - Numerical computations
- `osmnx` - OpenStreetMap data integration
- `geopandas` - Geographic data processing
- **`hotels.json`**: Structured data in JSON format (API-friendly)
- **`crawler.log`**: Detailed execution log with timestamps

### Expected Runtime

- **Typical execution time**: 5-15 minutes (depends on number of hotels and network speed)
- **Network requests**: ~100-200 HTTP requests (varies by hotel count)
- **Rate limiting**: 1-2 second delays between requests to be server-friendly

## Enhanced Tools

### Website Detection Enhancement
```bash
cd src
python detect_websites.py
```
Scans all hotel pages for official websites that may have been missed in the initial crawl:
- Uses multiple detection methods (JSON-LD, contact sections, external links)
- Validates website authenticity and accessibility
- Updates the dataset with newly found websites
- Provides detailed logging and summary reports

### Data Analysis & Reporting
```bash
cd src
python analyze_data.py [../data/hotels.json]
```
Generates comprehensive data quality analysis:
- Data completeness statistics for all fields
- Geographic distribution analysis
- Review score distributions and top-rated hotels
- Overall data quality scoring
- Exports detailed analysis report to `docs/`

### Interactive Map Visualization
```bash
cd src
python visualize_map.py
```
Creates an interactive map showing hotel locations:
- Plots all hotels with valid coordinates on an interactive map
- Color-coded markers based on star ratings
- Click-to-view hotel details and websites
- Exports as `data/corfu_hotels_map.html` for web viewing

## Running via GitHub Actions

The repository includes a GitHub Actions workflow that automatically runs the crawler and stores results as artifacts.

### Automatic Execution

The workflow runs automatically:
- **Daily at 2:00 AM UTC** (scheduled)
- **On every push to main branch** (manual trigger)
- **Manual workflow dispatch** (on-demand)

### Manual Trigger

1. Go to the **Actions** tab in your GitHub repository
## 📋 Sample Data Output

### **Hotel Dataset Example**
```json
{
  "name": "Delfino Blu Hotel in Agios Stefanos Avliotes, Corfu",
  "official_website": "https://corfudelfinoblu.reserve-online.net/",
  "address": "Corfu, Agios Stefanos Avliotes",
  "star_rating": "4",
  "review_score": "5.0",
  "number_of_reviews": "1", 
  "phone_number": "00302118503006",
  "latitude": "39.75687374887841",
  "longitude": "19.644466638565063",
  "detail_url": "https://www.greeka.com/ionian/corfu/hotels/..."
}
```

### **Map Output Example**
The `ultimate_corfu_map.png` shows:
- **🏝️ Accurate Corfu island shape** with real coastline
- **🏨 141 hotel locations** plotted as colored markers
- **📊 Statistics panel** (bottom-left): Hotel counts and data info
- **🎨 Legend panel** (top-right): Star rating distribution
- **🌊 Professional styling** with sea background and clean layout

## ⚙️ Configuration Options

### **Crawler Settings** (`config/config.ini`)
```ini
[crawler]
base_url = https://www.greeka.com/ionian/corfu/hotels/
delay_between_requests = 1
delay_between_hotels = 2
max_retries = 3
timeout = 30
```

### **Map Customization** (`ultimate_corfu_map.py`)
- **Colors**: Modify `get_star_color()` function
- **Sizes**: Adjust marker sizes in scatter plot section
- **Positioning**: Change info box locations via `bbox_to_anchor`
- **Resolution**: Modify `dpi` parameter in `savefig()`

# Retry settings
retries = 3        # Number of retry attempts for failed requests

# Timeout settings
timeout = 30       # Request timeout in seconds
```

### Adding Custom Fields

To extract additional fields:

1. Add the field to the `Hotel` dataclass
2. Implement extraction logic in `extract_hotel_details()`
3. Update the CSV fieldnames list in `save_to_csv()`

### Custom Output Formats

The modular design allows easy addition of new output formats:

```python
def save_to_xml(self, filename: str = "hotels.xml"):
    # Implementation for XML output
    pass
```

## Error Handling & Troubleshooting

### Common Issues

1. **Network Connectivity**: Ensure stable internet connection
2. **Rate Limiting**: The crawler includes delays; avoid reducing them
3. **Website Changes**: Greeka may update their HTML structure
4. **Missing Data**: Not all hotels have complete information

### Debug Mode

Enable verbose logging by modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Handling Failures

The crawler includes robust error handling:
- **Network failures**: Automatic retries with exponential backoff
- **Parsing errors**: Graceful degradation with logging
- **Missing fields**: Empty strings for unavailable data

## Technical Implementation Details

### Web Scraping Strategy

1. **Respectful Crawling**: Implements delays and user-agent headers
2. **Multiple Parsing Methods**: Uses various techniques to extract each field
3. **Coordinate Extraction**: Advanced parsing of Google Maps embeds
## 🔍 Use Cases & Applications

### **Tourism & Hospitality**
- **Market Research**: Analyze hotel distribution and pricing patterns
- **Competition Analysis**: Study competitor locations and ratings
- **Tourism Planning**: Identify accommodation gaps and opportunities

### **Academic & Research**
- **Geographic Studies**: Tourism distribution analysis
- **Data Science Projects**: Real-world dataset for analysis
- **Web Scraping Education**: Learning modern scraping techniques

### **Business Intelligence**
- **Location Analytics**: Understand hotel clustering patterns  
- **Market Mapping**: Visual representation of hospitality landscape
- **Data Visualization**: Professional cartographic presentations

## 🚨 Important Notes

### **Ethical Web Scraping**
- ✅ **Respectful Delays**: 1-2 second delays between requests
- ✅ **Public Data Only**: Extracts publicly available information
- ✅ **No Overloading**: Reasonable request rates to avoid server strain
- ✅ **Compliance**: Users should review target site's terms of service

### **Data Accuracy**
- **Dynamic Content**: Website changes may affect extraction accuracy
- **Validation Recommended**: Cross-check critical data points
- **Update Frequency**: Data reflects website state at crawl time

## 🤝 Contributing

We welcome contributions! Here's how to get involved:

### **Bug Reports**
- Use GitHub Issues for bug reports
- Include detailed reproduction steps
- Provide error messages and logs

### **Feature Requests** 
- Suggest new functionality via GitHub Issues
- Explain the use case and expected behavior
- Consider implementation complexity

### **Code Contributions**
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Write tests for new functionality
4. Ensure code follows existing style
5. Submit Pull Request with clear description

## 📄 License & Legal

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### **Disclaimer**
This tool is for educational and research purposes. Users are responsible for:
- Complying with target website's terms of service
- Following applicable laws and regulations  
- Using data ethically and responsibly

## 🙋 Support & Community

- **🐛 Issues**: [GitHub Issues](https://github.com/StamosKall/Greeka_Corfu_Crawler/issues)
- **💡 Discussions**: [GitHub Discussions](https://github.com/StamosKall/Greeka_Corfu_Crawler/discussions)
- **📧 Contact**: Open an issue for direct communication

---

<div align="center">

**⭐ Star this repository if you found it useful!** 

Made with ❤️ for the open source community

</div>