import os

import pandas as pd
import requests
from dash import Dash
from dash import dash_table
from dash import html
from dotenv import load_dotenv

load_dotenv()

tenant_id = os.getenv("TENANT_ID", "")
client_id = os.getenv("CLIENT_ID", "")
client_secret = os.getenv("CLIENT_SECRET", "")
workspace_id = os.getenv("WORKSPACE_ID", "")
dataset_id = os.getenv("DATASET_ID", "")

if not all([tenant_id, client_id, client_secret, workspace_id, dataset_id]):
    raise ValueError("Missing required environment variables. Check .env file.")

# === STEP 1: AUTH ===
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

token_res = requests.post(
    token_url,
    data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://analysis.windows.net/powerbi/api/.default",
    },
)

access_token = token_res.json()["access_token"]

# === STEP 2: QUERY DATA ===
query_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"

query = {
    "queries": [{"query": "EVALUATE TOPN(100, 'your_table_name')"}],
    "serializationSettings": {"includeNulls": True},
}

res = requests.post(
    query_url, headers={"Authorization": f"Bearer {access_token}"}, json=query
)


rows = res.json()["results"][0]["tables"][0]["rows"]
df = pd.DataFrame(rows)

# === STEP 3: DASH APP ===
app = Dash(__name__)

app.layout = html.Div(
    [
        html.H3("Power BI Data"),
        dash_table.DataTable(
            data=df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df.columns],
            page_size=10,
        ),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
