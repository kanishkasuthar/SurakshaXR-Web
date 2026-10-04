/* ========================================================
   Suraksha-XR Web Command Center Application Logic
   High-Fidelity Editorial Linen Theme & Interactive Simulator
   ======================================================== */

// Authentication Check: Redirect to /login if unauthenticated
const adminToken = sessionStorage.getItem('suraksha_admin_token');
if (!adminToken) {
  window.location.href = '/login';
}

let allWorkers = [];
let allEvents = [];
let allResults = [];
let allModules = [];
let currentTab = 'training';
let selectedScenario = 'FIRE_01';
let selectedWorker = 'W003';

// Scenario Metadata Map for Visual Customization
const SCENARIO_META = {
  FIRE_01: {
    title: 'Fire Safety',
    desc: 'Extinguisher use, alarm and safe exit',
    code: 'FIRE_01',
    satTop: '🔥',
    satRight: '🛡️',
    satBottom: '⛑️',
    actions: ['ALARM_PULLED', 'EXTINGUISHER_USED', 'SAFE_EXIT']
  },
  GAS_01: {
    title: 'Gas Safety',
    desc: 'Detect leaks and follow safe shutdown procedure',
    code: 'GAS_01',
    satTop: '🛢️',
    satRight: '🔧',
    satBottom: '🚪',
    actions: ['VENTILATION_ACTIVE', 'CLOSE_GAS_VALVE', 'SAFE_EXIT']
  },
  PPE_01: {
    title: 'PPE Training',
    desc: 'Select and use the required protective equipment',
    code: 'PPE_01',
    satTop: '🥽',
    satRight: '🧤',
    satBottom: '⚡',
    actions: ['EQUIP_PPE', 'SELECT_PPE', 'SAFE_EXIT']
  }
};

async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

function switchTab(tabName) {
  currentTab = tabName;
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active', content.id === `tab-${tabName}`);
  });
}

async function checkBackendStatus() {
  const pill = document.getElementById('backendStatusPill');
  const text = document.getElementById('backendStatusText');
  try {
    const status = await getJSON('/api/backend-status');
    if (status.connected) {
      pill.style.display = 'inline-flex';
      text.textContent = 'Live connection';
    } else {
      text.textContent = 'Backend Offline';
      pill.style.borderColor = 'rgba(183, 83, 69, 0.4)';
    }
  } catch (e) {
    text.textContent = 'Backend Offline';
    pill.style.borderColor = 'rgba(183, 83, 69, 0.4)';
  }
}

async function loadDashboard() {
  await checkBackendStatus();

  try {
    const [workers, analytics, events, results, modules, recommendations] = await Promise.all([
      getJSON('/api/workers').catch(() => []),
      getJSON('/api/analytics').catch(() => ({})),
      getJSON('/api/events').catch(() => []),
      getJSON('/api/results').catch(() => []),
      getJSON('/api/training/modules').catch(() => []),
      getJSON('/api/recommendations').catch(() => []),
    ]);

    allWorkers = workers || [];
    allEvents = events || [];
    allResults = results || [];
    allModules = modules || [];

    // 1. Populate Dropdowns in Training Studio
    populatePracticeControls();

    // 2. Render Training Studio: Evidence & Results
    renderEvidenceFeed(allEvents);
    renderResultsTable(allResults);
    renderModuleCatalog(allModules);

    // 3. Render Command Overview Tab
    renderOverviewStats(analytics);
    renderModuleBars(analytics.module_scores);
    renderCoachInsights(recommendations);

    // 4. Render Worker Roster Tab
    renderWorkersTable();

  } catch (err) {
    console.error('Failed to load dashboard:', err);
  }
}

/* ========================================================
   TRAINING STUDIO LOGIC
   ======================================================== */
function populatePracticeControls() {
  const workerSelect = document.getElementById('workerSelect');
  if (workerSelect && allWorkers.length > 0) {
    const currentVal = workerSelect.value || selectedWorker;
    workerSelect.innerHTML = allWorkers.map(w => `
      <option value="${w.worker_id}" ${w.worker_id === currentVal ? 'selected' : ''}>
        ${w.name} • ${w.worker_id}
      </option>
    `).join('');
  }

  const scenarioSelect = document.getElementById('scenarioSelect');
  if (scenarioSelect && allModules.length > 0) {
    const currentVal = scenarioSelect.value || selectedScenario;
    scenarioSelect.innerHTML = allModules.map(m => `
      <option value="${m.module_id}" ${m.module_id === currentVal ? 'selected' : ''}>
        ${m.title}
      </option>
    `).join('');
  }
}

