import os
import shutil
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from openai import OpenAI
    # Initialize OpenAI client with API key from environment variable
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    OPENAI_AVAILABLE = True
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY not found in .env file")
        OPENAI_AVAILABLE = False
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None
    print("Warning: OpenAI library not installed. Install with: pip install openai")

def get_car_brand_origin_with_openai(brands_list):
    """
    Use OpenAI API to get origin countries for car brands using GPT-4.

    Args:
        brands_list: List of car brand names

    Returns:
        dict: Mapping of brand name to origin country
    """
    if not OPENAI_AVAILABLE:
        print("OpenAI library not available. Please install it with: pip install openai")
        return {}

    if not openai_client:
        print("OpenAI client not available. Please check your .env file.")
        return {}

    brand_origin_mapping = {}

    try:
        # Create a prompt asking for origin countries of the brands
        brands_text = ", ".join(brands_list)
        prompt = f"""For each of the following car brands, provide the country of origin (where the company was founded/headquartered).
Please respond in the format: brand_name:country_name (use lowercase for country names)

Car brands: {brands_text}

Example format:
toyota:japan
bmw:germany
ford:usa

Please be accurate and only include the country name without any additional text."""

        print(f"Querying OpenAI GPT-4 for origin countries of brands: {brands_list}")

        # Make API call to OpenAI using GPT-4
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides accurate information about car brand origins. Always respond in the exact format requested."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )

        # Parse the response
        response_text = response.choices[0].message.content.strip()
        print(f"OpenAI GPT-4 Response:\n{response_text}")

        # Parse the response to extract brand:country mappings
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    brand = parts[0].strip().lower()
                    country = parts[1].strip().lower()
                    # Match the brand from our original list (case insensitive)
                    for original_brand in brands_list:
                        if original_brand.lower() == brand:
                            brand_origin_mapping[original_brand] = country
                            break

        print(f"Successfully extracted {len(brand_origin_mapping)} brand origins from OpenAI GPT-4")
        return brand_origin_mapping

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        print("Please make sure you have set your OpenAI API key in .env file and have sufficient credits.")
        return {}

