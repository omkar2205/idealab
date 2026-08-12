from pathlib import Path
import re

app = Path('app.js')
s = app.read_text()

s = re.sub(
    r"const pageInfo = \{\n\s*home:\['Workspace','Home'\],ideas:\['Idea pipeline','Ideas'\],brainstorming:\['Explore','Brainstorm'\],validation:\['Evidence','Validate'\],planning:\['Shape it','Planning'\],execution:\['Build it','Execution'\],reviews:\['Weekly rhythm','Weekly review'\],archive:\['History','Archive'\],profiles:\['Together','Profiles'\]\n\s*\};",
    "const pageInfo = {\n    home:['','Home'],ideas:['','Ideas'],brainstorming:['','Brainstorm'],validation:['','Validate'],planning:['','Planning'],execution:['','Execution'],reviews:['','Weekly review'],archive:['','Archive'],profiles:['','Profiles']\n  };",
    s,
)

s = s.replace(
    "function navigate(page){state.currentPage=page;const [k,t]=pageInfo[page]||pageInfo.home;els.pageKicker.textContent=k;els.pageTitle.textContent=t;",
    "function navigate(page){state.currentPage=page;const [k,t]=pageInfo[page]||pageInfo.home;els.pageKicker.textContent=k;els.pageKicker.hidden=!k;els.pageTitle.textContent=t;"
)

s = re.sub(
    r"  function activityRow\(a\)\{.*?\}\n\n  function renderHome\(\)\{.*?\n  \}\n\n  function ideaCard",
    """  function renderHome(){
    const d=state.dashboard||{},recent=state.ideas.slice().sort((a,b)=>String(b.LastActivityAt||b.UpdatedAt||'').localeCompare(String(a.LastActivityAt||a.UpdatedAt||''))).slice(0,6);
    els.homePage.innerHTML=`<div class=\"metric-grid\">${metric('primary',iconBulb(),d.activeIdeas??state.ideas.length,'Active ideas')}${metric('pink',iconChat(),d.byStage?.Brainstorming??0,'Brainstorming')}${metric('amber',iconSearch(),d.byStage?.Validation??0,'Validation')}${metric('green',iconCheck(),d.openTasks??0,'Open tasks')}</div><div class=\"panel\" style=\"margin-top:16px\"><div class=\"panel-head\"><h3>Recent ideas</h3><button class=\"text-button\" data-nav-inline=\"ideas\">View all</button></div>${recent.length?`<div class=\"idea-list\">${recent.map(ideaRow).join('')}</div>`:empty('No ideas yet','Add an idea to get started.','Add idea')}</div>`;
    bindRendered(els.homePage);
  }

  function ideaCard""",
    s,
    flags=re.S,
)

s = re.sub(
    r"  function renderFocus\(stage\)\{.*?\}\n\n  function renderArchive",
    """  function renderFocus(stage){const rows=state.ideas.filter(i=>i.Stage===stage);els.boardPage.innerHTML=`<div class=\"board-toolbar\"><span class=\"pill\">${rows.length} ideas</span></div>${rows.length?`<div style=\"display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px\">${rows.map(ideaCard).join('')}</div>`:empty(`No ideas in ${stage.toLowerCase()}`,`Add or move an idea to ${stage.toLowerCase()}.`)}`;bindRendered(els.boardPage);}

  function renderArchive""",
    s,
    flags=re.S,
)

s = re.sub(
    r"  function renderArchive\(\)\{.*?\n  \}\n  async function loadArchive",
    """  function renderArchive(){
    els.boardPage.innerHTML=`<div id=\"archiveRoot\"><div class=\"empty-state\"><div class=\"empty-state-inner\"><p>Loading archive…</p></div></div></div>`;
    loadArchive();
  }
  async function loadArchive""",
    s,
    flags=re.S,
)
s = s.replace("empty('Archive is empty','Parked and archived ideas will live here.','Go to ideas','ideas')", "empty('No archived ideas','Archived ideas will appear here.','Go to ideas','ideas')")

s = re.sub(
    r"  function renderReviews\(\)\{.*?\n  \}\n  async function loadReviews",
    """  function renderReviews(){
    els.reviewsPage.innerHTML=`<div class=\"board-toolbar\"><div class=\"board-spacer\"></div><button id=\"newReviewBtn\" class=\"button button-primary\">${iconPlus()} Start review</button></div><div class=\"review-layout\"><div><div class=\"review-card\"><div class=\"review-date\"><div><h3>Current snapshot</h3><p>${esc(todayLabel())}</p></div><span class=\"pill\">${state.dashboard.needsReview||0} need review</span></div><div class=\"profile-stats\"><div class=\"profile-stat\"><strong>${state.ideas.length}</strong><span>Active ideas</span></div><div class=\"profile-stat\"><strong>${state.dashboard.runningExperiments||0}</strong><span>Experiments</span></div><div class=\"profile-stat\"><strong>${state.dashboard.openTasks||0}</strong><span>Open tasks</span></div></div></div><div id=\"reviewSessions\" class=\"review-card\"><h3>Review sessions</h3><p>Loading sessions…</p></div></div><aside class=\"review-card\"><h3>Scoring</h3><div style=\"margin-top:14px;display:grid;gap:8px\"><span class=\"pill\">Excitement · 1–5</span><span class=\"pill\">Market potential · 1–5</span><span class=\"pill\">Feasibility · 1–5</span><span class=\"pill\">Speed to test · 1–5</span><span class=\"pill\">Capital efficiency · 1–5</span><span class=\"pill\">Confidence · 1–5</span></div></aside></div>`;
    $('newReviewBtn').addEventListener('click',createReview);loadReviews();
  }
  async function loadReviews""",
    s,
    flags=re.S,
)
s = s.replace("<p>Previous weekly check-ins.</p>", "")
s = s.replace("<small>Create the first one when you are ready.</small>", "<small>No review sessions yet.</small>")
s = s.replace("toast('Review created','Your weekly review session is ready.');", "toast('Review created');")

s = re.sub(
    r"  function renderProfiles\(\)\{.*?\}\n  function profileCard",
    """  function renderProfiles(){els.profilesPage.innerHTML=`<div class=\"profile-grid\">${state.profiles.map(profileCard).join('')}</div>`;}
  function profileCard""",
    s,
    flags=re.S,
)

s = s.replace("toast(id?'Idea updated':'Idea captured',id?'Changes saved.':'It is on the board.');", "toast(id?'Idea updated':'Idea saved','Changes saved.');")
app.write_text(s)

index = Path('index.html')
h = index.read_text()
h = h.replace(
    '<p class="eyebrow light">A space for ideas worth exploring</p>\n          <h1>Think freely.<br>Build deliberately.</h1>\n          <p>Capture rough thoughts, challenge assumptions, and move the promising ones forward together.</p>',
    '<h1>IdeaLab</h1>\n          <p>Private workspace for ideas, planning and reviews.</p>'
)
h = re.sub(r'\n        <div class="login-mini-board">.*?</div>', '', h, flags=re.S)
h = h.replace('<p class="eyebrow">Capture it before it disappears</p>', '<p class="eyebrow">Idea details</p>')
index.write_text(h)
