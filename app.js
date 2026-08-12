(() => {
  'use strict';

  const CONFIG = window.IDEALAB_CONFIG || {};
  const TOKEN_KEY = 'idealab_session_token';
  const state = { token: sessionStorage.getItem(TOKEN_KEY) || '', user: null, dashboard: {}, profiles: [], ideas: [], archive: [], activity: [], currentPage: 'home', currentIdea: null };
  const $ = id => document.getElementById(id);
  const qsa = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const one = (selector, root = document) => root.querySelector(selector);

  const els = {
    loginView:$('loginView'),appView:$('appView'),loginForm:$('loginForm'),loginEmail:$('loginEmail'),loginPassword:$('loginPassword'),loginError:$('loginError'),loginButton:$('loginButton'),
    passwordDialog:$('passwordDialog'),passwordForm:$('passwordForm'),newPassword:$('newPassword'),confirmPassword:$('confirmPassword'),passwordError:$('passwordError'),changePasswordButton:$('changePasswordButton'),
    sidebar:$('sidebar'),sidebarOpen:$('sidebarOpen'),sidebarClose:$('sidebarClose'),sidebarScrim:$('sidebarScrim'),sidebarName:$('sidebarName'),sidebarAvatar:$('sidebarAvatar'),profileMenuButton:$('profileMenuButton'),profileMenu:$('profileMenu'),logoutButton:$('logoutButton'),
    pageTitle:$('pageTitle'),pageKicker:$('pageKicker'),homePage:$('homePage'),boardPage:$('boardPage'),reviewsPage:$('reviewsPage'),profilesPage:$('profilesPage'),quickAddIdea:$('quickAddIdea'),topAddIdea:$('topAddIdea'),
    ideaDialog:$('ideaDialog'),ideaForm:$('ideaForm'),ideaDialogTitle:$('ideaDialogTitle'),ideaId:$('ideaId'),ideaTitle:$('ideaTitle'),ideaSummary:$('ideaSummary'),ideaStage:$('ideaStage'),ideaPriority:$('ideaPriority'),ideaOwner:$('ideaOwner'),ideaCategory:$('ideaCategory'),ideaTags:$('ideaTags'),ideaDescription:$('ideaDescription'),saveIdeaButton:$('saveIdeaButton'),
    detailDialog:$('detailDialog'),ideaDetailRoot:$('ideaDetailRoot'),searchButton:$('searchButton'),searchDialog:$('searchDialog'),globalSearch:$('globalSearch'),searchResults:$('searchResults'),navIdeaCount:$('navIdeaCount'),toastRegion:$('toastRegion')
  };

  const pageInfo = {
    home:['Workspace','Home'],ideas:['Idea pipeline','Ideas'],brainstorming:['Explore','Brainstorm'],validation:['Evidence','Validate'],planning:['Shape it','Planning'],execution:['Build it','Execution'],reviews:['Weekly rhythm','Weekly review'],archive:['History','Archive'],profiles:['Together','Profiles']
  };

  function esc(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
  function safe(v){return String(v||'').replace(/[^A-Za-z0-9_-]/g,'-');}
  function initials(v){return String(v||'?').trim().split(/\s+/).slice(0,2).map(x=>x[0]).join('').toUpperCase();}
  function formatDate(v,time=false){if(!v)return'';const d=new Date(v);if(Number.isNaN(d.getTime()))return String(v);return new Intl.DateTimeFormat('en-IN',time?{day:'numeric',month:'short',hour:'numeric',minute:'2-digit'}:{day:'numeric',month:'short',year:'numeric'}).format(d);}
  function todayLabel(){return new Intl.DateTimeFormat('en-IN',{weekday:'long',day:'numeric',month:'long'}).format(new Date());}
  function actionLabel(v){return String(v||'').toLowerCase().split('_').map(x=>x.charAt(0).toUpperCase()+x.slice(1)).join(' ');}
  function iconBulb(){return'<svg viewBox="0 0 24 24"><path d="M9 18h6M10 22h4M8.5 14.5C7 13.5 6 11.8 6 9.8A6 6 0 0 1 18 9.8c0 2-1 3.7-2.5 4.7-.7.5-1 1.1-1 1.8h-5c0-.7-.3-1.3-1-1.8Z"/></svg>'}
  function iconChat(){return'<svg viewBox="0 0 24 24"><path d="M4 5h16v11H7l-3 3V5Z"/><path d="M8 9h8M8 12h5"/></svg>'}
  function iconSearch(){return'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4"/></svg>'}
  function iconCheck(){return'<svg viewBox="0 0 24 24"><path d="M5 12l4 4L19 6"/></svg>'}
  function iconPlus(){return'<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>'}
  function iconClose(){return'<svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg>'}

  function toast(title,message='',type='success'){const n=document.createElement('div');n.className=`toast ${type}`;n.innerHTML=`<strong>${esc(title)}</strong>${message?`<p>${esc(message)}</p>`:''}`;els.toastRegion.appendChild(n);setTimeout(()=>n.remove(),4200);}
  function busy(btn,on,label){if(!btn)return;if(on){btn.dataset.old=btn.innerHTML;btn.disabled=true;btn.textContent=label||'Working…';}else{btn.disabled=false;if(btn.dataset.old)btn.innerHTML=btn.dataset.old;delete btn.dataset.old;}}

  async function api(action,data={}){
    if(!CONFIG.API_URL)throw new Error('The IdeaLab backend URL is not configured.');
    const body={action,data};if(state.token&&action!=='login')body.token=state.token;
    const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),CONFIG.REQUEST_TIMEOUT_MS||25000);
    try{
      const res=await fetch(CONFIG.API_URL,{method:'POST',redirect:'follow',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(body),signal:controller.signal});
      const text=await res.text();let payload;try{payload=JSON.parse(text);}catch{throw new Error('IdeaLab received an unreadable response from the backend.');}
      if(!payload.ok){const e=new Error(payload.message||'Something went wrong.');e.code=payload.error;e.details=payload.details;if(['SESSION_EXPIRED','AUTH_REQUIRED'].includes(e.code))clearSession(false);throw e;}
      return payload;
    }catch(e){if(e.name==='AbortError')throw new Error('The backend took too long to respond. Please try again.');throw e;}finally{clearTimeout(timer);}
  }

  function saveToken(token){state.token=token||'';if(state.token)sessionStorage.setItem(TOKEN_KEY,state.token);else sessionStorage.removeItem(TOKEN_KEY);}
  function clearSession(show=true){state.token='';state.user=null;state.dashboard={};state.profiles=[];state.ideas=[];state.archive=[];state.activity=[];sessionStorage.removeItem(TOKEN_KEY);if(show)showLogin();}
  function showLogin(){els.appView.hidden=true;els.loginView.hidden=false;closeSidebar();setTimeout(()=>els.loginEmail.focus(),40);}
  function showApp(){els.loginView.hidden=true;els.appView.hidden=false;hydrateProfile();}
  function userById(id){return state.profiles.map(p=>p.user||p).find(u=>u.userId===id)||(state.user?.userId===id?state.user:null);}

  function hydrateProfile(){
    if(!state.user)return;
    const color=state.user.accentColor||'#5869f6';els.sidebarName.textContent=state.user.displayName||state.user.fullName||'Profile';els.sidebarAvatar.textContent=initials(state.user.displayName||state.user.fullName);els.sidebarAvatar.style.background=`${color}18`;els.sidebarAvatar.style.color=color;els.navIdeaCount.textContent=state.ideas.length;
    els.ideaOwner.innerHTML=state.profiles.map(p=>{const u=p.user||p;return`<option value="${esc(u.userId)}">${esc(u.displayName||u.fullName)}</option>`}).join('');
  }

  async function loadState(){const p=await api('getAppState');state.user=p.user;state.dashboard=p.dashboard||{};state.profiles=p.profiles||[];state.ideas=p.ideas||[];state.activity=p.recentActivity||[];hydrateProfile();}
  async function refresh(){await loadState();renderCurrent();}

  async function login(e){
    e.preventDefault();els.loginError.hidden=true;busy(els.loginButton,true,'Signing in…');
    try{const p=await api('login',{email:els.loginEmail.value.trim(),password:els.loginPassword.value});saveToken(p.token);state.user=p.user;showApp();if(p.mustChangePassword){els.newPassword.value='';els.confirmPassword.value='';els.passwordError.hidden=true;els.passwordDialog.showModal();setTimeout(()=>els.newPassword.focus(),40);}else{await loadState();navigate('home');}}
    catch(err){els.loginError.textContent=err.message;els.loginError.hidden=false;}finally{busy(els.loginButton,false);}
  }

  async function changePassword(e){
    e.preventDefault();els.passwordError.hidden=true;const p=els.newPassword.value;
    if(p!==els.confirmPassword.value)return passwordError('The passwords do not match.');
    if(p.length<10||!/[a-z]/.test(p)||!/[A-Z]/.test(p)||!/[0-9]/.test(p)||!/[^A-Za-z0-9]/.test(p))return passwordError('Use 10+ characters with uppercase, lowercase, a number and a special character.');
    busy(els.changePasswordButton,true,'Saving…');try{const r=await api('changePassword',{newPassword:p});saveToken(r.token);state.user=r.user;els.passwordDialog.close();await loadState();navigate('home');toast('Password updated','Your IdeaLab account is ready.');}catch(err){passwordError(err.message);}finally{busy(els.changePasswordButton,false);}
  }
  function passwordError(msg){els.passwordError.textContent=msg;els.passwordError.hidden=false;}
  async function logout(){try{if(state.token)await api('logout');}catch{}clearSession(true);}

  function navigate(page){state.currentPage=page;const [k,t]=pageInfo[page]||pageInfo.home;els.pageKicker.textContent=k;els.pageTitle.textContent=t;qsa('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.nav===page));els.homePage.hidden=page!=='home';els.boardPage.hidden=!['ideas','brainstorming','validation','planning','execution','archive'].includes(page);els.reviewsPage.hidden=page!=='reviews';els.profilesPage.hidden=page!=='profiles';renderCurrent();closeSidebar();}
  function renderCurrent(){if(!state.user)return;if(state.currentPage==='home')renderHome();else if(state.currentPage==='reviews')renderReviews();else if(state.currentPage==='profiles')renderProfiles();else if(state.currentPage==='archive')renderArchive();else renderBoardPage(state.currentPage);}

  function metric(cls,icon,val,label){return`<article class="metric-card ${cls}"><div class="metric-icon">${icon}</div><strong>${esc(val??0)}</strong><p>${esc(label)}</p></article>`;}
  function empty(title,text,button='Add idea',nav=''){return`<div class="empty-state"><div class="empty-state-inner"><div class="empty-icon">${iconBulb()}</div><h3>${esc(title)}</h3><p>${esc(text)}</p><button class="button button-primary" ${nav?`data-nav-inline="${esc(nav)}"`:'data-new-idea'}>${esc(button)}</button></div></div>`;}
  function ideaRow(i){const u=userById(i.OwnerUserID),color=u?.accentColor||'#5869f6';return`<button class="idea-list-row" data-open-idea="${esc(i.IdeaID)}"><span class="owner-stripe" style="--owner-color:${color}"></span><span class="idea-list-copy"><strong>${esc(i.Title)}</strong><p>${esc(i.OneLineSummary||i.Description||'No description yet')}</p></span><span class="idea-list-meta"><span class="stage-chip stage-${safe(i.Stage)}">${esc(i.Stage)}</span></span></button>`;}
  function activityRow(a){return`<div class="activity-row"><span class="activity-dot"></span><strong>${esc(actionLabel(a.Action))}</strong><p>${esc(formatDate(a.CreatedAt,true))}</p></div>`;}

  function renderHome(){
    const d=state.dashboard||{},recent=state.ideas.slice().sort((a,b)=>String(b.LastActivityAt||b.UpdatedAt||'').localeCompare(String(a.LastActivityAt||a.UpdatedAt||''))).slice(0,6),name=state.user.displayName||'there';
    els.homePage.innerHTML=`<div class="hero-row"><div class="hero-copy"><p class="eyebrow">Two minds, one place</p><h2>Hey ${esc(name)}.</h2><p>What are we thinking about today?</p></div><div class="hero-date">${esc(todayLabel())}</div></div><div class="metric-grid">${metric('primary',iconBulb(),d.activeIdeas??state.ideas.length,'Active ideas')}${metric('pink',iconChat(),d.byStage?.Brainstorming??0,'Brainstorming')}${metric('amber',iconSearch(),d.byStage?.Validation??0,'Being validated')}${metric('green',iconCheck(),d.openTasks??0,'Open tasks')}</div><div class="dashboard-grid"><div class="panel"><div class="panel-head"><div><h3>Idea pulse</h3><p>Recently active ideas</p></div><button class="text-button" data-nav-inline="ideas">View board</button></div>${recent.length?`<div class="idea-list">${recent.map(ideaRow).join('')}</div>`:empty('No ideas yet','Capture the first rough idea. You can refine it later.','Add your first idea')}</div><div class="panel"><div class="panel-head"><div><h3>Recent activity</h3><p>What changed lately</p></div></div>${state.activity.length?`<div class="activity-list">${state.activity.slice(0,8).map(activityRow).join('')}</div>`:`<div class="activity-list"><div class="activity-row"><span class="activity-dot"></span><strong>IdeaLab is ready</strong><p>Your activity will appear here.</p></div></div>`}</div></div>`;
    bindRendered(els.homePage);
  }

  function ideaCard(i){const u=userById(i.OwnerUserID),color=u?.accentColor||'#5869f6',tags=String(i.Tags||'').split(',').map(x=>x.trim()).filter(Boolean).slice(0,3);return`<article class="idea-card" data-open-idea="${esc(i.IdeaID)}" style="--owner-color:${color}"><div class="idea-card-head"><h4>${esc(i.Title)}</h4><span class="priority-dot priority-${safe(i.Priority)}" title="${esc(i.Priority||'Medium')} priority"></span></div><p>${esc(i.OneLineSummary||i.Description||'No summary yet.')}</p>${tags.length?`<div class="idea-tags">${tags.map(t=>`<span class="idea-tag">${esc(t)}</span>`).join('')}</div>`:''}<div class="idea-card-foot"><span class="owner-mini"><span class="avatar" style="--owner-color:${color}">${esc(initials(u?.displayName||'?'))}</span>${esc(u?.displayName||'Unknown')}</span><span class="stage-chip stage-${safe(i.Stage)}">${esc(i.Stage)}</span></div></article>`;}
  function column(stage,ideas){const rows=ideas.filter(i=>i.Stage===stage);return`<section class="board-column"><div class="board-column-head"><h3>${esc(stage)}</h3><span class="column-count">${rows.length}</span></div><div class="board-cards">${rows.length?rows.map(ideaCard).join(''):'<div class="empty-column">Nothing here yet</div>'}</div></section>`;}

  function renderBoardPage(page){
    const map={brainstorming:'Brainstorming',validation:'Validation',planning:'Planning',execution:'Execution'},focus=map[page]||'';
    if(focus)return renderFocus(focus);
    const stages=['Idea','Brainstorming','Validation','Planning','Execution'];
    els.boardPage.innerHTML=`<div class="board-toolbar"><div class="filter-group"><button class="filter-button active" data-board-filter="all">All ideas</button><button class="filter-button" data-board-filter="mine">Mine</button><button class="filter-button" data-board-filter="chetana">Chetana</button></div><div class="board-spacer"></div><span class="pill">${state.ideas.length} total</span></div><div id="ideaBoard" class="board">${stages.map(s=>column(s,state.ideas)).join('')}</div>`;
    bindRendered(els.boardPage);qsa('[data-board-filter]',els.boardPage).forEach(b=>b.addEventListener('click',()=>filterBoard(b.dataset.boardFilter,b)));
  }
  function filterBoard(mode,btn){qsa('[data-board-filter]',els.boardPage).forEach(b=>b.classList.toggle('active',b===btn));let rows=state.ideas;if(mode==='mine')rows=rows.filter(i=>i.OwnerUserID===state.user.userId);if(mode==='chetana'){const c=state.profiles.map(p=>p.user||p).find(u=>/chetana/i.test(u.displayName||''));if(c)rows=rows.filter(i=>i.OwnerUserID===c.userId);}const stages=['Idea','Brainstorming','Validation','Planning','Execution'];$('ideaBoard').innerHTML=stages.map(s=>column(s,rows)).join('');bindRendered($('ideaBoard'));}
  function renderFocus(stage){const rows=state.ideas.filter(i=>i.Stage===stage),copy={Brainstorming:'Challenge it, stretch it, add angles.',Validation:'Turn assumptions into evidence.',Planning:'Give promising ideas enough structure to act.',Execution:'Things we have decided to actually build.'}[stage];els.boardPage.innerHTML=`<div class="hero-row"><div class="hero-copy"><p class="eyebrow">${esc(stage)}</p><h2>${esc(stage)}</h2><p>${esc(copy)}</p></div><span class="pill">${rows.length} ideas</span></div>${rows.length?`<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px">${rows.map(ideaCard).join('')}</div>`:empty(`Nothing in ${stage.toLowerCase()} yet`,`Move an idea here when it is ready for this stage.`)}`;bindRendered(els.boardPage);}

  function renderArchive(){
    els.boardPage.innerHTML=`<div class="hero-row"><div class="hero-copy"><p class="eyebrow">History, not clutter</p><h2>Archive</h2><p>Ideas we parked away remain searchable and recoverable.</p></div></div><div id="archiveRoot"><div class="empty-state"><div class="empty-state-inner"><p>Loading archive…</p></div></div></div>`;
    loadArchive();
  }
  async function loadArchive(){const root=$('archiveRoot');if(!root)return;try{const p=await api('listIdeas',{status:'Archived'});state.archive=p.ideas||[];root.innerHTML=state.archive.length?`<div class="archive-list">${state.archive.map(i=>`<button class="archive-card" style="width:100%;text-align:left;cursor:pointer" data-open-idea="${esc(i.IdeaID)}"><span><h4>${esc(i.Title)}</h4><p>${esc(i.OneLineSummary||'Archived idea')}</p></span><span class="pill">${esc(formatDate(i.ArchivedAt))}</span></button>`).join('')}</div>`:empty('Archive is empty','Parked and archived ideas will live here.','Go to ideas','ideas');bindRendered(root);}catch(e){root.innerHTML=empty('Could not load archive',e.message,'Go to ideas','ideas');bindRendered(root);}}

  function renderReviews(){
    els.reviewsPage.innerHTML=`<div class="hero-row"><div class="hero-copy"><p class="eyebrow">Weekly rhythm</p><h2>Review the board together.</h2><p>Score promising ideas independently and leave each review with a next action.</p></div><button id="newReviewBtn" class="button button-primary">${iconPlus()} Start review</button></div><div class="review-layout"><div><div class="review-card"><div class="review-date"><div><h3>This week's snapshot</h3><p>${esc(todayLabel())}</p></div><span class="pill">${state.dashboard.needsReview||0} need attention</span></div><div class="profile-stats"><div class="profile-stat"><strong>${state.ideas.length}</strong><span>Active ideas</span></div><div class="profile-stat"><strong>${state.dashboard.runningExperiments||0}</strong><span>Experiments</span></div><div class="profile-stat"><strong>${state.dashboard.openTasks||0}</strong><span>Open tasks</span></div></div></div><div id="reviewSessions" class="review-card"><h3>Review sessions</h3><p>Loading previous sessions…</p></div></div><aside class="review-card"><h3>Simple review rule</h3><p style="line-height:1.65;margin-top:10px">Don't try to prove an idea is brilliant. Decide what the smallest useful next step is. A disagreement between your two scores is a discussion prompt.</p><div style="margin-top:18px;display:grid;gap:8px"><span class="pill">Excitement · 1–5</span><span class="pill">Market potential · 1–5</span><span class="pill">Feasibility · 1–5</span><span class="pill">Speed to test · 1–5</span><span class="pill">Capital efficiency · 1–5</span><span class="pill">Confidence · 1–5</span></div></aside></div>`;
    $('newReviewBtn').addEventListener('click',createReview);loadReviews();
  }
  async function loadReviews(){const root=$('reviewSessions');if(!root)return;try{const p=await api('listReviewSessions'),rows=(p.reviewSessions||[]).slice().reverse();root.innerHTML=`<h3>Review sessions</h3><p>Previous weekly check-ins.</p><div class="review-list">${rows.length?rows.map(r=>`<div class="review-session"><span><strong>${esc(r.Title)}</strong><small>${esc(r.Status)} · ${esc(r.ReviewDate)}</small></span><span class="pill">${esc(r.CreatedByUserID===state.user.userId?'You':'Shared')}</span></div>`).join(''):`<div class="review-session"><span><strong>No sessions yet</strong><small>Create the first one when you are ready.</small></span></div>`}</div>`;}catch(e){root.innerHTML=`<h3>Review sessions</h3><p>${esc(e.message)}</p>`;}}
  async function createReview(){const b=$('newReviewBtn');busy(b,true,'Creating…');try{await api('createReviewSession',{});toast('Review created','Your weekly review session is ready.');await loadReviews();}catch(e){toast('Could not create review',e.message,'error');}finally{busy(b,false);}}

  function renderProfiles(){els.profilesPage.innerHTML=`<div class="hero-row"><div class="hero-copy"><p class="eyebrow">Your two-person team</p><h2>Different perspectives, shared board.</h2><p>Profiles show contribution and momentum, not a leaderboard.</p></div></div><div class="profile-grid">${state.profiles.map(profileCard).join('')}</div>`;}
  function profileCard(p){const u=p.user||p,s=p.stats||{},color=u.accentColor||'#5869f6';return`<article class="profile-card"><div class="profile-hero"><span class="avatar" style="background:${color}18;color:${color}">${esc(initials(u.displayName||u.fullName))}</span><span><h3>${esc(u.displayName||u.fullName)}</h3><p>${esc(u.email||'')}</p></span></div><div class="profile-stats"><div class="profile-stat"><strong>${s.ideasSubmitted||0}</strong><span>Ideas</span></div><div class="profile-stat"><strong>${s.activeIdeas||0}</strong><span>Active</span></div><div class="profile-stat"><strong>${s.brainstormNotes||0}</strong><span>Notes</span></div><div class="profile-stat"><strong>${s.experimentsOwned||0}</strong><span>Experiments</span></div><div class="profile-stat"><strong>${s.openTasks||0}</strong><span>Open tasks</span></div><div class="profile-stat"><strong>${s.movedToPlanning||0}</strong><span>Planning+</span></div></div></article>`;}

  function openIdeaForm(i=null){els.ideaForm.reset();els.ideaId.value=i?.IdeaID||'';els.ideaDialogTitle.textContent=i?'Edit idea':'New idea';els.ideaTitle.value=i?.Title||'';els.ideaSummary.value=i?.OneLineSummary||'';els.ideaStage.value=i?.Stage||'Idea';els.ideaPriority.value=i?.Priority||'Medium';els.ideaCategory.value=i?.Category||'';els.ideaTags.value=i?.Tags||'';els.ideaDescription.value=i?.Description||'';els.ideaOwner.value=i?.OwnerUserID||state.user?.userId||'';els.ideaDialog.showModal();setTimeout(()=>els.ideaTitle.focus(),40);}
  async function saveIdea(e){e.preventDefault();const id=els.ideaId.value,data={title:els.ideaTitle.value.trim(),oneLineSummary:els.ideaSummary.value.trim(),stage:els.ideaStage.value,priority:els.ideaPriority.value,ownerUserId:els.ideaOwner.value,category:els.ideaCategory.value.trim(),tags:els.ideaTags.value.trim(),description:els.ideaDescription.value.trim()};if(!data.title)return;busy(els.saveIdeaButton,true,'Saving…');try{if(id){data.ideaId=id;await api('updateIdea',data);}else await api('createIdea',data);els.ideaDialog.close();await refresh();toast(id?'Idea updated':'Idea captured',id?'Changes saved.':'It is on the board.');}catch(err){toast('Could not save idea',err.message,'error');}finally{busy(els.saveIdeaButton,false);}}

  async function openIdea(id){
    els.ideaDetailRoot.innerHTML='<div class="modal-body"><p>Loading idea…</p></div>';els.detailDialog.showModal();
    try{const p=await api('getIdea',{ideaId:id}),d=p.idea||{},i=d.idea||d;state.currentIdea=i;const u=userById(i.OwnerUserID),color=u?.accentColor||'#5869f6',notes=d.brainstorm||[],tasks=d.tasks||[],experiments=d.experiments||[],attachments=d.attachments||[];
      els.ideaDetailRoot.innerHTML=`<div style="position:relative"><button class="icon-button detail-close" data-close-detail>${iconClose()}</button><div class="detail-hero"><div class="detail-meta"><span class="stage-chip stage-${safe(i.Stage)}">${esc(i.Stage)}</span><span class="pill" style="color:${color}">${esc(u?.displayName||'Unknown')}</span>${i.Category?`<span class="pill">${esc(i.Category)}</span>`:''}</div><h2>${esc(i.Title)}</h2><p>${esc(i.OneLineSummary||'No one-line summary yet.')}</p></div><div class="detail-body"><section class="detail-section"><h3>Raw notes</h3><div class="detail-text">${esc(i.Description||'No notes yet.')}</div></section><section class="detail-section"><h3>Brainstorm (${notes.length})</h3>${notes.length?notes.slice().reverse().map(n=>`<div class="detail-text" style="margin-bottom:7px"><strong>${esc(userById(n.UserID)?.displayName||'IdeaLab')}</strong><br>${esc(n.Content)}</div>`).join(''):'<div class="detail-text">No brainstorm notes yet.</div>'}<div style="display:flex;gap:8px;margin-top:9px"><input id="brainstormInput" placeholder="Add a thought, question or angle…" style="flex:1;height:42px;border:1px solid var(--line);border-radius:10px;padding:0 11px"><button id="addBrainstormBtn" class="button button-secondary">Add</button></div></section><section class="detail-section"><h3>Progress</h3><div style="display:flex;gap:8px;flex-wrap:wrap"><span class="pill">${tasks.length} tasks</span><span class="pill">${experiments.length} experiments</span><span class="pill">${attachments.length} attachments</span></div></section></div><div class="detail-actions"><button class="button button-danger" data-archive-idea>Archive</button><button class="button button-secondary" data-edit-current>Edit idea</button></div></div>`;
      one('[data-close-detail]',els.ideaDetailRoot)?.addEventListener('click',()=>els.detailDialog.close());one('[data-edit-current]',els.ideaDetailRoot)?.addEventListener('click',()=>{els.detailDialog.close();openIdeaForm(state.currentIdea);});one('[data-archive-idea]',els.ideaDetailRoot)?.addEventListener('click',()=>archiveIdea(i.IdeaID));$('addBrainstormBtn')?.addEventListener('click',()=>addBrainstorm(i.IdeaID));
    }catch(err){els.ideaDetailRoot.innerHTML=`<div class="modal-body"><div class="empty-state"><div class="empty-state-inner"><h3>Could not load this idea</h3><p>${esc(err.message)}</p><button class="button button-secondary" data-close-failed>Close</button></div></div></div>`;one('[data-close-failed]',els.ideaDetailRoot)?.addEventListener('click',()=>els.detailDialog.close());}
  }
  async function addBrainstorm(ideaId){const input=$('brainstormInput'),btn=$('addBrainstormBtn');if(!input?.value.trim())return;busy(btn,true,'Adding…');try{await api('addBrainstorm',{ideaId,content:input.value.trim(),noteType:'Note'});els.detailDialog.close();await refresh();await openIdea(ideaId);toast('Thought added');}catch(e){toast('Could not add note',e.message,'error');busy(btn,false);}}
  async function archiveIdea(ideaId){if(!confirm('Archive this idea? You can still find it in Archive.'))return;try{await api('archiveIdea',{ideaId});els.detailDialog.close();await refresh();toast('Idea archived');}catch(e){toast('Could not archive idea',e.message,'error');}}

  function openSearch(){els.globalSearch.value='';renderSearch('');els.searchDialog.showModal();setTimeout(()=>els.globalSearch.focus(),40);}
  function renderSearch(q){q=String(q||'').trim().toLowerCase();const rows=state.ideas.filter(i=>!q||[i.Title,i.OneLineSummary,i.Description,i.Category,i.Tags].join(' ').toLowerCase().includes(q)).slice(0,12);els.searchResults.innerHTML=rows.length?rows.map(ideaRow).join(''):'<div style="padding:25px;text-align:center;color:var(--faint)">No matching ideas.</div>';bindRendered(els.searchResults);}
  function bindRendered(root){qsa('[data-open-idea]',root).forEach(x=>x.addEventListener('click',()=>openIdea(x.dataset.openIdea)));qsa('[data-nav-inline]',root).forEach(x=>x.addEventListener('click',()=>navigate(x.dataset.navInline)));qsa('[data-new-idea]',root).forEach(x=>x.addEventListener('click',()=>openIdeaForm()));}

  function openSidebar(){els.sidebar.classList.add('mobile-open');els.sidebarScrim.hidden=false;}
  function closeSidebar(){els.sidebar.classList.remove('mobile-open');els.sidebarScrim.hidden=true;}
  function bindStatic(){
    els.loginForm.addEventListener('submit',login);els.passwordForm.addEventListener('submit',changePassword);els.ideaForm.addEventListener('submit',saveIdea);els.logoutButton.addEventListener('click',logout);els.quickAddIdea.addEventListener('click',()=>openIdeaForm());els.topAddIdea.addEventListener('click',()=>openIdeaForm());els.searchButton.addEventListener('click',openSearch);els.globalSearch.addEventListener('input',e=>renderSearch(e.target.value));
    els.profileMenuButton.addEventListener('click',()=>{els.profileMenu.hidden=!els.profileMenu.hidden;els.profileMenuButton.setAttribute('aria-expanded',String(!els.profileMenu.hidden));});els.sidebarOpen.addEventListener('click',openSidebar);els.sidebarClose.addEventListener('click',closeSidebar);els.sidebarScrim.addEventListener('click',closeSidebar);
    qsa('[data-nav]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();navigate(b.dataset.nav);els.profileMenu.hidden=true;}));qsa('[data-close-dialog]').forEach(b=>b.addEventListener('click',()=>$(b.dataset.closeDialog)?.close()));qsa('[data-password-toggle]').forEach(b=>b.addEventListener('click',()=>{const i=$(b.dataset.passwordToggle);if(!i)return;i.type=i.type==='password'?'text':'password';b.setAttribute('aria-label',i.type==='password'?'Show password':'Hide password');}));
    document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();if(!els.appView.hidden)openSearch();}if(e.key==='Escape')closeSidebar();});[els.ideaDialog,els.detailDialog,els.searchDialog].forEach(d=>d.addEventListener('click',e=>{if(e.target===d)d.close();}));
  }

  async function boot(){bindStatic();if(!state.token)return showLogin();try{await loadState();showApp();navigate('home');}catch{clearSession(true);}}
  boot();
})();
