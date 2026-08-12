from pathlib import Path
import re

# ---------------- INDEX ----------------
p = Path('index.html')
s = p.read_text(encoding='utf-8')

s = s.replace(
    '<button id="searchButton" class="floating-action floating-action-secondary" aria-label="Search ideas" title="Search (Ctrl+K)">',
    '<button id="searchButton" class="floating-action floating-action-secondary" data-label="Search" aria-label="Search ideas" title="Search (Ctrl+K)">',
    1,
)
s = s.replace(
    '<button id="topAddIdea" class="floating-action floating-action-primary" aria-label="Add idea" title="New idea (N)">',
    '<button id="topAddIdea" class="floating-action floating-action-primary" data-label="Add idea" aria-label="Add idea" title="New idea (N)">',
    1,
)

avatar_dialog = '''\n  <dialog id="avatarDialog" class="modal modal-small avatar-dialog">\n    <div class="modal-head compact"><h2>Choose avatar</h2><button class="icon-button" type="button" data-close-dialog="avatarDialog" aria-label="Close"><svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg></button></div>\n    <div class="modal-body">\n      <div id="avatarOptions" class="avatar-options"></div>\n      <label class="field avatar-custom-field"><span>Custom emoji</span><input id="customAvatarInput" maxlength="12" placeholder="Paste an emoji"></label>\n    </div>\n    <div class="modal-actions"><button id="saveCustomAvatar" class="button button-primary" type="button">Save avatar</button></div>\n  </dialog>\n'''
if 'id="avatarDialog"' not in s:
    marker = '  <dialog id="passwordDialog" class="modal modal-small">'
    if marker not in s:
        raise SystemExit('password dialog marker not found')
    s = s.replace(marker, avatar_dialog + '\n' + marker, 1)

p.write_text(s, encoding='utf-8')

# ---------------- APP ----------------
p = Path('app.js')
s = p.read_text(encoding='utf-8')

# Elements
old = "    passwordDialog:$('passwordDialog'),passwordForm:$('passwordForm'),newPassword:$('newPassword'),confirmPassword:$('confirmPassword'),passwordError:$('passwordError'),changePasswordButton:$('changePasswordButton')"
new = "    avatarDialog:$('avatarDialog'),avatarOptions:$('avatarOptions'),customAvatarInput:$('customAvatarInput'),saveCustomAvatar:$('saveCustomAvatar'),\n    passwordDialog:$('passwordDialog'),passwordForm:$('passwordForm'),newPassword:$('newPassword'),confirmPassword:$('confirmPassword'),passwordError:$('passwordError'),changePasswordButton:$('changePasswordButton')"
if old not in s:
    raise SystemExit('elements marker not found')
s = s.replace(old, new, 1)

# Avatar helpers + momentum helpers
old = "  function profileName(id){const u=userById(id);return u?.displayName||u?.fullName||'Unknown';}\n"
new = """  function profileName(id){const u=userById(id);return u?.displayName||u?.fullName||'Unknown';}\n  function avatarFor(id){const u=userById(id);return String(u?.avatarEmoji||'').trim()||initials(u?.displayName||u?.fullName);}\n  function activityAgeDays(i){const d=new Date(i.LastActivityAt||i.UpdatedAt||i.CreatedAt||0);if(Number.isNaN(d.getTime()))return 999;return Math.max(0,(Date.now()-d.getTime())/86400000);}\n  function pulseClass(i){const score=combinedScore(i.IdeaID),ratings=ratingsForIdea(i.IdeaID).length,age=activityAgeDays(i);if(score!=null&&score>=8&&ratings>=Math.min(2,state.profiles.length)&&age<=7)return'pulse-hot';if((score!=null&&score>=6.5)||age<=5)return'pulse-warm';return'pulse-calm';}\n  function updatedLabel(i){const d=activityAgeDays(i);if(d<1)return'Updated today';if(d<2)return'Updated yesterday';if(d<14)return`Updated ${Math.floor(d)}d ago`;return fmtDate(i.UpdatedAt||i.LastActivityAt||i.CreatedAt);}\n"""
if old not in s:
    raise SystemExit('profileName marker not found')
s = s.replace(old, new, 1)

old = "  function ownerAvatar(id){const u=userById(id),color=u?.accentColor||'#5869f6';return `<span class=\"avatar\" style=\"background:${color}18;color:${color}\">${esc(initials(u?.displayName||u?.fullName))}</span>`;}"
new = "  function ownerAvatar(id){const u=userById(id),color=u?.accentColor||'#5869f6';return `<span class=\"avatar avatar-emoji\" style=\"background:${color}18;color:${color}\">${esc(avatarFor(id))}</span>`;}"
if old not in s:
    raise SystemExit('ownerAvatar marker not found')
