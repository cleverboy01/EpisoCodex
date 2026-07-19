# Security Spec
# Source: xai-grok-secrets/, xai-grok-telemetry/, xai-grok-auth/ (xai-org/grok-build)

## Secrets Redaction
The `xai-grok-secrets` crate scans content before it leaves the local system.

### What Gets Redacted
```
API Keys:          xai-..., sk-..., AKIA..., ghp_...
Auth Tokens:       Bearer tokens, OAuth access tokens
Private Keys:      -----BEGIN RSA PRIVATE KEY-----, etc.
Passwords:         Common patterns in env vars: PASSWORD=, SECRET=, TOKEN=
DB Connection Strings: postgresql://user:pass@host, mysql://...
AWS Credentials:   aws_access_key_id, aws_secret_access_key
```

### Redaction Pattern
```
[Input: "API_KEY=sk-abc123..."]
      ↓
Secrets Scanner (regex + ML)
      ↓
[Output: "API_KEY=[REDACTED]"]
```

### What is Safe to Include in Context
- File paths, function names, variable names
- Code logic (without hardcoded secrets)
- Error messages (check for embedded tokens first)
- Stack traces (usually safe)

---

## Telemetry Modes
Configure in `config.toml` under `[features] telemetry`:

| Mode | What's Sent | Default |
|------|-------------|---------|
| `false` / `disabled` | Nothing | Enterprise default |
| `session_metrics` | Session lifecycle metadata only (no content) | — |
| `true` / `enabled` | Full telemetry: events, Mixpanel analytics | Consumer default |

### Disable Telemetry
```bash
# Environment variable
export GROK_TELEMETRY_ENABLED=false
export GROK_TELEMETRY_TRACE_UPLOAD=false

# Or in ~/.grok/config.toml
[features]
telemetry = false

[telemetry]
trace_upload = false
```

### Zero Data Retention (ZDR)
Available for enterprise team accounts:
- Enable via xAI team admin console
- When ZDR is on, `/privacy` cannot change coding-data sharing
- Overrides all telemetry settings

---

## Authentication Credential Security

### Storage
- Session tokens: `~/.grok/auth.json`
- MCP OAuth tokens: `~/.grok/mcp_credentials.json`
- Permissions: owner-only (`0600` on Unix / NTFS ACL on Windows)
- DO NOT copy these files to shared directories, tickets, or chat

### Token Refresh
- Automatic before expiry (default: 5 minutes early)
- On 401 Unauthorized: immediate refresh + retry
- OIDC: silent refresh via IdP refresh_token
- External provider: re-runs auth binary with `GROK_AUTH_EXPIRED=1`

### Auth Precedence (highest → lowest)
```
1. Per-model api_key in config.toml [model.<name>]
2. Active session token (from ~/.grok/auth.json)
3. XAI_API_KEY environment variable
```

---

## External OTEL (Enterprise Monitoring)
For self-hosted monitoring without sending data to xAI:
```bash
export GROK_EXTERNAL_OTEL=true
export GROK_OTEL_ENDPOINT=http://localhost:4318  # your OTLP collector
export GROK_OTEL_PROTOCOL=http/protobuf

# Content gates (can be pinned to false by admin)
export GROK_OTEL_LOG_USER_PROMPTS=false   # don't log prompt content
export GROK_OTEL_LOG_TOOL_DETAILS=false   # don't log tool call details
```

---

## Permission System

### Tool Permission Levels
```
read_only:    automatic (no prompt)
mutating:     prompt user (unless acceptEdits or yolo mode)
destructive:  always prompt (delete, shell with dangerous pattern)
```

### Trust Model for Project Hooks
```
Global hooks (~/.grok/hooks/):    always trusted
Project hooks (.grok/hooks/):     require /hooks-trust command
Plugin hooks:                     trusted if plugin is installed
```

### Folder Trust
- Reading files in untrusted folders: allowed but warned
- Executing code in untrusted folders: blocked until trusted
- Trust granted per-folder via `grok trust` or `/trust` command
