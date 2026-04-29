"""Static scan for hardcoded credentials — CONN-02."""

import re
import pathlib


# Patterns that indicate a raw credential literal assignment
_CREDENTIAL_PATTERNS = [
    re.compile(r'tenant_id\s*=\s*["\'][A-Fa-f0-9\-]{30,}["\']', re.IGNORECASE),
    re.compile(r'client_id\s*=\s*["\'][A-Fa-f0-9\-]{30,}["\']', re.IGNORECASE),
    re.compile(r'client_secret\s*=\s*["\'][^"\']{10,}["\']', re.IGNORECASE),
    re.compile(r'workspace_id\s*=\s*["\'][A-Fa-f0-9\-]{30,}["\']', re.IGNORECASE),
    re.compile(r'dataset_id\s*=\s*["\'][A-Fa-f0-9\-]{30,}["\']', re.IGNORECASE),
]

_EXCLUDED_DIRS = {"tests", "starter-scripts", ".venv", ".git", "__pycache__", ".cache"}


def _get_py_files(root: pathlib.Path):
    """Yield all .py files excluding excluded directories."""
    for path in root.rglob("*.py"):
        parts = set(path.parts)
        if not parts.intersection(_EXCLUDED_DIRS):
            yield path


def test_no_hardcoded_credentials():
    """No .py file outside starter-scripts/ contains raw credential string literals."""
    root = pathlib.Path(__file__).parent.parent
    violations = []

    for py_file in _get_py_files(root):
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for lineno, line in enumerate(content.splitlines(), start=1):
            for pattern in _CREDENTIAL_PATTERNS:
                if pattern.search(line):
                    violations.append(
                        f"{py_file.relative_to(root)}:{lineno}: {line.strip()}"
                    )

    assert not violations, "Hardcoded credentials found in source files:\n" + "\n".join(
        violations
    )
