"""Presentation Constants.

Contains UI-specific labels and configuration.
"""

ROUTE_HOME = "/"
ROUTE_SCHEMA = "/schema"
ROUTE_MODEL = "/model"
ROUTE_DAX = "/dax"
ROUTE_EMBED = "/embed"
NAV_ROUTES = (ROUTE_HOME, ROUTE_SCHEMA, ROUTE_MODEL, ROUTE_DAX, ROUTE_EMBED)

# Options for the custom builder used in the UI.
MEASURE_LABELS = {
    "Revenue": "Revenue",
    "Profit": "Profit",
    "Orders": "Orders",
    "Avg Order Value": "Avg Order Value",
}

DIMENSION_LABELS = {
    "Category": "Category",
    "Territory Group": "Territory Group",
    "Country": "Country",
    "Month": "Month",
}
