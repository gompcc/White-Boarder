/* White Boarder — Frontend Logic */

let currentState = null;
let renderCounter = 0;
let mirrorLayout = true;
let useExcalidraw = false;

// --- Mermaid setup ---
mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  securityLevel: "loose",
  flowchart: { useMaxWidth: true, htmlLabels: true },
});

// --- Session Management ---

async function loadSessions() {
  const res = await fetch("/api/sessions");
  const sessions = await res.json();
  const list = document.getElementById("session-list");

  if (sessions.length === 0) {
    list.innerHTML = '<p class="placeholder">No previous sessions</p>';
    return;
  }

  list.innerHTML = sessions
    .map(
      (s) => `
    <div class="session-item" onclick="resumeSession('${escapeHtml(s.id)}')">
      <div>
        <div class="name">${escapeHtml(s.name)}</div>
        <div class="meta">${s.created} · ${s.photo_count} captures</div>
      </div>
    </div>
  `
    )
    .join("");
}

async function newSession() {
  const name = document.getElementById("session-name").value.trim();
  if (!name) {
    document.getElementById("session-name").focus();
    document.getElementById("session-name").placeholder = "Name is required";
    return;
  }
  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const data = await res.json();
  if (data.error) {
    alert(data.error);
    return;
  }
  currentState = data;
  showWorkspace();
}

async function resumeSession(id) {
  const res = await fetch(`/api/sessions/${id}/resume`, { method: "POST" });
  currentState = await res.json();
  showWorkspace();
  renderState();
}

function showWorkspace() {
  document.getElementById("session-picker").classList.add("hidden");
  document.getElementById("workspace").classList.remove("hidden");
  if (currentState) {
    document.getElementById("session-title").textContent =
      currentState.name || "Diagram";
  }
}

// --- Capture & Analysis ---

async function doCapture() {
  const textInput = document.getElementById("text-input");
  const text = textInput.value.trim();

  showLoading(true);

  try {
    const res = await fetch("/api/capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, mirror_layout: mirrorLayout }),
    });

    const data = await res.json();

    if (data.error) {
      alert("Capture error: " + data.error);
      return;
    }

    currentState = data;
    textInput.value = "";
    renderState();
  } catch (e) {
    alert("Failed to capture: " + e.message);
  } finally {
    showLoading(false);
  }
}

async function addContext() {
  const textInput = document.getElementById("text-input");
  const text = textInput.value.trim();
  if (!text) return;

  const res = await fetch("/api/context", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  currentState = await res.json();
  textInput.value = "";
}

async function dismissSuggestion(index) {
  const res = await fetch("/api/dismiss", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index }),
  });
  currentState = await res.json();
  renderState();
}

async function endSession() {
  if (!confirm("End this session and generate outputs?")) return;

  showLoading(true);
  try {
    const res = await fetch("/api/end", { method: "POST" });
    const data = await res.json();

    if (data.error) {
      alert("Error: " + data.error);
      return;
    }

    alert(
      `Session ended!\n\nOutputs saved:\n- ${data.claude_md_path}\n- ${data.spec_md_path}`
    );

    // Clean up Excalidraw if active
    if (window.destroyExcalidraw) window.destroyExcalidraw();

    // Return to session picker
    document.getElementById("workspace").classList.add("hidden");
    document.getElementById("session-picker").classList.remove("hidden");
    currentState = null;
    loadSessions();
  } finally {
    showLoading(false);
  }
}

// --- Rendering ---

