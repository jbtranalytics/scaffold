# Pre-commit and code quality recipes
set shell := ["bash", "-uc"]
set working-directory := ".."

# Default recipe: display available pre-commit recipes
default:
    @just --list pc

# Install pre-commit git hooks into the repository
install:
    uv run pre-commit install --install-hooks

# Run auto-formatter and auto-fix linter
fix:
    just pc format
    just pc lint-fix

# Run all pre-commit hooks against all files
all:
    uv run pre-commit run --all-files

# Update all pre-commit hooks to their latest versions
autoupdate:
    uv run pre-commit autoupdate

# Lint Python files with Ruff
lint:
    uv run ruff check .

# Fix auto-fixable lint issues with Ruff
lint-fix:
    uv run ruff check --fix .

# Format Python files with Ruff
format:
    uv run ruff format .

# Check Python formatting with Ruff without modifying
format-check:
    uv run ruff format --check .

# Run static type checking with Pyright
typecheck:
    uv run pyright
