// ============================================================
// THE ARCHIVE - frontend logic (v3 - single user, personal)
// ============================================================

const API_BASE = 'http://127.0.0.1:8000';

// ---------------- session helpers ----------------

function getToken() {
  return localStorage.getItem('archive_token');
}

function clearSession() {
  localStorage.removeItem('archive_token');
}

// ---------------- api fetch with session token ----------------

async function apiFetch(path, options = {}) {
  const token = getToken();
  options.headers = options.headers || {};
  if (token) options.headers['x-session-token'] = token;
  const res = await fetch(API_BASE + path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { const body = await res.json(); detail = body.detail || detail; } catch (_) {}
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

// ---------------- screen router ----------------

function showScreen(id) {
  ['screen-login', 'screen-app'].forEach(s => {
    const el = document.getElementById(s);
    if (el) el.hidden = (s !== id);
  });
}

// ---------------- helpers ----------------

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

function basename(path) {
  // Strip any leading path, works for both / and \ separators
  return (path || '').split(/[\\/]/).pop() || path;
}

// ---------------- login ----------------

function initLogin() {
  const btn   = document.getElementById('login-submit');
  const err   = document.getElementById('login-error');
  const userI = document.getElementById('login-username');
  const passI = document.getElementById('login-password');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const username = userI.value.trim();
    const password = passI.value.trim();
    if (!username) { err.dataset.tone = 'error'; err.textContent = 'Please enter your username.'; return; }
    if (!password) { err.dataset.tone = 'error'; err.textContent = 'Please enter your password.'; return; }
    btn.disabled = true;
    err.textContent = 'Signing in…';
    try {
      const res = await fetch(API_BASE + '/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        localStorage.setItem('archive_token', data.token);
        showScreen('screen-app');
        initApp();
      } else {
        err.dataset.tone = 'error';
        err.textContent = data.detail || data.message || 'Incorrect username or password.';
        btn.disabled = false;
      }
    } catch (e) {
      err.dataset.tone = 'error';
      err.textContent = 'Could not reach the server.';
      btn.disabled = false;
    }
  });

  passI.addEventListener('keydown', e => { if (e.key === 'Enter') btn.click(); });
  userI.addEventListener('keydown', e => { if (e.key === 'Enter') passI.focus(); });
}

// ---------------- health check ----------------

async function checkHealth() {
  const line = document.getElementById('statusLine');
  const text = document.getElementById('statusText');
  if (!line) return;
  try {
    await fetch(API_BASE + '/health');
    line.dataset.state = 'ok';
    text.textContent = 'the index is open';
  } catch {
    line.dataset.state = 'error';
    text.textContent = "can't reach the backend";
  }
}

// ---------------- user badge ----------------

function renderBadge() {
  const badge = document.getElementById('userBadge');
  if (!badge) return;
  badge.innerHTML = 'signed in as <span class="badge-name">Manivardhan</span>';
}

// ---------------- tabs ----------------

function initTabs() {
  const tabs = document.querySelectorAll('.desk-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => { t.classList.remove('is-active'); t.setAttribute('aria-selected','false'); });
      tab.classList.add('is-active');
      tab.setAttribute('aria-selected','true');
      document.querySelectorAll('.desk-panel').forEach(panel => {
        const match = panel.id === tab.dataset.panel;
        panel.classList.toggle('is-active', match);
        panel.hidden = !match;
      });
    });
  });
}

// ---------------- dropzone ----------------

function initDropzone() {
  const dropzone = document.getElementById('dropzone');
  const input    = document.getElementById('fileInput');
  const label    = document.getElementById('dropzoneLabel');
  if (!dropzone) return;
  input.addEventListener('change', () => { label.textContent = input.files[0]?.name || 'Drop a PDF or TXT file here'; });
  ['dragover','dragleave','drop'].forEach(evt => dropzone.addEventListener(evt, e => e.preventDefault()));
  dropzone.addEventListener('dragover', () => dropzone.classList.add('is-dragover'));
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('is-dragover'));
  dropzone.addEventListener('drop', e => {
    dropzone.classList.remove('is-dragover');
    const file = e.dataTransfer.files[0];
    if (file) { input.files = e.dataTransfer.files; label.textContent = file.name; }
  });
}

// ---------------- document upload ----------------

function initDocumentForm() {
  const form    = document.getElementById('panel-document');
  const input   = document.getElementById('fileInput');
  const btn     = document.getElementById('uploadBtn');
  const message = document.getElementById('uploadMessage');
  const label   = document.getElementById('dropzoneLabel');
  if (!form) return;

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const file = input.files[0];
    if (!file) { message.dataset.tone = 'error'; message.textContent = 'Choose a file first.'; return; }
    const formData = new FormData();
    formData.append('file', file);
    btn.disabled = true;
    message.dataset.tone = '';
    message.textContent = 'Accessioning…';
    try {
      const result = await apiFetch('/ingest/document', { method: 'POST', body: formData });
      message.dataset.tone = 'ok';
      message.textContent = result.source + ' — ' + result.chunks_added + ' chunks added.';
      input.value = '';
      label.textContent = 'Drop a PDF or TXT file here';
      loadCollection();
    } catch (err) {
      message.dataset.tone = 'error';
      message.textContent = err.message || "Couldn't accession that file.";
    } finally { btn.disabled = false; }
  });
}

// ---------------- note form ----------------

