# StillMe Gateway - Redis Client
"""
Redis client for caching and session management
"""

import json
import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis

from core.config import Settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper"""

    def __init__(self):
        self.settings = Settings()
        self.redis: Optional[redis.Redis] = None
        self.is_connected = False

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(
                self.settings.REDIS_URL,
                max_connections=self.settings.REDIS_POOL_SIZE,
                decode_responses=True,
            )

            # Test connection
            await self.redis.ping()
            self.is_connected = True
            logger.info("Connected to Redis")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        try:
            if self.redis:
                await self.redis.close()
                self.is_connected = False
                logger.info("Disconnected from Redis")
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set key-value pair"""
        try:
            if not self.is_connected:
                return False

            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)

            result = await self.redis.set(key, value, ex=expire)
            return result is True

        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        try:
            if not self.is_connected:
                return None

            value = await self.redis.get(key)
            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            if not self.is_connected:
                return False

            result = await self.redis.delete(key)
            return result > 0

        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if not self.is_connected:
                return False

            result = await self.redis.exists(key)
            return result > 0

        except Exception as e:
            logger.error(f"Error checking Redis key {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            if not self.is_connected:
                return False

            result = await self.redis.expire(key, seconds)
            return result is True

        except Exception as e:
            logger.error(f"Error setting expiration for Redis key {key}: {e}")
            return False

    async def hset(self, name: str, mapping: Dict[str, Any]) -> bool:
        """Set hash fields"""
        try:
            if not self.is_connected:
                return False

            # Serialize values
            serialized_mapping = {}
            for k, v in mapping.items():
                if not isinstance(v, str):
                    serialized_mapping[k] = json.dumps(v)
                else:
                    serialized_mapping[k] = v

            result = await self.redis.hset(name, mapping=serialized_mapping)
            return result >= 0

        except Exception as e:
            logger.error(f"Error setting Redis hash {name}: {e}")
            return False

    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field value"""
        try:
            if not self.is_connected:
                return None

            value = await self.redis.hget(name, key)
            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            logger.error(f"Error getting Redis hash field {name}.{key}: {e}")
            return None

    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        try:
            if not self.is_connected:
                return {}

            result = await self.redis.hgetall(name)

            # Deserialize values
            deserialized = {}
            for k, v in result.items():
                try:
                    deserialized[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    deserialized[k] = v

            return deserialized

        except Exception as e:
            logger.error(f"Error getting Redis hash {name}: {e}")
            return {}

    async def lpush(self, name: str, *values: Any) -> bool:
        """Push values to list"""
        try:
            if not self.is_connected:
                return False

            # Serialize values
            serialized_values = []
            for value in values:
                if not isinstance(value, str):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(value)

            result = await self.redis.lpush(name, *serialized_values)
            return result > 0

        except Exception as e:
            logger.error(f"Error pushing to Redis list {name}: {e}")
            return False

    async def rpop(self, name: str) -> Optional[Any]:
        """Pop value from list"""
        try:
            if not self.is_connected:
                return None

            value = await self.redis.rpop(name)
            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            logger.error(f"Error popping from Redis list {name}: {e}")
            return None

    async def llen(self, name: str) -> int:
        """Get list length"""
        try:
            if not self.is_connected:
                return 0

            result = await self.redis.llen(name)
            return result

        except Exception as e:
            logger.error(f"Error getting Redis list length {name}: {e}")
            return 0

    async def publish(self, channel: str, message: Any) -> bool:
        """Publish message to channel"""
        try:
            if not self.is_connected:
                return False

            # Serialize message if needed
            if not isinstance(message, str):
                message = json.dumps(message)

            result = await self.redis.publish(channel, message)
            return result > 0

        except Exception as e:
            logger.error(f"Error publishing to Redis channel {channel}: {e}")
            return False

    async def subscribe(self, *channels: str):
        """Subscribe to channels"""
        try:
            if not self.is_connected:
                return None

            pubsub = self.redis.pubsub()
            await pubsub.subscribe(*channels)
            return pubsub

        except Exception as e:
            logger.error(f"Error subscribing to Redis channels {channels}: {e}")
            return None

    # Getters
    def is_healthy(self) -> bool:
        """Check if Redis is healthy"""
        return self.is_connected and self.redis is not None
