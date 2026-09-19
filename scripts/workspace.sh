#!/usr/bin/env bash
# ==============================================================================
# Repository Workspace Environment Hook
# ==============================================================================
# Sourced by .envrc (or manually) to establish standard directory paths,
# export environment variables, and load the layered .env hierarchy
# (.env -> .env.dev -> .env.local).
#
# Supports forward references: if an expression like ${env:TOKEN} references a
# variable that is not defined yet (e.g. defined in .env but only populated in
# .env.local), it is tracked and automatically resolved in a post-load pass once
# all files are processed.
# ==============================================================================

# Determine the directory of this script, handling symlinks and direct sources
SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd -P -- "$(dirname -- "$SCRIPT_PATH")" && pwd -P)"

# Resolve REPO_DIR as two levels up (parent of scripts/)
REPO_DIR="$(cd -P -- "$SCRIPT_DIR/.." && pwd -P)"
export REPO_DIR

# Define standard workspace directory variables
export APPS_DIR="${REPO_DIR}/apps"
export SRC_DIR="${REPO_DIR}/src"
export CACHE_DIR="${REPO_DIR}/.cache"
export DATA_DIR="${CACHE_DIR}/.data"
export LOGS_DIR="${CACHE_DIR}/.logs"

# Change into repository root
cd "$REPO_DIR" || exit 1

# Registry for variables awaiting resolution
declare -A PENDING_ENV_VARS

# ------------------------------------------------------------------------------
# Resolve Patterns in Environment Variable Values
# Resolves inline patterns such as:
#   - "Bearer ${env:TOKEN}"
#   - "${env:REPO_DIR}/asdf"
#   - "${env:VAR:-fallback}" or "${VAR:-fallback}"
#   - "${VAR}"
# If a referenced variable is not yet defined and has no fallback, the pattern
# is preserved so it can be resolved in a later pass.
# ------------------------------------------------------------------------------
resolve_env_pattern() {
    local val="$1"
    # Match ${env:VAR:-fallback}, ${env:VAR}, ${VAR:-fallback}, or ${VAR}
    while [[ "$val" =~ \$\{((env:)?([a-zA-Z_][a-zA-Z0-9_]*)(:?[-?+=]([^}]*))?)\} ]]; do
        local token="${BASH_REMATCH[0]}"
        local var_name="${BASH_REMATCH[3]}"
        local op_and_arg="${BASH_REMATCH[4]}"

        if [[ -n "${!var_name+x}" ]]; then
            local var_val="${!var_name}"
            if [[ "$op_and_arg" == :-* ]]; then
                local fallback="${op_and_arg#:-}"
                [[ -z "$var_val" ]] && var_val="$fallback"
            elif [[ "$op_and_arg" == -* ]]; then
                local fallback="${op_and_arg#-}"
                [[ -z "${!var_name+x}" ]] && var_val="$fallback"
            fi
            val="${val//"$token"/$var_val}"
        elif [[ "$op_and_arg" == :-* || "$op_and_arg" == -* ]]; then
            # Has an explicit fallback even though var is unset
            local fallback="${op_and_arg#:-}"
            fallback="${fallback#-}"
            val="${val//"$token"/$fallback}"
        else
            # Variable not yet defined; leave token intact for future resolution passes
            break
        fi
    done
    printf '%s' "$val"
}

# ------------------------------------------------------------------------------
# Set Variable and Track Pending Patterns
# ------------------------------------------------------------------------------
set_env_var() {
    local key="$1"
    local raw="$2"
    local resolved
    resolved="$(resolve_env_pattern "$raw")"
    export "$key=$resolved"

    # If unresolved ${env:...} or ${...} remains, track it in PENDING_ENV_VARS
    if [[ "$resolved" =~ \$\{((env:)?([a-zA-Z_][a-zA-Z0-9_]*)) ]]; then
        PENDING_ENV_VARS["$key"]="$resolved"
    else
        unset "PENDING_ENV_VARS[$key]"
    fi
}

# ------------------------------------------------------------------------------
# Resolve All Pending Variables
# Iteratively resolves forward references (e.g. .env referencing .env.local).
# ------------------------------------------------------------------------------
resolve_all_pending() {
    local max_passes=5
    local pass=0
    while [[ ${#PENDING_ENV_VARS[@]} -gt 0 && $pass -lt $max_passes ]]; do
        local progress=0
        for key in "${!PENDING_ENV_VARS[@]}"; do
            local current="${PENDING_ENV_VARS[$key]}"
            local updated
            updated="$(resolve_env_pattern "$current")"
            if [[ "$updated" != "$current" ]]; then
                set_env_var "$key" "$updated"
                progress=1
            fi
        done
        [[ $progress -eq 0 ]] && break
        pass=$((pass + 1))
    done
}

# ------------------------------------------------------------------------------
# Layered Environment Loading (.env -> .env.dev -> .env.local)
# Each layer takes precedence over preceding layers.
# ------------------------------------------------------------------------------
load_env_file() {
    local env_file="$1"
    [[ -f "$env_file" ]] || return 0

    while IFS= read -r line || [[ -n "$line" ]]; do
        # Trim leading and trailing whitespace
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"

        # Skip comments and empty lines
        [[ -z "$line" || "$line" =~ ^# ]] && continue

        # Match key=value (with optional 'export ' prefix)
        if [[ "$line" =~ ^(export[[:space:]]+)?([a-zA-Z_][a-zA-Z0-9_]*)=(.*)$ ]]; then
            local key="${BASH_REMATCH[2]}"
            local val="${BASH_REMATCH[3]}"

            # Strip surrounding double or single quotes if present
            if [[ "$val" =~ ^\"(.*)\"$ ]]; then
                val="${BASH_REMATCH[1]}"
            elif [[ "$val" =~ ^\'(.*)\'$ ]]; then
                val="${BASH_REMATCH[1]}"
            fi

            set_env_var "$key" "$val"
        fi
    done < "$env_file"
}

# Load hierarchy in order
load_env_file "${REPO_DIR}/.env"
load_env_file "${REPO_DIR}/.env.dev"
load_env_file "${REPO_DIR}/.env.local"

# Final post-load pass to resolve forward references (.env -> .env.local)
resolve_all_pending

# ------------------------------------------------------------------------------
# Workspace Loaded Sentinel
# Proves that the workspace script and environment have been successfully sourced.
# ------------------------------------------------------------------------------
export WORKSPACE_LOADED=1
