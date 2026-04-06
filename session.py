"""Session state management for White Boarder."""

import json
import os
import time
from pathlib import Path

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")


class SessionManager:
    def __init__(self):
        self._active: dict | None = None
        self._session_id: str | None = None

    def list_sessions(self) -> list[dict]:
        """List all saved sessions."""
        sessions = []
        if not os.path.exists(SESSIONS_DIR):
            return sessions
        for name in sorted(os.listdir(SESSIONS_DIR), reverse=True):
            state_file = os.path.join(SESSIONS_DIR, name, "state.json")
            if os.path.exists(state_file):
                with open(state_file) as f:
                    state = json.load(f)
                sessions.append({
                    "id": name,
                    "name": state.get("name", name),
                    "created": state.get("created", ""),
                    "photo_count": len(state.get("photos", [])),
                })
        return sessions

    def create(self, name: str) -> dict:
        """Create a new session. Name is required and used as the directory name."""
        # Sanitize name for filesystem use
        safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in name).strip()
        if not safe_name:
            return {"error": "Session name is required"}

        # Check for duplicates
        session_dir = os.path.join(SESSIONS_DIR, safe_name)
        if os.path.exists(session_dir):
            return {"error": f"Session '{safe_name}' already exists"}

        self._session_id = safe_name
        self._active = {
            "id": safe_name,
            "name": safe_name,
            "created": time.strftime("%Y-%m-%d %H:%M"),
            "diagram": "",
            "diagram_type": "",
            "active_suggestions": [],
            "dismissed_suggestions": [],
            "questions": [],
            "user_text_history": [],
            "photos": [],
        }
        self._save()
        return self._active

    def load(self, session_id: str) -> dict | None:
        """Load a previous session to resume."""
        state_file = os.path.join(SESSIONS_DIR, session_id, "state.json")
        if not os.path.exists(state_file):
            return None
        with open(state_file) as f:
            self._active = json.load(f)
        self._session_id = session_id
        return self._active

    def get_state(self) -> dict | None:
        return self._active

    def get_photos_dir(self) -> str:
        return os.path.join(SESSIONS_DIR, self._session_id, "photos")

    def apply_update(self, result: dict, user_text: str, photo_path: str):
        """Apply Claude's analysis result to the session state."""
        if not self._active:
            return

        # Update diagram (Claude returns the full updated diagram)
        if result.get("diagram"):
            self._active["diagram"] = result["diagram"]
        if result.get("diagram_type"):
            self._active["diagram_type"] = result["diagram_type"]

        # Append new suggestions (cumulative, no duplicates)
        existing = set(self._active["active_suggestions"])
        dismissed = set(self._active["dismissed_suggestions"])
        new_suggestions = []
        for s in result.get("suggestions", []):
            if s not in existing and s not in dismissed:
                self._active["active_suggestions"].append(s)
                new_suggestions.append(s)
        self._active["new_suggestions"] = new_suggestions

        # Replace questions (refresh each capture)
        if result.get("questions"):
            self._active["questions"] = result["questions"]

        # Track user text
        if user_text:
            self._active["user_text_history"].append(user_text)

        # Track photo
        self._active["photos"].append(photo_path)

        self._save()

    def dismiss_suggestion(self, index: int):
        """Move a suggestion from active to dismissed."""
        if not self._active:
            return
        active = self._active["active_suggestions"]
        if 0 <= index < len(active):
            dismissed = active.pop(index)
            self._active["dismissed_suggestions"].append(dismissed)
            self._save()

    def add_user_text(self, text: str):
        """Add context text without a capture."""
        if self._active and text:
            self._active["user_text_history"].append(text)
            self._save()

    def end_session(self) -> dict:
        """End session and generate outputs."""
        if not self._active:
            return {"error": "No active session"}

        session_dir = os.path.join(SESSIONS_DIR, self._session_id)

        # Generate CLAUDE.md
        claude_md = self._generate_claude_md()
        claude_path = os.path.join(session_dir, "claude.md")
        with open(claude_path, "w") as f:
            f.write(claude_md)

        # Generate spec.md
        spec_md = self._generate_spec_md()
        spec_path = os.path.join(session_dir, "spec.md")
        with open(spec_path, "w") as f:
            f.write(spec_md)

        result = {
            "claude_md": claude_md,
            "spec_md": spec_md,
            "claude_md_path": claude_path,
            "spec_md_path": spec_path,
        }

        self._active = None
        self._session_id = None
        return result

    def _generate_claude_md(self) -> str:
        """Generate CLAUDE.md from existing template + session content."""
        # Start from the project's CLAUDE.md as base
        base_path = os.path.join(os.path.dirname(__file__), "CLAUDE.md")
        base = ""
        if os.path.exists(base_path):
            with open(base_path) as f:
                base = f.read()

        state = self._active
        lines = [base.rstrip(), "", "---", ""]
        lines.append("## Session: " + state.get("name", "Untitled"))
        lines.append("")

        if state.get("diagram"):
            lines.append("### Architecture")
            lines.append("```mermaid")
            lines.append(state["diagram"])
            lines.append("```")
            lines.append("")

        if state.get("user_text_history"):
            lines.append("### Key Decisions")
            for text in state["user_text_history"]:
                lines.append(f"- {text}")
            lines.append("")

        return "\n".join(lines)

    def _generate_spec_md(self) -> str:
        """Generate spec.md: session summary + tech spec."""
        state = self._active
        lines = [f"# Spec: {state.get('name', 'Untitled')}", ""]

        lines.append("## Session Summary")
        lines.append(f"- **Date**: {state.get('created', 'Unknown')}")
        lines.append(f"- **Photos captured**: {len(state.get('photos', []))}")
        lines.append("")

        if state.get("user_text_history"):
            lines.append("### Context Provided")
            for text in state["user_text_history"]:
                lines.append(f"- {text}")
            lines.append("")

        if state.get("diagram"):
            lines.append("## Architecture")
            lines.append("```mermaid")
            lines.append(state["diagram"])
            lines.append("```")
            lines.append("")

        if state.get("active_suggestions"):
            lines.append("## Open Suggestions")
            for s in state["active_suggestions"]:
                lines.append(f"- {s}")
            lines.append("")

        if state.get("dismissed_suggestions"):
            lines.append("## Addressed Suggestions")
            for s in state["dismissed_suggestions"]:
                lines.append(f"- ~~{s}~~")
            lines.append("")

        if state.get("questions"):
            lines.append("## Open Questions")
            for q in state["questions"]:
                lines.append(f"- {q}")
            lines.append("")

        return "\n".join(lines)

    def _save(self):
        """Persist current state to disk."""
        if not self._active or not self._session_id:
            return
        session_dir = os.path.join(SESSIONS_DIR, self._session_id)
        os.makedirs(session_dir, exist_ok=True)
        state_file = os.path.join(session_dir, "state.json")
        with open(state_file, "w") as f:
            json.dump(self._active, f, indent=2)
