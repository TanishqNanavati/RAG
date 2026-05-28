import json
import logging
import redis
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RedisSemanticCache:
    """Redis exact-match cache for RAG query payloads with in-memory fallback."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, ttl: int = 3600) -> None:
        self.ttl = ttl
        self.is_connected = False
        self.client = None
        self.in_memory_fallback: Dict[str, str] = {}

        try:
            self.client = redis.Redis(host=host, port=port, db=db, socket_connect_timeout=2)
            # Test connection
            self.client.ping()
            self.is_connected = True
            logger.info("Successfully connected to Redis cache.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Falling back to in-memory cache.")

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached RAG response payload."""
        if self.is_connected and self.client:
            try:
                cached_val = self.client.get(query)
                if cached_val:
                    logger.info(f"Cache HIT (Redis) for query: '{query}'")
                    return json.loads(cached_val)
            except Exception as e:
                logger.error(f"Redis cache retrieve failed: {e}")
        else:
            cached_val = self.in_memory_fallback.get(query)
            if cached_val:
                logger.info(f"Cache HIT (In-Memory Fallback) for query: '{query}'")
                return json.loads(cached_val)
        return None

    def set(self, query: str, response: Dict[str, Any]) -> None:
        """Saves a query response to cache."""
        val_str = json.dumps(response)
        if self.is_connected and self.client:
            try:
                self.client.setex(query, self.ttl, val_str)
                logger.info(f"Cached query response in Redis for {self.ttl}s")
            except Exception as e:
                logger.error(f"Redis cache save failed: {e}")
        else:
            self.in_memory_fallback[query] = val_str
            logger.info("Cached query response in In-Memory Fallback.")
