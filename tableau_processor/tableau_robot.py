#!/usr/bin/env python3
"""
Simple script to read Tableau workbook (.twb) files and extract the first worksheet title.
"""

import xml.etree.ElementTree as ET
import sys
from pathlib import Path


def read_tableau_first_sheet_title(twb_file_path):
    """
    Reads a Tableau workbook (.twb) file and returns the title of the first worksheet.
    
    Args:
        twb_file_path: Path to the .twb file
        
    Returns:
        str: The title of the first worksheet found, or None if no worksheet is found
    """
    try:
        # Parse the XML file
        tree = ET.parse(twb_file_path)
        root = tree.getroot()
        
        # Try to find worksheet elements - there are a couple of possible paths
        # Method 1: Direct worksheets under workbook
        worksheets = root.findall(".//worksheet")
        
        # Method 2: Sheets in windows
        if not worksheets:
            worksheets = root.findall(".//window/worksheet")
            
        # Method 3: Look for sheet-name elements
        if not worksheets:
            sheet_names = root.findall(".//sheet-name")
            if sheet_names:
                return sheet_names[0].text
        
        # If worksheets were found, return the name of the first one
        if worksheets:
            return worksheets[0].get('name')
            
        return None
        
    except Exception as e:
        print(f"Error reading Tableau file: {e}")
        return None


if __name__ == "__main__":
    # If file path provided as argument, use it, otherwise ask for input
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("Enter path to Tableau workbook (.twb) file: ")
    
    title = read_tableau_first_sheet_title(file_path)
    if title:
        print(f"First worksheet title: {title}")
    else:
        print("Could not find a worksheet title in the file.")
