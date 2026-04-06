"""White Boarder — Flask server for the whiteboarding partner app."""

import json
import os
from flask import Flask, jsonify, request, send_from_directory

from camera import capture_photo
from session import SessionManager
from claude_bridge import analyze_whiteboard

app = Flask(__name__, static_folder="static")
sessions = SessionManager()


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    return jsonify(sessions.list_sessions())


@app.route("/api/sessions", methods=["POST"])
def create_session():
    name = request.json.get("name", "").strip()
    if not name:
        return jsonify({"error": "Session name is required"}), 400
    result = sessions.create(name)
    if result.get("error"):
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/sessions/<session_id>/resume", methods=["POST"])
def resume_session(session_id):
    session = sessions.load(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session)


@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify(sessions.get_state())


@app.route("/api/capture", methods=["POST"])
def do_capture():
    state = sessions.get_state()
    if not state:
        return jsonify({"error": "No active session"}), 400

    # Capture photo from webcam
    photo_dir = sessions.get_photos_dir()
    photo_path = capture_photo(photo_dir)
    if not photo_path:
        return jsonify({"error": "Camera capture failed"}), 500

    # Get user text and flags from request
    data = request.json if request.is_json else {}
    user_text = data.get("text", "")
    mirror_layout = data.get("mirror_layout", True)

    # Send to Claude for analysis
    result = analyze_whiteboard(
        photo_path=photo_path,
        current_diagram=state.get("diagram", ""),
        diagram_type=state.get("diagram_type", ""),
        user_text_history=state.get("user_text_history", []),
        new_user_text=user_text,
        active_suggestions=state.get("active_suggestions", []),
        dismissed_suggestions=state.get("dismissed_suggestions", []),
        mirror_layout=mirror_layout,
    )

    if result.get("error"):
        return jsonify({"error": result["error"]}), 500

    # Update session state
    sessions.apply_update(result, user_text, photo_path)

    return jsonify(sessions.get_state())


@app.route("/api/dismiss", methods=["POST"])
def dismiss_suggestion():
    idx = request.json.get("index")
    if idx is not None:
        sessions.dismiss_suggestion(idx)
    return jsonify(sessions.get_state())


@app.route("/api/context", methods=["POST"])
def add_context():
    """Add text context without capturing a photo."""
    text = request.json.get("text", "")
    if text:
        sessions.add_user_text(text)
    return jsonify(sessions.get_state())


@app.route("/api/end", methods=["POST"])
def end_session():
    outputs = sessions.end_session()
    return jsonify(outputs)


if __name__ == "__main__":
    # use_reloader=False prevents spawning a child process that loses macOS camera permissions
    app.run(debug=True, port=5050, use_reloader=False)
