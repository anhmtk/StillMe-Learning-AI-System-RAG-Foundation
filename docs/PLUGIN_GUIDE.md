# StillMe AI Framework - Plugin Development Guide

This guide explains how to create new modules and plugins for the StillMe AI Framework.

## Table of Contents

- [Module Architecture](#module-architecture)
- [Creating a New Module](#creating-a-new-module)
- [Module Interface](#module-interface)
- [Configuration](#configuration)
- [Testing](#testing)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Module Architecture

StillMe uses a modular architecture where each component is a self-contained module that implements the `ModuleBase` interface. This ensures consistency and provides common functionality across the framework.

### Core Components

- **ModuleBase**: Abstract base class for all modules
- **ModuleInfo**: Information container for module metadata
- **ModuleStatus**: Status enumeration for module lifecycle
- **ConfigManager**: Centralized configuration management

## Creating a New Module

### 1. Basic Module Structure

```python
from stillme_core.base.module_base import ModuleBase, ModuleInfo, ModuleStatus
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class MyModule(ModuleBase):
    """My custom module for StillMe AI Framework"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Initialize your module here
    
    @property
    def module_info(self) -> ModuleInfo:
        return ModuleInfo(
            name="MyModule",
            version="1.0.0",
            description="Description of what this module does",
            author="Your Name",
            status=self._status,
            dependencies=["required", "packages"],
            config_schema={
                "param1": {"type": "str", "default": "default_value"},
                "param2": {"type": "int", "default": 42}
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the module"""
        try:
            # Your initialization logic here
            self._set_status(ModuleStatus.RUNNING)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MyModule: {e}")
            self._set_status(ModuleStatus.ERROR)
            return False
    
    async def process(self, input_data: Any) -> Any:
        """Process input data"""
        # Your processing logic here
        return processed_result
    
    async def cleanup(self) -> None:
        """Cleanup module resources"""
        # Your cleanup logic here
        self._set_status(ModuleStatus.STOPPED)
```

### 2. Stub Module (Placeholder)

If you need to create a placeholder module that's not yet implemented:

```python
from stillme_core.base.module_base import create_stub_module

# Create a stub module
stub = create_stub_module(
    name="FutureModule",
    description="This module will be implemented in the future"
)

# The stub will raise NotImplementedError when process() is called
```

## Module Interface

### Required Methods

All modules must implement these methods:

#### `module_info` (property)
Returns `ModuleInfo` with module metadata.

#### `initialize() -> bool`
Initializes the module. Returns `True` on success, `False` on failure.

#### `process(input_data: Any) -> Any`
Processes input data and returns the result. This is the main entry point for module functionality.

#### `cleanup() -> None`
Cleans up module resources when shutting down.

### Optional Methods

#### `get_config(key: str, default: Any = None) -> Any`
Gets a configuration value.

#### `set_config(key: str, value: Any) -> None`
Sets a configuration value.

## Configuration

### Using Configuration Manager

```python
from stillme_core.config.config_manager import get_config, get_threshold

# Get configuration
config = get_config()

# Get specific threshold
threshold = get_threshold("abuse_guard", "suggestion", 0.8)

# Get feature flag
enabled = get_feature_flag("emotion_detection", False)
```

### Module Configuration

```python
class MyModule(ModuleBase):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Get configuration values with defaults
        self.timeout = self.get_config("timeout", 30)
        self.max_retries = self.get_config("max_retries", 3)
```

### Environment Variable Overrides

Configuration can be overridden using environment variables with the `STILLME__` prefix:

```bash
# Override threshold
export STILLME__THRESHOLDS__ABUSE_GUARD__SUGGESTION=0.9

# Override feature flag
export STILLME__FEATURES__EMOTION_DETECTION=true

# Override policy level
export STILLME__POLICY__LEVEL=strict
```

## Testing

### Unit Tests

Create comprehensive unit tests for your module:

```python
import pytest
from my_module import MyModule

class TestMyModule:
    @pytest.fixture
    async def module(self):
        module = MyModule()
        await module.initialize()
        yield module
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_basic_functionality(self, module):
        result = await module.process("test input")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_error_handling(self, module):
        with pytest.raises(ValueError):
            await module.process(None)
```

### Integration Tests

Test your module with real data and other modules:

```python
@pytest.mark.asyncio
async def test_integration_with_other_modules(self):
    # Test interaction with other modules
    pass
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def process(self, input_data: Any) -> Any:
    try:
        # Your processing logic
        return result
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        self._set_status(ModuleStatus.ERROR)
        raise
```

### 2. Logging

Use appropriate logging levels:

```python
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

### 3. Resource Management

Always clean up resources:

```python
async def cleanup(self) -> None:
    try:
        # Close files, connections, etc.
        if self._connection:
            await self._connection.close()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    finally:
        self._set_status(ModuleStatus.STOPPED)
```

### 4. Configuration Validation

Validate configuration on initialization:

```python
async def initialize(self) -> bool:
    try:
        # Validate required configuration
        if not self.get_config("required_param"):
            raise ValueError("required_param is required")
        
        # Initialize with validated config
        return True
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False
```

## Examples

### Simple Text Processor

```python
class TextProcessor(ModuleBase):
    """Simple text processing module"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_length = self.get_config("max_length", 1000)
    
    @property
    def module_info(self) -> ModuleInfo:
        return ModuleInfo(
            name="TextProcessor",
            version="1.0.0",
            description="Processes text input",
            author="StillMe AI Team",
            status=self._status,
            dependencies=[],
            config_schema={
                "max_length": {"type": "int", "default": 1000}
            }
        )
    
    async def initialize(self) -> bool:
        self._set_status(ModuleStatus.RUNNING)
        return True
    
    async def process(self, input_data: Any) -> Any:
        if not isinstance(input_data, str):
            raise ValueError("Input must be a string")
        
        if len(input_data) > self.max_length:
            raise ValueError(f"Input too long (max {self.max_length} chars)")
        
        # Simple processing: convert to uppercase
        return input_data.upper()
    
    async def cleanup(self) -> None:
        self._set_status(ModuleStatus.STOPPED)
```

### API Client Module

```python
import httpx

class APIClient(ModuleBase):
    """HTTP API client module"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = self.get_config("base_url", "https://api.example.com")
        self.timeout = self.get_config("timeout", 30)
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def module_info(self) -> ModuleInfo:
        return ModuleInfo(
            name="APIClient",
            version="1.0.0",
            description="HTTP API client",
            author="StillMe AI Team",
            status=self._status,
            dependencies=["httpx"],
            config_schema={
                "base_url": {"type": "str", "default": "https://api.example.com"},
                "timeout": {"type": "int", "default": 30}
            }
        )
    
    async def initialize(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
            self._set_status(ModuleStatus.RUNNING)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize APIClient: {e}")
            self._set_status(ModuleStatus.ERROR)
            return False
    
    async def process(self, input_data: Any) -> Any:
        if not self._client:
            raise RuntimeError("APIClient not initialized")
        
        if isinstance(input_data, dict):
            method = input_data.get("method", "GET")
            endpoint = input_data.get("endpoint", "/")
            data = input_data.get("data")
        else:
            method = "GET"
            endpoint = str(input_data)
            data = None
        
        response = await self._client.request(method, endpoint, json=data)
        response.raise_for_status()
        return response.json()
    
    async def cleanup(self) -> None:
        if self._client:
            await self._client.aclose()
        self._set_status(ModuleStatus.STOPPED)
```

## Contributing

When contributing modules to StillMe:

1. Follow the module interface exactly
2. Include comprehensive tests
3. Document your module thoroughly
4. Use type hints
5. Handle errors gracefully
6. Clean up resources properly
7. Follow the coding style guidelines

For more information, see the main StillMe documentation and examples in the codebase.
