#!/usr/bin/env python3
"""
Tableau XML to TWBX Packager

This module provides functionality to:
1. Pack extracted Tableau folders back into .twbx files
2. Remove Mac-specific files (__MACOSX, .DS_Store)
3. Remove bracket prefix from final filename
4. Move packaged files to output/twbx directory

The module is designed to be imported and used by other scripts.
"""

import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict, Tuple


# Global constants
XML_SOURCE_DIR = Path("tableau_processor/xml_of_twbx")
OUTPUT_TWBX_DIR = Path("output/twbx")


class TableauPackager:
    """
    Class for packaging extracted Tableau folders back into .twbx files.
    
    This class handles:
    - Cleaning Mac-specific files
    - Zipping folder contents
    - Renaming to .twbx
    - Removing bracket prefixes
    - Moving to output directory
    """
    
    def __init__(self, source_dir: str | Path = None, output_dir: str | Path = None):
        """
        Initialize the TableauPackager.
        
        Args:
            source_dir: Directory containing extracted Tableau folders.
                       If None, uses the default XML_SOURCE_DIR.
            output_dir: Directory for output .twbx files.
                       If None, uses the default OUTPUT_TWBX_DIR.
        """
        self.source_dir = Path(source_dir) if source_dir else XML_SOURCE_DIR
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_TWBX_DIR
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def list_extracted_folders(self) -> List[Path]:
        """
        List all extracted Tableau folders in the source directory.
        Excludes Python files and other non-folder items.
        
        Returns:
            List of Path objects for extracted folders
        """
        if not self.source_dir.exists():
            return []
        
        folders = []
        for item in self.source_dir.iterdir():
            # Only include directories, exclude Python files
            if item.is_dir() and not item.name.startswith('.'):
                folders.append(item)
        
        return folders
    
    def clean_mac_files(self, folder_path: Path) -> int:
        """
        Remove Mac-specific files from the folder tree.
        Removes: __MACOSX folders and .DS_Store files
        
        Args:
            folder_path: Path to the folder to clean
            
        Returns:
            Number of items removed
        """
        removed_count = 0
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(folder_path, topdown=False):
            # Remove .DS_Store files
            for file in files:
                if file == '.DS_Store':
                    file_path = Path(root) / file
                    try:
                        file_path.unlink()
                        removed_count += 1
                    except Exception as e:
                        print(f"Warning: Could not remove {file_path}: {e}")
            
            # Remove __MACOSX directories
            for dir_name in dirs:
                if dir_name == '__MACOSX':
                    dir_path = Path(root) / dir_name
                    try:
                        shutil.rmtree(dir_path)
                        removed_count += 1
                    except Exception as e:
                        print(f"Warning: Could not remove {dir_path}: {e}")
        
        return removed_count
    
    def remove_bracket_prefix(self, folder_name: str) -> str:
        """
        Remove bracket prefix from folder name.
        Example: "[market_share] Online Travel Market Share Report, 2025-10"
                -> "Online Travel Market Share Report, 2025-10"
        
        Args:
            folder_name: Original folder name with bracket prefix
            
        Returns:
            Cleaned folder name without bracket prefix
        """
        # Pattern: [anything] followed by space and the rest
        import re
        match = re.match(r'\[.*?\]\s*(.*)', folder_name)
        if match:
            return match.group(1)
        return folder_name
    
    def zip_folder(self, folder_path: Path, zip_path: Path) -> bool:
        """
        Zip the contents of a folder.
        
        Args:
            folder_path: Path to the folder to zip
            zip_path: Path where the zip file should be created
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through all files and folders
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = Path(root) / file
                        # Calculate relative path from folder_path
                        arcname = file_path.relative_to(folder_path)
                        zipf.write(file_path, arcname)
            
            return True
        except Exception as e:
            print(f"Error zipping {folder_path}: {e}")
            return False
    
    def package_folder(self, folder_path: Path) -> Tuple[bool, str]:
        """
        Package a single extracted folder into a .twbx file.
        
        Process:
        1. Clean Mac-specific files
        2. Zip the folder contents
        3. Rename to .twbx
        4. Remove bracket prefix from filename
        5. Move to output directory
        
        Args:
            folder_path: Path to the extracted folder
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Step 1: Clean Mac files
            removed = self.clean_mac_files(folder_path)
            if removed > 0:
                print(f"  Cleaned {removed} Mac-specific files/folders")
            
            # Step 2: Create temporary zip file
            temp_zip = self.source_dir / f"{folder_path.name}.zip"
            if not self.zip_folder(folder_path, temp_zip):
                return False, f"Failed to zip {folder_path.name}"
            
            # Step 3: Determine final filename (remove bracket prefix)
            clean_name = self.remove_bracket_prefix(folder_path.name)
            final_twbx = self.output_dir / f"{clean_name}.twbx"
            
            # Step 4: Move and rename to .twbx
            shutil.move(str(temp_zip), str(final_twbx))
            
            return True, f"Successfully packaged {folder_path.name} -> {final_twbx.name}"
            
        except Exception as e:
            return False, f"Error packaging {folder_path.name}: {str(e)}"
    
    def package_all_folders(self) -> Dict[str, str]:
        """
        Package all extracted folders in the source directory.
        
        Returns:
            Dictionary of folder names to status messages
        """
        results = {}
        folders = self.list_extracted_folders()
        
        if not folders:
            return {"status": "No folders found to package"}
        
        print(f"Found {len(folders)} folder(s) to package:")
        for folder in folders:
            print(f"  - {folder.name}")
        
        print("\nPackaging folders...")
        for folder_path in folders:
            print(f"\nProcessing: {folder_path.name}")
            success, message = self.package_folder(folder_path)
            results[folder_path.name] = message
            print(f"  {message}")
        
        return results


def package_twbx_files(source_dir: str | Path = None, output_dir: str | Path = None) -> Dict[str, str]:
    """
    Convenience function to package all extracted Tableau folders.
    
    Args:
        source_dir: Directory containing extracted Tableau folders.
                   If None, uses the default XML_SOURCE_DIR.
        output_dir: Directory for output .twbx files.
                   If None, uses the default OUTPUT_TWBX_DIR.
        
    Returns:
        Dictionary of folder names to status messages
    """
    packager = TableauPackager(source_dir, output_dir)
    return packager.package_all_folders()


__all__ = ["TableauPackager", "package_twbx_files"]


if __name__ == "__main__":
    # Run with default directories
    print("Tableau TWBX Packager")
    print("=" * 50)
    results = package_twbx_files()

