import os
import shutil
import pandas as pd
from datetime import datetime

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

    # Add id column as the first column
    df.insert(0, 'id', range(1, len(df) + 1))
    print(f"Added 'id' column as first column with values from 1 to {len(df)}")

    # Save back to processed_data.csv
    df.to_csv(dst, index=False)
    print(f"Processed data saved to '{dst}'")

if __name__ == "__main__":
    main()
