#!/usr/bin/env python3
"""
Desktop App Server Configuration
Cấu hình server cho Desktop App
"""

import json
import os
from typing import Any


class DesktopAppServerConfig:
    """Desktop App Server Configuration Manager"""

    def __init__(self, config_file: str = "config/desktop_app_config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")

        # Default configuration
        return {
            "desktop_app": {"name": "StillMe Desktop", "version": "1.0.0"},
            "server": {
                "base_url": "http://localhost:8000",
                "timeout": 10000,
                "retry_attempts": 3,
                "retry_delay": 1000,
            },
            "endpoints": {
                "health": "/health",
                "version": "/version",
                "livez": "/livez",
                "readyz": "/readyz",
                "inference": "/inference",
            },
        }

    def get_base_url(self) -> str:
        """Get server base URL with fallback priority"""
        # 1. Environment variable
        env_url = os.environ.get("SERVER_BASE_URL")
        if env_url:
            return env_url

        # 2. Runtime config file
        runtime_file = "config/runtime_base_url.txt"
        if os.path.exists(runtime_file):
            try:
                with open(runtime_file, encoding="utf-8-sig") as f:
                    return f.read().strip()
            except Exception:
                pass

        # 3. Config file
        return self.config.get("server", {}).get("base_url", "http://localhost:8000")

    def get_endpoint(self, name: str) -> str:
        """Get full endpoint URL"""
        base_url = self.get_base_url()
        endpoint = self.config.get("endpoints", {}).get(name, f"/{name}")
        return f"{base_url.rstrip('/')}{endpoint}"

    def test_connection(self) -> dict[str, Any]:
        """Test connection to server"""
        import requests

        result = {
            "base_url": self.get_base_url(),
            "status": "unknown",
            "version": None,
            "error": None,
        }

        try:
            # Test /version endpoint
            response = requests.get(
                self.get_endpoint("version"),
                timeout=self.config.get("server", {}).get("timeout", 10000) / 1000,
            )

            if response.status_code == 200:
                result["status"] = "connected"
                result["version"] = response.json()
            else:
                result["status"] = "error"
                result["error"] = f"HTTP {response.status_code}"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def update_base_url(self, new_url: str):
        """Update base URL in config"""
        if "server" not in self.config:
            self.config["server"] = {}

        self.config["server"]["base_url"] = new_url

        # Save to file
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)


# Example usage
if __name__ == "__main__":
    config = DesktopAppServerConfig()

    print("Desktop App Server Configuration")
    print("=" * 40)
    print(f"Base URL: {config.get_base_url()}")
    print(f"Version endpoint: {config.get_endpoint('version')}")
    print(f"Health endpoint: {config.get_endpoint('health')}")

    # Test connection
    print("\nTesting connection...")
    result = config.test_connection()
    print(f"Status: {result['status']}")
    if result["version"]:
        print(
            f"Server: {result['version'].get('name', 'Unknown')} v{result['version'].get('version', 'Unknown')}"
        )
    if result["error"]:
        print(f"Error: {result['error']}")
