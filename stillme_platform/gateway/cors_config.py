# CORS Configuration for StillMe Gateway
"""
Environment-based CORS configuration for security
"""

import os
from typing import List

class CORSConfig:
    """CORS configuration based on environment"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
    def get_allowed_origins(self) -> List[str]:
        """Get allowed origins based on environment"""
        
        if self.environment == "production":
            # Production: Strict CORS
            origins = [
                "https://stillme.ai",
                "https://www.stillme.ai",
                "https://app.stillme.ai"
            ]
            
            # Add custom origins from environment
            custom_origins = os.getenv("ALLOWED_ORIGINS", "")
            if custom_origins:
                origins.extend(custom_origins.split(","))
                
        elif self.environment == "staging":
            # Staging: Moderate CORS
            origins = [
                "https://staging.stillme.ai",
                "https://dev.stillme.ai",
                "http://localhost:3000",
                "http://localhost:8080"
            ]
            
        else:  # development
            # Development: Permissive CORS (with warning)
            origins = [
                "http://localhost:3000",
                "http://localhost:8080", 
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8000"
            ]
            
            # Add custom development origins
            dev_origins = os.getenv("DEV_ALLOWED_ORIGINS", "")
            if dev_origins:
                origins.extend(dev_origins.split(","))
        
        return origins
    
    def get_cors_config(self) -> dict:
        """Get complete CORS configuration"""
        origins = self.get_allowed_origins()
        
        return {
            "allow_origins": origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type", 
                "Authorization", 
                "X-Requested-With",
                "X-Client-ID",
                "X-API-Key"
            ],
            "expose_headers": ["X-Request-ID", "X-Response-Time"],
            "max_age": 3600 if self.environment == "production" else 600
        }
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed"""
        allowed_origins = self.get_allowed_origins()
        
        # In development, allow localhost with any port
        if self.environment == "development" and origin.startswith("http://localhost:"):
            return True
            
        return origin in allowed_origins
    
    def get_security_warning(self) -> str:
        """Get security warning for current configuration"""
        if self.environment == "development":
            return "⚠️ DEVELOPMENT MODE: CORS is permissive. DO NOT use in production!"
        elif self.environment == "staging":
            return "🔶 STAGING MODE: CORS is moderate. Review before production."
        else:
            return "✅ PRODUCTION MODE: CORS is strict and secure."

# Global CORS configuration instance
cors_config = CORSConfig()
