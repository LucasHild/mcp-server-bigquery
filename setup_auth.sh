#!/bin/bash

# BigQuery MCP Server Authentication Setup Script

echo "🔧 BigQuery MCP Server Authentication Setup"
echo "============================================"
echo

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed."
    echo "📥 Please install it from: https://cloud.google.com/sdk/docs/install"
    echo
    exit 1
fi

echo "✅ gcloud CLI is installed"

# Check current authentication status
echo "🔍 Checking current authentication status..."
if gcloud auth list --format="value(account)" --filter="status:ACTIVE" | grep -q '@'; then
    CURRENT_ACCOUNT=$(gcloud auth list --format="value(account)" --filter="status:ACTIVE" | head -1)
    echo "✅ You are authenticated as: $CURRENT_ACCOUNT"
else
    echo "❌ You are not authenticated with gcloud"
    echo "🚀 Run: gcloud auth login"
    echo
    exit 1
fi

# Check if ADC is set up
echo "🔍 Checking Application Default Credentials..."
if [ -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
    echo "✅ Application Default Credentials are already set up"
else
    echo "⚠️  Application Default Credentials are not set up"
    echo "🚀 Would you like to set up Application Default Credentials now? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🔐 Setting up Application Default Credentials..."
        gcloud auth application-default login
        if [ $? -eq 0 ]; then
            echo "✅ Application Default Credentials set up successfully!"
        else
            echo "❌ Failed to set up Application Default Credentials"
            exit 1
        fi
    else
        echo "ℹ️  You can set up ADC later by running: gcloud auth application-default login"
    fi
fi

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -n "$CURRENT_PROJECT" ]; then
    echo "✅ Current project: $CURRENT_PROJECT"
else
    echo "⚠️  No default project set"
    echo "🚀 Would you like to set a default project? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "📝 Please enter your GCP project ID:"
        read -r PROJECT_ID
        gcloud config set project "$PROJECT_ID"
        if [ $? -eq 0 ]; then
            echo "✅ Default project set to: $PROJECT_ID"
            CURRENT_PROJECT="$PROJECT_ID"
        else
            echo "❌ Failed to set default project"
        fi
    fi
fi

echo
echo "🎉 Setup Summary:"
echo "=================="
echo "✅ gcloud CLI: Installed"
echo "✅ Authentication: $CURRENT_ACCOUNT"
echo "✅ Application Default Credentials: Set up"
if [ -n "$CURRENT_PROJECT" ]; then
    echo "✅ Default project: $CURRENT_PROJECT"
else
    echo "⚠️  Default project: Not set"
fi

echo
echo "🚀 Next Steps:"
echo "=============="
echo "1. Your BigQuery MCP server is now ready to use with Application Default Credentials"
echo "2. Use this MCP configuration:"
echo
echo '{
  "mcpServers": {
    "bigquery": {
      "command": "uv",
      "args": [
        "run",
        "--refresh-package", 
        "mcp-server-bigquery",
        "--with",
        "git+https://github.com/mexcool/mcp-server-bigquery.git@main#mcp-server-bigquery",
        "mcp-server-bigquery"'

if [ -n "$CURRENT_PROJECT" ]; then
    echo '        ,"--project", "'$CURRENT_PROJECT'"'
fi

echo '        ,"--location", "US"
      ]
    }
  }
}'

echo
echo "3. Or set environment variables:"
if [ -n "$CURRENT_PROJECT" ]; then
    echo "   export GOOGLE_CLOUD_PROJECT=\"$CURRENT_PROJECT\""
fi
echo "   export GOOGLE_CLOUD_LOCATION=\"US\""
echo
echo "📚 For more information, see the README.md file"
echo "🔗 Documentation: https://cloud.google.com/bigquery/docs/authentication" 
