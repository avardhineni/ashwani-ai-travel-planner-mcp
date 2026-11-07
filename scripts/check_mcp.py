"""Discover tools from one provider. Usage: python scripts/check_mcp.py weather"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp_client import discover_tools

async def main():
    if len(sys.argv) < 2 or sys.argv[1] not in {'tavily','aviationstack','weather'}:
        raise SystemExit('Usage: python scripts/check_mcp.py tavily|aviationstack|weather')
    provider = sys.argv[1]
    tools = await discover_tools(provider)
    print(f'{provider}: {len(tools)} discovered tools')
    for tool in tools:
        print(' -', tool)

if __name__ == '__main__':
    asyncio.run(main())
