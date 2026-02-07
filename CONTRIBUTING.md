# Contributing

## Building and Publishing

To prepare the package for distribution:

1. Increase the version number in `pyproject.toml`

2. Sync dependencies and update lockfile:

```bash
uv sync
```

3. Build package distributions:

```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

4. Publish to PyPI:

```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:

- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

## Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory {{PATH_TO_REPO}} run mcp-server-bigquery
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
