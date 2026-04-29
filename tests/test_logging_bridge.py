"""Tests for infrastructure/logging_bridge.py."""

import json
import pytest
from dash import Dash, html
from presentation.logging_bridge import setup_logging_bridge, inject_logging_script

# A minimal valid Dash index string that satisfies validation
_VALID_INDEX = """
<!DOCTYPE html>
<html>
    <head>{%metas%}<title>{%title%}</head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>
"""

class TestLoggingBridge:
    def test_inject_logging_script_standard_body(self):
        """Script is injected before </body> tag."""
        app = Dash(__name__)
        app.index_string = _VALID_INDEX
        inject_logging_script(app)
        assert '<script id="logging-bridge-js">' in app.index_string
        assert "</body>" in app.index_string

    def test_inject_logging_script_no_body(self):
        """Script is appended if no </body> tag found (fallback behavior)."""
        app = Dash(__name__)
        # Intentionally malformed but with required tokens
        app.index_string = "{%app_entry%}{%config%}{%scripts%}" 
        inject_logging_script(app)
        assert app.index_string.endswith('<script id="logging-bridge-js">\n    window.onerror = function(message, url, line, column, error) {\n        var stack = error ? error.stack : null;\n        fetch("/api/client-errors", {\n            method: "POST",\n            headers: {"Content-Type": "application/json"},\n            body: JSON.stringify({\n                message: message,\n                url: url,\n                line: line,\n                column: column,\n                stack: stack\n            })\n        });\n        return false; \n    };\n    console.log("Logging bridge initialized.");\n</script>\n')

    def test_log_browser_error_endpoint_success(self, caplog):
        """Endpoint accepts JSON and logs the error."""
        app = Dash(__name__)
        app.layout = html.Div("Dummy") # Layout required for server to run
        setup_logging_bridge(app)
        client = app.server.test_client()

        error_payload = {
            "message": "Uncaught ReferenceError: x is not defined",
            "url": "http://localhost:8050/",
            "line": 42,
            "column": 10,
            "stack": "ReferenceError: x is not defined\n    at http://localhost:8050/:42:10"
        }

        response = client.post(
            "/api/client-errors",
            data=json.dumps(error_payload),
            content_type="application/json"
        )

        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}
        
        # Verify log output
        assert "BROWSER ERROR: Uncaught ReferenceError: x is not defined (at http://localhost:8050/:42:10)" in caplog.text
        assert "BROWSER STACK: ReferenceError: x is not defined" in caplog.text

    def test_log_browser_error_endpoint_no_data(self):
        """Endpoint handles empty JSON payload gracefully."""
        app = Dash(__name__)
        app.layout = html.Div("Dummy")
        setup_logging_bridge(app)
        client = app.server.test_client()

        # Send empty JSON object instead of empty body
        response = client.post(
            "/api/client-errors",
            data=json.dumps({}),
            content_type="application/json"
        )
        assert response.status_code == 200
        assert response.get_json() == {"status": "ignored"}

    def test_log_browser_error_endpoint_malformed_json(self):
        """Endpoint returns 500 on internal processing error."""
        app = Dash(__name__)
        app.layout = html.Div("Dummy")
        setup_logging_bridge(app)
        client = app.server.test_client()

        # Sending non-JSON data with JSON content type to trigger exception
        response = client.post(
            "/api/client-errors",
            data="not-json",
            content_type="application/json"
        )
        assert response.status_code == 500
        # The actual error structure returned by flask/dash might vary, but status 500 is key
        assert "error" in response.get_json()
