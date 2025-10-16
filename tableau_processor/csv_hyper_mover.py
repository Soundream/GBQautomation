import os
import shutil
import uuid
import hashlib
import datetime
import json
from pathlib import Path

# Get current year and month for folder naming
CURRENT_DATE = datetime.datetime.now()
YEAR_MONTH = CURRENT_DATE.strftime("%Y-%m")

def generate_federated_name(filename):
    """Generate unique federated name using uuid and file hash"""
    # Create a unique identifier based on filename and a random uuid
    unique_id = str(uuid.uuid4()) + "federated_" + filename
    # Create hash
    hash_obj = hashlib.md5(unique_id.encode())
    # Get the hexdigest and slice to appropriate length
    federated_id = hash_obj.hexdigest()[:26]
    return f"federated.{federated_id}"

def generate_textscan_name(filename):
    """Generate unique textscan name using uuid and file hash"""
    # Similar approach but with a different prefix and length
    unique_id = str(uuid.uuid4()) + "textscan_" + filename
    hash_obj = hashlib.md5(unique_id.encode())
    textscan_id = hash_obj.hexdigest()[:26]
    return f"textscan.{textscan_id}"

def generate_object_id(filename):
    """Generate unique object id using filename and hash"""
    unique_id = str(uuid.uuid4()) + filename
    hash_obj = hashlib.md5(unique_id.encode())
    obj_id = hash_obj.hexdigest().upper()[:32]
    return f"[{filename}_{obj_id}]"

def move_and_generate_metadata(base_path=None):
    """
    Main function to move CSV and hyper files and generate metadata
    
    Args:
        base_path (str, optional): Base path of the project. If None, uses current directory's parent
    
    Returns:
        dict: Metadata for all moved files organized by folder and caption
    """
    # Set base path if not provided
    if base_path is None:
        base_path = str(Path(__file__).parent.parent)
    
    
    # Define task folders
    tasks = ["key_brands", "market_share", "shopcash"]
    
    # Initialize metadata dictionary
    all_metadata = {}
    
    # Process each task
    for task in tasks:
        # Define source and destination paths
        csv_source_path = os.path.join(base_path, "output", "csv", task)
        hyper_source_path = os.path.join(base_path, "output", "hyper", task)
        
        # Find the target directory in xml_of_twbx that starts with [task]
        xml_base_path = os.path.join(base_path, "tableau_processor", "xml_of_twbx")
        target_folder = None
        
        for folder in os.listdir(xml_base_path):
            if folder.startswith(f"[{task}]"):
                target_folder = folder
                break
        
        if not target_folder:
            print(f"Warning: No target folder found for task '{task}'. Skipping.")
            continue
        
        # Create destination directories
        csv_dest_path = os.path.join(xml_base_path, target_folder, "Data", f"{YEAR_MONTH}-csv")
        hyper_dest_path = os.path.join(xml_base_path, target_folder, "Data", f"{YEAR_MONTH}-hyper")
        
        os.makedirs(csv_dest_path, exist_ok=True)
        os.makedirs(hyper_dest_path, exist_ok=True)
        
        # Initialize metadata for this task
        task_metadata = {}
        
        # Process CSV files
        if os.path.exists(csv_source_path):
            for filename in os.listdir(csv_source_path):
                if filename.endswith(".csv"):
                    # Copy file to destination
                    source_file = os.path.join(csv_source_path, filename)
                    dest_file = os.path.join(csv_dest_path, filename)
                    shutil.copy2(source_file, dest_file)
                    
                    # Generate metadata
                    caption = os.path.splitext(filename)[0]
                    file_key = caption[7:]
                    federated_name = generate_federated_name(filename)
                    textscan_name = generate_textscan_name(filename)
                    object_id = generate_object_id(filename)
                    
                    # Store metadata
                    task_metadata[file_key] = {
                        "caption": caption,
                        "federated_name": federated_name,
                        "textscan_name": textscan_name,
                        "object_id": object_id,
                        "file_type": "csv",
                        "file_path": dest_file
                    }
        
        # Process hyper files
        if os.path.exists(hyper_source_path):
            for filename in os.listdir(hyper_source_path):
                if filename.endswith(".hyper"):
                    # Copy file to destination
                    source_file = os.path.join(hyper_source_path, filename)
                    dest_file = os.path.join(hyper_dest_path, filename)
                    shutil.copy2(source_file, dest_file)
        
        # Add this task's metadata to the overall metadata
        all_metadata[task] = task_metadata
        
        print(f"Processed {task}: Copied files and generated metadata")
    
    # Save metadata as JSON (optional)
    metadata_path = os.path.join(base_path, "tableau_processor", "current_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    print(f"Metadata saved to {metadata_path}")
    
    return all_metadata

if __name__ == "__main__":
    # When run directly, execute the function
    metadata = move_and_generate_metadata()
    print(f"Generated metadata for {sum(len(task_data) for task_data in metadata.values())} files")