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
            model="gpt-4.1",
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

def get_powertrain_types_with_openai(trim_list, df_subset=None):
    """
    Use OpenAI API to get powertrain types for car trims using GPT-5.

    Args:
        trim_list: List of car trim names
        df_subset: DataFrame subset containing car specifications for these trims

    Returns:
        dict: Mapping of trim name to powertrain type
    """
    if not OPENAI_AVAILABLE:
        print("OpenAI library not available. Please install it with: pip install openai")
        return {}

    if not openai_client:
        print("OpenAI client not available. Please check your .env file.")
        return {}

    powertrain_mapping = {}

    try:
        # Create a table representation with relevant columns if dataframe provided
        if df_subset is not None and not df_subset.empty:
            # Select only relevant columns for powertrain classification
            relevant_cols = ['car_brand', 'car_model', 'car_trim', 'Fuel_Type', 'Engine_CC', 'Battery_Capacity_kWh', 'Battery_Range_km']
            available_cols = [col for col in relevant_cols if col in df_subset.columns]
            df_text = df_subset[available_cols].to_string(index=False, max_rows=None)
        else:
            df_text = "No additional data available"

        # Create a list of trims for reference
        trims_text = "\n".join(trim_list)

        prompt = f"""The table below contains all new cars in the Egyptian car market. I want you to go through row by row (i.e. each car trim) and classify the "powertrain_type" into one of the following categories:
- Internal_Combustion_Engine (for traditional gasoline, diesel, or other fuel engines)
- Electric (for pure battery electric vehicles with no combustion engine)
- Hybrid (for vehicles that combine combustion engine with electric motor, non-pluggable)
- Plug_in_Hybrid_PHEV (for vehicles that can be plugged in to charge and have both combustion engine and electric motor)
- Mild_Hybrid_MHEV (for vehicles with small electric motor that assists combustion engine but cannot drive alone)
- Range_Extended_Electric_Vehicle_REEV_EREV (for electric vehicles with small combustion engine used only to charge battery)

For the classification, primarily use your knowledge and the internet. You can also use the data from the table below for validation.

Data table:
{df_text}

Car trims to classify:
{trims_text}

Example format:
2026 A/T / GL:Internal_Combustion_Engine
2025 A/T / CONNECT PLUS:Electric
XLE AWD Hybrid:Hybrid
330e M Sport:Plug_in_Hybrid_PHEV
A3 40 TFSI S Line:Mild_Hybrid_MHEV
i3 REx:Range_Extended_Electric_Vehicle_REEV_EREV

IMPORTANT: Only use these exact powertrain type names. Be accurate based on your automotive knowledge and the vehicle trim specifications."""

        print(f"Querying OpenAI GPT-5 for powertrain types of {len(trim_list)} trims...")

        # Make API call to OpenAI using GPT-5
        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an automotive expert that accurately classifies vehicle powertrains. Always respond in the exact format requested using only the allowed powertrain types."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000
        )

        # Parse the response
        response_text = response.choices[0].message.content.strip()
        print(f"OpenAI GPT-5 Response for powertrain types (full response):")
        print(response_text)
        print(f"\nResponse length: {len(response_text)} characters")
        print(f"Response object finish_reason: {response.choices[0].finish_reason}")

        # Parse the response to extract trim:powertrain_type mappings
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    trim_text = parts[0].strip().lower()
                    powertrain_type = parts[1].strip()

                    # Validate powertrain type
                    allowed_types = [
                        'Internal_Combustion_Engine',
                        'Electric',
                        'Hybrid',
                        'Plug_in_Hybrid_PHEV',
                        'Mild_Hybrid_MHEV',
                        'Range_Extended_Electric_Vehicle_REEV_EREV'
                    ]
                    if powertrain_type not in allowed_types:
                        print(f"Warning: Invalid powertrain type '{powertrain_type}' for '{trim_text}', skipping...")
                        continue

                    # Match the trim from our original list (case insensitive)
                    for original_trim in trim_list:
                        if original_trim.lower() == trim_text:
                            powertrain_mapping[original_trim] = powertrain_type
                            break

        print(f"Successfully extracted {len(powertrain_mapping)} powertrain types from OpenAI GPT-5")
        return powertrain_mapping

    except Exception as e:
        print(f"Error calling OpenAI API for powertrain types: {e}")
        print("Please make sure you have set your OpenAI API key in .env file and have sufficient credits.")
        return {}

