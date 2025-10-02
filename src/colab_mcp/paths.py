from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LogRoots:
    home: Path
    claude: Path
    cursor_logs: Path
    claude_cache_mcp: Path
    tmp: Path
    cursor_agent: Path
    codex: Path


def detect_roots(env: dict | None = None) -> LogRoots:
    e = env or os.environ
    home = Path(e.get("HOME", str(Path.home())))
    claude_dir = Path(e.get("CLAUDE_HOME", home / ".claude"))
    cursor_logs = Path(e.get("CURSOR_LOGS", home / ".cursor-server" / "data" / "logs"))
    claude_cache_mcp = Path(
        e.get(
            "CLAUDE_MCP_CACHE",
            home / ".cache" / "claude-cli-nodejs" / "-home-homeserver" / "mcp-logs-ide",
        )
    )
    tmp_dir = Path(e.get("TMPDIR", "/tmp"))
    cursor_agent_dir = Path(e.get("CURSOR_AGENT_HOME", home / ".local" / "share" / "cursor-agent"))
    codex_dir = Path(e.get("CODEX_HOME", home / ".codex"))
    return LogRoots(
        home=home,
        claude=claude_dir,
        cursor_logs=cursor_logs,
        claude_cache_mcp=claude_cache_mcp,
        tmp=tmp_dir,
        cursor_agent=cursor_agent_dir,
        codex=codex_dir,
    )


def session_project_dir(roots: LogRoots, project_scope: str) -> Path:
    return roots.claude / "projects" / project_scope


def global_history_file(roots: LogRoots) -> Path:
    return roots.claude / "history.jsonl"


def mcp_log_dir(roots: LogRoots) -> Path:
    return roots.claude_cache_mcp


def cursor_host_runs_dir(roots: LogRoots) -> Path:
    return roots.cursor_logs


def tmp_cwd_glob(roots: LogRoots) -> list[Path]:
    return sorted(roots.tmp.glob("claude-*-cwd"))


# Cursor agent helpers
def cursor_agent_versions_dir(roots: LogRoots) -> Path:
    return roots.cursor_agent / "versions"


# Codex helpers
def codex_history_file(roots: LogRoots) -> Path:
    return roots.codex / "history.jsonl"


def codex_config_file(roots: LogRoots) -> Path:
    return roots.codex / "config.toml"


def codex_auth_file(roots: LogRoots) -> Path:
    return roots.codex / "auth.json"


def codex_version_file(roots: LogRoots) -> Path:
    return roots.codex / "version.json"


def codex_tui_log_file(roots: LogRoots) -> Path:
    return roots.codex / "log" / "codex-tui.log"

