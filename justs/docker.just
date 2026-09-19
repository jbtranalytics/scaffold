# Docker Compose recipes for local alpine services (Postgres & Valkey)
set shell := ["bash", "-uc"]
set working-directory := ".."

ps_format := 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}'

# Default recipe: list docker recipes
default:
    @just --list docker

# Start postgres and valkey services with DOCKER_DATA_DIR mounts
up:
    mkdir -p "${DOCKER_DATA_DIR:-$HOME/.data}/app-data-pg" "${DOCKER_DATA_DIR:-$HOME/.data}/app-data-valkey"
    docker compose up -d

# Stop all docker compose services
down:
    docker compose down

# View status of containers
ps:
    docker compose ps

# Show all running docker containers on the system
ps-system:
    docker ps --format "{{ps_format}}"

# Stream live CPU, memory, and network usage stats
stats:
    docker stats

# Follow logs for all services or a specific service (usage: just docker logs [service])
logs SERVICE="":
    docker compose logs -f {{SERVICE}}

# Restart services (usage: just docker restart [service])
restart SERVICE="":
    docker compose restart {{SERVICE}}

# Open an interactive shell inside a container (usage: just docker exec <container> [cmd])
exec CONTAINER CMD="sh":
    docker exec -it {{CONTAINER}} {{CMD}}

# Stop services and wipe local compose volumes/networks
compose-clean:
    docker compose down -v --remove-orphans

# Stop all running containers system-wide
stop-all:
    @if [ -n "$$(docker ps -q)" ]; then \
        echo "Stopping all active containers..."; \
        docker stop $$(docker ps -q); \
    else \
        echo "No running containers found."; \
    fi

# Prune unused containers, networks, and dangling images (safe: does not touch volumes)
prune:
    docker system prune -f

# Deep cleanup: removes unused containers, networks, and images (preserves volumes)
prune-all:
    docker system prune -a -f

# ------------------------------------------------------------------------------
# NOTE ON DOCKER VOLUMES VS. BIND MOUNTS:
#
# Docker does NOT store volumes inside the container image (images are read-only).
# Instead, storage lives on the host in one of two ways:
#
# 1. Host Bind Mounts (What your scaffold uses):
#    - Syntax: `volumes: - ~/.data/app-data-pg:/var/lib/postgresql/data`
#    - Files live in a normal directory you choose (e.g. `/home/josht/.data/...`).
#    - You can view and edit them directly via standard shell commands (`ls`, `cp`).
#    - NEVER deleted by Docker pruning commands or `docker compose down -v`.
#      The data stays safely on your disk until you manually delete it (`rm -rf`).
#
# 2. Named Volumes (Docker-managed storage):
#    - Syntax: `volumes: - pgdata:/var/lib/postgresql/data`
#    - Files live hidden inside Docker's internal engine storage (/var/lib/docker/volumes/...).
#    - Docker manages their lifecycle completely.
#    - Running `docker volume prune` or `docker system prune --volumes` WILL
#      permanently delete any named volume not currently attached to a RUNNING container.
# ------------------------------------------------------------------------------

# Nuclear cleanup: destroys unused Docker named volumes (prompts for confirmation)
prune-volumes:
    @read -r -p "CAUTION: This will permanently delete all unused Docker named volumes! Proceed? [y/N] " confirm && \
    if [[ "$$confirm" =~ ^[yY] ]]; then \
        docker volume prune -f; \
    else \
        echo "Aborted."; \
    fi
