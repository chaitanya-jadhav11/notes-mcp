# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A minimal Notes app built on the **Model-Context-Protocol (MCP)**. A Python MCP server exposes note CRUD tools over stdio; an async client connects to that server and lets Claude AI manage notes interactively via tool calls.

## Commands

All commands use `uv` (Python package manager). Requires Python 3.12+.

```bash
# Install dependencies
uv sync

# Run the interactive chat client (main entry point)
uv run -m client.client

# Inspect/develop the MCP server in the MCP dev UI
uv run mcp dev server/server.py
```

No test or lint configuration exists yet.

## Architecture

The system has three layers communicating in a chain:

```
User → claude_client.py (Anthropic API) → MCPClient (stdio) → server.py (FastMCP) → db.py (SQLite)
```

**`client/claude_client.py`** — Wraps `AsyncAnthropic`. Maintains conversation history, converts MCP tool definitions to Anthropic format, handles multi-turn tool-call loops (Claude calls a tool → result sent back → Claude responds). Prompt caching (`cache_control: ephemeral`) is applied to the system prompt and last tool to reduce token costs.

**`client/client.py`** — `MCPClient` class manages the stdio subprocess connection to the server (via `AsyncExitStack`). The `main()` function runs the interactive REPL loop with color-coded output (`colorama`).

**`server/server.py`** — FastMCP server exposing 8 tools: `list_notes`, `create_note`, `get_note_by_id`, `get_notes_by_title`, `search_notes`, `update_note`, `delete_note_by_id`, `delete_notes_by_title`. Each tool delegates directly to `db.py`.

**`server/db.py`** — Thin SQLite layer. Opens a new connection per call (`get_conn()`). Notes have UUID primary keys and an ISO UTC `created_at` timestamp.

## Configuration

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY="sk-ant-..."
CLAUDE_MODEL="claude-haiku-4-5-20251001"
```

The SQLite database (`notes.db`) is created automatically in the working directory on first run.

## Key Implementation Notes

- The client runs on Windows; `asyncio.WindowsProactorEventLoopPolicy()` is set at startup.
- `claude_client.py:chat()` has infrastructure for extended thinking (configurable budget) but it is disabled in the default main loop.
- Tool schema conversion (`convert_mcp_tools_to_anthropic()`) bridges MCP's `inputSchema` format to the Anthropic SDK's `tools` list format.
