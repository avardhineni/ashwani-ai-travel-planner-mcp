"""MCP tool gateway for Tavily (remote), AviationStack (local) and weather (custom local).

Creates a fresh MCP client for each grouped operation to avoid keeping subprocess-bound
async tool references across independent Streamlit reruns or event loops.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from config import PROJECT_ROOT, env, python_for_aviation, python_for_weather


class MCPConfigurationError(RuntimeError):
    """An MCP provider is not configured or executable is missing."""


def server_config(name: str) -> dict[str, Any]:
    if name == 'tavily':
        api_key = env('TAVILY_API_KEY')
        if not api_key:
            raise MCPConfigurationError('TAVILY_API_KEY is missing')
        # Prefer authorization header to putting a credential in the URL.
        return {
            'transport': 'streamable_http',
            'url': 'https://mcp.tavily.com/mcp/',
            'headers': {'Authorization': f'Bearer {api_key}'},
        }
    if name == 'aviationstack':
        api_key = env('AVIATIONSTACK_API_KEY')
        executable = python_for_aviation()
        if not api_key:
            raise MCPConfigurationError('AVIATIONSTACK_API_KEY is missing')
        if not executable.is_file():
            raise MCPConfigurationError(
                'AviationStack MCP Python not found. Install the third-party server and set AVIATION_MCP_PYTHON.'
            )
        return {
            'transport': 'stdio',
            'command': str(executable),
            'args': ['-m', 'aviationstack_mcp', 'mcp', 'run'],
            'env': {**os.environ, 'AVIATION_STACK_API_KEY': api_key},
        }
    if name == 'weather':
        api_key = env('OPENWEATHER_API_KEY')
        script = PROJECT_ROOT / 'custom_weather_mcp_server.py'
        if not api_key:
            raise MCPConfigurationError('OPENWEATHER_API_KEY is missing')
        if not script.is_file():
            raise MCPConfigurationError('custom_weather_mcp_server.py is missing')
        return {
            'transport': 'stdio',
            'command': python_for_weather(),
            'args': [str(script)],
            'env': {**os.environ, 'OPENWEATHER_API_KEY': api_key},
        }
    raise MCPConfigurationError(f'Unknown MCP server: {name}')


def _client(name: str) -> MultiServerMCPClient:
    return MultiServerMCPClient({name: server_config(name)})


async def discover_tools(server_name: str) -> list[str]:
    client = _client(server_name)
    tools = await client.get_tools(server_name=server_name)
    return [tool.name for tool in tools]


async def invoke_tools(server_name: str, requests: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    """Discover one server's tools and invoke named tools in a single event loop."""
    client = _client(server_name)
    tools = await client.get_tools(server_name=server_name)
    by_name = {tool.name: tool for tool in tools}
    results = {}
    for tool_name, arguments in requests:
        tool = by_name.get(tool_name)
        if tool is None:
            raise LookupError(f'{server_name} MCP tool {tool_name!r} not found; available: {sorted(by_name)}')
        results[tool_name] = await tool.ainvoke(arguments)
    return results


async def tavily_mcp_search(query: str) -> Any:
    return (await invoke_tools('tavily', [('tavily_search', {'query': query})]))['tavily_search']


async def aviation_reference_data() -> dict[str, Any]:
    """Reference-data demo, not an airline fare or live availability search."""
    return await invoke_tools('aviationstack', [
        ('list_airports', {'limit': 10}),
        ('list_airlines', {'limit': 10}),
    ])


async def weather_mcp_lookup(city: str) -> dict[str, Any]:
    return await invoke_tools('weather', [
        ('get_current_weather', {'city': city}),
        ('get_forecast', {'city': city}),
    ])


def as_prompt_text(value: Any, limit: int = 6500) -> str:
    """Normalize MCP tool content blocks into a bounded prompt string."""
    if value is None:
        return 'Not available'
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, default=str, indent=2)
        except (TypeError, ValueError):
            text = str(value)
    return text[:limit] + ('\n[truncated]' if len(text) > limit else '')


if __name__ == '__main__':
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else 'weather'
    try:
        print('Discovered tools:', ', '.join(asyncio.run(discover_tools(name))))
    except Exception as exc:
        print(f'Tool discovery failed: {type(exc).__name__}: {exc}')
        raise SystemExit(1)
