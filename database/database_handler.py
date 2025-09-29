import sqlite3
import yaml
from typing import List, Dict, Any, Optional, Tuple
import logging

class DatabaseHandler:
    """Handles all database operations for the car chatbot."""

    def __init__(self, db_path: str = "cars.db", schema_path: str = "schema.yaml"):
        self.db_path = db_path
        self.schema_path = schema_path
        self.logger = logging.getLogger(__name__)
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """Load database schema from YAML file."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Failed to load schema: {e}")
            return {}

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            return conn
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dictionaries.

        Args:
            query: SQL query string
            params: Optional parameters for parameterized query

        Returns:
            List of dictionaries representing query results
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Convert rows to dictionaries
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))

                self.logger.info(f"Query executed successfully, returned {len(results)} rows")
                return results

        except sqlite3.Error as e:
            self.logger.error(f"SQL error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during query execution: {e}")
            raise

    def validate_query(self, query: str) -> bool:
        """
        Validate SQL query for safety (basic checks).

        Args:
            query: SQL query to validate

        Returns:
            True if query appears safe, False otherwise
        """
        query_lower = query.lower().strip()

        # Must be a SELECT query
        if not query_lower.startswith('select'):
            self.logger.warning("Query validation failed: not a SELECT statement")
            return False

        # Forbidden operations
        forbidden_keywords = [
            'insert', 'update', 'delete', 'drop', 'create', 'alter',
            'truncate', 'grant', 'revoke', 'exec', 'execute'
        ]

        for keyword in forbidden_keywords:
            if keyword in query_lower:
                self.logger.warning(f"Query validation failed: contains forbidden keyword '{keyword}'")
                return False

        return True

    def search_cars(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search cars based on structured criteria.

        Args:
            criteria: Dictionary with search criteria

        Returns:
            List of matching cars
        """
        query_parts = ["SELECT * FROM cars WHERE 1=1"]
        params = []

        # Price range
        if 'min_price' in criteria:
            query_parts.append("AND Price_EGP >= ?")
            params.append(criteria['min_price'])

        if 'max_price' in criteria:
            query_parts.append("AND Price_EGP <= ?")
            params.append(criteria['max_price'])

        # Body type
        if 'body_type' in criteria:
            query_parts.append("AND body_type = ?")
            params.append(criteria['body_type'])

        # Origin country
        if 'origin_country' in criteria:
            query_parts.append("AND Origin_Country = ?")
            params.append(criteria['origin_country'])

        # Exclude origin country
        if 'exclude_origin' in criteria:
            query_parts.append("AND Origin_Country != ?")
            params.append(criteria['exclude_origin'])

        # Transmission type
        if 'transmission' in criteria:
            query_parts.append("AND Transmission_Type = ?")
            params.append(criteria['transmission'])

        # Note: electric_vehicle column removed from schema

        # Features (boolean columns)
        feature_columns = ['ABS', 'ESP', 'Engine_Turbo', 'Air_Conditioning',
                          'Sunroof', 'Bluetooth', 'GPS', 'Cruise_Control']

        for feature in feature_columns:
            if feature.lower() in criteria or feature in criteria:
                query_parts.append(f"AND {feature} = 1")

        # Brand
        if 'brand' in criteria:
            query_parts.append("AND car_brand = ?")
            params.append(criteria['brand'])

        # Sorting and limiting
        query_parts.append("ORDER BY Price_EGP ASC")

        if 'limit' in criteria:
            query_parts.append("LIMIT ?")
            params.append(criteria['limit'])
        else:
            query_parts.append("LIMIT 10")  # Default limit

        query = " ".join(query_parts)
        return self.execute_query(query, tuple(params))

    def get_car_by_id(self, car_id: int) -> Optional[Dict[str, Any]]:
        """Get specific car by ID."""
        try:
            results = self.execute_query("SELECT * FROM cars WHERE id = ?", (car_id,))
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"Error fetching car by ID {car_id}: {e}")
            return None

    def get_brands(self) -> List[str]:
        """Get all unique car brands."""
        try:
            results = self.execute_query("SELECT DISTINCT car_brand FROM cars ORDER BY car_brand")
            return [row['car_brand'] for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching brands: {e}")
            return []

    def get_body_types(self) -> List[str]:
        """Get all unique body types."""
        try:
            results = self.execute_query("SELECT DISTINCT body_type FROM cars ORDER BY body_type")
            return [row['body_type'] for row in results if row['body_type']]
        except Exception as e:
            self.logger.error(f"Error fetching body types: {e}")
            return []

    def get_price_range(self) -> Tuple[int, int]:
        """Get min and max prices from database."""
        try:
            result = self.execute_query(
                "SELECT MIN(Price_EGP) as min_price, MAX(Price_EGP) as max_price FROM cars WHERE Price_EGP IS NOT NULL"
            )
            if result:
                return result[0]['min_price'], result[0]['max_price']
            return 0, 0
        except Exception as e:
            self.logger.error(f"Error fetching price range: {e}")
            return 0, 0

    def get_database_stats(self) -> Dict[str, Any]:
        """Get general database statistics."""
        try:
            stats = {}

            # Total cars
            total_result = self.execute_query("SELECT COUNT(*) as total FROM cars")
            stats['total_cars'] = total_result[0]['total'] if total_result else 0

            # Brands count
            brands_result = self.execute_query("SELECT COUNT(DISTINCT car_brand) as brand_count FROM cars")
            stats['total_brands'] = brands_result[0]['brand_count'] if brands_result else 0

            # Body types count
            body_types_result = self.execute_query("SELECT body_type, COUNT(*) as count FROM cars GROUP BY body_type ORDER BY count DESC")
            stats['body_types'] = {row['body_type']: row['count'] for row in body_types_result if row['body_type']}

            # Price range
            stats['min_price'], stats['max_price'] = self.get_price_range()

            # Origin distribution
            origin_result = self.execute_query("SELECT Origin_Country, COUNT(*) as count FROM cars GROUP BY Origin_Country ORDER BY count DESC LIMIT 5")
            stats['origin_distribution'] = {row['Origin_Country']: row['count'] for row in origin_result if row['Origin_Country']}

            return stats

        except Exception as e:
            self.logger.error(f"Error fetching database stats: {e}")
            return {}

    def format_price(self, price: Optional[int]) -> str:
        """Format price with proper EGP formatting."""
        if price is None:
            return "N/A"
        return f"{price:,} EGP"

    def format_car_summary(self, car: Dict[str, Any]) -> str:
        """Format car information for display."""
        brand = car.get('car_brand', 'Unknown')
        model = car.get('car_model', 'Unknown')
        trim = car.get('car_trim', '')
        price = self.format_price(car.get('Price_EGP'))
        body_type = car.get('body_type', 'Unknown')
        origin = car.get('Origin_Country', 'Unknown')
        transmission = car.get('Transmission_Type', 'Unknown')

        summary = f"**{brand} {model}"
        if trim:
            summary += f" {trim}"
        summary += f"**\n"
        summary += f"   Price: {price}\n"
        summary += f"   Type: {body_type.title()}\n"
        summary += f"   Origin: {origin.title()}\n"
        summary += f"   Transmission: {transmission.title()}\n"

        # Add key features
        features = []
        if car.get('Engine_Turbo'):
            features.append("Turbo")
        if car.get('ABS'):
            features.append("ABS")
        if car.get('ESP'):
            features.append("ESP")
        if car.get('Air_Conditioning'):
            features.append("A/C")
        if car.get('Sunroof'):
            features.append("Sunroof")
        # Note: electric_vehicle column removed from schema

        if features:
            summary += f"   Features: {', '.join(features)}\n"

        return summary