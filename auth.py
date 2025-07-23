#!/usr/bin/env python3
"""
BigQuery Authentication Module
Handles Google Cloud authentication using gcloud CLI.
"""

import os
from pathlib import Path
from google.cloud import bigquery
from google.auth import default

class BigQueryAuth:
    def __init__(self):
        self.client = None
        self.project = None
    
    def authenticate(self):
        """
        Authenticate using Application Default Credentials (gcloud CLI).
        Silently performs authentication without verbose output.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Suppress specific warning from google-auth
        import warnings
        warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")
        
        # Check for GOOGLE_APPLICATION_CREDENTIALS environment variable
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            print("Using default authentication method to set GOOGLE_APPLICATION_CREDENTIALS environment variable.")
            
            # Check for default credentials location
            home = Path.home()
            if os.name == 'nt':  # Windows
                default_path = home / 'AppData' / 'Roaming' / 'gcloud' / 'application_default_credentials.json'
            else:  # Mac/Linux
                default_path = home / '.config' / 'gcloud' / 'application_default_credentials.json'
                
            if default_path.exists():
                print(f"Default credentials found at: {default_path}")
            else:
                print("No default credentials found. Please run 'gcloud auth application-default login'")
        else:
            cred_file = Path(credentials_path)
            if not cred_file.exists():
                print(f"Warning: GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {credentials_path}")
        
        try:
            # Use Application Default Credentials silently
            credentials, project = default()
            
            if not credentials:
                print("ERROR: No valid credentials found. Run 'gcloud auth application-default login' first.")
                return False
            
            # Initialize BigQuery client
            self.client = bigquery.Client(credentials=credentials, project=project)
            self.project = project
            
            # Run a test query to verify access
            if not self._test_query():
                print(f"ERROR: Authentication succeeded but query test failed. Please check project permissions for {project}")
                return False
            
            print(f"Successfully authenticated to BigQuery project: {project}")
            return True
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def _test_query(self):
        """
        Run a simple test query to verify BigQuery access.
        
        Returns:
            bool: True if test query successful, False otherwise
        """
        try:
            query_job = self.client.query("SELECT 1 as test")
            results = list(query_job.result())
            return results[0].test == 1
        except Exception as e:
            print(f"Test query error: {e}")
            return False
    
    def get_client(self):
        """
        Get the authenticated BigQuery client.
        
        Returns:
            google.cloud.bigquery.Client: Authenticated BigQuery client
        """
        if not self.client:
            raise Exception("Not authenticated. Please call authenticate() first.")
        return self.client 