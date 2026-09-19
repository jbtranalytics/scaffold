# Recipes for apps/api (FastAPI)
set shell := ["bash", "-uc"]
set working-directory := ".."

# Default recipe: list api recipes
default:
    @just --list api
dev:
    uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# Run API production server with gunicorn worker
start:
    uv run gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 apps.api.main:app
