#!/usr/bin/env python3
"""
GBQautomation - Main Runner (In Progress)
Main entry point for the Google BigQuery automation workflow.

This script orchestrates the entire data collection process:
1. Authenticate with Google Cloud
2. Run BigQuery queries to collect data
3. Run additional data collection scripts
4. Process and save results to organized CSV files
"""

import sys
import os
from pathlib import Path

# Import the BigQuery runner module
from data_collection.bq_runner import main as run_bq

def main():
    """
    Main entry point for the GBQautomation workflow.
    
    This function:
    1. Sets up the environment
    2. Runs the BigQuery runner
    3. Executes any additional tasks
    """
    print("Starting GBQautomation workflow...")
    
    # Add the current directory to the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Run the BigQuery runner
    print("\nExecuting BigQuery data collection...")
    run_bq()
    
    print("\nGBQautomation workflow completed!")

if __name__ == "__main__":
    main()
