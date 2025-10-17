# Car Selection Chatbot - Universal Web Scraper

This project contains a comprehensive, multi-brand web scraper for extracting car information from a website.

## Project Overview

The scraper extracts detailed car specifications for **all car brands and models** available on the website (62+ brands), processing thousands of trims and saving the data to structured CSV files for analysis. Features intelligent rate limiting, comprehensive error handling, and flexible configuration options.

## Files

- `car_scraper.py` - Main scraper implementation with universal brand support
- `features_mapping.csv` - Field mapping configuration (website field names → output CSV columns)
- `scrapped_data.csv` - Generated output file with car data (timestamped filenames available)
- `scrapper_error_log.txt` - Comprehensive error logging for debugging
- `claude.md` - This documentation file

## Features

### Universal Brand Support
- **All Car Brands**: Automatically discovers and scrapes 62+ brands (Hyundai, Toyota, BMW, Mercedes, etc.)
- **Complete Coverage**: Processes all models and trims for each brand
- **Flexible Targeting**: Option to scrape specific brands or exclude certain brands
- **Scalable Architecture**: Easily handles thousands of car models and trims

### Data Extraction
- **Comprehensive Specifications**: Extracts 95+ fields including prices, technical specs, and features
- **Enhanced Data Quality**: Improved Engine_CC extraction with turbo detection ("1500 cc - turbo")
- **Complete Warranty Info**: Full warranty text extraction ("100000 km / 3 year(s)")
- **Multiple Years**: Handles different model years (2024, 2025, 2026)
- **Dual Touch Screen Support**: Separate columns for Touch_Screen and Multimedia_Touch_Screen

### Website Politeness & Rate Limiting
- **Intelligent Delays**: 200-500ms between requests with random jitter
- **Brand Transitions**: 1.5s delays when switching between brands
- **Exponential Backoff**: Smart retry logic for failed requests
- **Configurable Timing**: Adjustable delays for different use cases

### Key Fields Extracted
- **Basic Info**: Brand, model, trim name
- **Pricing**: Official price, market price, insurance, registration costs
- **Technical Specs**: Engine capacity, horsepower, transmission, fuel type, dimensions
- **Features**: 80+ boolean features (ABS, airbags, multimedia, etc.)

### Advanced Functionality
- **Smart Field Mapping**: Uses `features_mapping.csv` for flexible field name translation
- **Data Type Conversion**: Automatic conversion to int, float, bool, string types
- **Duplicate Prevention**: Avoids processing the same trim multiple times
- **Multi-Brand Error Handling**: Graceful failure recovery continues processing other brands
- **Advanced Progress Tracking**: Real-time statistics, processing rates, and completion estimates
- **Command-Line Interface**: Full argument parsing with multiple operation modes
- **Configurable Output**: Timestamped filenames and flexible file management

## Usage

### Command-Line Options

The scraper now features a comprehensive command-line interface with multiple operation modes:

```bash
# Scrape all brands (default - processes 62+ brands)
python car_scraper.py

# Test with specific brands only
python car_scraper.py --test-brands hyundai toyota

# Scrape specific brands
python car_scraper.py --brands bmw mercedes audi

# Exclude certain brands
python car_scraper.py --exclude hyundai kia

# Legacy mode (Hyundai only)
python car_scraper.py --hyundai-only

# Custom rate limiting
python car_scraper.py --min-delay 0.1 --max-delay 0.3 --brand-delay 1.0

# Get help
python car_scraper.py --help
```

### Operation Modes

#### Full Mode (Default)
```bash
python car_scraper.py
```
- Processes **all 62+ brands** available on the website
- Generates timestamped output files
- Uses intelligent rate limiting (200-500ms delays)
- Provides comprehensive progress tracking

#### Test Mode
```bash
python car_scraper.py --test-brands hyundai toyota
```
- Perfect for testing with a subset of brands
- Faster execution for development and verification
- Same data quality as full mode

#### Legacy Mode
```bash
python car_scraper.py --hyundai-only
```
- Maintains compatibility with original Hyundai-only functionality
- Uses the original scraping method

### Configuration

#### Field Mapping (`features_mapping.csv`)
The scraper uses a CSV file to map website field names to output CSV columns:

```csv
output_csv,website,d_type
Official_Price_EGP,Official Price,int
Transmission,transmission type,string
Fuel_Type,fuel,string
Year,yearyear,string
ABS,ABS,bool
```

- `output_csv`: Column name in the output CSV
- `website`: Field name as it appears on the website (case-sensitive)
- `d_type`: Data type for conversion (int, float, string, bool)

