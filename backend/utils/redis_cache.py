import os
import logging
import json
import pickle
import time
from typing import Optional, Any
import redis

logger = logging.getLogger(__name__)

class RedisCache:

    def __init__(self, default_ttl_seconds: int = 900):
       
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")  

        try:
            self.client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.default_ttl_seconds = default_ttl_seconds
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.exception(f"Failed to connect to Redis: {e}")
            self.client = None

    def set_json(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
        if not self.client:
            logger.error("Redis connection not available")
            return
        
        ttl = ttl if ttl is not None else self.default_ttl_seconds
        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
        except Exception as e:
            logger.exception(f"Failed to set JSON in Redis for key {key}: {e}")


    def get_json(self, key: str) -> Optional[dict]:
        if not self.client:
            logger.error("Redis connection not available")
            return None

        try:
            raw_data = self.client.get(key)
            if raw_data:
                return json.loads(raw_data)
        except Exception as e:
            logger.exception(f"Failed to get JSON from Redis for key {key}: {e}")
        return None

    def set_pickle(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.client:
            logger.error("Redis connection not available")
            return

        ttl = ttl if ttl is not None else self.default_ttl_seconds
        try:
            pickled = pickle.dumps(value)
            self.client.setex(key, ttl, pickled)
        except Exception as e:
            logger.exception(f"Failed to set pickled data in Redis for key {key}: {e}")

        
    def get_pickle(self, key: str) -> Any:
        if not self.client:
            logger.error("Redis connection not available")
            return None

        try:
            raw_data = self.client.get(key)
            if raw_data:
                return pickle.loads(raw_data)
        except Exception as e:
            logger.exception(f"Failed to get pickled data from Redis for key {key}: {e}")
        return None