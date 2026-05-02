"""Infrastructure Adapters.

Handles data transformation between infrastructure components and the domain.
"""


from pathlib import Path


import polars as pl
from typing import Any, Iterable, cast
from domain.ports import DataFrame


class PolarsDataFrameAdapter(DataFrame):
    """Adapter for Polars DataFrame that implements the domain's DataFrame protocol. (CA-002)"""

    def __init__(self, data_frame: pl.DataFrame) -> None:
        """Initialize with a Polars DataFrame."""
        self._df = data_frame

    @property
    def columns(self) -> list[str]:
        return self._df.columns

    @property
    def schema(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._df.schema)

    def to_dicts(self) -> list[dict[str, Any]]:
        return self._df.to_dicts()

    def select(self, *exprs: Any, **named_exprs: Any) -> "DataFrame":
        return PolarsDataFrameAdapter(self._df.select(*exprs, **named_exprs))

    def filter(self, *predicates: Any, **constraints: Any) -> "DataFrame":
        # Handle simple string equality for convenience if passed as keyword args
        if constraints:
            for key, value in constraints.items():
                self._df = self._df.filter(pl.col(key) == value)
            return PolarsDataFrameAdapter(self._df)
        return PolarsDataFrameAdapter(self._df.filter(*predicates))

    def sort(
        self,
        by: str | Any | list[str | Any],
        descending: bool | list[bool] = False,
    ) -> "DataFrame":
        return PolarsDataFrameAdapter(self._df.sort(by, descending=descending))

    def with_columns(self, *exprs: Any, **named_exprs: Any) -> "DataFrame":
        return PolarsDataFrameAdapter(self._df.with_columns(*exprs, **named_exprs))

    def head(self, n: int) -> "DataFrame":
        return PolarsDataFrameAdapter(self._df.head(n))

    def iter_rows(self, named: bool = True) -> Iterable[Any]:
        return self._df.iter_rows(named=named)

    def get_column(self, name: str) -> Any:
        return self._df.get_column(name)

    def unique(self, subset: str | list[str] | None = None, maintain_order: bool = False) -> "DataFrame":
        return PolarsDataFrameAdapter(self._df.unique(subset=subset, maintain_order=maintain_order))

    def group_by(self, by: str | list[str]) -> Any:
        # Returns a Polars GroupBy object - we might need to wrap it if we want full decoupling
        return self._df.group_by(by)

    def pivot(
        self,
        index: str | list[str],
        on: str | list[str],
        values: str | list[str],
        aggregate_function: str = "sum",
    ) -> "DataFrame":
        return PolarsDataFrameAdapter(
            self._df.pivot(index=index, on=on, values=values, aggregate_function=aggregate_function)
        )

    def with_column_renamed(self, old: str, new: str) -> "DataFrame":
        return PolarsDataFrameAdapter(self._df.rename({old: new}))

    def cast_date(self, column: str, alias: str) -> "DataFrame":
        return PolarsDataFrameAdapter(
            self._df.with_columns(pl.col(column).str.to_datetime(strict=False).alias(alias))
        )

    def format_date(self, column: str, alias: str, format: str) -> "DataFrame":
        return PolarsDataFrameAdapter(self._df.with_columns(pl.col(column).dt.strftime(format).alias(alias)))

    def aggregate(self, by: str | list[str], aggregations: dict[str, str]) -> "DataFrame":
        agg_exprs = []
        for col, func in aggregations.items():
            if func == "sum":
                agg_exprs.append(pl.col(col).sum())
            elif func == "mean":
                agg_exprs.append(pl.col(col).mean())
            elif func == "count":
                agg_exprs.append(pl.col(col).count())
            else:
                raise ValueError(f"Unsupported aggregation function: {func}")
        
        return PolarsDataFrameAdapter(self._df.group_by(by).agg(agg_exprs))

    def is_empty(self) -> bool:
        return self._df.is_empty()

    def __len__(self) -> int:
        return len(self._df)


class FileSystemTemplateLoader:
    """Implementation of TemplateLoaderPort that loads from the local filesystem. (OO-002)"""

    def __init__(self, base_path: Path) -> None:
        """Initialize with base path for assets."""
        self.base_path = base_path

    def load_html_template(self, name: str) -> str:
        """Load an HTML template from the assets directory."""
        template_path = self.base_path / name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text(encoding="utf-8")


def extract_column_name(column: str) -> str:
    """Extract Power BI column from 'Table'[Column] to Column."""
    return column.rsplit("[", 1)[-1].rstrip("]") if "[" in column else column
