# Code Quality Commands
# Install: https://just.systems/install.sh

# Lint - ruff
lint:
    ruff check .

# Format - ruff
fmt:
    ruff format .

# Type check - mypy and pyright
typecheck:
    mypy app.py components/ pages/ domain/ infrastructure/ presentation/ application/
    pyright app.py components/ pages/ domain/ infrastructure/ presentation/ application/

# Security - bandit
security:
    bandit -r app.py components/ pages/ domain/ infrastructure/ presentation/ application/ --skip B101,B201

# Run tests with coverage
test:
    pytest tests/ -v

test-cov:
    pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

# AGENTS.md specific checks
benchmark:
    pytest tests/ --benchmark-only

hypothesis:
    pytest tests/ --hypothesis-show-statistics

archon:
    pytest tests/ -m archon

mutmut:
    mutmut run

# Docstring coverage - interrogate
docs-check:
    interrogate --exclude tests/ --ignore-magic --fail-under 0

# All quality checks (except tests)
check: lint typecheck security deadcode docs-check

# Full pipeline - lint, format, typecheck, test
check-all: fmt lint typecheck test

# Dependencies
deps:
    pip install -e ".[dev]"

# Audit dependencies
audit:
    pip-audit --ignore-vuln=CVE-2025-69872 --ignore-vuln=PYSEC-2022-42969

# Check for unused imports
undeclared:
    deptry . --exclude tests/

# Dead code detection - vulture
deadcode:
    vulture --exclude tests,scripts,starter-scripts . --min-confidence 80

# Dependency vulnerability check - safety
safety-check:
    safety check --full-report --ignore 86338 --ignore 51457 --ignore 85681 --ignore 59234 --ignore 73501 || true

# Unused try-except - tryceratops
trycheck:
    python -m tryceratops app.py components/ pages/ domain/ infrastructure/ presentation/ application/ || true

# Pylint - thorough analysis
pylint-check:
    pylint app.py components/ domain/ infrastructure/ presentation/ application/ --disable=C0114,C0115,R0903,W0511,W0718,R1710,E1135,E1136,C0301,R0902 --score=no

# E2E Testing - Playwright
e2e:
    pytest tests/ -m "e2e" --browser chromium

# Accessibility - Axe
a11y:
    pytest tests/ -m "a11y"

# Advanced SAST - Semgrep
semgrep:
    semgrep scan

# Load Testing - Locust
load-test:
    locust -f tests/load_test.py --headless -u 50 -r 10 --run-time 1m

# Maintainability Index - Xenon
maintainability:
    xenon --max-absolute A --max-modules A --max-average A app.py components/ pages/ domain/ infrastructure/ presentation/ application/

# Full quality check
full-check: lint typecheck security deadcode docs-check audit safety-check trycheck pylint-check maintainability semgrep
