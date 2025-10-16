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
                    clean_pattern = pattern.replace("yyyymm_", "")
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
    
    # Generate filenames with and without prefix
    filenames_with_prefix = [f"{yyyymm}_{pattern}" for pattern in patterns]
    return filenames_with_prefix, patterns


def remove_yyyymm_prefix(filename):
    """Remove YYYYMM_ prefix from a filename"""
    return re.sub(r'^\d{6}_', '', filename)


def extract_timestamp_from_caption(caption):
    """Extract YYYYMM timestamp from caption like '202508_web_traffic' or '202508_web_traffic 01'"""
    match = re.match(r'^(\d{6})_', caption)
    if match:
        return match.group(1)
    return None


def has_suffix(caption, base_pattern):
    """Check if caption has suffix beyond the base pattern"""
    # Remove .csv extension if present
    clean_caption = caption.replace('.csv', '')
    # Check if caption is longer than the base pattern (YYYYMM_key)
    return len(clean_caption) > len(base_pattern)


def should_update_metadata(current_caption, new_caption, base_pattern, current_object_id=""):
    """Determine if new metadata should replace current metadata"""
    # Extract timestamps
    current_timestamp = extract_timestamp_from_caption(current_caption)
    new_timestamp = extract_timestamp_from_caption(new_caption)
    
    if not current_timestamp or not new_timestamp:
        # If we can't extract timestamps, default to updating
        return True
    
    # Compare timestamps
    if new_timestamp > current_timestamp:
        # New file is newer, always update
        return True
    elif new_timestamp < current_timestamp:
        # New file is older, don't update
        return False
    else:
        # Same timestamp, check for suffix
        new_has_suffix = has_suffix(new_caption, base_pattern)
        if new_has_suffix:
            # New file has suffix, update
            return True
        elif not current_object_id:
            # Same timestamp, no suffix, but current object_id is empty, update
            return True
        else:
            # New file has no suffix and current has object_id, don't update
            return False


