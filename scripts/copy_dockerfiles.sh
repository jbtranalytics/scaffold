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

# Copy and overwrite the Dockerfiles.
cp -f "$SRC_DIR/Dockerfile.public" "$DEST_DIR/Dockerfile.public"
cp -f "$SRC_DIR/Dockerfile.private" "$DEST_DIR/Dockerfile.private"

echo "✅ Dockerfiles have been copied to $DEST_DIR"