def get_car_body_types_with_openai(brand_model_combinations):
    """
    Use OpenAI API to get body types for car brand-model combinations using GPT-4.

    Args:
        brand_model_combinations: List of (brand, model) tuples

    Returns:
        dict: Mapping of (brand, model) tuple to body type
    """
    if not OPENAI_AVAILABLE:
        print("OpenAI library not available. Please install it with: pip install openai")
        return {}

    if not openai_client:
        print("OpenAI client not available. Please check your .env file.")
        return {}

    body_type_mapping = {}

    try:
        # Create a prompt asking for body types of the brand-model combinations
        combinations_text = ""
        for brand, model in brand_model_combinations:
            combinations_text += f"{brand} {model}\n"

        prompt = f"""For each of the following car brand-model combinations, provide the body type.
You must respond ONLY with one of these allowed body types: sedan, hatchback, crossover/suv, coupe, convertible, van

Please respond in the format: brand model:body_type (use lowercase for everything)

Car brand-model combinations:
{combinations_text}

Example format:
toyota camry:sedan
honda civic:hatchback
ford explorer:crossover/suv
bmw z4:convertible
porsche 911:coupe

IMPORTANT: Only use these exact body types: sedan, hatchback, crossover/suv, coupe, convertible, van
If uncertain, choose the most appropriate from the allowed list."""

        print(f"Querying OpenAI GPT-4 for body types of {len(brand_model_combinations)} brand-model combinations...")

        # Make API call to OpenAI using GPT-4
        response = openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides accurate information about car body types. Always respond in the exact format requested using only the allowed body types: sedan, hatchback, crossover/suv, coupe, convertible, van."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.1
        )

        # Parse the response
        response_text = response.choices[0].message.content.strip()
        print(f"OpenAI GPT-4 Response for body types:\n{response_text}")

        # Parse the response to extract brand model:body_type mappings
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    brand_model_text = parts[0].strip().lower()
                    body_type = parts[1].strip().lower()

                    # Validate body type
                    allowed_types = ['sedan', 'hatchback', 'crossover/suv', 'coupe', 'convertible', 'van']
                    if body_type not in allowed_types:
                        print(f"Warning: Invalid body type '{body_type}' for '{brand_model_text}', skipping...")
                        continue

                    # Match the brand-model from our original list (case insensitive)
                    for original_brand, original_model in brand_model_combinations:
                        original_text = f"{original_brand} {original_model}".lower()
                        if original_text == brand_model_text:
                            body_type_mapping[(original_brand, original_model)] = body_type
                            break

        print(f"Successfully extracted {len(body_type_mapping)} body types from OpenAI GPT-4")
        return body_type_mapping

    except Exception as e:
        print(f"Error calling OpenAI API for body types: {e}")
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

    # Create body_type column after Price_EGP using OpenAI
    if "Price_EGP" in df.columns and "car_brand" in df.columns and "car_model" in df.columns:
        # Find the position of Price_EGP column
        price_pos = df.columns.get_loc("Price_EGP")

        # Get unique combinations of car_brand and car_model
        unique_combinations = df[["car_brand", "car_model"]].drop_duplicates()
        brand_model_combinations = [(row["car_brand"], row["car_model"]) for _, row in unique_combinations.iterrows()]

        print(f"\nFound {len(brand_model_combinations)} unique brand-model combinations for body type classification")

        # Use OpenAI to get body types for all combinations (in batches)
        if OPENAI_AVAILABLE:
            print("Using OpenAI GPT-4 to determine body types for all brand-model combinations...")

            # Process combinations in batches to avoid token limits
            batch_size = 50  # Process 50 combinations at a time
            body_type_mapping = {}

            for i in range(0, len(brand_model_combinations), batch_size):
                batch = brand_model_combinations[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(brand_model_combinations) + batch_size - 1) // batch_size

                print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} combinations)...")
                batch_mapping = get_car_body_types_with_openai(batch)

                if batch_mapping:
                    body_type_mapping.update(batch_mapping)
                    print(f"Batch {batch_num} completed successfully: {len(batch_mapping)} body types extracted")
                else:
                    print(f"Batch {batch_num} failed - no body types extracted")

            print(f"Batch processing completed. Total body types extracted: {len(body_type_mapping)}")

            if body_type_mapping:
                # Create body_type column and fill it
                df["body_type"] = pd.NA

                for (brand, model), body_type in body_type_mapping.items():
                    mask = (df["car_brand"] == brand) & (df["car_model"] == model)
                    df.loc[mask, "body_type"] = body_type

                # Move the body_type column to be right after Price_EGP
                body_type_column = df.pop("body_type")
                df.insert(price_pos + 1, "body_type", body_type_column)

                # Count successful mappings
                filled_count = df["body_type"].notna().sum()
                total_count = len(df)
                unfilled_count = total_count - filled_count

                print(f"Successfully added 'body_type' column after 'Price_EGP'")
                print(f"Filled body type for {filled_count} out of {total_count} cars")
                if unfilled_count > 0:
                    unfilled_combinations = df[df["body_type"].isna()][["car_brand", "car_model"]].drop_duplicates()
                    print(f"Could not determine body type for {unfilled_count} cars from {len(unfilled_combinations)} brand-model combinations:")
                    for _, row in unfilled_combinations.iterrows():
                        print(f"  - {row['car_brand']} {row['car_model']}")

                # Show body type distribution
                body_type_counts = df["body_type"].value_counts()
                print(f"Body type distribution:")
                for body_type, count in body_type_counts.items():
                    print(f"  {body_type}: {count}")
            else:
                # Create empty body_type column if OpenAI fails
                df.insert(price_pos + 1, "body_type", pd.NA)
                print("Failed to get body types from OpenAI. Created empty 'body_type' column.")
        else:
            # Create empty body_type column if OpenAI not available
            df.insert(price_pos + 1, "body_type", pd.NA)
            print("OpenAI not available. Created empty 'body_type' column after 'Price_EGP'")
    else:
        print("Required columns for body type classification not found, skipping body type creation.")

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

    # Remove duplicate rows (keep first occurrence)
    rows_before_dedup = len(df)
    df = df.drop_duplicates(keep='first')
    rows_after_dedup = len(df)
    duplicates_removed = rows_before_dedup - rows_after_dedup

    if duplicates_removed > 0:
        print(f"\nRemoved {duplicates_removed} duplicate rows")
        print(f"Rows before deduplication: {rows_before_dedup}")
        print(f"Rows after deduplication: {rows_after_dedup}")
    else:
        print("\nNo duplicate rows found")

    # Create powertrain_type column after body_type using OpenAI
    if "body_type" in df.columns and "car_trim" in df.columns:
        # Find the position of body_type column
        body_type_pos = df.columns.get_loc("body_type")

        # Load powertrain types from power_train.csv
        print("\nLoading powertrain types from power_train.csv...")
        try:
            powertrain_df = pd.read_csv("power_train.csv")
            print(f"Loaded {len(powertrain_df)} powertrain mappings from power_train.csv")

            # Create a mapping dictionary from car_trim to powertrain_type
            powertrain_mapping = dict(zip(powertrain_df["car_trim"], powertrain_df["powertrain_type"]))

            # Create powertrain_type column and fill it
            df["powertrain_type"] = df["car_trim"].map(powertrain_mapping)

            # Move the powertrain_type column to be right after body_type
            powertrain_type_column = df.pop("powertrain_type")
            df.insert(body_type_pos + 1, "powertrain_type", powertrain_type_column)

            # Count successful mappings
            filled_count = df["powertrain_type"].notna().sum()
            total_count = len(df)
            unfilled_count = total_count - filled_count

            print(f"Successfully added 'powertrain_type' column after 'body_type'")
            print(f"Filled powertrain type for {filled_count} out of {total_count} cars")
            if unfilled_count > 0:
                unfilled_trims = df[df["powertrain_type"].isna()]["car_trim"].unique()
                print(f"Could not determine powertrain type for {unfilled_count} cars from {len(unfilled_trims)} trims")
                print(f"First 5 missing trims:")
                for trim in list(unfilled_trims)[:5]:
                    print(f"  - {trim}")

            # Show powertrain type distribution
            powertrain_counts = df["powertrain_type"].value_counts()
            print(f"Powertrain type distribution:")
            for powertrain_type, count in powertrain_counts.items():
                print(f"  {powertrain_type}: {count}")

            # Make powertrain type adjustments
            print("\nMaking powertrain type adjustments...")

            # Set santa-fe models to Plug_in_Hybrid_PHEV
            santa_fe_mask = df["car_model"] == "santa-fe"
            santa_fe_count = santa_fe_mask.sum()
            if santa_fe_count > 0:
                df.loc[santa_fe_mask, "powertrain_type"] = "Plug_in_Hybrid_PHEV"
                print(f"Set {santa_fe_count} santa-fe models to Plug_in_Hybrid_PHEV")

            # Set MG-4 models to Internal_Combustion_Engine
            mg4_mask = df["car_model"] == "mg-4"
            mg4_count = mg4_mask.sum()
            if mg4_count > 0:
                df.loc[mg4_mask, "powertrain_type"] = "Internal_Combustion_Engine"
                print(f"Set {mg4_count} MG-4 models to Internal_Combustion_Engine")

            # Set x-trail models to Plug_in_Hybrid_PHEV
            xtrail_mask = df["car_model"] == "x-trail"
            xtrail_count = xtrail_mask.sum()
            if xtrail_count > 0:
                df.loc[xtrail_mask, "powertrain_type"] = "Plug_in_Hybrid_PHEV"
                print(f"Set {xtrail_count} x-trail models to Plug_in_Hybrid_PHEV")

        except FileNotFoundError:
            # Create empty powertrain_type column if file not found
            df.insert(body_type_pos + 1, "powertrain_type", pd.NA)
            print("power_train.csv file not found. Created empty 'powertrain_type' column.")
        except Exception as e:
            # Create empty powertrain_type column if any error occurs
            df.insert(body_type_pos + 1, "powertrain_type", pd.NA)
            print(f"Error loading powertrain types: {e}. Created empty 'powertrain_type' column.")
    else:
        print("Required columns for powertrain classification not found, skipping powertrain type creation.")

    # Fix car_brand values
    print("\nFixing car_brand values...")
    if "car_brand" in df.columns:
        # Replace moris-garage with MG
        moris_count = (df["car_brand"] == "moris-garage").sum()
        if moris_count > 0:
            df["car_brand"] = df["car_brand"].replace("moris-garage", "MG")
            print(f"Replaced 'moris-garage' with 'MG' in {moris_count} rows")

        # Replace Citroën with Citroen
        citroen_count = (df["car_brand"] == "CitroÃ«n").sum()
        if citroen_count > 0:
            df["car_brand"] = df["car_brand"].replace("CitroÃ«n", "Citroen")
            print(f"Replaced 'CitroÃ«n' with 'Citroen' in {citroen_count} rows")

    # Add id column as the first column
    df.insert(0, 'id', range(1, len(df) + 1))
    print(f"Added 'id' column as first column with values from 1 to {len(df)}")

    # Save back to processed_data.csv
    df.to_csv(dst, index=False)
    print(f"Processed data saved to '{dst}'")

if __name__ == "__main__":
    main()
