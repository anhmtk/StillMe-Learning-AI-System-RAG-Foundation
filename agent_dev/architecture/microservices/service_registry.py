#!/usr/bin/env python3
"""
StillMe AgentDev - Service Registry
Enterprise-grade service discovery and registration
"""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import aiohttp
import yaml


class ServiceStatus(Enum):
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    STARTING = "STARTING"
    STOPPING = "STOPPING"
    UNKNOWN = "UNKNOWN"

@dataclass
class ServiceInstance:
    """Represents a service instance"""
    service_id: str
    service_name: str
    version: str
    host: str
    port: int
    status: ServiceStatus
    health_check_url: str
    metadata: dict[str, Any]
    registered_at: float
    last_heartbeat: float
    tags: list[str]

@dataclass
class ServiceDefinition:
    """Service definition for registration"""
    name: str
    version: str
    host: str
    port: int
    health_check_path: str = "/health"
    metadata: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None

class ServiceRegistry:
    """Enterprise service registry with health monitoring"""

    def __init__(self, config_path: Optional[str] = None):
        self.services: dict[str, ServiceInstance] = {}
        self.config = self._load_config(config_path)
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)
        self.health_check_timeout = self.config.get('health_check_timeout', 5)
        self.cleanup_interval = self.config.get('cleanup_interval', 60)
        self.running = False

    def _load_config(self, config_path: Optional[str] = None) -> dict[str, Any]:
        """Load service registry configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/service_registry.yaml")

        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        else:
            return {
                'heartbeat_interval': 30,
                'health_check_timeout': 5,
                'cleanup_interval': 60,
                'persistence': {
                    'enabled': True,
                    'file': '.agentdev/services.json'
                }
            }

    async def register_service(self, service_def: ServiceDefinition) -> str:
        """Register a new service instance"""
        service_id = f"{service_def.name}-{service_def.version}-{int(time.time())}"

        instance = ServiceInstance(
            service_id=service_id,
            service_name=service_def.name,
            version=service_def.version,
            host=service_def.host,
            port=service_def.port,
            status=ServiceStatus.STARTING,
            health_check_url=f"http://{service_def.host}:{service_def.port}{service_def.health_check_path}",
            metadata=service_def.metadata or {},
            registered_at=time.time(),
            last_heartbeat=time.time(),
            tags=service_def.tags or []
        )

        self.services[service_id] = instance

        # Start health monitoring
        asyncio.create_task(self._monitor_service_health(instance))

        # Persist to disk
        await self._persist_services()

        print(f"✅ Service registered: {service_id}")
        return service_id

    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service instance"""
        if service_id in self.services:
            instance = self.services[service_id]
            instance.status = ServiceStatus.STOPPING
            del self.services[service_id]
            await self._persist_services()
            print(f"❌ Service deregistered: {service_id}")
            return True
        return False

    async def discover_services(self, service_name: Optional[str] = None,
                              tags: Optional[list[str]] = None) -> list[ServiceInstance]:
        """Discover healthy service instances"""
        healthy_services = []

        for instance in self.services.values():
            if instance.status != ServiceStatus.HEALTHY:
                continue

            if service_name and instance.service_name != service_name:
                continue

            if tags and not any(tag in instance.tags for tag in tags):
                continue

            healthy_services.append(instance)

        return healthy_services

    async def get_service_url(self, service_name: str,
                            version: Optional[str] = None) -> Optional[str]:
        """Get URL for a healthy service instance"""
        services = await self.discover_services(service_name)

        if not services:
            return None

        # Filter by version if specified
        if version:
            services = [s for s in services if s.version == version]

        if not services:
            return None

        # Simple round-robin selection
        selected = services[0]  # TODO: Implement proper load balancing
        return f"http://{selected.host}:{selected.port}"

    async def _monitor_service_health(self, instance: ServiceInstance):
        """Monitor service health with periodic checks"""
        while instance.service_id in self.services:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        instance.health_check_url,
                        timeout=aiohttp.ClientTimeout(total=self.health_check_timeout)
                    ) as response:
                        if response.status == 200:
                            instance.status = ServiceStatus.HEALTHY
                            instance.last_heartbeat = time.time()
                        else:
                            instance.status = ServiceStatus.UNHEALTHY

            except Exception as e:
                instance.status = ServiceStatus.UNHEALTHY
                print(f"⚠️ Health check failed for {instance.service_id}: {e}")

            await asyncio.sleep(self.heartbeat_interval)

    async def _cleanup_stale_services(self):
        """Clean up stale service instances"""
        current_time = time.time()
        stale_threshold = self.heartbeat_interval * 3  # 3x heartbeat interval

        stale_services = []
        for service_id, instance in self.services.items():
            if current_time - instance.last_heartbeat > stale_threshold:
                stale_services.append(service_id)

        for service_id in stale_services:
            await self.deregister_service(service_id)
            print(f"🧹 Cleaned up stale service: {service_id}")

    async def _persist_services(self):
        """Persist service registry to disk"""
        if not self.config.get('persistence', {}).get('enabled', True):
            return

        persistence_file = Path(self.config['persistence']['file'])
        persistence_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to serializable format
        services_data = {}
        for service_id, instance in self.services.items():
            services_data[service_id] = {
                **asdict(instance),
                'status': instance.status.value
            }

        with open(persistence_file, 'w') as f:
            json.dump(services_data, f, indent=2)

    async def _load_persisted_services(self):
        """Load persisted services from disk"""
        persistence_file = Path(self.config['persistence']['file'])

        if not persistence_file.exists():
            return

        try:
            with open(persistence_file) as f:
                services_data = json.load(f)

            for service_id, data in services_data.items():
                instance = ServiceInstance(
                    service_id=data['service_id'],
                    service_name=data['service_name'],
                    version=data['version'],
                    host=data['host'],
                    port=data['port'],
                    status=ServiceStatus(data['status']),
                    health_check_url=data['health_check_url'],
                    metadata=data['metadata'],
                    registered_at=data['registered_at'],
                    last_heartbeat=data['last_heartbeat'],
                    tags=data['tags']
                )
                self.services[service_id] = instance

                # Restart health monitoring
                asyncio.create_task(self._monitor_service_health(instance))

        except Exception as e:
            print(f"⚠️ Failed to load persisted services: {e}")

    async def start(self):
        """Start the service registry"""
        if self.running:
            return

        self.running = True

        # Load persisted services
        await self._load_persisted_services()

        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

        print("🚀 Service Registry started")

    async def stop(self):
        """Stop the service registry"""
        self.running = False
        await self._persist_services()
        print("🛑 Service Registry stopped")

    async def _cleanup_task(self):
        """Background cleanup task"""
        while self.running:
            await asyncio.sleep(self.cleanup_interval)
            await self._cleanup_stale_services()

    def get_registry_status(self) -> dict[str, Any]:
        """Get registry status and statistics"""
        total_services = len(self.services)
        healthy_services = len([s for s in self.services.values()
                              if s.status == ServiceStatus.HEALTHY])

        return {
            'total_services': total_services,
            'healthy_services': healthy_services,
            'unhealthy_services': total_services - healthy_services,
            'uptime': time.time() - (min(s.registered_at for s in self.services.values())
                                   if self.services else time.time()),
            'services': [
                {
                    'service_id': s.service_id,
                    'service_name': s.service_name,
                    'version': s.version,
                    'status': s.status.value,
                    'last_heartbeat': s.last_heartbeat
                }
                for s in self.services.values()
            ]
        }

# Global service registry instance
service_registry = ServiceRegistry()

async def register_agentdev_service(service_name: str, port: int,
                                  metadata: Optional[dict[str, Any]] = None) -> str:
    """Convenience function to register AgentDev service"""
    service_def = ServiceDefinition(
        name=service_name,
        version="1.0.0",
        host="localhost",
        port=port,
        health_check_path="/health",
        metadata=metadata,
        tags=["agentdev", "automation"]
    )

    return await service_registry.register_service(service_def)

async def discover_agentdev_service(service_name: str) -> Optional[str]:
    """Convenience function to discover AgentDev service"""
    return await service_registry.get_service_url(service_name)

if __name__ == "__main__":
    async def main():
        # Example usage
        registry = ServiceRegistry()
        await registry.start()

        # Register a service
        service_def = ServiceDefinition(
            name="agentdev-core",
            version="1.0.0",
            host="localhost",
            port=8080,
            metadata={"capabilities": ["planning", "execution"]}
        )

        service_id = await registry.register_service(service_def)
        print(f"Registered service: {service_id}")

        # Discover services
        services = await registry.discover_services("agentdev-core")
        print(f"Discovered services: {len(services)}")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await registry.stop()

    asyncio.run(main())
