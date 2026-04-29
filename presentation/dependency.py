"""Dependency injection for the presentation layer."""

from typing import cast
from typing import TypeVar

from flask import current_app

T = TypeVar("T")


def get_repository[T](port_type: type[T]) -> T:
    """Get the dashboard repository from the current application context.

    Args:
        port_type: The specific port type required by the consumer.

    Returns:
        The repository instance cast to the requested port type.
    """
    repo = current_app.config.get("DASHBOARD_REPOSITORY")
    if repo is None:
        raise RuntimeError("Dashboard repository not initialized in app config")
    return cast(T, repo)
