"""Bridge to Claude API for whiteboard analysis with vision."""

import base64
import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You are a whiteboard analysis assistant. You receive a photo of a physical whiteboard and the current state of a digital Mermaid flowchart that represents it.

Your job:
1. Look at the whiteboard photo carefully — read every word, follow every arrow, note every brace/bracket grouping
2. Produce a Mermaid FLOWCHART that mirrors what's drawn
3. Provide suggestions to improve the architecture/map
4. Provide questions that strengthen the thinking

READING THE WHITEBOARD:
- Trace every arrow exactly as drawn — if an arrow goes A → B, the diagram must show A --> B
- Curly braces {{ }} on the whiteboard mean a group of items that belong together — use a Mermaid subgraph for these
- Square brackets [ ] on the whiteboard are individual nodes
- If arrows fan out (one source → multiple targets), replicate that fan-out
- If arrows converge (multiple sources → one target), replicate that convergence
- Read ALL text, including small annotations, labels on arrows, and side notes

MERMAID SYNTAX RULES:
- Always use quotes around node labels: A["My Label"]
- For labels with special characters (parens, colons, dots, slashes): A["raw/ directory"]
- Arrow labels: A -->|"label"| B
- Subgraphs for grouped items: subgraph Name\\n ... \\nend
- The diagram field must be ONLY the Mermaid code (no markdown fences)

CRITICAL: Return ONLY valid JSON:
{
  "diagram": "<Mermaid flowchart code>",
  "diagram_type": "flowchart",
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
  "questions": ["question 1", "question 2", "question 3"]
}

If there is no current diagram, create one from scratch.
If the whiteboard hasn't changed, return the existing diagram unchanged.
Keep the diagram stable — preserve existing node IDs, only add/remove what changed."""


def _encode_image(photo_path: str) -> tuple[str, str]:
    """Read and base64-encode an image file. Returns (base64_data, media_type)."""
    ext = os.path.splitext(photo_path)[1].lower()
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    media_type = media_types.get(ext, "image/jpeg")

    with open(photo_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    return data, media_type


MIRROR_INSTRUCTION = """LAYOUT MODE: MIRROR
Replicate the whiteboard EXACTLY as a flowchart:
- Every arrow on the board = an arrow in the diagram, same direction
- Every box/circle/item on the board = a node
- Every brace/bracket grouping = a subgraph
- Match the flow direction (TD for top-down, LR for left-right) to what's drawn
- If something branches, branch it. If something converges, converge it.
- Do NOT reorganize, regroup, or "improve" the layout — copy it faithfully"""

INTERPRET_INSTRUCTION = """LAYOUT MODE: INTERPRET
Reorganize the whiteboard content into the clearest possible flowchart.
- Optimize for readability and logical flow
- Restructure groupings if it improves clarity
- You're free to reorder nodes and change flow direction"""


def analyze_whiteboard(
    photo_path: str,
    current_diagram: str,
    diagram_type: str,
    user_text_history: list[str],
    new_user_text: str,
    active_suggestions: list[str],
    dismissed_suggestions: list[str],
    mirror_layout: bool = True,
) -> dict:
    """Send whiteboard photo + context to Claude API with vision, get structured analysis."""

    # Build text context
    parts = []

    parts.append(MIRROR_INSTRUCTION if mirror_layout else INTERPRET_INSTRUCTION)
    parts.append("")

    if current_diagram:
        parts.append(f"## Current Diagram ({diagram_type or 'auto'})")
        parts.append("```mermaid")
        parts.append(current_diagram)
        parts.append("```")
    else:
        parts.append("## Current Diagram")
        parts.append("No diagram yet — create one from the whiteboard photo.")

    if user_text_history or new_user_text:
        parts.append("\n## User Context")
        for text in user_text_history:
            parts.append(f"- {text}")
        if new_user_text:
            parts.append(f"- [LATEST] {new_user_text}")

    if active_suggestions:
        parts.append("\n## Active Suggestions (still open)")
        for s in active_suggestions:
            parts.append(f"- {s}")

    if dismissed_suggestions:
        parts.append("\n## Dismissed Suggestions (already addressed, don't repeat)")
        for s in dismissed_suggestions:
            parts.append(f"- {s}")

    parts.append("\nReturn ONLY the JSON response. No markdown fences, no explanation.")

    text_context = "\n".join(parts)

    try:
        image_data, media_type = _encode_image(photo_path)

        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": text_context,
                        },
                    ],
                }
            ],
        )

        response_text = response.content[0].text.strip()

        # Extract JSON if wrapped in markdown fences
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        return json.loads(response_text)

    except anthropic.AuthenticationError:
        return {"error": "Invalid API key. Add your key to .env: ANTHROPIC_API_KEY=sk-ant-..."}
    except anthropic.APIError as e:
        return {"error": f"Claude API error: {e}"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response as JSON: {e}\nRaw: {response_text[:500]}"}
    except FileNotFoundError:
        return {"error": f"Photo not found: {photo_path}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}
