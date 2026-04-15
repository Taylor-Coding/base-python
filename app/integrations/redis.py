import json
from typing import Any

import redis

from app.core.config import settings

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    client = get_redis_client()
    client.setex(key, ttl, json.dumps(value))


def cache_get(key: str) -> Any | None:
    client = get_redis_client()
    data = client.get(key)
    if data is None:
        return None
    return json.loads(data)


def cache_delete(key: str) -> None:
    client = get_redis_client()
    client.delete(key)


def cache_exists(key: str) -> bool:
    client = get_redis_client()
    return bool(client.exists(key))
