# Global Agent Directives & Permissions

## Tool Execution & Autonomous Workflows
- **Autonomous Execution**: Proactively run terminal commands, package installations, builds, and configuration changes without stopping to ask for manual confirmation.
- **Avoid Friction**: Do not ask the user for permission before running standard commands and scripts needed to complete their request.
- **Fast Execution**: For straightforward tasks and implementation plans, proceed directly to execution without waiting for manual confirmation unless specifically requested by the user.

## Project Scaffolding & Initialization
- **User-Directed Scaffolding**: Do not execute interactive project initialization commands (`uv init`, `npm init`, `cargo init`, `npx create-*`) or hand-roll baseline configuration files from scratch.
- **Guide Options First**: Walk the user through available scaffolding choices, templates, and flags, directing the user to run the init command.
- **Post-Scaffold Tool Automation**: Once the project scaffolding has been generated, take over with autonomous tool calls to configure, edit, and build upon the generated files.
- **Autonomous Dependency Management**: Distinguish between initial project root scaffolding (user-directed) and adding/installing dependencies (`uv add`, `npm install`, `cargo add`), which must always be executed autonomously without prompting.

## Destructive Actions Guard
- Only stop for user review and confirmation if an action is destructive or irreversible, such as:
  - Deleting untracked/uncommitted project files or home directory files (`rm -rf`)
  - Destructive git operations (e.g. `git push --force`, `git reset --hard` discarding uncommitted work)
  - Destroying production or cloud infrastructure

## Language & Runtime Standards
- **Python**: Target **Python 3.14** major version for all new environments, scripts, toolings, and dependencies.
- **Node.js**: Target **Node.js 26** major version for all JavaScript/TypeScript projects, runtimes, and package managers.
- **TypeScript**: Target modern TypeScript (5.8+) with strict type-checking, native Node.js 26 type stripping (`--experimental-strip-types`), `moduleResolution: "NodeNext"`, and prefer discriminated unions over legacy TypeScript `enum`s or `namespace`s.

## Architecture & API Design Patterns
- **Functional Core, Imperative Shell (FCIS)**:
  - **Functional Core**: Write domain logic, business rules, and transformations as pure, deterministic functions free of side effects and I/O. Pure functions return explicit Result types or discriminated unions (`{ ok: true, data } | { ok: false, error }`) rather than throwing side-effect exceptions.
  - **Imperative Shell**: Confine all side effects (database I/O, network requests, filesystem operations, external state) to thin outer shells and controllers that feed data into and handle results from the pure core. Shell controllers catch runtime/network errors and map them to explicit, strongly typed RPC responses.
- **RPC-Style APIs**:
  - Prefer explicit, action-oriented RPC-style endpoints and procedures over dogmatic RESTful CRUD resource mapping.
  - Structure API contracts with clear procedure names, strongly typed inputs, and predictable outputs (command/query style).
- **Leverage Trusted Libraries (Avoid Handrolling)**:
  - Prefer established, battle-tested, and widely adopted libraries rather than reinventing the wheel with hand-rolled solutions.
  - **No Constraint on Existing Dependencies**: The currently installed libraries in an environment are never a limitation when developing features. Proactively add, declare, and install new libraries and tools as needed rather than compromising or hand-rolling.
  - Only hand-roll implementations when strictly necessary (e.g., no suitable library exists, severe constraint requirements, or trivial logic where a dependency is truly excessive).
- **Adapter Pattern for Dependencies**:
  - Wrap third-party libraries, external SDKs, and I/O clients behind Adapter patterns.
  - Keep domain logic insulated from third-party API changes, vendor lock-in, and breaking upstream shifts.
- **Linear, Unidirectional Dependencies (Layered Architecture)**:
  - Enforce a strict one-way dependency flow: higher layers may import from previous/lower layers, but never in reverse.
  - **No Intra-Layer (Peer) Imports**: Packages or modules residing within the same layer must never import from each other. If sibling modules share types or utilities, that shared logic must be extracted down into a lower layer (e.g. Core or Protocols), or orchestrated from an upper layer. This trade-off prioritizes maintainability, strict decoupling, and readability over convenience.
  - **No `__init__.py` Re-exports**: Do not re-export functions, classes, or types in package `__init__.py` files. All call sites must explicitly import from their concrete defining module (e.g. `from packages.core.result import ok` or `from packages.clients.pool import get_valkey_client`). Keep `__init__.py` files empty (or docstring-only) to avoid circular imports, phantom namespaces, and hidden dependency graphs.
  - Strictly prohibit circular dependencies, backward imports, or lower-level modules depending on higher-level consumers.
