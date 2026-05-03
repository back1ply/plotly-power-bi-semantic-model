"""Domain exceptions.

Contains application-specific exception classes.
"""


class QueryNotFoundError(Exception):
    """Exception raised when a query is not found."""


class SchemaKeyError(Exception):
    """Exception raised when a schema key is not found."""


class QueryError(Exception):
    """Exception raised when a DAX query fails."""

    def __init__(self, message: str = "Query failed"):
        super().__init__(message)


class AuthenticationError(Exception):
    """Exception raised when authentication fails."""


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded."""


class SchemaLoadError(Exception):
    """Exception raised when a schema fails to load."""


class ConfigurationError(Exception):
    """Exception raised when application configuration is invalid or missing."""