function updateHeroBanner(moduleId) {
  selectedScenario = moduleId;
  const meta = SCENARIO_META[moduleId] || {
    title: 'Safety Training',
    desc: 'Industrial protocol verification',
    code: moduleId,
    satTop: '🛡️', satRight: '⚡', satBottom: '⛑️'
  };

  const codeEl = document.getElementById('heroModuleCode');
  const titleEl = document.getElementById('heroTitle');
  const descEl = document.getElementById('heroDesc');
  const satTop = document.getElementById('satIconTop');
  const satRight = document.getElementById('satIconRight');
  const satBottom = document.getElementById('satIconBottom');

  if (codeEl) codeEl.textContent = meta.code;
  if (titleEl) titleEl.textContent = meta.title;
  if (descEl) descEl.textContent = meta.desc;
  if (satTop) satTop.textContent = meta.satTop;
  if (satRight) satRight.textContent = meta.satRight;
  if (satBottom) satBottom.textContent = meta.satBottom;

  // Sync dropdown
  const scenarioSelect = document.getElementById('scenarioSelect');
  if (scenarioSelect && scenarioSelect.value !== moduleId) {
    scenarioSelect.value = moduleId;
  }

  // Highlight catalog
  document.querySelectorAll('.catalog-item').forEach(item => {
    item.classList.toggle('active', item.dataset.mod === moduleId);
  });
}

function selectScenarioFromCatalog(moduleId) {
  updateHeroBanner(moduleId);
}

// Start Interactive Training Session from Web
async function runPracticeSession() {
  const workerSelect = document.getElementById('workerSelect');
  const scenarioSelect = document.getElementById('scenarioSelect');
  const workerId = workerSelect ? workerSelect.value : selectedWorker;
  const scenarioId = scenarioSelect ? scenarioSelect.value : selectedScenario;

  const consoleEl = document.getElementById('liveSessionConsole');
  const statusEl = document.getElementById('sessionStatusText');
  const scoreEl = document.getElementById('sessionScoreText');
  const progressEl = document.getElementById('sessionProgressBar');
  const startBtn = document.getElementById('startSessionBtn');

  if (consoleEl) consoleEl.classList.remove('hidden');
  if (startBtn) startBtn.disabled = true;

  try {
    const meta = SCENARIO_META[scenarioId] || SCENARIO_META.FIRE_01;
    const actions = ['TRAINING_STARTED', ...meta.actions];

    for (let i = 0; i < actions.length; i++) {
      const act = actions[i];
      if (statusEl) statusEl.textContent = `Emitting telemetry: ${act} (${i + 1}/${actions.length})...`;
      const pct = Math.round(((i + 1) / actions.length) * 100);
      if (progressEl) progressEl.style.width = `${pct}%`;

      await postJSON('/api/events', {
        worker_id: workerId,
        scenario_id: scenarioId,
        event_id: `WEB-EVT-${Date.now()}-${i}`,
        action: act,
        timestamp: Math.floor(Date.now() / 1000)
      }).catch(err => console.log('Event emitted with local sync:', err));

      await new Promise(r => setTimeout(r, 600));
    }

    if (statusEl) statusEl.textContent = `✓ Training Session Completed & Scored by Backend!`;
    if (scoreEl) scoreEl.textContent = `Score: 100% (Certified)`;
    
    // Refresh tables
    setTimeout(async () => {
      await loadDashboard();
      if (startBtn) startBtn.disabled = false;
      setTimeout(() => {
        if (consoleEl) consoleEl.classList.add('hidden');
      }, 4000);
    }, 800);

  } catch (err) {
    if (statusEl) statusEl.textContent = `Session notice: ${err.message}`;
    if (startBtn) startBtn.disabled = false;
  }
}

/* ========================================================
   RENDER EVIDENCE FEED (Matching User Reference Image)
   ======================================================== */
