#!/usr/bin/env bash
# ==============================================================================
# Ollama Cloud Models Dynamic Pull Script
# ==============================================================================
# Dynamically discovers all available Ollama Cloud models (*-cloud) by
# querying the Ollama library registry web pages concurrently.
# ==============================================================================

set -euo pipefail

# Ensure OLLAMA_HOST points dynamically to WSL host IP if unset or default
if [[ -z "${OLLAMA_HOST:-}" || "$OLLAMA_HOST" == *"127.0.0.1"* || "$OLLAMA_HOST" == *"localhost"* || "$OLLAMA_HOST" == *"host.docker.internal"* ]]; then
    HOST_IP="$(ip route show default 2>/dev/null | awk '{print $3}' || true)"
    if [[ -n "$HOST_IP" ]]; then
        export OLLAMA_HOST="http://${HOST_IP}:11434"
    fi
fi

BOLD="$(tput bold 2>/dev/null || true)"
GREEN="$(tput setaf 2 2>/dev/null || true)"
BLUE="$(tput setaf 4 2>/dev/null || true)"
YELLOW="$(tput setaf 3 2>/dev/null || true)"
RESET="$(tput sgr0 2>/dev/null || true)"

log_warn() {
    echo -e "    ${YELLOW}!${RESET} $1"
}

echo -e "${BOLD}${BLUE}==>${RESET} ${BOLD}Discovering available Ollama Cloud models from registry...${RESET}"

# Fetch library model slugs and query tags in parallel (max 20 jobs)
TMP_TAGS="$(mktemp)"
trap 'rm -f "$TMP_TAGS"' EXIT

curl -s https://ollama.com/library \
  | grep -oE '/library/[a-z0-9.-]+' \
  | cut -d'/' -f3 \
  | sort -u \
  | xargs -P 20 -I {} bash -c 'curl -s "https://ollama.com/library/{}" | grep -oE "/library/[a-z0-9.-]+:[a-z0-9.-]*cloud[a-z0-9.-]*" | cut -d"/" -f3 || true' > "$TMP_TAGS"

CLOUD_MODELS=()
while read -r model_tag; do
    if [[ -n "$model_tag" ]]; then
        CLOUD_MODELS+=("$model_tag")
    fi
done < <(sort -u "$TMP_TAGS")

# Fallback defaults if web search fails
if [[ ${#CLOUD_MODELS[@]} -eq 0 ]]; then
    log_warn "Registry web search returned no cloud tags; using fallback cloud models."
    CLOUD_MODELS=(
        "gpt-oss:20b-cloud"
        "gpt-oss:120b-cloud"
        "gemma4:31b-cloud"
    )
fi

echo -e "${GREEN}Discovered ${#CLOUD_MODELS[@]} cloud models:${RESET}"
for model in "${CLOUD_MODELS[@]}"; do
    echo "  - $model"
done
echo

# Pull each discovered cloud model
for model in "${CLOUD_MODELS[@]}"; do
    echo -e "${BOLD}${GREEN}Pulling ${model}...${RESET}"
    ollama pull "$model" || echo -e "${YELLOW}Failed to pull ${model}, skipping...${RESET}"
    echo
done

echo -e "${BOLD}${GREEN}All cloud models processed!${RESET}"

# Dump updated JSON metadata to assets/ollama_cloud.json
mkdir -p assets
curl -s "${OLLAMA_HOST}/api/tags" | python3 -m json.tool > assets/ollama_cloud.json 2>/dev/null || true
echo -e "Saved model metadata to ${BOLD}assets/ollama_cloud.json${RESET}"

echo -e "\nCurrent available models in Ollama:"
ollama list
