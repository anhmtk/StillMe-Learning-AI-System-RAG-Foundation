"""StillMe Entry Point"""

import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)

class StillMeEntry:
    """StillMe Entry Point"""
    
    def __init__(self):
        self.logger = logger
        self.initialized = False
        self.logger.info("✅ StillMeEntry initialized")
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize StillMe system"""
        try:
            if self.initialized:
                self.logger.warning("⚠️ StillMe already initialized")
                return True
            
            # Initialize core components
            self._initialize_core_components()
            
            # Initialize learning systems
            self._initialize_learning_systems()
            
            # Initialize security systems
            self._initialize_security_systems()
            
            self.initialized = True
            self.logger.info("✅ StillMe system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize StillMe: {e}")
            return False
    
    def _initialize_core_components(self):
        """Initialize core components"""
        try:
            # Import and initialize core components
            from stillme_core.framework import StillMeFramework
            from stillme_core.router_loader import load_router
            
            # Initialize framework
            self.framework = StillMeFramework()
            
            # Load router
            self.router = load_router()
            
            self.logger.info("✅ Core components initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize core components: {e}")
            raise
    
    def _initialize_learning_systems(self):
        """Initialize learning systems"""
        try:
            # Import learning systems
            from stillme_core.learning import LearningPipeline
            from stillme_core.self_learning import ExperienceMemory
            
            # Initialize learning pipeline
            self.learning_pipeline = LearningPipeline()
            
            # Initialize experience memory
            self.experience_memory = ExperienceMemory()
            
            self.logger.info("✅ Learning systems initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize learning systems: {e}")
            raise
    
    def _initialize_security_systems(self):
        """Initialize security systems"""
        try:
            # Import security systems
            from stillme_core.security import SecurityManager
            from stillme_core.secrecy_filter import SecrecyFilter
            
            # Initialize security manager
            self.security_manager = SecurityManager()
            
            # Initialize secrecy filter
            self.secrecy_filter = SecrecyFilter()
            
            self.logger.info("✅ Security systems initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize security systems: {e}")
            raise
    
    def process_request(self, request: str, context: Dict[str, Any] = None) -> str:
        """Process a request"""
        try:
            if not self.initialized:
                self.logger.error("❌ StillMe not initialized")
                return "Error: System not initialized"
            
            # Choose model using router
            model = self.router.choose_model(request)
            
            # Process request (simplified)
            response = f"Processed request with model: {model}"
            
            self.logger.info(f"✅ Request processed: {model}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process request: {e}")
            return f"Error: {e}"
    
    def shutdown(self):
        """Shutdown StillMe system"""
        try:
            if not self.initialized:
                return
            
            # Cleanup resources
            self.initialized = False
            self.logger.info("✅ StillMe system shutdown")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to shutdown StillMe: {e}")

# Global StillMe instance
_stillme_instance = None

def get_stillme() -> StillMeEntry:
    """Get global StillMe instance"""
    global _stillme_instance
    if _stillme_instance is None:
        _stillme_instance = StillMeEntry()
    return _stillme_instance

def initialize_stillme(config: Dict[str, Any] = None) -> bool:
    """Initialize StillMe system"""
    return get_stillme().initialize(config)

def process_request(request: str, context: Dict[str, Any] = None) -> str:
    """Process a request"""
    return get_stillme().process_request(request, context)

def generate(prompt: str, context: Dict[str, Any] = None) -> str:
    """Generate response for prompt"""
    return get_stillme().process_request(prompt, context)

def shutdown_stillme():
    """Shutdown StillMe system"""
    get_stillme().shutdown()

if __name__ == "__main__":
    # Initialize StillMe
    if initialize_stillme():
        print("✅ StillMe initialized successfully")
        
        # Process a test request
        response = process_request("Hello, StillMe!")
        print(f"Response: {response}")
        
        # Shutdown
        shutdown_stillme()
    else:
        print("❌ Failed to initialize StillMe")
        sys.exit(1)
