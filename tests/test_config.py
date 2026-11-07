from pathlib import Path
from config import PROJECT_ROOT, resolve_project_path


def test_relative_paths_use_project_root():
    assert resolve_project_path('custom_weather_mcp_server.py') == PROJECT_ROOT / 'custom_weather_mcp_server.py'


def test_project_files_are_rooted():
    assert (PROJECT_ROOT / 'README.md').is_file()
