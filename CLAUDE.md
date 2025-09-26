# Car Selection Chatbot - Claude Documentation

## Project Overview
A comprehensive car selection chatbot system that helps users find the perfect vehicle based on their preferences. The system includes web scraping, data processing with AI enhancement, database creation, and a conversational chatbot interface.

## Project Structure

```
car-selection-chatbot/
├── web_scrapper/                    # Web scraping module
│   └── scrapped_data.csv           # Raw scraped car data
├── scrapped_data_postprocessing.py # Main data processing pipeline
├── database_creator.py             # SQLite database creation
├── database_tester.py              # Database testing and queries
├── cars.db                         # SQLite database with processed data
├── processed_data.csv              # Clean, processed car data
├── schema.yaml                     # Database schema definition
├── synonyms.yaml                   # Chatbot synonym mappings
├── simple_chatbot.py               # Main chatbot interface
├── .env                           # Environment variables (API keys)
└── CLAUDE.md                      # This documentation file
```

## Key Features

### 1. Data Processing Pipeline (`scrapped_data_postprocessing.py`)
- **Data Cleaning**: Removes invalid entries, normalizes columns
- **AI Enhancement**: Uses OpenAI GPT-4 for:
  - Body type classification (sedan, hatchback, crossover/suv, coupe, convertible, van)
  - Electric vehicle identification (boolean)
  - Origin country completion for missing brands
- **Warranty Parsing**: Splits warranty strings into km and years columns
- **Price Filtering**: Removes entries with invalid pricing
- **Year Filtering**: Keeps only recent model years based on current date
- **Column Standardization**: Renames and reorganizes columns

### 2. Database System
#### Database Creator (`database_creator.py`)
- Creates SQLite database with comprehensive schema
- Imports processed CSV data
- Creates performance indexes on key columns:
  - car_brand, car_model, car_trim
  - Price_EGP, Transmission_Type, Origin_Country, Engine_Turbo

#### Database Tester (`database_tester.py`)
- Comprehensive test suite for database validation
- Sample queries for data exploration
- Performance testing for indexed columns

### 3. Chatbot Interface (`simple_chatbot.py`)
- Interactive conversational interface
- Natural language query processing
- Car recommendation based on user preferences
- Integration with SQLite database for real-time queries

## Data Schema

### Core Vehicle Information
- `id`: Primary key (auto-increment)
- `car_brand`: Vehicle manufacturer
- `car_model`: Model name
- `car_trim`: Specific variant/trim level
- `Price_EGP`: Price in Egyptian Pounds
- `body_type`: AI-classified body style
- `electric_vehicle`: Boolean for EV status

### Engine & Performance
- `Engine_CC`: Engine displacement (cleaned numeric)
- `Engine_Turbo`: Boolean for turbocharger presence
- `Horsepower_HP`: Power output
- `Max_Speed_kmh`: Maximum speed
- `Acceleration_0_100_sec`: 0-100 km/h acceleration time
- `Torque_Newton_Meter`: Engine torque

### Transmission & Drivetrain
- `Transmission_Type`: Type of transmission
- `Number_transmission_Speeds`: Number of gears
- `Traction_Type`: Drive type (FWD, RWD, AWD)

### Dimensions & Capacity
- `Length_mm`, `Width_mm`, `Height_mm`: Vehicle dimensions
- `Wheelbase_mm`: Distance between axles
- `Ground_Clearance_mm`: Ground clearance
- `Trunk_Size_L`: Cargo capacity
- `Number_of_Seats`: Seating capacity (validated ≤9)
- `Fuel_Tank_L`: Fuel tank capacity

### Features & Safety
- Multiple boolean columns for features:
  - Safety: `ABS`, `EBD`, `ESP`, `Driver_Airbag`, `Passenger_Airbag`
  - Comfort: `Air_Conditioning`, `Power_Steering`, `Cruise_Control`
  - Technology: `Bluetooth`, `GPS`, `Multimedia_Touch_Screen`
  - Convenience: `Remote_Keyless`, `Central_Locking`, `Sunroof`

### Warranty & Pricing
- `Warranty_km`: Warranty distance coverage (extracted from text)
- `Warranty_years`: Warranty time coverage (extracted from text)
- `Minimum_Installment`: Minimum monthly payment
- `Minimum_Deposit`: Required down payment

### Origin & Assembly
- `Origin_Country`: Country where brand originated (AI-completed)
- `Assembly_Country`: Manufacturing location
- `Year`: Model year (filtered for recency)

## AI Integration

### OpenAI GPT-4 Usage
The system uses GPT-4 for intelligent data enhancement:

1. **Body Type Classification**
   - Processes brand-model combinations in batches of 50
   - Classifies into 6 standardized categories
   - Validates responses against allowed types

2. **Electric Vehicle Detection**
   - Identifies pure electric vehicles vs ICE/hybrid
   - Batch processing for efficiency
   - Accurate classification of complex cases

