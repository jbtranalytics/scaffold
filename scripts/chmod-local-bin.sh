#!/usr/bin/env bash
# ==============================================================================
# Fix / Ensure Executable Permissions on ~/.local/bin
# ==============================================================================
# Idempotently makes all files within $HOME/.local/bin executable (chmod +x).
#
# NOTE:
#   This script is included in the scaffold repository strictly for convenience
#   when setting up a brand-new WSL2 development machine. Once run to provision
#   the environment, it is not required by the project and can be safely deleted.
# ==============================================================================

set -euo pipefail

TARGET_DIR="${HOME}/.local/bin"

if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Directory $TARGET_DIR does not exist. Creating..."
    mkdir -p "$TARGET_DIR"
fi

echo "Ensuring executable permissions on all files in $TARGET_DIR..."

COUNT=0
# Loop through all regular files (excluding hidden directories if any)
while IFS= read -r -d '' file; do
    if [[ -f "$file" ]]; then
        chmod +x "$file"
        echo "  ✓ $(basename "$file") -> executable"
        COUNT=$((COUNT + 1))
    fi
done < <(find "$TARGET_DIR" -maxdepth 1 -type f -print0)

if [[ $COUNT -eq 0 ]]; then
    echo "No files found in $TARGET_DIR."
else
    echo "Successfully updated permissions for $COUNT file(s)."
fi
