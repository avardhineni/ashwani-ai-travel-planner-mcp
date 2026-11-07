# Ashwani AI Travel Planner — Multi-Agent Travel Research with LangGraph + MCP

> **A Python portfolio project demonstrating four LangGraph agents, three MCP server integrations, PostgreSQL checkpoint persistence, a Streamlit dashboard, and PDF travel-plan exports.**
>
> **Important:** This application researches and drafts travel plans. It **does not book** flights/hotels, guarantee prices, or verify that listed inventory is available. All outputs require independent verification before purchase or travel.

## Contents

- [Project overview](#project-overview)
- [Features](#features)
- [Architecture](#architecture)
- [How MCP works here](#how-mcp-works-here)
- [Repository structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Quick start on Windows](#quick-start-on-windows)
- [Install the local AviationStack MCP server](#install-the-local-aviationstack-mcp-server)
- [Run and verify](#run-and-verify)
- [Important code walkthrough](#important-code-walkthrough)
- [Example request](#example-request)
- [Known limitations](#known-limitations)
- [Security and responsible use](#security-and-responsible-use)
- [Troubleshooting](#troubleshooting)
- [Testing and future roadmap](#testing-and-future-roadmap)
- [Credits and references](#credits-and-references)

## Project overview

The project was created as a hands-on learning application for **Agentic AI engineering**. It extends a basic LangGraph travel-planning project by introducing Model Context Protocol (MCP), using the same application logic to access multiple external service providers through a common tool interface.

The user enters a natural-language request such as *"Plan a 7-day trip to Tokyo from Hyderabad with sightseeing and a budget of ₹200,000."* The application then runs four sequential agents:

1. **Flight Agent:** discovers airline/airport reference tools through a local AviationStack MCP server and uses Groq to produce clearly labeled flight-planning suggestions.
2. **Hotel Agent:** retrieves web research using Tavily's remote MCP server.
3. **Weather Agent:** uses an LLM to extract a destination city, then calls two tools exposed by our custom FastMCP Weather Server, which communicates with OpenWeatherMap.
4. **Itinerary Agent:** combines the preceding agents' outputs with the original requirements to generate a day-by-day plan.

The user's workflow state is checkpointed in **PostgreSQL**, while Streamlit displays agent results and creates an **A4 PDF travel plan**.

### What this project demonstrates

| Capability | Implementation |
| --- | --- |
| Workflow orchestration | `StateGraph` with four nodes and explicit edges |
| Shared agent state | `TravelState` (`TypedDict`) with LangGraph reducers |
| LLM inference | `ChatGroq`, configured with a currently supported model ID |
| MCP integration | `MultiServerMCPClient` from `langchain-mcp-adapters` |
| Remote MCP transport | Tavily via Streamable HTTP |
| Local MCP transport | AviationStack server via `stdio` |
| Custom MCP server | `FastMCP`, exposing weather and short-range forecast tools |
| Persistence | PostgreSQL / `AsyncPostgresSaver` checkpoints |
| Frontend | Streamlit with incremental agent completion updates |
| Reporting | ReportLab PDF with Markdown section formatting |
| Testing | `pytest`, environment checks, and MCP tool discovery scripts |

## Features

- Four-agent LangGraph pipeline: Flight → Hotel → Weather → Itinerary.
- Remote, third-party local, and self-authored local MCP integrations.
- Tool discovery using `client.get_tools(server_name=...)`, invocation using `.ainvoke(...)`.
- Independent provider credentials in a private `.env` file.
- Reusable, portable project paths (no tutorial author's `E:\` paths).
- Groq model selected using `GROQ_MODEL` instead of a hardcoded retired model.
- PostgreSQL checkpointing with the connection configuration needed for proper migrations.
- Error-aware tool invocation so missing providers can produce a clearly marked warning.
- Streamlit visualization of all **four current agents**, including Weather.
- Unique thread per new plan, so a new request does not accidentally mix in old checkpoints.
- PDF download and local automatic save under `travel_plans/`.
- No API credentials, local virtual environment, or generated travel plans in Git.

## Architecture

```mermaid
flowchart TD
    U[Traveler] --> UI[Streamlit frontend.py]
    UI --> G[LangGraph main.py]
    G --> F[Flight Agent]
    F --> H[Hotel Agent]
    H --> W[Weather Agent]
    W --> I[Itinerary Agent]
    F --> M[mcp_client.py]
    H --> M
    W --> M
    M --> T[Tavily Remote MCP - HTTP]
    M --> A[AviationStack Local MCP - stdio]
    M --> C[Custom Weather MCP - stdio]
    T --> TA[Tavily web service]
    A --> AA[AviationStack API]
    C --> OW[OpenWeatherMap API]
    F -.-> L[Groq LLM]
    W -.-> L
    I -.-> L
    G <--> PG[(PostgreSQL checkpoints)]
    I --> UI
    UI --> PDF[PDF export and download]
```

**How data flows:** `frontend.py` starts the graph → every node reads `TravelState` → MCP-backed nodes use `mcp_client.py` → MCP servers access their provider APIs → results update `TravelState` → Itinerary Agent generates the plan → Streamlit displays and exports it.

The graph is **sequential, not a supervisor-driven dynamic agent team**. MCP standardizes tool communication, but it does not by itself make a workflow autonomous.

## How MCP works here

| MCP server | Who maintains it? | Transport | Tools used | What it can and cannot prove |
| --- | --- | --- | --- | --- |
| Tavily | Tavily | `streamable_http` | `tavily_search` | Web research; not confirmed hotel rates or bookings |
| AviationStack | Third-party open-source project | `stdio` | `list_airports`, `list_airlines` | Reference information, **not verified live ticket prices** |
| Weather | This repository | `stdio` | `get_current_weather`, `get_forecast` | Current conditions and short-range forecast points, not distant trip weather |

### Remote versus local

- **Remote Tavily:** The application uses an HTTPS MCP endpoint hosted by Tavily. Authorization uses a bearer token sent in an HTTP header.
- **Local AviationStack:** The application starts a Python process from a separately cloned/open-source AviationStack MCP project and communicates with it over standard input/output.
- **Custom Weather:** The application starts `custom_weather_mcp_server.py` using its own Python virtual environment. The `@mcp.tool()` decorator exposes two tools.

An MCP server may still use a provider's **ordinary REST API internally**. MCP does not eliminate those APIs; it provides a standardized client-to-tool protocol.

## Repository structure

```text
ashwani-ai-travel-planner-mcp/
├── .github/
│   └── workflows/
│       └── tests.yml                    # GitHub Actions basic checks
├── scripts/
│   ├── check_setup.py                   # Checks configuration (no secrets printed)
│   └── check_mcp.py                     # Discovers tools from one MCP provider
├── tests/
│   ├── test_config.py
│   └── test_pdf_export.py
├── .env.example                         # Placeholder values only; copy to .env
├── .gitignore                           # Excludes secrets, local envs, generated files
├── .python-version                      # Recommended Python version
├── config.py                            # Paths and environment configuration
├── custom_weather_mcp_server.py         # Self-authored FastMCP server
├── mcp_client.py                        # MCP configuration, discovery, invocation
├── main.py                              # LangGraph agents, state, checkpoint runtime
├── frontend.py                          # Streamlit dashboard
├── pdf_export.py                        # ReportLab A4 PDF generator
├── test_db.py                           # Local PostgreSQL connection check
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

The following **local folders are not included in Git** and are created during setup:

```text
ashwani-travel-agent/                   # Main project Python virtual environment
aviationstack-mcp/                      # Separately cloned third-party MCP server
travel_plans/                           # Generated PDFs, private to your machine
.env                                    # Your real keys/passwords (NEVER publish)
```

## Prerequisites

- Windows 10/11 with **PowerShell** and VS Code (the commands below focus on Windows).
- **Python 3.13+** recommended, with `python` and `pip` available. Python 3.14 may also be used if all dependencies install successfully.
- Git (`git --version`).
- PostgreSQL Server 16+ installed and running on your computer. The project uses PostgreSQL 18 in its learning environment.
- API keys for **Groq**, **Tavily**, **AviationStack**, and **OpenWeatherMap**.
- Internet access for remote LLM, Tavily, AviationStack, and weather API operations.
- Optional: `uv` for installing the cloned AviationStack MCP server.

### Required accounts

| Provider | Link | Why used |
| --- | --- | --- |
| Groq | https://console.groq.com | Generates flight guidance, extracts destination, builds itinerary |
| Tavily | https://tavily.com | Remote MCP search for accommodation research |
| AviationStack | https://aviationstack.com | API consumed by the local AviationStack MCP server |
| OpenWeatherMap | https://openweathermap.org | Weather API consumed by the custom MCP server |

Provider plans, models, limits, weather history, flight endpoints and costs may change. Check each provider's current documentation.

## Quick start on Windows

### 1. Clone this GitHub project (or unpack its ZIP)

```powershell
git clone https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git
cd <YOUR_REPO_NAME>
```

**Before your first GitHub push:** if you downloaded the ZIP from ChatGPT, open the unzipped project root in VS Code and use the [Publishing to GitHub](#publishing-to-github) steps below instead.

### 2. Create a Python virtual environment

```powershell
py -3.13 -m venv ashwani-travel-agent
.\ashwani-travel-agent\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you are using Python 3.14 instead of 3.13, you can use `python -m venv ashwani-travel-agent`.

A correct terminal prompt begins with `(ashwani-travel-agent)`.

### 3. Create your PostgreSQL database

Open **pgAdmin 4 → select the `postgres` database → Query Tool**, then run:

```sql
CREATE DATABASE ashwani_travel_agent;
```

The name uses underscores because they are easier to use in SQL and connection URLs. It does not need to match the virtual environment's hyphenated name.

Make sure your Windows PostgreSQL service is running:

```powershell
Get-Service -Name "postgresql*"
Test-NetConnection localhost -Port 5432
```

If your server uses another port, change the connection URL accordingly.

### 4. Create a private `.env`

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace **all** `replace_with_...` placeholders with your own keys and connection details:

```dotenv
GROQ_API_KEY=your_actual_key
GROQ_MODEL=openai/gpt-oss-120b
TAVILY_API_KEY=your_actual_key
AVIATIONSTACK_API_KEY=your_actual_key
OPENWEATHER_API_KEY=your_actual_key
DATABASE_URL=postgresql://postgres:your_url_encoded_password@localhost:5432/ashwani_travel_agent
AVIATION_MCP_PYTHON=aviationstack-mcp/.venv/Scripts/python.exe
```

**Do not copy the example text literally.** Never commit `.env`. If the PostgreSQL password contains `@`, replace that character with `%40` in the URL. Other reserved URL characters must also be URL-encoded.

### 5. Install and configure the local AviationStack MCP server

Follow the dedicated section below. It is a separate Python project with its own `.venv`.

### 6. Check your local configuration

```powershell
python scripts/check_setup.py
```

This checks whether the expected settings and AviationStack interpreter exist, but does **not** verify that remote APIs are reachable.

## Install the local AviationStack MCP server

We integrate with the separate MIT-licensed project at [Pradumnasaraf/aviationstack-mcp](https://github.com/Pradumnasaraf/aviationstack-mcp). **Its source code is not bundled in this repository.**

From this project root:

```powershell
git clone https://github.com/Pradumnasaraf/aviationstack-mcp.git
python -m pip install uv
cd aviationstack-mcp
uv sync
cd ..
```

This creates `aviationstack-mcp/.venv` with the third-party server dependencies. The Python command for Windows should be:

```text
aviationstack-mcp/.venv/Scripts/python.exe
```

Our `mcp_client.py` starts the server automatically over `stdio`, passing its credential in the child process environment. You normally do **not** need to run a second always-on terminal for this stdio integration.

If you prefer a different installation directory, set `AVIATION_MCP_PYTHON` to its actual `python.exe` path. The path can be relative to this project root or absolute.

If your installation of the third-party repository uses a different entry point, consult its current README and adjust the `aviationstack` `args` in `mcp_client.py`. Do not assume an older tutorial command remains valid forever.

**Note:** AviationStack API access may restrict some endpoints based on your subscription. The project intentionally uses only reference-data tools and does not claim that they yield flight fares.

## Run and verify

### A. Verify PostgreSQL

```powershell
python test_db.py
```

Expected output resembles `Connected to PostgreSQL database: ashwani_travel_agent`. Do not paste credentials when sharing logs.

### B. Verify MCP tool discovery, one provider at a time

```powershell
python scripts/check_mcp.py weather
python scripts/check_mcp.py aviationstack
python scripts/check_mcp.py tavily
```

Typical discovered tools include:

- Weather: `get_current_weather`, `get_forecast`.
- AviationStack: `list_airports`, `list_airlines` (among others).
- Tavily: `tavily_search` (among others).

Tool discovery confirms that the server advertises those tools; **it does not mean every subsequent provider API request will succeed**.

### C. CLI application

```powershell
python main.py
```

Example input:

```text
Plan a 7-day Japan trip from Hyderabad including hotels and sightseeing under ₹200,000.
```

The graph will run four agents and display the final itinerary. Each run uses a unique PostgreSQL `thread_id`.

### D. Streamlit frontend

```powershell
python -m streamlit run frontend.py
```

Open **http://localhost:8501** in your browser. Enter a request, click **Generate My Travel Plan**, expand agent results, and click **Download PDF Plan**. The PDF is also saved to the local `travel_plans/` folder.

### E. Run local tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

GitHub Actions runs the same basic test suite on pushes and pull requests. External provider integration tests require credentials and are **not** part of the public CI workflow.

## Important code walkthrough

### `main.py` — LangGraph orchestration

`TravelState` defines shared fields: `user_query`, `flight_results`, `hotel_results`, `weather_results`, `itinerary`, `messages`, and `llm_calls`.

- `messages: Annotated[..., add_messages]` accumulates chat messages with LangGraph's message reducer.
- `llm_calls: Annotated[int, operator.add]` adds the per-node number of successful Groq responses, rather than setting an arbitrary value.
- Each node returns a **partial state update**.
- The graph is compiled with `AsyncPostgresSaver.from_conn_string`, which creates a connection with appropriate autocommit and row handling.
- Nodes use `await` for both LLM requests and MCP tool calls.
- The workflow is currently linear: `START → flight_agent → hotel_agent → weather_agent → itinerary_agent → END`.

### `mcp_client.py` — MCP tool integration

`server_config(name)` constructs a transport configuration for a specific provider; it does not hardcode the tutorial instructor's installation paths.

`discover_tools(name)` runs the MCP discovery phase and prints tool names for troubleshooting.

`invoke_tools(server, [(tool_name, args), ...])` discovers tools from exactly one configured MCP server and calls the requested tools with `.ainvoke()`.

`aviation_reference_data()`, `tavily_mcp_search()` and `weather_mcp_lookup()` expose reusable operations to the LangGraph nodes.

`as_prompt_text()` converts returned tool data into bounded text so an external tool response does not become arbitrarily long inside an LLM prompt.

### `custom_weather_mcp_server.py` — own MCP server

```python
mcp = FastMCP('Travel Planner Weather Server')

@mcp.tool()
def get_current_weather(city: str) -> dict:
    ...

@mcp.tool()
def get_forecast(city: str) -> dict:
    ...

if __name__ == '__main__':
    mcp.run(transport='stdio')
```

The decorator registers a Python function as an MCP tool. The functions call OpenWeatherMap's HTTPS API with a request timeout and return structured dictionaries. The forecast tool currently returns only **five three-hourly records** (roughly 15 hours), not a five-day forecast.

### `frontend.py` and `pdf_export.py`

Streamlit calls `app.astream(..., stream_mode='updates')` through an async helper to show progress as each node completes. Unlike token streaming, this delivers **node-level** updates. It stores the last generated PDF in Streamlit session state so the download persists after a widget rerun.

`pdf_export.py` creates A4 PDFs using ReportLab and your system's available fonts. It does not bundle proprietary font files. The PDF includes flight research, hotel research, weather, the itinerary, and a verification disclaimer.

## Example request

```text
Plan a complete 7-day Japan trip for two adults departing Hyderabad in April.
Include flight guidance, hotel research, sightseeing suggestions, weather information,
and keep total spending below ₹200,000 if possible.
Clearly identify any unverified prices or missing booking information.
```

Expected **workflow behavior** (not a promise of provider data):

1. Flight Agent returns research and warns when fares cannot be verified.
2. Hotel Agent returns Tavily search information or an explicit provider error.
3. Weather Agent attempts to extract a destination city and fetch current/short-range weather.
4. Itinerary Agent synthesizes a day-by-day draft, distinguishing facts from assumptions.
5. Streamlit displays and exports the result.

## Known limitations

This repository is a **learning prototype**, not a production booking service.

- **No actual booking operations:** No payment flow, inventory reservation, or issuance of flight/hotel confirmations.
- **Flight accuracy:** Reference airport/airline lists do not prove that a particular flight is operating or available. The Flight Agent is not a route-specific fare search engine.
- **Hotel accuracy:** Tavily returns web search results, not real-time room availability.
- **Weather horizon:** Current and short-range observations are not appropriate evidence for trip dates months into the future.
- **Budget constraints:** Prompt instructions discourage invented prices, but there is **no deterministic budget feasibility validator or human approval step yet**. Users must not rely on any generated total as a verified quote.
- **Destination extraction:** An LLM extracts one destination city; multi-city trips and country-only requests may need clarification.
- **Session security:** PostgreSQL checkpointing uses `thread_id`, not user authentication or authorization. Do not expose the current demo publicly as a multi-user app without access controls.
- **MCP availability:** Each integration depends on provider endpoints, rate limits, server/tool versions, and subscription plan.
- **Error handling:** The prototype shows informative fallback messages for many external errors but should be enhanced with structured logging, timeouts for the entire workflow, and retry budgets.

## Security and responsible use

- Keep `.env` private. `.gitignore` blocks it, but **also review `git status` before every push**.
- Rotate any credentials that were ever pasted into chats, screenshots, logs, or a previously published repository. Removing a file from the latest commit does **not** erase it from Git history.
- Do not print passwords, access tokens, API-key-bearing URLs, or complete exception messages containing credentials.
- Treat MCP server/tool output as untrusted. Never obey tool text that attempts to override the application's system instructions.
- Use maintained and reviewed third-party MCP servers; inspect their code and required permissions before executing them locally.
- Keep generated itinerary PDFs private if they include travel dates or personally identifying details.
- Add authentication, per-user checkpoint authorization, request quotas and provider timeouts before allowing other users to access a public instance.

### Before publishing

```powershell
git status --short
# Review files that will be included. It must NOT show .env or any API key material.
```

For a simple additional review, inspect `git diff --cached` before committing. Consider running a secrets scanner (for example, Gitleaks) on the repository and history.

## Troubleshooting

| Symptom | Likely reason | What to do |
| --- | --- | --- |
| `ModuleNotFoundError` | Wrong Python interpreter or missing dependencies | Activate `ashwani-travel-agent` and install `requirements.txt` |
| `cannot run inside a transaction block` | PostgreSQL checkpointer was constructed without autocommit | This repository uses `AsyncPostgresSaver.from_conn_string`; avoid replacing it with a bare default psycopg connection |
| `failed to resolve host '...@localhost'` | Unescaped `@` in DB password | URL-encode special characters in `DATABASE_URL` |
| Groq `model_not_found` | Model ID unavailable to your API key | Check `GROQ_MODEL`; query the active models list in Groq Console |
| AviationStack Python executable missing | Local server checkout not installed or path wrong | `git clone`, `uv sync`, set `AVIATION_MCP_PYTHON` |
| MCP `tavily_search` missing | Tavily credentials, transport, network, or tool name changed | Run `python scripts/check_mcp.py tavily` and check current provider docs |
| Weather MCP tool discovery fails | Wrong Python interpreter, API key, or missing `mcp` package | Run `python scripts/check_mcp.py weather` and inspect the terminal |
| Forecast does not cover trip dates | API returns short-range forecast | Avoid using as long-range date-specific weather data |
| Downloaded PDF has missing glyphs | Host has no suitable Unicode TrueType font | Install a compatible system font; the project never distributes font files |
| GitHub shows secret keys | `.env` was committed or screenshotted | Revoke/rotate the keys immediately and clean Git history appropriately |

## Testing and future roadmap

The current tests are deliberately offline; they validate basic configuration behavior and PDF output without requiring personal API keys or consuming paid quotas.

Planned enhancements (not yet implemented):

- **Budget feasibility validation:** structured estimates, deterministic arithmetic, and strict budget-compliance checks.
- **Human-in-the-loop:** user confirmation before exceeding a budget or changing destination/dates.
- **Supervisor / conditional routing:** call only the agents required for each request.
- **Real booking and pricing providers:** legitimate bookable fare/room inventories and link-out workflows.
- **Long-range weather support:** date-appropriate forecast or historical climate data.
- **Structured agent output:** Pydantic schemas with source URLs, quote timestamps and confidence/verification states.
- **Agent evaluations:** tool-call correctness, retrieval relevance, unsupported-claim rate, budget constraint adherence, regression suites, latency and cost monitoring.
- **Security hardening:** authentication, authorization for checkpoint threads, provider permission scoping and secret management.

## Publishing to GitHub

Create a new **empty** repository on GitHub, for example `ashwani-ai-travel-planner-mcp`, without adding a README or `.gitignore` (they already exist in this project).

Then from the project root in VS Code:

```powershell
git init
git add .
git status --short
git commit -m "Initial commit: LangGraph MCP travel planner"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/ashwani-ai-travel-planner-mcp.git
git push -u origin main
```

Replace the GitHub URL with **your own** newly created repository URL. Review the staged files and confirm `.env`, PDF exports, `ashwani-travel-agent/`, and `aviationstack-mcp/` do not appear.

**License decision:** This package includes newly adapted educational project code and acknowledges external references. Review the original tutorial/repository terms and choose the license you want for your repository. A third-party MCP server's MIT license applies to that separate project; it is not bundled here.

## Credits and references

This project was developed as an educational extension of a video tutorial by **CodeWithAarohi**. It is not affiliated with the API providers or original tutorial author.

- Tutorial project / MCP architecture: [CodeWithAarohi — AI Travel Planning App using LangGraph and MCP](https://github.com/codewithaarohi/AI-Travel-Planning-App-using-LangGraph-and-MCP)
- Earlier tutorial project: [CodeWithAarohi — AI Travel Planning System using LangGraph](https://github.com/codewithaarohi/AI-Travel-Planning-System-using-LangGraph)
- Third-party AviationStack MCP Server: [Pradumnasaraf/aviationstack-mcp](https://github.com/Pradumnasaraf/aviationstack-mcp)
- [LangGraph documentation](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangChain MCP adapters](https://docs.langchain.com/oss/python/langchain/mcp)
- [Tavily MCP documentation](https://docs.tavily.com/documentation/mcp)
- [Groq supported models](https://console.groq.com/docs/models)
- [Model Context Protocol specification](https://modelcontextprotocol.io)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [PostgreSQL](https://www.postgresql.org/)

---

**Portfolio summary:** *Developed a LangGraph-based multi-agent travel research assistant integrating remote, local and custom MCP servers, Groq LLMs, PostgreSQL checkpoint persistence, Streamlit, and downloadable PDF itinerary reports.*
