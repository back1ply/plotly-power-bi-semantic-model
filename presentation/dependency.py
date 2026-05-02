"""Dependency injection for the presentation layer."""

from typing import Any
from typing import cast
from typing import TypeVar

T = TypeVar("T")


class ServiceRegistry:
    """Typed registry for managing service instances (Eliminates Service Locator).
    
    This class allows for explicit registration and retrieval of services by 
    their port type, ensuring type safety and decoupling components from 
    the Flask application context where possible.
    """

    def __init__(self) -> None:
        self._services: dict[type, Any] = {}
        self._named_services: dict[str, Any] = {}

    def register[T](self, port_type: type[T], instance: T) -> None:
        """Register a service instance for a specific type."""
        self._services[port_type] = instance

    def register_named(self, name: str, instance: Any) -> None:
        """Register a service instance with a string name (for backward compatibility)."""
        self._named_services[name] = instance

    def get[T](self, port_type: type[T]) -> T:
        """Retrieve a service instance by its type."""
        # 1. Direct match (Fastest)
        instance = self._services.get(port_type)
        if instance is not None:
            return cast(T, instance)
            
        # 2. Search for registered types that are subclasses of port_type
        for registered_type, registered_instance in self._services.items():
            try:
                if issubclass(registered_type, port_type):
                    return cast(T, registered_instance)
            except TypeError:
                # Handle cases where issubclass fails (e.g. non-class types)
                continue

        # 3. Fallback to check if it's in named services by its name
        name = port_type.__name__
        instance = self._named_services.get(name)
            
        if instance is None:
            raise RuntimeError(f"Service of type '{port_type.__name__}' not registered")
        return cast(T, instance)

    def get_named[T](self, name: str) -> T:
        """Retrieve a service instance by its registered name."""
        instance = self._named_services.get(name)
        if instance is None:
            raise RuntimeError(f"Service named '{name}' not registered")
        return cast(T, instance)


# Singleton registry instance
registry = ServiceRegistry()


def get_repository[T](port_type: type[T]) -> T:
    """Get a repository or service from the registry by its type.

    Args:
        port_type: The specific port type required by the consumer.

    Returns:
        The instance.
    """
    return registry.get(port_type)


def get_service[T](key: str | type[T]) -> T:
    """Get a service from the registry by name or type.

    Args:
        key: The key (string) or type where the service is stored.

    Returns:
        The service instance.
    """
    if isinstance(key, type):
        return registry.get(key)
    return registry.get_named(key)
