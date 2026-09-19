"""PostgreSQL client factory and connection pool holder.

Layer 4: Transports, Clients & Adapters.
A logic-free client holding the raw connection pool and a health ping.
"""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from packages.core.settings.postgres import PostgresSettings, get_postgres_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class PostgresClient:
    """Thin connection pool holder around psycopg_pool.AsyncConnectionPool."""

    def __init__(
        self,
        conninfo: str | None = None,
        min_size: int | None = None,
        max_size: int | None = None,
        settings: PostgresSettings | None = None,
    ) -> None:
        effective_settings = settings or get_postgres_settings()
        effective_conninfo = conninfo or effective_settings.url
        effective_min_size = min_size if min_size is not None else effective_settings.min_size
        effective_max_size = max_size if max_size is not None else effective_settings.max_size

        self._conninfo = effective_conninfo
        self._pool = AsyncConnectionPool(
            conninfo=effective_conninfo,
            min_size=effective_min_size,
            max_size=effective_max_size,
            open=False,
            kwargs={"row_factory": dict_row},
        )

    @property
    def pool(self) -> AsyncConnectionPool[Any]:
        """Expose the raw underlying connection pool."""
        return self._pool

    async def open(self) -> None:
        """Open the connection pool."""
        await self._pool.open()

    async def close(self) -> None:
        """Close the connection pool."""
        await self._pool.close()

    async def ping(self) -> bool:
        """Perform a simple ping (SELECT 1) to verify database connectivity."""
        try:
            async with self._pool.connection() as conn, conn.cursor() as cur:
                await cur.execute("SELECT 1")
                res = await cur.fetchone()
                return res is not None
        except Exception:
            return False

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[Any]:
        """Acquire a connection from the pool."""
        async with self._pool.connection() as conn:
            yield conn


def create_postgres_client(
    conninfo: str | None = None,
    settings: PostgresSettings | None = None,
) -> PostgresClient:
    """Create a Postgres client initialized with overridable settings."""
    return PostgresClient(conninfo=conninfo, settings=settings)
