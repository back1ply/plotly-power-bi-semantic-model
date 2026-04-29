"""Tests for dashboard callbacks."""

from unittest.mock import MagicMock
from unittest.mock import patch

from domain import QueryKey
from domain import QueryNotFoundError
from domain import validate_dax_query
from presentation.callbacks import compute_active_nav
from presentation.callbacks import handle_inspector_logic
from presentation.constants import ROUTE_DAX
from presentation.constants import ROUTE_HOME
from presentation.constants import ROUTE_MODEL
from presentation.constants import ROUTE_SCHEMA


class TestCallbacks:
    def test_handle_inspector_success(self):
        """Inspector returns DAX query for selected chart."""
        mock_repo = MagicMock()
        mock_repo.get_raw_query.return_value = "EVALUATE 'Sales'"

        # Simulate Dash callback context
        with patch("presentation.callbacks.callback_context") as mock_ctx:
            mock_ctx.triggered = [
                {"id": {"type": "open-dax-inspector", "chart": "kpi_totals"}}
            ]
            
            result = handle_inspector_logic("kpi_totals", False, mock_repo)
            
            assert result.is_open is True
            assert result.content == "EVALUATE 'Sales'"
            mock_repo.get_raw_query.assert_called_once_with(QueryKey.KPI_TOTALS)

    def test_handle_inspector_query_not_found(self):
        """Inspector returns error message if query not found."""
        mock_repo = MagicMock()
        mock_repo.get_raw_query.side_effect = QueryNotFoundError("Missing")

        with patch("presentation.callbacks.callback_context") as mock_ctx:
            mock_ctx.triggered = [
                {"id": {"type": "open-dax-inspector", "chart": "sales_by_date"}}
            ]
            
            result = handle_inspector_logic("sales_by_date", False, mock_repo)
            assert "Query not found" in result.content

    def test_handle_inspector_no_clicks(self):
        """Inspector remains unchanged if no clicks triggered."""
        mock_repo = MagicMock()
        result = handle_inspector_logic("", False, mock_repo)
        assert result.is_open is False
        assert "Select a chart" in result.content

    def test_handle_inspector_repo_error(self):
        """Inspector returns error if repository fails."""
        mock_repo = MagicMock()
        mock_repo.get_raw_query.side_effect = RuntimeError("Not found")

        with patch("presentation.callbacks.callback_context") as mock_ctx:
            mock_ctx.triggered = [
                {"id": {"type": "open-dax-inspector", "chart": "kpi_totals"}}
            ]
            
            result = handle_inspector_logic("kpi_totals", False, mock_repo)
            assert "Repository error" in result.content


class TestComputeActiveNav:
    def test_home_route_activates_home(self):
        """Home pathname activates only home nav link."""
        result = compute_active_nav(ROUTE_HOME)
        assert result == (True, False, False, False, False)

    def test_schema_route_activates_schema(self):
        """Schema pathname activates only schema nav link."""
        result = compute_active_nav(ROUTE_SCHEMA)
        assert result == (False, True, False, False, False)

    def test_model_route_activates_model(self):
        """Model pathname activates only model nav link."""
        result = compute_active_nav(ROUTE_MODEL)
        assert result == (False, False, True, False, False)

    def test_dax_route_activates_dax(self):
        """DAX pathname activates only DAX nav link."""
        result = compute_active_nav(ROUTE_DAX)
        assert result == (False, False, False, True, False)

    def test_unknown_route_activates_nothing(self):
        """Unknown pathname leaves all nav links inactive."""
        result = compute_active_nav("/unknown")
        assert result == (False, False, False, False, False)


class TestValidateDaxQuery:
    def test_valid_evaluate_query(self):
        """Simple EVALUATE query passes."""
        assert validate_dax_query("EVALUATE 'Sales'") is None

    def test_valid_define_evaluate_query(self):
        """DEFINE MEASURE ... EVALUATE pattern passes."""
        dax = "DEFINE MEASURE Sales[X] = SUM(Sales[Amount])\nEVALUATE SUMMARIZECOLUMNS('Product'[Category], \"X\", [X])"
        assert validate_dax_query(dax) is None

    def test_evaluate_case_insensitive(self):
        """Keyword check is case-insensitive."""
        assert validate_dax_query("evaluate 'Sales'") is None

    def test_empty_string_rejected(self):
        """Empty input returns error."""
        assert validate_dax_query("") is not None

    def test_whitespace_only_rejected(self):
        """Whitespace-only input returns error."""
        assert validate_dax_query("   \n\t  ") is not None

    def test_missing_keyword_rejected(self):
        """Query without EVALUATE or DEFINE is rejected."""
        error = validate_dax_query("SELECT * FROM Sales")
        assert error is not None
        assert "EVALUATE" in error or "DEFINE" in error

    def test_info_dmv_blocked(self):
        """INFO.* DMV functions are blocked."""
        error = validate_dax_query("EVALUATE INFO.TABLES()")
        assert error is not None
        assert "INFO" in error

    def test_info_dmv_case_insensitive(self):
        """INFO.* block is case-insensitive."""
        assert validate_dax_query("EVALUATE info.COLUMNS()") is not None

    def test_exceeds_max_length_rejected(self):
        """Query over 10,000 chars is rejected."""
        long_dax = "EVALUATE 'Sales'\n" + "-- comment\n" * 1000
        error = validate_dax_query(long_dax)
        assert error is not None
        assert "length" in error.lower()
