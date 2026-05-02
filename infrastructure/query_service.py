import logging
from typing import Any

from domain import DataAnalysisExpressionsFragment
from domain import DataAnalysisExpressionsLoaderPort
from domain import DataAnalysisExpressionsSourcePort
from domain import DataAnalysisExpressionsTemplate
from domain import FragmentCategory
from domain import QueryKey
from domain import QueryNotFoundError

logger = logging.getLogger(__name__)


class QueryService(DataAnalysisExpressionsSourcePort):

    def __init__(self, query_source: DataAnalysisExpressionsLoaderPort) -> None:
        self._source = query_source

    def get_raw_query(self, key: QueryKey) -> str:
        try:
            return self._source.get_raw_query(key)
        except (KeyError, QueryNotFoundError) as exception:
            raise QueryNotFoundError(f"Query not found for key: {key}") from exception

    def get_query_template(self, key: str) -> DataAnalysisExpressionsTemplate:
        try:
            return self._source.get_query_template(key)
        except (KeyError, QueryNotFoundError) as exception:
            raise QueryNotFoundError(f"Template not found for key: {key}") from exception

    def get_fragment(self, category: FragmentCategory, key: str) -> DataAnalysisExpressionsFragment:
        try:
            return self._source.get_fragment(category, key)
        except (KeyError, QueryNotFoundError) as exception:
            raise QueryNotFoundError(f"Fragment not found for {category}/{key}") from exception

    def get_formatted_query(self, key: str, parameters: dict[str, Any] | None = None) -> str:
        parameters = parameters or {}
        try:
            template = self.get_query_template(key)
            return template.content.format(**parameters)
        except (KeyError, QueryNotFoundError, ValueError, AttributeError) as exception:
            raise QueryNotFoundError(
                f"Template or fragments not found for {key} with {parameters}: {exception}"
            ) from exception

    def get_summarized_query_text(self, measure_key: str, dimension_key: str) -> str:
        try:
            measure_dax = self.get_fragment(FragmentCategory.MEASURE, measure_key)
            dimension_dax = self.get_fragment(FragmentCategory.DIMENSION, dimension_key)
            template = self.get_query_template("summarizecolumns")

            return template.content.format(
                columns=f"{dimension_dax.content},",
                measures=f'"{measure_key}", {measure_dax.content}',
            )
        except (KeyError, QueryNotFoundError, ValueError, AttributeError) as exception:
            raise QueryNotFoundError(
                f"Template or fragments not found for {measure_key}/{dimension_key}: {exception}"
            ) from exception