def extract_metadata_from_twb(twb_path, task, expected_filenames, base_patterns, existing_metadata=None):
    """Extract metadata for specified filenames from a TWB file"""
    try:
        # print(f"Extracting metadata from {twb_path}")
        # Register namespace to handle Tableau XML correctly
        ET.register_namespace('', "http://www.tableausoftware.com/xml/tableau")
        tree = ET.parse(twb_path)
        root = tree.getroot()
        
        metadata = {}
        if existing_metadata is None:
            existing_metadata = {}
        
        # Create a mapping from prefixed to unprefixed names
        prefix_map = {prefixed: unprefixed for prefixed, unprefixed in zip(expected_filenames, base_patterns)}
        
        # Find all datasources
        for datasource in root.findall(".//datasource"):
            caption = datasource.get('caption', '')
            
            # Check if this datasource matches any of our expected filenames
            matched = False
            matched_base_name = None
            matched_prefixed_name = None
            for prefixed_name in expected_filenames:
                if caption == prefixed_name or caption == f"{prefixed_name}.csv":
                    matched = True
                    matched_base_name = prefix_map.get(prefixed_name)
                    matched_prefixed_name = prefixed_name
                    break
                    
            if not matched:
                continue
            
            # Check if we should update this metadata
            if matched_base_name in existing_metadata:
                current_caption = existing_metadata[matched_base_name].get('caption', '')
                current_object_id = existing_metadata[matched_base_name].get('object_id', '')
                if not should_update_metadata(current_caption, caption, matched_prefixed_name, current_object_id):
                    continue
            
            # print(f"Found matching datasource with caption: {caption}, base name: {matched_base_name}")
            
            # Extract federated name
            federated_name = datasource.get('name', '')
            
            # Find textscan connection - more direct approach
            textscan_name = ""
            # First try looking in named-connections directly under this datasource
            named_connections = datasource.find(".//named-connections")
            if named_connections is not None:
                for named_conn in named_connections.findall("./named-connection"):
                    conn_name = named_conn.get('name', '')
                    if 'textscan' in conn_name:
                        textscan_name = conn_name
                        break
            
            # If not found, search more broadly (fallback)
            if not textscan_name:
                for named_conn in root.findall(".//named-connection"):
                    if named_conn.get('caption') == caption and 'textscan' in named_conn.get('name', ''):
                        textscan_name = named_conn.get('name', '')
                        break
            
            # Find object-id - improved logic
            object_id = ""
            # First try to find object-id in the same datasource
            datasource_metadata = datasource.find(".//metadata-records")
            if datasource_metadata is not None:
                for metadata_record in datasource_metadata.findall("./metadata-record"):
                    obj_id_elem = metadata_record.find("./object-id")
                    if obj_id_elem is not None and obj_id_elem.text:
                        # Check if this object-id is related to our caption
                        parent_elem = metadata_record.find("./parent-name")
                        if parent_elem is not None and parent_elem.text:
                            # Remove .csv extension for comparison
                            clean_caption = caption.replace('.csv', '')
                            clean_parent = parent_elem.text.replace('.csv', '')
                            if clean_caption in clean_parent or clean_parent in clean_caption:
                                object_id = obj_id_elem.text
                                break
            
            # If not found in datasource metadata, search globally
            if not object_id:
                for metadata_record in root.findall(".//metadata-record"):
                    obj_id_elem = metadata_record.find("./object-id")
                    parent_elem = metadata_record.find("./parent-name")
                    
                    if (obj_id_elem is not None and obj_id_elem.text and 
                        parent_elem is not None and parent_elem.text):
                        # Remove .csv extension for comparison
                        clean_caption = caption.replace('.csv', '')
                        clean_parent = parent_elem.text.replace('.csv', '')
                        if clean_caption in clean_parent or clean_parent in clean_caption:
                            object_id = obj_id_elem.text
                            break
            
            # Store metadata with the base name (without YYYYMM prefix) as the key
            if matched_base_name:
                metadata[matched_base_name] = {
                    "caption": caption,
                    "federated_name": federated_name,
                    "textscan_name": textscan_name,
                    "object_id": object_id,
                    "twb_file": os.path.basename(twb_path)
                }
                
                print(f"Extracted metadata for {matched_base_name}: caption={caption}, federated={federated_name}, textscan={textscan_name}, object_id={object_id}")
            
        return metadata
    
    except Exception as e:
        import traceback
        print(f"Error extracting metadata from {twb_path}: {str(e)}")
        print(traceback.format_exc())
        return {}


def scan_task_folders(base_path=None):
    """Scan task folders in xml_of_twbx and extract metadata"""
    if base_path is None:
        base_path = str(Path(__file__).parent.parent)
    
    xml_twbx_path = os.path.join(base_path, "tableau_processor", "xml_of_twbx")
    
    # Load existing metadata if it exists
    existing_metadata_path = os.path.join(base_path, "tableau_processor", "template_metadata.json")
    all_metadata = {}
    if os.path.exists(existing_metadata_path):
        try:
            with open(existing_metadata_path, 'r') as f:
                all_metadata = json.load(f)
            print(f"Loaded existing metadata with {sum(len(task_data) for task_data in all_metadata.values())} entries")
        except Exception as e:
            print(f"Warning: Could not load existing metadata: {e}")
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
        # print(f"Processing task: {task}, source: {source_year}-{source_month}, data: {data_year}-{data_month}")
        
        # Generate expected filenames
        expected_filenames, base_patterns = generate_expected_filenames(task, data_year, data_month)
        # print(f"Looking for filenames: {expected_filenames}")
        # print(f"Base patterns: {base_patterns}")

        if not expected_filenames:
            continue
            
        # Get existing metadata for this task
        existing_task_metadata = all_metadata.get(task, {})
        
        # Find TWB files in the folder
        task_metadata = existing_task_metadata.copy()  # Start with existing metadata
        for file in os.listdir(folder_path):
            if file.endswith(".twb"):
                twb_path = os.path.join(folder_path, file)
                metadata = extract_metadata_from_twb(twb_path, task, expected_filenames, base_patterns, existing_task_metadata)
                task_metadata.update(metadata)  # This will update with new metadata
        
        # Update overall metadata
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