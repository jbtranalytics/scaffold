---
name: scaffold-guide
description: Architecture, toolchain, and scaffolding guide for the Node 26 and Python 3.14 monorepo.
---

# Scaffold Monorepo Architecture & Guide

This repository is a unified monorepo supporting **Python 3.14** and **Node.js 26** applications and shared libraries, managed via `proto`, `uv`, and `just`.

---

## Toolchain & Versions (`.prototools`)

Pinned toolchain versions in [`.prototools`](file:///home/josht/src/scaffold/.prototools):
- **Node.js**: `26`
- **Python**: `3.14`
- **uv**: `latest`

Activate toolchains:
```bash
proto use
```

---

## Python Dependency Management (`uv`)

Python dependencies are declared in [`requirements.in`](file:///home/josht/src/scaffold/requirements.in) and compiled into a pinned, reproducible [`requirements.txt`](file:///home/josht/src/scaffold/requirements.txt).

### Justfile Commands

All common tasks are declared in [`Justfile`](file:///home/josht/src/scaffold/Justfile) and modularized in [`justs/uv.just`](file:///home/josht/src/scaffold/justs/uv.just):

| Command | Description |
| :--- | :--- |
| `just check` | Runs all environment and type sanity checks (`just sanity all`) |
| `just uv install` | Syncs Python dependencies via `uv add` and `uv sync` |
| `just uv lock` | Updates `uv.lock` from `pyproject.toml` |
| `just uv upgrade` | Upgrades all locked dependencies (`uv lock --upgrade && uv sync`) |
| `just api dev` | Runs the FastAPI development server with reload on port 8000 |
| `just api start` | Runs the production API server with Gunicorn Uvicorn workers |
| `just web dev` | Runs Next.js frontend dev server (`npm --prefix apps/web run dev`) |
| `just web build` | Builds Next.js frontend (`npm --prefix apps/web run build`) |
| `just web add <c>` | Adds a shadcn component (e.g. `just web add dialog`) |
| `just web add-assistant <c>` | Adds an assistant-ui component (e.g. `just web add-assistant thread`) |
| `just docker up` | Starts local Alpine Postgres and Valkey services (`docker compose up -d`) |
| `just docker down` | Stops local docker services (`docker compose down`) |
| `just docker compose-clean` | Stops docker services and wipes volumes for fresh databases |
| `just docker logs [svc]` | Follows logs for all or a specific service (`just docker logs postgres`) |
| `just docker ps` | Lists running docker container status |
| `just pc fix` | Auto-formats and auto-fixes lint issues with Ruff |
| `just pc all` | Runs all pre-commit hooks against all files |

---

## Repository Structure

```
scaffold/
├── .env                   # Baseline shared environment configuration
├── .env.dev               # Local development environment configuration
├── .env.prod              # Production configuration (strict key parity with .env.dev)
├── .env.local.example     # Local secret overrides reference template
├── .prototools            # Proto toolchain pinning (node 26, python 3.14, uv latest)
├── .python-version        # 3.14
├── Justfile               # Root automation entrypoint
├── docker-compose.yml     # Local services: Alpine Postgres 18 & Alpine Valkey 9
├── pyproject.toml         # Python project specification (PEP 621, uv_build)
├── requirements.in        # Core Python requirements specification
├── requirements.txt       # Compiled requirements from uv
├── apps/
│   ├── api/               # Backend Python service / RPC application (FastAPI: apps/api/main.py)
│   └── web/               # Next.js 16 + Tailwind CSS v4 + shadcn UI + assistant-ui
│       ├── package.json   # Node package definition (all Node deps live here)
│       └── components.json# shadcn registry and theme configuration
├── docs/                  # Architecture & how-to documentation
├── justs/
│   ├── api.just           # FastAPI recipes
│   ├── docker.just        # Docker Compose recipes (Postgres & Valkey)
│   ├── uv.just            # Reusable uv recipes
│   └── web.just           # Next.js, shadcn & assistant-ui recipes
└── packages/              # Shared Python libraries & domain modules
    ├── core/              # Layer 1: Pure domain logic & Result types (zero I/O)
    └── protocols/         # Layer 2: RPC schemas & contracts
```

---

## Local Services (Docker Compose)

[`docker-compose.yml`](file:///home/josht/src/scaffold/docker-compose.yml) spins up:
- **PostgreSQL 18 (Alpine)**: mapped to `localhost:5432` with healthcheck and host bind mount `~/.data/app-data-pg:/var/lib/postgresql/data`.
- **Valkey 9 (Alpine)**: mapped to `localhost:6379` with AOF persistence, healthcheck, and host bind mount `~/.data/app-data-valkey:/data`.

```bash
just docker up           # Start services
just docker logs         # Tail logs
just docker down         # Stop services
just docker compose-clean # Reset databases to a blank slate
```

---

## UI Components & AI Chat (shadcn, assistant-ui & AG-UI)

- **shadcn UI & Lucide**: Configured in [`apps/web/components.json`](file:///home/josht/src/scaffold/apps/web/components.json) using Tailwind CSS v4 and Base UI primitives.
- **assistant-ui**: Pre-scaffolded in `apps/web/components/assistant-ui/` with ready-to-use thread, attachments, tool calls, and reasoning primitives.
- **React Markdown**: [`components/markdown-view.tsx`](file:///home/josht/src/scaffold/apps/web/components/markdown-view.tsx) provides GitHub Flavored Markdown rendering via `react-markdown` + `remark-gfm`.
- **AG-UI Protocol**: Integrated via `@assistant-ui/react`, `@assistant-ui/react-ag-ui`, and `@ag-ui/core` ([`components/ag-ui-demo.tsx`](file:///home/josht/src/scaffold/apps/web/components/ag-ui-demo.tsx)).

To add new UI components to `apps/web`:
```bash
just web-add <component-name>              # shadcn UI
just web-add-assistant <component-name>    # assistant-ui
```
