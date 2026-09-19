"""Ollama server and model settings.

Layer 1: Core / Settings.
Pure configuration models backed by pydantic-settings.

Windows Host Configuration (WSL2 Setup):
----------------------------------------
To allow native Ollama on Windows to accept incoming connections from WSL2:
1. Open PowerShell on Windows as Administrator.
2. Set system environment variable for Ollama host binding:
   [System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")
3. Restart the Ollama application in Windows (quit from system tray and re-launch).
4. Verify from WSL2 terminal:
   curl http://$(ip route show default | awk '{print $3}'):11434/api/tags
"""

import os
import socket
from functools import lru_cache

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from packages.core.settings.base import BaseAppSettings

KNOWN_OLLAMA_MODELS: tuple[str, ...] = (
    "gpt-oss:20b-cloud",
    "gpt-oss:120b-cloud",
    "qwen3-next:80b-cloud",
    "lfm2.5:latest",
    "gemma4:31b-cloud",
)


def get_default_ollama_host() -> str:
    """Detect default host URL for Ollama running on Windows host or locally.

    Order of resolution:
    1. OLLAMA_HOST environment variable if set.
    2. Try resolving host.docker.internal.
    3. Read default gateway IP from /etc/resolv.conf (WSL2 host address).
    4. Fallback to http://localhost:11434.
    """
    if env_host := os.environ.get("OLLAMA_HOST"):
        return env_host

    # Try resolving host.docker.internal
    try:
        socket.gethostbyname("host.docker.internal")
        return "http://host.docker.internal:11434"
    except socket.gaierror:
        pass

    # Try reading default gateway route (WSL2 host interface IP)
    try:
        with open("/proc/net/route", encoding="utf-8") as f:
            for line in f:
                fields = line.strip().split()
                if len(fields) >= 3 and fields[1] == "00000000":
                    # Hex IP to dotted string
                    hex_ip = fields[2]
                    ip_bytes = [int(hex_ip[i : i + 2], 16) for i in (6, 4, 2, 0)]
                    host_ip = ".".join(str(b) for b in ip_bytes)
                    return f"http://{host_ip}:11434"
    except Exception:
        pass

    # Fallback to nameserver from /etc/resolv.conf
    try:
        with open("/etc/resolv.conf", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("nameserver"):
                    host_ip = line.split()[1]
                    return f"http://{host_ip}:11434"
    except Exception:
        pass

    return "http://localhost:11434"


class OllamaSettings(BaseAppSettings):
    """Ollama configuration settings with dynamic layered environment variable loading."""

    model_config = SettingsConfigDict(
        env_prefix="OLLAMA_",
        extra="ignore",
    )

    host: str = Field(default_factory=get_default_ollama_host)
    default_model: str = Field(default="gpt-oss:20b-cloud", validation_alias="OLLAMA_DEFAULT_MODEL")
    available_models: tuple[str, ...] = Field(default=KNOWN_OLLAMA_MODELS)
    request_timeout: float = Field(default=120.0, validation_alias="OLLAMA_REQUEST_TIMEOUT")


@lru_cache(maxsize=1)
def get_ollama_settings() -> OllamaSettings:
    """Return default overridable singleton for Ollama settings."""
    return OllamaSettings()
