"""Environment loading, resolution, and .env hierarchy management.

Layer 1: Core (env parsing, ${env:VAR} pattern expansion, WSL2 host resolution).

Provides:
- get_wsl_host_ip(): Resolves Windows host IP when running inside WSL2.
- resolve_env_files(): Resolves layered .env file order based on APP_ENV/ENVIRONMENT.
- expand_env_patterns(): Expands ${env:VAR}, ${VAR:-fallback}, and $VAR expressions in environment variable values.
- load_workspace_env(): Loads layered .env files into os.environ with multi-pass pattern resolution.
"""

import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path

# Match ${env:VAR:-fallback}, ${env:VAR}, ${VAR:-fallback}, ${VAR}, or $VAR
_ENV_PATTERN_REGEX = re.compile(r"\$\{?(?:env:)?([a-zA-Z_][a-zA-Z0-9_]*)(?::?[-?+=]([^}]*))?\}?")


@lru_cache(maxsize=1)
def get_wsl_host_ip() -> str | None:
    """Return the Windows host IP address when running inside WSL2, or None if not WSL2."""
    if not Path("/proc/version").is_file():
        return None
    try:
        proc_ver = Path("/proc/version").read_text(encoding="utf-8").lower()
        if "wsl2" not in proc_ver and "microsoft" not in proc_ver:
            return None

        # Check default gateway IP (Windows host in WSL2)
        res = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout:
            parts = res.stdout.split()
            if len(parts) >= 3 and parts[0] == "default":
                return parts[2]
    except Exception:
        pass
    return None


def resolve_host(host: str) -> str:
    """Resolve 'localhost', 'host.docker.internal', or fallback for WSL2 host daemons."""
    if host.lower() in ("localhost", "127.0.0.1", "host.docker.internal"):
        wsl_ip = get_wsl_host_ip()
        if wsl_ip and os.getenv("WSL_FORCE_HOST_IP", "0") == "1":
            return wsl_ip
    return host


def resolve_env_files() -> tuple[str, ...]:
    """Determine the layered .env file sequence based on APP_ENV or ENVIRONMENT."""
    env = (os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or "dev").lower()
    if env.startswith("dev"):
        return (".env", ".env.dev", ".env.local")
    return (".env", ".env.prod", ".env.local")


def expand_env_value(val: str, env_dict: dict[str, str] | None = None) -> str:
    """Expand ${env:VAR:-fallback}, ${VAR}, and $VAR patterns in a string value."""
    lookup = env_dict if env_dict is not None else dict(os.environ)

    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        fallback = match.group(2)

        if var_name in lookup:
            return lookup[var_name]
        if fallback is not None:
            clean_fallback = fallback.lstrip(":-")
            return clean_fallback
        return match.group(0)

    current = val
    for _ in range(5):
        updated = _ENV_PATTERN_REGEX.sub(_replace, current)
        if updated == current:
            break
        current = updated

    return current


def load_workspace_env(base_dir: str | Path | None = None) -> dict[str, str]:
    """Load layered .env files into os.environ with multi-pass variable resolution.

    Matching the behavior of scripts/workspace.sh.
    """
    root_dir = Path(base_dir or Path.cwd()).resolve()
    env_files = resolve_env_files()

    loaded_vars: dict[str, str] = {}

    for env_filename in env_files:
        env_path = root_dir / env_filename
        if not env_path.is_file():
            continue

        with env_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("export "):
                    line = line[7:].strip()

                if "=" not in line:
                    continue

                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()

                if (val.startswith('"') and val.endswith('"')) or (
                    val.startswith("'") and val.endswith("'")
                ):
                    val = val[1:-1]

                loaded_vars[key] = val

    resolved_env: dict[str, str] = dict(os.environ)
    resolved_env.update(loaded_vars)

    for _ in range(5):
        changed = False
        for k, v in list(loaded_vars.items()):
            expanded = expand_env_value(v, resolved_env)
            if expanded != v:
                loaded_vars[k] = expanded
                resolved_env[k] = expanded
                changed = True
        if not changed:
            break

    for k, v in loaded_vars.items():
        os.environ[k] = v

    # Expose resolved WSL_HOST_IP if running inside WSL2
    wsl_ip = get_wsl_host_ip()
    if wsl_ip:
        os.environ.setdefault("WSL_HOST_IP", wsl_ip)

    return loaded_vars