function initNoteForm() {
  const form     = document.getElementById('panel-note');
  const titleI   = document.getElementById('noteTitle');
  const contentI = document.getElementById('noteContent');
  const btn      = document.getElementById('noteBtn');
  const message  = document.getElementById('noteMessage');
  if (!form) return;

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const title   = titleI.value.trim();
    const content = contentI.value.trim();
    if (!title || !content) return;
    btn.disabled = true;
    message.dataset.tone = '';
    message.textContent = 'Filing…';
    try {
      const result = await apiFetch('/ingest/note', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      });
      message.dataset.tone = 'ok';
      message.textContent = result.source + ' — ' + result.chunks_added + ' chunks added.';
      titleI.value = '';
      contentI.value = '';
      loadCollection();
    } catch (err) {
      message.dataset.tone = 'error';
      message.textContent = err.message || "Couldn't file that note.";
    } finally { btn.disabled = false; }
  });
}

// ---------------- collection ----------------

async function loadCollection() {
  const list  = document.getElementById('collectionList');
  const empty = document.getElementById('collectionEmpty');
  if (!list) return;
  try {
    const result = await apiFetch('/documents');
    const docs = result.documents || [];
    list.querySelectorAll('.collection-item').forEach(el => el.remove());
    if (docs.length === 0) { empty.style.display = ''; return; }
    empty.style.display = 'none';
    docs.forEach((doc, i) => {
      const li  = document.createElement('li');
      li.className = 'collection-item';
      const num  = String(i + 1).padStart(3, '0');
      const name = basename(doc.source);
      li.innerHTML = '<span class="call-number">#' + num + '</span><span class="item-name" title="' + escapeHtml(name) + '">' + escapeHtml(name) + '</span><div class="item-actions"><button class="btn-delete" title="Delete">🗑️</button></div>';

      const delBtn = li.querySelector('.btn-delete');
      delBtn.addEventListener('click', async () => {
        if (confirm(`Delete ${doc.source}?`)) {
          try {
            await apiFetch(`/documents?source=${encodeURIComponent(doc.source)}`, { method: 'DELETE' });
            loadCollection();
          } catch(e) { alert(e.message || 'Could not delete document.'); }
        }
      });
      list.appendChild(li);
    });
  } catch (err) {
    // 401 = session expired — boot back to login
    if (err.status === 401) {
      clearSession();
      location.reload();
      return;
    }
    if (empty) { empty.style.display = ''; empty.textContent = 'Could not load collection.'; }
  }
}

// ---------------- render card ----------------

function renderCard({ question, answer, sources, isError, isLoading }) {
  const card = document.createElement('article');
  card.className = 'index-card' + (isError ? ' is-error' : '');
  const q = document.createElement('p');
  q.className = 'card-question';
  q.textContent = question;
  card.appendChild(q);
  const a = document.createElement(isLoading ? 'p' : 'div');
  a.className = isLoading ? 'card-loading' : 'card-answer';
  if (isLoading) {
    a.textContent = 'consulting the index';
  } else {
    a.innerHTML = marked.parse(answer ?? '');
  }
  card.appendChild(a);
  if (!isLoading && sources && sources.length > 0) {
    const wrapper   = document.createElement('div');
    wrapper.className = 'card-sources-wrapper';
    const toggle    = document.createElement('button');
    toggle.className = 'sources-toggle';
    toggle.textContent = 'Sources (' + sources.length + ')';
    toggle.setAttribute('aria-expanded','false');
    const sourcesEl = document.createElement('div');
    sourcesEl.className = 'card-sources';
    sourcesEl.hidden = true;
    sources.forEach(s => {
      const tab = document.createElement('span');
      tab.className = 'source-tab';
      tab.textContent = basename(s.source) + (s.page ? ' - p.' + s.page : '');
      if (s.preview) {
        const preview = document.createElement('span');
        preview.className = 'source-preview';
        preview.textContent = s.preview;
        tab.appendChild(preview);
      }
      sourcesEl.appendChild(tab);
    });
    toggle.addEventListener('click', () => {
      const isOpen = !sourcesEl.hidden;
      sourcesEl.hidden = isOpen;
      toggle.setAttribute('aria-expanded', String(!isOpen));
      toggle.classList.toggle('is-open', !isOpen);
    });
    wrapper.appendChild(toggle);
    wrapper.appendChild(sourcesEl);
    card.appendChild(wrapper);
  }
  return card;
}

// ---------------- ask form ----------------

function initAskForm() {
  const form      = document.getElementById('askForm');
  const input     = document.getElementById('questionInput');
  const btn       = document.getElementById('askBtn');
  const feed      = document.getElementById('cardFeed');
  const feedEmpty = document.getElementById('feedEmpty');
  if (!form) return;

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const question = input.value.trim();
    if (!question) return;
    feedEmpty.style.display = 'none';
    btn.disabled = true;
    input.value = '';
    const loadingCard = renderCard({ question, isLoading: true });
    feed.appendChild(loadingCard);
    try {
      const result = await apiFetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, chat_history: [] }),
      });
      const card = renderCard({ question, answer: result.answer, sources: result.sources });
      feed.replaceChild(card, loadingCard);
      loadCollection(); // keep sidebar in sync
    } catch (err) {
      const card = renderCard({ question, answer: err.message || "The archive couldn't answer that.", isError: true });
      feed.replaceChild(card, loadingCard);
    } finally { btn.disabled = false; }
  });
}

// ---------------- logout ----------------

function initLogout() {
  const btn = document.getElementById('logoutBtn');
  if (!btn) return;
  btn.addEventListener('click', () => { clearSession(); location.reload(); });
}

// ---------------- main app init ----------------

function initApp() {
  checkHealth();
  renderBadge();
  initTabs();
  initDropzone();
  initDocumentForm();
  initNoteForm();
  initAskForm();
  initLogout();
  loadCollection();
}

// ---------------- boot ----------------

document.addEventListener('DOMContentLoaded', () => {
  const token = getToken();
  if (token) {
    showScreen('screen-app');
    initApp();
  } else {
    showScreen('screen-login');
    initLogin();
  }
});
