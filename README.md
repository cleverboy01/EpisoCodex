# 🚀 EpisoCodex — Grok Build Autonomous AI Engineering Framework

<div align="center">

![xAI Grok Build](https://img.shields.io/badge/xAI%20Grok--Build-Autonomous%20Agent-red?style=for-the-badge&logo=github)
![Grok AI](https://img.shields.io/badge/Grok--AI-Code%20Agent-black?style=for-the-badge&logo=x)
![Version](https://img.shields.io/badge/Version-2.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-Apache%202.0-orange?style=for-the-badge)

<br/>

### 💡 **An open-source autonomous AI software engineering framework built upon the core architecture of xAI's [grok-build](https://github.com/xai-org/grok-build).**

*Empower your IDE with Grok Build capabilities: self-healing, self-learning, and token-efficient AI agents.*

[Quick Start](#-quick-start) • [Grok Build Architecture](#-grok-build-architecture) • [Features](#-key-features) • [CLI Reference](#-cli-reference) • [SEO & Keywords](#-keywords--search-index) • [License](#-license)

---

</div>

> [!NOTE]
> ℹ️ **Attribution Notice:**
> **EpisoCodex** is an open-source enhancement and adaptation derived from the **[xAI grok-build](https://github.com/xai-org/grok-build)** codebase and agent design specification.

---

## 🔍 Overview: Grok Build Autonomous Engineering

**EpisoCodex (Grok Build Engine)** brings xAI's **grok-build** autonomous coding capabilities directly to local development environments, Cursor, Windsurf, and Antigravity IDE. Designed for token efficiency, multi-agent coordination, and self-healing execution loops.

### Key Keywords & Focus Areas
* **grok-build** / **grok build**: Autonomous AI developer harness & workflow execution.
* **xAI / Grok AI**: Modern LLM agent orchestration, system-2 reasoning, and sandbox execution.
* **Proto-AGI Coding Harness**: Self-learning RLHF memory loops and AST chunk optimization.

---

## ⚡ What Makes Grok Build Architecture Different?

Standard AI coding extensions rely on static system prompts and unoptimized context windows. **EpisoCodex**, using **grok-build** core principles, acts as an Operating System for your AI coding assistant:

| Capability | Standard AI Extension | Grok Build Engine (EpisoCodex) |
|---|---|---|
| 🔀 **Skill Routing** | Manual static prompts | **Semantic Skill Router** auto-loads relevant tools |
| 🧠 **Error Avoidance** | Repeated trial-and-error | **RLHF Feedback Loop** remembers and avoids past errors |
| 🛡️ **Token Efficiency** | Context window burn | **Token Squeezer Guard** prevents wasteful file reads |
| 🏖️ **Safety & Verification** | Direct codebase edits | **Sandbox Simulator** tests patches before applying |
| 📝 **Session Persistence** | Context lost on reset | **Episodic Memory** persists across developer sessions |
| 🔧 **Self-Improvement** | Manual code review | **Self-Rewrite Engine** auto-proposes refactorings |

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
# Clone the Grok Build inspired repository
git clone https://github.com/cleverboy01/EpisoCodex.git
cd EpisoCodex

# Run one-click bootstrapper
python setup.py
```

### 2. Launch Workspace
```bash
# Launch Modern Desktop GUI Dashboard
python gui/guicli.py

# Or launch Terminal Live AGI Dashboard
python agicli.py
```

### 3. Run Autonomous Grok Task
```bash
python agicli.py run "refactor authentication module using JWT and verify in sandbox"
```

> 💡 **No Proprietary API Keys Required:** Operates locally with your existing AI assistant (Cursor, Windsurf, Antigravity IDE, Claude, GPT-4, Grok).

---

## 🏗️ Grok Build Architecture

### Cognitive Execution Loop

```mermaid
flowchart TD
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
```

---

## 🖥️ Desktop GUI (Antigravity & Grok Manager)

Located inside `gui/guicli.py`, the desktop application offers a clean visual interface for monitoring AI operations:
* 📡 **Live IDE Sync Dashboard:** Real-time stream of active tools and editor state.
* 🚀 **Visual Token Budget:** Real-time session and daily token consumption bars.
* 🛡️ **Workspace Sync:** Aligns memory and tracking to your local workspace account.
* 🎯 **Interactive Task Runner:** Execute tasks directly from a desktop interface.

---

## 📖 CLI Reference

| Command | Description |
|---|---|
| `python agicli.py` | Open interactive terminal dashboard |
| `python agicli.py run "<task>"` | Execute task through full Grok build cognitive loop |
| `python agicli.py loop [--iterations N]` | Start continuous self-improvement loop |
| `python agicli.py tokens` | Display current token budget ledger |
| `python agicli.py scan` | Run codebase health & rewrite scan |
| `python agicli.py memory "<task>"` | Perform RLHF preflight error check |

---

## 🛠️ IDE Integration (Cursor, Windsurf, Antigravity)

* **Cursor / Windsurf:** Copy `agents/` folder into your project root and import `agents/.cursorrules`.
* **Antigravity IDE:** Automatic hook detection via `agents/hooks/agent-hooks.json`.

---

## 🔑 Keywords & Search Index

`grok-build` `grok build` `xai grok` `grok ai` `grok-code` `xai-org/grok-build` `autonomous-agent` `ai-software-engineer` `proto-agi` `cursor-rules` `windsurf-ai` `token-optimization` `rlhf-agent` `self-healing-code` `antigravity-agi` `episocodex`

---

## 📜 Acknowledgments & License

This project incorporates architectural concepts and code patterns adapted from xAI's open-source **[grok-build](https://github.com/xai-org/grok-build)** project.

Distributed under the **Apache 2.0 License**.

---

<div align="center">

**Built with 🧠 EpisoCodex — Powered by xAI's grok-build architecture**  
⭐ Star this repository if you find it helpful!

</div>
