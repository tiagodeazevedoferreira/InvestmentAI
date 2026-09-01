from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlencode
from typing import Any


@dataclass
class TradingCentralClient:
    """Read-only Trading Central API adapter.

    Endpoint paths are configurable because provider entitlements/API versions
    can differ by customer. This adapter never places orders.
    """
    base_url: str = ""
    api_token: str | None = None
    timeout: float = 15.0

    @classmethod
    def from_env(cls) -> "TradingCentralClient":
        return cls(
            base_url=os.getenv("TRADING_CENTRAL_API_BASE_URL", "").rstrip("/"),
            api_token=os.getenv("TRADING_CENTRAL_API_TOKEN"),
            timeout=float(os.getenv("TRADING_CENTRAL_TIMEOUT", "15")),
        )

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        if not self.base_url:
            raise RuntimeError("TRADING_CENTRAL_API_BASE_URL is not configured")
        query = "?" + urlencode(params) if params else ""
        req = urllib.request.Request(self.base_url + path + query, method="GET")
        req.add_header("Accept", "application/json")
        if self.api_token:
            req.add_header("Authorization", f"Bearer {self.api_token}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Trading Central HTTP {exc.code}: {body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Trading Central connection error: {exc.reason}") from exc

    def technical_summary(self, **params: str) -> Any:
        return self._get("/technicalsummaries/v3", params)

    def support_resistance(self, **params: str) -> Any:
        return self._get("/supportandresistance/v3", params)

    def instrument_events(self, instrument_id: str, **params: str) -> Any:
        return self._get(f"/instrumentevents/v3/{instrument_id}", params)

    def article_sentiment(self, **params: str) -> Any:
        return self._get("/article-sentiments/v5/entities", params)

    def article_analytics(self, entity: str, **params: str) -> Any:
        return self._get(f"/article-analytics/v4/entities/{entity}", params)

    def latest_articles(self, **params: str) -> Any:
        return self._get("/latest-articles/v4", params)

    def economic_events(self, **params: str) -> Any:
        return self._get("/economicevents/v3", params)

    def anticipated_events(self, instrument_id: str, **params: str) -> Any:
        return self._get(f"/anticipatedevents/v3/{instrument_id}", params)

    def stops(self, **params: str) -> Any:
        return self._get("/stops/v3", params)
