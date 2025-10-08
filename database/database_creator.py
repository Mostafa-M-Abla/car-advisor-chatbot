import sqlite3
import pandas as pd
import os
import yaml

class CarsDatabase:
    """Class for creating and managing the cars SQLite database."""

    def __init__(self, db_path='cars.db', csv_path='processed_data.csv', schema_path='schema.yaml'):
        self.db_path = db_path
        self.csv_path = csv_path
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self):
        """Load and parse schema.yaml file."""
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)

        return schema

    def _generate_create_table_sql(self):
        """Generate CREATE TABLE SQL statement from schema."""
        columns = self.schema.get('columns', [])

        if not columns:
            raise ValueError("No columns found in schema.yaml")

        # Build column definitions
        column_defs = []
        for col in columns:
            name = col['name']
            col_type = col['doc_type']

            # Handle primary key
            if name == 'id':
                column_defs.append(f"{name} {col_type} PRIMARY KEY AUTOINCREMENT")
            else:
                column_defs.append(f"{name} {col_type}")

        # Create full SQL statement
        create_sql = "CREATE TABLE cars (\n    " + ",\n    ".join(column_defs) + "\n)"
        return create_sql

    def _get_boolean_columns(self):
        """Extract list of boolean columns from schema."""
        boolean_cols = []
        for col in self.schema.get('columns', []):
            if col['doc_type'] == 'BOOLEAN':
                boolean_cols.append(col['name'])
        return boolean_cols

    def create_database(self):
        """Create the cars database with schema and indexes."""
        # Connect to SQLite database (creates if doesn't exist)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Drop table if exists (for clean setup)
        cursor.execute('DROP TABLE IF EXISTS cars')
        print(f"Dropped existing 'cars' table if it existed")

        # Generate CREATE TABLE SQL from schema.yaml
        create_table_sql = self._generate_create_table_sql()
        print(f"Generated CREATE TABLE SQL from {self.schema_path}")

        cursor.execute(create_table_sql)
        print("Created 'cars' table successfully")

        # Create indexes for specified columns
        self._create_indexes(cursor)

        # Import data from CSV
        self._import_csv_data(conn)

        # Commit and close
        conn.commit()
        conn.close()
        print(f"Database '{self.db_path}' created successfully with all indexes")

    def _create_indexes(self, cursor):
        """Create indexes for performance optimization."""
        indexes = [
            'car_brand',
            'car_model',
            'car_trim',
            'Price_EGP',
            'body_type',
            'Transmission_Type',
            'Origin_Country',
            'Engine_Turbo'
        ]

        for column in indexes:
            index_sql = f'CREATE INDEX idx_{column} ON cars ({column})'
            cursor.execute(index_sql)
            print(f"Created index for {column}")

    def _import_csv_data(self, conn):
        """Import data from CSV file into the database."""
        if not os.path.exists(self.csv_path):
            print(f"{self.csv_path} not found - database created but no data imported")
            return

        df = pd.read_csv(self.csv_path)

        # Get boolean columns dynamically from schema
        boolean_columns = self._get_boolean_columns()
        print(f"Found {len(boolean_columns)} boolean columns from schema")

        # Convert boolean columns from True/False strings to 1/0
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].map({'True': 1, 'False': 0, True: 1, False: 0}).fillna(0).astype(int)

        # Import data using pandas to_sql
        df.to_sql('cars', conn, if_exists='append', index=False)
        print(f"Imported {len(df)} records from {self.csv_path}")

if __name__ == "__main__":
    # Create database (look for CSV in parent directory)
    db_creator = CarsDatabase(csv_path='../processed_data.csv')
    db_creator.create_database()