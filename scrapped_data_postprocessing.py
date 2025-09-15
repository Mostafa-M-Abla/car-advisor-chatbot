import os
import shutil
import pandas as pd

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

    # Save back to processed_data.csv
    df.to_csv(dst, index=False)
    print(f"Processed data saved to '{dst}'")

if __name__ == "__main__":
    main()
