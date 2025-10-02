# Installation Guide

Get Colab MCP up and running in 2 minutes.

## Prerequisites

- **Python 3.10+** (check with `python3 --version`)
- **pip** (Python package installer)
- **sudo access** (for the installer to detect tools correctly)
- At least one AI coding assistant installed (Claude Desktop, Cursor, Codex, or Gemini)

## Step 1: Install the Package

```bash
pip install colab-mcp
```

This installs:
- The `colab-mcp` command (the MCP server)
- The `colab-mcp-cli` command (helper CLI for inspecting logs)
- Python package `colab_mcp` you can import if needed

## Step 2: Run the Installer

The easiest way:

```bash
sudo python -m colab_mcp.install
```

Or if you cloned the repo:

```bash
cd colab-mcp
sudo ./install.py
```

### Why sudo?

The installer needs elevated permissions to:
- Detect AI tools installed system-wide
- Write config files to your user home directory with correct ownership
- Scan system paths for binaries

Your data is safe - the installer just reads/writes config files.

## Step 3: Interactive Setup

The installer will:

1. **Scan** for AI coding tools on your system
2. **Show** which ones it found
3. **Let you choose** which ones to configure

Use:
- **↑/↓** to move between options
- **Space** to toggle selection
- **Enter** to confirm
- **Q** to quit

Example output:

```
┌─────────────────────────────────────────────────┐
│                Tool Selection                   │
├─────────────────────────────────────────────────┤
│ Use ↑/↓ to move, space to toggle, enter to     │
│ confirm, q to cancel                            │
└─────────────────────────────────────────────────┘

 ➜ [■] 1. Claude Desktop    detected  · binary 'claude' at /usr/local/bin/claude
   [■] 2. Cursor Agent       detected  · path /home/you/.cursor
   [ ] 3. Codex CLI          not detected
   [ ] 4. Gemini CLI         not detected
   [ ] 5. Install everywhere
```

## Step 4: Restart Your AI Tools

After the installer finishes, you need to restart each AI tool you configured:

### Claude Desktop

```bash
# macOS
killall Claude && open -a Claude

# Linux
pkill claude && claude &
```

Or just quit and reopen the app.

### Cursor

Just restart the editor. File → Quit, then reopen.

### Codex CLI

No restart needed - it reloads config automatically.

### Gemini

Restart the Gemini app or CLI.

## Step 5: Verify It's Working

Open one of your AI tools and try:

> "List my recent coding sessions"

or

> "What was I working on yesterday?"

If you get a response (not an error), it's working! 🎉

## Manual Installation (Advanced)

If you prefer not to use the installer, you can manually edit your MCP configs.

### Claude Desktop

Edit `~/.claude/mcp.json`:

```json
{
  "servers": {
    "colab-mcp": {
      "command": "colab-mcp",
      "env": {
        "CLAUDE_HOME": "/home/yourusername/.claude",
        "CURSOR_LOGS": "/home/yourusername/.cursor-server/data/logs",
        "TMPDIR": "/tmp"
      }
    }
  }
}
```

### Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "colab-mcp": {
      "command": "colab-mcp",
      "env": {
        "CLAUDE_HOME": "/home/yourusername/.claude",
        "CURSOR_LOGS": "/home/yourusername/.cursor-server/data/logs",
        "TMPDIR": "/tmp"
      }
    }
  }
}
```

**Note:** Cursor uses `mcpServers` (camelCase), Claude uses `servers`.

### Codex

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.colab-mcp]
command = "colab-mcp"
args = []
env = { CLAUDE_HOME = "/home/yourusername/.claude", CURSOR_LOGS = "/home/yourusername/.cursor-server/data/logs", TMPDIR = "/tmp" }
```

### Gemini

Edit `~/.gemini/mcp.json`:

```json
{
  "servers": {
    "colab-mcp": {
      "command": "colab-mcp",
      "env": {
        "CLAUDE_HOME": "/home/yourusername/.claude",
        "CURSOR_LOGS": "/home/yourusername/.cursor-server/data/logs",
        "TMPDIR": "/tmp"
      }
    }
  }
}
```

**Remember:** Replace `/home/yourusername` with your actual home directory path.

## Troubleshooting

### "Command not found: colab-mcp"

Make sure pip installed it to a directory in your PATH:

```bash
which colab-mcp
```

If empty, try:

```bash
python3 -m pip install --user colab-mcp
# Then add ~/.local/bin to your PATH
export PATH="$HOME/.local/bin:$PATH"
```

### "Permission denied" errors

Make sure you ran the installer with `sudo`:

```bash
sudo python -m colab_mcp.install
```

### AI tool doesn't see the MCP server

1. Double-check the config file syntax (JSON is picky about commas!)
2. Make sure you restarted the AI tool
3. Check the tool's logs for MCP connection errors

### Still stuck?

Open an issue on [GitHub](https://github.com/yourusername/colab-mcp/issues) with:
- Your OS and Python version
- Which AI tools you're using
- Any error messages

We'll help you out!

## Uninstalling

To remove Colab MCP:

```bash
pip uninstall colab-mcp
```

Then manually remove the `colab-mcp` entries from your AI tool configs.

---

**Next:** Check out [Usage Examples](usage-examples.md) to see what you can do with Colab MCP!

