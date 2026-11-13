"""Talks to the MadPlan server's /api/v1/ha routes."""

from __future__ import annotations

from datetime import date
from typing import Any

import aiohttp


class MadPlanError(Exception):
    """The server could not be reached or gave an unexpected answer."""


class MadPlanAuthError(MadPlanError):
    """The API token was refused."""


class MadPlanClient:
    def __init__(self, session: aiohttp.ClientSession, url: str, token: str) -> None:
        self._session = session
        self._base = f"{url.rstrip('/')}/api/v1/ha"
        self._headers = {"Authorization": f"Bearer {token}"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            async with self._session.request(
                method,
                f"{self._base}{path}",
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=20),
                allow_redirects=False,
                **kwargs,
            ) as response:
                if response.status in (401, 403):
                    raise MadPlanAuthError(f"token refused ({response.status})")
                if response.status >= 300:
                    raise MadPlanError(f"{method} {path} returned {response.status}")
                return await response.json()
        except (aiohttp.ClientError, TimeoutError) as exc:
            raise MadPlanError(str(exc)) from exc

    async def summary(self) -> dict[str, Any]:
        return await self._request("GET", "/summary")

    async def calendar(self, start: date | None = None, end: date | None = None) -> list[dict[str, Any]]:
        params = {}
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        return await self._request("GET", "/calendar", params=params)

    async def shopping(self) -> dict[str, Any]:
        return await self._request("GET", "/shopping")

    async def set_item_checked(self, item_id: int, checked: bool) -> None:
        await self._request("POST", f"/shopping/{item_id}", json={"checked": checked})

    async def add_item(self, name: str) -> None:
        await self._request("POST", "/shopping", json={"name": name})

    async def update_pantry(self, payload: dict[str, Any]) -> None:
        await self._request("POST", "/pantry", json=payload)

    async def vote_meal(self, meal_id: int, vote: str) -> None:
        await self._request("POST", f"/meals/{meal_id}/vote", json={"vote": vote})

    async def send_to_mealie(self) -> dict[str, Any]:
        return await self._request("POST", "/send-to-mealie")

    async def meal_cooked(self, meal_id: int, cooked: bool) -> None:
        await self._request("POST", f"/meals/{meal_id}/cooked", json={"cooked": cooked})