s = s.replace(old, new, 1)

# Profile hydration
old = "    if(!state.user)return;const c=state.user.accentColor||'#5869f6';els.sidebarName.textContent=state.user.displayName||state.user.fullName||'Profile';els.sidebarAvatar.textContent=initials(state.user.displayName||state.user.fullName);els.sidebarAvatar.style.background=`${c}18`;els.sidebarAvatar.style.color=c;els.navIdeaCount.textContent=state.ideas.length;"
new = "    if(!state.user)return;const c=state.user.accentColor||'#5869f6';els.sidebarName.textContent=state.user.displayName||state.user.fullName||'Profile';els.sidebarAvatar.textContent=String(state.user.avatarEmoji||'').trim()||initials(state.user.displayName||state.user.fullName);els.sidebarAvatar.classList.toggle('avatar-emoji',Boolean(String(state.user.avatarEmoji||'').trim()));els.sidebarAvatar.style.background=`${c}18`;els.sidebarAvatar.style.color=c;els.navIdeaCount.textContent=state.ideas.length;"
if old not in s:
    raise SystemExit('hydrate profile marker not found')
s = s.replace(old, new, 1)

# Load avatars along with ratings
old = "    try{const r=await insights('listRatings');state.ratings=r.ratings||[];}catch(e){state.ratings=[];console.warn('Ratings unavailable',e.message);}hydrateProfile();"
new = """    try{const r=await insights('listRatings');state.ratings=r.ratings||[];}catch(e){state.ratings=[];console.warn('Ratings unavailable',e.message);}\n    try{const a=await insights('listAvatars'),map=new Map((a.avatars||[]).map(x=>[x.userId,x.avatarEmoji||'']));state.profiles.forEach(p=>{const u=p.user||p;u.avatarEmoji=map.get(u.userId)||'';});const mine=state.profiles.map(p=>p.user||p).find(u=>u.userId===state.user.userId);if(mine)state.user.avatarEmoji=mine.avatarEmoji||'';}catch(e){console.warn('Avatars unavailable',e.message);}\n    hydrateProfile();"""
if old not in s:
    raise SystemExit('loadState ratings marker not found')
s = s.replace(old, new, 1)

# Visual idea card
old = "  function ideaCard(i){const u=userById(i.OwnerUserID),color=u?.accentColor||'#5869f6';return`<article class=\"idea-card\" draggable=\"true\" data-drag-idea=\"${esc(i.IdeaID)}\" data-open-idea=\"${esc(i.IdeaID)}\" style=\"--owner-color:${color}\"><div class=\"idea-card-head\"><h4>${esc(i.Title)}</h4>${scoreBadge(i.IdeaID)}</div><p>${esc(i.OneLineSummary||i.Description||'No summary')}</p><div class=\"idea-card-foot\"><span class=\"owner-mini\">${ownerAvatar(i.OwnerUserID)}${esc(u?.displayName||'Unknown')}</span><span class=\"stage-chip stage-${safe(i.Stage)}\">${esc(i.Stage)}</span></div></article>`;}"
new = """  function ideaCard(i){const u=userById(i.OwnerUserID),color=u?.accentColor||'#5869f6',score=combinedScore(i.IdeaID),tags=String(i.Tags||'').split(',').map(x=>x.trim()).filter(Boolean).slice(0,2);return`<article class=\"idea-card stage-surface-${safe(i.Stage)} ${pulseClass(i)}\" draggable=\"true\" data-drag-idea=\"${esc(i.IdeaID)}\" data-open-idea=\"${esc(i.IdeaID)}\" style=\"--owner-color:${color}\"><div class=\"idea-card-stage\"><span>${esc(i.Stage)}</span><span class=\"idea-score-orb ${score==null?'empty':''}\"><strong>${score==null?'—':score.toFixed(1)}</strong></span></div><h4>${esc(i.Title)}</h4><p>${esc(i.OneLineSummary||i.Description||'No summary')}</p>${tags.length?`<div class=\"idea-tags\">${tags.map(t=>`<span>${esc(t)}</span>`).join('')}</div>`:''}<div class=\"idea-card-foot\"><span class=\"owner-mini\">${ownerAvatar(i.OwnerUserID)}${esc(u?.displayName||'Unknown')}</span><small>${esc(updatedLabel(i))}</small></div></article>`;}"""
if old not in s:
    raise SystemExit('ideaCard marker not found')
s = s.replace(old, new, 1)

