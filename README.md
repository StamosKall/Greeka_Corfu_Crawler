# Greeka Corfu Hotels Crawler

A comprehensive web crawler that extracts hotel information from Greeka's Corfu hotels listing page (https://www.greeka.com/ionian/corfu/hotels/). The crawler automatically navigates through all hotel listings, visits individual hotel pages, and extracts detailed information including ratings, reviews, contact details, and geographic coordinates.

## Features

- **Comprehensive Data Extraction**: Extracts hotel name, star rating, review scores, contact information, and coordinates
- **Advanced Coordinate Extraction**: 99.3% success rate extracting precise latitude/longitude coordinates from map data
- **Website Detection Enhancement**: Automatically detects and validates official hotel websites
- **Interactive Map Visualization**: Generates interactive maps showing hotel locations
- **Data Analysis & Reporting**: Comprehensive data quality analysis and statistics
- **Robust Error Handling**: Handles network failures, missing data, and parsing errors gracefully
- **Multiple Output Formats**: Saves data in both CSV and JSON formats
- **Respectful Crawling**: Implements delays and retry logic to avoid overwhelming the target server
- **Detailed Logging**: Comprehensive logging for monitoring and debugging
- **GitHub Actions Integration**: Automated crawling via GitHub Actions with artifact storage

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

## Project Structure

```
Greeka_Corfu_Crawler/
├── src/                            # Source code
│   ├── crawler.py                  # Main hotel data crawler
│   ├── detect_websites.py          # Website detection enhancement
│   ├── analyze_data.py             # Data analysis and reporting
│   └── visualize_map.py            # Interactive map generation
├── data/                           # Data files and outputs
│   ├── hotels.csv                  # Final hotel dataset (CSV)
│   ├── hotels.json                 # Final hotel dataset (JSON)
│   ├── corfu_hotels_map.html       # Interactive map visualization
│   └── *.log                       # Execution logs
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

## How the Crawler Works

### 1. **Main Listing Page Processing**
- Fetches the main Greeka Corfu hotels page
- Parses HTML to extract links to individual hotel detail pages
- Filters out non-hotel links and duplicates

### 2. **Hotel Detail Page Processing**
For each hotel link found:
- Fetches the individual hotel page
- Extracts hotel information using multiple parsing strategies:
  - **Name**: From `<h1>` tags or page title
  - **Star Rating**: From star symbols (★) or rating indicators
  - **Reviews**: From review score patterns and review count text
  - **Contact Info**: Phone numbers from `tel:` links and text patterns
  - **Website**: Official website links (excluding social media)
  - **Address**: From address/location HTML elements and text patterns
  - **Coordinates**: From Google Maps embeds and JavaScript variables

### 3. **Data Processing & Storage**
- Validates and cleans extracted data
- Saves results in both CSV and JSON formats
- Generates detailed logs and summary statistics

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/StamosKall/Greeka_Corfu_Crawler.git
   cd Greeka_Corfu_Crawler
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running Locally

Execute the crawler with:

```bash
cd src
python crawler.py
```

The crawler will:
1. Start by fetching the main Greeka Corfu hotels page
2. Extract all hotel detail page links
3. Visit each hotel page and extract information
4. Save results to `../data/hotels.csv` and `../data/hotels.json`
5. Display a summary of extracted data

### Output Files

After successful execution, you'll find in the `data/` folder:

- **`hotels.csv`**: Tabular data in CSV format (Excel-compatible)
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
2. Select the **"Greeka Corfu Hotels Crawler"** workflow
3. Click **"Run workflow"** button
4. Choose the branch and click **"Run workflow"**

### Accessing Results

After workflow completion:
1. Go to the completed workflow run
2. Scroll down to **"Artifacts"** section
3. Download **"hotel-data"** artifact containing:
   - `hotels.csv`
   - `hotels.json`
   - `crawler.log`

## Sample Output

### CSV Format
```csv
name,official_website,address,star_rating,review_score,number_of_reviews,phone_number,latitude,longitude,detail_url
"Delfino Blu Boutique Hotel","https://www.delfinoblu.gr/","Agios Stefanos Avliotes, Corfu","4","4.2","87","+30 26630 51012","39.7912","19.6858","https://www.greeka.com/ionian/corfu/hotels/location-agios-stefanos-avliotes/delfino-blu/"
"Corfu Palace Hotel","https://www.corfupalace.com/","Garitsa Bay, Corfu Town","5","4.5","156","+30 26610 39485","39.6242","19.9217","https://www.greeka.com/ionian/corfu/hotels/corfu-palace/"
```

### JSON Format
```json
[
  {
    "name": "Delfino Blu Boutique Hotel",
    "official_website": "https://www.delfinoblu.gr/",
    "address": "Agios Stefanos Avliotes, Corfu",
    "star_rating": "4",
    "review_score": "4.2",
    "number_of_reviews": "87",
    "phone_number": "+30 26630 51012",
    "latitude": "39.7912",
    "longitude": "19.6858",
    "detail_url": "https://www.greeka.com/ionian/corfu/hotels/location-agios-stefanos-avliotes/delfino-blu/"
  }
]
```

## Configuration & Customization

### Modifying Crawler Behavior

Key parameters in `crawler.py`:

```python
# Request delays (seconds)
time.sleep(1)      # Between page requests
time.sleep(2)      # Between hotel processing

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
4. **Data Validation**: Cleans and validates extracted information

### Dependencies

- **requests**: HTTP library for web requests
- **beautifulsoup4**: HTML parsing and navigation
- **lxml**: Fast XML/HTML parser (BeautifulSoup backend)

### Architecture

- **Object-Oriented Design**: Clean, maintainable code structure
- **Dataclass Models**: Type-safe data representation
- **Comprehensive Logging**: Detailed execution tracking
- **Modular Functions**: Easily testable and extensible

## Legal & Ethical Considerations

- **Respectful Crawling**: Implements appropriate delays between requests
- **Public Data Only**: Only extracts publicly available information
- **No Personal Data**: Focuses on business/contact information only
- **Terms of Service**: Users should review Greeka's ToS before use

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit changes: `git commit -am 'Add feature'`
5. Push to branch: `git push origin feature-name`
6. Submit a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For issues, questions, or contributions:
- **GitHub Issues**: Report bugs or request features
- **Pull Requests**: Contribute improvements
- **Discussions**: General questions and community support

---

**Disclaimer**: This crawler is for educational and research purposes. Users are responsible for complying with the target website's terms of service and applicable laws.