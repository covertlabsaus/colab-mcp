#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pwd
import shutil
import sys
import termios
import tty
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


console = Console()

GRADIENT_ASCII = Text.from_markup(
    "[rgb(255,140,0)]   █████████           ████            █████      ██████   ██████   █████████  ███████████  [/]\n"
    "[rgb(255,160,50)]  ███░░░░░███         ░░███           ░░███      ░░██████ ██████   ███░░░░░███░░███░░░░░███ [/]\n"
    "[rgb(240,180,80)] ███     ░░░   ██████  ░███   ██████   ░███████   ░███░█████░███  ███     ░░░  ░███    ░███ [/]\n"
    "[rgb(220,195,110)]░███          ███░░███ ░███  ░░░░░███  ░███░░███  ░███░░███ ░███ ░███          ░██████████  [/]\n"
    "[rgb(190,210,140)]░███         ░███ ░███ ░███   ███████  ░███ ░███  ░███ ░░░  ░███ ░███          ░███░░░░░░   [/]\n"
    "[rgb(160,220,170)]░░███     ███░███ ░███ ░███  ███░░███  ░███ ░███  ░███      ░███ ░░███     ███ ░███         [/]\n"
    "[rgb(130,225,200)] ░░█████████ ░░██████  █████░░████████ ████████   █████     █████ ░░█████████  █████        [/]\n"
    "[rgb(135,206,250)]  ░░░░░░░░░   ░░░░░░  ░░░░░  ░░░░░░░░ ░░░░░░░░   ░░░░░     ░░░░░   ░░░░░░░░░  ░░░░░         [/]\n"
)

@dataclass
class DetectionResult:
    found: bool
    evidence: List[str] = field(default_factory=list)


@dataclass
class ToolInstaller:
    key: str
    display_name: str
    detection_fn: Callable[[Path], DetectionResult]
    install_fn: Callable[["InstallContext"], None]
    description: str


@dataclass
class InstallContext:
    console: Console
    home: Path
    server_name: str
    server_command: str
    env: Dict[str, str]
    target_user: str
    target_uid: int
    target_gid: int


class SelectionMenu:
    def __init__(self, items: Sequence[Tuple[Optional[ToolInstaller], DetectionResult]]) -> None:
        self.items = list(items)
        self.cursor = 0
        self.selected: List[int] = [idx for idx, (tool, result) in enumerate(self.items[:-1]) if result.found]

    def _row_text(self, idx: int, tool: Optional[ToolInstaller], result: DetectionResult) -> Text:
        is_cursor = idx == self.cursor
        selected = idx in self.selected
        pointer = "➜" if is_cursor else " "
        checkbox = "[■]" if selected else "[ ]"
        label = "Install everywhere" if tool is None else tool.display_name
        status = "detected" if result.found else "not detected"
        status_style = "green" if result.found else "yellow"
        evidence = ", ".join(result.evidence[:2]) if result.evidence else ""

        line = Text()
        line.append(f" {pointer} ", style="bold cyan" if is_cursor else "")
        line.append(checkbox, style="bold green" if selected else "dim")
        line.append(" ")
        line.append(f"{idx + 1}. {label}", style="bold" if result.found else "white")
        line.append("  ")
        line.append(status, style=status_style)
        if evidence:
            line.append(f"  · {evidence}", style="dim")
        return line

    def _draw(self) -> None:
        console.clear()
        header = Panel(
            Text(
                "Agentic coding tools detected. Use the selector to choose where to install the MCP server.",
                style="bold",
            ),
            border_style="cyan",
            title="Tool Selection",
        )
        console.print(header)
        console.print(Panel("Use ↑/↓ to move, space to toggle, enter to confirm, q to cancel", border_style="magenta"))

        body = Text()
        for idx, (tool, result) in enumerate(self.items):
            body.append(self._row_text(idx, tool, result))
            body.append("\n")
        console.print(Panel(body, border_style="white"))

    def _read_key(self) -> str:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            first = sys.stdin.read(1)
            if not first:
                return ""
            if first == "\x03":
                raise KeyboardInterrupt
            if first in ("\r", "\n"):
                return "enter"
            if first == " ":
                return "space"
            if first in ("q", "Q"):
                return "quit"
            if first == "\x1b":
                tail = sys.stdin.read(2)
                if tail == "[A":
                    return "up"
                if tail == "[B":
                    return "down"
            return ""
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def prompt(self) -> List[int]:
        all_idx = len(self.items) - 1
        while True:
            self._draw()
            key = self._read_key()
            if key == "up":
                self.cursor = (self.cursor - 1) % len(self.items)
            elif key == "down":
                self.cursor = (self.cursor + 1) % len(self.items)
            elif key == "space":
                if self.cursor == all_idx:
                    if len(self.selected) == all_idx:
                        self.selected.clear()
                    else:
                        self.selected = list(range(all_idx))
                else:
                    if self.cursor in self.selected:
                        self.selected.remove(self.cursor)
                    else:
                        self.selected.append(self.cursor)
            elif key == "enter":
                if self.cursor == all_idx and len(self.selected) != all_idx:
                    self.selected = list(range(all_idx))
                break
            elif key == "quit":
                self.selected = []
                break
        console.clear()
        return sorted(self.selected)