# Home: focus first, metrics second
home_pat = re.compile(r"  function renderHome\(\)\{\n.*?\n  \}\n\n  function boardColumn", re.S)
home_new = """  function renderHome(){\n    const avgScore=avg(state.ideas.map(i=>combinedScore(i.IdeaID)).filter(v=>v!=null)),rated=state.ideas.filter(i=>ratingsForIdea(i.IdeaID).length>0).length;\n    const focus=[...state.ideas].sort((a,b)=>{const sa=combinedScore(a.IdeaID)??-1,sb=combinedScore(b.IdeaID)??-1;if(sb!==sa)return sb-sa;return activityAgeDays(a)-activityAgeDays(b);}).slice(0,3);\n    const recent=[...state.ideas].sort((a,b)=>String(b.LastActivityAt||b.UpdatedAt||'').localeCompare(String(a.LastActivityAt||a.UpdatedAt||''))).slice(0,6);\n    wrap(`<section class=\"focus-section\"><div class=\"focus-head\"><div><span>Current focus</span><h2>Ideas with momentum</h2></div><button class=\"text-button\" data-nav-inline=\"ideas\">All ideas</button></div>${focus.length?`<div class=\"focus-grid\">${focus.map(i=>ideaCard(i)).join('')}</div>`:empty('No ideas yet','Use the + button to add the first idea.')}</section><div class=\"metric-grid metric-grid-compact\">${metric('primary',icon.bulb,state.ideas.length,'Active ideas')}${metric('pink',icon.chat,rated,'Rated')}${metric('amber',icon.search,avgScore==null?'—':avgScore.toFixed(1),'Average score')}${metric('green',icon.check,state.ideas.filter(i=>i.Stage==='Execution').length,'Execution')}</div><section class=\"recent-section\"><div class=\"section-simple-head\"><h3>Recent ideas</h3></div>${recent.length?`<div class=\"idea-list clean-list\">${recent.map(ideaRow).join('')}</div>`:''}</section>`);\n  }\n\n  function boardColumn"""
s, n = home_pat.subn(home_new, s, count=1)
if n != 1:
    raise SystemExit('renderHome block not found')

# Board columns stage-aware
s = s.replace(
    "function boardColumn(stage,ideas){const rows=ideas.filter(i=>i.Stage===stage);return`<section class=\"board-column\" data-drop-stage=\"${esc(stage)}\">",
    "function boardColumn(stage,ideas){const rows=ideas.filter(i=>i.Stage===stage);return`<section class=\"board-column board-stage-${safe(stage)}\" data-drop-stage=\"${esc(stage)}\">",
    1,
)
s = s.replace(
    "<span class=\"pill\">Drag cards between stages</span>",
    "<span class=\"board-hint\">Drag to move stage</span>",
    1,
)

# Analytics hero
analytics_pat = re.compile(r"  function renderAnalytics\(\)\{.*?\}\\n  function bindAnalytics", re.S)
# The regex above may not match because source has a real newline sequence, use exact broad pattern instead.
analytics_pat = re.compile(r"  function renderAnalytics\(\)\{.*?\}\n  function bindAnalytics", re.S)
analytics_new = """  function renderAnalytics(){const ideas=analyticsIdeas(),scores=ideas.map(i=>combinedScore(i.IdeaID)).filter(v=>v!=null),paired=ideas.filter(i=>ratingsForIdea(i.IdeaID).length>=2),gaps=paired.map(i=>({i,g:ratingGap(i.IdeaID)})).sort((a,b)=>b.g-a.g).slice(0,5);wrap(`<div class=\"analytics-hero\"><div class=\"analytics-hero-top\"><div><span>Analytics</span><h2>Idea pipeline</h2></div>${analyticsFilterBar()}</div>${pipelineHTML(ideas)}<div class=\"analytics-hero-stats\"><div><strong>${ideas.length}</strong><span>Ideas</span></div><div><strong>${scores.length}</strong><span>Rated</span></div><div><strong>${scores.length?avg(scores).toFixed(1):'—'}</strong><span>Average score</span></div><div><strong>${ideas.filter(i=>i.Stage==='Execution').length}</strong><span>Execution</span></div></div></div><div class=\"analytics-grid\"><section class=\"analytics-card\"><h3>Top rated</h3>${topBars(ideas)}</section><section class=\"analytics-card\"><h3>Score distribution</h3>${distributionHTML(ideas)}</section><section class=\"analytics-card\"><h3>Rating comparison</h3>${scatterHTML(ideas)}</section><section class=\"analytics-card\"><h3>Largest disagreements</h3>${gaps.length?`<div class=\"disagreement-list\">${gaps.map(x=>`<div class=\"disagreement-item\" data-open-idea=\"${esc(x.i.IdeaID)}\"><strong>${esc(x.i.Title)}</strong><span class=\"score-badge\">${x.g.toFixed(1)}</span></div>`).join('')}</div>`:'<p style=\"color:var(--faint);font-size:10px\">No paired ratings.</p>'}</section><section class=\"analytics-card\"><h3>Ideas created</h3>${timelineHTML(ideas)}</section><section class=\"analytics-card\"><h3>Category performance</h3>${categoryBars(ideas)}</section><section class=\"analytics-card full\"><h3>Ranked ideas</h3>${analyticsTable(ideas)}</section></div>`);bindAnalytics();}\n  function bindAnalytics"""
s, n = analytics_pat.subn(analytics_new, s, count=1)
if n != 1:
    raise SystemExit('renderAnalytics block not found')

