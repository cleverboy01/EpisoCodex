---
name: requirements
description: Analyze the codebase and generate a structured REQUIREMENTS.md file with functional requirements, gaps, and technical debt
when_to_use: Use when user asks to document requirements, generate specs, understand what the system does, find missing tests or documentation
short_description: Generate requirements from code
argument_hint: (optional) specific module or directory to analyze
allowed_tools: [read_file, grep, list_dir, write_file]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Requirements Generator Skill

Analyzes existing code to infer and document system requirements.
The code IS the spec — we read it, not guess it.

## Analysis Protocol (Token-Efficient)

### Step 1: Map entry points (2-3 tool calls)
```
1. list_dir(".") → find project type
2. grep "def main\|func main\|export default\|app.listen\|router\." → entry points
3. Read entry point file (line range only, skip imports)
```

### Step 2: Extract public API (grep-based, no full reads)
```
grep "^def \|^class \|^pub fn \|^export function \|^export class " src/ --include="*.py|*.rs|*.ts"
```
→ extract: function names, class names, their docstrings (next line only)

### Step 3: Map to existing tests
```
grep "def test_\|it(\|test(\|#\[test\]" tests/ → list of test names
```
Cross-reference: which public functions have tests? Which don't?

### Step 4: Find error handling gaps
```
grep -n "raise\|throw\|panic!\|unwrap()\|expect(" src/
```
→ identify: functions that can fail but callers may not handle

### Step 5: Check documentation
```
grep -n "\"\"\"$\|///\|//!" src/  → doc comment coverage
```

## Output: agents/requirements/REQUIREMENTS.md
```markdown
# System Requirements
Generated: [timestamp]
Analyzed: [N files, N functions]

## System Overview
[2-paragraph description inferred from entry points + README]

## Functional Requirements (FR)

### Inferred from Code
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| FR-001 | [verb] [noun] when [condition] | file.py:func_name | ✅ Tested |
| FR-002 | [verb] [noun] | file.py:func_name | ⚠️ Untested |
| FR-003 | [verb] [noun] | file.py:func_name | ❌ Undocumented |

## Gap Analysis

### Missing Tests (MT)
| ID | Function | File | Priority |
|----|----------|------|----------|
| MT-001 | auth_user() | src/auth.py | HIGH |

### Missing Documentation (MD)
| ID | Function | File |
|----|----------|------|
| MD-001 | process_payment() | src/payments.py |

### Error Handling Gaps (EH)
| ID | Location | Risk |
|----|----------|------|
| EH-001 | src/db.py:42 | unwrap() on DB connection |

## Technical Debt (TD)
| ID | Description | File | Effort |
|----|-------------|------|--------|
| TD-001 | Function does 3 things (SRP violation) | src/utils.py:parse_and_validate_and_save | Medium |

## Recommended Actions
1. [Priority 1 action]
2. [Priority 2 action]
```

## Token Budget
- Entry point read: ~100 tokens
- grep for all public functions: ~50 tokens
- grep for tests: ~50 tokens
- Output: ~500 tokens
- **Total: ~700 tokens for full project analysis** ← near-zero
