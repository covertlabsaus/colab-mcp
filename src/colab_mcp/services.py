from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional

from .paths import (
    LogRoots,
    global_history_file,
    session_project_dir,
    codex_history_file,
    codex_tui_log_file,
)
from .readers import (
    load_mcp_json_array,
    read_tmp_cwd,
    scan_cursor_log,
    stream_chat_jsonl,
    stream_codex_history,
    read_text_file,
)
from .types import ChatRecord, CursorEvent, McpLogEntry, SessionMetadata


def list_session_files(roots: LogRoots) -> Dict[str, List[Path]]:
    sessions: Dict[str, List[Path]] = defaultdict(list)
    projects_dir = roots.claude / "projects"
    if not projects_dir.exists():
        return {}
    for scope_dir in projects_dir.iterdir():
        if not scope_dir.is_dir():
            continue
        for f in scope_dir.glob("*.jsonl"):
            sid = f.stem
            sessions[sid].append(f)
    return dict(sessions)


def session_metadata(roots: LogRoots, session_id: str) -> Optional[SessionMetadata]:
    sessions = list_session_files(roots)
    files = sessions.get(session_id)
    if not files:
        return None
    first_ts: Optional[str] = None
    last_ts: Optional[str] = None
    count = 0
    scope = files[0].parent.name
    for f in files:
        for rec in stream_chat_jsonl(f):
            ts = rec.timestamp
            if ts:
                if first_ts is None or ts < first_ts:
                    first_ts = ts
                if last_ts is None or ts > last_ts:
                    last_ts = ts
            if rec.message:
                count += 1
    # best-effort cwd via latest tmp pointer
    cwd = None
    for p in sorted((roots.tmp).glob("claude-*-cwd")):
        cwd = read_tmp_cwd(p) or cwd
    return SessionMetadata(session_id=session_id, project_scope=scope, first_ts=first_ts, last_ts=last_ts, messages=count, cwd=cwd)


def build_context_bundle(
    roots: LogRoots,
    session_id: str,
    limit_chat: int = 200,
    limit_mcp: int = 100,
    limit_cursor: int = 200,
    include_chat: bool = True,
    include_mcp: bool = True,
    include_cursor: bool = False,
    include_cwd: bool = True,
) -> Dict[str, Any]:
    sessions = list_session_files(roots)
    files = sessions.get(session_id, [])
    chat: List[Dict[str, Any]] = []
    if include_chat:
        for f in files:
            for rec in stream_chat_jsonl(f):
                if rec.message:
                    chat.append({
                        "timestamp": rec.timestamp,
                        "role": rec.message.role,
                        "content": rec.message.content,
                    })
                if len(chat) >= limit_chat:
                    break
            if len(chat) >= limit_chat:
                break

    # Attach recent MCP runtime entries (optional)
    mcp_entries: List[Dict[str, Any]] = []
    if include_mcp:
        mcp_dir = roots.claude_cache_mcp
        if mcp_dir.exists():
            candidates = sorted(mcp_dir.glob("*.txt"))[-3:]
            for p in candidates:
                for e in load_mcp_json_array(p):
                    if len(mcp_entries) >= limit_mcp:
                        break
                    mcp_entries.append({"timestamp": e.timestamp, "debug": e.debug, "sessionId": e.sessionId})

    # Cursor host log (latest run)
    cursor_events: List[Dict[str, Any]] = []
    if include_cursor:
        runs_dir = roots.cursor_logs
        if runs_dir.exists():
            for run in sorted(runs_dir.iterdir()):
                for ext in ("exthost1", "exthost2"):
                    ev_dir = run / ext / "Anthropic.claude-code"
                    log_path = ev_dir / "Claude VSCode.log"
                    for ev in scan_cursor_log(log_path):
                        if len(cursor_events) >= limit_cursor:
                            break
                        cursor_events.append({"timestamp": ev.timestamp, "level": ev.level, "message": ev.message})

    # cwd pointer (best-effort)
    cwd = None
    for p in sorted((roots.tmp).glob("claude-*-cwd")):
        cwd = read_tmp_cwd(p) or cwd

    return {
        "sessionId": session_id,
        "chat": chat,
        "mcp": mcp_entries,
        "cursor": cursor_events,
        "cwd": cwd,
    }


def codex_summary(roots: LogRoots, tail: int = 200) -> dict:
    history_path = codex_history_file(roots)
    events = []
    for i, obj in enumerate(stream_codex_history(history_path)):
        if i >= tail:
            break
        events.append(obj)
    tui_log = read_text_file(codex_tui_log_file(roots), tail_lines=1000)
    return {"history_tail": events, "tui_log_tail": tui_log}


def search_across(roots: LogRoots, query: str, scope: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    sessions = list_session_files(roots)
    def add_result(kind: str, payload: Dict[str, Any]):
        if len(results) < limit:
            results.append({"kind": kind, **payload})

    if scope in ("all", "chat"):
        for sid, files in sessions.items():
            for f in files:
                for rec in stream_chat_jsonl(f):
                    text = json_like(rec.raw)
                    if query.lower() in text.lower():
                        add_result("chat", {"sessionId": sid, "file": str(f), "timestamp": rec.timestamp})
                        if len(results) >= limit:
                            return results

    if scope in ("all", "mcp"):
        mcp_dir = roots.claude_cache_mcp
        for p in sorted(mcp_dir.glob("*.txt")):
            for e in load_mcp_json_array(p):
                if query.lower() in (e.debug or "").lower():
                    add_result("mcp", {"file": str(p), "timestamp": e.timestamp, "debug": e.debug})
                    if len(results) >= limit:
                        return results

    if scope in ("all", "cursor"):
        runs_dir = roots.cursor_logs
        for run in sorted(runs_dir.iterdir()):
            for ext in ("exthost1", "exthost2"):
                ev_dir = run / ext / "Anthropic.claude-code"
                log_path = ev_dir / "Claude VSCode.log"
                for ev in scan_cursor_log(log_path):
                    if query.lower() in ev.message.lower():
                        add_result("cursor", {"file": str(log_path), "timestamp": ev.timestamp, "message": ev.message})
                        if len(results) >= limit:
                            return results

    return results


def json_like(obj: Any) -> str:
    try:
        import json
        return json.dumps(obj, ensure_ascii=False)[:10000]
    except Exception:
        return str(obj)[:10000]

