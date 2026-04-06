# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is White Boarder?

A local Mac whiteboarding partner app. You whiteboard on a physical board, the app captures photos, maintains an incrementally-updated Mermaid diagram, and provides suggestions/questions. Outputs a `CLAUDE.md` and `spec.md` per session.

## Tech Stack

Python 3.13 + Flask, OpenCV for camera, Anthropic API (vision) for AI analysis, Mermaid.js for diagram rendering. Vanilla HTML/CSS/JS frontend — no framework.

## Setup

```bash
# 1. Add your API key to .env (git-ignored, never committed)
cp .env.example .env
# Edit .env → ANTHROPIC_API_KEY=sk-ant-...

# 2. Activate and run
source venv/bin/activate
python app.py                    # http://localhost:5050
pip install -r requirements.txt  # Install/update deps
```

## Architecture

- `app.py` �� Flask routes, orchestrates capture → analysis ��� state update
- `camera.py` — OpenCV webcam capture (manual button, auto-detect is future work)
- `claude_bridge.py` — Sends whiteboard photo (base64) + context to Claude API with vision, parses JSON response
- `session.py` — Session state (diagram, suggestions, questions), persistence to `sessions/{id}/state.json`, output generation
- `static/` — Single-page UI: CSS Grid layout (2/3 diagram | 1/3 suggestions+questions), Mermaid.js rendering
- `sessions/` — Persisted session data, photos, generated outputs

## Key Design Decisions

- **Anthropic API with vision** — sends actual whiteboard photos to Claude Sonnet; API key in `.env` (git-ignored)
- **Security** — `.env` in `.gitignore`, `.env.example` checked in as template, no secrets in code
- **Incremental diagram updates** — Claude receives current Mermaid state + changes, returns patched diagram (not full regeneration)
- **Cumulative dismissable suggestions** — new suggestions append, user dismisses addressed ones, dismissed list sent to Claude to avoid repetition
- **Session persistence** — save/resume via JSON state files

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
