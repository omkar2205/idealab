from pathlib import Path
import re

# INDEX
p = Path('index.html')
s = p.read_text()

# Add desktop collapse button beside brand.
old = '''        <button id="sidebarClose" class="icon-button sidebar-close" aria-label="Close navigation">
          <svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg>
        </button>'''
new = '''        <button id="sidebarCollapse" class="icon-button sidebar-collapse" aria-label="Collapse navigation" aria-expanded="true">
          <svg viewBox="0 0 24 24"><path d="m14 7-5 5 5 5"/></svg>
        </button>
        <button id="sidebarClose" class="icon-button sidebar-close" aria-label="Close navigation">
          <svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg>
        </button>'''
if old not in s:
    raise SystemExit('sidebar close block not found')
s = s.replace(old, new, 1)

# Remove duplicate New idea button from sidebar.
s = re.sub(r'''\n\s*<button id="quickAddIdea" class="button button-primary sidebar-create">.*?</button>\n''', '\n', s, count=1, flags=re.S)

# Replace top header with only mobile menu + floating actions.
pattern = r'''\n\s*<main class="main-content">\n\s*<header class="topbar">.*?</header>\n'''
replacement = '''
    <main class="main-content">
      <button id="sidebarOpen" class="icon-button mobile-menu floating-menu" aria-label="Open navigation">
        <svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      </button>

      <div class="floating-actions" aria-label="Quick actions">
        <button id="searchButton" class="floating-action floating-action-secondary" aria-label="Search ideas" title="Search">
          <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4"/></svg>
        </button>
        <button id="topAddIdea" class="floating-action floating-action-primary" aria-label="Add idea" title="Add idea">
          <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
        </button>
      </div>
'''
s2, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('topbar block not found')
s = s2
p.write_text(s)

# APP
p = Path('app.js')
s = p.read_text()

s = s.replace("  const TOKEN_KEY = 'idealab_session_token';", "  const TOKEN_KEY = 'idealab_session_token';\n  const SIDEBAR_KEY = 'idealab_sidebar_collapsed';", 1)

old = "sidebar:$('sidebar'),sidebarOpen:$('sidebarOpen'),sidebarClose:$('sidebarClose'),sidebarScrim:$('sidebarScrim'),sidebarName:$('sidebarName'),sidebarAvatar:$('sidebarAvatar'),profileMenuButton:$('profileMenuButton'),profileMenu:$('profileMenu'),logoutButton:$('logoutButton'),"
new = "sidebar:$('sidebar'),sidebarOpen:$('sidebarOpen'),sidebarCollapse:$('sidebarCollapse'),sidebarClose:$('sidebarClose'),sidebarScrim:$('sidebarScrim'),sidebarName:$('sidebarName'),sidebarAvatar:$('sidebarAvatar'),profileMenuButton:$('profileMenuButton'),profileMenu:$('profileMenu'),logoutButton:$('logoutButton'),"
if old not in s:
    raise SystemExit('sidebar els block not found')
s = s.replace(old, new, 1)

old = "pageTitle:$('pageTitle'),pageKicker:$('pageKicker'),homePage:$('homePage'),boardPage:$('boardPage'),reviewsPage:$('reviewsPage'),profilesPage:$('profilesPage'),quickAddIdea:$('quickAddIdea'),topAddIdea:$('topAddIdea'),"
new = "homePage:$('homePage'),boardPage:$('boardPage'),reviewsPage:$('reviewsPage'),profilesPage:$('profilesPage'),topAddIdea:$('topAddIdea'),"
if old not in s:
    raise SystemExit('page els block not found')
s = s.replace(old, new, 1)

old = "function navigate(page){state.currentPage=page;const [k,t]=pageInfo[page]||pageInfo.home;els.pageKicker.textContent=k;els.pageKicker.hidden=!k;els.pageTitle.textContent=t;qsa('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.nav===page));"
new = "function navigate(page){state.currentPage=page;qsa('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.nav===page));"
if old not in s:
    raise SystemExit('navigate header logic not found')
s = s.replace(old, new, 1)

old = "  function openSidebar(){els.sidebar.classList.add('mobile-open');els.sidebarScrim.hidden=false;}\n  function closeSidebar(){els.sidebar.classList.remove('mobile-open');els.sidebarScrim.hidden=true;}"
new = '''  function setSidebarCollapsed(collapsed, persist=false){
    document.body.classList.toggle('sidebar-collapsed',Boolean(collapsed));
    if(els.sidebarCollapse){
      els.sidebarCollapse.setAttribute('aria-expanded',String(!collapsed));
      els.sidebarCollapse.setAttribute('aria-label',collapsed?'Expand navigation':'Collapse navigation');
      const path=els.sidebarCollapse.querySelector('path');
      if(path)path.setAttribute('d',collapsed?'m10 7 5 5-5 5':'m14 7-5 5 5 5');
    }
    if(persist)localStorage.setItem(SIDEBAR_KEY,collapsed?'1':'0');
  }
  function toggleSidebarCollapsed(){setSidebarCollapsed(!document.body.classList.contains('sidebar-collapsed'),true);}
  function openSidebar(){els.sidebar.classList.add('mobile-open');els.sidebarScrim.hidden=false;}
  function closeSidebar(){els.sidebar.classList.remove('mobile-open');els.sidebarScrim.hidden=true;}'''
if old not in s:
    raise SystemExit('sidebar functions not found')
s = s.replace(old, new, 1)

