# Power BI Sales Dashboard

A white-label Dash BI shell that connects to any Power BI semantic model and delivers fully branded analytics — without Power BI Embedded costs or Microsoft UI lock-in.

## Features

- **Executive Summary** — KPI cards, trend charts, category/territory breakdowns, product performance table
- **Data Model Schema** — browsable table/column/measure explorer
- **Model Diagram** — interactive entity-relationship diagram of the semantic model
- **DAX Query View** — write and execute arbitrary DAX against the live model; schema panel for field discovery
- **DAX Inspector** — inspect the DAX query behind any chart
- **White-label theming** — app title, primary color, and font configurable via env vars
- **Caching** — disk-based cache with configurable TTL to minimize API calls
- **Dark mode** — Mantine UI with forced dark theme

## Requirements

- Python 3.12+
- Azure AD app registration with Power BI API permissions (`Dataset.Read.All`)

## Installation

```bash
# Install dependencies (recommended: uv)
uv sync

# Or pip
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```env
TENANT_ID=your-azure-tenant-id
CLIENT_ID=your-app-registration-client-id
CLIENT_SECRET=your-client-secret-value
WORKSPACE_ID=your-power-bi-workspace-id
DATASET_ID=your-power-bi-dataset-id
```

### Azure Setup

1. Register an app in Azure AD
2. Grant API permissions: `Dataset.Read.All` (Power BI Service)
3. Add the service principal to your Power BI workspace with at least Viewer permissions

## Usage

```bash
python app.py
```

App runs at `http://127.0.0.1:8050`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TENANT_ID` | Azure tenant ID | — |
| `CLIENT_ID` | App registration client ID | — |
| `CLIENT_SECRET` | App client secret | — |
| `WORKSPACE_ID` | Power BI workspace ID | — |
| `DATASET_ID` | Power BI dataset ID | — |
| `APP_TITLE` | Sidebar brand name | `Sales Dashboard` |
| `PRIMARY_COLOR` | Mantine color name for accent | `blue` |
| `FONT_FAMILY` | CSS font-family string | `'Inter', sans-serif` |
| `CACHE_TTL_SECONDS` | Cache TTL in seconds | `3600` |
| `REQUEST_TIMEOUT_SECONDS` | API request timeout | `60` |
| `USE_DISK_CACHE` | Persist cache to disk | `false` |
| `PRELOAD_DATA` | Populate cache at startup | `false` |
| `PBI_API_BASE` | Power BI REST API base URL | `https://api.powerbi.com/v1.0/myorg` |

## Project Structure

```
.
├── app.py                   # Application factory + entry point
├── config.py                # AppConfig + ThemeConfig (env-driven)
├── layout.py                # AppShell layout
├── di.py                    # Dependency injection container
├── domain/                  # Core entities, ports, exceptions, utils
├── application/             # Use cases and data loading
├── infrastructure/          # PBI client, cache, auth, DAX loader
│   ├── pbi_client.py
│   ├── cache.py
│   ├── auth.py
│   ├── dax.py
│   └── repository.py
├── presentation/            # UI logic
│   ├── callbacks.py         # All Dash callbacks
│   ├── charts.py            # Plotly chart builders
│   ├── constants.py         # Nav routes, UI labels
│   ├── theme.py             # Plotly color palette
│   └── helpers.py
├── components/
│   └── base.py              # Sidebar, DAX inspector drawer
├── pages/
│   ├── home.py              # Executive Summary (/)
│   ├── schema.py            # Data Model Schema (/schema)
│   ├── model_view.py        # Model Diagram (/model)
│   └── dax_query.py         # DAX Query View (/dax)
├── queries/
│   └── dax.json             # Named DAX queries
├── assets/
│   └── style.css
└── tests/
```

## Testing

```bash
pytest tests/ -v --cov=domain --cov=application --cov=infrastructure --cov=presentation
```

## Development Workflow with Power BI MCP

This project uses [@microsoft/powerbi-modeling-mcp](https://www.npmjs.com/package/@microsoft/powerbi-modeling-mcp) as a **dev-time tool only** — not a runtime dependency. The production app uses the REST API exclusively.

### Why MCP for dev

The MCP connects via XMLA endpoint and gives instant access to schema exploration, live DAX execution, and measure inspection — all without writing boilerplate auth/request code. Use it to design and validate queries before committing them to `queries/dax.json`.

### Adding a new chart — recommended flow

```
1. MCP: table_operations.List          → discover available tables
2. MCP: table_operations.GetSchema     → inspect columns + data types
3. MCP: measure_operations.List        → see existing measures
4. MCP: dax_query_operations.Execute   → iterate on DAX until result is correct
5. REST: validate final DAX via app's PbiClient → confirm response shape matches
6. Copy working DAX → queries/dax.json
7. Wire to Plotly chart in presentation/charts.py
```

### Why final REST validation

MCP uses XMLA; the app uses REST API. Response shapes can differ slightly (column name casing, nulls). One REST sanity check before committing prevents silent bugs in production.

## License

MIT
