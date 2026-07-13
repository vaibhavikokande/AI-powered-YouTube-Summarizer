import json
from functools import lru_cache
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


async def cache_get_json(key: str) -> Any | None:
    client = get_redis_client()
    value = await client.get(key)
    return json.loads(value) if value is not None else None


async def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    client = get_redis_client()
    await client.set(key, json.dumps(value), ex=ttl_seconds)