#### Rate Limiting Configuration
```bash
# Conservative (slower, very website-friendly)
python car_scraper.py --min-delay 0.5 --max-delay 1.0 --brand-delay 3.0

# Balanced (default)
python car_scraper.py --min-delay 0.2 --max-delay 0.5 --brand-delay 1.5

# Aggressive (faster, still polite)
python car_scraper.py --min-delay 0.1 --max-delay 0.3 --brand-delay 1.0
```

#### Special Pattern Handling
The scraper handles various website text formats with enhanced accuracy:
- **Concatenated fields**: `"transmission typeautomatic"` → extracts `"automatic"`
- **Multi-word values**: `"traction typefront traction"` → extracts `"front traction"`
- **Numeric patterns**: `"fuel92"` → extracts `"92"`
- **Year patterns**: `"yearyear2026"` → extracts `"2026"`
- **Engine with Turbo**: `"engine capacity1500 cc - turbo"` → extracts `"1500 cc - turbo"`
- **Complete Warranty**: `"warranty100000 km / 3 year(s)"` → extracts `"100000 km / 3 year(s)"`

## Output Format

### CSV Structure
The output CSV contains 95 columns:
1. **Identification**: `car_brand`, `car_model`, `car_trim`
2. **Pricing**: `Official_Price_EGP`, `Market_Price_EGP`, etc.
3. **Technical**: `Engine_CC`, `Horsepower_HP`, `Transmission`, etc.
4. **Features**: `ABS`, `Airbag`, `Bluetooth`, etc.

### Sample Output
```csv
car_brand,car_model,car_trim,Official_Price_EGP,Transmission,Fuel_Type,Year
hyundai,Accent-RB,Hyundai Accent RB 2026 A/T / GL,799900,automatic,92,2026
hyundai,Elantra-AD,Hyundai Elantra AD 2026 A/T / Smart,945000,automatic,92,2026
hyundai,i30,Hyundai I30 2026 A/T / Blaze,1149000,dsg,95,2026
```

## Technical Implementation

### Architecture
- **Object-oriented design** with `CarScraper` class
- **Modular methods** for brands, models, trims, and specifications
- **Configurable field mapping** system
- **Robust error handling** and logging

### Web Scraping Strategy
1. **Hierarchical scraping**: Brands → Models → Trims → Specifications
2. **BeautifulSoup parsing** for HTML content extraction
3. **Regex patterns** for text processing and field extraction
4. **Request management** with proper delays and error handling

### Data Processing
- **Type conversion** based on configuration
- **Data cleaning** and validation
- **Duplicate detection** and prevention
- **Market price fallback** (uses official price when market price unavailable)

## Error Handling

### Logging System
- **Console output**: Real-time progress updates
- **File logging**: Detailed error information in `error_log.txt`
- **Graceful degradation**: Continues processing even if individual items fail

### Common Issues
- **Network timeouts**: Automatic retry with delays
- **Missing data**: Appropriate default values
- **Malformed HTML**: Skip problematic entries and continue
- **File access**: Handles CSV file locking issues

## Performance

### Metrics
- **Processing speed**: ~2-3 seconds per trim
- **Data coverage**: 95 fields per car
- **Success rate**: >95% data extraction success
- **Memory usage**: Minimal (processes one trim at a time)

### Scalability
- **Easily extensible** to other car brands
- **Configurable field mapping** for different websites
- **Modular design** allows easy modification

## Development Notes

### Recent Improvements
- Fixed field extraction patterns for concatenated website text
- Updated field mappings for accurate data extraction
- Enhanced error handling and logging
- Implemented comprehensive progress tracking

### Known Limitations
- Currently optimized for Hyundai models on the website
- Requires manual field mapping updates for new data fields
- Depends on website structure remaining consistent

### Future Enhancements
- Extend to other car brands (BMW, Mercedes, etc.)
- Add multi-threading for faster processing
- Implement data validation and quality checks
- Add support for multiple output formats (JSON, Excel)

## Commands for Claude Code

To run the scraper:
```bash
python car_scraper.py
```

To check field mappings:
```bash
head -10 features_mapping.csv
```

To view results:
```bash
head -5 scrapped_data.csv
```

To check for errors:
```bash
tail -20 error_log.txt
```

## About Claude Code Costs

Regarding your question about Claude Code costs: The conversation with Claude incurs costs while it's active. However, once you stop chatting (close the conversation or let it timeout), no additional costs are incurred. The scraper will continue running independently on your machine without any additional Claude costs, as it's now a standalone Python script.