# Profiles with avatar control
profile_pat = re.compile(r"  function renderProfiles\(\)\{.*?\}\n\n  function openQuickIdea", re.S)
profile_new = """  function renderProfiles(){wrap(`<div class=\"profile-grid\">${state.profiles.map(p=>{const u=p.user||p,s=p.stats||{},c=u.accentColor||'#5869f6',mine=u.userId===state.user.userId;return`<article class=\"profile-card studio-profile-card\"><div class=\"profile-hero\"><span class=\"avatar profile-avatar ${u.avatarEmoji?'avatar-emoji':''}\" style=\"background:${c}18;color:${c}\">${esc(String(u.avatarEmoji||'').trim()||initials(u.displayName||u.fullName))}</span><span><h3>${esc(u.displayName||u.fullName)}</h3><p>${esc(u.email||'')}</p></span>${mine?`<button class=\"button button-secondary button-small profile-avatar-button\" data-change-avatar>Change avatar</button>`:''}</div><div class=\"profile-stats\"><div class=\"profile-stat\"><strong>${s.ideasSubmitted||0}</strong><span>Ideas</span></div><div class=\"profile-stat\"><strong>${s.activeIdeas||0}</strong><span>Active</span></div><div class=\"profile-stat\"><strong>${s.brainstormNotes||0}</strong><span>Notes</span></div><div class=\"profile-stat\"><strong>${s.experimentsOwned||0}</strong><span>Experiments</span></div><div class=\"profile-stat\"><strong>${s.openTasks||0}</strong><span>Open tasks</span></div><div class=\"profile-stat\"><strong>${state.ratings.filter(r=>r.reviewerUserId===u.userId).length}</strong><span>Ratings</span></div></div></article>`}).join('')}</div>`);}\n\n  const AVATAR_OPTIONS=['🧠','💡','🚀','🧑‍💻','👩‍💻','🎯','🦊','🐼','🌙','⭐','🪐','🎨','📚','☕','🔥','🌿'];\n  function openAvatarPicker(){els.avatarOptions.innerHTML=AVATAR_OPTIONS.map(a=>`<button type=\"button\" class=\"avatar-option\" data-avatar-choice=\"${a}\">${a}</button>`).join('');els.customAvatarInput.value=String(state.user.avatarEmoji||'');qsa('[data-avatar-choice]',els.avatarOptions).forEach(b=>b.addEventListener('click',()=>saveAvatar(b.dataset.avatarChoice)));els.avatarDialog.showModal();}\n  async function saveAvatar(value){const emoji=String(value||'').trim();busy(els.saveCustomAvatar,true,'Saving…');try{const p=await insights('saveAvatar',{avatarEmoji:emoji});state.user.avatarEmoji=p.avatarEmoji||'';state.profiles.forEach(x=>{const u=x.user||x;if(u.userId===state.user.userId)u.avatarEmoji=p.avatarEmoji||'';});els.avatarDialog.close();hydrateProfile();renderCurrent();toast('Avatar updated');}catch(e){toast('Could not update avatar',e.message,'error');}finally{busy(els.saveCustomAvatar,false);}}\n\n  function openQuickIdea"""
s, n = profile_pat.subn(profile_new, s, count=1)
if n != 1:
    raise SystemExit('renderProfiles block not found')

# Detail hero score treatment
old = "<div class=\"detail-title-row\"><div><h2>${esc(i.Title)}</h2><p>${esc(i.OneLineSummary||'')}</p></div></div>"
new = "<div class=\"detail-title-row\"><div><h2>${esc(i.Title)}</h2><p>${esc(i.OneLineSummary||'')}</p></div><div class=\"detail-score-block ${pulseClass(i)}\"><strong>${score==null?'—':score.toFixed(1)}</strong><span>Combined score</span></div></div>"
if old not in s:
    raise SystemExit('detail title marker not found')
s = s.replace(old, new, 1)
# Remove duplicate score pill in detail meta
s = s.replace("${score!=null?`<span class=\"pill score-pill\">${score.toFixed(1)} / 10</span>`:''}", "", 1)

