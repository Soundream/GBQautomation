#!/usr/bin/env python3
"""
Tableau TWBX to XML Converter

This module provides functionality to:
1. Check for existing extracted Tableau files
2. Convert Tableau .twbx files to .zip and extract them
3. Identify file types based on specific naming patterns

The module is designed to be imported and used by the main runner script.
"""

import os
import shutil
import zipfile
import re
from pathlib import Path
from typing import  List, Dict, Tuple


# Global constants for Tableau file types
TABLEAU_TYPE_KEY_BRANDS = "key_brands"
TABLEAU_TYPE_MARKET_SHARE = "market_share"
TABLEAU_TYPE_SHOPCASH = "shopcash"
TABLEAU_TYPE_UNKNOWN = "unknown"

# Global constant for output directory - same directory as this script
OUTPUT_DIR = Path(__file__).parent

# Global constant for templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "tableau_files" / "templates"


class TableauExtractor:
    """
    Class for extracting and processing Tableau .twbx files.
    
    This class handles the conversion of .twbx files to .zip archives,
    extraction of their contents, and identification of file types.
    """
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize the TableauExtractor.
        
        Args:
            templates_dir: Directory containing template .twbx files.
                          If None, uses the default TEMPLATES_DIR.
        """
        self.templates_dir = Path(templates_dir) if templates_dir else TEMPLATES_DIR
        
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    def list_tableau_files(self) -> List[Path]:
        """
        List all .twbx files in the templates directory.
        
        Returns:
            List of Path objects for .twbx files
        """
        return list(self.templates_dir.glob("*.twbx"))
    
    def identify_file_type(self, file_path: Path) -> str:
        """
        Identify the type of a Tableau file based on its filename.
        
        Specific file mapping rules:
        - Files containing "ecommerce" -> SHOPCASH
        - Files containing "brands" -> KEY_BRANDS
        - Files containing "market share" -> MARKET_SHARE
        
        Args:
            file_path: Path to the Tableau file
            
        Returns:
            String representing the file type
        """
        filename = file_path.name.lower()
        
        if "ecommerce" in filename:
            return TABLEAU_TYPE_SHOPCASH
        elif "brands" in filename:
            return TABLEAU_TYPE_KEY_BRANDS
        elif "market share" in filename:
            return TABLEAU_TYPE_MARKET_SHARE
        else:
            return TABLEAU_TYPE_UNKNOWN

    def get_extraction_path(self, file_path: Path) -> Path:
        """
        Determine the extraction path for a Tableau file.
        
        Args:
            file_path: Path to the Tableau file
            
        Returns:
            Path where the file should be extracted
        """
        file_type = self.identify_file_type(file_path)
        
        # Create a directory name based on the file type and original filename
        # Remove the .twbx extension and create a suitable directory name with type prefix
        base_name = file_path.stem
        dir_name = f"[{file_type}] {base_name}"
        
        return OUTPUT_DIR / dir_name
    
    def is_already_extracted(self, file_path: Path) -> bool:
        """
        Check if a Tableau file has already been extracted.
        
        Args:
            file_path: Path to the Tableau file
            
        Returns:
            True if the file has already been extracted, False otherwise
        """
        extraction_path = self.get_extraction_path(file_path)
        
        # Check if the extraction directory exists and contains expected files
        # This is a simple check that can be expanded based on specific requirements
        if extraction_path.exists():
            # Check for the presence of .twb file which indicates a successful extraction
            twb_files = list(extraction_path.glob("*.twb"))
            return len(twb_files) > 0
            
        return False
    
    def extract_tableau_file(self, file_path: Path, force: bool = False) -> Tuple[bool, str]:
        """
        Convert .twbx to .zip and extract its contents.
        
        Args:
            file_path: Path to the Tableau file
            force: If True, extract even if the file appears to be already extracted
            
        Returns:
            Tuple of (success, message)
        """
        if not force and self.is_already_extracted(file_path):
            return False, f"File {file_path.name} already extracted"
        
        extraction_path = self.get_extraction_path(file_path)
        
        # Create temporary zip file path
        temp_zip = OUTPUT_DIR / f"{file_path.stem}.zip"
        
        try:
            # Copy the .twbx file to a .zip file
            shutil.copy2(file_path, temp_zip)
            
            # Create the extraction directory
            os.makedirs(extraction_path, exist_ok=True)
            
            # Extract the zip file
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(extraction_path)
            
            # Remove the temporary zip file
            os.remove(temp_zip)
            
            return True, f"Successfully extracted {file_path.name} to {extraction_path}"
            
        except Exception as e:
            return False, f"Error extracting {file_path.name}: {str(e)}"
    
    def extract_all_templates(self, force: bool = False) -> Dict[str, str]:
        """
        Extract all template files in the templates directory.
        
        Args:
            force: If True, extract even if files appear to be already extracted
            
        Returns:
            Dictionary of filenames to status messages
        """
        results = {}
        
        for file_path in self.list_tableau_files():
            success, message = self.extract_tableau_file(file_path, force)
            results[file_path.name] = message
        
        return results


def extract_templates(templates_dir: str = None, force: bool = False) -> Dict[str, str]:
    """
    Convenience function to extract all template files.
    
    Args:
        templates_dir: Directory containing template .twbx files.
                      If None, uses the default TEMPLATES_DIR.
        force: If True, extract even if files appear to be already extracted
        
    Returns:
        Dictionary of filenames to status messages
    """
    extractor = TableauExtractor(templates_dir)
    return extractor.extract_all_templates(force)


if __name__ == "__main__":
    # Run with default templates directory
    results = extract_templates()
    for filename, message in results.items():
        print(f"{filename}: {message}")