from __future__ import annotations

import os
import shutil
from pathlib import Path

from backend.paths import is_frozen, resource_root

ROOT = resource_root()
DATA_DIR = ROOT / "data"
BUNDLED_DB = DATA_DIR / "dictionary.db"
USER_DIR = Path.home() / ".en-word"


def static_dir() -> Path | None:
    dist = ROOT / "dist"
    return dist if dist.exists() else None


def resolve_db_path() -> Path:
    override = os.environ.get("ENWORD_DB")
    if override:
        return Path(override)

    user_db = USER_DIR / "dictionary.db"
    if is_frozen():
        ensure_user_db()
        if user_db.exists():
            return user_db
        raise FileNotFoundError("Bundled dictionary database not found in app package.")

    if BUNDLED_DB.exists():
        return BUNDLED_DB
    if user_db.exists():
        return user_db
    raise FileNotFoundError("Dictionary database not found. Run: npm run db:download")


def ensure_user_db() -> Path:
    USER_DIR.mkdir(parents=True, exist_ok=True)
    user_db = USER_DIR / "dictionary.db"
    if not user_db.exists() and BUNDLED_DB.exists():
        shutil.copy2(BUNDLED_DB, user_db)
    return resolve_db_path()
