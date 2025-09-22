# This script is not designed for Tableau,
# but for retrieving data for the Competitive Benchmarking deck (page 7).
# It can also be reused to retrieve data in other loops as needed.


#!/usr/bin/env python
# Lightweight BigQuery query tool
# Only supports legacy SQL mode (or you can change) and country parameter filling

from google.cloud import bigquery
import sys
import os

# Add parent directory to path to allow imports from sibling modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth_credential.auth import BigQueryAuth

# Initialize authentication
print("Setting up BigQuery authentication...")
auth = BigQueryAuth()
if not auth.authenticate():
    print("Authentication failed. Please check your credentials.")
    
client = auth.get_client()
print("Authentication successful!\n")


def run_simple_query(country):
    """
    Run preset SQL template, only replace country parameter
    Use legacy SQL mode, print results directly
    
    Args:
        country (str): Country name, e.g. 'United Arab Emirates'
    """
    
    # SQL template (legacy mode)
    #   Marketplace: company_type in ('Meta',)
    #   Online Travel: company_type in ('Meta', 'OTA')
    #       Note: you have to change 2 places in the sql template that contain the "set" of company_type
    sql_template = """
    SELECT 
      company,
      tt,
      round(tt / total_tt*100) AS percentage
    FROM (
      -- First calculate downloads for each company
      SELECT company, SUM(downloads) AS tt
      FROM [wego-cloud:appannie.appannie_tableau_report_updated_2019_03_05]
      WHERE country='{country}' and 
      company_type in ('Meta', 'OTA') and (month between '2024-09' and '2025-08')
      GROUP BY company
    ) AS t
    CROSS JOIN (
      -- Then calculate total downloads
      SELECT SUM(downloads) AS total_tt
      FROM [wego-cloud:appannie.appannie_tableau_report_updated_2019_03_05]
      WHERE country='{country}' and 
      company_type in ('Meta', 'OTA') and (month between '2024-09' and '2025-08')
    ) AS total
    ORDER BY tt DESC
    """
    
    # Fill country parameter
    sql_query = sql_template.format(country=country)
    print(f"\nExecuting query: country={country}")
    
    # Set legacy SQL mode
    job_config = bigquery.QueryJobConfig(use_legacy_sql=True)  # Change to False if you want to use standard SQL mode
    
    try:
        # Execute query
        query_job = client.query(sql_query, job_config=job_config)
        results = query_job.result()
        
        # Get field names
        field_names = [field.name for field in results.schema]
        
        # Print header
        header = " | ".join(field_names)
        print("=" * len(header))
        print(header)
        
        # Print results directly
        row_count = 0
        for row in results:
            # Convert row to value list and print
            row_values = [str(row[field]) for field in field_names]
            if row_values[0] == "Wego":
                print(" | ".join(row_values))
                print(f"rank: {row_count+1}")
            row_count += 1
        
    except Exception as e:
        print(f"Query execution failed: {e}")




if __name__ == "__main__":
    # only support MENA countries
    for country in ["Saudi Arabia", "Kuwait", "United Arab Emirates", "Bahrain", "Qatar", 
                    "Oman", "Egypt", "Algeria", "Jordan", "Lebanon", "Morocco"]:

        # Note that it will not save any csv file, just print the results
        run_simple_query(country) 
