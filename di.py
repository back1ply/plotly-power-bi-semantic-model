"""Dependency Injection Container.

Provides centralized management and initialization of application components.
Moved to root to maintain proper layering (Composition Root).
"""

from application.data_loader import StartupDataLoader
from config import AppConfig
from infrastructure.auth import MsalTokenProvider
from infrastructure.cache import InMemoryCache
from infrastructure.cache import QueryCache
from infrastructure.dax import DaxQueryLoader
from infrastructure.decorators import CachingRepositoryDecorator
from infrastructure.pbi_client import PbiClient
from infrastructure.pbi_client import PbiClientConfig
from infrastructure.pbi_embed import PbiEmbedService
from infrastructure.query_service import QueryService
from infrastructure.rate_limiting import SlidingWindowRateLimiter
from infrastructure.repository import LiveRepository
from infrastructure.schema_service import SchemaService


class DiContainer:
    """Lightweight dependency injection container for component management."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize the container with dependencies wired together.

        Args:
            config: Application configuration.
        """
        self.config = config

        # 1. Infrastructure Services
        self.token_provider = MsalTokenProvider(
            tenant_id=config.tenant_id,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )

        self.rate_limiter = SlidingWindowRateLimiter(
            max_requests=config.max_rate_limit_requests,
            window_seconds=config.rate_limit_window,
        )

        self.pbi_config = PbiClientConfig(
            workspace_id=config.workspace_id,
            dataset_id=config.dataset_id,
            api_base=config.api_base,
            request_timeout=config.request_timeout,
        )

        self.pbi_client = PbiClient(
            token_provider=self.token_provider,
            rate_limiter=self.rate_limiter,
            config=self.pbi_config,
        )

        self.pbi_embed = PbiEmbedService(
            token_provider=self.token_provider,
            config=self.pbi_config,
        )

        if config.use_disk_cache:
            self.query_cache = QueryCache(
                cache_dir=config.cache_dir,
                ttl_seconds=config.cache_ttl,
            )
        else:
            self.query_cache = InMemoryCache(ttl_seconds=config.cache_ttl)

        self.query_loader = DaxQueryLoader.from_path(config.dax_path)

        # 2. Implementation Services
        self.query_service = QueryService(query_source=self.query_loader)
        self.schema_service = SchemaService(
            query_client=self.pbi_client,
            query_service=self.query_service,
        )

        self.live_repository = LiveRepository(
            query_service=self.query_service,
            schema_service=self.schema_service,
            query_client=self.pbi_client,
        )

        self.repository = CachingRepositoryDecorator(
            repository=self.live_repository,
            query_cache=self.query_cache,
        )

        # 3. Domain/Core Logic
        # StartupDataLoader now depends on RepositoryPort (OO-002)
        self.data_loader = StartupDataLoader(repository=self.repository)
