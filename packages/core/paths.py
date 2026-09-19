from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = REPO_DIR / "apps"
SMOKE_DIR = REPO_DIR / "smoke"
SRC_DIR = REPO_DIR / "src"


WEB_DIR = APPS_DIR / "web"
API_DIR = APPS_DIR / "api"
