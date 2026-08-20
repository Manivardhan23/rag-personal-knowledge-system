// ============================================================
// THE ARCHIVE - frontend logic (v2 - multi-user, BYOK)
// ============================================================

const API_BASE = 'http://127.0.0.1:8000';

// ---------------- identity helpers ----------------

async function hashKey(key) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(key));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 12);
}

function getIdentity() {
  const role = localStorage.getItem('archive_role');
  if (role === 'admin') return { isAdmin: true, memberId: null, groqKey: null, name: 'Admin' };
  const memberId = localStorage.getItem('archive_member_id');
  const groqKey  = localStorage.getItem('archive_groq_key');
  const name     = localStorage.getItem('archive_name') || 'User';
  if (memberId && groqKey) return { isAdmin: false, memberId, groqKey, name };
  return null;
}

function clearIdentity() {
  ['archive_role','archive_member_id','archive_groq_key','archive_name'].forEach(k => localStorage.removeItem(k));
}

// ---------------- api fetch with identity headers ----------------

function buildHeaders(identity, extra = {}) {
  const headers = { ...extra };
  if (identity.isAdmin) {
    headers['x-is-admin'] = 'true';
  } else {
    headers['x-groq-api-key'] = identity.groqKey;
    headers['x-member-id']    = identity.memberId;
  }
  return headers;
}

