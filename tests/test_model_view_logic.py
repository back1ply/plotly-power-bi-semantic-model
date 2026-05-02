"""Tests for model_view internal logic."""

from unittest.mock import patch

# Mock dash.register_page to allow importing the module for logic testing
with patch("dash.register_page"):
    from pages.model_view import _build_model_data

from domain import ColumnType, ModelSchema, TableSchema
from domain.services import ColumnClassifier

def test_detect_column_type_key():
    classifier = ColumnClassifier()
    assert classifier.detect_type("CustomerKey", "Sales") == ColumnType.KEY
    assert classifier.detect_type("ID", "Product") == ColumnType.KEY
    assert classifier.detect_type("SurrogateID", "Product") == ColumnType.KEY

def test_detect_column_type_date():
    classifier = ColumnClassifier()
    assert classifier.detect_type("OrderDate", "Sales") == ColumnType.DATE
    assert classifier.detect_type("FiscalYear", "Date") == ColumnType.DATE
    assert classifier.detect_type("Month", "Date") == ColumnType.DATE

def test_detect_column_type_measure():
    classifier = ColumnClassifier()
    assert classifier.detect_type("Revenue", "Sales") == ColumnType.MEASURE
    assert classifier.detect_type("Profit", "Sales") == ColumnType.MEASURE
    # Not in Sales table, shouldn't be measure by default unless measure list
    assert classifier.detect_type("Amount", "Other") == ColumnType.REGULAR

def test_detect_column_type_hidden():
    classifier = ColumnClassifier()
    assert classifier.detect_type("RowNumber", "Any") == ColumnType.HIDDEN
    assert classifier.detect_type("InternalID", "Any") == ColumnType.HIDDEN

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
    classifier = ColumnClassifier()
    data = _build_model_data(schema, relationships, classifier)

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
    
    classifier = ColumnClassifier()
    data = _build_model_data(schema, [], classifier)
    table = data["tables"][0]
    
    assert len(table["columns"]) == 12
    assert table["extraColumns"] == 8
