# White Boarder — Task Tracking

## Completed (v1)
- [x] Flask skeleton + static UI (CSS Grid 3-panel layout)
- [x] Camera module (OpenCV webcam capture, manual button)
- [x] Claude bridge (OpenCV extraction → text → `claude -p` → JSON parsing)
- [x] Session state management (diagram, suggestions, questions, dismiss tracking)
- [x] Mermaid.js rendering + dismissable suggestions UI
- [x] Session persistence (save/load state.json, resume)
- [x] Output generation (CLAUDE.md + spec.md on End Session)
- [x] CLAUDE.md with build/run commands

## Future Work
- [ ] Auto-capture: detect when user leaves frame (presence detection)
- [ ] pytesseract OCR integration for better whiteboard text extraction
- [ ] Keyboard shortcut hints in UI
- [ ] Session export/import
- [ ] Diagram type evolution mid-session (Claude can switch types)
