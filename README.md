# Scaffold Monorepo

Unified **Python 3.14** and **Node.js 26** monorepo template managed with `proto`, `uv`, and `just`.

## Quick Start

### 1. Toolchains
Activate pinned versions via [`proto`](https://moonrepo.dev/proto):
```bash
proto use
```

### 2. Dependencies
Install Python dependencies and pre-commit hooks:
```bash
just uv install
just pc install
```

Install frontend dependencies:
```bash
just web install
```

### 3. Local Services
Spin up Alpine PostgreSQL 18 and Valkey 9:
```bash
just docker up
```

### 4. Development
- **Backend API**: `just api dev` (FastAPI at `http://localhost:8000`)
- **Frontend**: `just web dev` (Next.js at `http://localhost:3000`)
- **Sanity Checks**: `just check` or `just pc all`

For architecture details, layered design rules, and full command references, see [docs/SCAFFOLD.md](file:///home/josht/src/scaffold/docs/SCAFFOLD.md) and [AGENTS.md](file:///home/josht/src/scaffold/AGENTS.md).