def main():
    # 1) Copy the CSV to the current path and name it processed_data.csv
    src = os.path.join("web_scrapper", "scrapped_data.csv")
    dst = "processed_data.csv"

    if not os.path.isfile(src):
        raise FileNotFoundError(f"Source file not found: {src}")

    shutil.copyfile(src, dst)
    print(f"Copied '{src}' -> '{dst}'")

    # Load the copied file
    df = pd.read_csv(dst, dtype=str)
    df = df.replace(r'^\s*$', pd.NA, regex=True)

    # Normalize column names
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]

    # 2) Count the number of columns
    print(f"Number of columns BEFORE deletion: {df.shape[1]}")

    # 3) Delete specified columns
    cols_to_drop = [
        "Multimedia_System",
        "Fog_Lights",
        "Touch_Screen",
        "Alarm_or_Anti_Theft_System",
    ]
    existing_to_drop = [c for c in cols_to_drop if c in df.columns]
    df = df.drop(columns=existing_to_drop, errors="ignore")
    if existing_to_drop:
        print(f"Dropped columns: {existing_to_drop}")

    # 4) Recount the number of columns
    print(f"Number of columns AFTER deletion: {df.shape[1]}")

    # Delete rows where only first 3 columns are filled
    if df.shape[1] >= 3:
        first_three_cols = df.columns[:3]
        rest_cols = df.columns[3:]

        rows_before = len(df)
        if len(rest_cols) > 0:
            mask_first_three_have_values = df[first_three_cols].notna().all(axis=1)
            mask_rest_are_empty = df[rest_cols].isna().all(axis=1)
            to_delete_mask = mask_first_three_have_values & mask_rest_are_empty
            df = df.loc[~to_delete_mask].copy()
        rows_after = len(df)
        print(f"Rows BEFORE deletion: data only in first three columns: {rows_before}")
        print(f"Rows AFTER deletion  data only in first three columns: {rows_after}")

    # NEW RULE: Delete rows where Official_Price_EGP is <1000 OR empty
    if "Official_Price_EGP" in df.columns:
        # Convert to numeric safely
        df["Official_Price_EGP"] = pd.to_numeric(df["Official_Price_EGP"], errors="coerce")

        rows_before = len(df)
        # condition: value < 1000 OR NaN (empty)
        condition = (df["Official_Price_EGP"].isna()) | (df["Official_Price_EGP"] < 1000)
        df = df.loc[~condition].copy()
        rows_after = len(df)

        print(f"Rows BEFORE deletion: missing official price: {rows_before}")
        print(f"Rows AFTER deletion: missing official price: {rows_after}")
        print(f"Rows removed: {rows_before - rows_after}")
    else:
        print("Column 'Official_Price_EGP' not found, skipping price filter.")

    # Date-based Year filtering
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    if "Year" in df.columns:
        # Convert Year to numeric
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

        rows_before = len(df)

        if current_month <= 6:  # January to June
            min_year = current_year - 1
            condition = df["Year"] < min_year
        else:  # July to December
            min_year = current_year
            condition = df["Year"] < min_year

        df = df.loc[~condition].copy()
        rows_after = len(df)

        print(f"Current date: {current_date.strftime('%B %Y')}")
        print(f"Minimum allowed year: {min_year}")
        print(f"Rows BEFORE year filtering: {rows_before}")
        print(f"Rows AFTER year filtering: {rows_after}")
        print(f"Rows removed (old years): {rows_before - rows_after}")
    else:
        print("Column 'Year' not found, skipping year-based filtering.")

    # Rename Official_Price_EGP column to Price_EGP
    if "Official_Price_EGP" in df.columns:
        df = df.rename(columns={"Official_Price_EGP": "Price_EGP"})
        print("Renamed column 'Official_Price_EGP' to 'Price_EGP'")
    else:
        print("Column 'Official_Price_EGP' not found, skipping column rename.")

    # Rename Speeds column to Number_transmission_Speeds
    if "Speeds" in df.columns:
        df = df.rename(columns={"Speeds": "Number_transmission_Speeds"})
        print("Renamed column 'Speeds' to 'Number_transmission_Speeds'")
    else:
        print("Column 'Speeds' not found, skipping column rename.")

    # Rename Transmission column to Transmission_Type
    if "Transmission" in df.columns:
        df = df.rename(columns={"Transmission": "Transmission_Type"})
        print("Renamed column 'Transmission' to 'Transmission_Type'")
    else:
        print("Column 'Transmission_Type' not found, skipping column rename.")


    # Delete additional specified columns
    additional_cols_to_drop = [
        "Market_Price_EGP",
        "Cassette_Radio",
        "Fabric_Brushes",
        "CD_Changer",
        "DVD_Player",
        "Cloth",
        "Velour",
        "AM_FM_Radio"
    ]
    existing_additional_to_drop = [c for c in additional_cols_to_drop if c in df.columns]
    df = df.drop(columns=existing_additional_to_drop, errors="ignore")
    if existing_additional_to_drop:
        print(f"Dropped additional columns: {existing_additional_to_drop}")
    else:
        print("No additional columns found to drop.")

    # Clean car_trim column - remove specific substrings
    if "car_trim" in df.columns:
        substrings_to_remove = ["( AUTO MOBILITY)", "Local simplified", "(Abou Ghaly)"]
        rows_modified = 0

        for substring in substrings_to_remove:
            # Count rows that will be modified before replacement
            mask = df["car_trim"].str.contains(substring, na=False)
            count_before = mask.sum()

            # Remove the substring
            df["car_trim"] = df["car_trim"].str.replace(substring, "", regex=False)

            if count_before > 0:
                rows_modified += count_before
                print(f"Removed '{substring}' from {count_before} rows in car_trim column")

        if rows_modified == 0:
            print("No specified substrings found in car_trim column to remove")
        else:
            print(f"Total rows modified in car_trim column: {rows_modified}")
    else:
        print("Column 'car_trim' not found, skipping substring removal.")

    # Create engine_turbo column based on Engine_CC
    if "Engine_CC" in df.columns:
        # Find the position of Engine_CC column
        engine_cc_pos = df.columns.get_loc("Engine_CC")

        # Create engine_turbo column with True/False based on whether "turbo" is in Engine_CC
        engine_turbo_values = df["Engine_CC"].str.contains("turbo", case=False, na=False)

        # Insert the new column right after Engine_CC
        df.insert(engine_cc_pos + 1, 'Engine_Turbo', engine_turbo_values)

        turbo_count = engine_turbo_values.sum()
        total_count = len(df)
        print(f"Added 'Engine_Turbo' column after 'Engine_CC': {turbo_count} out of {total_count} cars have turbo engines")

        # Clean Engine_CC column - keep only the numeric value
        # Extract numeric values using regex (digits only)
        df["Engine_CC"] = df["Engine_CC"].str.extract(r'(\d+)')[0]
        print("Cleaned 'Engine_CC' column to keep only numeric values")
    else:
        print("Column 'Engine_CC' not found, skipping engine_turbo column creation.")

    # Clean Number_of_Seats column - delete values over 9
    if "Number_of_Seats" in df.columns:
        # Convert to numeric, keep original for comparison
        numeric_seats = pd.to_numeric(df["Number_of_Seats"], errors="coerce")

        # Count how many values are over 9
        over_9_mask = numeric_seats > 9
        over_9_count = over_9_mask.sum()

        # Delete values over 9 by setting them to NaN
        df.loc[over_9_mask, "Number_of_Seats"] = pd.NA

        if over_9_count > 0:
            print(f"Deleted {over_9_count} values over 9 in 'Number_of_Seats' column")
        else:
            print("No values over 9 found in 'Number_of_Seats' column")
    else:
        print("Column 'Number_of_Seats' not found, skipping seat count cleaning.")

    # Create Warranty_km and Warranty_years columns from Warranty column
    if "Warranty" in df.columns:
        # Find the position of Warranty column
        warranty_pos = df.columns.get_loc("Warranty")

        # Extract km value (number before "km")
        warranty_km_values = df["Warranty"].str.extract(r'(\d+)\s*km', expand=False)
        warranty_km_values = pd.to_numeric(warranty_km_values, errors='coerce')

        # Extract years value (number after "/" and before "year")
        warranty_years_values = df["Warranty"].str.extract(r'/\s*(\d+)\s*year', expand=False)
        warranty_years_values = pd.to_numeric(warranty_years_values, errors='coerce')

        # Insert the new columns right after Warranty
        df.insert(warranty_pos + 1, 'Warranty_km', warranty_km_values)
        df.insert(warranty_pos + 2, 'Warranty_years', warranty_years_values)

        # Count successful extractions
        km_count = warranty_km_values.notna().sum()
        years_count = warranty_years_values.notna().sum()
        total_warranty_count = df["Warranty"].notna().sum()

        print(f"Added 'Warranty_km' and 'Warranty_years' columns after 'Warranty'")
        print(f"Successfully extracted km values from {km_count} out of {total_warranty_count} warranty entries")
        print(f"Successfully extracted years values from {years_count} out of {total_warranty_count} warranty entries")

        # Delete the original Warranty column after successful extraction
        df = df.drop(columns=["Warranty"])
        print("Deleted original 'Warranty' column after splitting into km and years columns")
    else:
        print("Column 'Warranty' not found, skipping warranty parsing.")

    # Fill missing Origin_Country values based on car_brand
    if "Origin_Country" in df.columns and "car_brand" in df.columns:
        # Count missing values before processing
        missing_before = df["Origin_Country"].isna().sum()
        print(f"\nOrigin_Country missing values before processing: {missing_before}")

        if missing_before > 0:
            # Get unique brands that have missing Origin_Country
            brands_with_missing = df[df["Origin_Country"].isna()]["car_brand"].unique()
            print(f"Car brands with missing Origin_Country: {list(brands_with_missing)}")

            # Create a mapping of brand to origin country based on available data
            brand_origin_mapping = {}
            filled_brands = []

            for brand in brands_with_missing:
                # Find non-null origin countries for this brand
                brand_origins = df[(df["car_brand"] == brand) & (df["Origin_Country"].notna())]["Origin_Country"].unique()

                if len(brand_origins) > 0:
                    # Use the most common origin country for this brand
                    most_common_origin = df[(df["car_brand"] == brand) & (df["Origin_Country"].notna())]["Origin_Country"].mode()
                    if len(most_common_origin) > 0:
                        brand_origin_mapping[brand] = most_common_origin.iloc[0]
                        filled_brands.append(brand)

            # Fill missing values using the mapping
            for brand, origin in brand_origin_mapping.items():
                mask = (df["car_brand"] == brand) & (df["Origin_Country"].isna())
                df.loc[mask, "Origin_Country"] = origin

            # Count missing values after processing
            missing_after = df["Origin_Country"].isna().sum()
            filled_count = missing_before - missing_after

            print(f"Successfully filled Origin_Country for brands: {filled_brands}")
            print(f"Filled {filled_count} missing Origin_Country values")
            print(f"Origin_Country missing values after processing: {missing_after}")

            # Check if there are still missing values and which brands they belong to
            if missing_after > 0:
                remaining_brands = df[df["Origin_Country"].isna()]["car_brand"].unique()
                print(f"Brands still missing Origin_Country (no reference data available): {list(remaining_brands)}")

                # Use OpenAI to fill remaining missing values
                if OPENAI_AVAILABLE and len(remaining_brands) > 0:
                    print("\nUsing OpenAI GPT-4 to fill remaining missing Origin_Country values...")
                    openai_brand_mapping = get_car_brand_origin_with_openai(list(remaining_brands))

                    if openai_brand_mapping:
                        # Fill missing values using OpenAI results
                        openai_filled_brands = []
                        for brand, origin in openai_brand_mapping.items():
                            mask = (df["car_brand"] == brand) & (df["Origin_Country"].isna())
                            df.loc[mask, "Origin_Country"] = origin
                            openai_filled_brands.append(brand)

                        # Final count after OpenAI filling
                        final_missing = df["Origin_Country"].isna().sum()
                        openai_filled_count = missing_after - final_missing

                        print(f"OpenAI GPT-4 successfully filled Origin_Country for brands: {openai_filled_brands}")
                        print(f"OpenAI filled {openai_filled_count} additional missing Origin_Country values")
                        print(f"Final Origin_Country missing values: {final_missing}")

                        if final_missing > 0:
                            final_remaining_brands = df[df["Origin_Country"].isna()]["car_brand"].unique()
                            print(f"Brands still missing after OpenAI (could not be resolved): {list(final_remaining_brands)}")
                        else:
                            print("SUCCESS: All Origin_Country values successfully filled using dataset + OpenAI!")
                    else:
                        print("OpenAI could not provide origin information for the remaining brands")
                else:
                    if not OPENAI_AVAILABLE:
                        print("OpenAI not available to fill remaining missing values")
            else:
                print("All Origin_Country values successfully filled using existing data!")
        else:
            print("No missing Origin_Country values found")
    else:
        print("Columns 'Origin_Country' or 'car_brand' not found, skipping origin country filling.")

    # Add id column as the first column
    df.insert(0, 'id', range(1, len(df) + 1))
    print(f"Added 'id' column as first column with values from 1 to {len(df)}")

    # Save back to processed_data.csv
    df.to_csv(dst, index=False)
    print(f"Processed data saved to '{dst}'")

if __name__ == "__main__":
    main()
