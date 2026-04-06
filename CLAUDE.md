# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is White Boarder?

A local Mac whiteboarding partner. Captures whiteboard photos via webcam, sends to Claude Vision API, maintains an incrementally-updated diagram with suggestions and questions. Outputs `claude.md` + `spec.md` per session.

## Tech Stack

Python 3.13 + Flask, OpenCV (camera only), Anthropic API (vision), Mermaid.js + Excalidraw (dual renderer). Vanilla HTML/CSS/JS frontend — no build step.

## Setup

```bash
source venv/bin/activate
cp .env.example .env           # Add ANTHROPIC_API_KEY
python app.py                  # http://localhost:5050
pip install -r requirements.txt
```

## Architecture

- `app.py` — Flask routes, orchestrates capture → analysis → state update
- `camera.py` — OpenCV webcam capture (manual button; `use_reloader=False` for macOS camera permissions)
- `claude_bridge.py` — Base64-encodes photos, sends to Claude API with vision, parses JSON. Mirror/Interpret mode toggle
- `session.py` — Session state, persistence to `sessions/{name}/state.json`, deduplicates suggestions, generates outputs
- `static/` — Single-page UI with CSS Grid (2/3 diagram | 1/3 panels). Excalidraw loaded via esm.sh CDN as ES module
- `sessions/` — Named session directories with state, photos, generated outputs

## Key Design Decisions

- **Anthropic API with vision** — sends actual whiteboard photos to Claude Sonnet; API key in `.env` (git-ignored)
- **Dual renderer** — Mermaid.js (default, structured) or Excalidraw (interactive, freeform via `mermaid-to-excalidraw` conversion). Toggle in UI
- **Mirror vs Interpret** — Mirror mode copies whiteboard layout faithfully; Interpret mode lets Claude optimize the diagram
- **Incremental updates** — Claude receives current diagram state + diff context, returns patched diagram
- **Cumulative suggestions** — deduplicated, dismissable, new ones get green outline. Dismissed list sent to Claude to avoid repetition
- **Named sessions** — directory path is the session name, not a timestamp ID

## Workflow Rules

### Plan First
- Enter plan mode for any non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately

### Self-Improvement
- After ANY correction: update `tasks/lessons.md` with the pattern
- Every correction becomes a rule in CLAUDE.md

### Verification
- Never mark a task complete without proving it works
- Run the server, test routes, demonstrate correctness

### Task Management
1. Write plan to `tasks/todo.md` with checkable items
2. Track progress, mark items complete as you go
3. Update `tasks/lessons.md` after corrections

### Core Principles
- **Simplicity First**: minimal code impact, no over-engineering
- **No Laziness**: find root causes, no temporary fixes
