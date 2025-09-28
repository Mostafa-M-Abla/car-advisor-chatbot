import sqlite3
import pandas as pd
import os

class CarsDatabase:
    """Class for creating and managing the cars SQLite database."""

    def __init__(self, db_path='cars.db', csv_path='processed_data.csv'):
        self.db_path = db_path
        self.csv_path = csv_path

    def create_database(self):
        """Create the cars database with schema and indexes."""
        # Connect to SQLite database (creates if doesn't exist)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Drop table if exists (for clean setup)
        cursor.execute('DROP TABLE IF EXISTS cars')
        print(f"Dropped existing 'cars' table if it existed")

        # Create cars table based on schema.yaml
        create_table_sql = '''
        CREATE TABLE cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_brand TEXT,
            car_model TEXT,
            car_trim TEXT,
            Price_EGP INTEGER,
            body_type TEXT,
            Insurance_Price_EGP INTEGER,
            Register_Price_EGP INTEGER,
            Engine_CC INTEGER,
            Engine_Turbo BOOLEAN,
            Horsepower_HP INTEGER,
            Max_Speed_kmh INTEGER,
            Acceleration_0_100_sec REAL,
            Number_transmission_Speeds INTEGER,
            Transmission_Type TEXT,
            Fuel_Type INTEGER,
            Number_of_Cylinders INTEGER,
            Fuel_Tank_L INTEGER,
            Torque_Newton_Meter INTEGER,
            Length_mm INTEGER,
            Width_mm INTEGER,
            Height_mm INTEGER,
            Ground_Clearance_mm INTEGER,
            Wheelbase_mm INTEGER,
            Trunk_Size_L INTEGER,
            Origin_Country TEXT,
            Assembly_Country TEXT,
            Year INTEGER,
            Number_of_Seats INTEGER,
            Traction_Type TEXT,
            ABS BOOLEAN,
            EBD BOOLEAN,
            Driver_Airbag BOOLEAN,
            Passenger_Airbag BOOLEAN,
            Rear_Sensors BOOLEAN,
            Air_Conditioning BOOLEAN,
            Power_Steering BOOLEAN,
            Electric_Mirrors BOOLEAN,
            Remote_Keyless BOOLEAN,
            Central_Locking BOOLEAN,
            Cruise_Control BOOLEAN,
            Sunroof BOOLEAN,
            Tinted_Glass BOOLEAN,
            Front_Power_Windows BOOLEAN,
            Back_Power_Windows BOOLEAN,
            Bluetooth BOOLEAN,
            USB_Port BOOLEAN,
            AUX BOOLEAN,
            Alloy_Wheels BOOLEAN,
            Fog_Light BOOLEAN,
            Multifunction BOOLEAN,
            Warranty_km INTEGER,
            Warranty_years INTEGER,
            Minimum_Installment INTEGER,
            Minimum_Deposit INTEGER,
            Fuel_Consumption_l_100_km TEXT,
            Side_Airbag BOOLEAN,
            Power_Seats BOOLEAN,
            CD_Player BOOLEAN,
            Closing_Mirrors BOOLEAN,
            Leather_Seats BOOLEAN,
            EPS BOOLEAN,
            Rear_Camera BOOLEAN,
            GPS BOOLEAN,
            Front_Sensors BOOLEAN,
            Intelligent_Parking_System BOOLEAN,
            Rear_Spoiler BOOLEAN,
            Electric_Chairs BOOLEAN,
            Start_Engine BOOLEAN,
            ESP BOOLEAN,
            Steptronic BOOLEAN,
            Panoramic_Sunroof BOOLEAN,
            Touch_Activated_Door_Lock BOOLEAN,
            Heated_Seats BOOLEAN,
            Cool_Box BOOLEAN,
            Rear_Seat_Entertainment BOOLEAN,
            Daytime_Running_Lights BOOLEAN,
            Start_Stop_System BOOLEAN,
            Tyre_Pressure_Sensor BOOLEAN,
            Xenon_Headlights BOOLEAN,
            Front_Camera BOOLEAN,
            Immobilizer_Key BOOLEAN,
            Roof_Rack BOOLEAN,
            Anti_Theft_System BOOLEAN,
            Alarm BOOLEAN,
            Multimedia_Touch_Screen BOOLEAN,
            Off_Road_Tyres BOOLEAN
        )
        '''

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

        # Convert boolean columns from True/False strings to 1/0
        boolean_columns = [
            'Engine_Turbo', 'ABS', 'EBD', 'Driver_Airbag', 'Passenger_Airbag',
            'Rear_Sensors', 'Air_Conditioning', 'Power_Steering', 'Electric_Mirrors',
            'Remote_Keyless', 'Central_Locking', 'Cruise_Control', 'Sunroof',
            'Tinted_Glass', 'Front_Power_Windows', 'Back_Power_Windows', 'Bluetooth',
            'USB_Port', 'AUX', 'Alloy_Wheels', 'Fog_Light', 'Multifunction',
            'Side_Airbag', 'Power_Seats', 'CD_Player', 'Closing_Mirrors',
            'Leather_Seats', 'EPS', 'Rear_Camera', 'GPS', 'Front_Sensors',
            'Intelligent_Parking_System', 'Rear_Spoiler', 'Electric_Chairs',
            'Start_Engine', 'ESP', 'Steptronic', 'Panoramic_Sunroof',
            'Touch_Activated_Door_Lock', 'Heated_Seats', 'Cool_Box',
            'Rear_Seat_Entertainment', 'Daytime_Running_Lights', 'Start_Stop_System',
            'Tyre_Pressure_Sensor', 'Xenon_Headlights', 'Front_Camera',
            'Immobilizer_Key', 'Roof_Rack', 'Anti_Theft_System', 'Alarm',
            'Multimedia_Touch_Screen', 'Off_Road_Tyres'
        ]

        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].map({'True': 1, 'False': 0, True: 1, False: 0}).fillna(0).astype(int)

        # Import data using pandas to_sql
        df.to_sql('cars', conn, if_exists='append', index=False)
        print(f"Imported {len(df)} records from {self.csv_path}")

if __name__ == "__main__":
    # Create database
    db_creator = CarsDatabase()
    db_creator.create_database()