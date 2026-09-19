"""Extended Key-Value storage implementation and model (Layer 3).

Demonstrates extending BaseKVStoreModel with additional relational columns (e.g. metadata_json, tags, owner_id)
leveraging PostgreSQL capabilities beyond raw KV semantics.
"""

from typing import TYPE_CHECKING, Any

from sqlmodel import Field

from packages.stores.base.models import BaseKVStoreModel
from packages.stores.base.postgres import PostgresKVStore

if TYPE_CHECKING:
    from packages.clients.postgres import PostgresClient


class ExtendedKVStoreModel(BaseKVStoreModel, table=True):
    """Extended Key-Value model adding rich relational columns for PostgreSQL."""

    __tablename__: Any = "extended_kv_store"

    owner_id: str | None = Field(default=None, index=True, nullable=True)
    tags: str | None = Field(default=None, index=True, nullable=True)
    metadata_json: str | None = Field(default=None, nullable=True)


class ExtendedKVStore(PostgresKVStore[ExtendedKVStoreModel]):
    """Extended Key-Value & Secret store backed by ExtendedKVStoreModel."""

    def __init__(
        self,
        client: PostgresClient,
        encryption_key: str | bytes | None = None,
        password: str | bytes | None = None,
        auto_encrypt: bool = False,
    ) -> None:
        super().__init__(
            client=client,
            model_cls=ExtendedKVStoreModel,
            encryption_key=encryption_key,
            password=password,
            auto_encrypt=auto_encrypt,
        )
