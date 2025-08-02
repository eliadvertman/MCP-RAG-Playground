"""
Main dependency injection container implementation.
"""

from typing import Any, Callable, Dict, Optional, TypeVar, Type
from enum import Enum
from .config import ConfigRegistry, ConfigProvider

T = TypeVar('T')


class ServiceScope(Enum):
    """Service lifetime scopes."""
    SINGLETON = "singleton"  # Single instance for container lifetime
    TRANSIENT = "transient"  # New instance every time
    SCOPED = "scoped"       # Single instance per scope/request


class ServiceRegistration:
    """Represents a service registration."""
    
    def __init__(self, 
                 factory: Callable[[], Any], 
                 scope: ServiceScope = ServiceScope.SINGLETON,
                 dependencies: Optional[list[str]] = None):
        self.factory = factory
        self.scope = scope
        self.dependencies = dependencies or []
        self.instance = None  # For singleton instances


class Container:
    """Dependency injection container."""
    
    def __init__(self, environment: str = "default"):
        self.environment = environment
        self._services: Dict[str, ServiceRegistration] = {}
        self._config_registry = ConfigRegistry()
        self._building_services: set[str] = set()  # Track circular dependencies
    
    def register_config_provider(self, provider: ConfigProvider) -> 'Container':
        """
        Register a configuration provider.
        
        Args:
            provider: Configuration provider instance
            
        Returns:
            Self for method chaining
        """
        self._config_registry.register(provider)
        return self
    
    def register_service(self, 
                        name: str, 
                        factory: Callable[[], T], 
                        scope: ServiceScope = ServiceScope.SINGLETON,
                        dependencies: Optional[list[str]] = None) -> 'Container':
        """
        Register a service with the container.
        
        Args:
            name: Service name
            factory: Factory function to create the service
            scope: Service lifetime scope
            dependencies: List of dependency service names
            
        Returns:
            Self for method chaining
        """
        registration = ServiceRegistration(factory, scope, dependencies)
        self._services[name] = registration
        return self
    
    def register_singleton(self, name: str, factory: Callable[[], T]) -> 'Container':
        """Register a singleton service."""
        return self.register_service(name, factory, ServiceScope.SINGLETON)
    
    def register_transient(self, name: str, factory: Callable[[], T]) -> 'Container':
        """Register a transient service."""
        return self.register_service(name, factory, ServiceScope.TRANSIENT)
    
    def register_instance(self, name: str, instance: Any) -> 'Container':
        """Register a pre-created instance as singleton."""
        def factory():
            return instance
        
        registration = ServiceRegistration(factory, ServiceScope.SINGLETON)
        registration.instance = instance
        self._services[name] = registration
        return self
    
    def get(self, service_name: str) -> Any:
        """
        Get a service instance from the container.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service not registered
            RuntimeError: If circular dependency detected
        """
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' not registered")
        
        # Check for circular dependencies
        if service_name in self._building_services:
            raise RuntimeError(f"Circular dependency detected for service '{service_name}'")
        
        registration = self._services[service_name]
        
        # Return singleton instance if already created
        if registration.scope == ServiceScope.SINGLETON and registration.instance is not None:
            return registration.instance
        
        # Build dependencies first
        self._building_services.add(service_name)
        try:
            instance = self._build_service(registration)
        finally:
            self._building_services.discard(service_name)
        
        # Cache singleton instances
        if registration.scope == ServiceScope.SINGLETON:
            registration.instance = instance
        
        return instance
    
    def get_config(self, config_name: str) -> Any:
        """
        Get configuration from registered providers.
        
        Args:
            config_name: Name of the configuration provider
            
        Returns:
            Configuration object
        """
        return self._config_registry.get_config(config_name, self.environment)
    
    def has_service(self, service_name: str) -> bool:
        """Check if a service is registered."""
        return service_name in self._services
    
    def has_config(self, config_name: str) -> bool:
        """Check if a configuration provider is registered."""
        return config_name in self._config_registry.list_providers()
    
    def clear_singletons(self) -> None:
        """Clear all singleton instances (useful for testing)."""
        for registration in self._services.values():
            if registration.scope == ServiceScope.SINGLETON:
                registration.instance = None
    
    def _build_service(self, registration: ServiceRegistration) -> Any:
        """Build a service instance, resolving dependencies."""
        # No dependencies, just call factory
        if not registration.dependencies:
            return registration.factory()
        
        # Resolve dependencies and inject them
        dependencies = {}
        for dep_name in registration.dependencies:
            dependencies[dep_name] = self.get(dep_name)
        
        # Call factory with dependencies
        # Note: This assumes factory can accept dependencies as keyword arguments
        # For more complex scenarios, we might need a different approach
        try:
            return registration.factory(**dependencies)
        except TypeError:
            # Fallback: call factory without arguments
            return registration.factory()
    
    def list_services(self) -> list[str]:
        """Get list of registered service names."""
        return list(self._services.keys())
    
    def list_configs(self) -> list[str]:
        """Get list of registered configuration provider names."""
        return self._config_registry.list_providers()