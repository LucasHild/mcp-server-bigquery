# BigQuery MCP server

[![smithery badge](https://smithery.ai/badge/mcp-server-bigquery)](https://smithery.ai/server/mcp-server-bigquery)

A Model Context Protocol server that provides access to BigQuery. This server enables LLMs to inspect database schemas and execute queries.

## Components

### Tools

The server implements one tool:

- `execute-query`: Executes a SQL query using BigQuery dialect
- `list-tables`: Lists all tables in the BigQuery database
- `describe-table`: Describes the schema of a specific table

## Configuration

The server can be configured with the following arguments:

- `--project` (optional): The GCP project ID. Can also be set via `GOOGLE_CLOUD_PROJECT` environment variable.
- `--location` (optional): The GCP location (e.g. `europe-west9`). Can also be set via `GOOGLE_CLOUD_LOCATION` environment variable (default: `US`).
- `--dataset` (optional): Only take specific BigQuery datasets into consideration. Several datasets can be specified by repeating the argument (e.g. `--dataset my_dataset_1 --dataset my_dataset_2`). If not provided, all datasets in the project will be considered.
- `--key-file` (optional): Path to a service account key file for BigQuery. Can also be set via `GOOGLE_APPLICATION_CREDENTIALS` environment variable. If not provided, the server will use Application Default Credentials.

## Authentication

The server supports multiple authentication methods:

### 1. Application Default Credentials (Recommended for Local Development)

This is the most secure and convenient method for local development:

```bash
# Install gcloud CLI (if not already installed)
# https://cloud.google.com/sdk/docs/install

# Authenticate with your Google account
gcloud auth application-default login

# Set your default project (optional)
gcloud config set project YOUR_PROJECT_ID
```

### 2. Environment Variables

Set the required environment variables:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="US"  # Optional, defaults to US
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"  # Optional
```

### 3. Service Account Key File

For automated or CI/CD environments:

1. Create a service account in the Google Cloud Console
2. Grant the following IAM roles:
   - `BigQuery Data Viewer`
   - `BigQuery Job User`
3. Download the JSON key file
4. Use `--key-file` parameter or set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

### Authentication Priority

The server uses the following priority order for authentication:

1. `--key-file` parameter or `GOOGLE_APPLICATION_CREDENTIALS` environment variable
2. Application Default Credentials (via `gcloud auth application-default login`)
3. Compute Engine/Cloud Run automatic authentication (if running on GCP)

## Quickstart

### Install

#### Installing via Smithery

To install BigQuery Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/mcp-server-bigquery):

```bash
npx -y @smithery/cli install mcp-server-bigquery --client claude
```

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

##### Development/Unpublished Servers Configuration

**Using Application Default Credentials (Recommended):**

```json
"mcpServers": {
  "bigquery": {
    "command": "uv",
    "args": [
      "--directory",
      "{{PATH_TO_REPO}}",
      "run",
      "mcp-server-bigquery",
      "--project",
      "{{GCP_PROJECT_ID}}",
      "--location",
      "{{GCP_LOCATION}}"
    ]
  }
}
```

**Using Environment Variables:**

```json
"mcpServers": {
  "bigquery": {
    "command": "uv",
    "args": [
      "--directory",
      "{{PATH_TO_REPO}}",
      "run",
      "mcp-server-bigquery"
    ],
    "env": {
      "GOOGLE_CLOUD_PROJECT": "{{GCP_PROJECT_ID}}",
      "GOOGLE_CLOUD_LOCATION": "{{GCP_LOCATION}}"
    }
  }
}
```

##### Published Servers Configuration

**Using Application Default Credentials (Recommended):**

```json
"mcpServers": {
  "bigquery": {
    "command": "uvx",
    "args": [
      "mcp-server-bigquery",
      "--project",
      "{{GCP_PROJECT_ID}}",
      "--location",
      "{{GCP_LOCATION}}"
    ]
  }
}
```

**Using Environment Variables:**

```json
"mcpServers": {
  "bigquery": {
    "command": "uvx",
    "args": [
      "mcp-server-bigquery"
    ],
    "env": {
      "GOOGLE_CLOUD_PROJECT": "{{GCP_PROJECT_ID}}",
      "GOOGLE_CLOUD_LOCATION": "{{GCP_LOCATION}}"
    }
  }
}
```

Replace `{{PATH_TO_REPO}}`, `{{GCP_PROJECT_ID}}`, and `{{GCP_LOCATION}}` with the appropriate values.

**Setup Instructions:**

1. **For Application Default Credentials:** Run `gcloud auth application-default login` before starting Claude Desktop
2. **For Environment Variables:** Set the environment variables in your shell or MCP configuration
3. **For Service Account Keys:** Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your key file

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:

```bash
uv sync
```

2. Build package distributions:

```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:

```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:

- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory {{PATH_TO_REPO}} run mcp-server-bigquery
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