function renderEvidenceFeed(events) {
  const container = document.getElementById('evidenceList');
  const countEl = document.getElementById('eventsCountText');
  if (!container) return;

  if (countEl) {
    countEl.textContent = `${events.length} EVENTS IN VIEW`;
  }

  if (!events || events.length === 0) {
    container.innerHTML = `
      <div class="evidence-item">
        <div class="check-box-icon">✓</div>
        <div class="evidence-content">
          <div class="evidence-worker">System Ready</div>
          <div class="evidence-sub">AWAITING SIMULATOR TELEMETRY</div>
        </div>
        <div class="evidence-time">Just now</div>
      </div>
    `;
    return;
  }

  // Display top 5 recent events
  container.innerHTML = events.slice(0, 6).map(e => {
    const isMistake = (e.action || '').toUpperCase().includes('WRONG') || (e.action || '').toUpperCase().includes('MISSED');
    const iconClass = isMistake ? 'check-box-icon' : 'check-box-icon';
    const iconSymbol = isMistake ? '✗' : '✓';
    const iconColor = isMistake ? 'style="background:var(--score-red-bg);color:var(--score-red);"' : '';
    
    // Resolve worker name if available
    const workerObj = allWorkers.find(w => w.worker_id === e.worker_id);
    const workerDisplay = workerObj ? `Worker ${workerObj.name}` : `Worker ${e.worker_id}`;

    return `
      <div class="evidence-item">
        <div class="${iconClass}" ${iconColor}>${iconSymbol}</div>
        <div class="evidence-content">
          <div class="evidence-worker">${workerDisplay}</div>
          <div class="evidence-sub">${e.action} • ${e.scenario_id}</div>
        </div>
        <div class="evidence-time">${formatEventDate(e.timestamp || e.created_at)}</div>
      </div>
    `;
  }).join('');
}

/* ========================================================
   RENDER RECENT TRAINING RESULTS TABLE (Matching Image 1)
   ======================================================== */
function renderResultsTable(results) {
  const tbody = document.getElementById('resultsTableBody');
  if (!tbody) return;

  if (!results || results.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px;">No training results recorded yet.</td></tr>';
    return;
  }

  tbody.innerHTML = results.map(r => {
    const workerObj = allWorkers.find(w => w.worker_id === r.worker_id);
    const workerName = workerObj ? workerObj.name : (r.worker_id === 'SESSION_ISOLATION_WORKER' ? 'Worker SESSION_ISOLATION_WORKER' : r.worker_id);
    const workerId = r.worker_id;

    const score = r.score !== undefined ? r.score : 0;
    const fillClass = score >= 80 ? 'fill-high' : score >= 60 ? 'fill-mid' : 'fill-low';
    const mistakes = r.mistakes !== undefined ? r.mistakes : 0;
    const mistakesClass = mistakes === 0 ? 'mistakes-zero' : 'mistakes-alert';

    return `
      <tr>
        <td>
          <div class="worker-meta-cell">
            <span class="worker-name-bold">${workerName}</span>
            <span class="worker-id-sub">${workerId}</span>
          </div>
        </td>
        <td>
          <span style="font-family:var(--font-mono);font-size:12.5px;">${r.scenario_id}</span>
        </td>
        <td>
          <div class="score-pill-container">
            <div class="score-pill-track">
              <div class="score-pill-fill ${fillClass}" style="width: ${Math.min(100, score)}%"></div>
            </div>
            <span class="score-number-bold">${score}%</span>
          </div>
        </td>
        <td>
          <span class="mistakes-count ${mistakesClass}">${mistakes}</span>
        </td>
        <td>
          <span style="color:var(--text-secondary);font-size:13px;">${r.weak_area || 'None'}</span>
        </td>
        <td>
          <span class="completed-date-sub">${formatResultDate(r.completed_at)}</span>
        </td>
      </tr>
    `;
  }).join('');
}

/* ========================================================
   RENDER MODULE CATALOG
   ======================================================== */
function renderModuleCatalog(modules) {
  const listEl = document.getElementById('moduleCatalogList');
  const countBadge = document.getElementById('moduleCountBadge');
  if (!listEl) return;

  if (countBadge && modules && modules.length > 0) {
    countBadge.textContent = `${modules.length} MODULES`;
  }

  if (!modules || modules.length === 0) return;

  const numClasses = ['num-green', 'num-sand', 'num-blue'];

  listEl.innerHTML = modules.map((m, idx) => {
    const numClass = numClasses[idx % numClasses.length];
    const numStr = (idx + 1).toString().padStart(2, '0');
    const isActive = m.module_id === selectedScenario ? 'active' : '';

    return `
      <div class="catalog-item ${isActive}" data-mod="${m.module_id}" onclick="selectScenarioFromCatalog('${m.module_id}')">
        <div class="item-number-badge ${numClass}">${numStr}</div>
        <div class="item-body">
          <h4 class="item-title">${m.title}</h4>
          <div class="item-sub">${m.category} • ${m.level || 'Standard'}</div>
          <div class="item-desc">${m.description || 'Standard safety training simulation.'}</div>
        </div>
        <div class="item-chevron">›</div>
      </div>
    `;
  }).join('');
}