# Bind avatar control
old = "function bindRendered(root){qsa('[data-open-idea]',root).forEach(x=>x.addEventListener('click',e=>{if(e.defaultPrevented)return;openIdea(x.dataset.openIdea);}));qsa('[data-nav-inline]',root).forEach(x=>x.addEventListener('click',()=>navigate(x.dataset.navInline)));qsa('[data-new-idea]',root).forEach(x=>x.addEventListener('click',openQuickIdea));qsa('[data-idea-view]',root).forEach(x=>x.addEventListener('click',()=>{state.ideaView=x.dataset.ideaView;localStorage.setItem(VIEW_KEY,state.ideaView);renderIdeas();}));}"
new = "function bindRendered(root){qsa('[data-open-idea]',root).forEach(x=>x.addEventListener('click',e=>{if(e.defaultPrevented)return;openIdea(x.dataset.openIdea);}));qsa('[data-nav-inline]',root).forEach(x=>x.addEventListener('click',()=>navigate(x.dataset.navInline)));qsa('[data-new-idea]',root).forEach(x=>x.addEventListener('click',openQuickIdea));qsa('[data-change-avatar]',root).forEach(x=>x.addEventListener('click',openAvatarPicker));qsa('[data-idea-view]',root).forEach(x=>x.addEventListener('click',()=>{state.ideaView=x.dataset.ideaView;localStorage.setItem(VIEW_KEY,state.ideaView);renderIdeas();}));}"
if old not in s:
    raise SystemExit('bindRendered marker not found')
s = s.replace(old, new, 1)

# Static avatar button + dialog backdrop
old = "els.searchButton.addEventListener('click',openSearch);els.topAddIdea.addEventListener('click',openQuickIdea);"
new = "els.searchButton.addEventListener('click',openSearch);els.topAddIdea.addEventListener('click',openQuickIdea);els.saveCustomAvatar.addEventListener('click',()=>saveAvatar(els.customAvatarInput.value));"
if old not in s:
    raise SystemExit('static action marker not found')
s = s.replace(old, new, 1)

old = "[els.quickIdeaDialog,els.ideaDialog,els.detailDialog,els.searchDialog,els.passwordDialog,els.mediaDialog]"
new = "[els.quickIdeaDialog,els.ideaDialog,els.detailDialog,els.searchDialog,els.avatarDialog,els.passwordDialog,els.mediaDialog]"
if old not in s:
    raise SystemExit('dialog array marker not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')

