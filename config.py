import os
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import TypeVar

from dotenv import load_dotenv

from domain.exceptions import ConfigurationError

load_dotenv()

T = TypeVar("T")


def _env_field[T](key: str, default: T, converter: Callable[[Any], T] | None = None) -> Any:
    if converter is None:
        _type = type(default)
        _conv = _type if _type is not Any else str
    else:
        _conv = converter

    def _get_val():
        val = os.getenv(key)
        if val is None or (val == "" and default != ""):
            return default
        return _conv(val)

    return field(default_factory=_get_val)


@dataclass(frozen=True)
class ThemeConfig:
    app_title: str = _env_field("APP_TITLE", "Sales Dashboard")
    primary_color: str = _env_field("PRIMARY_COLOR", "blue")
    font_family: str = _env_field("FONT_FAMILY", "'Inter', sans-serif")


@dataclass(frozen=True)
class AppConfig:
    tenant_id: str = _env_field("TENANT_ID", "")
    client_id: str = _env_field("CLIENT_ID", "")
    client_secret: str = _env_field("CLIENT_SECRET", "")
    workspace_id: str = _env_field("WORKSPACE_ID", "")
    dataset_id: str = _env_field("DATASET_ID", "")
    report_id: str = _env_field("REPORT_ID", "")
    cache_dir: str = _env_field("CACHE_DIR", "./.cache")
    cache_ttl: int = _env_field("CACHE_TTL_SECONDS", 3600, int)
    use_disk_cache: bool = _env_field("USE_DISK_CACHE", False, lambda v: str(v).lower() == "true")
    max_retries: int = _env_field("STARTUP_RETRY_MAX", 3, int)
    retry_delay: float = _env_field("STARTUP_RETRY_DELAY", 2.0, float)
    max_rate_limit_requests: int = _env_field("RATE_LIMIT_MAX_REQUESTS", 120, int)
    rate_limit_window: int = _env_field("RATE_LIMIT_WINDOW_SECONDS", 60, int)
    request_timeout: int = _env_field("REQUEST_TIMEOUT_SECONDS", 60, int)
    api_base: str = _env_field("PBI_API_BASE", "https://api.powerbi.com/v1.0/myorg")
    preload_data: bool = _env_field("PRELOAD_DATA", False, lambda v: str(v).lower() == "true")
    debug: bool = _env_field("FLASK_DEBUG", False, lambda v: str(v).lower() in ("true", "1", "t"))

    def validate(self) -> None:
        """Validates that all required configuration is present."""
        required = {
            "TENANT_ID": self.tenant_id,
            "CLIENT_ID": self.client_id,
            "CLIENT_SECRET": self.client_secret,
            "WORKSPACE_ID": self.workspace_id,
            "DATASET_ID": self.dataset_id,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please check your .env file or environment settings."
            )

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent

    dax_path: Path = field(
        default_factory=lambda: Path(
            os.getenv(
                "DAX_PATH",
                str(Path(__file__).resolve().parent / "queries" / "dax.json"),
            )
        )
    )


def get_env_var(key: str, default: Any = None) -> Any:
    return os.environ.get(key, default)
