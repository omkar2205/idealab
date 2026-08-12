(() => {
  'use strict';

  const CONFIG = window.IDEALAB_CONFIG || {};
  const TOKEN_KEY = 'idealab_session_token';
  const state = {
    token: sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || '',
    user: null,
    dashboard: {},
    profiles: [],
    ideas: [],
    activity: [],
    currentPage: 'home',
    currentIdea: null,
    busy: false
  };

  const $ = (id) => document.getElementById(id);
  const qsa = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  const els = {
    loginView: $('loginView'), appView: $('appView'), loginForm: $('loginForm'),
    loginEmail: $('loginEmail'), loginPassword: $('loginPassword'), loginError: $('loginError'), loginButton: $('loginButton'),
    passwordDialog: $('passwordDialog'), passwordForm: $('passwordForm'), newPassword: $('newPassword'), confirmPassword: $('confirmPassword'), passwordError: $('passwordError'), changePasswordButton: $('changePasswordButton'),
    sidebar: $('sidebar'), sidebarOpen: $('sidebarOpen'), sidebarClose: $('sidebarClose'), sidebarScrim: $('sidebarScrim'),
    sidebarName: $('sidebarName'), sidebarAvatar: $('sidebarAvatar'), profileMenuButton: $('profileMenuButton'), profileMenu: $('profileMenu'), logoutButton: $('logoutButton'),
    pageTitle: $('pageTitle'), pageKicker: $('pageKicker'), homePage: $('homePage'), boardPage: $('boardPage'), reviewsPage: $('reviewsPage'), profilesPage: $('profilesPage'),
    quickAddIdea: $('quickAddIdea'), topAddIdea: $('topAddIdea'), ideaDialog: $('ideaDialog'), ideaForm: $('ideaForm'), ideaDialogTitle: $('ideaDialogTitle'),
    ideaId: $('ideaId'), ideaTitle: $('ideaTitle'), ideaSummary: $('ideaSummary'), ideaStage: $('ideaStage'), ideaPriority: $('ideaPriority'), ideaOwner: $('ideaOwner'), ideaCategory: $('ideaCategory'), ideaTags: $('ideaTags'), ideaDescription: $('ideaDescription'), saveIdeaButton: $('saveIdeaButton'),
    detailDialog: $('detailDialog'), ideaDetailRoot: $('ideaDetailRoot'), searchButton: $('searchButton'), searchDialog: $('searchDialog'), globalSearch: $('globalSearch'), searchResults: $('searchResults'),
    navIdeaCount: $('navIdeaCount'), toastRegion: $('toastRegion')
  };

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  }

  function safeClass(value) { return String(value || '').replace(/[^A-Za-z0-9_-]/g, '-'); }
  function initials(name) { return String(name || '?').trim().split(/\s+/).slice(0,2).map(x => x[0]).join('').toUpperCase(); }
  function titleCaseAction(action) { return String(action || '').toLowerCase().split('_').map(x => x.charAt(0).toUpperCase()+x.slice(1)).join(' '); }
  function formatDate(value, withTime = false) {
    if (!value) return '';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return new Intl.DateTimeFormat('en-IN', withTime ? {day:'numeric',month:'short',hour:'numeric',minute:'2-digit'} : {day:'numeric',month:'short',year:'numeric'}).format(d);
  }
  function todayLabel() { return new Intl.DateTimeFormat('en-IN',{weekday:'long',day:'numeric',month:'long'}).format(new Date()); }

  function showToast(title, message = '', type = 'success') {
    const node = document.createElement('div');
    node.className = `toast ${type}`;
    node.innerHTML = `<strong>${escapeHtml(title)}</strong>${message ? `<p>${escapeHtml(message)}</p>` : ''}`;
    els.toastRegion.appendChild(node);
    setTimeout(() => node.remove(), 4200);
  }

  function setButtonBusy(button, busy, label) {
    if (!button) return;
    if (busy) {
      button.dataset.original = button.innerHTML;
      button.disabled = true;
      button.textContent = label || 'Working…';
    } else {
      button.disabled = false;
      if (button.dataset.original) button.innerHTML = button.dataset.original;
      delete button.dataset.original;
    }
  }

  async function api(action, data = {}, options = {}) {
    if (!CONFIG.API_URL) throw new Error('The IdeaLab backend URL is not configured.');
    const body = { action, data };
    if (state.token && action !== 'login') body.token = state.token;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT_MS || 25000);
    try {
      const response = await fetch(CONFIG.API_URL, {
        method: 'POST',
        redirect: 'follow',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify(body),
        signal: controller.signal
      });
      const text = await response.text();
      let payload;
      try { payload = JSON.parse(text); }
      catch { throw new Error('IdeaLab received an unreadable response from the backend.'); }
      if (!payload.ok) {
        const err = new Error(payload.message || 'Something went wrong.');
        err.code = payload.error;
        err.details = payload.details;
        if (['SESSION_EXPIRED','AUTH_REQUIRED'].includes(err.code)) clearSession(false);
        throw err;
      }
      return payload;
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('The backend took too long to respond. Please try again.');
      throw error;
    } finally { clearTimeout(timeout); }
  }

  function storeToken(token) {
    state.token = token || '';
    if (state.token) sessionStorage.setItem(TOKEN_KEY, state.token);
    else sessionStorage.removeItem(TOKEN_KEY);
  }

  function clearSession(showLogin = true) {
    state.token = ''; state.user = null; state.dashboard = {}; state.profiles = []; state.ideas = []; state.activity = [];
    sessionStorage.removeItem(TOKEN_KEY); localStorage.removeItem(TOKEN_KEY);
    if (showLogin) showLoginView();
  }

  function showLoginView() {
    els.appView.hidden = true; els.loginView.hidden = false;
    closeMobileSidebar();
    setTimeout(() => els.loginEmail.focus(), 50);
  }

  function showAppView() {
    els.loginView.hidden = true; els.appView.hidden = false;
    hydrateProfileUI();
  }

  function hydrateProfileUI() {
    if (!state.user) return;
    els.sidebarName.textContent = state.user.displayName || state.user.fullName || 'Profile';
    els.sidebarAvatar.textContent = initials(state.user.displayName || state.user.fullName);
    els.sidebarAvatar.style.background = `${state.user.accentColor || '#5869f6'}18`;
    els.sidebarAvatar.style.color = state.user.accentColor || '#5869f6';
    els.navIdeaCount.textContent = state.ideas.filter(i => i.Status !== 'Archived').length;
    els.ideaOwner.innerHTML = state.profiles.map(p => {
      const u = p.user || p;
      return `<option value="${escapeHtml(u.userId)}">${escapeHtml(u.displayName || u.fullName)}</option>`;
    }).join('');
  }

  async function loadAppState() {
    const payload = await api('getAppState');
    state.user = payload.user;
    state.dashboard = payload.dashboard || {};
    state.profiles = payload.profiles || [];
    state.ideas = payload.ideas || [];
    state.activity = payload.recentActivity || [];
    hydrateProfileUI();
  }

  async function refreshAll() {
    await loadAppState();
    renderCurrentPage();
  }

  async function login(event) {
    event.preventDefault();
    els.loginError.hidden = true;
    setButtonBusy(els.loginButton, true, 'Signing in…');
    try {
      const payload = await api('login', { email: els.loginEmail.value.trim(), password: els.loginPassword.value });
      storeToken(payload.token);
      state.user = payload.user;
      showAppView();
      if (payload.mustChangePassword) {
        els.passwordError.hidden = true;
        els.newPassword.value = ''; els.confirmPassword.value = '';
        els.passwordDialog.showModal();
        setTimeout(() => els.newPassword.focus(), 50);
      } else {
        await loadAppState();
        navigate('home');
      }
    } catch (error) {
      els.loginError.textContent = error.message;
      els.loginError.hidden = false;
    } finally { setButtonBusy(els.loginButton, false); }
  }

  async function changePassword(event) {
    event.preventDefault();
    els.passwordError.hidden = true;
    const password = els.newPassword.value;
    if (password !== els.confirmPassword.value) return showPasswordError('The passwords do not match.');
    if (password.length < 10 || !/[a-z]/.test(password) || !/[A-Z]/.test(password) || !/[0-9]/.test(password) || !/[^A-Za-z0-9]/.test(password)) {
      return showPasswordError('Use 10+ characters with uppercase, lowercase, a number and a special character.');
    }
    setButtonBusy(els.changePasswordButton, true, 'Saving…');
    try {
      const payload = await api('changePassword', { newPassword: password });
      storeToken(payload.token); state.user = payload.user;
      els.passwordDialog.close();
      await loadAppState(); navigate('home');
      showToast('Password updated', 'Your IdeaLab account is ready.');
    } catch (error) { showPasswordError(error.message); }
    finally { setButtonBusy(els.changePasswordButton, false); }
  }
  function showPasswordError(message) { els.passwordError.textContent = message; els.passwordError.hidden = false; }

  async function logout() {
    try { if (state.token) await api('logout'); } catch (_) {}
    clearSession(true);
  }

  const pageInfo = {
    home: ['Workspace','Home'], ideas: ['Idea pipeline','Ideas'], brainstorming: ['Explore','Brainstorm'], validation: ['Evidence','Validate'],
    planning: ['Shape it','Planning'], execution: ['Build it','Execution'], reviews: ['Weekly rhythm','Weekly review'], archive: ['History','Archive'], profiles: ['Together','Profiles']
  };

  function navigate(page) {
    state.currentPage = page;
    const [kicker,title] = pageInfo[page] || pageInfo.home;
    els.pageKicker.textContent = kicker; els.pageTitle.textContent = title;
    qsa('.nav-item').forEach(btn => btn.classList.toggle('active', btn.dataset.nav === page));
    els.homePage.hidden = page !== 'home';
    els.boardPage.hidden = !['ideas','brainstorming','validation','planning','execution','archive'].includes(page);
    els.reviewsPage.hidden = page !== 'reviews';
    els.profilesPage.hidden = page !== 'profiles';
    renderCurrentPage(); closeMobileSidebar();
  }

  function renderCurrentPage() {
    if (!state.user) return;
    if (state.currentPage === 'home') renderHome();
    else if (state.currentPage === 'reviews') renderReviews();
    else if (state.currentPage === 'profiles') renderProfiles();
    else renderBoardPage(state.currentPage);
  }

  function renderHome() {
    const d = state.dashboard || {};
    const recent = state.ideas.slice().sort((a,b) => String(b.LastActivityAt||b.UpdatedAt||'').localeCompare(String(a.LastActivityAt||a.UpdatedAt||''))).slice(0,6);
    const name = state.user.displayName || 'there';
    els.homePage.innerHTML = `
      <div class="hero-row"><div class="hero-copy"><p class="eyebrow">Two minds, one place</p><h2>Hey ${escapeHtml(name)}.</h2><p>What are we thinking about today?</p></div><div class="hero-date">${escapeHtml(todayLabel())}</div></div>
      <div class="metric-grid">
        ${metricCard('primary', iconBulb(), d.activeIdeas ?? state.ideas.length, 'Active ideas')}
        ${metricCard('pink', iconChat(), d.byStage?.Brainstorming ?? countStage('Brainstorming'), 'Brainstorming')}
        ${metricCard('amber', iconSearch(), d.byStage?.Validation ?? countStage('Validation'), 'Being validated')}
        ${metricCard('green', iconCheck(), d.openTasks ?? 0, 'Open tasks')}
      </div>
      <div class="dashboard-grid">
        <div class="panel"><div class="panel-head"><div><h3>Idea pulse</h3><p>Recently active ideas</p></div><button class="text-button" data-nav-inline="ideas">View board</button></div>
          ${recent.length ? `<div class="idea-list">${recent.map(ideaListRow).join('')}</div>` : emptyState('No ideas yet','Capture the first rough idea. You can refine it later.','Add your first idea')}
        </div>
        <div class="panel"><div class="panel-head"><div><h3>Recent activity</h3><p>What changed lately</p></div></div>
          ${state.activity.length ? `<div class="activity-list">${state.activity.slice(0,8).map(activityRow).join('')}</div>` : `<div class="activity-list"><div class="activity-row"><span class="activity-dot"></span><strong>IdeaLab is ready</strong><p>Your activity will appear here.</p></div></div>`}
        </div>
      </div>`;
    bindRenderedActions(els.homePage);
  }

  function metricCard(cls, icon, value, label) { return `<article class="metric-card ${cls}"><div class="metric-icon">${icon}</div><strong>${escapeHtml(value ?? 0)}</strong><p>${escapeHtml(label)}</p></article>`; }
  function countStage(stage) { return state.ideas.filter(x => x.Stage === stage && x.Status !== 'Archived').length; }

  function ideaListRow(idea) {
    const owner = userById(idea.OwnerUserID);
    const color = owner?.accentColor || '#5869f6';
    return `<button class="idea-list-row" data-open-idea="${escapeHtml(idea.IdeaID)}"><span class="owner-stripe" style="--owner-color:${color}"></span><span class="idea-list-copy"><strong>${escapeHtml(idea.Title)}</strong><p>${escapeHtml(idea.OneLineSummary || idea.Description || 'No description yet')}</p></span><span class="idea-list-meta"><span class="stage-chip stage-${safeClass(idea.Stage)}">${escapeHtml(idea.Stage)}</span></span></button>`;
  }

  function activityRow(item) {
    return `<div class="activity-row"><span class="activity-dot"></span><strong>${escapeHtml(titleCaseAction(item.Action))}</strong><p>${escapeHtml(formatDate(item.CreatedAt,true))}</p></div>`;
  }

  function renderBoardPage(page) {
    if (page === 'archive') return renderArchive();
    const map = { brainstorming:'Brainstorming', validation:'Validation', planning:'Planning', execution:'Execution' };
    const focusStage = map[page] || '';
    if (focusStage) return renderFocusedStage(focusStage);
    const stages = ['Idea','Brainstorming','Validation','Planning','Execution'];
    const active = state.ideas.filter(i => i.Status !== 'Archived');
    els.boardPage.innerHTML = `<div class="board-toolbar"><div class="filter-group"><button class="filter-button active" data-board-filter="all">All ideas</button><button class="filter-button" data-board-filter="mine">Mine</button><button class="filter-button" data-board-filter="chetana">Chetana</button></div><div class="board-spacer"></div><span class="pill">${active.length} total</span></div><div id="ideaBoard" class="board">${stages.map(stage => boardColumn(stage, active)).join('')}</div>`;
    bindRenderedActions(els.boardPage);
    qsa('[data-board-filter]', els.boardPage).forEach(btn => btn.addEventListener('click', () => filterBoard(btn.dataset.boardFilter, btn)));
  }

  function boardColumn(stage, ideas) {
    const rows = ideas.filter(i => i.Stage === stage);
    return `<section class="board-column"><div class="board-column-head"><h3>${escapeHtml(stage)}</h3><span class="column-count">${rows.length}</span></div><div class="board-cards">${rows.length ? rows.map(ideaCard).join('') : `<div class="empty-column">Nothing here yet</div>`}</div></section>`;
  }

  function filterBoard(mode, button) {
    qsa('[data-board-filter]', els.boardPage).forEach(b => b.classList.toggle('active', b === button));
    let ideas = state.ideas.filter(i => i.Status !== 'Archived');
    if (mode === 'mine') ideas = ideas.filter(i => i.OwnerUserID === state.user.userId);
    if (mode === 'chetana') { const c = state.profiles.map(x=>x.user||x).find(u => /chetana/i.test(u.displayName||'')); if (c) ideas = ideas.filter(i => i.OwnerUserID === c.userId); }
    const stages = ['Idea','Brainstorming','Validation','Planning','Execution'];
    $('ideaBoard').innerHTML = stages.map(stage => boardColumn(stage, ideas)).join('');
    bindRenderedActions($('ideaBoard'));
  }

  function renderFocusedStage(stage) {
    const ideas = state.ideas.filter(i => i.Status !== 'Archived' && i.Stage === stage);
    const subtitle = {Brainstorming:'Challenge it, stretch it, add angles.',Validation:'Turn assumptions into evidence.',Planning:'Give promising ideas enough structure to act.',Execution:'Things we have decided to actually build.'}[stage];
    els.boardPage.innerHTML = `<div class="hero-row"><div class="hero-copy"><p class="eyebrow">${escapeHtml(stage)}</p><h2>${escapeHtml(stage)}</h2><p>${escapeHtml(subtitle)}</p></div><span class="pill">${ideas.length} ideas</span></div>${ideas.length ? `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px">${ideas.map(ideaCard).join('')}</div>` : emptyState(`Nothing in ${stage.toLowerCase()} yet`,`Move an idea here when it is ready for this stage.`,'Add an idea')}`;
    bindRenderedActions(els.boardPage);
  }

  function ideaCard(idea) {
    const owner = userById(idea.OwnerUserID); const color = owner?.accentColor || '#5869f6';
    const tags = String(idea.Tags || '').split(',').map(x=>x.trim()).filter(Boolean).slice(0,3);
    return `<article class="idea-card" data-open-idea="${escapeHtml(idea.IdeaID)}" style="--owner-color:${color}"><div class="idea-card-head"><h4>${escapeHtml(idea.Title)}</h4><span class="priority-dot priority-${safeClass(idea.Priority)}" title="${escapeHtml(idea.Priority||'Medium')} priority"></span></div><p>${escapeHtml(idea.OneLineSummary || idea.Description || 'No summary yet.')}</p>${tags.length ? `<div class="idea-tags">${tags.map(t=>`<span class="idea-tag">${escapeHtml(t)}</span>`).join('')}</div>`:''}<div class="idea-card-foot"><span class="owner-mini"><span class="avatar" style="--owner-color:${color}">${escapeHtml(initials(owner?.displayName||'?'))}</span>${escapeHtml(owner?.displayName||'Unknown')}</span><span class="stage-chip stage-${safeClass(idea.Stage)}">${escapeHtml(idea.Stage)}</span></div></article>`;
  }

  function renderArchive() {
    const rows = state.ideas.filter(i => i.Status === 'Archived');
    els.boardPage.innerHTML = `<div class="hero-row"><div class="hero-copy"><p class="eyebrow">History, not clutter</p><h2>Archive</h2><p>Ideas we parked away remain searchable and recoverable.</p></div></div>${rows.length ? `<div class="archive-list">${rows.map(i=>`<button class="archive-card" style="border:1px solid var(--line);width:100%;text-align:left;cursor:pointer" data-open-idea="${escapeHtml(i.IdeaID)}"><span><h4>${escapeHtml(i.Title)}</h4><p>${escapeHtml(i.OneLineSummary||'Archived idea')}</p></span><span class="pill">${escapeHtml(formatDate(i.ArchivedAt))}</span></button>`).join('')}</div>` : emptyState('Archive is empty','Parked and archived ideas will live here.','Go to ideas','ideas')}`;
    bindRenderedActions(els.boardPage);
  }

  function renderReviews() {
    els.reviewsPage.innerHTML = `<div class="hero-row"><div class="hero-copy"><p class="eyebrow">Weekly rhythm</p><h2>Review the board together.</h2><p>Look at what changed, score promising ideas independently, and leave each review with a next action.</p></div><button id="newReviewBtn" class="button button-primary">${iconPlus()} Start review</button></div><div class="review-layout"><div><div class="review-card"><div class="review-date"><div><h3>This week's snapshot</h3><p>${escapeHtml(todayLabel())}</p></div><span class="pill">${state.dashboard.needsReview || 0} need attention</span></div><div class="profile-stats"><div class="profile-stat"><strong>${state.ideas.filter(i=>i.Status!=='Archived').length}</strong><span>Active ideas</span></div><div class="profile-stat"><strong>${state.dashboard.runningExperiments||0}</strong><span>Experiments</span></div><div class="profile-stat"><strong>${state.dashboard.openTasks||0}</strong><span>Open tasks</span></div></div></div><div id="reviewSessions" class="review-card"><h3>Review sessions</h3><p>Load previous sessions or start a new one.</p><div class="review-list"><div class="review-session"><span><strong>No sessions loaded yet</strong><small>Create the first weekly review when you are ready.</small></span></div></div></div></div><aside class="review-card"><h3>Simple review rule</h3><p style="line-height:1.65;margin-top:10px">Don't try to prove an idea is brilliant. Decide what the smallest useful next step is. A disagreement between your two scores is a discussion prompt, not a problem.</p><div style="margin-top:18px;display:grid;gap:8px"><span class="pill">Excitement · 1–5</span><span class="pill">Market potential · 1–5</span><span class="pill">Feasibility · 1–5</span><span class="pill">Speed to test · 1–5</span><span class="pill">Capital efficiency · 1–5</span><span class="pill">Confidence · 1–5</span></div></aside></div>`;
    $('newReviewBtn').addEventListener('click', createReviewSession);
    loadReviewSessions();
  }

  async function loadReviewSessions() {
    try {
      const payload = await api('listReviewSessions');
      const rows = (payload.reviewSessions || []).slice().reverse();
      const list = $('reviewSessions'); if (!list) return;
      list.innerHTML = `<h3>Review sessions</h3><p>Previous weekly check-ins.</p><div class="review-list">${rows.length ? rows.map(r=>`<div class="review-session"><span><strong>${escapeHtml(r.Title)}</strong><small>${escapeHtml(r.Status)} · ${escapeHtml(r.ReviewDate)}</small></span><span class="pill">${escapeHtml(r.CreatedByUserID===state.user.userId?'You':'Shared')}</span></div>`).join('') : `<div class="review-session"><span><strong>No sessions yet</strong><small>Create the first one when you are ready.</small></span></div>`}</div>`;
    } catch (_) {}
  }

  async function createReviewSession() {
    const button = $('newReviewBtn'); setButtonBusy(button,true,'Creating…');
    try { await api('createReviewSession', {}); showToast('Review created','Your weekly review session is ready.'); await loadReviewSessions(); }
    catch (e) { showToast('Could not create review',e.message,'error'); }
    finally { setButtonBusy(button,false); }
  }

  function renderProfiles() {
    els.profilesPage.innerHTML = `<div class="hero-row"><div class="hero-copy"><p class="eyebrow">Your two-person team</p><h2>Different perspectives, shared board.</h2><p>Profiles show contribution and momentum, not a leaderboard.</p></div></div><div class="profile-grid">${state.profiles.map(profileCard).join('')}</div>`;
  }

  function profileCard(profile) {
    const u = profile.user || profile, s = profile.stats || {}, color = u.accentColor || '#5869f6';
    return `<article class="profile-card" style="--owner-color:${color}"><div class="profile-hero"><span class="avatar" style="background:${color}18;color:${color}">${escapeHtml(initials(u.displayName||u.fullName))}</span><span><h3>${escapeHtml(u.displayName||u.fullName)}</h3><p>${escapeHtml(u.email||'')}</p></span></div><div class="profile-stats"><div class="profile-stat"><strong>${s.ideasSubmitted||0}</strong><span>Ideas</span></div><div class="profile-stat"><strong>${s.activeIdeas||0}</strong><span>Active</span></div><div class="profile-stat"><strong>${s.brainstormNotes||0}</strong><span>Notes</span></div><div class="profile-stat"><strong>${s.experimentsOwned||0}</strong><span>Experiments</span></div><div class="profile-stat"><strong>${s.openTasks||0}</strong><span>Open tasks</span></div><div class="profile-stat"><strong>${s.movedToPlanning||0}</strong><span>Planning+</span></div></div></article>`;
  }

  function emptyState(title, text, buttonText, nav) {
    return `<div class="empty-state"><div class="empty-state-inner"><div class="empty-icon">${iconBulb()}</div><h3>${escapeHtml(title)}</h3><p>${escapeHtml(text)}</p><button class="button button-primary" ${nav?`data-nav-inline="${escapeHtml(nav)}"`:'data-new-idea'}>${escapeHtml(buttonText)}</button></div></div>`;
  }

  function openIdeaForm(idea = null) {
    els.ideaForm.reset();
    els.ideaId.value = idea?.IdeaID || '';
    els.ideaDialogTitle.textContent = idea ? 'Edit idea' : 'New idea';
    els.ideaTitle.value = idea?.Title || '';
    els.ideaSummary.value = idea?.OneLineSummary || '';
    els.ideaStage.value = idea?.Stage || 'Idea';
    els.ideaPriority.value = idea?.Priority || 'Medium';
    els.ideaCategory.value = idea?.Category || '';
    els.ideaTags.value = idea?.Tags || '';
    els.ideaDescription.value = idea?.Description || '';
    if (idea?.OwnerUserID) els.ideaOwner.value = idea.OwnerUserID;
    else if (state.user) els.ideaOwner.value = state.user.userId;
    els.ideaDialog.showModal();
    setTimeout(()=>els.ideaTitle.focus(),50);
  }

  async function saveIdea(event) {
    event.preventDefault();
    const id = els.ideaId.value;
    const data = { title: els.ideaTitle.value.trim(), oneLineSummary: els.ideaSummary.value.trim(), stage: els.ideaStage.value, priority: els.ideaPriority.value, ownerUserId: els.ideaOwner.value, category: els.ideaCategory.value.trim(), tags: els.ideaTags.value.trim(), description: els.ideaDescription.value.trim() };
    if (!data.title) return;
    setButtonBusy(els.saveIdeaButton,true,'Saving…');
    try {
      if (id) { data.ideaId = id; await api('updateIdea', data); }
      else await api('createIdea', data);
      els.ideaDialog.close(); await refreshAll();
      showToast(id ? 'Idea updated' : 'Idea captured', id ? 'Changes saved.' : 'It is on the board.');
    } catch (e) { showToast('Could not save idea',e.message,'error'); }
    finally { setButtonBusy(els.saveIdeaButton,false); }
  }

  async function openIdeaDetail(id) {
    els.ideaDetailRoot.innerHTML = `<div class="modal-body"><div style="height:240px" class="skeleton"></div></div>`;
    els.detailDialog.showModal();
    try {
      const payload = await api('getIdea',{ideaId:id});
      const detail = payload.idea || {};
      const idea = detail.idea || detail;
      state.currentIdea = idea;
      const owner = userById(idea.OwnerUserID), color = owner?.accentColor || '#5869f6';
      const brainstorm = detail.brainstorm || [], tasks = detail.tasks || [], experiments = detail.experiments || [], attachments = detail.attachments || [];
      els.ideaDetailRoot.innerHTML = `<div style="position:relative"><button class="icon-button detail-close" data-close-detail>${iconClose()}</button><div class="detail-hero"><div class="detail-meta"><span class="stage-chip stage-${safeClass(idea.Stage)}">${escapeHtml(idea.Stage)}</span><span class="pill" style="color:${color}">${escapeHtml(owner?.displayName||'Unknown')}</span>${idea.Category?`<span class="pill">${escapeHtml(idea.Category)}</span>`:''}</div><h2>${escapeHtml(idea.Title)}</h2><p>${escapeHtml(idea.OneLineSummary||'No one-line summary yet.')}</p></div><div class="detail-body"><section class="detail-section"><h3>Raw notes</h3><div class="detail-text">${escapeHtml(idea.Description||'No notes yet.')}</div></section><section class="detail-section"><h3>Brainstorm (${brainstorm.length})</h3>${brainstorm.length?brainstorm.slice().reverse().map(n=>`<div class="detail-text" style="margin-bottom:7px"><strong>${escapeHtml(userById(n.UserID)?.displayName||'IdeaLab')}</strong><br>${escapeHtml(n.Content)}</div>`).join(''):'<div class="detail-text">No brainstorm notes yet.</div>'}<div style="display:flex;gap:8px;margin-top:9px"><input id="brainstormInput" placeholder="Add a thought, question or angle…" style="flex:1;height:42px;border:1px solid var(--line);border-radius:10px;padding:0 11px"><button id="addBrainstormBtn" class="button button-secondary">Add</button></div></section><section class="detail-section"><h3>Progress</h3><div style="display:flex;gap:8px;flex-wrap:wrap"><span class="pill">${tasks.length} tasks</span><span class="pill">${experiments.length} experiments</span><span class="pill">${attachments.length} attachments</span></div></section></div><div class="detail-actions"><button class="button button-danger" data-archive-idea="${escapeHtml(idea.IdeaID)}">Archive</button><button class="button button-secondary" data-edit-current>Edit idea</button></div></div>`;
      $('[data-close-detail]',els.ideaDetailRoot)?.addEventListener('click',()=>els.detailDialog.close());
      $('[data-edit-current]',els.ideaDetailRoot)?.addEventListener('click',()=>{els.detailDialog.close();openIdeaForm(state.currentIdea);});
      $('[data-archive-idea]',els.ideaDetailRoot)?.addEventListener('click',()=>archiveIdea(idea.IdeaID));
      $('addBrainstormBtn')?.addEventListener('click',()=>addBrainstorm(idea.IdeaID));
    } catch (e) { els.ideaDetailRoot.innerHTML = `<div class="modal-body">${emptyState('Could not load this idea',e.message,'Close')}</div>`; $('[data-new-idea]',els.ideaDetailRoot)?.addEventListener('click',()=>els.detailDialog.close()); }
  }

  async function addBrainstorm(ideaId) {
    const input = $('brainstormInput'), button = $('addBrainstormBtn'); if (!input?.value.trim()) return;
    setButtonBusy(button,true,'Adding…');
    try { await api('addBrainstorm',{ideaId,content:input.value.trim(),noteType:'Note'}); await openIdeaDetailRefresh(ideaId); showToast('Thought added'); }
    catch(e){showToast('Could not add note',e.message,'error');setButtonBusy(button,false);}
  }
  async function openIdeaDetailRefresh(id){ els.detailDialog.close(); await refreshAll(); await openIdeaDetail(id); }

  async function archiveIdea(ideaId) {
    if (!confirm('Archive this idea? You can still find it in Archive.')) return;
    try { await api('archiveIdea',{ideaId}); els.detailDialog.close(); await refreshAll(); showToast('Idea archived'); }
    catch(e){showToast('Could not archive idea',e.message,'error');}
  }

  function userById(id) { return state.profiles.map(p=>p.user||p).find(u=>u.userId===id) || (state.user?.userId===id?state.user:null); }

  function openSearch() {
    els.globalSearch.value=''; renderSearchResults(''); els.searchDialog.showModal(); setTimeout(()=>els.globalSearch.focus(),40);
  }
  function renderSearchResults(query) {
    const q=String(query||'').trim().toLowerCase();
    const rows=state.ideas.filter(i=>!q||[i.Title,i.OneLineSummary,i.Description,i.Category,i.Tags].join(' ').toLowerCase().includes(q)).slice(0,12);
    els.searchResults.innerHTML=rows.length?rows.map(ideaListRow).join(''):`<div style="padding:25px;text-align:center;color:var(--faint)">No matching ideas.</div>`;
    bindRenderedActions(els.searchResults);
  }

  function bindRenderedActions(root) {
    qsa('[data-open-idea]',root).forEach(el=>el.addEventListener('click',()=>openIdeaDetail(el.dataset.openIdea)));
    qsa('[data-nav-inline]',root).forEach(el=>el.addEventListener('click',()=>navigate(el.dataset.navInline)));
    qsa('[data-new-idea]',root).forEach(el=>el.addEventListener('click',()=>openIdeaForm()));
  }

  function openMobileSidebar(){els.sidebar.classList.add('mobile-open');els.sidebarScrim.hidden=false;}
  function closeMobileSidebar(){els.sidebar.classList.remove('mobile-open');els.sidebarScrim.hidden=true;}

  function iconBulb(){return '<svg viewBox="0 0 24 24"><path d="M9 18h6M10 22h4M8.5 14.5C7 13.5 6 11.8 6 9.8A6 6 0 0 1 18 9.8c0 2-1 3.7-2.5 4.7-.7.5-1 1.1-1 1.8h-5c0-.7-.3-1.3-1-1.8Z"/></svg>'}
  function iconChat(){return '<svg viewBox="0 0 24 24"><path d="M4 5h16v11H7l-3 3V5Z"/><path d="M8 9h8M8 12h5"/></svg>'}
  function iconSearch(){return '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4"/></svg>'}
  function iconCheck(){return '<svg viewBox="0 0 24 24"><path d="M5 12l4 4L19 6"/></svg>'}
  function iconPlus(){return '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>'}
  function iconClose(){return '<svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg>'}

  function bindStaticEvents() {
    els.loginForm.addEventListener('submit',login);
    els.passwordForm.addEventListener('submit',changePassword);
    els.ideaForm.addEventListener('submit',saveIdea);
    els.logoutButton.addEventListener('click',logout);
    els.quickAddIdea.addEventListener('click',()=>openIdeaForm());
    els.topAddIdea.addEventListener('click',()=>openIdeaForm());
    els.searchButton.addEventListener('click',openSearch);
    els.globalSearch.addEventListener('input',e=>renderSearchResults(e.target.value));
    els.profileMenuButton.addEventListener('click',()=>{els.profileMenu.hidden=!els.profileMenu.hidden;els.profileMenuButton.setAttribute('aria-expanded',String(!els.profileMenu.hidden));});
    els.sidebarOpen.addEventListener('click',openMobileSidebar); els.sidebarClose.addEventListener('click',closeMobileSidebar); els.sidebarScrim.addEventListener('click',closeMobileSidebar);
    qsa('[data-nav]').forEach(btn=>btn.addEventListener('click',e=>{e.preventDefault();navigate(btn.dataset.nav);els.profileMenu.hidden=true;}));
    qsa('[data-close-dialog]').forEach(btn=>btn.addEventListener('click',()=>$(btn.dataset.closeDialog)?.close()));
    qsa('[data-password-toggle]').forEach(btn=>btn.addEventListener('click',()=>{const input=$(btn.dataset.passwordToggle);if(!input)return;input.type=input.type==='password'?'text':'password';btn.setAttribute('aria-label',input.type==='password'?'Show password':'Hide password');}));
    document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();if(!els.appView.hidden)openSearch();}if(e.key==='Escape')closeMobileSidebar();});
    [els.ideaDialog,els.detailDialog,els.searchDialog].forEach(d=>d.addEventListener('click',e=>{if(e.target===d)d.close();}));
  }

  async function boot() {
    bindStaticEvents();
    if (!state.token) return showLoginView();
    try { await loadAppState(); showAppView(); navigate('home'); }
    catch { clearSession(true); }
  }

  boot();
})();