# ---------------- CSS ----------------
p = Path('styles.css')
s = p.read_text(encoding='utf-8')
marker = '/* IdeaLab creative studio refresh */'
if marker not in s:
    s += r'''

/* IdeaLab creative studio refresh */
:root{
  --bg:#f4f0e9;--surface:#fffdfa;--soft:#eee9e1;--muted:#e6dfd6;--line:rgba(50,45,39,.10);
  --stage-idea:#6f7890;--stage-idea-soft:#f0f1f4;--stage-brain:#cf6d8b;--stage-brain-soft:#fff0f4;
  --stage-valid:#7d62be;--stage-valid-soft:#f4efff;--stage-plan:#b77a27;--stage-plan-soft:#fff4df;
  --stage-exec:#42876a;--stage-exec-soft:#eaf7f0;--studio-dark:#171923;--studio-dark2:#232633;
  --shadow:0 18px 55px rgba(44,38,30,.08);--shadow-lg:0 30px 100px rgba(19,18,23,.20)
}
body{background:radial-gradient(circle at 55% -15%,#fffdf9 0,transparent 38%),var(--bg)}
.page-root{padding:34px clamp(28px,3.4vw,54px) 120px}
.page-section{max-width:1540px}

/* Floating studio rail */
.sidebar{inset:14px auto 14px 14px;height:auto;border:1px solid rgba(45,40,34,.09);border-radius:24px;background:rgba(255,253,250,.93);box-shadow:0 20px 55px rgba(45,39,31,.08);backdrop-filter:blur(20px)}
.main-content{margin-left:calc(var(--sidebar) + 28px)}
.sidebar-head{padding:0 7px}.brand-logo{width:35px;height:42px}.main-nav{padding:3px}.nav-item{border-radius:13px;min-height:44px}.nav-item:hover{background:rgba(54,51,47,.055);transform:translateX(2px)}.nav-item.active{background:#171923;color:#fff;box-shadow:0 8px 22px rgba(23,25,35,.13)}.nav-item.active svg{color:#fff}.nav-divider{background:rgba(45,40,34,.08)}
.sidebar-profile{border-top:0;padding-top:10px}.profile-chip{background:rgba(255,255,255,.55);border:1px solid rgba(45,40,34,.06)}
body.sidebar-collapsed .sidebar{width:78px}body.sidebar-collapsed .main-content{margin-left:106px}

/* Floating actions expand into labels */
.floating-actions{right:28px;bottom:28px}.floating-action{width:54px;height:54px;display:flex;align-items:center;justify-content:center;gap:8px;overflow:hidden;white-space:nowrap;transition:width .22s cubic-bezier(.2,.8,.2,1),transform .18s ease,box-shadow .18s ease}.floating-action::after{content:attr(data-label);max-width:0;opacity:0;font-weight:800;font-size:12px;transition:max-width .22s ease,opacity .16s ease}.floating-action:hover{width:126px;transform:translateY(-3px)}.floating-action:hover::after{max-width:70px;opacity:1}.floating-action-primary{background:#171923;box-shadow:0 15px 36px rgba(23,25,35,.25)}.floating-action-primary:hover{background:#242735}.floating-action-secondary{background:#fffdfa;border:1px solid rgba(45,40,34,.12)}

/* Home focus */
.focus-section{margin-bottom:22px}.focus-head{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:14px}.focus-head>div>span{display:block;margin-bottom:4px;color:var(--faint);font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.focus-head h2{margin:0;font:800 clamp(25px,3vw,38px)/1.05 var(--display);letter-spacing:-.045em}.focus-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.metric-grid-compact{margin:20px 0}.metric-grid-compact .metric-card{min-height:96px;padding:15px;border:0;background:rgba(255,253,250,.7);box-shadow:none}.metric-grid-compact .metric-icon{display:none}.metric-grid-compact .metric-card strong{margin:0 0 5px;font-size:24px}.recent-section{margin-top:4px}.section-simple-head{padding:0 4px 8px}.section-simple-head h3{margin:0;font:800 14px var(--display)}.clean-list{padding:0;background:transparent}.clean-list .idea-list-row{border-bottom:1px solid rgba(45,40,34,.07);border-radius:0}.clean-list .idea-list-row:last-child{border-bottom:0}

/* Stage-aware idea cards */
.board{gap:14px}.board-column{background:rgba(255,255,255,.30);border:1px solid rgba(45,40,34,.06);border-radius:20px}.board-column-head{height:56px;padding:0 15px}.board-column-head h3{font-size:12px}.board-cards{padding:0 9px 12px;gap:10px}.board-hint{color:var(--faint);font-size:10px;font-weight:700}
.idea-card{min-height:190px;padding:17px 17px 15px;border:0;border-radius:18px;background:var(--stage-card,#fffdfa);box-shadow:0 12px 28px rgba(55,46,37,.055);transition:transform .2s cubic-bezier(.2,.8,.2,1),box-shadow .2s ease,filter .2s ease}.idea-card::before{display:none}.idea-card:hover{transform:translateY(-5px) rotate(-.35deg);box-shadow:0 22px 48px rgba(45,38,30,.12)}.idea-card.dragging{transform:rotate(1.5deg) scale(.98);opacity:.62}.idea-card-stage{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;color:var(--stage-color,#606879);font-size:9px;font-weight:900;letter-spacing:.11em;text-transform:uppercase}.idea-card h4{margin:0;font:800 17px/1.25 var(--display);letter-spacing:-.025em}.idea-card>p{margin:9px 0 14px;color:#5b5c64;font-size:11px;line-height:1.58;-webkit-line-clamp:3}.idea-tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:auto}.idea-tags span{padding:4px 7px;border-radius:999px;background:rgba(255,255,255,.55);color:#74727a;font-size:8px;font-weight:700}.idea-card-foot{margin-top:16px;padding-top:12px;border-top:1px solid rgba(45,40,34,.075)}.idea-card-foot small{color:#85828a;font-size:8px;font-weight:700}.owner-mini{font-size:9px}.owner-mini .avatar{width:26px;height:26px;border-radius:9px;font-size:10px}
.stage-surface-Idea{--stage-card:var(--stage-idea-soft);--stage-color:var(--stage-idea)}.stage-surface-Brainstorming{--stage-card:var(--stage-brain-soft);--stage-color:var(--stage-brain)}.stage-surface-Validation{--stage-card:var(--stage-valid-soft);--stage-color:var(--stage-valid)}.stage-surface-Planning{--stage-card:var(--stage-plan-soft);--stage-color:var(--stage-plan)}.stage-surface-Execution{--stage-card:var(--stage-exec-soft);--stage-color:var(--stage-exec)}
.idea-score-orb{position:relative;width:45px;height:45px;display:grid;place-items:center;border-radius:50%;background:rgba(255,255,255,.72);box-shadow:inset 0 0 0 1px rgba(45,40,34,.08)}.idea-score-orb strong{font:800 14px/1 var(--display);letter-spacing:-.04em}.idea-score-orb.empty{color:var(--faint)}.pulse-hot .idea-score-orb::after,.detail-score-block.pulse-hot::after{content:"";position:absolute;inset:-5px;border:1px solid color-mix(in srgb,var(--stage-color,var(--primary)) 50%,transparent);border-radius:inherit;animation:ideaPulse 2.2s ease-out infinite}.pulse-warm .idea-score-orb::after{content:"";position:absolute;inset:-3px;border:1px solid rgba(80,80,90,.10);border-radius:inherit}@keyframes ideaPulse{0%{opacity:.8;transform:scale(.9)}70%,100%{opacity:0;transform:scale(1.18)}}
.board-column.drag-over{outline:0;background:rgba(88,105,246,.08);box-shadow:inset 0 0 0 2px rgba(88,105,246,.25)}

/* Side workspace for ideas */
.modal-detail{position:fixed;inset:0 0 0 auto;margin:0;width:min(1080px,calc(100vw - 100px));height:100dvh;max-height:none;border:0;border-radius:28px 0 0 28px;background:#fffdfa;box-shadow:-30px 0 90px rgba(18,18,24,.18);animation:workspaceIn .26s cubic-bezier(.2,.8,.2,1);overflow:hidden}.modal-detail::backdrop{background:rgba(20,20,26,.28);backdrop-filter:blur(5px)}@keyframes workspaceIn{from{transform:translateX(34px);opacity:.2}to{transform:none;opacity:1}}.detail-shell{height:100%;display:flex;flex-direction:column}.detail-hero{flex:0 0 auto;padding:30px 34px 24px;background:linear-gradient(145deg,#fffdfa,#f4f0e9);border-bottom:0}.detail-title-row{display:flex;align-items:flex-end;justify-content:space-between;gap:30px}.detail-title-row>div:first-child{min-width:0}.detail-hero h2{font-size:34px;max-width:760px}.detail-score-block{position:relative;flex:0 0 auto;width:112px;height:112px;border-radius:34px;display:grid;place-items:center;align-content:center;background:#171923;color:#fff;box-shadow:0 18px 42px rgba(23,25,35,.20)}.detail-score-block strong{font:800 34px/1 var(--display);letter-spacing:-.06em}.detail-score-block span{margin-top:7px;color:rgba(255,255,255,.55);font-size:8px;font-weight:700}.detail-tabs{flex:0 0 auto;padding:0 30px;border-bottom:1px solid rgba(45,40,34,.08);background:#fffdfa}.detail-tab{position:relative;border-radius:0}.detail-tab.active{background:transparent;color:#171923}.detail-tab.active::after{content:"";position:absolute;left:12px;right:12px;bottom:-1px;height:2px;border-radius:2px;background:#171923}.detail-content{flex:1;min-height:0;overflow:auto;padding:26px 34px}.detail-actions{flex:0 0 auto;background:rgba(255,253,250,.92);backdrop-filter:blur(14px)}.info-card{border:0;background:rgba(239,235,226,.62);border-radius:17px}.inline-form{border:0;background:#f1ede6;border-radius:18px}.note-card,.comment-card,.experiment-card,.task-card{border:0;background:#f4f0e9;border-radius:15px}

/* Analytics destination */
.analytics-hero{margin:-8px 0 18px;padding:27px;border-radius:26px;background:radial-gradient(circle at 88% -30%,rgba(88,105,246,.34),transparent 38%),linear-gradient(135deg,var(--studio-dark),var(--studio-dark2));color:#fff;box-shadow:0 26px 70px rgba(23,25,35,.17)}.analytics-hero-top{display:flex;align-items:flex-start;justify-content:space-between;gap:22px;margin-bottom:22px}.analytics-hero-top>div:first-child>span{display:block;color:rgba(255,255,255,.42);font-size:9px;font-weight:800;letter-spacing:.13em;text-transform:uppercase}.analytics-hero-top h2{margin:3px 0 0;font:800 28px/1.1 var(--display);letter-spacing:-.04em}.analytics-hero .analytics-filters{margin:0;justify-content:flex-end}.analytics-hero .analytics-filters select,.analytics-hero .button-secondary{border-color:rgba(255,255,255,.14);background:rgba(255,255,255,.08);color:#fff}.analytics-hero .analytics-filters select option{color:#171923}.analytics-hero .pipeline{margin:0;padding:0;background:transparent}.analytics-hero .pipeline-step{color:#fff;border-color:rgba(255,255,255,.10);background:rgba(255,255,255,.055)}.analytics-hero .pipeline-step:hover{background:rgba(255,255,255,.11);transform:translateY(-2px)}.analytics-hero .pipeline-step span,.analytics-hero .pipeline-step small{color:rgba(255,255,255,.58)}.analytics-hero-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin-top:18px;border-radius:16px;overflow:hidden;background:rgba(255,255,255,.08)}.analytics-hero-stats>div{padding:13px 15px;background:rgba(10,10,15,.18)}.analytics-hero-stats strong{display:block;font:800 20px/1 var(--display)}.analytics-hero-stats span{display:block;margin-top:5px;color:rgba(255,255,255,.48);font-size:8px;font-weight:700}.analytics-grid{gap:14px}.analytics-card{border:0;border-radius:20px;background:rgba(255,253,250,.78);box-shadow:0 10px 30px rgba(45,38,30,.05)}
.bar-fill{transition:width .65s cubic-bezier(.2,.8,.2,1)}.timeline-line{stroke-dasharray:1000;stroke-dashoffset:1000;animation:drawLine .9s ease forwards}@keyframes drawLine{to{stroke-dashoffset:0}}

/* Profiles + emoji avatars */
.avatar-emoji{font-family:"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif;font-weight:400}.studio-profile-card{position:relative;overflow:hidden;border:0;background:rgba(255,253,250,.8);box-shadow:0 14px 38px rgba(45,38,30,.055)}.studio-profile-card::after{content:"";position:absolute;width:180px;height:180px;border-radius:50%;right:-95px;top:-95px;background:var(--primarySoft);opacity:.55;pointer-events:none}.profile-hero{position:relative;z-index:1}.profile-avatar{width:64px!important;height:64px!important;border-radius:22px!important;font-size:26px!important}.profile-avatar-button{margin-left:auto}.avatar-options{display:grid;grid-template-columns:repeat(8,1fr);gap:8px}.avatar-option{aspect-ratio:1;border:1px solid rgba(45,40,34,.09);border-radius:14px;background:#f4f0e9;font-size:24px;cursor:pointer;transition:.16s ease}.avatar-option:hover{transform:translateY(-2px) scale(1.04);background:#fff;box-shadow:0 8px 20px rgba(45,38,30,.08)}.avatar-custom-field{margin-top:18px;margin-bottom:0}.avatar-dialog .modal-body{padding-top:18px}

/* Softer containers and motion */
.panel,.review-card,.profile-card{border-color:rgba(45,40,34,.075)}.panel{background:rgba(255,253,250,.72);backdrop-filter:blur(8px)}.view-toggle{border:0;background:rgba(255,253,250,.72);box-shadow:0 5px 18px rgba(45,38,30,.05)}.view-toggle button.active{background:#171923;color:#fff}.data-table tbody tr{transition:background .15s ease,transform .15s ease}.data-table tbody tr:hover{background:#f4f0e9}.toast{border:0;border-radius:15px;box-shadow:0 18px 50px rgba(45,38,30,.14)}

@media(max-width:1100px){.focus-grid{grid-template-columns:1fr 1fr}.focus-grid .idea-card:last-child{display:none}.analytics-hero-top{display:block}.analytics-hero .analytics-filters{margin-top:18px;justify-content:flex-start}}
@media(max-width:900px){.sidebar{inset:0 auto 0 0;height:auto;border-radius:0 22px 22px 0}.main-content,body.sidebar-collapsed .main-content{margin-left:0}.page-root{padding-top:78px}.floating-action:hover{width:54px}.floating-action::after{display:none}.modal-detail{width:100vw;border-radius:0}.detail-title-row{align-items:flex-start}.detail-score-block{width:86px;height:86px;border-radius:27px}.detail-score-block strong{font-size:27px}.analytics-hero{border-radius:20px}}
@media(max-width:650px){.page-root{padding-inline:14px}.focus-grid{grid-template-columns:1fr}.focus-grid .idea-card:last-child{display:block}.focus-head h2{font-size:27px}.metric-grid-compact{grid-template-columns:repeat(2,1fr)}.idea-card{min-height:170px}.analytics-hero{padding:18px}.analytics-hero-stats{grid-template-columns:repeat(2,1fr)}.analytics-hero .pipeline{grid-template-columns:1fr}.avatar-options{grid-template-columns:repeat(4,1fr)}.detail-hero{padding:24px 18px 18px}.detail-hero h2{font-size:27px}.detail-title-row{display:block}.detail-score-block{margin-top:18px}.detail-tabs{padding-inline:10px}.detail-content{padding:20px 16px}.floating-actions{right:15px;bottom:15px}}
'''

p.write_text(s, encoding='utf-8')
