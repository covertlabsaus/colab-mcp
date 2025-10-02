from __future__ import annotations

import argparse
import json
import sys

from .paths import detect_roots
from .services import build_context_bundle, list_session_files, search_across, session_metadata, codex_summary


def _print_json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_list_sessions(args: argparse.Namespace) -> int:
    roots = detect_roots()
    sessions = list_session_files(roots)
    out = []
    for sid in sorted(sessions.keys()):
        md = session_metadata(roots, sid)
        if not md:
            continue
        if args.filter_project and md.project_scope != args.filter_project:
            continue
        out.append({
            "sessionId": md.session_id,
            "project": md.project_scope,
            "first": md.first_ts,
            "last": md.last_ts,
            "messages": md.messages,
            "cwd": md.cwd,
        })
    _print_json(out)
    return 0


def cmd_fetch_transcript(args: argparse.Namespace) -> int:
    roots = detect_roots()
    bundle = build_context_bundle(
        roots,
        session_id=args.session_id,
        limit_chat=args.limit,
        limit_mcp=0 if not args.include_mcp else 50,
        limit_cursor=0 if not args.include_cursor else 100,
        include_chat=not args.no_chat,
        include_mcp=args.include_mcp,
        include_cursor=args.include_cursor,
    )
    if not args.no_chat and "chat" in bundle:
        chat = bundle.get("chat", [])
        bundle["chat"] = chat[args.offset: args.offset + args.limit]
    _print_json(bundle)
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    roots = detect_roots()
    md = session_metadata(roots, args.session_id)
    if not md:
        _print_json({"error": "unknown session"})
        return 1
    _print_json({
        "sessionId": md.session_id,
        "project": md.project_scope,
        "first": md.first_ts,
        "last": md.last_ts,
        "messages": md.messages,
        "cwd": md.cwd,
    })
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    roots = detect_roots()
    res = search_across(roots, query=args.query, scope=args.scope, limit=args.limit)
    _print_json(res)
    return 0


def cmd_codex_status(args: argparse.Namespace) -> int:
    roots = detect_roots()
    res = codex_summary(roots, tail=args.tail)
    _print_json(res)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="colab-mcp-cli", description="Colab MCP CLI helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("list-sessions")
    sp.add_argument("--filter-project")
    sp.set_defaults(func=cmd_list_sessions)

    sp = sub.add_parser("fetch-transcript")
    sp.add_argument("--session-id", required=True)
    sp.add_argument("--offset", type=int, default=0)
    sp.add_argument("--limit", type=int, default=50)
    sp.add_argument("--include-mcp", action="store_true")
    sp.add_argument("--include-cursor", action="store_true")
    sp.add_argument("--no-chat", action="store_true")
    sp.set_defaults(func=cmd_fetch_transcript)

    sp = sub.add_parser("summarize-session")
    sp.add_argument("--session-id", required=True)
    sp.set_defaults(func=cmd_summarize)

    sp = sub.add_parser("search")
    sp.add_argument("--query", required=True)
    sp.add_argument("--scope", choices=["chat", "mcp", "cursor", "all"], default="all")
    sp.add_argument("--limit", type=int, default=50)
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("codex-status")
    sp.add_argument("--tail", type=int, default=200)
    sp.set_defaults(func=cmd_codex_status)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


