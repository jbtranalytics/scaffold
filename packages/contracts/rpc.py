"""Protocols and RPC contracts.

Layer 2: Protocols (schemas, procedure definitions, abstract contracts).
Depends solely on Layer 1 (Core).
"""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RpcRequest:
    procedure: str
    params: dict[str, Any]
    id: str | None = None


@dataclass(frozen=True, slots=True)
class RpcResponse:
    ok: bool
    result: Any | None = None
    error: str | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
