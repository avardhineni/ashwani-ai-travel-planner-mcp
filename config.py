"""Local configuration. Never print keys or commit a real .env file."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / '.env', override=False)


def env(name: str, default: str = '') -> str:
    return os.getenv(name, default).strip()


def resolve_project_path(raw: str) -> Path:
    """Resolve a path from .env; relative paths are relative to this project."""
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def python_for_aviation() -> Path:
    default = 'aviationstack-mcp/.venv/Scripts/python.exe' if os.name == 'nt' else 'aviationstack-mcp/.venv/bin/python'
    return resolve_project_path(env('AVIATION_MCP_PYTHON', default))


def python_for_weather() -> str:
    return sys.executable


def require_database_url() -> str:
    value = env('DATABASE_URL')
    if not value:
        raise RuntimeError('DATABASE_URL missing. Copy .env.example to .env and set it.')
    return value


def require_groq_key() -> str:
    value = env('GROQ_API_KEY')
    if not value:
        raise RuntimeError('GROQ_API_KEY missing. Add it to your private .env file.')
    return value
