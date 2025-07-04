from . import server
import asyncio
import argparse
import os

def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(
        description='BigQuery MCP Server',
        epilog="""
Authentication Options:
  1. Application Default Credentials (recommended for local development):
     Run: gcloud auth application-default login
  
  2. Service Account Key File:
     Use --key-file or set GOOGLE_APPLICATION_CREDENTIALS environment variable
  
  3. Environment Variables:
     GOOGLE_CLOUD_PROJECT: BigQuery project ID
     GOOGLE_CLOUD_LOCATION: BigQuery location (default: US)
     GOOGLE_APPLICATION_CREDENTIALS: Path to service account key file
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--project', 
        help='BigQuery project ID (can also be set via GOOGLE_CLOUD_PROJECT environment variable)', 
        required=False
    )
    parser.add_argument(
        '--location', 
        help='BigQuery location, e.g., US, EU (can also be set via GOOGLE_CLOUD_LOCATION environment variable, default: US)', 
        required=False
    )
    parser.add_argument(
        '--key-file', 
        help='Path to BigQuery Service Account key file (can also be set via GOOGLE_APPLICATION_CREDENTIALS environment variable)', 
        required=False
    )
    parser.add_argument(
        '--dataset', 
        help='Specific BigQuery dataset to include (can be specified multiple times)', 
        required=False, 
        action='append'
    )
    
    args = parser.parse_args()

    # Use environment variables as fallback
    project = args.project or os.getenv('GOOGLE_CLOUD_PROJECT')
    location = args.location or os.getenv('GOOGLE_CLOUD_LOCATION', 'US')
    key_file = getattr(args, 'key_file') or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    datasets_filter = args.dataset if args.dataset else []
    
    # Show what configuration we're using
    print(f"Starting BigQuery MCP Server with:")
    print(f"  Project: {project}")
    print(f"  Location: {location}")
    print(f"  Key file: {key_file or 'Using Application Default Credentials'}")
    print(f"  Datasets filter: {datasets_filter or 'All datasets'}")
    
    asyncio.run(server.main(project, location, key_file, datasets_filter))

# Optionally expose other important items at package level
__all__ = ['main', 'server']