async function renderState() {
  if (!currentState) return;

  const mermaidContainer = document.getElementById("mermaid-output");
  const excalidrawContainer = document.getElementById("excalidraw-output");
  const placeholder = document.getElementById("diagram-placeholder");
  const badge = document.getElementById("diagram-type-badge");

  if (currentState.diagram) {
    placeholder.classList.add("hidden");
    badge.textContent = currentState.diagram_type || "";

    if (useExcalidraw && window.excalidrawLoaded) {
      // --- Excalidraw rendering ---
      mermaidContainer.classList.add("hidden");
      excalidrawContainer.classList.remove("hidden");

      // Init Excalidraw if not already mounted
      if (!excalidrawContainer.hasChildNodes()) {
        window.initExcalidraw(excalidrawContainer);
        // Small delay for React to mount
        await new Promise((r) => setTimeout(r, 500));
      }

      const ok = await window.updateExcalidraw(currentState.diagram);
      if (!ok) {
        // Fallback: show Mermaid if conversion fails
        excalidrawContainer.classList.add("hidden");
        mermaidContainer.classList.remove("hidden");
        renderMermaid(mermaidContainer, currentState.diagram);
      }
    } else {
      // --- Mermaid rendering ---
      mermaidContainer.classList.remove("hidden");
      excalidrawContainer.classList.add("hidden");
      renderMermaid(mermaidContainer, currentState.diagram);
    }
  }

  // Suggestions (cumulative, dismissable, new ones highlighted)
  const sugList = document.getElementById("suggestions-list");
  const newSet = new Set(currentState.new_suggestions || []);
  if (currentState.active_suggestions && currentState.active_suggestions.length > 0) {
    sugList.innerHTML = currentState.active_suggestions
      .map(
        (s, i) => `
      <div class="item${newSet.has(s) ? ' item-new' : ''}">
        <span class="text">${escapeHtml(s)}</span>
        <button class="dismiss" onclick="dismissSuggestion(${i})" title="Dismiss">&times;</button>
      </div>
    `
      )
      .join("");
  } else {
    sugList.innerHTML = '<p class="placeholder">Suggestions will appear after first capture</p>';
  }

  // Questions
  const qList = document.getElementById("questions-list");
  if (currentState.questions && currentState.questions.length > 0) {
    qList.innerHTML = currentState.questions
      .map((q) => `<div class="question-item">${escapeHtml(q)}</div>`)
      .join("");
  } else {
    qList.innerHTML = '<p class="placeholder">Questions will appear after first capture</p>';
  }
}

async function renderMermaid(container, diagram) {
  renderCounter++;
  const renderId = `mermaid-svg-${renderCounter}`;
  try {
    const oldSvg = document.getElementById(renderId);
    if (oldSvg) oldSvg.remove();

    const { svg } = await mermaid.render(renderId, diagram);
    container.innerHTML = svg;
  } catch (e) {
    const partial = document.getElementById(renderId);
    if (partial) partial.remove();

    container.innerHTML = `<pre style="color:#e74c3c;white-space:pre-wrap;">Diagram render error:\n${e.message}\n\nRaw:\n${escapeHtml(diagram)}</pre>`;
  }
}

// --- Utilities ---

function showLoading(show) {
  document.getElementById("loading").classList.toggle("hidden", !show);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function toggleMirror() {
  mirrorLayout = !mirrorLayout;
  document.getElementById("btn-mirror").classList.toggle("active", mirrorLayout);
}

function toggleRenderer() {
  useExcalidraw = !useExcalidraw;
  const btn = document.getElementById("btn-renderer");
  btn.classList.toggle("active", useExcalidraw);
  btn.textContent = useExcalidraw ? "Mermaid" : "Excalidraw";

  if (!useExcalidraw && window.destroyExcalidraw) {
    window.destroyExcalidraw();
    document.getElementById("excalidraw-output").innerHTML = "";
  }

  // Re-render with current state
  if (currentState && currentState.diagram) {
    renderState();
  }
}

// --- Keyboard Shortcuts ---

document.addEventListener("keydown", (e) => {
  // Ctrl+Space or Cmd+Space to capture
  if ((e.ctrlKey || e.metaKey) && e.code === "Space") {
    e.preventDefault();
    doCapture();
  }
});

// --- Init ---
loadSessions();
