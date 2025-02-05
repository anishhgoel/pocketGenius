import os
import logging
import json
import pickle
import time
from typing import Optional, Any
import redis

logger = logging.getLogger(__name__)

class RedisCache:
    """
    A production-ish Redis-based cache to store simple key -> value items with TTL.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl_seconds: int = 900  # 15 minutes by default
    ):
        """
        Initialize RedisCache. Host/port can be read from environment or passed explicitly.
        :param host: Redis host (defaults to REDIS_HOST env).
        :param port: Redis port (defaults to REDIS_PORT env).
        :param db: Redis database index, default 0.
        :param password: Redis password, if needed.
        :param default_ttl_seconds: Default TTL for cached entries.
        """
        if not host:
            host = os.getenv("REDIS_HOST", "localhost")
        if not port:
            port = int(os.getenv("REDIS_PORT", "6379"))
        if not password:
            password = os.getenv("REDIS_PASSWORD", None)

        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            # In real production, you might want connection pooling, timeouts, etc.
        )
        self.default_ttl_seconds = default_ttl_seconds

    def set_json(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        """
        Store a Python dict as JSON in Redis with an optional TTL.
        """
        ttl = ttl if ttl is not None else self.default_ttl_seconds
        try:
            # Convert dict to JSON string
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
        except Exception as e:
            logger.exception(f"Failed to set JSON in Redis for key {key}: {e}")

    def get_json(self, key: str) -> Optional[dict]:
        """
        Retrieve a JSON value from Redis and load it as a Python dict.
        Returns None if key not found or on error.
        """
        try:
            raw_data = self.client.get(key)
            if raw_data:
                return json.loads(raw_data)
        except Exception as e:
            logger.exception(f"Failed to get JSON from Redis for key {key}: {e}")
        return None

    def set_pickle(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store an arbitrary Python object in Redis via pickle with an optional TTL.
        """
        ttl = ttl if ttl is not None else self.default_ttl_seconds
        try:
            pickled = pickle.dumps(value)
            self.client.setex(key, ttl, pickled)
        except Exception as e:
            logger.exception(f"Failed to set pickled data in Redis for key {key}: {e}")

    def get_pickle(self, key: str) -> Any:
        """
        Retrieve a Python object from Redis via pickle.
        Returns None if key not found or on error.
        """
        try:
            raw_data = self.client.get(key)
            if raw_data:
                return pickle.loads(raw_data)
        except Exception as e:
            logger.exception(f"Failed to get pickled data from Redis for key {key}: {e}")
        return None