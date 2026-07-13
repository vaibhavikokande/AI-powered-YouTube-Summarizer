import json
from unittest.mock import AsyncMock, patch

from app.core.cache import cache_get_json, cache_set_json


async def test_cache_get_json_returns_none_when_missing():
    with patch("app.core.cache.get_redis_client") as mock_get_client:
        mock_get_client.return_value.get = AsyncMock(return_value=None)

        result = await cache_get_json("some-key")

    assert result is None


async def test_cache_get_json_returns_parsed_value():
    with patch("app.core.cache.get_redis_client") as mock_get_client:
        mock_get_client.return_value.get = AsyncMock(return_value=json.dumps({"a": 1}))

        result = await cache_get_json("some-key")

    assert result == {"a": 1}


async def test_cache_set_json_stores_serialized_value_with_ttl():
    with patch("app.core.cache.get_redis_client") as mock_get_client:
        mock_set = AsyncMock()
        mock_get_client.return_value.set = mock_set

        await cache_set_json("some-key", {"a": 1}, 60)

    mock_set.assert_called_once_with("some-key", json.dumps({"a": 1}), ex=60)
