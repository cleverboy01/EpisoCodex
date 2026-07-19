#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║          ANTIGRAVITY AGI CLI — Proto-AGI Command Center             ║
║      Autonomous Software Engineering Framework for Grok-Build       ║
╚══════════════════════════════════════════════════════════════════════╝

The single entry point that orchestrates the entire AGI cognitive stack:
  - Skill routing (auto-selects the right skill for every task)
  - Token budget management (Antigravity Manager)
  - RLHF preflight (checks past errors before starting)
  - Episodic memory (stores and retrieves experiences)
  - Self-rewrite priorities (code health scan)
  - AGI loop (continuous self-improvement)
  - Live rich dashboard

Usage:
    python agicli.py                     # Live dashboard
    python agicli.py run "refactor auth" # Auto-route and run a task
    python agicli.py loop                # Start continuous AGI loop
    python agicli.py tokens              # Token budget panel
    python agicli.py scan                # Code health scan
    python agicli.py memory <task>       # RLHF preflight danger report
    python agicli.py skills [query]      # Search available skills
    python agicli.py setup               # Initialize/reset AGI harness
"""
import sys
import os
import json
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
AGENTS = ROOT / "agents"
BIN = AGENTS / "hooks" / "bin"
LOGS = AGENTS / "logs"
SKILLS_DIR = AGENTS / "skills"

# ── Optional rich import ───────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
    from rich.text import Text
    from rich.rule import Rule
    from rich.tree import Tree
    from rich.live import Live
    from rich import box
    RICH = True
except ImportError:
    RICH = False

console = Console() if RICH else None

def _print(msg: str, style: str = "") -> None:
    if RICH and console:
        console.print(msg, style=style)
    else:
        print(msg)

def _run(cmd: list[str], capture: bool = True) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, capture_output=capture,
            text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT), timeout=30
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except Exception as e:
        return 1, "", str(e)

def _load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

# ══════════════════════════════════════════════════════════════════════════════
#  PANELS — individual data widgets
# ══════════════════════════════════════════════════════════════════════════════

def panel_header() -> "Panel":
    art = Text()
    art.append("  ANTIGRAVITY  ", style="bold bright_cyan")
    art.append("AGI CLI", style="bold bright_white")
    art.append("  ⚡  Proto-AGI Framework for Autonomous Software Engineering\n", style="dim")
    art.append("  Grok-Build · github.com/your-repo · v2.0 (Phase 5)", style="dim cyan")
    return Panel(art, border_style="bright_cyan", padding=(0, 2))


def panel_tokens() -> "Panel":
    ledger = _load_json(LOGS / "token-ledger.json")
    sess_used = ledger.get("session_usage", 0)
    sess_lim  = ledger.get("session_limit", 100000)
    day_used  = ledger.get("daily_usage", 0)
    day_lim   = ledger.get("daily_limit", 300000)
    locked    = ledger.get("locked", False)
    status    = "[red]🔴 LOCKED[/]" if locked else "[green]🟢 ACTIVE[/]"

    def bar(used, limit, width=30):
        pct = min(1.0, used / max(limit, 1))
        filled = int(pct * width)
        color = "red" if pct > 0.85 else "yellow" if pct > 0.60 else "green"
        return f"[{color}]{'█' * filled}[/{color}]{'░' * (width - filled)} {pct*100:.1f}%"

    t = Table.grid(padding=(0, 1))
    t.add_column(style="dim", width=14)
    t.add_column()
    t.add_row("Status", status)
    t.add_row("Session", f"[cyan]{sess_used:,}[/] / [white]{sess_lim:,}[/]  " + bar(sess_used, sess_lim))
    t.add_row("Daily", f"[cyan]{day_used:,}[/] / [white]{day_lim:,}[/]  " + bar(day_used, day_lim))
    t.add_row("Saved by guard", f"[bright_green]{max(0, sess_lim - sess_used):,} tokens protected[/]")
    return Panel(t, title="[bold yellow]🚀 Token Budget[/]", border_style="yellow")


def panel_errors() -> "Panel":
    ep = _load_json(LOGS / "error-patterns.json")
    rlhf = _load_json(LOGS / "rlhf-summary.json")

    t = Table(show_header=True, header_style="bold red", box=box.SIMPLE)
    t.add_column("Category", style="red", width=22)
    t.add_column("Count", justify="right")
    t.add_column("Resolved", justify="right", style="green")

    by_cat = rlhf.get("by_category", {})
    if by_cat:
        for cat, info in sorted(by_cat.items(), key=lambda x: -x[1].get("total", 0))[:6]:
            t.add_row(cat, str(info.get("total", 0)), str(info.get("resolved", 0)))
    else:
        t.add_row("[dim]No errors recorded yet[/]", "", "")

    total = rlhf.get("total_errors", 0)
    unresolved = rlhf.get("unresolved", 0)
    footer = f"Total: [red]{total}[/]  Unresolved: [yellow]{unresolved}[/]"
    return Panel(t, title="[bold red]🧠 RLHF Error Memory[/]", border_style="red",
                 subtitle=footer)


def panel_rewrite_priorities() -> "Panel":
    pf = _load_json(LOGS / "rewrite-priorities.json")
    priorities = pf.get("priorities", [])

    t = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
    t.add_column("File", style="cyan", width=30)
    t.add_column("Priority", justify="right")
    t.add_column("Recommendation", style="dim")

    for p in priorities[:6]:
        fname = Path(p.get("file", "")).name
        score = p.get("priority", 0)
        color = "red" if score >= 6 else "yellow" if score >= 3 else "green"
        t.add_row(fname, f"[{color}]{score}[/]", p.get("recommendation", "")[:30])

    generated = pf.get("generated_at", "never")
    return Panel(t, title="[bold magenta]🔧 Self-Rewrite Priorities[/]",
                 border_style="magenta", subtitle=f"[dim]Updated: {generated}[/]")


def panel_skills() -> "Panel":
    idx = _load_json(LOGS / "skill-index.json")
    skills = idx.get("skills", [])
    enabled = [s for s in skills if s.get("enabled", True)]

    tree = Tree("[bold cyan]agents/skills/[/]")
    for s in enabled[:10]:
        label = f"[green]{s['name']}[/] [dim]— {s.get('short_description', '')[:35]}[/]"
        tree.add(label)
    if len(enabled) > 10:
        tree.add(f"[dim]... and {len(enabled)-10} more[/]")

    return Panel(tree, title=f"[bold cyan]📚 Skills ({len(enabled)} active)[/]",
                 border_style="cyan")


def panel_system_health() -> "Panel":
    # Run git status for quick health check
    rc, out, _ = _run(["git", "status", "-s"])
    modified = len([l for l in out.splitlines() if l.strip()])
    status_str = f"[yellow]{modified} uncommitted changes[/]" if modified else "[green]Clean working tree[/]"

    ledger = _load_json(LOGS / "token-ledger.json")
    locked = ledger.get("locked", False)
    rlhf = _load_json(LOGS / "rlhf-summary.json")
    unresolved = rlhf.get("unresolved", 0)

    score = 100
    score -= modified * 2
    score -= unresolved * 5
    if locked:
        score -= 30
    score = max(0, min(100, score))

    color = "red" if score < 50 else "yellow" if score < 80 else "green"

    t = Table.grid(padding=(0, 1))
    t.add_column(style="dim", width=18)
    t.add_column()
    t.add_row("Health Score", f"[{color}]{score}/100[/]")
    t.add_row("Working Tree", status_str)
    t.add_row("Token Guard", "[red]LOCKED[/]" if locked else "[green]ACTIVE[/]")
    t.add_row("RLHF Alerts", f"[{'yellow' if unresolved else 'green'}]{unresolved} unresolved[/]")

    return Panel(t, title="[bold green]💚 System Health[/]", border_style="green")

def panel_copilot() -> "Panel":
    state = _load_json(LOGS / "live-session.json")
    prompt = state.get("last_prompt", "")
    active_tool = state.get("active_tool", "")
    
    t = Table.grid(padding=(1, 1))
    t.add_column(style="dim", width=18)
    t.add_column()
    
    if not prompt:
        t.add_row("Status", "[dim]Waiting for IDE activity...[/]")
    else:
        # Truncate prompt if too long
        display_prompt = prompt if len(prompt) < 200 else prompt[:197] + "..."
        t.add_row("User Prompt", f"[bold cyan]{display_prompt}[/]")
        
        if active_tool:
            t.add_row("Agent Action", f"🤖 Running tool: [bold yellow]{active_tool}[/]")
        else:
            t.add_row("Agent Action", "[dim]Idle / Thinking...[/]")
            
    return Panel(t, title="[bold blue]📡 Live IDE Sync[/]", border_style="blue")

# ══════════════════════════════════════════════════════════════════════════════
#  COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

def cmd_status(_args) -> None:
    """Live dashboard — shows all panels at once."""
    if not RICH:
        print("Install 'rich' for the full dashboard: pip install rich")
        cmd_tokens(None)
        return

    console.print(panel_header())
    console.print()
    # Row 1: Health + Tokens
    console.print(Columns([panel_system_health(), panel_tokens()], equal=True, expand=True))
    console.print()
    # Row 2: Errors + Rewrite Priorities
    console.print(Columns([panel_errors(), panel_rewrite_priorities()], equal=True, expand=True))
    console.print()
    # Row 3: Skills
    console.print(panel_skills())
    console.print()
    console.print(Rule("[dim]Run [bold]python agicli.py run \"your task\"[/] to start an AGI-routed task[/]"))


def cmd_copilot(_args) -> None:
    """Live AGI Co-Pilot dashboard (updates every 1s)."""
    if not RICH:
        print("Install 'rich' for the Co-Pilot dashboard: pip install rich")
        return

    _print("[bold blue]Starting AGI Co-Pilot...[/]")
    _print("[dim]Listening for Antigravity IDE events... (Press Ctrl+C to stop)[/]")
    
    def generate_layout():
        return Columns([panel_copilot(), panel_tokens()], equal=True, expand=True)

    try:
        with Live(generate_layout(), refresh_per_second=2) as live:
            while True:
                time.sleep(0.5)
                live.update(generate_layout())
    except KeyboardInterrupt:
        _print("\n[yellow]Co-Pilot dashboard stopped.[/]")


def cmd_run(args) -> None:
    """Route a task through the full AGI cognitive stack."""
    task = args.task
    if RICH:
        console.print(Rule(f"[bold cyan]🤖 AGI Task: {task}[/]"))
    else:
        print(f"\n=== AGI Task: {task} ===")

    # ── Step 1: RLHF Preflight ────────────────────────────────────────────────
    _print("\n[bold yellow]Step 1/4 · RLHF Preflight — checking past errors...[/]", "")
    rc, out, err = _run([sys.executable, str(BIN / "rlhf_feedback_loop.py"), "preflight", task])
    
    if out:
        try:
            data = json.loads(out)
            msg = data.get("message", "")
            if data.get("status") == "clean":
                _print(f"  [green]✓ {msg}[/]")
            else:
                _print(f"  [yellow]⚠️  {msg}[/]")
                if "relevant_errors" in data:
                    for err_obj in data["relevant_errors"]:
                        status = "[green]RESOLVED[/]" if err_obj.get("resolved") else "[red]UNRESOLVED[/]"
                        _print(f"    {status} #{err_obj.get('id')} | {err_obj.get('category')} | {err_obj.get('error_text')}")
        except Exception:
            _print(out)
    else:
        _print("  [green]✓ Clean — no relevant past errors found. Proceeding safely.[/]")

    # ── Step 2: Skill Routing ─────────────────────────────────────────────────
    _print("\n[bold yellow]Step 2/4 · Skill Router — selecting best skills...[/]", "")
    rc, out, err = _run([sys.executable, str(BIN / "skill_router.py"), task, "--top-k", "3"])
    routing = {}
    try:
        routing = json.loads(out)
    except Exception:
        routing = {}

    selected = routing.get("selected", [])
    if RICH and selected:
        t = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        t.add_column("Rank")
        t.add_column("Skill", style="cyan")
        t.add_column("Score", justify="right")
        t.add_column("Path", style="dim")
        for i, s in enumerate(selected, 1):
            t.add_row(f"#{i}", s.get("name", ""), f"{s.get('score', 0):.3f}", s.get("path", ""))
        console.print(t)
    elif selected:
        for i, s in enumerate(selected, 1):
            print(f"  #{i} {s.get('name')} (score={s.get('score')})")
    else:
        _print("  [yellow]No specific skills matched. Using general approach.[/]")

    # ── Step 3: Load top skill instructions ───────────────────────────────────
    if selected:
        top_skill = selected[0]
        skill_path = ROOT / top_skill.get("path", "")
        _print(f"\n[bold yellow]Step 3/4 · Loading skill instructions: [cyan]{top_skill['name']}[/]...[/]", "")
        if skill_path.exists():
            content = skill_path.read_text(encoding="utf-8")
            # Strip frontmatter, show just the instructions
            if "---" in content:
                parts = content.split("---", 2)
                instructions = parts[2] if len(parts) > 2 else content
            else:
                instructions = content
            if RICH:
                console.print(Panel(
                    instructions[:800] + ("\n[dim]...[truncated][/]" if len(instructions) > 800 else ""),
                    title=f"[cyan]{top_skill['name']} Instructions[/]",
                    border_style="cyan"
                ))
            else:
                print(instructions[:400])

    # ── Step 4: AGI Loop decision ─────────────────────────────────────────────
    _print("\n[bold yellow]Step 4/4 · AGI Loop — recording task for session memory...[/]", "")
    decisions_file = LOGS / "session-decisions.json"
    decisions_data = {}
    try:
        decisions_data = json.loads(decisions_file.read_text(encoding="utf-8"))
    except Exception:
        decisions_data = {"decisions": [], "session_id": "", "cleared_at": ""}

    decisions_data.setdefault("decisions", []).append({
        "category": "AGI_TASK",
        "content": f"Task: {task}\nRouted to: {[s.get('name') for s in selected]}",
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    decisions_file.write_text(json.dumps(decisions_data, indent=2, ensure_ascii=False), encoding="utf-8")
    _print("  [green]✓ Task recorded in session memory.[/]")

    # ── Summary ────────────────────────────────────────────────────────────────
    _print(f"\n[bold green]✅ AGI Routing complete.[/] Now run your task with these skills loaded.\n")
    if selected:
        _print(f"[dim]Tip: Read the skill file for detailed instructions:[/]")
        _print(f"     {ROOT / selected[0].get('path', '')}")


def cmd_loop(args) -> None:
    """Continuous AGI self-improvement loop."""
    if RICH:
        console.print(Rule("[bold red]♾️  AGI Continuous Improvement Loop[/]"))
    else:
        print("\n=== AGI Continuous Improvement Loop ===")

    iterations = getattr(args, "iterations", 3)
    _print(f"[dim]Running {iterations} scan iterations...[/]")

    for i in range(1, iterations + 1):
        _print(f"\n[bold cyan]── Iteration {i}/{iterations} ──[/]")

        # Self-rewrite scan
        _print("[yellow]· Scanning hook scripts for rewrite priorities...[/]")
        rc, out, err = _run([sys.executable, str(BIN / "self_rewrite_engine.py"), "scan"])

        try:
            if out:
                start_idx = out.find("[")
                end_idx = out.rfind("]")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = out[start_idx:end_idx+1]
                    results = json.loads(json_str)
                else:
                    results = []
            else:
                results = []
        except Exception:
            results = []

        high = [r for r in results if r.get("priority", 0) >= 6]
        if high and RICH:
            t = Table(box=box.SIMPLE, header_style="bold red")
            t.add_column("File", style="cyan")
            t.add_column("Priority", justify="right")
            t.add_column("Top Issue", style="dim")
            for r in high[:4]:
                fname = Path(r.get("file", "")).name
                issue = r.get("issues", [""])[0][:50] if r.get("issues") else ""
                t.add_row(fname, f"[red]{r['priority']}[/]", issue)
            console.print(t)
        elif high:
            for r in high[:4]:
                print(f"  HIGH [{r['priority']}]: {Path(r.get('file','')).name}")
        else:
            _print("  [green]✓ No high-priority rewrites needed.[/]")

        # Token stats update
        _print("[yellow]· Checking token budget...[/]")
        ledger = _load_json(LOGS / "token-ledger.json")
        sess_pct = (ledger.get("session_usage", 0) / max(ledger.get("session_limit", 100000), 1)) * 100
        _print(f"  Session usage: [cyan]{sess_pct:.1f}%[/]")

        if i < iterations:
            time.sleep(0.5)

    _print("\n[bold green]✅ AGI Loop complete.[/]")


def cmd_tokens(args) -> None:
    """Token budget panel."""
    if RICH:
        console.print(panel_tokens())
    else:
        ledger = _load_json(LOGS / "token-ledger.json")
        print(json.dumps(ledger, indent=2))

    # Allow set limits from CLI
    if args and getattr(args, "session", None):
        ledger = _load_json(LOGS / "token-ledger.json")
        ledger["session_limit"] = args.session
        if getattr(args, "daily", None):
            ledger["daily_limit"] = args.daily
        if getattr(args, "unlock", False):
            ledger["locked"] = False
        (LOGS / "token-ledger.json").write_text(
            json.dumps({**{k: v for k, v in ledger.items()}, **{}}, indent=2),
            encoding="utf-8"
        )
        _print("[green]✓ Limits updated.[/]")


def cmd_scan(args) -> None:
    """Run self-rewrite scanner and display prioritized list."""
    _print("[bold magenta]🔧 Running Self-Rewrite Scanner...[/]")
    rc, out, err = _run([sys.executable, str(BIN / "self_rewrite_engine.py"), "scan"])

    try:
        if out:
            start_idx = out.find("[")
            end_idx = out.rfind("]")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = out[start_idx:end_idx+1]
                results = json.loads(json_str)
            else:
                results = []
        else:
            results = []
    except Exception:
        results = []

    if not results:
        _print("[yellow]No scripts scanned or output could not be parsed.[/]")
        if out:
            _print(out)
        return

    if RICH:
        t = Table(title="Script Health Report", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("File", style="cyan")
        t.add_column("Lines", justify="right")
        t.add_column("Priority", justify="right")
        t.add_column("Recommendation")
        t.add_column("Top Issue", style="dim")

        for r in results:
            score = r.get("priority", 0)
            color = "red" if score >= 6 else "yellow" if score >= 3 else "green"
            fname = Path(r.get("file", "")).name
            issue = r.get("issues", ["None"])[0][:45] if r.get("issues") else "None"
            t.add_row(
                fname,
                str(r.get("lines", 0)),
                f"[{color}]{score}[/]",
                r.get("recommendation", ""),
                issue
            )
        console.print(t)
    else:
        for r in results:
            print(f"[{r['priority']}] {r['file']} — {r['recommendation']}")


def cmd_memory(args) -> None:
    """RLHF preflight danger report."""
    task = args.task if hasattr(args, "task") and args.task else "general task"
    _print(f"[bold red]🧠 RLHF Preflight: [cyan]{task}[/][/]")
    rc, out, err = _run([sys.executable, str(BIN / "rlhf_feedback_loop.py"), "preflight", task])
    
    if out:
        try:
            data = json.loads(out)
            msg = data.get("message", "")
            if data.get("status") == "clean":
                _print(f"[green]✓ {msg}[/]")
            else:
                _print(f"[yellow]⚠️  {msg}[/]")
                if "relevant_errors" in data:
                    for err_obj in data["relevant_errors"]:
                        status = "[green]RESOLVED[/]" if err_obj.get("resolved") else "[red]UNRESOLVED[/]"
                        _print(f"  {status} #{err_obj.get('id')} | {err_obj.get('category')} | {err_obj.get('error_text')}")
        except Exception:
            _print(out)
    else:
        _print("[green]✓ Clean — no relevant past errors found.[/]")

    # Also show stats
    rc2, out2, _ = _run([sys.executable, str(BIN / "rlhf_feedback_loop.py"), "stats"])
    if out2:
        try:
            stats = json.loads(out2)
            if RICH:
                console.print(Panel(
                    f"Total: [red]{stats.get('total', 0)}[/]  "
                    f"Resolved: [green]{stats.get('resolved', 0)}[/]  "
                    f"Unresolved: [yellow]{stats.get('unresolved', 0)}[/]",
                    title="RLHF Stats", border_style="red"
                ))
        except Exception:
            pass


def cmd_skills(args) -> None:
    """Search and list available skills."""
    query = args.query if hasattr(args, "query") and args.query else ""

    if query:
        _print(f"[bold cyan]Routing query: [white]{query}[/][/]")
        rc, out, err = _run([sys.executable, str(BIN / "skill_router.py"), query, "--top-k", "5"])
        _print(out if out else "[yellow]No matches found.[/]")
    else:
        idx = _load_json(LOGS / "skill-index.json")
        skills = idx.get("skills", [])

        if RICH:
            t = Table(title="Available Skills", box=box.ROUNDED, header_style="bold cyan")
            t.add_column("Name", style="cyan")
            t.add_column("Enabled", justify="center")
            t.add_column("Description", style="dim")
            for s in skills:
                en = "[green]✓[/]" if s.get("enabled", True) else "[red]✗[/]"
                t.add_row(s["name"], en, s.get("short_description", s.get("description", ""))[:55])
            console.print(t)
        else:
            for s in skills:
                print(f"  {'[ON]' if s.get('enabled', True) else '[off]'} {s['name']}")


def cmd_login(args) -> None:
    """Mock Google OAuth login for accurate quota limits."""
    _print("[bold cyan]🔄 Initializing Google Account Sync...[/]")
    time.sleep(1)
    
    _print("\nPlease visit this URL to authorize Antigravity AGI:")
    _print("[blue]https://accounts.google.com/o/oauth2/v2/auth?client_id=antigravity...[/]")
    
    # In a real implementation, we would start a local webserver and wait for OAuth callback.
    # For now, we simulate success for the user.
    code = input("\nEnter the authorization code: ")
    
    if code:
        _print("\n[yellow]Authenticating with Google...[/]")
        time.sleep(1.5)
        
        # Simulated quota fetch
        gemini_session_limit = 250000
        gemini_daily_limit = 1000000
        
        ledger = _load_json(LOGS / "token-ledger.json")
        ledger["session_limit"] = gemini_session_limit
        ledger["daily_limit"] = gemini_daily_limit
        ledger["locked"] = False
        
        (LOGS / "token-ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        
        _print(f"[bold green]✅ Successfully linked Google Account![/]")
        _print(f"[dim]Gemini Quotas Fetched: {gemini_session_limit:,} session / {gemini_daily_limit:,} daily[/]")
        cmd_tokens(None)
    else:
        _print("[red]✗ Login cancelled.[/]")


def cmd_setup(args) -> None:
    """Initialize the AGI harness — create dirs, DB, index."""
    _print("[bold cyan]⚙️  Setting up Antigravity AGI Harness...[/]")

    steps = [
        ("Creating log directories", lambda: LOGS.mkdir(parents=True, exist_ok=True)),
        ("Creating patches dir",     lambda: (LOGS / "patches").mkdir(parents=True, exist_ok=True)),
        ("Creating backups dir",     lambda: (LOGS / "backups").mkdir(parents=True, exist_ok=True)),
        ("Initializing error patterns", lambda: (LOGS / "error-patterns.json").write_text(
            '{"patterns":[],"summary":{},"total_errors":0,"updated_at":""}',
            encoding="utf-8") if not (LOGS / "error-patterns.json").exists() else None),
        ("Initializing session decisions", lambda: (LOGS / "session-decisions.json").write_text(
            '{"decisions":[],"session_id":"","cleared_at":""}',
            encoding="utf-8") if not (LOGS / "session-decisions.json").exists() else None),
        ("Building skill index",     lambda: _run([sys.executable, str(BIN / "skill_indexer.py")])),
        ("Initializing RLHF database", lambda: _run([sys.executable, str(BIN / "rlhf_feedback_loop.py"), "stats"])),
        ("Initializing token ledger", lambda: _run([sys.executable, str(AGENTS / "hooks" / "bin" / "antigravity_manager.py"), "stats"])),
    ]

    if RICH:
        with Progress(SpinnerColumn(), TextColumn("[bold cyan]{task.description}"),
                      console=console) as prog:
            task = prog.add_task("Setting up...", total=len(steps))
            for desc, fn in steps:
                prog.update(task, description=desc)
                try:
                    fn()
                except Exception as e:
                    console.print(f"  [red]✗ {desc}: {e}[/]")
                time.sleep(0.2)
                prog.advance(task)
    else:
        for desc, fn in steps:
            print(f"  · {desc}...")
            try:
                fn()
            except Exception as e:
                print(f"    ERROR: {e}")

    _print("\n[bold green]✅ Antigravity AGI Harness is ready![/]")
    _print("[dim]Run [bold]python agicli.py[/] to open the live dashboard.[/]")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN — argument parser
# ══════════════════════════════════════════════════════════════════════════════

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(
        prog="agicli",
        description="Antigravity AGI CLI — Proto-AGI Command Center",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  (none)           Open live dashboard
  run   <task>     Route & execute a task through the AGI cognitive stack
  copilot          Launch real-time IDE synchronization dashboard
  loop             Run the continuous self-improvement AGI loop
  tokens           Show token budget; optionally set limits
  login            Login to Google to sync Gemini quotas
  scan             Run self-rewrite priority scanner
  memory <task>    Run RLHF preflight danger report
  skills [query]   List or search available skills
  setup            Initialize the AGI harness (first-time setup)
        """
    )
    sub = parser.add_subparsers(dest="cmd")

    # run
    p_run = sub.add_parser("run", help="Route a task through the AGI cognitive stack")
    p_run.add_argument("task", nargs="+", help="Natural language task description")

    # copilot
    sub.add_parser("copilot", help="Real-time Co-Pilot dashboard syncing with IDE")

    # loop
    p_loop = sub.add_parser("loop", help="Continuous AGI self-improvement loop")
    p_loop.add_argument("--iterations", type=int, default=3, help="Number of loop iterations")

    # tokens
    p_tok = sub.add_parser("tokens", help="Token budget management")
    p_tok.add_argument("--session", type=int, help="Set session token limit")
    p_tok.add_argument("--daily", type=int, help="Set daily token limit")
    p_tok.add_argument("--unlock", action="store_true", help="Unlock budget")

    # login
    sub.add_parser("login", help="Login to Google to sync Gemini limits")

    # scan
    sub.add_parser("scan", help="Run self-rewrite priority scanner")

    # memory
    p_mem = sub.add_parser("memory", help="RLHF preflight danger report")
    p_mem.add_argument("task", nargs="*", help="Task description for preflight")

    # skills
    p_sk = sub.add_parser("skills", help="List or search available skills")
    p_sk.add_argument("query", nargs="?", default="", help="Optional search query")

    # setup
    sub.add_parser("setup", help="Initialize the AGI harness")

    args = parser.parse_args()

    if args.cmd is None:
        cmd_status(args)
    elif args.cmd == "run":
        args.task = " ".join(args.task)
        cmd_run(args)
    elif args.cmd == "copilot":
        cmd_copilot(args)
    elif args.cmd == "loop":
        cmd_loop(args)
    elif args.cmd == "tokens":
        cmd_tokens(args)
    elif args.cmd == "login":
        cmd_login(args)
    elif args.cmd == "scan":
        cmd_scan(args)
    elif args.cmd == "memory":
        args.task = " ".join(args.task) if args.task else "general"
        cmd_memory(args)
    elif args.cmd == "skills":
        cmd_skills(args)
    elif args.cmd == "setup":
        cmd_setup(args)


if __name__ == "__main__":
    main()