- **Base Layering (Core & Protocols as Mandatory Foundations)**:
  - **Mandatory Layers (1 & 2)**:
    - **Layer 1: Core (`packages/core/`) [REQUIRED]**: Pure domain models, value types, validation logic, and deterministic transformation functions. Contains zero side effects, zero I/O, and zero external dependencies.
    - **Layer 2: Contracts & Protocols (`packages/contracts/`, `contracts/`, `rpc/`) [REQUIRED]**: Formal RPC procedure definitions, request/response schemas, wire types, abstract interface contracts, and ABCs. Depends solely on Layer 1 (Core).
  - **Recommended Upper Layers (Structure as Needed)**:
    - **Layer 3: Stores & State (`packages/stores/`) [RECOMMENDED]**: Reactive application state, caching, and mutation orchestration coordinating between Core and Transports.
      - `packages/stores/base/`: Generic storage operations (e.g. `PostgresStore`, `ValkeyStore`).
      - `packages/stores/domain/`: Domain-specific stores that inherit/compose base stores and implement domain persistence.
    - **Layer 4: Transports, Adapters & Shell (`apps/api/`, `apps/web/`, `packages/clients/`) [RECOMMENDED]**: Concrete I/O implementations (HTTP/RPC servers, network clients, database drivers, UI views).
  - While upper layers can be tailored or structured based on project scope, **Layer 1 is always Core and Layer 2 is always Protocols**.
- **Maintainability & Readability Over DRY & Optimization**:
  - Optimize for code maintainability, clarity, and readability over dogmatic DRY principles and premature compute/memory optimizations.
  - Prefer explicit, easy-to-follow, and self-contained code over complex indirection, excessive abstractions, or micro-optimized cleverness that obscures intent.
- **Separation of Clients/Transports and Stores**:
  - **Clients & Transports**: Treat network clients, RPC transports, and protocol handlers as thin, logic-free singletons that can be injected or passed around freely. They must contain zero business logic and zero application state.
  - **Stores & State**: Confine application state, reactive data, caching, and domain mutations entirely to dedicated stores. Stores consume clients/transports to fetch or persist data, but transports never manage or retain application state.
- **Settings as Overridable Singletons**:
  - Treat configuration and settings objects as domain-level singletons, but always accept them as optional parameters in functions, classes, and factories.
  - When the settings argument is omitted, automatically fall back to the domain's default singleton (`settings = settings ?? getDefaultDomainSettings()`).
- **Classes as Thin Wrappers Around Functions**:
  - Keep core domain logic, computations, and transformations in standalone, pure functions.
  - When classes are needed for ergonomics, dependency wiring, or lifecycle management, structure them as thin wrappers and delegators around those underlying pure functions.
- **Wire-Ready Data & JSON State Hydration**:
  - All domain models, application state, and transfer objects must be strictly serializable to plain JSON to facilitate transport over the wire, caching, and persistence.
  - Any stateful class must be fully reinstantiable purely from raw JSON state (e.g. via `from_dict`/`to_dict`, `from_json`/`to_json`, or initializers accepting JSON payloads), with zero opaque, non-serializable, or circular in-memory references.

## UI & UX Architecture (Shell & Component Pattern)
Maintain visual and structural consistency across all user interfaces using a framework-agnostic Shell & Component composition model:
- **Macro Layouts via Shells**: Every page or view must inherit from or be wrapped in an explicit Shell layout frame.
- **Component-Driven Composition**: Assemble pages by composing modular, single-responsibility components.
- **Encapsulated Presentation & State Decoupling**: Shells handle layout/chrome; components accept explicit props and emit actions; state and stores handle mutations and data fetching outside UI views.

## Code Modernization & Deprecation Policy
- **Python 3.14 Obsolete & Deprecated Patterns**: No `from __future__ import annotations`, use built-in type syntax (`list[T]`, `X | None`, `type Alias = ...`), no `datetime.utcnow()`, use `pathlib.Path`, no `setup.py` / `requirements.txt` monoliths.
- **Node.js 26 Obsolete & Deprecated Patterns**: No CommonJS in new code; use `node:` protocol prefix for built-ins; no `node-fetch`, `axios`, `uuid`, `dotenv`, `nodemon`. Native `fetch()`, `crypto.randomUUID()`, `node --env-file`, `node --watch`.

## Environment Variables (.env Policy)
- **Hierarchy**: `.env` -> `.env.dev` -> `.env.local`
- **Key Parity**: Strict key parity between `.env.dev` and `.env.prod`.
- **Docker Mounts**: `DOCKER_DATA_DIR` is reserved for Docker host mounts; `DATA_DIR` is for application code.
