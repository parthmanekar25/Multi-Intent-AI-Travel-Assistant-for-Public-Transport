"""Shared LTA DataMall HTTP client with pagination and caching."""

from __future__ import annotations

import logging
from typing import Any

import requests

from singapore_transport.config import get_settings
from singapore_transport.utils import cached_call

logger = logging.getLogger(__name__)


class LTAClient:
    def __init__(self, api_key: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.lta_api_key
        self.timeout = timeout or settings.request_timeout_seconds
        self.base_url = settings.lta_base_url.rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError(
                "LTA_API_KEY is not set. Copy .env.example to .env and add your AccountKey."
            )
        return {"AccountKey": self.api_key, "accept": "application/json"}

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        cache_name: str | None = None,
        cache_key: Any = None,
        ttl: int | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        url = f"{self.base_url}/{path.lstrip('/')}"

        def _fetch() -> dict[str, Any]:
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params or {},
                    timeout=self.timeout,
                )
                if response.status_code != 200:
                    logger.warning(
                        "LTA %s returned %s: %s",
                        path,
                        response.status_code,
                        response.text[:200],
                    )
                    return {
                        "error": f"Status {response.status_code}",
                        "status_code": response.status_code,
                    }
                return response.json()
            except requests.RequestException as exc:
                logger.warning("LTA request failed for %s: %s", path, exc)
                return {"error": str(exc)}

        if cache_name is not None:
            key = cache_key if cache_key is not None else (path, tuple(sorted((params or {}).items())))
            return cached_call(
                cache_name,
                key,
                _fetch,
                ttl=ttl or settings.cache_ttl_seconds,
            )
        return _fetch()

    def get_paginated(
        self,
        path: str,
        *,
        page_size: int = 500,
        max_pages: int = 40,
        cache_name: str | None = None,
        ttl: int | None = None,
    ) -> list[dict[str, Any]]:
        settings = get_settings()

        def _fetch_all() -> list[dict[str, Any]]:
            all_rows: list[dict[str, Any]] = []
            skip = 0
            for _ in range(max_pages):
                data = self.get(path, params={"$skip": skip})
                if "error" in data:
                    break
                rows = data.get("value") or []
                if not rows:
                    break
                all_rows.extend(rows)
                if len(rows) < page_size:
                    break
                skip += page_size
            return all_rows

        if cache_name:
            return cached_call(
                cache_name,
                path,
                _fetch_all,
                ttl=ttl or settings.bus_services_cache_ttl_seconds,
                maxsize=8,
            )
        return _fetch_all()


_default_client: LTAClient | None = None


def get_lta_client() -> LTAClient:
    global _default_client
    if _default_client is None:
        _default_client = LTAClient()
    return _default_client
