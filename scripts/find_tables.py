from infrastructure.pbi_client import PbiClient


def find_working_tables():
    client = PbiClient()
    # Common AdventureWorks tables
    candidates = [
        "Sales",
        "Internet Sales",
        "FactInternetSales",
        "Product",
        "Sales Territory",
        "Date",
    ]

    print("--- Searching for valid tables ---")
    for table in candidates:
        dax = f"EVALUATE TOPN(1, '{table}')"
        print(f"Checking '{table}'...", end=" ", flush=True)
        df = client.query(dax)
        if df is not None:
            print("FOUND!")
            print(f"Columns: {df.columns.tolist()}\n")
        else:
            print("Not found.")


if __name__ == "__main__":
    find_working_tables()