async function apiFetch(path, options = {}, identity = null) {
  if (identity) options.headers = buildHeaders(identity, options.headers || {});
  const res = await fetch(API_BASE + path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { const body = await res.json(); detail = body.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

// ---------------- screen router ----------------

function showScreen(id) {
  ['screen-onboarding','screen-admin-login','screen-app'].forEach(s => {
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

// ---------------- onboarding ----------------

function initOnboarding() {
  const btn   = document.getElementById('ob-submit');
  const err   = document.getElementById('ob-error');
  const nameI = document.getElementById('ob-name');
  const keyI  = document.getElementById('ob-key');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const name = nameI.value.trim();
    const key  = keyI.value.trim();
    if (!name) { err.dataset.tone = 'error'; err.textContent = 'Please enter your name.'; return; }
    if (!key.startsWith('gsk_')) { err.dataset.tone = 'error'; err.textContent = "That doesn't look like a Groq key (should start with gsk_)."; return; }
    btn.disabled = true;
    err.textContent = 'Saving...';
    const memberId = await hashKey(key);
    localStorage.setItem('archive_groq_key',  key);
    localStorage.setItem('archive_member_id', memberId);
    localStorage.setItem('archive_name',      name);
    showScreen('screen-app');
    initApp({ isAdmin: false, memberId, groqKey: key, name });
  });

  keyI.addEventListener('keydown', e => { if (e.key === 'Enter') btn.click(); });
}

// ---------------- admin login ----------------

function initAdminLogin() {
  const btn   = document.getElementById('adm-submit');
  const err   = document.getElementById('adm-error');
  const passI = document.getElementById('adm-password');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const secret = passI.value.trim();
    if (!secret) { err.dataset.tone = 'error'; err.textContent = 'Enter the admin password.'; return; }
    btn.disabled = true;
    err.textContent = 'Checking...';
    try {
      const res = await apiFetch('/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ secret }),
      });
      if (res.success) {
        localStorage.setItem('archive_role', 'admin');
        showScreen('screen-app');
        initApp({ isAdmin: true, memberId: null, groqKey: null, name: 'Admin' });
      } else {
        err.dataset.tone = 'error';
        err.textContent = res.message || 'Incorrect password.';
        btn.disabled = false;
      }
    } catch (e) {
      err.dataset.tone = 'error';
      err.textContent = e.message || 'Could not reach server.';
      btn.disabled = false;
    }
  });

  passI.addEventListener('keydown', e => { if (e.key === 'Enter') btn.click(); });
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

function renderBadge(identity) {
  const badge = document.getElementById('userBadge');
  if (!badge) return;
  badge.innerHTML = 'signed in as <span class="badge-name">' + escapeHtml(identity.name) + '</span>' + (identity.isAdmin ? '<span class="badge-admin">&#9733; admin</span>' : '');
}

// ---------------- tabs ----------------

function initTabs() {
  const tabs = document.querySelectorAll('.desk-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => { t.classList.remove('is-active'); t.setAttribute('aria-selected','false'); });
      tab.classList.add('is-active');
      tab.setAttribute('aria-selected','true');
      document.querySelectorAll('[data-panel]').forEach(panel => {
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

function initDocumentForm(identity) {
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
    message.textContent = 'Accessioning...';
    try {
      const result = await apiFetch('/ingest/document', { method: 'POST', body: formData }, identity);
      message.dataset.tone = 'ok';
      message.textContent = result.source + ' - ' + result.chunks_added + ' chunks added.';
      input.value = '';
      label.textContent = 'Drop a PDF or TXT file here';
      loadCollection(identity);
    } catch (err) {
      message.dataset.tone = 'error';
      message.textContent = err.message || "Couldn't accession that file.";
    } finally { btn.disabled = false; }
  });
}

// ---------------- note form ----------------

function initNoteForm(identity) {
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
    message.textContent = 'Filing...';
    try {
      const result = await apiFetch('/ingest/note', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      }, identity);
      message.dataset.tone = 'ok';
      message.textContent = result.source + ' - ' + result.chunks_added + ' chunks added.';
      titleI.value = '';
      contentI.value = '';
      loadCollection(identity);
    } catch (err) {
      message.dataset.tone = 'error';
      message.textContent = err.message || "Couldn't file that note.";
    } finally { btn.disabled = false; }
  });
}

// ---------------- collection ----------------

async function loadCollection(identity) {
  const list  = document.getElementById('collectionList');
  const empty = document.getElementById('collectionEmpty');
  if (!list) return;
  try {
    const result = await apiFetch('/documents', {}, identity);
    const docs = result.documents || [];
    list.querySelectorAll('.collection-item').forEach(el => el.remove());
    if (docs.length === 0) { empty.style.display = ''; return; }
    empty.style.display = 'none';
    docs.forEach((doc, i) => {
      const li  = document.createElement('li');
      li.className = 'collection-item';
      const num = String(i + 1).padStart(3, '0');
      li.innerHTML = '<span class="call-number">#' + num + '</span><span class="item-name" title="' + escapeHtml(doc.source) + '">' + escapeHtml(doc.source) + '</span>';
      list.appendChild(li);
    });
  } catch (_) {}
}

// ---------------- render card ----------------

function renderCard({ question, answer, sources, isError, isLoading }) {
  const card = document.createElement('article');
  card.className = 'index-card' + (isError ? ' is-error' : '');
  const q = document.createElement('p');
  q.className = 'card-question';
  q.textContent = question;
  card.appendChild(q);
  const a = document.createElement('p');
  a.className = isLoading ? 'card-loading' : 'card-answer';
  a.textContent = isLoading ? 'consulting the index' : answer;
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
      tab.textContent = s.source + (s.page ? ' - p.' + s.page : '');
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

function initAskForm(identity) {
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
      }, identity);
      const card = renderCard({ question, answer: result.answer, sources: result.sources });
      feed.replaceChild(card, loadingCard);
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
  btn.addEventListener('click', () => { clearIdentity(); location.reload(); });
}

// ---------------- main app init ----------------

function initApp(identity) {
  checkHealth();
  renderBadge(identity);
  initTabs();
  initDropzone();
  initDocumentForm(identity);
  initNoteForm(identity);
  initAskForm(identity);
  initLogout();
  loadCollection(identity);
}

// ---------------- boot ----------------

document.addEventListener('DOMContentLoaded', () => {
  const isAdminPage = window.location.search.includes('admin') || window.location.pathname.includes('admin');
  const identity    = getIdentity();

  if (identity) {
    showScreen('screen-app');
    initApp(identity);
  } else if (isAdminPage) {
    showScreen('screen-admin-login');
    initAdminLogin();
  } else {
    showScreen('screen-onboarding');
    initOnboarding();
    initAdminLogin();
  }
});
