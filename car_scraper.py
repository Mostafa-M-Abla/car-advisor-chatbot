import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import time
import logging
from typing import Dict, List, Optional, Any
import re

class CarScraper:
    def __init__(self):
        self.base_url = "https://eg.hatla2ee.com/en/new-car"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Setup logging
        self.setup_logging()

        # Load features mapping
        self.features_mapping = self.load_features_mapping()

        # Initialize CSV
        self.csv_filename = "scrapped_data.csv"
        self.error_log_filename = "error_log.txt"
        self.scraped_trims = set()  # To avoid duplicates

    def setup_logging(self):
        """Setup logging to console and error file"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('error_log.txt', mode='a')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_error(self, message: str):
        """Log error message to both console and file"""
        self.logger.error(message)
        with open(self.error_log_filename, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - ERROR: {message}\n")

    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def load_features_mapping(self) -> Dict[str, Dict]:
        """Load and parse features mapping CSV"""
        try:
            df = pd.read_csv('features_mapping.csv')
            mapping = {}
            for _, row in df.iterrows():
                website_name = str(row['website']).lower().strip()
                mapping[website_name] = {
                    'output_csv': row['output_csv'],
                    'd_type': row['d_type']
                }
            self.log_info(f"Loaded {len(mapping)} feature mappings")
            return mapping
        except Exception as e:
            self.log_error(f"Failed to load features_mapping.csv: {e}")
            return {}

    def initialize_csv(self):
        """Initialize the CSV file with proper headers"""
        try:
            headers = ['car_brand', 'car_model', 'car_trim']
            # Add all output_csv columns from features mapping
            output_columns = [mapping['output_csv'] for mapping in self.features_mapping.values()]
            headers.extend(output_columns)

            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            self.log_info(f"Initialized CSV file with {len(headers)} columns")

        except Exception as e:
            self.log_error(f"Failed to initialize CSV: {e}")

    def convert_data_type(self, value: str, data_type: str) -> Any:
        """Convert scraped value to specified data type"""
        if not value or value.strip() == '':
            return None

        try:
            value = value.strip()

            if data_type == 'int':
                # Extract numbers from string
                numbers = re.findall(r'\d+', value.replace(',', ''))
                return int(''.join(numbers)) if numbers else None

            elif data_type == 'float':
                # Extract decimal numbers
                match = re.search(r'\d+\.?\d*', value.replace(',', ''))
                return float(match.group()) if match else None

            elif data_type == 'bool':
                # Check if feature is present
                return value.lower() not in ['', 'no', 'false', 'n/a', 'not available']

            else:  # string
                return value

        except Exception as e:
            self.log_error(f"Failed to convert '{value}' to {data_type}: {e}")
            return None

    def make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Make HTTP request and return BeautifulSoup object"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            self.log_error(f"Failed to load page {url}: {e}")
            return None

    def get_brands(self) -> List[str]:
        """Extract all car brands from main page"""
        url = self.base_url
        soup = self.make_request(url)

        if not soup:
            return []

        brands = []
        try:
            # Look for all brand links with the specific pattern
            brand_links = soup.find_all('a', href=re.compile(r'/en/new-car/[^/]+/?$'))
            for link in brand_links:
                href = link.get('href')
                if href:
                    # Extract brand name from URL
                    brand = href.strip('/').split('/')[-1]
                    if brand and brand != 'new-car' and brand not in brands:
                        brands.append(brand)

            self.log_info(f"Found {len(brands)} brands")
            return brands

        except Exception as e:
            self.log_error(f"Failed to extract brands: {e}")
            return []

    def get_models(self, brand: str) -> List[Dict]:
        """Get all models for a brand, excluding unavailable ones"""
        url = f"{self.base_url}/{brand}"
        soup = self.make_request(url)

        if not soup:
            return []

        models = []
        try:
            # Look for model links with the pattern /en/new-car/brand/model
            model_links = soup.find_all('a', href=re.compile(f'/en/new-car/{brand}/[^/]+/?$'))

            for link in model_links:
                # Check if model is available (skip if contains error indicators)
                text_content = link.get_text().lower()
                if '_error_' in text_content or 'not available' in text_content:
                    continue

                href = link.get('href')
                if href:
                    # Extract model name from URL
                    model_name = href.strip('/').split('/')[-1]
                    if model_name:
                        models.append({
                            'name': model_name,
                            'url': href
                        })

            self.log_info(f"Found {len(models)} available models for {brand}")
            return models

        except Exception as e:
            self.log_error(f"Failed to extract models for {brand}: {e}")
            return []

    def test_single_model(self, brand: str = "hyundai", model_name: str = "Accent-RB"):
        """Test scraping with a single model"""
        self.log_info(f"Starting test with {brand} {model_name}")

        # Initialize CSV
        self.initialize_csv()

        # Test URL
        model_url = f"{self.base_url}/{brand}/{model_name}"
        self.log_info(f"Testing with URL: {model_url}")

        # Get trims for this model
        trims = self.get_trims(brand, model_name, model_url)

        if not trims:
            self.log_error(f"No trims found for {brand} {model_name}")
            return

        self.log_info(f"Found {len(trims)} trims to process")

        # Process each trim
        for i, trim in enumerate(trims[:3]):  # Limit to first 3 for testing
            self.log_info(f"Processing trim {i+1}/{min(3, len(trims))}: {trim['name']}")
            self.scrape_trim_data(brand, model_name, trim)

        self.log_info("Test completed successfully!")

    def get_trims(self, brand: str, model_name: str, model_url: str) -> List[Dict]:
        """Extract all trims from model page"""
        soup = self.make_request(model_url)

        if not soup:
            return []

        trims = []
        try:
            # Look for trim links in the table structure
            # Based on the webpage analysis, trims are in a table with links to individual trim pages
            trim_links = soup.find_all('a', href=re.compile(f'/en/new-car/{brand}/{model_name}/\\d+/?$'))

            for link in trim_links:
                href = link.get('href')
                trim_name = link.get_text().strip()

                if href and trim_name:
                    # Create full trim name
                    full_trim_name = f"{brand.title()} {model_name} {trim_name}"

                    if full_trim_name not in self.scraped_trims:
                        trims.append({
                            'name': trim_name,
                            'full_name': full_trim_name,
                            'url': href
                        })

            # If no trim links found, try to find trim info in table rows
            if not trims:
                table_rows = soup.find_all('tr')
                for row in table_rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) > 0:
                        # Look for links within table cells
                        link = row.find('a', href=re.compile(f'/en/new-car/{brand}/{model_name}/\\d+'))
                        if link:
                            href = link.get('href')
                            trim_name = link.get_text().strip()
                            if href and trim_name:
                                full_trim_name = f"{brand.title()} {model_name} {trim_name}"
                                if full_trim_name not in self.scraped_trims:
                                    trims.append({
                                        'name': trim_name,
                                        'full_name': full_trim_name,
                                        'url': href
                                    })

            self.log_info(f"Found {len(trims)} trims for {brand} {model_name}")
            return trims

        except Exception as e:
            self.log_error(f"Failed to extract trims for {brand} {model_name}: {e}")
            return []

    def scrape_trim_data(self, brand: str, model_name: str, trim: Dict):
        """Scrape all data for a specific trim"""
        try:
            # Avoid duplicates
            if trim['full_name'] in self.scraped_trims:
                self.log_info(f"Skipping duplicate trim: {trim['full_name']}")
                return

            # Get trim details page
            trim_url = trim['url'] if trim['url'].startswith('http') else f"https://eg.hatla2ee.com{trim['url']}"
            soup = self.make_request(trim_url)

            if not soup:
                return

            # Initialize row data
            row_data = {
                'car_brand': brand,
                'car_model': model_name,
                'car_trim': trim['full_name']
            }

            # Scrape basic info (prices, etc.) from listing
            self.scrape_basic_info(soup, row_data)

            # Scrape detailed specifications
            self.scrape_specifications(soup, row_data)

            # Save to CSV
            self.save_row_to_csv(row_data)

            # Mark as processed
            self.scraped_trims.add(trim['full_name'])

            self.log_info(f"Successfully scraped data for {trim['full_name']}")

        except Exception as e:
            self.log_error(f"Failed to scrape trim {trim.get('full_name', 'unknown')}: {e}")

    def scrape_basic_info(self, soup: BeautifulSoup, row_data: Dict):
        """Scrape basic info like prices from the page"""
        try:
            # Look for pricing information in tables and text
            all_text = soup.get_text().lower()

            # Extract specific price types
            price_patterns = {
                'official price': r'official price[:\s]*(\d+(?:,\d+)*)\s*egp',
                'market price': r'market price[:\s]*(\d+(?:,\d+)*)\s*egp',
                'minimum deposit': r'minimum deposit[:\s]*(\d+(?:,\d+)*)\s*egp',
                'minimum installment': r'minimum installment[:\s]*(\d+(?:,\d+)*)\s*egp'
            }

            for feature_name, pattern in price_patterns.items():
                match = re.search(pattern, all_text)
                if match and feature_name in self.features_mapping:
                    value = match.group(1).replace(',', '')
                    mapping = self.features_mapping[feature_name]
                    converted_value = self.convert_data_type(value, mapping['d_type'])
                    row_data[mapping['output_csv']] = converted_value

            # Also try to extract from table cells
            table_cells = soup.find_all(['td', 'th'])
            for cell in table_cells:
                text = cell.get_text().lower().strip()
                for website_name, mapping in self.features_mapping.items():
                    if website_name in text:
                        # Try to get value from next sibling or same cell
                        value_text = text
                        next_cell = cell.find_next_sibling(['td', 'th'])
                        if next_cell:
                            value_text = next_cell.get_text().strip()

                        converted_value = self.convert_data_type(value_text, mapping['d_type'])
                        if converted_value is not None:
                            row_data[mapping['output_csv']] = converted_value
                        break

        except Exception as e:
            self.log_error(f"Failed to scrape basic info: {e}")

    def scrape_specifications(self, soup: BeautifulSoup, row_data: Dict):
        """Scrape specifications from Descriptions and Equipment sections"""
        try:
            # Get all page text for pattern matching
            all_text = soup.get_text().lower()

            # Search for all features in the text
            for website_name, mapping in self.features_mapping.items():
                if website_name in all_text:
                    if mapping['d_type'] == 'bool':
                        # For boolean features, presence indicates True
                        row_data[mapping['output_csv']] = True
                    else:
                        # Try to extract numeric values near the feature name
                        pattern = rf'{re.escape(website_name)}[:\s]*(\d+(?:\.\d+)?(?:,\d+)*)\s*(\w*)'
                        match = re.search(pattern, all_text)
                        if match:
                            value = match.group(1).replace(',', '')
                            converted_value = self.convert_data_type(value, mapping['d_type'])
                            if converted_value is not None:
                                row_data[mapping['output_csv']] = converted_value

            # Look for specific sections with headings
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text().lower()
                if any(keyword in heading_text for keyword in ['description', 'equipment', 'specification', 'feature']):
                    # Process the section after this heading
                    section = heading.parent or heading.find_next_sibling()
                    if section:
                        self.extract_features_from_section(section, row_data)

            # Process all table rows for structured data
            table_rows = soup.find_all('tr')
            for row in table_rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # First cell might contain feature name, second cell the value
                    feature_text = cells[0].get_text().lower().strip()
                    value_text = cells[1].get_text().strip()

                    for website_name, mapping in self.features_mapping.items():
                        if website_name in feature_text:
                            converted_value = self.convert_data_type(value_text, mapping['d_type'])
                            if converted_value is not None:
                                row_data[mapping['output_csv']] = converted_value
                            break

        except Exception as e:
            self.log_error(f"Failed to scrape specifications: {e}")

    def extract_features_from_section(self, section: BeautifulSoup, row_data: Dict):
        """Extract features from a section of the page"""
        try:
            # Find all text elements that might contain feature names
            text_elements = section.find_all(['td', 'li', 'span', 'div', 'dt', 'dd'])

            for element in text_elements:
                text = element.get_text().lower().strip()

                # Try to match with features mapping
                for website_name, mapping in self.features_mapping.items():
                    if website_name in text:
                        # For boolean features, just mark as True if found
                        if mapping['d_type'] == 'bool':
                            row_data[mapping['output_csv']] = True
                        else:
                            # Try to extract value
                            value = self.extract_value_from_element(element)
                            converted_value = self.convert_data_type(value, mapping['d_type'])
                            if converted_value is not None:
                                row_data[mapping['output_csv']] = converted_value
                        break

        except Exception as e:
            self.log_error(f"Failed to extract features from section: {e}")

    def extract_value_from_element(self, element: BeautifulSoup) -> str:
        """Extract numeric or text value from an element"""
        try:
            text = element.get_text().strip()

            # Try to find the next sibling or parent that might contain the value
            siblings = element.find_next_siblings()
            for sibling in siblings[:3]:  # Check first 3 siblings
                sibling_text = sibling.get_text().strip()
                if sibling_text and sibling_text != text:
                    text = sibling_text
                    break

            return text

        except:
            return ""

    def save_row_to_csv(self, row_data: Dict):
        """Save a row of data to CSV file"""
        try:
            # Get all column headers from the CSV
            with open(self.csv_filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)

            # Prepare row with all columns
            row = []
            for header in headers:
                row.append(row_data.get(header, ''))

            # Append to CSV
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)

        except Exception as e:
            self.log_error(f"Failed to save row to CSV: {e}")

if __name__ == "__main__":
    scraper = CarScraper()
    scraper.test_single_model()