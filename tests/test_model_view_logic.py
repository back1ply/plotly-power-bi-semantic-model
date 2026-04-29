"""Tests for model_view internal logic."""

from unittest.mock import patch

# Mock dash.register_page to allow importing the module for logic testing
with patch("dash.register_page"):
    from pages.model_view import _build_model_data

from domain import ColumnType, ModelSchema, TableSchema
from domain.services import ColumnClassifier

def test_detect_column_type_key():
    assert ColumnClassifier.detect_type("CustomerKey", "Sales") == ColumnType.KEY
    assert ColumnClassifier.detect_type("ID", "Product") == ColumnType.KEY
    assert ColumnClassifier.detect_type("SurrogateID", "Product") == ColumnType.KEY

def test_detect_column_type_date():
    assert ColumnClassifier.detect_type("OrderDate", "Sales") == ColumnType.DATE
    assert ColumnClassifier.detect_type("FiscalYear", "Date") == ColumnType.DATE
    assert ColumnClassifier.detect_type("Month", "Date") == ColumnType.DATE

def test_detect_column_type_measure():
    assert ColumnClassifier.detect_type("SalesAmount", "Sales") == ColumnType.MEASURE
    assert ColumnClassifier.detect_type("Profit", "Sales") == ColumnType.MEASURE
    # Not in Sales table, shouldn't be measure by default unless measure list
    assert ColumnClassifier.detect_type("Amount", "Other") == ColumnType.REGULAR

def test_detect_column_type_hidden():
    assert ColumnClassifier.detect_type("RowNumber", "Any") == ColumnType.HIDDEN
    assert ColumnClassifier.detect_type("InternalID", "Any") == ColumnType.HIDDEN

def test_build_model_data_structure():
    schema = ModelSchema(tables={
        "Sales": TableSchema(name="Sales", columns=["OrderKey", "Amount"], measures=["TotalSales"]),
        "Product": TableSchema(name="Product", columns=["ProductKey", "Name"], measures=[]),
    })
    from domain import ModelRelationship
    relationships = [
        ModelRelationship(
            from_table="Sales", from_column="ProductKey",
            to_table="Product", to_column="ProductKey",
            from_cardinality="Many", to_cardinality="One",
            is_active=True, cross_filtering_behavior="OneDirection"
        )
    ]
    data = _build_model_data(schema, relationships)

    assert "tables" in data
    assert "relationships" in data
    
    # Check tables
    sales_node = next(t for t in data["tables"] if t["name"] == "Sales")
    assert len(sales_node["columns"]) == 3 # OrderKey, Amount, TotalSales
    assert any(c["name"] == "OrderKey" and c["type"] == "key" for c in sales_node["columns"])
    
    # Check relationships
    rel = data["relationships"][0]
    assert rel["from"] == "Sales"
    assert rel["cardinality"] == "*:1"

def test_build_model_data_column_limit():
    # Test capping MAX_COLUMNS_DISPLAY (12)
    cols = [f"Col{i}" for i in range(20)]
    schema = ModelSchema(tables={
        "LargeTable": TableSchema(name="LargeTable", columns=cols, measures=[]),
    })
    
    data = _build_model_data(schema, [])
    table = data["tables"][0]
    
    assert len(table["columns"]) == 12
    assert table["extraColumns"] == 8