3. **Origin Country Completion**
   - Fills missing brand origin information
   - Leverages GPT-4's knowledge of automotive brands
   - Handles new/emerging brands not in datasets

### Batch Processing Strategy
- **Batch Size**: 50 combinations per API call
- **Error Handling**: Continues processing if individual batches fail
- **Progress Tracking**: Detailed logging of batch completion
- **Token Management**: Prevents API limits through intelligent batching

## Database Performance

### Indexes
Performance-optimized with indexes on frequently queried columns:
```sql
CREATE INDEX idx_car_brand ON cars (car_brand);
CREATE INDEX idx_car_model ON cars (car_model);
CREATE INDEX idx_Price_EGP ON cars (Price_EGP);
CREATE INDEX idx_Transmission_Type ON cars (Transmission_Type);
CREATE INDEX idx_Origin_Country ON cars (Origin_Country);
CREATE INDEX idx_Engine_Turbo ON cars (Engine_Turbo);
```

### Sample Queries
```sql
-- Find cheapest electric vehicles
SELECT car_brand, car_model, Price_EGP
FROM cars
WHERE electric_vehicle = 1
ORDER BY Price_EGP ASC;

-- Count by body type
SELECT body_type, COUNT(*)
FROM cars
GROUP BY body_type;

-- Premium German cars
SELECT * FROM cars
WHERE Origin_Country = 'germany'
AND Price_EGP > 2000000;
```

## Usage Instructions

### Data Processing
```bash
# Process raw scraped data with AI enhancement
python scrapped_data_postprocessing.py
```

### Database Creation
```bash
# Create SQLite database from processed data
python database_creator.py
```

### Database Testing
```bash
# Run comprehensive database tests
python database_tester.py
```

### Chatbot Interface
```bash
# Start interactive car recommendation chatbot
python simple_chatbot.py
```

## Configuration

### Environment Variables (`.env`)
```
OPENAI_API_KEY=your-openai-api-key-here
```

### Schema Configuration (`schema.yaml`)
Defines the complete database structure with column types and constraints.

### Synonym Configuration (`synonyms.yaml`)
Maps user input variations to standardized terms for better chatbot understanding.

## Data Quality Metrics

### Processing Results
- **Total Records**: 886 vehicles
- **Data Completeness**: 100% for all AI-enhanced columns
- **Body Type Coverage**: 100% classification success
- **Electric Vehicle Detection**: 13.1% identified as electric
- **Origin Country**: 100% completion using AI assistance

### Quality Assurance
- **Price Validation**: Removes entries < 1,000 EGP
- **Year Filtering**: Dynamic filtering based on current date
- **Seat Count Validation**: Removes invalid counts > 9
- **Boolean Standardization**: Consistent True/False values
- **Unicode Handling**: Proper encoding for international text

## Performance Considerations

### API Usage Optimization
- **Batch Processing**: Reduces API calls by 75%
- **Smart Caching**: Reuses brand-model combinations
- **Error Recovery**: Graceful handling of API failures
- **Rate Limiting**: Built-in delays between batches

### Database Optimization
- **Strategic Indexing**: Fast queries on common search criteria
- **Normalized Schema**: Efficient storage and retrieval
- **Data Types**: Appropriate types for optimal performance

## Troubleshooting

### Common Issues

1. **Permission Denied on CSV**: Close any open Excel/CSV viewers
2. **OpenAI API Errors**: Check API key in `.env` file
3. **Unicode Encoding**: Script handles special characters automatically
4. **Memory Issues**: Large datasets processed in chunks

### Debugging Commands
```bash
# Check database contents
python -c "import sqlite3; conn = sqlite3.connect('cars.db'); print(conn.execute('SELECT COUNT(*) FROM cars').fetchone())"

# Verify processed data
python -c "import pandas as pd; print(pd.read_csv('processed_data.csv').info())"
```

## Future Enhancements

### Potential Improvements
- **Multi-language Support**: Extend AI processing for Arabic text
- **Image Recognition**: Add vehicle image classification
- **Price Prediction**: ML models for price forecasting
- **User Preferences**: Learning from user interactions
- **Real-time Updates**: Automated scraping and processing

### Scalability Considerations
- **Database Migration**: PostgreSQL for larger datasets
- **API Management**: Rate limiting and quota management
- **Caching Layer**: Redis for frequent queries
- **Microservices**: Separate scraping, processing, and chatbot services

## Contributing

### Code Standards
- **Python Style**: Follow PEP 8 guidelines
- **Error Handling**: Comprehensive exception handling
- **Logging**: Detailed progress and error logging
- **Documentation**: Clear docstrings and comments

### Testing
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline validation
- **Performance Tests**: Database query optimization
- **Data Quality Tests**: Validation of AI-enhanced data

---

*This documentation provides a comprehensive guide to the car selection chatbot system. For technical support or contributions, refer to the individual module documentation and code comments.*