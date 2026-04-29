from infrastructure.pbi_client import PbiClient
from infrastructure.dax import ModelSchema
from infrastructure.dax_builder import build_kpi_dax
import logging

logging.basicConfig(level=logging.INFO)


def debug_connection():
    print("--- PBI Connection Debug ---")
    client = PbiClient()
    schema = ModelSchema()

    print("\n1. Testing OAuth2 Token Fetch...")
    client.get_token()
    if client._token:
        print(f"SUCCESS: Token retrieved (starts with {client._token[:10]}...)")
    else:
        print("FAILURE: Could not retrieve token. Check .env")
        return

    print('\n2. Testing Simple DAX Query: EVALUATE SUMMARIZECOLUMNS("Test", 1)')
    df = client.query('EVALUATE SUMMARIZECOLUMNS("Test", 1)')
    if df is not None:
        print("SUCCESS: Simple query returned data.")
        print(df)
    else:
        print("FAILURE: Simple query failed.")

    print("\n3. Testing Schema Discovery...")
    schema.discover()
    if schema._tables:
        print(f"SUCCESS: Discovered {len(schema._tables)} tables: {schema._tables}")
    else:
        print("FAILURE: No tables discovered.")

    print("\n4. Testing Real KPI DAX...")
    dax = build_kpi_dax("revenue", None, schema)
    print(f"Generated DAX:\n{dax}")
    df = client.query(dax)
    if df is not None:
        print("SUCCESS: KPI DAX returned data.")
        print(df)
    else:
        print("FAILURE: KPI DAX failed.")


if __name__ == "__main__":
    debug_connection()