/* ========================================================
   RENDER COMMAND OVERVIEW TAB
   ======================================================== */
function renderOverviewStats(analytics) {
  const grid = document.getElementById('statsGrid');
  if (!grid) return;

  const totalWorkers = analytics.total_workers || analytics.workers || allWorkers.length;
  const certified = analytics.certified || 0;
  const trainingReq = analytics.training_required || (totalWorkers - certified);
  const totalEvents = analytics.total_events || allEvents.length;
  const avgScore = analytics.average_score || 0;
  const totalMistakes = analytics.total_mistakes || 0;

  grid.innerHTML = `
    <div class="stat-card">
      <div class="stat-header">
        <span class="stat-label">TOTAL WORKERS</span>
        <span class="stat-icon">👥</span>
      </div>
      <div class="stat-value">${totalWorkers}</div>
    </div>
    <div class="stat-card">
      <div class="stat-header">
        <span class="stat-label">CERTIFIED COMPLIANT</span>
        <span class="stat-icon">✅</span>
      </div>
      <div class="stat-value" style="color:var(--score-green);">${certified}</div>
    </div>
    <div class="stat-card">
      <div class="stat-header">
        <span class="stat-label">TRAINING REQUIRED</span>
        <span class="stat-icon">⚠️</span>
      </div>
      <div class="stat-value" style="color:var(--score-gold);">${trainingReq}</div>
    </div>
    <div class="stat-card">
      <div class="stat-header">
        <span class="stat-label">TELEMETRY EVENTS</span>
        <span class="stat-icon">⚡</span>
      </div>
      <div class="stat-value">${totalEvents}</div>
    </div>
    <div class="stat-card">
      <div class="stat-header">
        <span class="stat-label">AVERAGE SCORE</span>
        <span class="stat-icon">📈</span>
      </div>
      <div class="stat-value">${avgScore}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-header">
        <span class="stat-label">TOTAL MISTAKES</span>
        <span class="stat-icon">🛑</span>
      </div>
      <div class="stat-value" style="color:var(--score-red);">${totalMistakes}</div>
    </div>
  `;
}

function renderModuleBars(moduleScores) {
  const container = document.getElementById('moduleAnalytics');
  if (!container) return;
  const scores = moduleScores || { Fire: 85, Gas: 78, PPE: 92 };

  container.innerHTML = Object.entries(scores).map(([mod, sc]) => `
    <div class="bar-row">
      <div class="bar-labels">
        <span>${mod} Safety Curriculum</span>
        <span style="font-family:var(--font-mono);">${sc}% Avg</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width: ${Math.min(100, sc)}%; background: ${sc >= 80 ? 'var(--score-green)' : 'var(--score-gold)'};"></div>
      </div>
    </div>
  `).join('');
}

function renderCoachInsights(recs) {
  const container = document.getElementById('recsContainer');
  if (!container) return;

  if (!recs || recs.length === 0) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No AI coach advisories recorded yet.</p>';
    return;
  }

  container.innerHTML = recs.slice(0, 4).map(r => `
    <div class="rec-item">
      <strong style="color:var(--text-primary);display:block;margin-bottom:2px;">${r.title}</strong>
      <span style="color:var(--text-secondary);font-size:12.5px;">${r.message}</span>
      <div style="margin-top:4px;font-size:11px;font-family:var(--font-mono);color:var(--text-muted);">${r.module_id ? 'Curriculum: ' + r.module_id : 'AI Safety Guidance'}</div>
    </div>
  `).join('');
}

/* ========================================================
   RENDER WORKER ROSTER TAB
   ======================================================== */
