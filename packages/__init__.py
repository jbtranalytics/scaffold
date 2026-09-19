"""Scaffold application entrypoint and package root."""

from .contracts.rpc import RpcResponse
from .core.result import ok


def main() -> None:
    result = ok("Scaffold monorepo initialized successfully.")
    response = RpcResponse(ok=result.ok, result=result.data)
    print(f"[{response.ok}] {response.result}")


__all__ = ["main"]
