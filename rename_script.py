import os
from pathlib import Path

renames = {
    "PbiClientConfig": "PbiClientConfig",
    "PbiClient": "PbiClient",
    "DiContainer": "DiContainer",
    "KpiConfig": "KpiConfig",
}


def rename_in_file(file_path):
    path = Path(file_path)
    with path.open(encoding="utf-8") as f:
        content = f.read()

    new_content = content
    for old, new in renames.items():
        new_content = new_content.replace(old, new)

    if new_content != content:
        with path.open("w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {file_path}")


exclude_dirs = {
    ".git",
    ".venv",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    ".mypy_cache",
}

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if (
            file.endswith(".py")
            or file.endswith(".md")
            or file.endswith(".json")
            or file.endswith(".toml")
        ):
            rename_in_file(Path(root) / file)