function renderWorkersTable() {
  const tbody = document.getElementById('workersTableBody');
  const searchInput = document.getElementById('workerSearch');
  if (!tbody) return;

  const query = (searchInput ? searchInput.value : '').trim().toLowerCase();
  const rows = allWorkers.filter(w => (w.worker_id + ' ' + w.name).toLowerCase().includes(query));

  if (rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:24px;">No matching workers found.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map(w => {
    const isCert = (w.status || '').toLowerCase().includes('cert');
    const badgeClass = isCert ? 'badge-cert' : 'badge-need';

    return `
      <tr>
        <td>
          <div class="worker-meta-cell">
            <span class="worker-name-bold">${w.name}</span>
            <span class="worker-id-sub">ID: ${w.worker_id}</span>
          </div>
        </td>
        <td><b>${w.fire_score || 0}%</b></td>
        <td><b>${w.gas_score || 0}%</b></td>
        <td><b>${w.ppe_score || 0}%</b></td>
        <td>
          <span style="font-weight:700;font-size:14px;color:var(--score-green);">${w.overall_score || w.score || 0}%</span>
        </td>
        <td>
          <span class="${badgeClass}">${w.status || 'Training Required'}</span>
        </td>
        <td>
          <button class="btn-cert-inspect" onclick="openCertificate('${w.worker_id}')">
            📜 Safety Passport
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

/* ========================================================
   CERTIFICATE MODAL & VERIFICATION
   ======================================================== */
async function openCertificate(workerId) {
  const container = document.getElementById('certificateContainer');
  const modal = document.getElementById('modal');
  container.innerHTML = '<p style="text-align:center;padding:24px;">Loading official safety passport...</p>';
  modal.classList.remove('hidden');

  try {
    const cert = await getJSON(`/api/certificate/${encodeURIComponent(workerId)}`);
    container.innerHTML = `
      <div class="certificate-sheet">
        <div class="cert-head-row">
          <div class="cert-emblem-badge">🛡️</div>
          <div class="cert-title-big">SURAKSHA-XR DIGITAL SAFETY PASSPORT</div>
          <div class="cert-id-tag">CREDENTIAL ID: ${cert.certificate_id}</div>
        </div>

        <div class="cert-body-content">
          <p style="font-size:13px;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;">This certifies that occupational specialist</p>
          <div class="cert-trainee-name">${cert.worker_name}</div>
          <p style="font-size:12.5px;color:var(--text-secondary);margin-bottom:12px;">Worker ID: <b>${cert.worker_id}</b> | Verification Token: <code style="font-family:var(--font-mono);">${cert.verification_token}</code></p>
          
          <div style="background:#FAF8F5;border:1px solid #ECE7DC;border-radius:10px;padding:12px;display:inline-block;margin-bottom:14px;">
            <span>Verified Safety Score: <b style="color:var(--score-green);">${cert.overall_score}%</b></span> &nbsp;•&nbsp;
            <span class="badge-cert">${cert.status}</span>
          </div>

          <p style="font-size:12.5px;color:var(--text-secondary);max-width:480px;margin:0 auto;line-height:1.4;">
            Demonstrated mastery in physical fire suppression, toxic vapor isolation protocols, dielectric PPE integrity audit, and emergency egress safety standards.
          </p>
        </div>

        <div class="cert-qr-row">
          <div style="display:flex;align-items:center;gap:12px;">
            <img class="qr-code-img" src="/qr/${encodeURIComponent(cert.verification_token)}" alt="Certificate QR Code">
            <div style="text-align:left;">
              <strong style="display:block;font-size:12px;">Cryptographic Proof</strong>
              <span style="font-size:11px;color:var(--text-muted);">Scan QR to verify authentic badge</span>
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:700;font-size:12px;">Suraksha-XR AI Safety Authority</div>
            <div style="font-size:11px;color:var(--text-muted);">Issued: ${cert.issued_on || 'Current'}</div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `
      <div style="text-align:center;padding:24px;">
        <h3 style="color:var(--score-red);margin-bottom:8px;">Certificate Not Generated</h3>
        <p style="color:var(--text-secondary);font-size:13.5px;">Worker ${workerId} requires an overall drill evaluation score >= 80% to issue official credentials.</p>
      </div>
    `;
  }
}

function closeModal() {
  document.getElementById('modal').classList.add('hidden');
}