old = "els.loginForm.addEventListener('submit',login);els.passwordForm.addEventListener('submit',changePassword);els.ideaForm.addEventListener('submit',saveIdea);els.logoutButton.addEventListener('click',logout);els.quickAddIdea.addEventListener('click',()=>openIdeaForm());els.topAddIdea.addEventListener('click',()=>openIdeaForm());els.searchButton.addEventListener('click',openSearch);"
new = "els.loginForm.addEventListener('submit',login);els.passwordForm.addEventListener('submit',changePassword);els.ideaForm.addEventListener('submit',saveIdea);els.logoutButton.addEventListener('click',logout);els.topAddIdea.addEventListener('click',()=>openIdeaForm());els.searchButton.addEventListener('click',openSearch);els.sidebarCollapse?.addEventListener('click',toggleSidebarCollapsed);"
if old not in s:
    raise SystemExit('static event block not found')
s = s.replace(old, new, 1)

old = "  async function boot(){bindStatic();if(!state.token)return showLogin();try{await loadState();showApp();navigate('home');}catch{clearSession(true);}}"
new = "  async function boot(){setSidebarCollapsed(localStorage.getItem(SIDEBAR_KEY)==='1');bindStatic();if(!state.token)return showLogin();try{await loadState();showApp();navigate('home');}catch{clearSession(true);}}"
if old not in s:
    raise SystemExit('boot function not found')
s = s.replace(old, new, 1)
p.write_text(s)

# CSS: append focused overrides so existing responsive rules remain intact.
p = Path('styles.css')
s = p.read_text()
append = r'''

/* Compact navigation and floating quick actions */
.sidebar,.main-content{transition:width .2s ease,margin-left .2s ease}
.sidebar-collapse{width:32px;height:32px;border:0;background:transparent;color:var(--faint)}
.sidebar-collapse:hover{background:var(--soft);color:var(--text)}
.sidebar-create{display:none!important}
.page-root{padding-top:clamp(26px,3.2vw,46px);padding-bottom:110px}
.floating-actions{position:fixed;z-index:32;right:24px;bottom:24px;display:flex;align-items:center;gap:10px}
.floating-action{width:52px;height:52px;padding:0;border-radius:50%;display:grid;place-items:center;cursor:pointer;transition:.16s ease;box-shadow:0 12px 30px rgba(22,28,45,.14)}
.floating-action:hover{transform:translateY(-2px)}
.floating-action svg{width:21px;height:21px}
.floating-action-secondary{border:1px solid var(--line);background:#fff;color:var(--text)}
.floating-action-secondary:hover{background:var(--soft)}
.floating-action-primary{border:0;background:var(--primary);color:#fff;box-shadow:0 12px 28px rgba(88,105,246,.3)}
.floating-action-primary:hover{background:var(--primary2)}
.floating-menu{display:none}
.toast-region{bottom:92px}

body.sidebar-collapsed .sidebar{width:84px;padding-left:10px;padding-right:10px}
body.sidebar-collapsed .main-content{margin-left:84px}
body.sidebar-collapsed .sidebar-head{padding:0 4px;gap:3px}
body.sidebar-collapsed .brand{gap:0}
body.sidebar-collapsed .brand>span:last-child{display:none}
body.sidebar-collapsed .nav-label{display:none}
body.sidebar-collapsed .main-nav{overflow-x:hidden;padding-top:12px}
body.sidebar-collapsed .nav-item{justify-content:center;padding:0;gap:0}
body.sidebar-collapsed .nav-item>span{display:none}
body.sidebar-collapsed .nav-item svg{width:20px;height:20px}
body.sidebar-collapsed .sidebar-profile{display:flex;justify-content:center}
body.sidebar-collapsed .profile-chip{width:50px;justify-content:center;padding:8px}
body.sidebar-collapsed .profile-chip-copy,body.sidebar-collapsed .profile-chip>svg{display:none}
body.sidebar-collapsed .profile-menu{left:64px;right:auto;bottom:8px;width:150px}

@media(max-width:900px){
  body.sidebar-collapsed .sidebar{width:var(--sidebar);padding:22px 15px 16px}
  body.sidebar-collapsed .main-content{margin-left:0}
  body.sidebar-collapsed .sidebar-head{padding:0 8px;gap:initial}
  body.sidebar-collapsed .brand{gap:10px}
  body.sidebar-collapsed .brand>span:last-child{display:inline}
  body.sidebar-collapsed .nav-label{display:block}
  body.sidebar-collapsed .main-nav{padding-top:0}
  body.sidebar-collapsed .nav-item{justify-content:flex-start;padding:0 11px;gap:11px}
  body.sidebar-collapsed .nav-item>span{display:inline-flex}
  body.sidebar-collapsed .nav-count{margin-left:auto}
  body.sidebar-collapsed .sidebar-profile{display:block}
  body.sidebar-collapsed .profile-chip{width:100%;justify-content:flex-start;padding:8px}
  body.sidebar-collapsed .profile-chip-copy{display:grid}
  body.sidebar-collapsed .profile-chip>svg{display:block}
  body.sidebar-collapsed .profile-menu{left:4px;right:4px;bottom:58px;width:auto}
  .sidebar-collapse{display:none}
  .floating-menu{position:fixed;z-index:34;left:16px;top:16px;display:inline-grid;box-shadow:0 8px 22px rgba(22,28,45,.1)}
  .page-root{padding-top:76px}
  .floating-actions{right:16px;bottom:16px}
  .toast-region{bottom:84px}
}

@media(max-width:620px){
  .floating-action{width:50px;height:50px}
  .page-root{padding-top:72px;padding-bottom:96px}
}
'''
if '/* Compact navigation and floating quick actions */' not in s:
    s += append
p.write_text(s)
