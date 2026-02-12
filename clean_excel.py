
import pandas as pd
import os

excel_path = "/Users/jxiaox/Investment/Spider_XHS/datas/excel_datas/5b6150c56b58b741e26b8c7f.xlsx"

if not os.path.exists(excel_path):
    print(f"File not found: {excel_path}")
    exit(1)

print(f"Reading {excel_path}...")
try:
    df = pd.read_excel(excel_path)
    count_before = len(df)
    print(f"Rows before: {count_before}")
    
    # Remove duplicates based on '笔记ID' (Note ID) column
    # Assuming column name is '笔记ID', checking first
    if '笔记ID' in df.columns:
        df_cleaned = df.drop_duplicates(subset=['笔记ID'], keep='first')
    elif 'note_id' in df.columns:
        df_cleaned = df.drop_duplicates(subset=['note_id'], keep='first')
        print("Used 'note_id' column")
    else:
        # Check first column if specific name not found
        first_col = df.columns[0]
        print(f"Column '笔记ID' not found. Using first column '{first_col}' for deduplication check (assuming Note ID first)")
        df_cleaned = df.drop_duplicates(subset=[first_col], keep='first')

    count_after = len(df_cleaned)
    print(f"Rows after: {count_after}")
    print(f"Removed duplicates: {count_before - count_after}")
    
    # Save back to same file
    df_cleaned.to_excel(excel_path, index=False)
    print("Cleaned file saved.")
    
except Exception as e:
    print(f"Error processing excel: {e}")
