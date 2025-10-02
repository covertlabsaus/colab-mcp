# Contributing to Colab MCP

Thanks for your interest in making Colab MCP better! This is a young project and there's lots of room for improvement.

## How to Contribute

### 1. Report Bugs

Found something broken? [Open an issue](https://github.com/yourusername/colab-mcp/issues/new) with:

- **What you expected to happen**
- **What actually happened**
- **Steps to reproduce**
- **Your environment** (OS, Python version, which AI tools you're using)
- **Relevant logs or error messages**

Please search existing issues first to avoid duplicates!

### 2. Request Features

Have an idea? [Open an issue](https://github.com/yourusername/colab-mcp/issues/new) with:

- **The problem you're trying to solve**
- **Your proposed solution**
- **Why this would be useful to others**

Feature discussions are welcome even if you don't plan to implement them yourself.

### 3. Submit Pull Requests

Want to code? Awesome! Here's how:

1. **Fork the repo**
2. **Create a branch** (`git checkout -b feature/your-feature-name`)
3. **Make your changes**
4. **Test them** (at least manually, automated tests coming soon™)
5. **Commit with clear messages** (`git commit -m "Add support for Windsurf IDE"`)
6. **Push to your fork** (`git push origin feature/your-feature-name`)
7. **Open a PR** against `main`

We'll review it and provide feedback!

## Development Setup

### Clone the Repo

```bash
git clone https://github.com/yourusername/colab-mcp.git
cd colab-mcp
```

### Install in Development Mode

```bash
pip install -e .
```

This installs the package in "editable" mode - changes you make to the code take effect immediately.

### Install with Dev Dependencies (if we add them later)

```bash
pip install -e ".[dev]"
```

### Run the Server Locally

```bash
colab-mcp
```

Or directly:

```bash
python -m colab_mcp.main
```

### Test the CLI

```bash
colab-mcp-cli list-sessions
```

## Code Style

We're pretty relaxed, but:

- **Use type hints** where reasonable (`def foo(x: int) -> str:`)
- **Document non-obvious things** (docstrings or comments)
- **Keep it readable** - clarity > cleverness
- **Follow existing patterns** - consistency matters

We use:
- **Black** for formatting (when we set it up)
- **Ruff** for linting (when we set it up)
- **mypy** for type checking (aspirationally)

But honestly, if you submit a PR and it works, we can fix style in review. Don't let perfect be the enemy of good.

## Project Structure

```
colab-mcp/
├── src/colab_mcp/          # Main package
│   ├── main.py             # FastMCP server (the heart)
│   ├── cli.py              # CLI for inspecting logs
│   ├── paths.py            # Path detection logic
│   ├── readers.py          # Log file parsers
│   ├── services.py         # Business logic
│   └── types.py            # Pydantic models
├── install.py              # Interactive installer (Rich TUI)
├── docs/                   # Documentation (you are here)
├── tests/                  # Tests (needs more love)
├── pyproject.toml          # Package config
└── README.md               # Main readme
```

### Key Files to Know

- **`main.py`** - The MCP server. Add new tools/resources here.
- **`readers.py`** - Log parsers. Add support for new AI tools here.
- **`paths.py`** - Path detection. Add new tool paths here.
- **`install.py`** - The installer. Add new tool installers here.

## Areas That Need Help

### High Priority

1. **Add support for more AI tools** (Windsurf, Aider, Cline, etc.)
2. **Improve error handling** (lots of places that could fail more gracefully)
3. **Write tests** (we have one smoke test, need way more)
4. **Windows compatibility** (mostly works but untested)

### Medium Priority

5. **Better search** (semantic search instead of just text matching)
6. **Performance optimization** (caching, indexing for large log sets)
7. **Add more examples** (usage patterns, integration recipes)
8. **CLI improvements** (better output formatting, more commands)

### Low Priority (but cool)

9. **Export functionality** (save transcripts as markdown/PDF)
10. **Web UI** (browse sessions in a browser)
11. **Real-time sync** (watch log files for changes)
12. **Cross-session linking** (connect related conversations)

Pick something that sounds fun!

## Adding Support for a New AI Tool

Let's say you want to add support for "Windsurf IDE". Here's the process:

### 1. Add Path Detection

In `paths.py`:

```python
def detect_windsurf_logs() -> Optional[Path]:
    """Detect Windsurf log directory."""
    home = Path.home()
    candidates = [
        home / ".windsurf" / "logs",
        home / ".config" / "windsurf" / "logs",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None
```

### 2. Add Log Reader (if needed)

If Windsurf has a custom log format, add a parser in `readers.py`:

```python
def read_windsurf_logs(log_path: Path) -> Generator[WindsurfEvent, None, None]:
    """Parse Windsurf log files."""
    for line in log_path.read_text().splitlines():
        # Parse however Windsurf formats its logs
        yield WindsurfEvent(...)
```

### 3. Add to Service Layer

In `services.py`, integrate it into `list_session_files()` or relevant functions:

```python
windsurf_logs = detect_windsurf_logs()
if windsurf_logs:
    for log_file in windsurf_logs.glob("*.log"):
        # Process log files
        pass
```

### 4. Add to Installer

In `install.py`:

```python
def detect_windsurf(home: Path) -> DetectionResult:
    evidence: List[str] = []
    if shutil.which("windsurf"):
        evidence.append("binary 'windsurf' found")
    if (home / ".windsurf").exists():
        evidence.append(f"path {home / '.windsurf'}")
    return DetectionResult(found=bool(evidence), evidence=evidence)

def install_windsurf(ctx: InstallContext) -> None:
    merge_mcp_json(
        ctx, 
        ctx.home / ".windsurf" / "mcp.json", 
        root_key="servers"  # or whatever Windsurf uses
    )

# Add to the tools list in main():
tools.append(
    ToolInstaller(
        "windsurf",
        "Windsurf IDE",
        detect_windsurf,
        install_windsurf,
        "Windsurf IDE support"
    )
)
```

### 5. Test It

1. Install Windsurf (or fake it with empty directories)
2. Run `sudo ./install.py`
3. Make sure it detects and configures correctly
4. Verify the MCP server can read Windsurf logs

### 6. Submit a PR

With:
- Your changes
- A brief description of what you added
- Any testing you did

Done! 🎉

## Communication

- **GitHub Issues** for bugs and features
- **Pull Requests** for code changes
- **Discussions** (if we enable them) for questions and ideas

## License

By contributing, you agree your code will be licensed under MIT (same as the project).

## Recognition

Contributors will be:
- Added to the README
- Credited in release notes
- Forever enshrined in git history

Not much, but it's honest work. 😊

---

Thanks for making Colab MCP better! 🙌