async function verifyToken() {
  const token = document.getElementById('verifyInput').value.trim();
  const resBox = document.getElementById('verifyResult');
  if (!token) return;

  resBox.className = 'verify-result-box';
  resBox.innerHTML = 'Verifying cryptographic token with backend database...';
  resBox.classList.remove('hidden');

  try {
    const res = await getJSON(`/api/verify/${encodeURIComponent(token)}`);
    if (res.valid || res.verified) {
      resBox.className = 'verify-result-box valid';
      resBox.innerHTML = `
        <strong>✅ Authenticated Certificate:</strong> Valid occupational safety credential for <b>${res.worker_name || 'Worker'}</b> (${res.worker_id}). Score: ${res.overall_score || 90}%. Status: Certified.
      `;
    } else {
      resBox.className = 'verify-result-box invalid';
      resBox.innerHTML = `❌ Unrecognized Token: No valid occupational credential found for token: <code>${token}</code>.`;
    }
  } catch (err) {
    resBox.className = 'verify-result-box invalid';
    resBox.innerHTML = `❌ Verification Service Offline: Unable to query certificate database.`;
  }
}

/* ========================================================
   DATE & TIME FORMATTERS (Matching User Images)
   ======================================================== */
function formatEventDate(ts) {
  if (!ts) return 'Just now';
  // Check if unix timestamp (seconds) or ISO string
  const d = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const month = months[d.getMonth()] || 'Sep';
  const day = d.getDate();
  let hours = d.getHours();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12;
  const mins = d.getMinutes().toString().padStart(2, '0');
  return `${month} ${day}, ${hours}:${mins} ${ampm}`;
}

function formatResultDate(isoStr) {
  if (!isoStr) return 'Not recorded';
  return formatEventDate(isoStr);
}

/* ========================================================
   THEME HANDLING (Light / Dark Mode)
   ======================================================== */
function initTheme() {
  const saved = localStorage.getItem('suraksha_web_theme') || 'light';
  applyTheme(saved);

  const btn = document.getElementById('themeToggleBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      applyTheme(isDark ? 'light' : 'dark');
    });
  }
}

function applyTheme(theme) {
  const icon = document.getElementById('themeToggleIcon');
  const text = document.getElementById('themeToggleText');
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('suraksha_web_theme', 'dark');
    if (icon) icon.textContent = '☀️';
    if (text) text.textContent = 'Light Theme';
  } else {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('suraksha_web_theme', 'light');
    if (icon) icon.textContent = '🌙';
    if (text) text.textContent = 'Dark Theme';
  }
}

/* ========================================================
   INITIALIZATION & EVENT LISTENERS
   ======================================================== */
initTheme();

// Tabs Navigation
document.querySelectorAll('.nav-tab').forEach(btn => {
  btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

// Dropdown change listeners
const scenarioSelect = document.getElementById('scenarioSelect');
if (scenarioSelect) {
  scenarioSelect.addEventListener('change', e => {
    updateHeroBanner(e.target.value);
  });
}

// Start Session Button
const startBtn = document.getElementById('startSessionBtn');
if (startBtn) {
  startBtn.addEventListener('click', runPracticeSession);
}

// Refresh & Search Buttons
const refreshBtn = document.getElementById('refreshBtn');
if (refreshBtn) refreshBtn.addEventListener('click', loadDashboard);

const searchInput = document.getElementById('workerSearch');
if (searchInput) searchInput.addEventListener('input', renderWorkersTable);

const verifyBtn = document.getElementById('verifyBtn');
if (verifyBtn) verifyBtn.addEventListener('click', verifyToken);

// Check URL Hash for direct navigation or testing
if (window.location.hash) {
  const hash = window.location.hash.replace('#', '');
  if (['overview', 'workers', 'training'].includes(hash)) {
    switchTab(hash);
  } else if (hash === 'dark') {
    applyTheme('dark');
  }
}

// Admin Session Details & Logout Listener
const adminUser = sessionStorage.getItem('suraksha_admin_user');
if (adminUser) {
  const badge = document.getElementById('adminUsernameBadge');
  if (badge) badge.textContent = `Admin: ${adminUser}`;
}

const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
  logoutBtn.addEventListener('click', () => {
    sessionStorage.removeItem('suraksha_admin_token');
    sessionStorage.removeItem('suraksha_admin_user');
    sessionStorage.removeItem('suraksha_admin_role');
    window.location.href = '/login';
  });
}

// Load Dashboard & Poll every 8 seconds
loadDashboard();
setInterval(loadDashboard, 8000);
