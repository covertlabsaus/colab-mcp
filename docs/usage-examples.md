# Usage Examples

Real-world scenarios showing how Colab MCP helps your workflow.

## Scenario 1: Picking Up Where You Left Off

### The Problem

It's Friday evening. You've been working on a new authentication feature with Claude Code. You make good progress but don't finish. Monday morning, you open Cursor to continue coding, but you've forgotten some of the design decisions you made.

### With Colab MCP

Open Cursor and ask:

> "What did I discuss with Claude about authentication on Friday?"

Your AI assistant:
1. Calls `list_sessions()` to find Friday's sessions
2. Calls `fetch_transcript()` to get the conversation
3. Summarizes the key decisions you made
4. You're back in context in 30 seconds instead of 30 minutes

### What You'd Say

> "Check my last session from Friday and tell me what approach we decided on for user authentication"

## Scenario 2: Debugging Across Tools

### The Problem

You're debugging a weird error. You tried fixing it in Claude Code, then switched to Cursor, then ran some terminal commands with Codex. Now you can't remember what you already tried.

### With Colab MCP

Ask any AI tool:

> "Search my logs for 'connection timeout' from today"

Your AI assistant:
1. Calls `search_logs(query="connection timeout", scope="all")`
2. Finds mentions across chat, IDE logs, and terminal history
3. Shows you exactly what you already tried
4. You don't waste time repeating failed solutions

### What You'd Say

> "What have I already tried to fix this connection timeout error?"

## Scenario 3: Team Handoff

### The Problem

You're handing off a feature to a teammate. You need to explain what you've built, what works, what doesn't, and what's left to do.

### With Colab MCP

Instead of writing a novel in Slack:

> "Summarize all my sessions working on the payment integration feature"

Your AI assistant:
1. Calls `list_sessions(filter_project="payment-integration")`
2. Calls `summarize_session()` for each one
3. Generates a structured summary of:
   - What was implemented
   - What issues came up
   - What decisions were made
   - What's still TODO
4. You share the summary instead of typing it all out

### What You'd Say

> "Give me a summary of all the work I've done on the payment integration this week"

## Scenario 4: Learning from Past Mistakes

### The Problem

You vaguely remember solving a similar problem 3 weeks ago. But which session was it? What was the solution?

### With Colab MCP

Ask:

> "Search my chat history for discussions about rate limiting"

Your AI assistant:
1. Calls `search_logs(query="rate limiting", scope="chat")`
2. Finds the relevant conversation from 3 weeks ago
3. Shows you the solution you used
4. You apply the same pattern instead of reinventing it

### What You'd Say

> "I remember talking about rate limiting before. What did we decide?"

## Scenario 5: Context-Aware Code Review

### The Problem

You're using Gemini to review some code you wrote. But Gemini doesn't know the constraints and requirements you discussed with Claude earlier.

### With Colab MCP

Prime your AI with context:

> "Before reviewing this code, check my session from this morning where I discussed the requirements for this feature"

Your AI assistant:
1. Fetches the relevant session
2. Understands the constraints you're working with
3. Reviews the code with full context
4. Gives better, more relevant feedback

### What You'd Say

> "Review this code, but first check what requirements I discussed in my last session"

## Scenario 6: Terminal History Inspection

### The Problem

You ran a bunch of terminal commands earlier. Some worked, some didn't. Now you can't remember which ones were successful.

### With Colab MCP

Ask:

> "What commands did I run in the terminal in the last hour?"

Your AI assistant:
1. Calls `codex_status()` to get recent terminal activity
2. Shows you the command history with timestamps
3. You see exactly what you did

### What You'd Say

> "Show me my terminal history from today"

## Common Prompts That Just Work

Once you have Colab MCP installed, these prompts become useful:

### Session Management

- "List my recent coding sessions"
- "What was I working on yesterday?"
- "Show me sessions from last week about the API refactor"
- "Summarize my last 3 sessions"

### Search & Discovery

- "Search my logs for 'database migration'"
- "Find discussions about authentication"
- "What errors have I encountered today?"
- "Search my chat history for React best practices"

### Context Retrieval

- "What did I discuss in my session from Monday morning?"
- "Get the transcript of my last session"
- "What decisions did I make about the architecture?"
- "What was the context from my previous conversation?"

### Tool-Specific

- "What Cursor errors did I encounter this morning?"
- "Show me recent Codex activity"
- "What files was I editing in my last Cursor session?"

## Advanced: Direct CLI Usage

For power users, you can use `colab-mcp-cli` directly:

```bash
# List all sessions
colab-mcp-cli list-sessions

# Get session metadata
colab-mcp-cli summarize-session --session-id abc123

# Fetch full transcript
colab-mcp-cli fetch-transcript --session-id abc123 --limit 50

# Search logs
colab-mcp-cli search-logs --query "authentication" --scope chat

# Check Codex status
colab-mcp-cli codex-status --tail 100
```

Output is JSON, so you can pipe it to `jq`:

```bash
colab-mcp-cli list-sessions | jq '.[] | select(.project == "my-app")'
```

## Tips & Tricks

### 1. Use Specific Time References

Instead of:
> "What was I working on recently?"

Try:
> "What was I working on yesterday afternoon?"

More specific = better results.

### 2. Mention the Tool

If you know which tool you used:
> "Check my Cursor session from this morning"

This helps narrow down the search.

### 3. Combine with Context

You can reference past work in your prompts:
> "Check my session from yesterday about authentication, then help me implement the login flow we discussed"

### 4. Search Before Asking

If you can't remember the details:
> "Search my logs for discussions about performance optimization, then summarize what we decided"

### 5. Use Filters

When you have lots of sessions:
> "List sessions from the last 7 days related to the API project"

## What Doesn't Work (Yet)

Some things that would be cool but aren't implemented yet:

- ❌ Cross-session conversation threads
- ❌ Semantic search (it's text search only right now)
- ❌ Automatic context injection (you have to ask for it)
- ❌ Real-time sync between tools (they read logs on demand)
- ❌ Export to markdown/PDF

PRs welcome! 😊

---

**Next:** Want to contribute? Check out [Contributing](contributing.md)!

