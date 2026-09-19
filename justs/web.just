# Recipes for apps/web (Next.js + shadcn + Lucide + assistant-ui)
set shell := ["bash", "-uc"]
set working-directory := ".."

# Default recipe: list web recipes
default:
    @just --list web

# Run Next.js development server
dev:
    npm --prefix apps/web run dev

# Build Next.js production bundle
build:
    npm --prefix apps/web run build

# Start Next.js production server
start:
    npm --prefix apps/web run start

# Run ESLint on web app
lint:
    npm --prefix apps/web run lint

# Install dependencies from package-lock.json
install:
    npm --prefix apps/web install

# Check for outdated packages in apps/web
outdated:
    npm --prefix apps/web outdated || true

# Upgrade packages within semantic version ranges (^ and ~)
upgrade:
    npm --prefix apps/web update

# Interactive upgrade to latest major/minor releases (via npm-check-updates)
upgrade-latest:
    cd apps/web && npx -y npm-check-updates -u && npm install

# Add a npm package dependency (usage: just web add-pkg <pkg> [flags])
add-pkg PKG *FLAGS:
    npm --prefix apps/web install {{FLAGS}} {{PKG}}

# Add shadcn component to apps/web (usage: just web add <component>)
add COMPONENT:
    cd apps/web && npx -y shadcn@latest add {{COMPONENT}}

# Add assistant-ui component to apps/web (usage: just web add-assistant <component>)
add-assistant COMPONENT:
    cd apps/web && npx -y assistant-ui@latest add {{COMPONENT}} --use-npm
