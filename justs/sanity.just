# Sanity check recipes for development toolchains
set shell := ["bash", "-uc"]
set working-directory := ".."

# Default recipe: list sanity checks
default:
    @just --list sanity

# Run Python sanity check (version and executable binary path)
python:
    uv run python -c "import sys; print(f'Python: {sys.version}\nBinary: {sys.executable}')"

# Run Node.js sanity check (version and executable binary path)
node:
    node -e "console.log('Node:  ', process.version); console.log('Binary:', process.execPath)"

# Print working directories (raw shell pwd, justfile directory, and caller directory)
pwd:
    @echo "Shell pwd (default):  $(pwd)"
    @echo "Module directory:     {{justfile_directory()}}"
    @echo "Invocation directory: {{invocation_directory()}}"

# Run typecheck sanity check
types:
    uv run pyright

# Run all sanity checks
all: pwd python node types
