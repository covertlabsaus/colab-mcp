from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Generator, Iterable, Optional

from .types import ChatMessage, ChatRecord, CursorEvent, McpLogEntry


def _safe_json_lines(path: Path) -> Iterable[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                # Skip malformed lines
                continue


def stream_chat_jsonl(path: Path) -> Generator[ChatRecord, None, None]:
    for obj in _safe_json_lines(path):
        msg = None
        m = obj.get("message")
        if isinstance(m, dict) and "role" in m:
            msg = ChatMessage(role=m.get("role"), content=m.get("content"), model=m.get("model"))
        yield ChatRecord(
            type=obj.get("type", "unknown"),
            timestamp=obj.get("timestamp"),
            sessionId=obj.get("sessionId"),
            cwd=obj.get("cwd"),
            message=msg,
            raw=obj,
        )


def load_mcp_json_array(path: Path) -> Generator[McpLogEntry, None, None]:
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return
    if not isinstance(data, list):
        return
    for item in data:
        if not isinstance(item, dict):
            continue
        debug = item.get("debug")
        ts = item.get("timestamp")
        if not debug or not ts:
            continue
        yield McpLogEntry(debug=debug, timestamp=ts, sessionId=item.get("sessionId"), cwd=item.get("cwd"))


CURSOR_LINE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} .*?) \[(?P<level>info|warn|error)\] (?P<msg>.*)$")


def scan_cursor_log(path: Path) -> Generator[CursorEvent, None, None]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = CURSOR_LINE.match(line.strip())
            if not m:
                continue
            yield CursorEvent(level=m.group("level"), timestamp=m.group("ts"), message=m.group("msg"))


def read_tmp_cwd(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return None


# --- Codex readers ---

def stream_codex_history(path: Path) -> Generator[dict, None, None]:
    for obj in _safe_json_lines(path):
        yield obj


def read_text_file(path: Path, tail_lines: int = 2000) -> str:
    if not path.exists():
        return ""
    try:
        # naive tail
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-tail_lines:])
    except Exception:
        return ""

