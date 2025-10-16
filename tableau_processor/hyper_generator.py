#!/usr/bin/env python3
"""
CSV to Hyper File Converter

Convert CSV files to Tableau Hyper format using Tableau Hyper API.
Supports reading from directory structure and mapping data types according to rules.
Optimized for performance with batch processing and single Hyper service.
"""

import os
import json
import shutil
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from tableauhyperapi import HyperProcess, Connection, SqlType, TableDefinition, Inserter, CreateMode

# Global constants for directory structure
CSV_ROOT_DIR = Path("output/csv")
HYPER_ROOT_DIR = Path("output/hyper")
# SUBFOLDERS = ["key_brands", "market_share", "shopcash"]
SUBFOLDERS = ["shopcash"]
RULES_PATH = "tableau_processor/date_rules.json"


def convert_datatype_to_hyper_type(column_name, dtype):
    """
    Convert pandas datatype to Hyper API compatible type
    
    Args:
        column_name: Column name
        dtype: pandas datatype
        
    Returns:
        TableDefinition.Column object
    """
    if pd.api.types.is_integer_dtype(dtype):
        return TableDefinition.Column(column_name, SqlType.big_int())
    elif pd.api.types.is_float_dtype(dtype):
        return TableDefinition.Column(column_name, SqlType.double())
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return TableDefinition.Column(column_name, SqlType.date())
    elif pd.api.types.is_bool_dtype(dtype):
        return TableDefinition.Column(column_name, SqlType.bool())
    else:
        return TableDefinition.Column(column_name, SqlType.text())


def find_date_columns_for_file(df, rules, folder, file_name):
    """
    Identify columns that should be converted to date format based on rules
    
    Args:
        df: DataFrame with data
        rules: Dictionary of date field rules
        folder: Current folder being processed
        file_name: Name of the file being processed
        
    Returns:
        tuple of (list of columns to convert, list of messages about conversions)
    """
    date_columns = []
    messages = []
    
    # Identify columns to be converted to dates
    for col in df.columns:
        for rule_col, folder_rules in rules.items():
            if col == rule_col and folder in folder_rules:
                # Check if the file name matches any pattern in the rules
                for file_pattern in folder_rules[folder]:
                    if file_pattern in file_name:
                        date_columns.append(col)
                        messages.append(f"Converting column '{col}' to date format (file: {file_name})")
                        break
    
    return date_columns, messages


def process_csv_directory(rules_path=RULES_PATH):
    """
    Process CSV directory structure and convert to corresponding Hyper file structure
    
    Args:
        rules_path: Path to JSON file with date field rules
        
    Returns:
        List of generated Hyper file paths
    """
    # Ensure output directory exists
    HYPER_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean output directories
    for folder in SUBFOLDERS:
        folder_path = HYPER_ROOT_DIR / folder
        if folder_path.exists():
            for item in folder_path.glob("*"):
                if item.is_file() and item.name != ".gitkeep":
                    os.remove(item)
                elif item.is_dir():
                    shutil.rmtree(item)
    
    # Load date field rules
    rules = {}
    if Path(rules_path).exists():
        with open(rules_path, 'r') as f:
            rules = json.load(f)
    
    results = []
    conversion_messages = []
    
    # Collect all CSV files to process
    all_csv_files = []
    
    for folder in SUBFOLDERS:
        csv_folder = CSV_ROOT_DIR / folder
        hyper_folder = HYPER_ROOT_DIR / folder
        
        if not csv_folder.exists():
            print(f"Folder does not exist: {csv_folder}")
            continue
        
        # Create output directory
        hyper_folder.mkdir(parents=True, exist_ok=True)
        
        # Collect CSV files
        csv_files = list(csv_folder.glob("*.csv"))
        all_csv_files.extend([(csv_file, hyper_folder / f"{csv_file.stem}.hyper", folder) for csv_file in csv_files])
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("tableau_processor")
    logs_dir.mkdir(exist_ok=True)
    
    # Start a single Hyper process for all files with custom log directory
    with HyperProcess(telemetry=False, parameters={"log_dir": str(logs_dir)}) as hyper:
        # Process all files with progress bar
        for csv_file, hyper_file, folder in tqdm(all_csv_files, desc="Converting CSV to Hyper"):
            file_name = csv_file.stem
            
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Find columns to convert to date format
            date_columns, messages = find_date_columns_for_file(df, rules, folder, file_name)
            conversion_messages.extend(messages)
            
            # Convert identified columns to date format at once
            for col in date_columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception as e:
                    conversion_messages.append(f"Could not convert column '{col}' to date: {e}")
            
            # Ensure output directory exists and remove existing file
            hyper_file = Path(hyper_file)
            hyper_file.parent.mkdir(parents=True, exist_ok=True)
            if hyper_file.exists() and hyper_file.is_file():
                os.remove(hyper_file)
            
            # Create table definition
            columns = [convert_datatype_to_hyper_type(col_name, dtype) for col_name, dtype in df.dtypes.items()]
            table_def = TableDefinition("Extract.Extract", columns)
            
            # Create and populate Hyper file
            with Connection(hyper.endpoint, hyper_file, CreateMode.CREATE_AND_REPLACE) as connection:
                connection.catalog.create_schema("Extract")
                connection.catalog.create_table(table_def)
                
                with Inserter(connection, "Extract.Extract") as inserter:
                    # Prepare all rows as a batch
                    rows_to_insert = []
                    for _, row in df.iterrows():
                        rows_to_insert.append([row[col] if pd.notna(row[col]) else None for col in df.columns])
                    
                    # Batch insert all rows at once
                    inserter.add_rows(rows_to_insert)
            
            results.append(hyper_file)
    
    # Print date conversion messages at the end
    for message in conversion_messages:
        print(message)
    
    return results


if __name__ == "__main__":
    # Process all CSV files
    results = process_csv_directory()
    print(f"Total files generated: {len(results)}")