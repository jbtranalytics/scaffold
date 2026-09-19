"""Valkey client factory and connection holder.

Layer 4: Transports, Clients & Adapters.
A logic-free client holding the raw connection/client and a health ping.
"""

from typing import Any

import valkey.asyncio as valkey_async

from packages.core.settings.valkey import ValkeySettings, get_valkey_settings


class ValkeyClient:
    """Thin connection pool / client holder around valkey.asyncio.Valkey."""

    def __init__(
        self,
        client: Any = None,
        url: str | None = None,
        settings: ValkeySettings | None = None,
    ) -> None:
        if client is not None:
            self._client = client
        else:
            effective_settings = settings or get_valkey_settings()
            effective_url = url or effective_settings.url
            self._client = valkey_async.from_url(effective_url, decode_responses=False)

    @property
    def client(self) -> Any:
        """Expose the raw underlying Valkey client instance."""
        return self._client

    async def open(self) -> None:
        """Open client connection resources if applicable."""

    async def close(self) -> None:
        """Close client connection resources."""
        await self._client.aclose()

    async def ping(self) -> bool:
        """Perform a simple ping to verify Valkey connectivity."""
        try:
            res = await self._client.ping()
            return bool(res)
        except Exception:
            return False


def create_valkey_client(
    url: str | None = None,
    settings: ValkeySettings | None = None,
) -> ValkeyClient:
    """Create a Valkey client initialized with overridable settings."""
    return ValkeyClient(url=url, settings=settings)
