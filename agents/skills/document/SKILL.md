---
name: document
description: Add or improve documentation for code (docstrings, README, API docs, inline comments)
when_to_use: Use when user asks to document, add docstrings, write README, or improve code comments
short_description: Write documentation
argument_hint: file or module to document
allowed_tools: [read_file, grep, list_dir, search_replace, write_file]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Document Skill

Adds clear, accurate documentation to code.

## Documentation Types

### Docstrings (function/class level)
```python
def authenticate(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.
    
    Args:
        username: The user's login name (case-insensitive).
        password: Plain-text password (will be hashed internally).
    
    Returns:
        User object if credentials are valid, None if authentication fails.
    
    Raises:
        DatabaseError: If the user database is unavailable.
    
    Example:
        user = authenticate("alice", "hunter2")
        if user is None:
            return redirect("/login")
    """
```

### README sections
- **What it does** (one paragraph, non-technical first)
- **Quick start** (code that works in < 5 minutes)
- **Configuration** (all env vars and config options)
- **API reference** (if a library)
- **Contributing** (if open source)

### Inline comments
- Comment WHY not WHAT (code shows what; comment explains intent)
- Comment non-obvious algorithms, business rules, workarounds
- Remove stale comments that no longer match the code

## Protocol
1. Read the target file completely
2. Understand what each public function/class does
3. Write documentation that a new team member could use
4. Check for existing docs that need updating (not just adding new ones)
5. Verify docstrings match actual behavior (parameters, return types, exceptions)
