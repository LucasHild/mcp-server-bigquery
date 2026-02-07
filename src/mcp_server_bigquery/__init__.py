from . import server
import asyncio
import argparse
import os


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description='BigQuery MCP Server')
    parser.add_argument('--project', help='BigQuery project', required=False)
    parser.add_argument('--location', help='BigQuery location', required=False)
    parser.add_argument('--key-file', help='BigQuery Service Account', required=False)
    parser.add_argument('--dataset', help='BigQuery dataset', required=False, action='append')
    parser.add_argument('--timeout', help='Query timeout in seconds', required=False, type=float)

    args = parser.parse_args()

    # Get values from environment variables if not provided as arguments
    project = args.project or os.environ.get('BIGQUERY_PROJECT')
    location = args.location or os.environ.get('BIGQUERY_LOCATION')
    key_file = args.key_file or os.environ.get('BIGQUERY_KEY_FILE')
    
    datasets_filter = args.dataset if args.dataset else []
    if not datasets_filter and 'BIGQUERY_DATASETS' in os.environ:
        datasets_filter = os.environ.get('BIGQUERY_DATASETS', '').split(',')
        datasets_filter = [d.strip() for d in datasets_filter if d.strip()]

    timeout_env = os.environ.get('BIGQUERY_TIMEOUT')
    timeout = args.timeout or (float(timeout_env) if timeout_env else None)

    asyncio.run(server.main(project, location, key_file, datasets_filter, timeout))

# Optionally expose other important items at package level
__all__ = ['main', 'server']
