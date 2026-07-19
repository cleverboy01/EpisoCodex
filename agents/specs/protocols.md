# Protocols Spec
# Source: xai-acp-lib/, xai-grok-mcp/ (xai-org/grok-build)

## Agent Client Protocol (ACP)
ACP is xAI's protocol for connecting external editors (VS Code, Neovim, JetBrains)
to the Grok agent runtime.

### ACP Architecture
```
Editor / IDE                    Grok Agent Runtime
┌──────────────┐   ACP (JSON)   ┌─────────────────────┐
│ ACP Client   │◄──────────────►│ ACP Gateway          │
│ (extension)  │   over stdio   │ (xai-acp-lib)        │
└──────────────┘   or TCP/Unix  └──────────┬──────────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Session Actor│
                                    │ (MvpAgent)  │
                                    └─────────────┘
```

### ACP Message Flow
```
Client → Gateway: { "type": "create_session", "model": "grok-3" }
Gateway → Client: { "type": "session_created", "session_id": "abc" }

Client → Gateway: { "type": "prompt", "session_id": "abc", "text": "refactor this" }
Gateway → Client: { "type": "text_chunk", "content": "I'll start by..." }
Gateway → Client: { "type": "tool_call", "tool": "read_file", "input": {...} }
Gateway → Client: { "type": "tool_result", "output": "..." }
Gateway → Client: { "type": "turn_end", "reason": "stop" }
```

### ACP AuthMethod
```
auth_method_id: identifies which credentials are used
  - oauth_session: browser-based login token
  - api_key: XAI_API_KEY environment variable
  - external_provider: custom auth binary
```

---

## Model Context Protocol (MCP)
MCP is an open standard for connecting AI agents to external tools and data sources.
Allows any tool/database/API to be exposed to the agent without code changes.

### MCP Architecture
```
Agent (MCP Client)              MCP Server (any language)
┌──────────────────┐  JSON-RPC  ┌──────────────────────────┐
│ xai-grok-mcp     │◄──────────►│ Your tool server         │
│ (MCP client impl)│  over HTTP │ (SQLite, GitHub API, etc)│
└──────────────────┘  or stdio  └──────────────────────────┘
```

### MCP Server Config (config.toml)
```toml
[[mcpServers]]
name = "github"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env = { GITHUB_TOKEN = "${GITHUB_TOKEN}" }

[[mcpServers]]
name = "postgres"
command = "uvx"
args = ["mcp-server-postgres", "postgresql://localhost/mydb"]
```

### MCP Tool Calling
- Tools from MCP servers appear in the agent's toolset as `server__tool_name`
- Agent calls them exactly like built-in tools
- Namespace: `mcp` in canonical tool meta
- Discovery: agent queries `tools/list` on server startup

### MCP OAuth
- Credentials stored in `~/.grok/mcp_credentials.json`
- Permissions: owner-only (`0600`)
- Tokens refreshed automatically

---

## Plugin System
Plugins extend the agent with bundled skills, hooks, and config.

### Plugin Structure
```
~/.grok/plugins/<plugin-name>/
  ├── manifest.json     # metadata, version, permissions
  ├── skills/           # skill .md files
  │   └── my-skill/
  │       └── SKILL.md
  └── hooks/            # hook JSON files
      └── my-hook.json
```

### Plugin Skill Namespace
Plugin skills are keyed as `plugin:<plugin-name>:<skill-name>` to prevent
collision with user/repo skills. Same-scope resolution uses directory basename.

### Plugin Variables in Skills
```
${CLAUDE_PLUGIN_ROOT}  → plugin installation directory
${CLAUDE_PLUGIN_DATA}  → plugin data directory (persistent storage)
```
