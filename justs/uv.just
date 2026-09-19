# uv recipes for python dependency management
set shell := ["bash", "-uc"]
set working-directory := ".."

# Default recipe: display available uv recipes
default:
    @just --list uv

# Add/sync dependencies from requirements.in and requirements-dev.in into pyproject.toml and install
install:
    uv add -r requirements.in
    uv add --dev -r requirements-dev.in
    uv sync

# Install production dependencies only (no dev tools)
install-prod:
    uv add -r requirements.in
    uv sync --no-dev

# Lock dependencies without installing
lock:
    uv lock

# Upgrade all locked dependencies
upgrade:
    uv lock --upgrade && uv sync
