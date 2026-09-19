#!/usr/bin/env bash
# ==============================================================================
# WSL2 Ubuntu Environment Bootstrap Script
# ==============================================================================
# Sets up a complete developer workstation in WSL2 Ubuntu idempotently:
#   1. System packages & build dependencies (apt)
#   2. WSL configuration (/etc/wsl.conf for systemd & default user)
#   3. Zsh shell & default shell configuration
#   4. Homebrew (Linuxbrew) & environment integration
#   5. Homebrew packages (CLI utilities, runtimes, tooling)
#   6. Rust / Cargo tools (just-lsp)
#   7. Oh My Zsh & custom plugins (autosuggestions, syntax-highlighting)
#   8. Starship prompt theme configuration (~/.config/starship.toml)
#   9. Custom CLI helpers (~/.local/bin/ag, ~/.local/bin/xdg-open)
#  10. GitHub CLI credential helper configuration for Git
#  11. Managed ~/.zshenv, ~/.zshrc, and workspace hook
#
# Files Created / Managed by this script:
#   - ~/.zshenv                        (Environment variables & PATH ordering)
#   - ~/.zshrc                         (Interactive shell, aliases & tool hooks)
#   - ~/.config/starship.toml          (Starship prompt theme configuration)
#   - ~/.local/bin/ag                  (Antigravity IDE launcher wrapper)
#   - ~/.local/bin/xdg-open            (Windows browser/app opener bridge)
#   - ~/.docker/config.json            (Docker CLI plugins directory configuration)
#   - ~/scripts/workspace.sh           (Default startup project workspace hook)
#   - /etc/wsl.conf                    (WSL systemd & default user configuration)
#   - ~/.gitconfig                     (GitHub credential helper entries)
#
# NOTE:
#   This script is included in the scaffold repository strictly for convenience
#   when setting up a brand-new WSL2 development machine. Once run to provision
#   the environment, it is not required by the project and can be safely deleted.
# ==============================================================================

set -euo pipefail

# ANSI color output
BOLD="$(tput bold 2>/dev/null || true)"
GREEN="$(tput setaf 2 2>/dev/null || true)"
BLUE="$(tput setaf 4 2>/dev/null || true)"
YELLOW="$(tput setaf 3 2>/dev/null || true)"
RED="$(tput setaf 1 2>/dev/null || true)"
RESET="$(tput sgr0 2>/dev/null || true)"

log_step() {
    echo -e "\n${BOLD}${BLUE}==>${RESET} ${BOLD}$1${RESET}"
}

log_info() {
    echo -e "    ${GREEN}✓${RESET} $1"
}

log_warn() {
    echo -e "    ${YELLOW}!${RESET} $1"
}

log_error() {
    echo -e "    ${RED}✗${RESET} $1" >&2
}

# ------------------------------------------------------------------------------
# User Git Identity Setup (Prompted at start)
# ------------------------------------------------------------------------------
GIT_USER_NAME=""
GIT_USER_EMAIL=""

prompt_user_identity() {
    local current_name
    local current_email
    current_name="$(git config --global user.name 2>/dev/null || true)"
    current_email="$(git config --global user.email 2>/dev/null || true)"

    # If both user.name and user.email are already configured, skip prompting entirely
    if [[ -n "$current_name" && -n "$current_email" ]]; then
        log_info "Git identity already configured: $current_name <$current_email>"
        return 0
    fi

    echo -e "\n${BOLD}${BLUE}==>${RESET} ${BOLD}Git User Identity Setup${RESET}"

    # Only prompt if stdin is a terminal, otherwise keep existing or env vars
    if [[ -t 0 ]]; then
        if [[ -n "$current_name" ]]; then
            GIT_USER_NAME="$current_name"
        else
            read -r -p "Enter your Git user name: " GIT_USER_NAME
        fi

        if [[ -n "$current_email" ]]; then
            GIT_USER_EMAIL="$current_email"
        else
            read -r -p "Enter your Git email address: " GIT_USER_EMAIL
        fi
    else
        GIT_USER_NAME="${GIT_AUTHOR_NAME:-${current_name:-}}"
        GIT_USER_EMAIL="${GIT_AUTHOR_EMAIL:-${current_email:-}}"
    fi

    if [[ -n "$GIT_USER_NAME" ]]; then
        git config --global user.name "$GIT_USER_NAME"
        log_info "Git user.name set to: $GIT_USER_NAME"
    fi
    if [[ -n "$GIT_USER_EMAIL" ]]; then
        git config --global user.email "$GIT_USER_EMAIL"
        log_info "Git user.email set to: $GIT_USER_EMAIL"
    fi
}

