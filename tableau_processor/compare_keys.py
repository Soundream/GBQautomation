#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
from typing import Dict, Set, Tuple, Any, Optional, List


def print_diff_table(template_data: Dict[str, Any], current_data: Dict[str, Any]) -> None:
    """
    Print a simplified table showing only the differences between template and current files.
    Shows file names directly instead of checkmarks. 
    Removes the redundant File column.
    
    Args:
        template_data: Template metadata JSON data
        current_data: Current metadata JSON data
    """
    # Collect differences
    differences = []
    
    # Check all folders
    all_folders = set(template_data.keys()) | set(current_data.keys())
    
    for folder in all_folders:
        # If folder in both
        if folder in template_data and folder in current_data:
            template_files = set(template_data[folder].keys())
            current_files = set(current_data[folder].keys())
            
            # Files in template but not in current
            for file in template_files - current_files:
                differences.append((folder, file, "--"))
            
            # Files in current but not in template
            for file in current_files - template_files:
                differences.append((folder, "--", file))
        
        # Folder only in template
        elif folder in template_data:
            for file in template_data[folder].keys():
                differences.append((folder, file, "--"))
        
        # Folder only in current
        else:
            for file in current_data[folder].keys():
                differences.append((folder, "--", file))
    
    # If no differences found
    if not differences:
        print("\nNo differences found between template and current files.")
        return
    
    # Calculate column widths
    folder_width = max(len("Folder"), max([len(d[0]) for d in differences]))
    template_width = max(len("Template"), max([len(str(d[1])) for d in differences]))
    current_width = max(len("Current"), max([len(str(d[2])) for d in differences]))
    
    # Print header
    print("\nDifferences between template and current files:")
    print("+" + "-" * (folder_width + 2) + "+" + "-" * (template_width + 2) + "+" + 
          "-" * (current_width + 2) + "+")
    
    print("| {:<{}} | {:<{}} | {:<{}} |".format(
        "Folder", folder_width,
        "Template", template_width,
        "Current", current_width
    ))
    
    print("+" + "=" * (folder_width + 2) + "+" + "=" * (template_width + 2) + "+" + 
          "=" * (current_width + 2) + "+")
    
    # Print difference rows
    current_folder = None
    for folder, template_status, current_status in differences:
        # Only show folder name once per group
        folder_display = folder if folder != current_folder else ""
        current_folder = folder
        
        print("| {:<{}} | {:<{}} | {:<{}} |".format(
            folder_display, folder_width,
            template_status, template_width,
            current_status, current_width
        ))
    
    print("+" + "-" * (folder_width + 2) + "+" + "-" * (template_width + 2) + "+" + 
          "-" * (current_width + 2) + "+")


