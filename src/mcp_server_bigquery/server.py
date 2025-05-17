from google.cloud import bigquery
from google.oauth2 import service_account
import logging
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from typing import Any, Optional
import google.auth
from google.auth.credentials import Credentials as GoogleAuthCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging to both stdout and file
logger = logging.getLogger('mcp_bigquery_server')
handler_stdout = logging.StreamHandler()
handler_file = logging.FileHandler('/tmp/mcp_bigquery_server.log')

# Set format for both handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler_stdout.setFormatter(formatter)
handler_file.setFormatter(formatter)

# Add both handlers to logger
logger.addHandler(handler_stdout)
logger.addHandler(handler_file)

# Set overall logging level
logger.setLevel(logging.DEBUG)

logger.info("Starting MCP BigQuery Server")

class BigQueryDatabase:
    def __init__(self, project: str, location: str, key_file: Optional[str], datasets_filter: list[str]):
        """Initialize a BigQuery database client"""
        logger.info(f"Initializing BigQuery client for project: {project}, location: {location}, key_file: {key_file}")
        if not project:
            raise ValueError("Project is required")
        if not location:
            raise ValueError("Location is required")
        
        credentials: Optional[GoogleAuthCredentials] = None
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]

        if key_file:
            try:
                logger.info(f"Attempting to load credentials from key_file: {key_file}")
                # google.auth.load_credentials_from_file can handle various credential types
                # including service account keys and authorized user keys (like ADC files).
                creds_obj, _ = google.auth.load_credentials_from_file(
                    key_file,
                    scopes=scopes,
                )
                credentials = creds_obj
                logger.info(f"Successfully loaded credentials from key_file: {key_file}")
            except Exception as e:
                logger.error(f"Error loading credentials from key_file '{key_file}': {e}")
                # Include the original exception type and message for better debugging
                raise ValueError(f"Invalid key file '{key_file}'. Failed to load credentials: {type(e).__name__} - {e}")
        else:
            # No key_file provided.
            # The BigQuery client will attempt to use Application Default Credentials automatically.
            # We try to load them explicitly here to provide earlier feedback or set a quota project.
            logger.info("No key_file provided. Attempting to load Application Default Credentials.")
            try:
                creds_obj, detected_project_id = google.auth.default(
                    scopes=scopes,
                    quota_project_id=project # Good practice to set quota_project_id from the provided project
                )
                credentials = creds_obj
                logger.info(f"Successfully loaded Application Default Credentials. Effective project for quota: {detected_project_id or project}")
            except google.auth.exceptions.DefaultCredentialsError as e:
                logger.warning(
                    f"Could not automatically find Application Default Credentials: {e}. "
                    "The BigQuery client will still attempt to find them. "
                    "Ensure GOOGLE_APPLICATION_CREDENTIALS is set or you are in a GCP-configured environment."
                )
                # credentials remains None, BigQuery client will try its own ADC lookup.
            except Exception as e: # Catch any other unexpected errors during google.auth.default()
                logger.error(f"An unexpected error occurred while trying to load Application Default Credentials: {e}")
                # credentials remains None, BigQuery client will try its own ADC lookup.

        self.client = bigquery.Client(credentials=credentials, project=project, location=location)
        self.datasets_filter = datasets_filter

    def execute_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a SQL query and return results as a list of dictionaries"""
        logger.debug(f"Executing query: {query}")
        try:
            if params:
                job = self.client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params))
            else:
                job = self.client.query(query)
                
            results = job.result()
            rows = [dict(row.items()) for row in results]
            logger.debug(f"Query returned {len(rows)} rows")
            return rows
        except Exception as e:
            logger.error(f"Database error executing query: {e}")
            raise
    
    def list_tables(self) -> list[str]:
        """List all tables in the BigQuery database"""
        logger.debug("Listing all tables")

        if self.datasets_filter:
            datasets = [self.client.dataset(dataset) for dataset in self.datasets_filter]
        else:
            datasets = list(self.client.list_datasets())

        logger.debug(f"Found {len(datasets)} datasets")

        tables = []
        for dataset in datasets:
            dataset_tables = self.client.list_tables(dataset.dataset_id)
            tables.extend([
                f"{dataset.dataset_id}.{table.table_id}" for table in dataset_tables
            ])

        logger.debug(f"Found {len(tables)} tables")
        return tables

    def describe_table(self, table_name: str) -> list[dict[str, Any]]:
        """Describe a table in the BigQuery database"""
        logger.debug(f"Describing table: {table_name}")

        parts = table_name.split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid table name: {table_name}")

        dataset_id = parts[0]
        table_id = parts[1]

        query = f"""
            SELECT ddl
            FROM {dataset_id}.INFORMATION_SCHEMA.TABLES
            WHERE table_name = @table_name;
        """
        return self.execute_query(query, params=[
            bigquery.ScalarQueryParameter("table_name", "STRING", table_id),
        ])

async def main(project: str, location: str, key_file: Optional[str], datasets_filter: list[str]):
    logger.info(f"Starting BigQuery MCP Server with project: {project} and location: {location}")

    db = BigQueryDatabase(project, location, key_file, datasets_filter)
    server = Server("bigquery-manager")

    # Register handlers
    logger.debug("Registering handlers")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
                name="execute-query",
                description="Execute a SELECT query on the BigQuery database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SELECT SQL query to execute using BigQuery dialect"},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="list-tables",
                description="List all tables in the BigQuery database",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="describe-table",
                description="Get the schema information for a specific table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Name of the table to describe (e.g. my_dataset.my_table)"},
                    },
                    "required": ["table_name"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests"""
        logger.debug(f"Handling tool execution request: {name}")

        try:
            if name == "list-tables":
                results = db.list_tables()
                return [types.TextContent(type="text", text=str(results))]

            elif name == "describe-table":
                if not arguments or "table_name" not in arguments:
                    raise ValueError("Missing table_name argument")
                results = db.describe_table(arguments["table_name"])
                return [types.TextContent(type="text", text=str(results))]

            if name == "execute-query":
                results = db.execute_query(arguments["query"])
                return [types.TextContent(type="text", text=str(results))]

            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="bigquery",
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
