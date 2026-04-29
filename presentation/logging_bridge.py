"""Logging Bridge.

Provides a mechanism to capture client-side JavaScript errors and log them
to the server-side console. (CA-002)
"""

import logging

from dash import Dash
from flask import jsonify
from flask import request

logger = logging.getLogger(__name__)

_BROWSER_LOGGING_SCRIPT = """
<script id="logging-bridge-js">
    window.onerror = function(message, url, line, column, error) {
        var stack = error ? error.stack : null;
        fetch("/api/client-errors", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                message: message,
                url: url,
                line: line,
                column: column,
                stack: stack
            })
        });
        return false; 
    };
    console.log("Logging bridge initialized.");
</script>
"""


def inject_logging_script(app: Dash) -> None:
    """Inject browser logging script into the Dash index string.

    Args:
        app: The Dash application instance.
    """
    if "</body>" in app.index_string:
        app.index_string = app.index_string.replace("</body>", f"{_BROWSER_LOGGING_SCRIPT}</body>")
    else:
        app.index_string += _BROWSER_LOGGING_SCRIPT


def setup_logging_bridge(app: Dash) -> None:
    """Sets up a route and client-side hook for browser error logging.

    Args:
        app: The Dash application instance.
    """
    server = app.server

    @server.route("/api/client-errors", methods=["POST"])
    def log_browser_error():
        """Endpoint for browser to POST errors."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"status": "ignored"}), 200

            logger.error(
                "BROWSER ERROR: %s (at %s:%s:%s)",
                data.get("message"),
                data.get("url"),
                data.get("line"),
                data.get("column"),
            )
            if data.get("stack"):
                logger.error("BROWSER STACK: %s", data.get("stack"))

            return jsonify({"status": "ok"}), 200
        except Exception as exc:
            logger.error("Failed to log browser error: %s", exc)
            return (
                jsonify(
                    {
                        "error": {
                            "code": "LOG_FAILURE",
                            "message": "Internal server error",
                        }
                    }
                ),
                500,
            )

    # Inject a script into the app to catch errors
    inject_logging_script(app)
