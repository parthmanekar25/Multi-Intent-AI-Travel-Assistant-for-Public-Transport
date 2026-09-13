"""In-memory TTL cache helpers."""

from __future__ import annotations

from typing import Any, Callable, Hashable, TypeVar

from cachetools import TTLCache

T = TypeVar("T")

# Shared caches keyed by logical resource name
_caches: dict[str, TTLCache] = {}


def get_cache(name: str, maxsize: int = 256, ttl: int = 60) -> TTLCache:
    cache = _caches.get(name)
    if cache is None or cache.ttl != ttl or cache.maxsize != maxsize:
        cache = TTLCache(maxsize=maxsize, ttl=ttl)
        _caches[name] = cache
    return cache


def cached_call(
    cache_name: str,
    key: Hashable,
    fn: Callable[[], T],
    *,
    ttl: int = 60,
    maxsize: int = 256,
) -> T:
    cache = get_cache(cache_name, maxsize=maxsize, ttl=ttl)
    if key in cache:
        return cache[key]  # type: ignore[return-value]
    value = fn()
    cache[key] = value
    return value


def clear_all_caches() -> None:
    for cache in _caches.values():
        cache.clear()
