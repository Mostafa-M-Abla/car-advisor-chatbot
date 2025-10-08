import sqlite3
import pandas as pd
import yaml
import os

class DatabaseTester:
    """Class for testing and querying the cars database."""

    def __init__(self, db_path='cars.db', schema_path='schema.yaml'):
        self.db_path = db_path
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self):
        """Load and parse schema.yaml file."""
        if not os.path.exists(self.schema_path):
            print(f"Warning: Schema file not found at {self.schema_path}")
            return {}

        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)

        return schema

    def _get_boolean_columns(self):
        """Extract list of boolean columns from schema."""
        boolean_cols = []
        for col in self.schema.get('columns', []):
            if col['doc_type'] == 'BOOLEAN':
                boolean_cols.append(col['name'])
        return boolean_cols

    def run_all_tests(self):
        """Run all database tests."""
        conn = sqlite3.connect(self.db_path)

        print("=== Database Test Queries ===")

        self.test_total_records(conn)
        self.test_cars_by_brand(conn)
        self.test_price_range(conn)
        self.test_transmission_types(conn)
        self.test_origin_countries(conn)
        self.test_turbo_engines(conn)
        self.test_first_five_rows(conn)
        self.test_null_values_in_boolean_columns(conn)
        self.test_cheapest_non_chinese_with_features(conn)
        self.test_cheapest_car_overall(conn)
        self.test_traction_types(conn)
        self.test_cheapest_non_chinese_crossover(conn)

        conn.close()

    def test_total_records(self, conn):
        """Test 1: Count total records."""
        result = conn.execute("SELECT COUNT(*) as total_cars FROM cars").fetchone()
        print(f"Total cars in database: {result[0]}")

    def test_cars_by_brand(self, conn):
        """Test 2: Count by brand."""
        print("\nCars by brand:")
        results = conn.execute("SELECT car_brand, COUNT(*) as count FROM cars GROUP BY car_brand ORDER BY count DESC LIMIT 5").fetchall()
        for brand, count in results:
            print(f"  {brand}: {count}")

    def test_price_range(self, conn):
        """Test 3: Price range."""
        result = conn.execute("SELECT MIN(Price_EGP), MAX(Price_EGP), AVG(Price_EGP) FROM cars WHERE Price_EGP IS NOT NULL").fetchone()
        print(f"\nPrice range: {result[0]:,.0f} - {result[1]:,.0f} EGP (avg: {result[2]:,.0f})")

    def test_transmission_types(self, conn):
        """Test 4: Transmission types."""
        print("\nTransmission types:")
        results = conn.execute("SELECT Transmission_Type, COUNT(*) FROM cars WHERE Transmission_Type IS NOT NULL GROUP BY Transmission_Type").fetchall()
        for trans, count in results:
            print(f"  {trans}: {count}")

    def test_origin_countries(self, conn):
        """Test 5: Countries of origin."""
        print("\nTop origin countries:")
        results = conn.execute("SELECT Origin_Country, COUNT(*) FROM cars WHERE Origin_Country IS NOT NULL GROUP BY Origin_Country ORDER BY COUNT(*) DESC LIMIT 5").fetchall()
        for country, count in results:
            print(f"  {country}: {count}")

    def test_turbo_engines(self, conn):
        """Test 6: Cars with turbo engines."""
        result = conn.execute("SELECT COUNT(*) FROM cars WHERE Engine_Turbo = 1").fetchone()
        print(f"\nCars with turbo engines: {result[0]}")

    def test_first_five_rows(self, conn):
        """Test 7: First 5 rows with all columns."""
        print("\nFirst 5 rows in database (all columns):")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cars ORDER BY id LIMIT 5")
        results = cursor.fetchall()

        # Get column names
        column_names = [description[0] for description in cursor.description]

        # Convert to pandas DataFrame for better table display
        df = pd.DataFrame(results, columns=column_names)

        # Set pandas display options for better table formatting
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 20)

        print(df.to_string(index=False))

    def test_null_values_in_boolean_columns(self, conn):
        """Test 8: Check for NULL values in boolean columns."""
        print("\n\nTest 8: Checking for NULL values in boolean columns:")

        # Get boolean columns dynamically from schema
        boolean_columns = self._get_boolean_columns()
        print(f"Testing {len(boolean_columns)} boolean columns from schema.yaml")

        columns_with_nulls = []
        for col in boolean_columns:
            null_count = conn.execute(f"SELECT COUNT(*) FROM cars WHERE {col} IS NULL").fetchone()[0]
            if null_count > 0:
                columns_with_nulls.append((col, null_count))

        if columns_with_nulls:
            print(f"Found NULL values in {len(columns_with_nulls)} boolean columns:")
            for col, count in columns_with_nulls:
                print(f"  {col}: {count} NULL values")
        else:
            print("All boolean columns have non-NULL values (0 or 1)")

        # Also check total record count for reference
        total_records = conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
        print(f"\nTotal records in database: {total_records}")

    def test_cheapest_non_chinese_with_features(self, conn):
        """Test 9: Find cheapest non-Chinese car with automatic transmission, ABS and ESP."""
        print("\n\nTest 9: Cheapest non-Chinese car with automatic transmission, ABS and ESP:")
        query = """
        SELECT id, car_brand, car_model, car_trim, Price_EGP, Origin_Country, Transmission_Type
        FROM cars
        WHERE Origin_Country != 'china'
        AND Transmission_Type = 'automatic'
        AND ABS = 1
        AND ESP = 1
        AND Price_EGP IS NOT NULL
        ORDER BY Price_EGP ASC
        LIMIT 1
        """
        result = conn.execute(query).fetchone()

        if result:
            id_val, brand, model, trim, price, origin, transmission = result
            print(f"ID: {id_val}")
            print(f"Brand: {brand}")
            print(f"Model: {model}")
            print(f"Trim: {trim}")
            print(f"Price: {price:,} EGP")
            print(f"Origin: {origin}")
            print(f"Transmission: {transmission}")
        else:
            print("No cars found matching the criteria")

    def test_cheapest_car_overall(self, conn):
        """Test 10: Find the cheapest car overall."""
        print("\n\nTest 10: Cheapest car in the database:")
        query = """
        SELECT id, car_brand, car_model, car_trim, Price_EGP, Origin_Country, Transmission_Type
        FROM cars
        WHERE Price_EGP IS NOT NULL
        ORDER BY Price_EGP ASC
        LIMIT 1
        """
        result = conn.execute(query).fetchone()

        if result:
            id_val, brand, model, trim, price, origin, transmission = result
            # Clean the trim string to handle Unicode characters
            trim_clean = trim.encode('ascii', errors='ignore').decode('ascii') if trim else ""
            print(f"ID: {id_val}")
            print(f"Brand: {brand}")
            print(f"Model: {model}")
            print(f"Trim: {trim_clean}")
            print(f"Price: {price:,} EGP")
            print(f"Origin: {origin}")
            print(f"Transmission: {transmission}")
        else:
            print("No cars found")

    def test_traction_types(self, conn):
        """Test 11: Check traction types to identify crossovers."""
        print("\n\nTraction types in database:")
        results = conn.execute("SELECT Traction_Type, COUNT(*) FROM cars WHERE Traction_Type IS NOT NULL GROUP BY Traction_Type ORDER BY COUNT(*) DESC").fetchall()
        for traction, count in results:
            print(f"  {traction}: {count}")

    def test_cheapest_non_chinese_crossover(self, conn):
        """Test 12: Find cheapest non-Chinese crossover."""
        print("\n\nTest 12: Cheapest non-Chinese crossover/SUV:")
        query = """
        SELECT id, car_brand, car_model, car_trim, Price_EGP, Origin_Country, Transmission_Type, Traction_Type
        FROM cars
        WHERE Origin_Country != 'china'
        AND (Traction_Type LIKE '%4%' OR Traction_Type LIKE '%awd%' OR Traction_Type LIKE '%all%' OR
             car_model LIKE '%suv%' OR car_model LIKE '%cross%' OR car_trim LIKE '%suv%' OR car_trim LIKE '%cross%')
        AND Price_EGP IS NOT NULL
        ORDER BY Price_EGP ASC
        LIMIT 5
        """
        results = conn.execute(query).fetchall()

        if results:
            print("Top 5 cheapest non-Chinese crossovers/SUVs:")
            for i, result in enumerate(results, 1):
                id_val, brand, model, trim, price, origin, transmission, traction = result
                trim_clean = trim.encode('ascii', errors='ignore').decode('ascii') if trim else ""
                print(f"\n{i}. ID: {id_val}")
                print(f"   Brand: {brand}")
                print(f"   Model: {model}")
                print(f"   Trim: {trim_clean}")
                print(f"   Price: {price:,} EGP")
                print(f"   Origin: {origin}")
                print(f"   Transmission: {transmission}")
                print(f"   Traction: {traction}")
        else:
            print("No crossovers/SUVs found matching the criteria")

    def custom_query(self, query):
        """Execute a custom SQL query and return results."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            return results, column_names
        except Exception as e:
            print(f"Error executing query: {e}")
            return None, None
        finally:
            conn.close()

if __name__ == "__main__":
    # Run all tests
    tester = DatabaseTester()
    tester.run_all_tests()