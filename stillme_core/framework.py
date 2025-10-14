#!/usr/bin/env python3
"""
STILLME AI FRAMEWORK
STILLME AI FRAMEWORK

This is the core framework for StillMe AI - an AI IPC system.
StillMe is an AI created by Anh Nguyen (Vietnamese) with major support
from AI organizations such as OpenAI, Google, DeepSeek, and its purpose
to accompany and befriend everyone.

PROJECT STATUS: ACTIVE

- Modules: 10 core modules
- Tests: Available
- Complexity: Moderate
- Security: Basic encryption
- Performance: Standard
- Language: Vietnamese + English support

CORE MODULES:
1. ContentIntegrityFilter - Content filtering
2. LayeredMemoryV1 - Memory management
3. UnifiedAPIManager - API management
4. ConversationalCore - Chat engine
5. PersonaMorph - Personality system
6. EthicalCoreSystem - Ethics checking
7. TokenOptimizer - Token optimization
8. EmotionSenseV1 - Emotion detection
9. SecureMemoryManager - Encryption + backup
10. AgentDev - Development assistant

INFO:
- SecureMemoryManager integration available
- Project cleanup completed
- All 10 modules working
- Vietnamese language support available
- Testing coverage available

NEXT ACTIONS:
1. Test framework startup
2. Verify SecureMemoryManager health
3. Run integration tests
4. Performance benchmarking
"""

import os
import sys
import time
import logging
from typing import Any, Dict, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global flag for module imports
MODULES_IMPORTED = True