# ------------------------------------------------------------------------------
# 1. Base System Prerequisites (apt)
# ------------------------------------------------------------------------------
install_system_packages() {
    log_step "Checking base system packages (apt)..."
    local REQUIRED_PACKAGES=(
        build-essential
        procps
        curl
        file
        git
        zsh
        ca-certificates
    )

    local MISSING_PACKAGES=()
    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            MISSING_PACKAGES+=("$pkg")
        fi
    done

    if [[ ${#MISSING_PACKAGES[@]} -gt 0 ]]; then
        log_info "Installing missing apt packages: ${MISSING_PACKAGES[*]}..."
        sudo apt-get update -y
        sudo apt-get upgrade -y
        sudo apt-get install -y "${MISSING_PACKAGES[@]}"
    else
        log_info "All base system packages are already installed."
    fi
}

# ------------------------------------------------------------------------------
# 2. WSL Configuration (/etc/wsl.conf)
# ------------------------------------------------------------------------------
configure_wsl() {
    log_step "Checking /etc/wsl.conf configuration..."
    local changed=0
    local target_user="${SUDO_USER:-$USER}"

    if [[ ! -f /etc/wsl.conf ]]; then
        log_info "Creating /etc/wsl.conf with systemd=true and default user..."
        sudo bash -c "cat <<EOF > /etc/wsl.conf
[boot]
systemd=true

[user]
default=${target_user}
EOF"
    else
        if ! grep -q "systemd=true" /etc/wsl.conf 2>/dev/null; then
            sudo bash -c "echo -e '\n[boot]\nsystemd=true' >> /etc/wsl.conf"
            changed=1
        fi
        if ! grep -q "default=" /etc/wsl.conf 2>/dev/null; then
            sudo bash -c "echo -e '\n[user]\ndefault=${target_user}' >> /etc/wsl.conf"
            changed=1
        fi
        if [[ $changed -eq 0 ]]; then
            log_info "/etc/wsl.conf already properly configured."
        else
            log_info "/etc/wsl.conf updated."
        fi
    fi
}

# ------------------------------------------------------------------------------
# 3. Set Default Shell to Zsh
# ------------------------------------------------------------------------------
configure_default_shell() {
    log_step "Checking default login shell..."
    local zsh_path
    zsh_path="$(command -v zsh || which zsh)"

    if [[ "$SHELL" != "$zsh_path" ]]; then
        if ! grep -q "^$zsh_path$" /etc/shells; then
            echo "$zsh_path" | sudo tee -a /etc/shells >/dev/null
        fi
        sudo chsh -s "$zsh_path" "$USER"
        log_info "Default shell set to $zsh_path (takes effect on next login)."
    else
        log_info "Default shell is already $zsh_path."
    fi
}

# ------------------------------------------------------------------------------
# 4. Homebrew Installation & Activation
# ------------------------------------------------------------------------------
install_homebrew() {
    log_step "Checking Homebrew installation..."
    if ! command -v brew >/dev/null 2>&1 && [[ ! -d "/home/linuxbrew/.linuxbrew" ]]; then
        log_info "Installing Homebrew non-interactively..."
        NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        log_info "Homebrew is already installed."
    fi

    # Activate Homebrew in current running bash script session
    if [[ -d "/home/linuxbrew/.linuxbrew" ]]; then
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    elif [[ -d "$HOME/.linuxbrew" ]]; then
        eval "$("$HOME/.linuxbrew/bin/brew" shellenv)"
    fi
}

# ------------------------------------------------------------------------------
# 5. Homebrew Formulas & Toolchain Packages
# ------------------------------------------------------------------------------
install_brew_packages() {
    log_step "Checking Homebrew packages..."

    local BREW_PACKAGES=(
        bat
        btop
        direnv
        docker
        docker-buildx
        docker-compose
        duckdb
        eza
        fnm
        fzf
        gh
        jq
        just
        make
        node
        pre-commit
        proto
        ripgrep
        rust
        shellcheck
        starship
        uv
        zoxide
    )

    local TO_INSTALL=()
    for pkg in "${BREW_PACKAGES[@]}"; do
        if ! brew list "$pkg" >/dev/null 2>&1; then
            TO_INSTALL+=("$pkg")
        fi
    done

    if [[ ${#TO_INSTALL[@]} -gt 0 ]]; then
        log_info "Installing missing Homebrew formulas: ${TO_INSTALL[*]}..."
        brew install "${TO_INSTALL[@]}"
    else
        log_info "All required Homebrew packages are already installed."
    fi
}

# ------------------------------------------------------------------------------
# 6. Rust / Cargo Tools
# ------------------------------------------------------------------------------
install_cargo_tools() {
    log_step "Checking Cargo packages..."
    if command -v cargo >/dev/null 2>&1; then
        if ! command -v just-lsp >/dev/null 2>&1 && [[ ! -f "$HOME/.cargo/bin/just-lsp" ]]; then
            log_info "Installing just-lsp via cargo..."
            cargo install just-lsp
        else
            log_info "just-lsp is already installed."
        fi
    else
        log_warn "Cargo not found in path; skipping cargo packages."
    fi
}

# ------------------------------------------------------------------------------
# 7. Oh My Zsh & Custom Plugins
# ------------------------------------------------------------------------------
setup_oh_my_zsh() {
    log_step "Checking Oh My Zsh and plugins..."

    local omz_dir="$HOME/.oh-my-zsh"
    if [[ ! -d "$omz_dir" ]]; then
        log_info "Installing Oh My Zsh non-interactively..."
        RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c \
            "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
    else
        log_info "Oh My Zsh is already installed."
    fi

    local custom_plugins_dir="${ZSH_CUSTOM:-$omz_dir/custom}/plugins"
    mkdir -p "$custom_plugins_dir"

    # zsh-autosuggestions
    if [[ ! -d "$custom_plugins_dir/zsh-autosuggestions" ]]; then
        log_info "Cloning zsh-autosuggestions plugin..."
        git clone https://github.com/zsh-users/zsh-autosuggestions "$custom_plugins_dir/zsh-autosuggestions"
    else
        log_info "zsh-autosuggestions plugin already installed."
    fi

    # zsh-syntax-highlighting
    if [[ ! -d "$custom_plugins_dir/zsh-syntax-highlighting" ]]; then
        log_info "Cloning zsh-syntax-highlighting plugin..."
        git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$custom_plugins_dir/zsh-syntax-highlighting"
    else
        log_info "zsh-syntax-highlighting plugin already installed."
    fi
}

# ------------------------------------------------------------------------------
# 8. Starship Configuration (~/.config/starship.toml)
# ------------------------------------------------------------------------------
configure_starship() {
    log_step "Checking Starship prompt configuration..."
    local config_dir="$HOME/.config"
    mkdir -p "$config_dir"

    cat <<'EOF' > "$config_dir/starship.toml"
# ~/.config/starship.toml
# Starship prompt configuration

command_timeout = 1000
add_newline = true

format = """
$directory\
$git_branch\
$git_status\
$package\
$nodejs\
$python\
$rust\
$golang\
$docker_context\
$fill\
$cmd_duration\
$line_break\
$character"""

[fill]
symbol = " "

[character]
success_symbol = "[❯](bold green)"
error_symbol = "[❯](bold red)"
vimcmd_symbol = "[❮](bold yellow)"

[directory]
truncation_length = 4
truncate_to_repo = true
style = "bold cyan"
read_only = " 󰌾"

[git_branch]
symbol = " "
style = "bold purple"
format = "[$symbol$branch]($style) "

[git_status]
style = "bold red"
format = '([\[$all_status$ahead_behind\]]($style) )'

[cmd_duration]
min_time = 2_000
style = "bold yellow"
format = "took [$duration]($style) "

[nodejs]
symbol = " "
style = "bold green"
format = "via [$symbol($version )]($style)"

[python]
symbol = " "
style = "bold yellow"
format = 'via [${symbol}${pyenv_prefix}(${version} )(\($virtualenv\) )]($style)'

[rust]
symbol = "󱘗 "
style = "bold red"
format = "via [$symbol($version )]($style)"

[golang]
symbol = " "
style = "bold cyan"
format = "via [$symbol($version )]($style)"

[docker_context]
symbol = " "
style = "bold blue"
format = "via [$symbol$context]($style) "

[package]
disabled = true
EOF
    log_info "Configured ~/.config/starship.toml"
}

# ------------------------------------------------------------------------------
# 9. Local CLI Helper Binaries (~/.local/bin)
# ------------------------------------------------------------------------------
configure_local_binaries() {
    log_step "Configuring ~/.local/bin helper utilities..."
    mkdir -p "$HOME/.local/bin"

    # 1. Antigravity IDE launcher wrapper (ag / agy)
    cat <<'EOF' > "$HOME/.local/bin/ag"
#!/usr/bin/env bash
#
# ag: CLI helper to open files or directories in Antigravity IDE (similar to `code`)
#

set -e

# 1. Locate the antigravity-ide binary
CLI=""
if command -v antigravity-ide >/dev/null 2>&1; then
    CLI="$(command -v antigravity-ide)"
elif command -v agy-ide >/dev/null 2>&1; then
    CLI="$(command -v agy-ide)"
else
    # Find the remote-cli installed by Antigravity IDE server
    CLI=$(find "$HOME/.antigravity-ide-server/bin" -maxdepth 4 -name "antigravity-ide" -type f 2>/dev/null | sort -V | tail -n 1)
fi

# 2. Discover active VSCODE_IPC_HOOK_CLI if unset or broken
if [ -z "$VSCODE_IPC_HOOK_CLI" ] || [ ! -S "$VSCODE_IPC_HOOK_CLI" ]; then
    LATEST_SOCK=$(ls -t /run/user/${UID:-1000}/vscode-ipc-*.sock /tmp/vscode-ipc-*.sock 2>/dev/null | head -n 1)
    if [ -n "$LATEST_SOCK" ] && [ -S "$LATEST_SOCK" ]; then
        export VSCODE_IPC_HOOK_CLI="$LATEST_SOCK"
    fi
fi

# 3. If remote-cli is found and active IPC socket exists, use it directly
if [ -n "$CLI" ] && [ -x "$CLI" ] && [ -n "$VSCODE_IPC_HOOK_CLI" ]; then
    if [ $# -eq 0 ]; then
        exec "$CLI" "."
    else
        exec "$CLI" "$@"
    fi
fi

# 4. Fallback: Launch via Windows Antigravity IDE executable if closed/detached
WIN_EXE="/mnt/c/Users/josht/AppData/Local/Programs/Antigravity IDE/Antigravity IDE.exe"
if [ -f "$WIN_EXE" ]; then
    DISTRO="${WSL_DISTRO_NAME:-Ubuntu}"
    TARGET_ARGS=()

    if [ $# -eq 0 ]; then
        TARGET_ARGS+=("$(pwd)")
    else
        for arg in "$@"; do
            if [ -e "$arg" ]; then
                TARGET_ARGS+=("$(realpath "$arg")")
            else
                TARGET_ARGS+=("$arg")
            fi
        done
    fi

    POWERSHELL_CMD="Start-Process 'C:\Users\josht\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe' -ArgumentList '--remote', 'wsl+${DISTRO}'"
    for target in "${TARGET_ARGS[@]}"; do
        POWERSHELL_CMD+=", '$target'"
    done

    powershell.exe -NoProfile -Command "$POWERSHELL_CMD" >/dev/null 2>&1
    exit 0
fi

# 5. Fallback: run CLI directly if found
if [ -n "$CLI" ] && [ -x "$CLI" ]; then
    if [ $# -eq 0 ]; then
        exec "$CLI" "."
    else
        exec "$CLI" "$@"
    fi
fi

echo "Error: Antigravity IDE executable could not be found." >&2
exit 1
EOF
    chmod +x "$HOME/.local/bin/ag"

    # 2. xdg-open wrapper to open links/files in Windows browser/apps from WSL
    cat <<'EOF' > "$HOME/.local/bin/xdg-open"
#!/usr/bin/env bash
#
# xdg-open wrapper for WSL to open URLs or files with the default Windows handler
#
if [ -z "$1" ]; then
    echo "Usage: xdg-open <url|file>" >&2
    exit 1
fi

TARGET="$1"

if [[ "$TARGET" =~ ^https?:// ]] || [[ "$TARGET" =~ ^mailto: ]]; then
    powershell.exe -NoProfile -Command "Start-Process '$TARGET'" >/dev/null 2>&1
elif [ -e "$TARGET" ]; then
    WIN_PATH=$(wslpath -w "$TARGET" 2>/dev/null || echo "$TARGET")
    powershell.exe -NoProfile -Command "Start-Process '$WIN_PATH'" >/dev/null 2>&1
else
    powershell.exe -NoProfile -Command "Start-Process '$TARGET'" >/dev/null 2>&1
fi
EOF
    chmod +x "$HOME/.local/bin/xdg-open"

    log_info "Installed ~/.local/bin/ag and ~/.local/bin/xdg-open"
}

# ------------------------------------------------------------------------------
# 10. Docker CLI Plugins Configuration (~/.docker/config.json)
# ------------------------------------------------------------------------------
configure_docker() {
    log_step "Configuring Docker CLI plugins..."
    mkdir -p "$HOME/.docker"

    cat <<'EOF' > "$HOME/.docker/config.json"
{
  "cliPluginsExtraDirs": [
    "/home/linuxbrew/.linuxbrew/lib/docker/cli-plugins"
  ]
}
EOF
    log_info "Configured ~/.docker/config.json (enabled docker compose & buildx plugins)"

    # Add user to docker group if the group exists
    if getent group docker >/dev/null 2>&1; then
        sudo usermod -aG docker "$USER" 2>/dev/null || true
    fi
}

# ------------------------------------------------------------------------------
# 10. Git Credentials Configuration
# ------------------------------------------------------------------------------
configure_git() {
    log_step "Configuring Git credential helper..."
    local gh_bin="/home/linuxbrew/.linuxbrew/bin/gh"
    if [[ ! -x "$gh_bin" ]]; then
        gh_bin="$(command -v gh 2>/dev/null || true)"
    fi

    if [[ -n "$gh_bin" ]]; then
        # Safely replace existing helpers without erroring on duplicates
        git config --global --unset-all credential."https://github.com".helper 2>/dev/null || true
        git config --global --unset-all credential."https://gist.github.com".helper 2>/dev/null || true
        git config --global credential."https://github.com".helper ""
        git config --global --add credential."https://github.com".helper "!$gh_bin auth git-credential"
        git config --global credential."https://gist.github.com".helper ""
        git config --global --add credential."https://gist.github.com".helper "!$gh_bin auth git-credential"
        log_info "Configured GitHub credential helper using $gh_bin"
    else
        log_warn "gh CLI not found; skipping GitHub credential helper config."
    fi
}

# ------------------------------------------------------------------------------
# 11. Write Shell Dotfiles (~/.zshenv, ~/.zshrc, ~/scripts/workspace.sh)
# ------------------------------------------------------------------------------
write_dotfiles() {
    log_step "Writing shell dotfiles (~/.zshenv, ~/.zshrc, scripts)..."

    mkdir -p "$HOME/.local/bin" "$HOME/bin" "$HOME/scripts" "$HOME/src"

    # Backup existing dotfiles once if not already backed up
    if [[ -f "$HOME/.zshenv" && ! -f "$HOME/.zshenv.bak" ]]; then
        cp "$HOME/.zshenv" "$HOME/.zshenv.bak"
    fi
    if [[ -f "$HOME/.zshrc" && ! -f "$HOME/.zshrc.bak" ]]; then
        cp "$HOME/.zshrc" "$HOME/.zshrc.bak"
    fi

    # ~/.zshenv
    cat <<'EOF' > "$HOME/.zshenv"
# ~/.zshenv: Sourced on all invocations of zsh (interactive, non-interactive, scripts)

# Prevent Ubuntu's /etc/zsh/zshrc from running redundant compinit before Oh My Zsh
skip_global_compinit=1

# Proto environment
export PROTO_HOME="$HOME/.proto"

# Homebrew environment setup
if [[ -d "/home/linuxbrew/.linuxbrew" ]]; then
    export HOMEBREW_PREFIX="/home/linuxbrew/.linuxbrew"
    export HOMEBREW_CELLAR="/home/linuxbrew/.linuxbrew/Cellar"
    export HOMEBREW_REPOSITORY="/home/linuxbrew/.linuxbrew/Homebrew"
    export MANPATH="/home/linuxbrew/.linuxbrew/share/man${MANPATH+:$MANPATH}:"
    export INFOPATH="/home/linuxbrew/.linuxbrew/share/info:${INFOPATH:-}"
    fpath=(/home/linuxbrew/.linuxbrew/share/zsh/site-functions $fpath)
    export FPATH
    path=(
        $HOME/.local/bin
        $HOME/bin
        $HOME/.cargo/bin
        $PROTO_HOME/shims
        $PROTO_HOME/bin
        /home/linuxbrew/.linuxbrew/bin
        /home/linuxbrew/.linuxbrew/sbin
        $path
    )
elif [[ -d "$HOME/.linuxbrew" ]]; then
    export HOMEBREW_PREFIX="$HOME/.linuxbrew"
    export HOMEBREW_CELLAR="$HOME/.linuxbrew/Cellar"
    export HOMEBREW_REPOSITORY="$HOME/.linuxbrew/Homebrew"
    export MANPATH="$HOME/.linuxbrew/share/man${MANPATH+:$MANPATH}:"
    export INFOPATH="$HOME/.linuxbrew/share/info:${INFOPATH:-}"
    fpath=("$HOME/.linuxbrew/share/zsh/site-functions" $fpath)
    export FPATH
    path=(
        $HOME/.local/bin
        $HOME/bin
        $HOME/.cargo/bin
        $PROTO_HOME/shims
        $PROTO_HOME/bin
        "$HOME/.linuxbrew/bin"
        "$HOME/.linuxbrew/sbin"
        $path
    )
else
    path=(
        $HOME/.local/bin
        $HOME/bin
        $HOME/.cargo/bin
        $PROTO_HOME/shims
        $PROTO_HOME/bin
        $path
    )
fi

# Ensure unique entries in PATH and FPATH without scanning disk
typeset -U path PATH fpath FPATH
export PATH

# Default environment settings
export LANG="${LANG:-en_US.UTF-8}"
export EDITOR="${EDITOR:-nano}"
export VISUAL="${VISUAL:-$EDITOR}"
EOF
    log_info "Configured ~/.zshenv"

    # ~/.zshrc
    cat <<'EOF' > "$HOME/.zshrc"
# If not running interactively, don't do anything
[[ -o interactive ]] || return

# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Starship manages the prompt theme
ZSH_THEME=""

# Plugins
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)

source $ZSH/oh-my-zsh.sh

# -----------------------------------------------------------------------------
# Modern CLI Tool Integrations & Aliases
# -----------------------------------------------------------------------------

# Better ls (eza)
if (( $+commands[eza] )); then
    alias ls="eza --icons --group-directories-first"
    alias ll="eza -la --icons --group-directories-first"
    alias la="eza -a --icons --group-directories-first"
    alias tree="eza --tree --icons"
fi

# Better cat (bat)
if (( $+commands[bat] )); then
    alias cat="bat --paging=never"
fi

# Fast Node Manager (fnm)
if (( $+commands[fnm] )); then
    eval "$(fnm env --use-on-cd --shell zsh)"
fi

# Smarter cd (zoxide: type 'z folder_name' to jump anywhere)
if (( $+commands[zoxide] )); then
    eval "$(zoxide init zsh)"
fi

# Fuzzy finder (fzf: Ctrl+R history, Ctrl+T file find, Alt+C cd find)
if (( $+commands[fzf] )); then
    eval "$(fzf --zsh)"
fi

# Direnv (automatic per-directory environment loading)
if (( $+commands[direnv] )); then
    eval "$(direnv hook zsh)"
fi

# Antigravity IDE aliases (delegates to ~/.local/bin/ag)
alias agy="ag"
alias antigravity="ag"

# Jump to workspace only if shell starts in home directory
[[ "$PWD" == "$HOME" && -f ~/scripts/workspace.sh ]] && source ~/scripts/workspace.sh

# Starship prompt (keep at the very end of .zshrc)
if (( $+commands[starship] )); then
    eval "$(starship init zsh)"
fi
EOF
    log_info "Configured ~/.zshrc"

    # Default ~/scripts/workspace.sh if missing
    if [[ ! -f "$HOME/scripts/workspace.sh" ]]; then
        cat <<'EOF' > "$HOME/scripts/workspace.sh"
cd ~/src/scaffold 2>/dev/null || cd ~/src 2>/dev/null || cd ~
EOF
        chmod +x "$HOME/scripts/workspace.sh"
        log_info "Created default ~/scripts/workspace.sh"
    fi
}

# ------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------
main() {
    echo -e "${BOLD}${GREEN}====================================================${RESET}"
    echo -e "${BOLD}${GREEN}   WSL2 Ubuntu Environment Bootstrap Setup          ${RESET}"
    echo -e "${BOLD}${GREEN}====================================================${RESET}"

    prompt_user_identity
    install_system_packages
    configure_wsl
    configure_default_shell
    install_homebrew
    install_brew_packages
    install_cargo_tools
    setup_oh_my_zsh
    configure_starship
    configure_local_binaries
    configure_docker
    configure_git
    write_dotfiles

    echo
    echo -e "${BOLD}${GREEN}Bootstrap complete!${RESET}"
    echo -e "Restart your shell or run ${BOLD}exec zsh${RESET} to reload your environment."
}

main "$@"
