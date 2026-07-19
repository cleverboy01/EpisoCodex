---
name: explain-code
description: Read a file or function and explain what it does in simple terms
when_to_use: Use when the user asks to explain, understand, or document code. Also use for "what does this do?", "how does X work?"
short_description: Explain code clearly
argument_hint: file path or function name to explain
allowed_tools: [read_file, search_replace, list_dir]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Explain Code Skill

Reads and explains code in clear, simple language.

## Steps

1. **Locate the target**: find the file or function specified.
2. **Read it**: use `read_file` to get the content.
3. **Analyze**:
   - What is the purpose/responsibility?
   - What are the inputs and outputs?
   - What are the key algorithms or data flows?
   - What are potential gotchas or edge cases?
4. **Explain** in 3 layers:
   - **One sentence**: the core purpose.
   - **Key steps**: numbered list of what it does.
   - **Details**: any non-obvious logic, patterns, or trade-offs.
5. **Optionally**: add inline comments to the file if user asks.

## Output Format
```
## Purpose
[One sentence]

## How It Works
1. [Step 1]
2. [Step 2]
...

## Key Details
- [Important detail]
- [Edge case or gotcha]
```
