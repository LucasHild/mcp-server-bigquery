from google.cloud import bigquery
from google.oauth2 import service_account
import importlib.metadata
import logging
import mcp.types as types
from mcp.server import Server, ServerRequestContext
import mcp.server.stdio
from typing import Any, Optional

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
    def __init__(self, project: str, location: str, key_file: Optional[str], datasets_filter: list[str], timeout: Optional[float] = None):
        """Initialize a BigQuery database client"""
        logger.info(f"Initializing BigQuery client for project: {project}, location: {location}, key_file: {key_file}")
        if not project:
            raise ValueError("Project is required")
        if not location:
            raise ValueError("Location is required")
        
        credentials: service_account.Credentials | None = None
        if key_file:
            try:
                credentials_path = key_file
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
            except Exception as e:
                logger.error(f"Error loading service account credentials: {e}")
                raise ValueError(f"Invalid key file: {e}")

        self.client = bigquery.Client(credentials=credentials, project=project, location=location)
        self.datasets_filter = datasets_filter
        self.timeout = timeout

    def execute_query(self, query: str, params: list[bigquery.ScalarQueryParameter] | None = None) -> list[dict[str, Any]]:
        """Execute a SQL query and return results as a list of dictionaries"""
        logger.debug(f"Executing query: {query}")
        try:
            if params:
                job = self.client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params))
            else:
                job = self.client.query(query)
                
            results = job.result(timeout=self.timeout)
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
        if len(parts) != 2 and len(parts) != 3:
            raise ValueError(f"Invalid table name: {table_name}")

        dataset_id = ".".join(parts[:-1])
        table_id = parts[-1]

        query = f"""
            SELECT ddl
            FROM {dataset_id}.INFORMATION_SCHEMA.TABLES
            WHERE table_name = @table_name;
        """
        return self.execute_query(query, params=[
            bigquery.ScalarQueryParameter("table_name", "STRING", table_id),
        ])

TOOLS = [
    types.Tool(
        name="execute-query",
        description="Execute a SELECT query on the BigQuery database",
        input_schema={
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
        input_schema={
            "type": "object",
            "properties": {},
        },
    ),
    types.Tool(
        name="describe-table",
        description="Get the schema information for a specific table",
        input_schema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Name of the table to describe (e.g. my_dataset.my_table)"},
            },
            "required": ["table_name"],
        },
    ),
]


async def main(project: str, location: str, key_file: Optional[str], datasets_filter: list[str], timeout: Optional[float] = None):
    logger.info(f"Starting BigQuery MCP Server with project: {project} and location: {location}")

    db = BigQueryDatabase(project, location, key_file, datasets_filter, timeout)

    async def handle_list_tools(
        ctx: ServerRequestContext, params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        return types.ListToolsResult(tools=TOOLS)

    async def handle_call_tool(
        ctx: ServerRequestContext, params: types.CallToolRequestParams
    ) -> types.CallToolResult:
        name = params.name
        arguments = params.arguments or {}
        logger.debug(f"Handling tool execution request: {name}")

        try:
            if name == "list-tables":
                results = db.list_tables()
            elif name == "describe-table":
                if "table_name" not in arguments:
                    raise ValueError("Missing table_name argument")
                results = db.describe_table(arguments["table_name"])
            elif name == "execute-query":
                if "query" not in arguments:
                    raise ValueError("Missing query argument")
                results = db.execute_query(arguments["query"])
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error handling tool {name}: {e}")
            message = str(e) or f"{type(e).__name__}: {repr(e)}"
            return types.CallToolResult(content=[types.TextContent(type="text", text=message)], is_error=True)

        return types.CallToolResult(content=[types.TextContent(type="text", text=str(results))])

    server = Server(
        "bigquery",
        version=importlib.metadata.version("mcp-server-bigquery"),
        on_list_tools=handle_list_tools,
        on_call_tool=handle_call_tool,
    )

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(read_stream, write_stream, server.create_initialization_options())
