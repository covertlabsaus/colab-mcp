from __future__ import annotations

import os
from typing import Literal

from fastmcp import FastMCP

from .paths import detect_roots
from .services import build_context_bundle, list_session_files, search_across, session_metadata, codex_summary


mcp = FastMCP(name="LogContextServer")


@mcp.tool()
def list_sessions(filter_project: str | None = None) -> list[dict]:
    """List known session IDs with basic metadata (first/last timestamp, messages, cwd)."""
    roots = detect_roots()
    sessions = list_session_files(roots)
    out: list[dict] = []
    for sid in sorted(sessions.keys()):
        md = session_metadata(roots, sid)
        if not md:
            continue
        if filter_project and md.project_scope != filter_project:
            continue
        out.append({
            "sessionId": md.session_id,
            "project": md.project_scope,
            "first": md.first_ts,
            "last": md.last_ts,
            "messages": md.messages,
            "cwd": md.cwd,
        })
    return out


@mcp.tool()
def fetch_transcript(
    session_id: str,
    offset: int = 0,
    limit: int = 50,
    include_chat: bool = True,
    include_mcp: bool = False,
    include_cursor: bool = False,
) -> dict:
    """Return a curated transcript/context bundle for a session with pagination and limits."""
    roots = detect_roots()
    bundle = build_context_bundle(
        roots,
        session_id=session_id,
        limit_chat=limit,
        limit_mcp=50 if include_mcp else 0,
        limit_cursor=100 if include_cursor else 0,
        include_chat=include_chat,
        include_mcp=include_mcp,
        include_cursor=include_cursor,
    )
    if include_chat and "chat" in bundle:
        chat = bundle.get("chat", [])
        bundle["chat"] = chat[offset: offset + limit]
    return bundle


@mcp.tool()
def summarize_session(session_id: str) -> dict:
    """Small summary for UI/tooling: first/last timestamps, message count, cwd pointer."""
    roots = detect_roots()
    md = session_metadata(roots, session_id)
    if not md:
        return {"error": "unknown session"}
    return {
        "sessionId": md.session_id,
        "project": md.project_scope,
        "first": md.first_ts,
        "last": md.last_ts,
        "messages": md.messages,
        "cwd": md.cwd,
    }


@mcp.tool()
def codex_status(tail: int = 200) -> dict:
    """OpenAI Codex CLI: tail of history and TUI log for quick inspection."""
    roots = detect_roots()
    return codex_summary(roots, tail=tail)


@mcp.tool()
def search_logs(query: str, scope: Literal["chat", "mcp", "cursor", "all"] = "all", limit: int = 50) -> list[dict]:
    """Search across chat transcripts, MCP runtime logs, and Cursor host logs."""
    roots = detect_roots()
    return search_across(roots, query=query, scope=scope, limit=limit)


def run() -> None:
    # Allow env overrides without code changes
    mcp.run()


if __name__ == "__main__":
    run()


