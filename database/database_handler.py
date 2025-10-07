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