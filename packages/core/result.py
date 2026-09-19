"""Core Result types and pure functional primitives.

Layer 1: Core (zero side effects, zero I/O, zero external dependencies).
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class Ok[T]:
    data: T
    ok: Literal[True] = True
    error: None = None


@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E
    ok: Literal[False] = False
    data: None = None


type Result[T, E] = Ok[T] | Err[E]


def ok[T](data: T) -> Ok[T]:
    """Create a successful Result."""
    return Ok(data=data)


def err[E](error: E) -> Err[E]:
    """Create an error Result."""
    return Err(error=error)
