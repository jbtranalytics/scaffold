"""User SQLModel entity and domain repository (Layer 3).

Demonstrates SQLModel entity modeling with Argon2id password hashing and verification.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlmodel import Field, Session, SQLModel

from packages.core.crypto import hash_argon2, verify_argon2
from packages.core.result import Result, err, ok
from packages.stores.base.postgres import PostgresStore

if TYPE_CHECKING:
    from packages.clients.postgres import PostgresClient


class UserModel(SQLModel, table=True):
    """User entity table with Argon2id password hashing."""

    __tablename__: Any = "users"

    id: str = Field(primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    password_hash: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )

    def set_password(self, plain_password: str) -> None:
        """Hash plain password using Argon2id and store it in password_hash."""
        self.password_hash = hash_argon2(plain_password)

    def verify_password(self, candidate_password: str) -> bool:
        """Verify candidate password against stored Argon2id password_hash."""
        return verify_argon2(candidate_password, self.password_hash)


class UserStore:
    """User domain repository orchestrating PostgresStore and UserModel."""

    def __init__(self, client: PostgresClient) -> None:
        self._raw_store = PostgresStore(client)
        self._client = client

    async def init_table(self) -> Result[bool, str]:
        """Ensure users table exists via SQLModel metadata."""
        try:
            async with self._client.connection() as conn:
                with Session(conn) as session:
                    UserModel.metadata.create_all(session.get_bind())
            return ok(True)
        except Exception as e:
            return err(f"Failed to init users table: {e}")

    async def create_user(
        self,
        user_id: str,
        username: str,
        email: str,
        plain_password: str,
    ) -> Result[UserModel, str]:
        """Create and persist a new user with Argon2id hashed password."""
        try:
            user = UserModel(
                id=user_id,
                username=username,
                email=email,
                password_hash="",  # Placeholder set immediately below
            )
            user.set_password(plain_password)

            async with self._client.connection() as conn:
                with Session(conn) as session:
                    session.add(user)
                    session.commit()
                    session.refresh(user)
            return ok(user)
        except Exception as e:
            return err(f"Failed to create user: {e}")

    async def find_by_id(self, user_id: str) -> Result[UserModel | None, str]:
        """Fetch user by ID."""
        try:
            async with self._client.connection() as conn:
                with Session(conn) as session:
                    user = session.get(UserModel, user_id)
            return ok(user)
        except Exception as e:
            return err(f"Failed to find user by id: {e}")

    async def verify_credentials(
        self,
        user_id: str,
        candidate_password: str,
    ) -> Result[bool, str]:
        """Fetch user and verify candidate password against Argon2id hash."""
        user_res = await self.find_by_id(user_id)
        if not user_res.ok:
            return err(user_res.error or "User query failed")
        if user_res.data is None:
            return ok(False)
        return ok(user_res.data.verify_password(candidate_password))