def wait_for_enter(message: str, interactive: bool) -> None:
    if not interactive:
        return
    console.print(Text(message, style="dim"))
    try:
        console.input("")
    except EOFError:
        pass


def is_subpath(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def ensure_ownership(path: Path, ctx: InstallContext) -> None:
    if not hasattr(os, "chown"):
        return
    for candidate in [path, *path.parents]:
        if not is_subpath(candidate, ctx.home):
            break
        try:
            os.chown(candidate, ctx.target_uid, ctx.target_gid)
        except OSError:
            pass
        if candidate == ctx.home:
            break


def build_env(home: Path) -> Dict[str, str]:
    return {
        "CLAUDE_HOME": str(home / ".claude"),
        "CURSOR_LOGS": str(home / ".cursor-server" / "data" / "logs"),
        "CLAUDE_MCP_CACHE": str(home / ".cache" / "claude-cli-nodejs" / "-home-homeserver" / "mcp-logs-ide"),
        "TMPDIR": "/tmp",
    }


def render_codex_block(ctx: InstallContext) -> str:
    env_inline = ", ".join(f"{k} = \"{v}\"" for k, v in ctx.env.items())
    return (
        f"\n[mcp_servers.{ctx.server_name}]\n"
        f"command = \"{ctx.server_command}\"\n"
        f"args = []\n"
        f"env = {{ {env_inline} }}\n"
    )


def upsert_codex_block(existing: str, name: str, block: str) -> str:
    import re

    pattern = re.compile(rf"^\[mcp_servers\.{re.escape(name)}\]\s*$", re.M)
    match = pattern.search(existing)
    if not match:
        suffix = "\n" if existing and not existing.endswith("\n") else ""
        return existing + suffix + block
    start = match.start()
    remainder = existing[match.end():]
    next_header = re.search(r"^\[.+?\]\s*$", remainder, re.M)
    end = match.end() + (next_header.start() if next_header else len(remainder))
    return existing[:start] + block + existing[end:]


def merge_mcp_json(ctx: InstallContext, path: Path, root_key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_ownership(path.parent, ctx)
    data: Dict[str, object] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            ctx.console.print(f"[yellow]Warning:[/] {path} is not valid JSON; replacing with a fresh MCP configuration.")
            data = {}
    servers = data.get(root_key)
    if not isinstance(servers, dict):
        servers = {}
    servers[ctx.server_name] = {
        "command": ctx.server_command,
        "env": ctx.env,
    }
    data[root_key] = servers
    path.write_text(json.dumps(data, indent=2) + "\n")
    ensure_ownership(path, ctx)


def install_codex(ctx: InstallContext) -> None:
    config_path = ctx.home / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    ensure_ownership(config_path.parent, ctx)
    current = config_path.read_text() if config_path.exists() else ""
    block = render_codex_block(ctx)
    updated = upsert_codex_block(current, ctx.server_name, block)
    config_path.write_text(updated)
    ensure_ownership(config_path, ctx)


def install_claude(ctx: InstallContext) -> None:
    merge_mcp_json(ctx, ctx.home / ".claude" / "mcp.json", root_key="servers")


def install_cursor(ctx: InstallContext) -> None:
    merge_mcp_json(ctx, ctx.home / ".cursor" / "mcp.json", root_key="mcpServers")


def install_gemini(ctx: InstallContext) -> None:
    merge_mcp_json(ctx, ctx.home / ".gemini" / "mcp.json", root_key="servers")


def detect_claude(home: Path) -> DetectionResult:
    evidence: List[str] = []
    for binary in ("claude", "claude-code"):
        path = shutil.which(binary)
        if path:
            evidence.append(f"binary '{binary}' at {path}")
    for rel in (".claude", ".cache/claude-cli-nodejs", ".config/claude"):
        resolved = home / rel
        if resolved.exists():
            evidence.append(f"path {resolved}")
    return DetectionResult(found=bool(evidence), evidence=evidence)


def detect_codex(home: Path) -> DetectionResult:
    evidence: List[str] = []
    for binary in ("codex", "codex-cli"):
        path = shutil.which(binary)
        if path:
            evidence.append(f"binary '{binary}' at {path}")
    config_dir = home / ".codex"
    if config_dir.exists():
        evidence.append(f"path {config_dir}")
    return DetectionResult(found=bool(evidence), evidence=evidence)


def detect_gemini(home: Path) -> DetectionResult:
    evidence: List[str] = []
    for binary in ("gemini", "google-gemini", "gcloud"):
        path = shutil.which(binary)
        if path:
            evidence.append(f"binary '{binary}' at {path}")
    for rel in (".config/gemini", ".local/share/google-gemini"):
        resolved = home / rel
        if resolved.exists():
            evidence.append(f"path {resolved}")
    return DetectionResult(found=bool(evidence), evidence=evidence)


def detect_cursor(home: Path) -> DetectionResult:
    evidence: List[str] = []
    for binary in ("cursor", "cursor-agent"):
        path = shutil.which(binary)
        if path:
            evidence.append(f"binary '{binary}' at {path}")
    for rel in (".cursor", ".cursor-server", "Library/Application Support/Cursor"):
        resolved = home / rel
        if resolved.exists():
            evidence.append(f"path {resolved}")
    return DetectionResult(found=bool(evidence), evidence=evidence)


def require_sudo() -> None:
    if hasattr(os, "geteuid"):
        if os.geteuid() != 0:
            console.print("[bold red]Please rerun with sudo so we can inspect your developer CLI setups:[/] [white]sudo colab-mcp-install[/]")
            sys.exit(1)
    else:
        console.print("[bold red]This installer expects a POSIX environment with sudo available.[/]")
        sys.exit(1)


def get_target_identity() -> Tuple[str, Path, int, int]:
    sudo_user = os.environ.get("SUDO_USER")
    username = sudo_user or os.environ.get("USER") or os.environ.get("USERNAME")
    if not username:
        import getpass

        username = getpass.getuser()
    try:
        record = pwd.getpwnam(username)
    except KeyError:
        record = pwd.getpwuid(os.getuid())
        username = record.pw_name
    home = Path(record.pw_dir)
    return username, home, record.pw_uid, record.pw_gid


def show_welcome(features: Sequence[str]) -> None:
    console.clear()
    console.print(GRADIENT_ASCII)
    console.print()
    body = Text()
    body.append("Welcome to the Covert Labs MCP installer.\n\n", style="bold")
    body.append("This wizard links your agentic CLIs to a shared Colab MCP so you can move work between tools without losing history.\n\n")
    for feature in features:
        body.append(f" • {feature}\n")
    console.print(Panel(body, border_style="cyan", title="Welcome"))


def show_selection_intro() -> None:
    message = Text(
        "We found these agentic coding tools on your system.\n"
        "Next you'll choose which ones should register the MCP server.",
    )
    console.print(Panel(message, border_style="magenta", title="Scan Complete"))


def present_detection(tools: Sequence[ToolInstaller], home: Path) -> List[Tuple[ToolInstaller, DetectionResult]]:
    rows: List[Tuple[ToolInstaller, DetectionResult]] = []
    table = Table(box=box.SIMPLE_HEAVY, title="CLI scan", expand=True)
    table.add_column("Tool")
    table.add_column("Detected", justify="center")
    table.add_column("Evidence")
    for tool in tools:
        result = tool.detection_fn(home)
        rows.append((tool, result))
        status = "[green]yes" if result.found else "[yellow]no"
        evidence = "\n".join(result.evidence) if result.evidence else "--"
        table.add_row(tool.display_name, status, evidence)
    console.print(table)
    return rows


def select_tools(
    detected: Sequence[Tuple[ToolInstaller, DetectionResult]],
    interactive: bool,
) -> List[ToolInstaller]:
    if not interactive:
        return [tool for tool, result in detected if result.found]

    items: List[Tuple[Optional[ToolInstaller], DetectionResult]] = list(detected)
    any_found = any(result.found for _, result in detected)
    all_result = DetectionResult(found=any_found, evidence=["virtual option"])
    items.append((None, all_result))

    menu = SelectionMenu(items)
    indexes = menu.prompt()
    if not indexes:
        console.print("[yellow]Installation cancelled by user.[/]")
        return []

    all_idx = len(items) - 1
    if len(indexes) == all_idx:
        return [tool for tool, _ in detected]

    chosen = [items[i][0] for i in indexes if i < all_idx]
    return [tool for tool in chosen if tool is not None]


def run_installations(selected: Sequence[ToolInstaller], ctx: InstallContext) -> List[Tuple[ToolInstaller, bool, str]]:
    results: List[Tuple[ToolInstaller, bool, str]] = []
    console.clear()
    console.print(Panel("Applying MCP configuration to selected CLIs...", border_style="cyan", title="Installing"))
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("{task.percentage:>3.0f}%"),
        console=console,
        transient=True,
    ) as progress:
        for tool in selected:
            task = progress.add_task(f"{tool.display_name}", total=1)
            try:
                tool.install_fn(ctx)
            except Exception as exc:  # noqa: BLE001
                results.append((tool, False, str(exc)))
            else:
                results.append((tool, True, ""))
            progress.update(task, advance=1)
    return results


def show_results(results: Sequence[Tuple[ToolInstaller, bool, str]]) -> None:
    table = Table(title="Installation summary", box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("Tool")
    table.add_column("Status", justify="center")
    table.add_column("Notes")
    for tool, ok, message in results:
        status = "[green]success" if ok else "[red]failed"
        note = message or "Configured MCP endpoints"
        table.add_row(tool.display_name, status, note)
    console.print(table)


def show_final_instructions(selected: Sequence[ToolInstaller], ctx: InstallContext) -> None:
    instructions = Text(
        "Refresh or restart each CLI so it reloads the MCP server.\n"
        "Run their reload command if available, otherwise exit and relaunch.\n"
        "You can rerun sudo colab-mcp-install anytime to update these entries."
    )
    console.print(Panel(instructions, border_style="green", title="Final steps"))

    tree = Tree("[bold cyan]MCP capabilities[/]")
    server_node = tree.add(f"[bold]{ctx.server_name}[/] (command: {ctx.server_command})")
    env_node = server_node.add("Environment")
    for key, value in ctx.env.items():
        env_node.add(f"{key} = {value}")

    paths = {
        "claude": ctx.home / ".claude" / "mcp.json",
        "codex": ctx.home / ".codex" / "config.toml",
        "gemini": ctx.home / ".gemini" / "mcp.json",
        "cursor": ctx.home / ".cursor" / "mcp.json",
    }
    tools_node = server_node.add("Linked agentic CLIs")
    if selected:
        for tool in selected:
            path = paths.get(tool.key)
            display_path = str(path) if path else "config updated"
            tools_node.add(f"{tool.display_name} → {display_path}")
    else:
        tools_node.add("No CLIs were configured")

    console.print(tree)


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive installer for the Colab MCP across agentic CLIs")
    parser.add_argument("--server-name", default="colab-mcp", help="Server identifier used in each config")
    parser.add_argument("--server-command", default="colab-mcp", help="Command to launch the MCP server")
    parser.add_argument("--yes", action="store_true", help="Run non-interactively with an implicit 'all' selection")
    args = parser.parse_args()

    require_sudo()
    interactive = sys.stdin.isatty() and not args.yes

    target_user, home, uid, gid = get_target_identity()
    ctx = InstallContext(
        console=console,
        home=home,
        server_name=args.server_name,
        server_command=args.server_command,
        env=build_env(home),
        target_user=target_user,
        target_uid=uid,
        target_gid=gid,
    )

    features = (
        "Scan installed CLIs and link them to the shared MCP",
        "Let you hand-pick which tools to configure",
        "Write configs into your user home even when running under sudo",
        "Remind you to refresh each CLI so the MCP server loads",
    )
    show_welcome(features)
    wait_for_enter("Press Enter to start the scan...", interactive)

    console.clear()
    tools: List[ToolInstaller] = [
        ToolInstaller("claude", "Anthropic Claude Code CLI", detect_claude, install_claude, ""),
        ToolInstaller("codex", "OpenAI Codex CLI", detect_codex, install_codex, ""),
        ToolInstaller("gemini", "Google Gemini CLI", detect_gemini, install_gemini, ""),
        ToolInstaller("cursor", "Cursor Agent CLI", detect_cursor, install_cursor, ""),
    ]

    detected = present_detection(tools, home)
    show_selection_intro()
    wait_for_enter("Press Enter to choose which tools to configure...", interactive)

    selected_tools = [tool for tool, _ in detected] if args.yes else select_tools(detected, interactive)
    if not selected_tools:
        return 0

    results = run_installations(selected_tools, ctx)
    wait_for_enter("Press Enter to review the results...", interactive)

    console.clear()
    show_results(results)
    console.print()
    show_final_instructions(selected_tools, ctx)

    failures = [tool for tool, ok, _ in results if not ok]
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        console.print("\n[red]Installer interrupted by user.[/]")
        raise