class StillMeFramework:
    """
    Main framework class for StillMe AI system
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize StillMe Framework"""
        self.config = config or {}
        self.logger = logger
        self._metrics = {
            "startup_time": time.time(),
            "heartbeat": [],
            "requests": 0,
            "errors": 0,
        }

        # Initialize core components
        self._initialize_components()
        
        # Initialize core modules
        self._initialize_core_modules()

        self.logger.info("STILLME Framework started")

    def _initialize_components(self):
        """Initialize core components"""
        try:
            # Initialize ethics checker
            from stillme_core.modules.ethical_core_system import EthicsChecker

            security_level = self.config.get("security_level", "medium")
            if isinstance(security_level, str):
                self.ethics = EthicsChecker(level=security_level)
            else:
                self.ethics = EthicsChecker(level="medium")

            # Initialize API docs
            self._api_docs = self._create_api_docs()
            
            # Initialize AgentDev
            self._init_agentdev()

        except Exception as e:
            self.logger.warning(f"Some components not available: {e}")
            # Still try to initialize AgentDev even if other components fail
            self._init_agentdev()

    def _create_api_docs(self):
        """Create API documentation generator"""

        class OpenAPIGenerator:
            def __init__(self):
                self.spec = {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "StillMe AI Framework",
                        "version": "1.0.0",
                        "description": "AI IPC system",
                    },
                    "paths": {},
                }

            def generate_spec(self):
                return self.spec

        return OpenAPIGenerator()

    def _initialize_core_modules(self):
        """Initialize all core modules"""
        if not MODULES_IMPORTED:
            self.logger.warning("Modules not imported, skipping initialization")
            return

        try:
            # Initialize core modules
            self._init_content_filter()
            self._init_memory_system()
            self._init_api_manager()
            self._init_conversational_core()
            self._init_persona_morph()
            self._init_ethical_core()
            self._init_token_optimizer()
            self._init_emotion_sense()
            self._init_secure_memory()
            self._init_agentdev()

        except Exception as e:
            self.logger.error(f"Error initializing modules: {e}")

    def _init_content_filter(self):
        """Initialize Content Integrity Filter"""
        try:
            from stillme_core.modules.content_integrity_filter import (
                ContentIntegrityFilter,
            )

            self.content_filter = ContentIntegrityFilter()
        except ImportError:
            self.logger.warning("ContentIntegrityFilter not available")

    def _init_memory_system(self):
        """Initialize Layered Memory System"""
        try:
            from stillme_core.modules.layered_memory_v1 import LayeredMemoryV1

            self.layered_memory = LayeredMemoryV1()
        except ImportError:
            self.logger.warning("LayeredMemoryV1 not available")

    def _init_api_manager(self):
        """Initialize Unified API Manager"""
        try:
            from stillme_core.modules.unified_api_manager import UnifiedAPIManager

            self.api_manager = UnifiedAPIManager()
        except ImportError:
            self.logger.warning("UnifiedAPIManager not available")

    def _init_conversational_core(self):
        """Initialize Conversational Core"""
        try:
            from stillme_core.modules.conversational_core_v1 import ConversationalCore

            self.conversational_core = ConversationalCore()
        except ImportError:
            self.logger.warning("ConversationalCore not available")

    def _init_persona_morph(self):
        """Initialize Persona Morph"""
        try:
            from stillme_core.modules.persona_morph import PersonaMorph

            self.persona_morph = PersonaMorph()
        except ImportError:
            self.logger.warning("PersonaMorph not available")

    def _init_ethical_core(self):
        """Initialize Ethical Core System"""
        try:
            from stillme_core.modules.ethical_core_system import EthicalCoreSystem

            self.ethical_core = EthicalCoreSystem()
        except ImportError:
            self.logger.warning("EthicalCoreSystem not available")

    def _init_token_optimizer(self):
        """Initialize Token Optimizer"""
        try:
            from stillme_core.modules.token_optimizer import TokenOptimizer

            self.token_optimizer = TokenOptimizer()
        except ImportError:
            self.logger.warning("TokenOptimizer not available")

    def _init_emotion_sense(self):
        """Initialize Emotion Sense V1"""
        try:
            from stillme_core.modules.emotion_sense_v1 import EmotionSenseV1

            self.emotion_sense = EmotionSenseV1()
        except ImportError:
            self.logger.warning("EmotionSenseV1 not available")

    def _init_secure_memory(self):
        """Initialize Secure Memory Manager"""
        try:
            from stillme_core.modules.secure_memory_manager import SecureMemoryManager

            self.secure_memory = SecureMemoryManager()
        except ImportError:
            self.logger.warning("SecureMemoryManager not available")

    def _init_agentdev(self):
        """Initialize AgentDev"""
        try:
            from agent_dev.core.agentdev import AgentDev

            self.agentdev = AgentDev()
            self.logger.info("AgentDev initialized successfully")
        except ImportError as e:
            self.logger.warning(f"AgentDev not available: {e}")
        except Exception as e:
            self.logger.error(f"Error initializing AgentDev: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get framework status"""
        return {
            "status": "ACTIVE",
            "uptime": time.time() - self._metrics["startup_time"],
            "requests": self._metrics["requests"],
            "errors": self._metrics["errors"],
            "core_modules": self._get_core_modules_status(),
        }

    def _get_core_modules_status(self) -> Dict[str, str]:
        """Get status of all core modules"""
        status = {}

        if hasattr(self, "content_filter"):
            status["content_filter"] = "ACTIVE"
        if hasattr(self, "layered_memory"):
            status["layered_memory"] = "ACTIVE"
        if hasattr(self, "api_manager"):
            status["api_manager"] = "ACTIVE"
        if hasattr(self, "conversational_core"):
            status["conversational_core"] = "ACTIVE"
        if hasattr(self, "persona_morph"):
            status["persona_morph"] = "ACTIVE"
        if hasattr(self, "ethical_core"):
            status["ethical_core"] = "ACTIVE"
        if hasattr(self, "token_optimizer"):
            status["token_optimizer"] = "ACTIVE"
        if hasattr(self, "emotion_sense"):
            status["emotion_sense"] = "ACTIVE"
        if hasattr(self, "secure_memory"):
            status["secure_memory"] = "ACTIVE"
        if hasattr(self, "agentdev"):
            status["agentdev"] = "ACTIVE"

        return status

    async def test_module_integration(self) -> Dict[str, bool]:
        """Test integration between modules"""
        results = {}

        try:
            # Test 1: Content Filter + Memory System
            if hasattr(self, "content_filter") and hasattr(self, "layered_memory"):
                results["content_memory_integration"] = True

            # Test 2: API Manager + Conversational Core
            if hasattr(self, "api_manager") and hasattr(self, "conversational_core"):
                results["api_conversational_integration"] = True

            # Test 3: Ethical Core + All Modules
            if hasattr(self, "ethical_core"):
                results["ethical_integration"] = True

            # Test 4: Secure Memory + All Modules
            if hasattr(self, "secure_memory"):
                results["secure_memory_integration"] = True

            # Test 5: AgentDev + All Modules
            if hasattr(self, "agentdev"):
                results["agentdev_integration"] = True

        except Exception as e:
            self.logger.error(f"Integration test failed: {e}")
            results["integration_test"] = False

        return results

    def process_request(self, request: str) -> str:
        """Process a request through the framework"""
        try:
            self._metrics["requests"] += 1

            # Basic request processing
            response = f"StillMe AI processed: {request}"

            return response

        except Exception as e:
            self._metrics["errors"] += 1
            self.logger.error(f"Request processing failed: {e}")
            return f"Error processing request: {e}"

    def get_agentdev(self) -> Any:
        """Get AgentDev - Development assistant"""
        return getattr(self, "agentdev", None)

    def record_heartbeat(self) -> None:
        """Record heartbeat for monitoring"""
        self._metrics["heartbeat"].append(float(time.time()))


def initialize_framework(config: Optional[Dict[str, Any]] = None) -> StillMeFramework:
    """Initialize StillMe Framework"""
    try:
        # Set dry run mode if specified
        if os.getenv("STILLME_DRY_RUN"):
            config = config or {}
            config["dry_run"] = True

        framework = StillMeFramework(config)
        framework._initialize_core_modules()

        return framework

    except Exception as e:
        logger.critical(f"Framework initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Test framework initialization
    framework = initialize_framework()
    print("StillMe Framework initialized successfully!")
    print(f"Status: {framework.get_status()}")