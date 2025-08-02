"""
Configuration provider interfaces for dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ConfigProvider(ABC):
    """Abstract base class for configuration providers."""
    
    @abstractmethod
    def get_config(self, environment: str = "default") -> Any:
        """
        Get configuration for the specified environment.
        
        Args:
            environment: The environment name (e.g., 'dev', 'test', 'prod')
            
        Returns:
            Configuration object specific to the provider
        """
        pass
    
    @abstractmethod
    def get_config_name(self) -> str:
        """Get the name of this configuration provider."""
        pass


class ConfigRegistry:
    """Registry for managing multiple configuration providers."""
    
    def __init__(self):
        self._providers: Dict[str, ConfigProvider] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def register(self, provider: ConfigProvider) -> None:
        """Register a configuration provider."""
        name = provider.get_config_name()
        self._providers[name] = provider
        
        # Initialize cache for this provider
        if name not in self._cache:
            self._cache[name] = {}
    
    def get_config(self, config_name: str, environment: str = "default") -> Any:
        """
        Get configuration from a registered provider.
        
        Args:
            config_name: Name of the configuration provider
            environment: Environment name
            
        Returns:
            Configuration object
            
        Raises:
            KeyError: If configuration provider not found
        """
        if config_name not in self._providers:
            raise KeyError(f"Configuration provider '{config_name}' not found")
        
        # Check cache first
        cache_key = f"{config_name}:{environment}"
        if cache_key in self._cache.get(config_name, {}):
            return self._cache[config_name][cache_key]
        
        # Get config from provider and cache it
        provider = self._providers[config_name]
        config = provider.get_config(environment)
        self._cache[config_name][cache_key] = config
        
        return config
    
    def clear_cache(self, config_name: Optional[str] = None) -> None:
        """
        Clear configuration cache.
        
        Args:
            config_name: If provided, clear cache for specific provider only
        """
        if config_name:
            if config_name in self._cache:
                self._cache[config_name].clear()
        else:
            for provider_cache in self._cache.values():
                provider_cache.clear()
    
    def list_providers(self) -> list[str]:
        """Get list of registered provider names."""
        return list(self._providers.keys())