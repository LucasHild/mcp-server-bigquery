# BigQuery MCP server

A Model Context Protocol server that provides access to BigQuery. This server enables LLMs to inspect database schemas and execute queries.

## Components

### Tools

The server implements three tools:

- `execute-query`: Executes a SQL query using BigQuery dialect
- `list-tables`: Lists all tables in the BigQuery database
- `describe-table`: Describes the schema of a specific table

## Configuration

The server can be configured either with command line arguments or environment variables.

| Argument     | Environment Variable | Required | Description                                                                                                                                                                                                                                                                                                                                                    |
| ------------ | -------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--project`  | `BIGQUERY_PROJECT`   | Yes      | The GCP project ID.                                                                                                                                                                                                                                                                                                                                            |
| `--location` | `BIGQUERY_LOCATION`  | Yes      | The GCP location (e.g. `europe-west9`).                                                                                                                                                                                                                                                                                                                        |
| `--dataset`  | `BIGQUERY_DATASETS`  | No       | Only take specific BigQuery datasets into consideration. Several datasets can be specified by repeating the argument (e.g. `--dataset my_dataset_1 --dataset my_dataset_2`) or by joining them with a comma in the environment variable (e.g. `BIGQUERY_DATASETS=my_dataset_1,my_dataset_2`). If not provided, all datasets in the project will be considered. |
| `--key-file` | `BIGQUERY_KEY_FILE`  | No       | Path to a service account key file for BigQuery. If not provided, the server will use the default credentials.                                                                                                                                                                                                                                                 |
| `--timeout`  | `BIGQUERY_TIMEOUT`   | No       | Maximum time in seconds to wait for a query to complete. If not provided, queries will wait indefinitely.                                                                                                                                                                                                                                                      |

## Installation

### Claude Code

```bash
claude mcp add bigquery --scope user -- uvx mcp-server-bigquery --project {{GCP_PROJECT_ID}} --location {{GCP_LOCATION}}
```

### Codex

```bash
codex mcp add bigquery -- uvx mcp-server-bigquery --project {{GCP_PROJECT_ID}} --location {{GCP_LOCATION}}
```
