import pytest
from domain.utils import validate_dax_query, clean_dax_query

@pytest.mark.parametrize("input_query, expected_cleaned", [
    ("\u200bEVALUATE Table", "EVALUATE Table"),
    ("\ufeffDEFINE VAR x=1", "DEFINE VAR x=1"),
    ("  EVALUATE\u200c Table  ", "EVALUATE Table"),
    ("\u200dEVALUATE\u200b ROW(\"a\", 1)", "EVALUATE ROW(\"a\", 1)"),
    ("/* comment */\u200b EVALUATE", "/* comment */ EVALUATE"),
])
def test_clean_dax_query_invisible_chars(input_query, expected_cleaned):
    """Verify that all known invisible characters are stripped."""
    assert clean_dax_query(input_query) == expected_cleaned

def test_validate_dax_query_with_dirty_input():
    """Verify that validation passes for queries that contain invisible characters but are otherwise valid."""
    dirty_query = "\u200b  EVALUATE 'Product'"
    assert validate_dax_query(dirty_query) is None

def test_validate_dax_query_empty_after_cleaning():
    """Verify that a query consisting only of invisible characters is caught as empty."""
    only_invisible = "\u200b\ufeff \u200c "
    assert validate_dax_query(only_invisible) == "Query is empty."

def test_validate_dax_query_blocked_dmv_with_invisible_chars():
    """Verify that blocking logic still works even if separators are invisible."""
    # This checks if someone tries to hide "INFO.TABLES" using ZWSP
    sneaky_query = "EVALUATE INFO\u200b.TABLES()"
    # Since clean_dax_query is called at start of validation, the ZWSP is removed
    # and the blocked DMV check should trigger on the concatenated string.
    assert validate_dax_query(sneaky_query) == "INFO.* DMV functions are not permitted."
