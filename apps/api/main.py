import contextlib
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from packages.clients.pool import close_client_pools, open_client_pools
from packages.contracts.rpc import RpcRequest, RpcResponse
from packages.core.result import ok

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Manage application connection pool lifecycles."""
    # Warm up client pools if available/configured
    with contextlib.suppress(Exception):
        await open_client_pools()
    yield
    await close_client_pools()


app = FastAPI(title="Scaffold API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/rpc")
def handle_rpc(req: RpcRequest) -> dict[str, object]:
    """Action-oriented RPC procedure handler."""
    result = ok({"procedure": req.procedure, "handled": True, "echo": req.params})
    response = RpcResponse(ok=result.ok, result=result.data, id=req.id)
    return response.to_dict()
