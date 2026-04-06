# White Boarder

An AI whiteboarding partner that runs locally on your Mac. Point your laptop camera at a whiteboard, capture photos as you draw, and White Boarder maintains a live digital diagram with suggestions and questions to strengthen your thinking.

## How It Works

1. Start a named session
2. Whiteboard on a physical board in front of your laptop camera
3. Hit **Capture** (or `Ctrl+Space`) when you step back
4. Claude Vision analyzes the photo and produces/updates a diagram
5. Suggestions and questions appear in the side panels
6. End the session to generate a `claude.md` and `spec.md`

## Setup

```bash
# Clone and enter the project
cd "White Boarder"

# Create virtual environment and install deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add your Anthropic API key
cp .env.example .env
# Edit .env → ANTHROPIC_API_KEY=sk-ant-...

# Run
python app.py
# Open http://localhost:5050
```

## Features

- **Whiteboard capture** — OpenCV webcam capture via manual button
- **Claude Vision analysis** — sends actual photos to Claude Sonnet for diagram generation
- **Dual renderer** — toggle between Mermaid.js (structured) and Excalidraw (interactive/freeform)
- **Mirror mode** — toggle to faithfully replicate whiteboard layout vs. Claude's optimized interpretation
- **Cumulative suggestions** — new suggestions highlighted with green outline, dismissable
- **Session persistence** — save and resume sessions by name
- **Session outputs** — generates `claude.md` (project context file) and `spec.md` (session summary + tech spec)

## UI Layout

```
┌──────────────────────────────┬───────────────────┐
│                              │   SUGGESTIONS     │
│   DIAGRAM (2/3)              │   (dismissable)   │
│   Mermaid or Excalidraw      ├───────────────────┤
│                              │   QUESTIONS       │
│                              │                   │
├──────────────────────────────┴───────────────────┤
│ [Text input]                    [Capture] [End]  │
└──────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend**: Python, Flask, OpenCV (camera), Anthropic API (vision)
- **Frontend**: Vanilla HTML/CSS/JS, Mermaid.js, Excalidraw (via CDN)
- **No build step** — just `python app.py`
