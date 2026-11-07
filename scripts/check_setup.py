"""Print which components are configured, without exposing credentials."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import env, python_for_aviation

def is_configured(name):
    value = env(name)
    return bool(value) and not value.lower().startswith('replace_with')

checks = {
    'Groq API key': is_configured('GROQ_API_KEY'),
    'Tavily API key': is_configured('TAVILY_API_KEY'),
    'AviationStack API key': is_configured('AVIATIONSTACK_API_KEY'),
    'OpenWeatherMap API key': is_configured('OPENWEATHER_API_KEY'),
    'PostgreSQL URL': is_configured('DATABASE_URL'),
    'AviationStack MCP interpreter': python_for_aviation().is_file(),
}
for name, ok in checks.items():
    print(f'{name}: {"configured" if ok else "missing"}')
if not all(checks.values()):
    raise SystemExit('Setup incomplete: see README.md.')
print('Configuration present (external connectivity not yet tested).')
