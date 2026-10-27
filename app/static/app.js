/* Sage frontend — vanilla JS, no build step. */
(function () {
  "use strict";

  const API = ""; // same-origin; Vercel rewrites everything to the function
  const state = {
    token: localStorage.getItem("sage_token") || null,
    user: JSON.parse(localStorage.getItem("sage_user") || "null"),
    documents: [],
    conversations: [],
    activeDoc: null,
    activeConv: null,
    tab: "login",
  };

  const $ = (id) => document.getElementById(id);

  async function api(path, opts = {}) {
    const headers = { ...(opts.headers || {}) };
    if (!(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
    if (state.token) headers["Authorization"] = "Bearer " + state.token;
    const res = await fetch(API + path, { ...opts, headers });
    if (res.status === 401) { logout(false); throw new Error("Session expired — log in again."); }
    if (res.status === 429) throw new Error("Too many requests — slow down a moment.");
    if (!res.ok) {
      let detail = res.statusText;
      try { const j = await res.json(); detail = j.detail || detail; } catch (_) {}
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  function toast(msg) {
    const t = $("toast");
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(t._timer);
    t._timer = setTimeout(() => (t.hidden = true), 3200);
  }

  /* ---- Views ---- */
  function show(viewId) {
    ["auth-view", "chat-view", "empty-view"].forEach((id) => {
      $(id).hidden = id !== viewId;
    });
  }

  function renderAuth() {
    $("name-field").hidden = state.tab !== "signup";
    $("auth-submit").textContent = state.tab === "login" ? "Log in" : "Create account";
    document.querySelectorAll(".auth-tab").forEach((b) => {
      b.classList.toggle("active", b.dataset.tab === state.tab);
    });
    show("auth-view");
  }

  function renderApp() {
    $("user-chip").textContent = state.user ? state.user.email : "";
    $("logout-btn").hidden = false;
    if (state.activeConv) {
      $("view-title").textContent = "Conversation";
      $("view-sub").textContent = "Grounded Q&A over your document";
      show("chat-view");
    } else if (state.activeDoc) {
      $("view-title").textContent = state.activeDoc.title;
      $("view-sub").textContent = state.activeDoc.filename + " · " + state.activeDoc.char_count.toLocaleString() + " chars";
      show("chat-view");
    } else {
      $("view-title").textContent = "New conversation";
      $("view-sub").textContent = state.documents.length ? "Select a document to begin" : "Upload a document to begin";
      show("empty-view");
    }
  }

  /* ---- Data loading ---- */
  async function loadDocuments() {
    state.documents = await api("/api/documents");
    renderDocs();
  }
  async function loadConversations() {
    state.conversations = await api("/api/conversations");
    renderConvs();
  }

  function renderDocs() {
    const el = $("doc-list");
    el.innerHTML = "";
    state.documents.forEach((d) => {
      const div = document.createElement("div");
      div.className = "doc-item" + (state.activeDoc && state.activeDoc.id === d.id ? " active" : "");
      div.innerHTML = `<span>${escapeHtml(d.title)}</span><span class="doc-meta">${d.char_count.toLocaleString()} chars</span>`;
      div.onclick = () => { state.activeDoc = d; state.activeConv = null; clearMessages(); renderDocs(); renderApp(); };
      el.appendChild(div);
    });
  }

  function renderConvs() {
    const el = $("conv-list");
    el.innerHTML = "";
    state.conversations.forEach((c) => {
      const div = document.createElement("div");
      div.className = "conv-item" + (state.activeConv && state.activeConv.id === c.id ? " active" : "");
      div.textContent = c.title;
      div.onclick = async () => {
        state.activeConv = await api("/api/conversations/" + c.id);
        state.activeDoc = null;
        renderConvs(); renderDocs(); renderApp();
        renderConversation();
      };
      el.appendChild(div);
    });
  }

  function clearMessages() { $("messages").innerHTML = ""; }

  function renderConversation() {
    clearMessages();
    (state.activeConv.messages || []).forEach((m) => addMessage(m.role, m.content, m.citations || [], false));
  }

  /* ---- Messages ---- */
  function addMessage(role, content, citations, grounded, blocked) {
    const wrap = document.createElement("div");
    wrap.className = "msg role-" + role;
    if (role === "assistant") {
      if (blocked) wrap.classList.add("blocked");
      else if (grounded === false) wrap.classList.add("ungrounded");
    }
    const roleLabel = document.createElement("div");
    roleLabel.className = "msg-role";
    roleLabel.textContent = role === "user" ? "You" : "Sage";
    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.textContent = content;
    wrap.appendChild(roleLabel);
    wrap.appendChild(bubble);
    if (citations && citations.length) {
      const cit = document.createElement("div");
      cit.className = "citations";
      citations.forEach((c) => {
        const d = document.createElement("div");
        d.className = "citation";
        d.textContent = "“" + c + "”";
        cit.appendChild(d);
      });
      wrap.appendChild(cit);
    }
    $("messages").appendChild(wrap);
    $("messages").scrollTop = $("messages").scrollHeight;
  }

  /* ---- Actions ---- */
  async function ask(question) {
    addMessage("user", question, [], true);
    const payload = { question };
    if (state.activeDoc) payload.document_id = state.activeDoc.id;
    else if (state.activeConv) payload.conversation_id = state.activeConv.id;
    try {
      const res = await api("/api/conversations/ask", { method: "POST", body: JSON.stringify(payload) });
      const citations = res.citations.map((c) => c.snippet);
      addMessage("assistant", res.answer, citations, res.grounded, res.blocked);
      if (state.activeConv) state.activeConv = await api("/api/conversations/" + res.conversation_id);
      else { state.activeConv = { id: res.conversation_id }; state.activeDoc = null; }
      loadConversations();
      renderDocs(); renderApp();
    } catch (e) {
      addMessage("assistant", "Error: " + e.message, [], false, true);
    }
  }

  async function upload(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    toast("Uploading “" + file.name + "”…");
    try {
      const doc = await api("/api/documents", { method: "POST", body: fd });
      state.activeDoc = doc; state.activeConv = null; clearMessages();
      await loadDocuments();
      renderApp();
      toast("Document uploaded — ask away.");
    } catch (e) {
      toast("Upload failed: " + e.message);
    }
  }

  async function summarize() {
    const doc = state.activeDoc;
    if (!doc) { toast("Select a document first."); return; }
    addMessage("user", "Summarize this document.", [], true);
    try {
      const res = await api("/api/summarize", { method: "POST", body: JSON.stringify({ document_id: doc.id, ratio: 0.3, max_sentences: 8 }) });
      addMessage("assistant", res.summary, [], true);
    } catch (e) {
      addMessage("assistant", "Error: " + e.message, [], false, true);
    }
  }

  /* ---- Auth ---- */
  async function submitAuth(e) {
    e.preventDefault();
    $("auth-error").hidden = true;
    const email = $("email").value.trim();
    const password = $("password").value;
    const full_name = $("full_name").value.trim();
    const path = state.tab === "login" ? "/api/auth/login" : "/api/auth/signup";
    const body = state.tab === "login" ? { email, password } : { email, password, full_name };
    try {
      const res = await api(path, { method: "POST", body: JSON.stringify(body) });
      state.token = res.access_token;
      state.user = res.user;
      localStorage.setItem("sage_token", state.token);
      localStorage.setItem("sage_user", JSON.stringify(state.user));
      await loadDocuments();
      await loadConversations();
      renderApp();
    } catch (err) {
      $("auth-error").textContent = err.message;
      $("auth-error").hidden = false;
    }
  }

  function logout(clear = true) {
    if (clear) { state.token = null; state.user = null; localStorage.removeItem("sage_token"); localStorage.removeItem("sage_user"); }
    renderAuth();
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  /* ---- Wire up ---- */
  function wire() {
    $("menu-btn").onclick = () => $("sidebar").classList.toggle("open");
    $("logout-btn").onclick = () => logout();
    $("new-chat-btn").onclick = () => { state.activeDoc = null; state.activeConv = null; clearMessages(); renderDocs(); renderConvs(); renderApp(); };
    $("auth-form").onsubmit = submitAuth;
    document.querySelectorAll(".auth-tab").forEach((b) => {
      b.onclick = () => { state.tab = b.dataset.tab; renderAuth(); };
    });
    $("ask-form").onsubmit = (e) => {
      e.preventDefault();
      const q = $("question").value.trim();
      if (!q) return;
      $("question").value = "";
      ask(q);
    };
    $("upload-btn").onclick = () => $("file-input").click();
    $("empty-upload").onclick = () => $("file-input").click();
    $("file-input").onchange = (e) => { upload(e.target.files[0]); e.target.value = ""; };
    $("summarize-btn").onclick = summarize;
    $("question").addEventListener("input", (e) => {
      e.target.style.height = "auto";
      e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
    });
  }

  async function init() {
    wire();
    if (state.token) {
      try {
        await loadDocuments();
        await loadConversations();
        renderApp();
        return;
      } catch (_) { logout(false); }
    }
    renderAuth();
  }

  init();
})();