def print_comparison_table(template_data: Dict[str, Any], current_data: Dict[str, Any]) -> None:
    """
    Print a formatted table comparing template and current metadata files.
    
    Args:
        template_data: Template metadata JSON data
        current_data: Current metadata JSON data
    """
    # Determine column widths for nice formatting
    folder_width = max(len("Folder"), max([len(f) for f in list(template_data.keys()) + list(current_data.keys())]))
    file_width = max(len("File Name"), 
                   max([len(f) for folder in template_data.values() for f in folder.keys()] + 
                       [len(f) for folder in current_data.values() for f in folder.keys()]))
    
    template_width = max(len("Template"), 12)
    current_width = max(len("Current"), 12)
    
    # Print table header
    print("+" + "-" * (folder_width + 2) + "+" + "-" * (file_width + 2) + "+" + 
          "-" * (template_width + 2) + "+" + "-" * (current_width + 2) + "+")
    
    print("| {:<{}} | {:<{}} | {:<{}} | {:<{}} |".format(
        "Folder", folder_width, 
        "File Name", file_width,
        "Template", template_width,
        "Current", current_width
    ))
    
    print("+" + "=" * (folder_width + 2) + "+" + "=" * (file_width + 2) + "+" + 
          "=" * (template_width + 2) + "+" + "=" * (current_width + 2) + "+")
    
    # Get all unique folders
    all_folders = sorted(list(set(list(template_data.keys()) + list(current_data.keys()))))
    
    # Process each folder
    for folder in all_folders:
        folder_in_template = folder in template_data
        folder_in_current = folder in current_data
        
        # If folder exists in both files
        if folder_in_template and folder_in_current:
            template_files = set(template_data[folder].keys())
            current_files = set(current_data[folder].keys())
            all_files = sorted(list(template_files | current_files))
            
            # Print each file in the folder
            for i, file in enumerate(all_files):
                file_in_template = file in template_files
                file_in_current = file in current_files
                
                template_status = "✓" if file_in_template else "—"
                current_status = "✓" if file_in_current else "—"
                
                # For the first file in a folder, show the folder name
                folder_display = folder if i == 0 else ""
                
                print("| {:<{}} | {:<{}} | {:<{}} | {:<{}} |".format(
                    folder_display, folder_width, 
                    file, file_width,
                    template_status, template_width,
                    current_status, current_width
                ))
            
            # Add separator line between folders
            print("+" + "-" * (folder_width + 2) + "+" + "-" * (file_width + 2) + "+" + 
                  "-" * (template_width + 2) + "+" + "-" * (current_width + 2) + "+")
        
        # If folder exists only in template
        elif folder_in_template:
            template_files = sorted(list(template_data[folder].keys()))
            
            for i, file in enumerate(template_files):
                folder_display = folder if i == 0 else ""
                print("| {:<{}} | {:<{}} | {:<{}} | {:<{}} |".format(
                    folder_display, folder_width, 
                    file, file_width,
                    "✓", template_width,
                    "—", current_width
                ))
            
            print("+" + "-" * (folder_width + 2) + "+" + "-" * (file_width + 2) + "+" + 
                  "-" * (template_width + 2) + "+" + "-" * (current_width + 2) + "+")
        
        # If folder exists only in current
        else:
            current_files = sorted(list(current_data[folder].keys()))
            
            for i, file in enumerate(current_files):
                folder_display = folder if i == 0 else ""
                print("| {:<{}} | {:<{}} | {:<{}} | {:<{}} |".format(
                    folder_display, folder_width, 
                    file, file_width,
                    "—", template_width,
                    "✓", current_width
                ))
            
            print("+" + "-" * (folder_width + 2) + "+" + "-" * (file_width + 2) + "+" + 
                  "-" * (template_width + 2) + "+" + "-" * (current_width + 2) + "+")


def compare_metadata_keys(current_file: str, template_file: str, verbose: bool = True, 
                         as_table: bool = False, diff_only: bool = False) -> Dict[str, Any]:
    """
    Compare keys in two metadata JSON files at both the folder level and file level.
    Uses the template file as the standard for comparison.
    
    Args:
        current_file: Path to current metadata JSON file
        template_file: Path to template metadata JSON file (considered as the standard)
        verbose: Whether to print comparison results
        as_table: Whether to display results as a table
        diff_only: Whether to display only the differences in a simplified table
        
    Returns:
        Dictionary containing comparison results
    """
    # Read the two JSON files
    with open(current_file, 'r') as f1:
        current_data = json.load(f1)
    
    with open(template_file, 'r') as f2:
        template_data = json.load(f2)
    
    # If diff only format requested, print differences table and return
    if diff_only:
        print_diff_table(template_data, current_data)
        
    # If table format requested, print as table and return
    elif as_table:
        print(f"\nComparison Table of {template_file} (Template) vs {current_file} (Current):")
        print_comparison_table(template_data, current_data)
        
    # Get first level keys (folders)
    current_folders = set(current_data.keys())
    template_folders = set(template_data.keys())
    
    # Compare first level keys
    missing_in_current = template_folders - current_folders
    extra_in_current = current_folders - template_folders
    common_folders = current_folders & template_folders
    
    if verbose and not (as_table or diff_only):
        print(f"Comparing keys in {current_file} against {template_file}:")
        print("-" * 50)
    
    results = {
        "folders": {
            "missing_in_current": list(missing_in_current),
            "extra_in_current": list(extra_in_current),
            "match": len(missing_in_current) == 0 and len(extra_in_current) == 0
        },
        "files": {},
        "all_match": True
    }
    
    # Output first level key comparison results
    if verbose and not (as_table or diff_only):
        if missing_in_current:
            print(f"Folders in template but missing in current: {', '.join(missing_in_current)}")
        
        if extra_in_current:
            print(f"Extra folders in current not in template: {', '.join(extra_in_current)}")
        
        if not missing_in_current and not extra_in_current:
            print("First level keys (folders) match perfectly!")
    
    # Compare second level keys (files)
    if verbose and not (as_table or diff_only):
        print("\nSecond level keys (files) comparison:")
    
    all_files_match = True
    
    # For each common folder, compare the file keys
    for folder in common_folders:
        current_files = set(current_data[folder].keys())
        template_files = set(template_data[folder].keys())
        
        missing_files = template_files - current_files
        extra_files = current_files - template_files
        
        results["files"][folder] = {
            "missing_in_current": list(missing_files),
            "extra_in_current": list(extra_files),
            "match": len(missing_files) == 0 and len(extra_files) == 0
        }
        
        if verbose and not (as_table or diff_only):
            print(f"\nFolder '{folder}':")
        
        if missing_files and verbose and not (as_table or diff_only):
            print(f"  Files in template but missing in current: {', '.join(missing_files)}")
            all_files_match = False
        
        if extra_files and verbose and not (as_table or diff_only):
            print(f"  Extra files in current not in template: {', '.join(extra_files)}")
            all_files_match = False
        
        if not missing_files and not extra_files and verbose and not (as_table or diff_only):
            print(f"  Files in folder '{folder}' match perfectly!")
    
    results["all_match"] = all_files_match and results["folders"]["match"]
    
    # Summary
    if verbose and not (as_table or diff_only):
        print("\n" + "=" * 50)
        if results["all_match"]:
            print("All keys match perfectly between the two files!")
        else:
            print("Differences found between the files.")
            print("\nSUGGESTED ACTION:")
            print("- Use the template file keys as the standard for your implementation.")
            print("- Update your code to handle the missing files in the current metadata.")
            print("- Consider if the extra files in current metadata need special handling.")
    
    return results


