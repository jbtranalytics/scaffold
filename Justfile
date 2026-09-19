# Root Justfile for scaffold monorepo
set shell := ["bash", "-uc"]

# Submodules
mod uv "justs/uv.just"
mod api "justs/api.just"
mod web "justs/web.just"
mod docker "justs/docker.just"
mod sanity "justs/sanity.just"
mod pc "justs/pc.just"

# Default recipe listing available commands
default:
    @just --list

# Setup dev tools via proto
setup:
    proto use

# Run all sanity checks
check:
    @just sanity all
