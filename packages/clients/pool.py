"""Client singleton pools and lifecycle registry.

Layer 4: Transports, Clients & Adapters.
Manages process-wide lazy singletons for database and cache connections,
with graceful startup and shutdown coordination.
"""

from packages.clients.postgres import PostgresClient, create_postgres_client
from packages.clients.valkey import ValkeyClient, create_valkey_client

# Module-level singletons (lazily initialized)
_VALKEY_CLIENT: ValkeyClient | None = None
_POSTGRES_CLIENT: PostgresClient | None = None


def get_valkey_client(url: str | None = None) -> ValkeyClient:
    """Get or create the process-wide Valkey client singleton."""
    global _VALKEY_CLIENT
    if _VALKEY_CLIENT is None:
        _VALKEY_CLIENT = create_valkey_client(url=url)
    return _VALKEY_CLIENT


def get_postgres_client(conninfo: str | None = None) -> PostgresClient:
    """Get or create the process-wide Postgres client singleton."""
    global _POSTGRES_CLIENT
    if _POSTGRES_CLIENT is None:
        _POSTGRES_CLIENT = create_postgres_client(conninfo=conninfo)
    return _POSTGRES_CLIENT


async def open_client_pools() -> None:
    """Open and warmup connection pools on application startup."""
    pg = get_postgres_client()
    await pg.open()


async def close_client_pools() -> None:
    """Gracefully close all connection pools on application shutdown."""
    global _VALKEY_CLIENT, _POSTGRES_CLIENT

    if _VALKEY_CLIENT is not None:
        await _VALKEY_CLIENT.close()
        _VALKEY_CLIENT = None

    if _POSTGRES_CLIENT is not None:
        await _POSTGRES_CLIENT.close()
        _POSTGRES_CLIENT = None