def suggest_modifications(current_file: str, template_file: str) -> Dict[str, Any]:
    """
    Suggest specific modifications to align current_file with template_file
    
    Args:
        current_file: Path to current metadata JSON file
        template_file: Path to template metadata JSON file
        
    Returns:
        Dictionary containing suggested modifications
    """
    # First compare the keys
    comparison = compare_metadata_keys(current_file, template_file, verbose=False)
    
    # Read the files
    with open(current_file, 'r') as f1:
        current_data = json.load(f1)
    
    with open(template_file, 'r') as f2:
        template_data = json.load(f2)
    
    suggestions = {
        "add_folders": [],
        "remove_folders": [],
        "add_files": {},
        "remove_files": {}
    }
    
    # Folder-level suggestions
    for folder in comparison["folders"]["missing_in_current"]:
        suggestions["add_folders"].append(folder)
    
    for folder in comparison["folders"]["extra_in_current"]:
        suggestions["remove_folders"].append(folder)
    
    # File-level suggestions
    for folder, files_info in comparison["files"].items():
        if files_info["missing_in_current"]:
            suggestions["add_files"][folder] = files_info["missing_in_current"]
        
        if files_info["extra_in_current"]:
            suggestions["remove_files"][folder] = files_info["extra_in_current"]
    
    # Print suggestions
    print("\nSuggested modifications to align with template file:")
    print("-" * 50)
    
    if suggestions["add_folders"] or suggestions["remove_folders"]:
        print("\nFolder modifications:")
        for folder in suggestions["add_folders"]:
            print(f"  + Add folder: {folder}")
        
        for folder in suggestions["remove_folders"]:
            print(f"  - Remove folder: {folder} (or ensure it matches template)")
    
    if suggestions["add_files"] or suggestions["remove_files"]:
        print("\nFile modifications:")
        for folder, files in suggestions["add_files"].items():
            print(f"  In folder '{folder}':")
            for file in files:
                print(f"    + Add: {file}")
        
        for folder, files in suggestions["remove_files"].items():
            print(f"  In folder '{folder}':")
            for file in files:
                print(f"    - Extra file: {file} (consider handling)")
    
    if comparison["all_match"]:
        print("\nNo modifications needed. Files are already aligned.")
    
    return suggestions


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compare_keys.py current_file.json template_file.json [--suggest|--table|--diff]")
        sys.exit(1)
    
    current_file = sys.argv[1]
    template_file = sys.argv[2]
    
    if len(sys.argv) > 3:
        if sys.argv[3] == "--suggest":
            suggest_modifications(current_file, template_file)
        elif sys.argv[3] == "--table":
            compare_metadata_keys(current_file, template_file, as_table=True)
        elif sys.argv[3] == "--diff":
            compare_metadata_keys(current_file, template_file, diff_only=True)
        else:
            print(f"Unknown option: {sys.argv[3]}")
    else:
        compare_metadata_keys(current_file, template_file)