# 🚀 Antigravity AGI — Proto-AGI Framework for Autonomous Software Engineering

<div align="center">

![Version](https://img.shields.io/badge/version-2.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11+-green?style=flat-square)
![Based On](https://img.shields.io/badge/based%20on-Grok--Build-red?style=flat-square)
![License](https://img.shields.io/badge/license-Apache%202.0-orange?style=flat-square)
![Token Optimized](https://img.shields.io/badge/token--optimized-yes-brightgreen?style=flat-square)

**An autonomous AI engineering framework inspired by and built upon the core architecture of xAI's [grok-build](https://github.com/xai-org/grok-build).**

Drop it into any project. Your AI assistant becomes a self-healing, self-learning, token-efficient engineering agent.

[Quick Start](#quick-start) · [Architecture](#architecture) · [CLI Reference](#cli-reference) · [IDE Integration](#ide-integration) · [Phases](#cognitive-phases)

</div>

---

## What Makes This Different

Redesigned around the autonomous execution patterns of **grok-build**, most "AI coding" setups are just a system prompt. **Antigravity AGI** acts as an **operating system for your AI assistant**:

| Feature | Typical AI Setup | Grok-Build Based Architecture (Antigravity AGI) |
|---|---|---|
| **Skill selection** | Manual & static | **Auto-routed** via semantic skill router |
| **Past mistake avoidance** | None | **RLHF memory & feedback loop** — prevents repeating errors |
| **Context efficiency** | Uncontrolled & costly | **Token Squeezer Guard** blocks wasteful, full-file reads |
| **Code changes** | Direct & hopeful | **Sandboxed** simulation before applying to production |
| **Session learning** | Forgotten on close | **Episodic memory** persists across sessions |
| **Code quality** | Manual review | **Self-Rewrite Engine** auto-proposes improvements |
| **Task management** | You write TODOs | **Self-Healing Loop** auto-discovers and prioritizes work |

---

## Quick Start

```bash
# 1. Clone the repo
git clone [https://github.com/your-username/antigravity-agi](https://github.com/your-username/antigravity-agi)
cd antigravity-agi

# 2. One-click setup (creates DBs, indexes skills, installs dependencies)
python setup.py

# 3. Choose your workspace:
# OPTION A: Launch the Desktop GUI Dashboard
python gui/guicli.py

# OPTION B: Open the Terminal-based Live AGI Dashboard
python agicli.py

# 4. Run your first AGI-routed task via CLI
python agicli.py run "refactor the auth module to use JWT"
No proprietary API keys required. Everything runs locally using your existing AI assistant (Cursor, Windsurf, Antigravity IDE, etc.).Desktop GUI (Antigravity Manager)Inside gui/, we provide guicli.py — an ultra-modern Desktop Application built with customtkinter designed to monitor agent operations based on grok-build workflow patterns:📡 Live IDE Sync Dashboard: Dynamically shows what you type in the editor and what tools the agent is running.🚀 Visual Token Budget: Displays colorful, real-time progress bars for Session and Daily token usage.🛡️ IDE Configuration Sync: Syncs with your local workspace configs to align execution metrics with your active profile.🎯 Interactive Task Runner: Type any coding task, watch the cognitive loop execute, and view live logs.ArchitectureCognitive Execution Loop (Grok-Build Inspired Loop)Code snippetflowchart TD
    A([🖥️ SessionStart Hook]) --> B[📚 Skill Indexer\nBuilds skill-index.json]
    B --> C{User Task}
    C --> D[🧠 RLHF Preflight\nCheck past errors]
    D --> E[🔀 Skill Router\nSemantic skill selection]
    E --> F[🎯 Task Execution\nWith selected skills]
    F --> G{Result OK?}
    G -->|Yes| H[📝 Episodic Memory\nStore experience]
    G -->|No| I[🏥 Self-Heal Loop\nSandbox → Fix → Retry]
    I --> J{3 retries\nexhausted?}
    J -->|No| F
    J -->|Yes| K[🚨 Critic Agent\nAdversarial review]
    K --> H
    H --> L[🔧 Self-Rewrite Engine\nPrioritize improvements]
    L --> M[🔑 Token Guard\nUpdate token ledger]
    M --> N([💾 SessionEnd Hook\nFlush memory to disk])

    style A fill:#1a1a2e,color:#e94560
    style N fill:#1a1a2e,color:#e94560
    style I fill:#16213e,color:#f5a623
    style K fill:#16213e,color:#e94560
    style E fill:#0f3460,color:#53d8fb
    style D fill:#0f3460,color:#53d8fb
System ArchitectureCode snippetgraph LR
    subgraph CLI["🖥️ agicli.py — Command Center"]
        D[status]
        RN[run task]
        LP[loop]
        TK[tokens]
        SC[scan]
        MM[memory]
        SK[skills]
    end

    subgraph Cognitive["🧠 Cognitive Stack (agents/hooks/bin/)"]
        SR[skill_router.py]
        RL[rlhf_feedback_loop.py]
        EM[episodic_memory.py]
        RE[self_rewrite_engine.py]
        CO[chunk_optimizer.py]
    end

    subgraph Safety["🛡️ Safety & Control"]
        SG[safe_shell_guard.py]
        TS[token_squeezer.py]
        AM[antigravity_manager.py]
        SB[sandbox_runner.py]
    end

    subgraph Persistence["💾 Persistent Storage"]
        SI[(skill-index.json)]
        RD[(rlhf-memory.db)]
        ED[(episodic-memory.db)]
        TL[(token-ledger.json)]
        RP[(rewrite-priorities.json)]
    end

    CLI --> Cognitive
    CLI --> Safety
    Cognitive --> Persistence
    Safety --> Persistence
Cognitive PhasesThis framework adapts the multi-agent cognitive design of grok-build into 5 distinct phases:Phase 1: 🔀 Dynamic Skill RetrievalNever load all skills into context. The Skill Router semantically matches your task to the top-K relevant skills and loads only those instructions.Bashpython agicli.py skills "refactor authentication"
# → auto-selects: auto-fix, safe-commit, sandbox-run
Phase 2: 🧬 Self-EvolutionIf no skill matches, the Meta-Agent synthesizes a new skill from scratch, tests it, and adds it to the index permanently.Phase 3: 🧠 Episodic MemoryBefore starting: recall similar past experiences. After finishing: store a structured post-mortem. The agent gets smarter with every session.Bashpython agicli.py memory "fix database connection timeout"
# → RLHF Preflight Report: 2 similar past errors found
#   [RESOLVED] #12 | connection_refused | fix: add retry backoff
Phase 4: 🔬 System-2 Thinking (Critic + Sandbox)Risky changes are reviewed by the Critic Agent and simulated in a throwaway workspace copy before touching production code.Phase 5: 🎯 Proactive AgencyWhen idle, the Goal Generator scans the codebase for debt, bugs, and missing tests — building a prioritized, approval-gated task queue autonomously.CLI ReferenceBashpython agicli.py [command] [options]
CommandDescription(none)Open the live AGI dashboardrun "task"Route task through full AGI cognitive stackloop [--iterations N]Start continuous self-improvement looptokens [--session N] [--daily N] [--unlock]Token budget managementscanSelf-rewrite priority scannermemory "task"RLHF preflight danger reportskills [query]List or semantic-search available skillssetupInitialize the AGI harness (first-time)Token Optimization EngineAntigravity AGI incorporates context-saving concepts inspired by advanced AI code engineering platforms:Token Squeezer GuardBlocks large file reads before they burn your context window:Files > 150 lines without StartLine/EndLine → DENIEDRanges > 200 lines → DENIEDForces the agent to use grep + targeted readsChunk OptimizerSplits large Python files into AST-level chunks (functions/classes) for surgical edits:Bashpython agents/hooks/bin/chunk_optimizer.py list path/to/large_file.py
# → Lists 14 functions with token estimates
#   analyze() → 687 tokens  (L169-L241)
#   apply_patch() → 602 tokens (L294-L363)

python agents/hooks/bin/chunk_optimizer.py view large_file.py analyze
# → Returns only the analyze() function code (~150 lines)

python agents/hooks/bin/chunk_optimizer.py replace large_file.py analyze patched_analyze.py
# → Surgically replaces one function. File structure preserved.
IDE IntegrationCursor / WindsurfCopy the agents/ folder to your project root.In Cursor: Settings → Rules for AI → paste contents of agents/.cursorrules.Your AI assistant now has the full cognitive stack available.Antigravity IDE (Full Integration)The agents/hooks/agent-hooks.json file is auto-detected.All hooks fire automatically on tool usage.Run python agicli.py in a side terminal for the live dashboard.Folder StructurePlaintextantigravity-agi/
├── agicli.py                   ← 🖥️  Main CLI command center
├── setup.py                    ← ⚙️  One-click bootstrapper
├── agents/
│   ├── .cursorrules            ← 📋 AI assistant rules (always active)
│   ├── AGENTS.md               ← 🗺️  System index for AI agents
│   ├── hooks/
│   │   ├── agent-hooks.json    ← ⚡ Hook configuration
│   │   └── bin/
│   │       ├── antigravity_manager.py  ← 🚀 Token budget manager
│   │       ├── chunk_optimizer.py      ← ✂️  AST-based file splitter
│   │       ├── token_squeezer.py       ← 🛡️  Token burn guard
│   │       ├── skill_router.py         ← 🔀 Semantic skill routing
│   │       ├── skill_indexer.py        ← 📚 Skill index builder
│   │       ├── rlhf_feedback_loop.py   ← 🧠 Error memory & RLHF
│   │       ├── episodic_memory.py      ← 💾 Experience ledger
│   │       ├── self_rewrite_engine.py  ← 🔧 Autonomous code optimizer
│   │       ├── sandbox_runner.py       ← 🏖️  Safe execution sandbox
│   │       ├── error_pattern_tracker.py← 🔍 Error pattern detection
│   │       ├── safe_shell_guard.py     ← 🔒 Destructive command blocker
│   │       ├── session_log.py          ← 📝 Session audit log
│   │       └── session_memory_flush.py ← 💫 Memory persistence
│   ├── agent-definitions/          ← 🤖 Specialized sub-agents
│   │   ├── autonomous-agi.md
│   │   ├── critic.md
│   │   ├── goal-generator.md
│   │   ├── meta-agent.md
│   │   └── skill-router.md
│   ├── skills/                     ← ⚡ Slash-command skills
│   └── specs/                      ← 📖 System design specs
└── README.md


Acknowledgments & LicenseThis project incorporates architectural concepts and code patterns adapted from xAI's open-source grok-build project.Distributed under the Apache 2.0 license. Free for personal and commercial use.Built with 🧠 Antigravity AGI (Powered by Grok-Build concepts)The token-efficient, self-learning AI coding harness.⭐ Star this repo if it made your AI smarter!
