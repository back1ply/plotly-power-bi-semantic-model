"""Dependency Injection Container.

Provides centralized management and initialization of application components.
Moved to root to maintain proper layering (Composition Root).
"""

from application.data_loader import StartupDataLoader
from config import AppConfig
from domain import ClassifierPort
from domain import DataAnalysisExpressionsLoaderPort
from domain import DataAnalysisExpressionsSourcePort
from domain import EmbedPort
from domain import QueryClientPort
from domain import RateLimiterPort
from domain import ReadWriteCachePort
from domain import RepositoryPort
from domain import SchemaPort
from domain import TemplateLoaderPort
from domain import TokenProviderPort
from domain.services import ColumnClassifier
from infrastructure.adapters import FileSystemTemplateLoader
from infrastructure.auth import MsalTokenProvider
from infrastructure.cache import InMemoryCache
from infrastructure.cache import QueryCache
from infrastructure.data_analysis_expressions import DataAnalysisExpressionsQueryLoader
from infrastructure.decorators import CachingDataDecorator
from infrastructure.decorators import CachingSchemaDecorator
from infrastructure.decorators import UnifiedCachingRepository
from infrastructure.power_bi_client import PowerBiClient
from infrastructure.power_bi_client import PowerBiClientConfiguration
from infrastructure.power_bi_embed import PowerBiEmbedService
from infrastructure.query_service import QueryService
from infrastructure.rate_limiting import SlidingWindowRateLimiter
from infrastructure.repository import LiveRepository
from infrastructure.schema_service import SchemaService


class DiContainer:
    """Lightweight dependency injection container for component management."""

    token_provider: TokenProviderPort
    rate_limiter: RateLimiterPort
    power_bi_config: PowerBiClientConfiguration
    power_bi_client: QueryClientPort
    power_bi_embed: EmbedPort
    query_cache: ReadWriteCachePort
    query_loader: DataAnalysisExpressionsLoaderPort
    query_service: DataAnalysisExpressionsSourcePort
    schema_service: SchemaPort
    live_repository: RepositoryPort
    cached_schema: SchemaPort
    cached_data: CachingDataDecorator  # Specific class as it has extra methods? No, DataPort.
    repository: RepositoryPort
    data_loader: StartupDataLoader
    classifier: ClassifierPort
    asset_loader: TemplateLoaderPort

    def __init__(self, config: AppConfig) -> None:
        """Initialize the container with dependencies wired together.

        Args:
            config: Application configuration.
        """
        self.config = config

        # 1. Infrastructure Services
        self.asset_loader = FileSystemTemplateLoader(base_path=config.base_dir / "assets")

        self.token_provider = MsalTokenProvider(
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )

        self.rate_limiter = SlidingWindowRateLimiter(
            max_requests=config.max_rate_limit_requests,
            window_seconds=config.rate_limit_window,
        )

        self.power_bi_config = PowerBiClientConfiguration(
            workspace_id=config.workspace_id,
            dataset_id=config.dataset_id,
            api_base=config.api_base,
            request_timeout=config.request_timeout,
        )

        self.power_bi_client = PowerBiClient(
            token_provider=self.token_provider,
            rate_limiter=self.rate_limiter,
            config=self.power_bi_config,
        )

        self.power_bi_embed = PowerBiEmbedService(
            token_provider=self.token_provider,
            config=self.power_bi_config,
        )

        if config.use_disk_cache:
            self.query_cache = QueryCache(
                cache_dir=config.cache_dir,
                ttl_seconds=config.cache_ttl,
            )
        else:
            self.query_cache = InMemoryCache(ttl_seconds=config.cache_ttl)

        self.query_loader = DataAnalysisExpressionsQueryLoader.from_path(config.dax_path)

        # 2. Implementation Services
        self.query_service = QueryService(query_source=self.query_loader)
        self.schema_service = SchemaService(
            query_client=self.power_bi_client,
            query_service=self.query_service,
        )

        self.live_repository = LiveRepository(
            query_service=self.query_service,
            schema_service=self.schema_service,
            query_client=self.power_bi_client,
        )

        # Segregated Decorators (CA-001)
        self.cached_schema = CachingSchemaDecorator(
            schema_service=self.schema_service,
            query_cache=self.query_cache,
        )

        self.cached_data = CachingDataDecorator(
            data_service=self.live_repository,
            query_cache=self.query_cache,
        )

        # For backward compatibility with unified RepositoryPort consumers (CA-001)
        self.repository = UnifiedCachingRepository(
            schema=self.cached_schema,
            data=self.cached_data,
            dax_query_source=self.query_service,
            client=self.power_bi_client,
        )

        # 3. Domain/Core Logic
        self.classifier = ColumnClassifier()

        # StartupDataLoader now depends on DataPort (OO-002, CA-001)
        self.data_loader = StartupDataLoader(repository=self.cached_data)
