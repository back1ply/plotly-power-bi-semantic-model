from infrastructure.pbi_client import PbiClient


def probe_model():
    client = PbiClient()

    # 1. Get all tables and columns by exhaustive check of common names
    tables = [
        "Sales",
        "Internet Sales",
        "FactInternetSales",
        "Product",
        "Date",
        "Sales Territory",
        "Customer",
    ]
    schema = {}

    print("--- Probing Tables and Columns ---")
    for t in tables:
        df = client.query(f"EVALUATE TOPN(1, '{t}')")
        if df is not None:
            schema[t] = df.columns.tolist()
            print(f"Found Table: {t}")
            print(f"  Columns: {schema[t]}")

    # 2. Probe for common Measures
    # We check if a measure exists by trying to evaluate it in a simple SUMMARIZECOLUMNS
    common_measures = [
        "Total Sales",
        "Total Revenue",
        "Total Cost",
        "Profit",
        "Margin",
        "Total Orders",
        "Order Count",
    ]
    found_measures = []

    print("\n--- Probing for Measures ---")
    for m in common_measures:
        # Measure name must be in brackets [Measure]
        dax = f'EVALUATE SUMMARIZECOLUMNS("Value", [{m}])'
        df = client.query(dax)
        if df is not None:
            found_measures.append(m)
            print(f"Found Measure: [{m}] = {df.iloc[0, 0]}")

    return schema, found_measures


if __name__ == "__main__":
    probe_model()
