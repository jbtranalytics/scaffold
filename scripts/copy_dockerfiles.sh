#!/usr/bin/env bash
# Copies the Dockerfiles from the private monorepo to the public repository,
# overwriting any existing files.

set -euo pipefail

# Directory containing the source Dockerfiles (relative to this script)
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../images" && pwd)"
DEST_DIR="/home/josht/src/scaffold_public"

# Ensure the destination directory exists.
if [[ ! -d "$DEST_DIR" ]]; then
  echo "Error: Destination directory $DEST_DIR does not exist."
  exit 1
fi

# Ensure destination subdirectory exists for the web package.json
mkdir -p "$DEST_DIR/apps/web"
# Copy package.json (public dependency manifest) – it will be used by the public Docker image to install node modules
cp -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/../apps/web" && pwd)/package.json" "$DEST_DIR/apps/web/package.json"

# Copy Pyproject and uv.lock for Python dependencies
cp -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/pyproject.toml" "$DEST_DIR/pyproject.toml"
cp -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/uv.lock" "$DEST_DIR/uv.lock"


# Copy and overwrite the Dockerfile.public
cp -f "$SRC_DIR/Dockerfile.public" "$DEST_DIR/images/Dockerfile.public"

echo "✅ Dockerfiles and related files have been copied to $DEST_DIR"
