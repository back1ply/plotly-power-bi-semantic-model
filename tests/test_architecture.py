"""Architecture boundary tests using pytest-archon."""

import pytest
from pytest_archon import archrule

@pytest.mark.archon
def test_domain_layer_dependencies():
    """Domain layer must not depend on outer layers."""
    (
        archrule("Domain depends on nothing")
        .match("domain.*")
        .should_not_import("application.*")
        .should_not_import("infrastructure.*")
        .should_not_import("presentation.*")
        .should_not_import("pages.*")
        .should_not_import("components.*")
        .should_not_import("app")
        .check("domain")
    )

@pytest.mark.archon
def test_application_layer_dependencies():
    """Application layer depends only on Domain."""
    (
        archrule("Application depends only on Domain")
        .match("application.*")
        .should_not_import("infrastructure.*")
        .should_not_import("presentation.*")
        .should_not_import("pages.*")
        .should_not_import("components.*")
        .check("application")
    )

@pytest.mark.archon
def test_infrastructure_layer_dependencies():
    """Infrastructure layer depends only on Domain and Application, never Presentation."""
    (
        archrule("Infrastructure does not depend on UI")
        .match("infrastructure.*")
        .should_not_import("presentation.*")
        .should_not_import("pages.*")
        .should_not_import("components.*")
        .check("infrastructure")
    )