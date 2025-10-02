from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional


@dataclass
class McpLogEntry:
    debug: str
    timestamp: str
    sessionId: Optional[str] = None
    cwd: Optional[str] = None


@dataclass
class ChatMessage:
    role: Literal["user", "assistant"]
    content: Any
    model: Optional[str] = None


@dataclass
class ChatRecord:
    type: str
    timestamp: Optional[str]
    sessionId: Optional[str]
    cwd: Optional[str]
    message: Optional[ChatMessage] = None
    raw: Any = None


@dataclass
class CursorEvent:
    level: str
    timestamp: str
    message: str


@dataclass
class SessionMetadata:
    session_id: str
    project_scope: str
    first_ts: Optional[str]
    last_ts: Optional[str]
    messages: int
    cwd: Optional[str] = None

