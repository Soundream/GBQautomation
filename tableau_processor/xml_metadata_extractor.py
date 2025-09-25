import os
import re
import json
import xml.etree.ElementTree as ET
import datetime
from pathlib import Path


def get_task_from_folder_name(folder_name):
    """Extract task name from folder name like '[shopcash] Ecommerce Key Markets Report, 2025-08'"""
    match = re.match(r'\[(.*?)\]', folder_name)
    if match:
        return match.group(1)
    return None


def extract_date_from_folder_name(folder_name):
    """Extract YYYY-MM from folder name like '[shopcash] Ecommerce Key Markets Report, 2025-08'"""
    match = re.search(r'(\d{4})-(\d{2})', folder_name)
    if match:
        return match.group(1), match.group(2)  # year, month
    return None, None


def get_next_month(year, month):
    """Get the next month after the given year and month"""
    year = int(year)
    month = int(month)
    
    if month == 12:
        return str(year + 1), "01"
    else:
        return str(year), f"{month + 1:02d}"


def load_filename_patterns(task, base_path=None):
    """Load filename patterns for a specific task from queries.json"""
    if base_path is None:
        base_path = str(Path(__file__).parent.parent)
    
    queries_path = os.path.join(base_path, "data_collection", "sql", "queries.json")
    
    with open(queries_path, 'r') as f:
        queries_data = json.load(f)
    
    # Find patterns for the specified task
    for folder_info in queries_data.get("folders", []):
        if folder_info.get("folder") == task:
            patterns = []
            for query in folder_info.get("queries", []):
                pattern = query.get("filename_pattern")
                if pattern:
                    # Remove the yyyymm prefix as we'll add it later
                    clean_pattern = pattern.replace("yyyymm", "")
                    patterns.append(clean_pattern)
            return patterns
    
    return []


def generate_expected_filenames(task, year, month):
    """Generate expected filenames based on task, year, and month"""
    patterns = load_filename_patterns(task)
    
    if not patterns:
        print(f"Warning: No patterns found for task '{task}'")
        return []
    
    # Format as YYYYMM
    yyyymm = f"{year}{month}"
    
    # Generate filenames
    filenames = [f"{yyyymm}{pattern}" for pattern in patterns]
    return filenames


def extract_metadata_from_twb(twb_path, task, expected_filenames):
    """Extract metadata for specified filenames from a TWB file"""
    try:
        # Register namespace to handle Tableau XML correctly
        ET.register_namespace('', "http://www.tableausoftware.com/xml/tableau")
        tree = ET.parse(twb_path)
        root = tree.getroot()
        
        metadata = {}
        
        # Find all datasources
        for datasource in root.findall(".//datasource"):
            caption = datasource.get('caption', '')
            
            # Check if this datasource matches any of our expected filenames
            matched = False
            for filename in expected_filenames:
                if caption == filename or caption == f"{filename}.csv":
                    matched = True
                    break
                    
            if not matched:
                continue
                
            # Extract federated name
            federated_name = datasource.get('name', '')
            
            # Find textscan connection
            textscan_name = ""
            for named_connection in datasource.findall(".//named-connection"):
                if 'textscan' in named_connection.get('name', ''):
                    textscan_name = named_connection.get('name', '')
                    break
            
            # Find object-id (which might be farther away in the XML)
            object_id = ""
            for metadata_record in root.findall(f".//metadata-record[.//remote-alias]"):
                family_elem = metadata_record.find(".//family")
                obj_id_elem = metadata_record.find(".//object-id")
                
                if (family_elem is not None and obj_id_elem is not None and 
                    caption in family_elem.text and obj_id_elem.text):
                    object_id = obj_id_elem.text
                    break
            
            # Store metadata
            metadata[caption] = {
                "caption": caption,
                "federated_name": federated_name,
                "textscan_name": textscan_name,
                "object_id": object_id,
                "twb_file": os.path.basename(twb_path)
            }
            
        return metadata
    
    except Exception as e:
        print(f"Error extracting metadata from {twb_path}: {str(e)}")
        return {}


def scan_task_folders(base_path=None):
    """Scan task folders in xml_of_twbx and extract metadata"""
    if base_path is None:
        base_path = str(Path(__file__).parent.parent)
    
    xml_twbx_path = os.path.join(base_path, "tableau_processor", "xml_of_twbx")
    
    all_metadata = {}
    
    # Only look at immediate subfolders of xml_of_twbx
    for folder_name in os.listdir(xml_twbx_path):
        folder_path = os.path.join(xml_twbx_path, folder_name)
        
        # Skip if not a directory or doesn't start with [
        if not os.path.isdir(folder_path) or not folder_name.startswith('['):
            continue
        
        # Extract task and date from folder name
        task = get_task_from_folder_name(folder_name)
        source_year, source_month = extract_date_from_folder_name(folder_name)
        
        if not task or not source_year or not source_month:
            print(f"Warning: Could not extract task or date from folder '{folder_name}'. Skipping.")
            continue
            
        # Get next month (data month)
        data_year, data_month = get_next_month(source_year, source_month)
        print(f"Processing task: {task}, source: {source_year}-{source_month}, data: {data_year}-{data_month}")
        
        # Generate expected filenames
        expected_filenames = generate_expected_filenames(task, data_year, data_month)
        if not expected_filenames:
            continue
            
        # Find TWB files in the folder
        task_metadata = {}
        for file in os.listdir(folder_path):
            if file.endswith(".twb"):
                twb_path = os.path.join(folder_path, file)
                metadata = extract_metadata_from_twb(twb_path, task, expected_filenames)
                task_metadata.update(metadata)
        
        # Add to overall metadata
        if task_metadata:
            all_metadata[task] = task_metadata
    
    # Save to JSON file
    output_path = os.path.join(base_path, "tableau_processor", "template_metadata.json")
    with open(output_path, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    print(f"Metadata extracted and saved to {output_path}")
    return all_metadata


if __name__ == "__main__":
    metadata = scan_task_folders()
    file_count = sum(len(task_data) for task_data in metadata.values())
    print(f"Extracted metadata for {file_count} datasources across {len(metadata)} tasks")