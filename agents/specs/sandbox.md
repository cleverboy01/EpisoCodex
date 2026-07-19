# Sandbox Spec
# Source: xai-grok-sandbox/src/ (xai-org/grok-build)

## Purpose
Execute agent-generated code in an isolated environment to prevent:
- Accidental system damage (`rm -rf /`, `sudo` abuse)
- Runaway processes consuming all resources
- Unauthorized network access
- Leaking host environment variables

## Sandbox Layers (Defense in Depth)
```
Layer 1: Hook Guard (PreToolUse)     → blocks obvious destructive patterns
Layer 2: Permission System           → user-approved tool allowlist
Layer 3: Process Sandbox             → OS-level isolation
Layer 4: Workspace Checkpoint        → rollback on failure
```

## Permission Modes
- `default`: standard Grok permission prompts for destructive ops
- `acceptEdits`: auto-approve file edits, still prompt for shell
- `bypassPermissions` / `yolo`: skip all confirmations (dangerous!)
- `ask`: always prompt (most conservative)

## Process Isolation
On supported platforms, shell commands run inside a sandboxed subprocess:
- **macOS**: `sandbox-exec` profile restricts file system and network
- **Linux**: `seccomp` / `bubblewrap` namespace isolation
- **Windows**: Job objects for resource limits (best-effort)

## Worktree Isolation (for Subagents)
Full filesystem isolation via git worktree:
```
parent_cwd/           → parent works here
parent_cwd/.worktrees/
  └── subagent-abc/   → subagent isolated here
      ├── (full copy of working tree)
      └── (deleted on completion, or snapshotted to git ref)
```

## Resource Limits
- Process timeout: configurable per tool call
- Memory: OS-level via Job objects / cgroups
- Network: blocked by default in strict mode

## Safe Patterns for Code Execution
```
# Always:
1. Validate command before execution (hook guard)
2. Run in restricted cwd, not system root
3. Set timeout on all subprocesses
4. Capture both stdout and stderr
5. Check exit code before treating as success

# For untrusted code:
6. Use worktree isolation (subagent with isolation=worktree)
7. Enable sandbox-exec/seccomp
8. Disable network if not needed
```

## Checkpoint Before Execution
```
before_mutating_operation():
    checkpoint = git_stash() or file_snapshot()
    try:
        result = execute()
    except:
        restore(checkpoint)
        raise
```

## Dangerous Patterns to Block
```bash
rm -rf /                    # wipe filesystem
rm -rf /*                   # wipe filesystem
sudo rm -rf                 # elevated wipe
dd if=/dev/zero of=/dev/sd* # overwrite disk
mkfs.*                      # format disk
:(){ :|:& };:               # fork bomb
> /etc/passwd               # overwrite critical system file
chmod -R 777 /              # permission bomb
```
