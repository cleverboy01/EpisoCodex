# Tools Spec
# Source: xai-grok-tools/src/ (xai-org/grok-build)

## Tool Taxonomy (ToolKind)
Every tool is classified as Read-Only or Mutating:

### Read-Only Tools (no side effects)
| Kind | Presentation Name | Description |
|------|-------------------|-------------|
| `read` | Read | Read file contents |
| `search` | Search | Grep/ripgrep search |
| `list` / `list_dir` | List Files | Directory listing |
| `lsp` | Code Intelligence | LSP hover, goto-def |
| `memory_search` | Memory Search | Semantic search in memory index |
| `memory_get` | Memory Read | Retrieve memory entry |
| `web_search` | Web Search | Search the web |
| `web_fetch` | Web Fetch | Fetch a URL |
| `ask_user` | Ask User | Request user input |
| `enter_plan` / `exit_plan` | Enter/Exit Plan Mode | Mode switching |

### Mutating Tools (require checkpoint before use)
| Kind | Presentation Name | Description |
|------|-------------------|-------------|
| `edit` | Edit | Modify file (search_replace) |
| `write` | Write | Create/overwrite file |
| `delete` | Delete | Remove file |
| `move` | Move | Move/rename file |
| `execute` | Run Command | Shell command via PTY |
| `skill` | Skill | Execute a slash-command skill |
| `task` | Subagent | Spawn a child agent |
| `image_gen` | Generate Image | AI image generation |
| `video_gen` | Generate Video | AI video generation |
| `deploy_app` | Deploy App | Deploy to cloud |
| `background_task_action` | Background Task | Launch background process |
| `goal_update` | Update Goal | Update goal loop state |

## Canonical Tool Meta Envelope
Every tool call carries a `_meta` field under key `"x.ai/tool"`:
```json
{
  "x.ai/tool": {
    "version": 1,
    "name": "read_file",
    "kind": "read",
    "namespace": "grok_build",
    "label": "Read",
    "read_only": true,
    "input": { "path": "/src/main.rs" }
  }
}
```

## Tool Namespaces
- `grok_build`: standard Grok Build toolset
- `grok_build_concise`: compact variant (fewer args)
- `grok_build_hashline`: hash-based line tracking variant
- `codex`: OpenAI Codex compatible
- `opencode`: SST opencode compatible
- `mcp`: external MCP server tools (dynamic)

## Tool Implementation Pattern
```
Tool Definition (JSON Schema)
    → Tool Registry (name → handler mapping)
        → Tool Executor (validates input, calls handler)
            → Handler (performs action, returns result)
                → Result (text/error/tool_result)
```

## Max Payload Size
- `toolInput` or `toolResult`: **128 KB** max.
- Larger payloads are truncated with `[truncated]` suffix.

## Wire Format (canonical input fields)
```
path, offset, limit, command, description, cwd, directory, pattern
```
