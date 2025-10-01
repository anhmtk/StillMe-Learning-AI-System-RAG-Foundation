"""
Base Module Interface for StillMe AI Framework

This module provides the base interface that all StillMe modules should implement.
It ensures consistency and provides common functionality across the framework.

Author: StillMe AI Team
Version: 1.0.0
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """Module status enumeration"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass
class ModuleInfo:
    """Module information container"""
    name: str
    version: str
    description: str
    author: str
    status: ModuleStatus
    dependencies: List[str]
    config_schema: Optional[Dict[str, Any]] = None


class ModuleBase(ABC):
    """
    Base class for all StillMe modules
    
    This abstract base class defines the interface that all modules must implement.
    It provides common functionality and ensures consistency across the framework.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the module
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._status = ModuleStatus.INITIALIZED
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def module_info(self) -> ModuleInfo:
        """
        Get module information
        
        Returns:
            ModuleInfo: Module information container
        """
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the module
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """
        Process input data
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed output data
            
        Raises:
            NotImplementedError: If the module is a stub/placeholder
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Cleanup module resources
        """
        pass

    @property
    def status(self) -> ModuleStatus:
        """Get current module status"""
        return self._status

    def _set_status(self, status: ModuleStatus) -> None:
        """Set module status"""
        self._status = status
        self._logger.info(f"Module status changed to: {status.value}")

    def is_implemented(self) -> bool:
        """
        Check if module is fully implemented (not a stub)
        
        Returns:
            bool: True if implemented, False if stub
        """
        return self._status != ModuleStatus.NOT_IMPLEMENTED

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value


class StubModule(ModuleBase):
    """
    Stub module implementation for placeholder modules
    
    This class provides a standard implementation for modules that are not yet
    fully implemented. It raises NotImplementedError with clear messages.
    """

    def __init__(self, name: str, description: str = "Not implemented yet", config: Optional[Dict[str, Any]] = None):
        """
        Initialize stub module
        
        Args:
            name: Module name
            description: Module description
            config: Optional configuration
        """
        super().__init__(config)
        self._name = name
        self._description = description
        self._status = ModuleStatus.NOT_IMPLEMENTED

    @property
    def module_info(self) -> ModuleInfo:
        """Get module information"""
        return ModuleInfo(
            name=self._name,
            version="0.0.0-stub",
            description=self._description,
            author="StillMe AI Team",
            status=self._status,
            dependencies=[],
            config_schema=None
        )

    async def initialize(self) -> bool:
        """Initialize stub module"""
        self._logger.warning(f"Stub module '{self._name}' initialized - functionality not available")
        self._set_status(ModuleStatus.INITIALIZED)
        return True

    async def process(self, input_data: Any) -> Any:
        """
        Process input data (stub implementation)
        
        Raises:
            NotImplementedError: Always raises for stub modules
        """
        error_msg = f"Module '{self._name}' is not implemented yet. {self._description}"
        self._logger.error(error_msg)
        raise NotImplementedError(error_msg)

    async def cleanup(self) -> None:
        """Cleanup stub module"""
        self._logger.info(f"Stub module '{self._name}' cleaned up")
        self._set_status(ModuleStatus.STOPPED)


def create_stub_module(name: str, description: str = "Not implemented yet") -> StubModule:
    """
    Factory function to create stub modules
    
    Args:
        name: Module name
        description: Module description
        
    Returns:
        StubModule: Configured stub module
    """
    return StubModule(name, description)
