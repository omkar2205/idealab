from pathlib import Path
import re

# ---------- index.html ----------
p = Path('index.html')
s = p.read_text(encoding='utf-8')

brain = '''        <button class="nav-item" data-nav="brainstorming" title="Brainstorm">
          <svg viewBox="0 0 24 24"><path d="M4 5h16v11H7l-3 3V5Z"/><path d="M8 9h8M8 12h5"/></svg><span>Brainstorm</span>
        </button>
'''
valid = '''        <button class="nav-item" data-nav="validation" title="Validate">
          <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6"/><path d="m16 16 4 4M8.5 11l1.7 1.7 3.5-3.5"/></svg><span>Validate</span>
        </button>
'''
s = s.replace(brain, '', 1).replace(valid, '', 1)

ideas_block = '''        <button class="nav-item" data-nav="ideas" title="Ideas">
          <svg viewBox="0 0 24 24"><path d="M9 18h6M10 22h4M8.5 14.5C7 13.5 6 11.8 6 9.8A6 6 0 0 1 18 9.8c0 2-1 3.7-2.5 4.7-.7.5-1 1.1-1 1.8h-5c0-.7-.3-1.3-1-1.8Z"/></svg><span>Ideas</span><span id="navIdeaCount" class="nav-count">0</span>
        </button>
'''
mywork = ideas_block + '''        <button class="nav-item" data-nav="mywork" title="My Work">
          <svg viewBox="0 0 24 24"><path d="M9 5h10v16H5V5h4"/><path d="M9 3h6v4H9zM8 12l2 2 4-4M8 18h7"/></svg><span>My Work</span>
        </button>
'''
if 'data-nav="mywork"' not in s:
    if ideas_block not in s:
        raise SystemExit('Ideas nav marker missing')
    s = s.replace(ideas_block, mywork, 1)

stage_field = '<label class="field"><span>Stage</span><select id="ideaStage"><option>Idea</option><option>Brainstorming</option><option>Validation</option><option>Planning</option><option>Execution</option></select></label>'
s = s.replace(stage_field, '<input id="ideaStage" type="hidden" value="Idea">', 1)
p.write_text(s, encoding='utf-8')

# ---------- app.js ----------
p = Path('app.js')
s = p.read_text(encoding='utf-8')

s = s.replace("  const STAGES = ['Idea','Brainstorming','Validation','Planning','Execution'];", "  const STAGES = ['Idea','Planning','Execution'];", 1)
s = s.replace("  const TASK_STATUSES = ['To Do','Doing','Done'];", "  const TASK_STATUSES = ['To Do','Doing','Blocked','Done'];", 1)
s = s.replace("    dragIdeaId:'', analyticsFilters:{owner:'all',stage:'all',category:'all',score:'all'}", "    dragIdeaId:'', workItems:[], workFilter:'mine', analyticsFilters:{owner:'all',stage:'all',category:'all',score:'all',flow:'all'}", 1)

helper_marker = "  function updatedLabel(i){const d=activityAgeDays(i);if(d<1)return'Updated today';if(d<2)return'Updated yesterday';if(d<14)return`Updated ${Math.floor(d)}d ago`;return fmtDate(i.UpdatedAt||i.LastActivityAt||i.CreatedAt);}\n"
helpers = helper_marker + '''  function workflowStatus(i){const s=String(i?.Status||'');if(s==='Completed')return'Completed';if(String(i?.Stage||'Idea')!=='Idea')return String(i?.Stage||'Idea');if(s==='Awaiting Review')return'Awaiting review';if(s==='Needs Work')return'Needs work';if(s==='Approved')return'Approved';return'Draft';}
  function workflowBucket(i){if(String(i?.Status||'')==='Completed')return'Completed';if(String(i?.Stage||'')==='Planning')return'Planning';if(String(i?.Stage||'')==='Execution')return'Execution';if(String(i?.Status||'')==='Awaiting Review')return'Review';if(String(i?.Status||'')==='Approved')return'Approved';return'Ideas';}
  function otherMember(){return state.profiles.map(p=>p.user||p).find(u=>u.userId!==state.user?.userId)||null;}
  function currentWorkflowSurface(i){return i.Stage==='Idea'?`status-surface-${safe(workflowStatus(i))}`:`stage-surface-${safe(i.Stage)}`;}
'''
if helper_marker not in s:
    raise SystemExit('helper marker missing')
s = s.replace(helper_marker, helpers, 1)

old_render_current = "  function renderCurrent(){if(!state.user)return;const page=state.currentPage;if(page==='home')renderHome();else if(page==='ideas')renderIdeas();else if(['brainstorming','validation','planning','execution'].includes(page))renderStage(page);else if(page==='reviews')renderReviews();else if(page==='analytics')renderAnalytics();else if(page==='archive')renderArchive();else if(page==='profiles')renderProfiles();else renderHome();}"
new_render_current = "  function renderCurrent(){if(!state.user)return;const page=state.currentPage;if(page==='home')renderHome();else if(page==='ideas')renderIdeas();else if(page==='mywork')renderMyWork();else if(['planning','execution'].includes(page))renderStage(page);else if(page==='reviews')renderReviews();else if(page==='analytics')renderAnalytics();else if(page==='archive')renderArchive();else if(page==='profiles')renderProfiles();else renderHome();}"
if old_render_current not in s:
    raise SystemExit('renderCurrent marker missing')
s = s.replace(old_render_current, new_render_current, 1)

idea_funcs_pat = re.compile(r"  function ideaRow\(i\)\{.*?\n  function renderHome", re.S)
idea_funcs = '''  function ideaRow(i){const u=userById(i.OwnerUserID),color=u?.accentColor||'#5869f6';return`<button class="idea-list-row" data-open-idea="${esc(i.IdeaID)}"><span class="owner-stripe" style="--owner-color:${color}"></span><span class="idea-list-copy"><strong>${esc(i.Title)}</strong><p>${esc(i.OneLineSummary||i.Description||'No description')}</p></span><span class="idea-list-meta">${scoreBadge(i.IdeaID)}<span class="stage-chip stage-${safe(i.Stage)}">${esc(workflowStatus(i))}</span></span></button>`;}
  function ideaCard(i){const u=userById(i.OwnerUserID),color=u?.accentColor||'#5869f6',score=combinedScore(i.IdeaID),tags=String(i.Tags||'').split(',').map(x=>x.trim()).filter(Boolean).slice(0,2);return`<article class="idea-card ${currentWorkflowSurface(i)} ${pulseClass(i)}" draggable="false" data-open-idea="${esc(i.IdeaID)}" style="--owner-color:${color}"><div class="idea-card-stage"><span>${esc(workflowStatus(i))}</span><span class="idea-score-orb ${score==null?'empty':''}"><strong>${score==null?'—':score.toFixed(1)}</strong></span></div><h4>${esc(i.Title)}</h4><p>${esc(i.OneLineSummary||i.Description||'No summary')}</p>${tags.length?`<div class="idea-tags">${tags.map(t=>`<span>${esc(t)}</span>`).join('')}</div>`:''}<div class="idea-card-foot"><span class="owner-mini">${ownerAvatar(i.OwnerUserID)}${esc(u?.displayName||'Unknown')}</span><small>${esc(updatedLabel(i))}</small></div></article>`;}

  function renderHome'''
s, n = idea_funcs_pat.subn(idea_funcs, s, count=1)
if n != 1:
    raise SystemExit('idea functions block missing')

# Replace Ideas board + ranked + lifecycle stages. Keep old DnD function unused below.
board_pat = re.compile(r"  function boardColumn\(stage,ideas\)\{.*?\n\n  function bindBoardDnD", re.S)
board_new = '''  function ideaStatusColumn(title,ideas){return`<section class="board-column board-status-${safe(title)}"><div class="board-column-head"><h3>${esc(title)}</h3><span class="column-count">${ideas.length}</span></div><div class="board-cards">${ideas.length?ideas.map(ideaCard).join(''):'<div class="empty-column">No ideas</div>'}</div></section>`;}
  function renderIdeas(){if(state.ideaView==='ranked')return renderRanked();const rows=state.ideas.filter(i=>i.Stage==='Idea'&&i.Status!=='Completed');const draft=rows.filter(i=>!['Awaiting Review','Needs Work','Approved'].includes(String(i.Status||''))),review=rows.filter(i=>i.Status==='Awaiting Review'),needs=rows.filter(i=>i.Status==='Needs Work'),approved=rows.filter(i=>i.Status==='Approved');wrap(`<div class="board-toolbar"><div class="view-toggle"><button class="active" data-idea-view="board">Board</button><button data-idea-view="ranked">Ranked</button></div><div class="board-spacer"></div><span class="board-hint">Review before planning</span></div><div class="board idea-review-board">${ideaStatusColumn('Draft',draft)}${ideaStatusColumn('Awaiting review',review)}${ideaStatusColumn('Needs work',needs)}${ideaStatusColumn('Approved',approved)}</div>`);}
  function rankedRows(ideas=state.ideas){return [...ideas].sort((a,b)=>(combinedScore(b.IdeaID)??-1)-(combinedScore(a.IdeaID)??-1));}
  function renderRanked(){const users=state.profiles.map(p=>p.user||p),rows=rankedRows(state.ideas.filter(i=>i.Stage==='Idea'&&i.Status!=='Completed'));wrap(`<div class="board-toolbar"><div class="view-toggle"><button data-idea-view="board">Board</button><button class="active" data-idea-view="ranked">Ranked</button></div><div class="board-spacer"></div><span class="pill">${rows.length} ideas</span></div><div class="panel table-wrap"><table class="data-table"><thead><tr><th>#</th><th>Idea</th><th>Status</th><th>Owner</th>${users.map(u=>`<th>${esc(u.displayName)} score</th>`).join('')}<th>Combined</th><th>Category</th></tr></thead><tbody>${rows.map((i,idx)=>`<tr data-open-idea="${esc(i.IdeaID)}"><td class="rank-number">${idx+1}</td><td><strong>${esc(i.Title)}</strong></td><td><span class="stage-chip">${esc(workflowStatus(i))}</span></td><td>${esc(profileName(i.OwnerUserID))}</td>${users.map(u=>`<td>${round1(ratingScore(ratingFor(i.IdeaID,u.userId)))}</td>`).join('')}<td><strong>${round1(combinedScore(i.IdeaID))}</strong></td><td>${esc(i.Category||'—')}</td></tr>`).join('')}</tbody></table></div>`);}
  function renderStage(page){const stage={planning:'Planning',execution:'Execution'}[page],rows=state.ideas.filter(i=>i.Stage===stage);wrap(`<div class="board-toolbar"><span class="pill">${rows.length} ideas</span></div>${rows.length?`<div class="lifecycle-grid">${rows.map(ideaCard).join('')}</div>`:empty('No ideas here',stage==='Planning'?'Approved ideas can be moved here from Ideas.':'Planning ideas can be started when you are ready to execute.')}`);}

  function renderMyWork(){const other=otherMember();wrap(`<div class="work-toolbar"><div><span class="eyebrow">Responsibilities</span><h2>My Work</h2></div><div class="view-toggle work-toggle"><button class="${state.workFilter==='mine'?'active':''}" data-work-filter="mine">Mine</button>${other?`<button class="${state.workFilter==='other'?'active':''}" data-work-filter="other">${esc(other.displayName||other.fullName)}</button>`:''}<button class="${state.workFilter==='all'?'active':''}" data-work-filter="all">All</button></div></div><div id="workRoot" class="work-root"><div class="work-loading">Loading responsibilities…</div></div>`);qsa('[data-work-filter]',els.pageRoot).forEach(b=>b.addEventListener('click',()=>{state.workFilter=b.dataset.workFilter;renderMyWork();}));loadMyWork();}
  async function loadMyWork(){const root=$('workRoot');if(!root)return;try{const p=await insights('listWork');state.workItems=p.items||[];drawMyWork();}catch(e){root.innerHTML=empty('Could not load responsibilities',e.message);}}
  function drawMyWork(){const root=$('workRoot');if(!root)return;const other=otherMember(),assignee=state.workFilter==='mine'?state.user.userId:state.workFilter==='other'?other?.userId:null;let items=state.workItems.filter(x=>!assignee||x.assigneeUserId===assignee);const today=new Date();today.setHours(0,0,0,0);const week=today.getTime()+7*86400000;const due=x=>{const d=new Date(x.dueDate||'');return Number.isNaN(d.getTime())?0:d.getTime();};const groups=[['Pending reviews',items.filter(x=>x.type==='review')],['Overdue',items.filter(x=>x.type!=='review'&&due(x)&&due(x)<today.getTime())],['Due this week',items.filter(x=>x.type!=='review'&&due(x)>=today.getTime()&&due(x)<=week)],['Later',items.filter(x=>x.type!=='review'&&due(x)>week)],['No due date',items.filter(x=>x.type!=='review'&&!due(x))]].filter(([,r])=>r.length);const overdue=items.filter(x=>x.type!=='review'&&due(x)&&due(x)<today.getTime()).length,reviews=items.filter(x=>x.type==='review').length;root.innerHTML=`<div class="work-summary"><div><strong>${items.length}</strong><span>Open</span></div><div><strong>${reviews}</strong><span>Reviews</span></div><div><strong>${overdue}</strong><span>Overdue</span></div></div>${groups.length?groups.map(([title,rows])=>`<section class="work-group"><h3>${esc(title)}</h3><div class="work-list">${rows.map(x=>`<article class="work-item ${x.type==='review'?'review-work':''}"><div class="work-item-main"><span class="work-type">${esc(x.type==='review'?'Review':x.type==='task'?'Task':'Idea')}</span><strong>${esc(x.title)}</strong><p>${esc(x.ideaTitle)} · ${esc(x.ideaStage||'Idea')}</p></div><div class="work-item-meta">${x.dueDate?`<span>${esc(fmtDate(x.dueDate))}</span>`:''}<span class="pill">${esc(x.status||'Open')}</span><button class="button button-secondary button-small" data-work-open="${esc(x.ideaId)}" data-work-tab="${x.type==='review'?'rating':x.ideaStage==='Execution'?'execution':x.ideaStage==='Planning'?'planning':'overview'}">${x.type==='review'?'Review':'Open'}</button>${x.type==='task'?`<button class="button button-primary button-small" data-work-done="${esc(x.id)}">Done</button>`:''}</div></article>`).join('')}</div></section>`).join(''):empty('Nothing pending','No open responsibilities in this view.')}`;qsa('[data-work-open]',root).forEach(b=>b.addEventListener('click',()=>openIdea(b.dataset.workOpen,b.dataset.workTab||'overview')));qsa('[data-work-done]',root).forEach(b=>b.addEventListener('click',()=>completeWorkTask(b.dataset.workDone)));}
  async function completeWorkTask(taskId){try{await api('updateTask',{taskId,status:'Done'});toast('Task completed');await loadMyWork();}catch(e){toast('Could not update task',e.message,'error');}}

  function bindBoardDnD'''
s, n = board_pat.subn(board_new, s, count=1)
if n != 1:
    raise SystemExit('board block missing')

# Analytics flow filter and lifecycle pipeline
s = s.replace("  function analyticsIdeas(){return state.ideas.filter(i=>{const f=state.analyticsFilters;if(f.owner!=='all'&&i.OwnerUserID!==f.owner)return false;if(f.stage!=='all'&&i.Stage!==f.stage)return false;", "  function analyticsIdeas(){return state.ideas.filter(i=>{const f=state.analyticsFilters;if(f.owner!=='all'&&i.OwnerUserID!==f.owner)return false;if(f.stage!=='all'&&i.Stage!==f.stage)return false;if(f.flow!=='all'&&workflowBucket(i)!==f.flow)return false;", 1)
pipe_pat = re.compile(r"  function pipelineHTML\(ideas\)\{.*?\n  function topBars", re.S)
pipe_new = '''  function pipelineHTML(ideas){const steps=['Ideas','Review','Approved','Planning','Execution','Completed'];return`<div class="pipeline">${steps.map(s=>{const n=ideas.filter(i=>workflowBucket(i)===s).length,pct=ideas.length?Math.round(n/ideas.length*100):0;return`<button class="pipeline-step" data-analytics-flow="${esc(s)}"><strong>${n}</strong><span>${esc(s==='Review'?'Awaiting review':s)}</span><small>${pct}%</small></button>`}).join('')}</div>`;}
  function topBars'''
s, n = pipe_pat.subn(pipe_new, s, count=1)
if n != 1:
    raise SystemExit('pipelineHTML missing')

bind_analytics_pat = re.compile(r"  function bindAnalytics\(\)\{.*?\n  function exportRows", re.S)
bind_analytics_new = '''  function bindAnalytics(){['Owner','Stage','Category','Score'].forEach(k=>{const el=$(`analytics${k}`);el?.addEventListener('change',()=>{state.analyticsFilters[k.toLowerCase()]=el.value;if(k==='Stage')state.analyticsFilters.flow='all';renderAnalytics();});});$('exportCsv')?.addEventListener('click',()=>exportAnalytics('csv'));$('exportExcel')?.addEventListener('click',()=>exportAnalytics('excel'));qsa('[data-analytics-flow]',els.pageRoot).forEach(x=>x.addEventListener('click',()=>{state.analyticsFilters.flow=x.dataset.analyticsFlow;state.analyticsFilters.stage='all';renderAnalytics();}));qsa('[data-svg-idea]',els.pageRoot).forEach(x=>x.addEventListener('click',()=>openIdea(x.dataset.svgIdea)));}
  function exportRows'''
s, n = bind_analytics_pat.subn(bind_analytics_new, s, count=1)
if n != 1:
    raise SystemExit('bindAnalytics missing')
s = s.replace("headers:['Idea','Owner','Stage',...users.map(u=>`${u.displayName} score`),'Combined score','Category','Priority','Created','Updated']", "headers:['Idea','Owner','Stage','Status',...users.map(u=>`${u.displayName} score`),'Combined score','Category','Priority','Created','Updated']", 1)
s = s.replace("[i.Title,profileName(i.OwnerUserID),i.Stage,...users.map", "[i.Title,profileName(i.OwnerUserID),i.Stage,workflowStatus(i),...users.map", 1)

# New ideas start Draft and immediately go to self rating.
s = s.replace("ownerUserId:state.user.userId,stage:'Idea',priority:'Medium'});els.quickIdeaDialog.close();await refresh();toast('Idea saved');if(p.idea?.IdeaID)openIdea(p.idea.IdeaID);", "ownerUserId:state.user.userId,stage:'Idea',status:'Draft',priority:'Medium'});els.quickIdeaDialog.close();await refresh();toast('Idea saved');if(p.idea?.IdeaID)openIdea(p.idea.IdeaID,'rating');", 1)
s = s.replace("const draft={Title:els.quickIdeaTitle.value.trim(),OneLineSummary:els.quickIdeaSummary.value.trim(),OwnerUserID:state.user.userId,Stage:'Idea',Priority:'Medium'}", "const draft={Title:els.quickIdeaTitle.value.trim(),OneLineSummary:els.quickIdeaSummary.value.trim(),OwnerUserID:state.user.userId,Stage:'Idea',Status:'Draft',Priority:'Medium'}", 1)

save_idea_pat = re.compile(r"  async function saveIdea\(e\)\{.*?\n\n  async function openIdea", re.S)
save_idea_new = '''  async function saveIdea(e){e.preventDefault();const id=els.ideaId.value,data={title:els.ideaTitle.value.trim(),oneLineSummary:els.ideaSummary.value.trim(),stage:els.ideaStage.value,priority:els.ideaPriority.value,ownerUserId:els.ideaOwner.value,category:els.ideaCategory.value.trim(),tags:els.ideaTags.value.trim(),description:els.ideaDescription.value.trim(),problem:els.ideaProblem.value.trim(),proposedSolution:els.ideaSolution.value.trim(),targetUser:els.ideaTargetUser.value.trim(),whyItCouldWork:els.ideaWhy.value.trim(),nextAction:els.ideaNextAction.value.trim(),nextActionOwner:els.ideaNextOwner.value,nextActionDue:els.ideaNextDue.value};if(!data.title)return;busy(els.saveIdeaButton,true,'Saving…');try{let created=null;if(id){data.ideaId=id;await api('updateIdea',data);}else{data.status='Draft';created=await api('createIdea',data);}els.ideaDialog.close();await refresh();toast(id?'Idea updated':'Idea saved');if(!id&&created?.idea?.IdeaID)openIdea(created.idea.IdeaID,'rating');}catch(err){toast('Could not save idea',err.message,'error');}finally{busy(els.saveIdeaButton,false);}}

  async function openIdea'''
s, n = save_idea_pat.subn(save_idea_new, s, count=1)
if n != 1:
    raise SystemExit('saveIdea block missing')

s = s.replace("  function detailTabs(){return[['overview','Overview'],['brainstorm','Brainstorm'],['rating','Rating'],['validation','Validate'],['planning','Plan'],['execution','Execute'],['media','Media']];}", "  function detailTabs(){return[['overview','Overview'],['brainstorm','Discussion'],['rating','Rating'],['validation','Validation'],['planning','Plan'],['execution','Execute'],['media','Media']];}", 1)

# Show lifecycle state in idea hero.
render_detail_pat = re.compile(r"  function renderIdeaDetail\(\)\{.*?\n  function renderDetailTab", re.S)
render_detail_new = '''  function renderIdeaDetail(){const i=state.currentIdea,d=state.currentIdeaData;if(!i||!d)return;const u=userById(i.OwnerUserID),c=u?.accentColor||'#5869f6',score=combinedScore(i.IdeaID);els.ideaDetailRoot.innerHTML=`<div class="detail-shell"><button class="icon-button detail-close" data-close-detail>${icon.close}</button><div class="detail-hero"><div class="detail-meta"><span class="stage-chip">${esc(workflowStatus(i))}</span><span class="pill" style="color:${c}">${esc(u?.displayName||'Unknown')}</span>${i.Category?`<span class="pill">${esc(i.Category)}</span>`:''}</div><div class="detail-title-row"><div><h2>${esc(i.Title)}</h2><p>${esc(i.OneLineSummary||'')}</p></div><div class="detail-score-block ${pulseClass(i)}"><strong>${score==null?'—':score.toFixed(1)}</strong><span>Combined score</span></div></div></div><div class="detail-tabs">${detailTabs().map(([k,label])=>`<button class="detail-tab ${state.currentTab===k?'active':''}" data-detail-tab="${k}">${label}</button>`).join('')}</div><div id="detailContent" class="detail-content">${renderDetailTab()}</div><div class="detail-actions"><button class="button button-danger button-small" data-archive-idea>Archive</button><div class="detail-action-right"><button class="button button-secondary button-small" data-rate-current>Rate idea</button><button class="button button-secondary button-small" data-edit-current>Edit</button></div></div></div>`;bindDetailEvents();afterDetailRender();}
  function renderDetailTab'''
s, n = render_detail_pat.subn(render_detail_new, s, count=1)
if n != 1:
    raise SystemExit('renderIdeaDetail missing')
s = s.replace("case'planning':return planningTab(i);", "case'planning':return planningTab(i,d);", 1)

rating_pat = re.compile(r"  function ratingTab\(i\)\{.*?\n  function validationTab", re.S)
rating_new = '''  function workflowPanel(i,mine){const status=String(i.Status||'Draft'),isOwner=i.OwnerUserID===state.user.userId,isReviewer=i.CoOwnerUserID===state.user.userId,other=otherMember();if(i.Stage!=='Idea')return'';if(isOwner&&['','Active','Draft','Needs Work'].includes(status)){return`<div class="workflow-panel"><div><span class="eyebrow">Next step</span><h3>${status==='Needs Work'?'Update and resubmit':'Send for review'}</h3><p>${mine?`Your rating is saved. Send this idea to ${esc(other?.displayName||'the other member')} for an independent review.`:'Rate your idea first. Once your self-rating is saved, you can send it for review.'}</p></div>${mine?'<button id="sendForReviewBtn" class="button button-primary">Send for review</button>':''}</div>`;}if(status==='Awaiting Review'){if(isReviewer)return`<div class="workflow-panel"><div><span class="eyebrow">Review requested</span><h3>Your decision</h3><p>${mine?'Your rating is saved. Choose what should happen next.':'Rate the idea first, then choose a decision.'}</p></div>${mine?'<div class="workflow-actions"><button class="button button-primary" data-review-decision="Proceed">Proceed</button><button class="button button-secondary" data-review-decision="Needs work">Needs work</button><button class="button button-danger" data-review-decision="Park">Park</button></div>':''}</div>`;return`<div class="workflow-panel waiting"><div><span class="eyebrow">Awaiting review</span><h3>Waiting for ${esc(profileName(i.CoOwnerUserID))}</h3><p>You can still edit the idea while the review is pending.</p></div></div>`;}if(status==='Approved'&&isOwner)return`<div class="workflow-panel approved"><div><span class="eyebrow">Approved</span><h3>Ready for planning</h3><p>The review is complete. Move this idea into Planning when you want to turn it into responsibilities and actions.</p></div><button id="movePlanningBtn" class="button button-primary">Move to Planning</button></div>`;return'';}
  function ratingTab(i){const users=state.profiles.map(p=>p.user||p),mine=ratingFor(i.IdeaID,state.user.userId),combined=combinedScore(i.IdeaID);return`<div class="rating-summary"><div class="big-score"><strong>${round1(combined)}</strong><span>Combined score</span></div><div><table class="rating-table"><thead><tr><th>Criteria</th>${users.map(u=>`<th>${esc(u.displayName)}</th>`).join('')}</tr></thead><tbody>${CRITERIA.map(([k,label])=>`<tr><td>${esc(label)}</td>${users.map(u=>`<td>${ratingFor(i.IdeaID,u.userId)?.[k]||'—'}</td>`).join('')}</tr>`).join('')}<tr><td><strong>Overall</strong></td>${users.map(u=>`<td><strong>${round1(ratingScore(ratingFor(i.IdeaID,u.userId)))}</strong></td>`).join('')}</tr></tbody></table></div></div><div class="inline-form rating-form" style="margin-top:16px"><h3 class="section-title">${mine?'Your rating':'Rate this idea'}</h3><div class="rating-input-grid">${CRITERIA.map(([k,label])=>`<div class="rating-control"><label>${esc(label)}</label><select data-rating-field="${k}">${Array.from({length:10},(_,x)=>x+1).map(v=>`<option value="${v}" ${(mine?.[k]||8)==v?'selected':''}>${v}</option>`).join('')}</select></div>`).join('')}</div><label class="field" style="margin-top:12px"><span>Note</span><textarea id="ratingNotes" rows="3">${esc(mine?.notes||'')}</textarea></label><button id="saveRatingBtn" class="button button-primary button-small">${mine?'Update rating':'Save rating'}</button></div>${workflowPanel(i,mine)}`;}
  function validationTab'''
s, n = rating_pat.subn(rating_new, s, count=1)
if n != 1:
    raise SystemExit('ratingTab missing')

plan_pat = re.compile(r"  function planningTab\(i\)\{.*?\n  function executionTab", re.S)
plan_new = '''  function planningTab(i,d){const tasks=d.tasks||[];return`<div class="detail-grid"><div class="info-card"><h4>Problem</h4><p>${esc(i.Problem||'Not defined')}</p></div><div class="info-card"><h4>Target user</h4><p>${esc(i.TargetUser||'Not defined')}</p></div><div class="info-card"><h4>Solution</h4><p>${esc(i.ProposedSolution||'Not defined')}</p></div><div class="info-card"><h4>Why it could work</h4><p>${esc(i.WhyItCouldWork||'Not defined')}</p></div></div><div class="inline-form" style="margin-top:14px"><h3 class="section-title">Next action</h3><div class="inline-form-grid"><label class="field field-span"><span>Action</span><input id="planNextAction" value="${esc(i.NextAction||'')}"></label><label class="field"><span>Owner</span><select id="planNextOwner"><option value="">Not assigned</option>${state.profiles.map(p=>{const u=p.user||p;return`<option value="${esc(u.userId)}" ${i.NextActionOwner===u.userId?'selected':''}>${esc(u.displayName||u.fullName)}</option>`}).join('')}</select></label><label class="field"><span>Due</span><input id="planNextDue" type="date" value="${esc(i.NextActionDue||'')}"></label></div><button id="savePlanBtn" class="button button-primary button-small">Save plan</button></div><section class="responsibility-section"><div class="section-simple-head"><h3>Responsibilities</h3></div><div class="planning-task-list">${tasks.length?tasks.map(t=>`<article class="planning-task"><div><strong>${esc(t.Title)}</strong><span>${esc(profileName(t.OwnerUserID))}${t.DueDate?` · ${esc(fmtDate(t.DueDate))}`:''}</span></div><select data-task-status="${esc(t.TaskID)}">${TASK_STATUSES.map(x=>`<option ${x===t.Status?'selected':''}>${x}</option>`).join('')}</select></article>`).join(''):'<p class="quiet-copy">No responsibilities assigned yet.</p>'}</div><div class="inline-form"><div class="inline-form-grid"><label class="field field-span"><span>Responsibility</span><input id="taskTitle"></label><label class="field"><span>Owner</span><select id="taskOwner">${state.profiles.map(p=>{const u=p.user||p;return`<option value="${esc(u.userId)}" ${u.userId===state.user.userId?'selected':''}>${esc(u.displayName||u.fullName)}</option>`}).join('')}</select></label><label class="field"><span>Due</span><input id="taskDue" type="date"></label></div><button id="addTaskBtn" class="button button-primary button-small">Add responsibility</button></div></section>${i.Stage==='Planning'?'<div class="stage-action"><button id="startExecutionBtn" class="button button-primary">Start execution</button></div>':''}`;}
  function executionTab'''
s, n = plan_pat.subn(plan_new, s, count=1)
if n != 1:
    raise SystemExit('planningTab missing')

exec_pat = re.compile(r"  function executionTab\(i,d\)\{.*?\n  function mediaTab", re.S)
exec_new = '''  function executionTab(i,d){const tasks=d.tasks||[];return`<div class="task-board">${TASK_STATUSES.map(status=>`<section class="task-column"><h4>${status}</h4>${tasks.filter(t=>t.Status===status).map(t=>`<div class="task-card"><strong>${esc(t.Title)}</strong><p>${esc(t.Description||'')}</p><small>${esc(profileName(t.OwnerUserID))}${t.DueDate?` · ${esc(fmtDate(t.DueDate))}`:''}</small><select data-task-status="${esc(t.TaskID)}">${TASK_STATUSES.map(s=>`<option ${s===t.Status?'selected':''}>${s}</option>`).join('')}</select></div>`).join('')||'<p style="color:var(--faint);font-size:9px">No tasks</p>'}</section>`).join('')}</div><div class="inline-form"><h3 class="section-title">Add responsibility</h3><div class="inline-form-grid"><label class="field field-span"><span>Task</span><input id="taskTitle"></label><label class="field"><span>Owner</span><select id="taskOwner">${state.profiles.map(p=>{const u=p.user||p;return`<option value="${esc(u.userId)}" ${u.userId===state.user.userId?'selected':''}>${esc(u.displayName||u.fullName)}</option>`}).join('')}</select></label><label class="field"><span>Due</span><input id="taskDue" type="date"></label></div><button id="addTaskBtn" class="button button-primary button-small">Add responsibility</button></div>${i.Status!=='Completed'?'<div class="stage-action"><button id="completeIdeaBtn" class="button button-primary">Mark idea completed</button></div>':'<div class="completed-banner">Completed</div>'}`;}
  function mediaTab'''
s, n = exec_pat.subn(exec_new, s, count=1)
if n != 1:
    raise SystemExit('executionTab missing')

# Wire workflow buttons.
after_pat = re.compile(r"  function afterDetailRender\(\)\{.*?\n  async function reloadCurrentIdea", re.S)
after_new = '''  function afterDetailRender(){const i=state.currentIdea;if(!i)return;$('addBrainstormBtn')?.addEventListener('click',()=>addBrainstorm(i.IdeaID));$('addCommentBtn')?.addEventListener('click',()=>addComment(i.IdeaID));$('saveRatingBtn')?.addEventListener('click',()=>saveRating(i.IdeaID));$('sendForReviewBtn')?.addEventListener('click',()=>sendForReview(i.IdeaID));qsa('[data-review-decision]',els.ideaDetailRoot).forEach(b=>b.addEventListener('click',()=>reviewDecision(i.IdeaID,b.dataset.reviewDecision)));$('movePlanningBtn')?.addEventListener('click',()=>moveToPlanning(i.IdeaID));$('startExecutionBtn')?.addEventListener('click',()=>startExecution(i.IdeaID));$('completeIdeaBtn')?.addEventListener('click',()=>completeIdea(i.IdeaID));$('addExperimentBtn')?.addEventListener('click',()=>addExperiment(i.IdeaID));$('savePlanBtn')?.addEventListener('click',()=>savePlan(i.IdeaID));$('addTaskBtn')?.addEventListener('click',()=>addTask(i.IdeaID));qsa('[data-task-status]',els.ideaDetailRoot).forEach(s=>s.addEventListener('change',()=>updateTaskStatus(i.IdeaID,s.dataset.taskStatus,s.value)));$('attachMediaBtn')?.addEventListener('click',()=>$('attachmentInput')?.click());$('attachmentInput')?.addEventListener('change',e=>uploadAttachments(i.IdeaID,e.target.files));qsa('[data-preview-attachment]',els.ideaDetailRoot).forEach(c=>c.addEventListener('click',()=>previewAttachment(c.dataset.previewAttachment,c.dataset.driveUrl)));if(state.currentTab==='media')hydrateMediaThumbnails();}
  async function reloadCurrentIdea'''
s, n = after_pat.subn(after_new, s, count=1)
if n != 1:
    raise SystemExit('afterDetailRender missing')

workflow_insert = '''  async function sendForReview(ideaId){const other=otherMember();if(!other){toast('Reviewer unavailable','A second active member is required.','error');return;}if(!ratingFor(ideaId,state.user.userId)){toast('Rate your idea first','Save your self-rating before sending it for review.','error');return;}const b=$('sendForReviewBtn');busy(b,true,'Sending…');try{await api('updateIdea',{ideaId,coOwnerUserId:other.userId,status:'Awaiting Review'});await refresh(false);await reloadCurrentIdea('rating');toast('Sent for review',`${other.displayName||other.fullName} can now review the idea.`);}catch(e){toast('Could not send for review',e.message,'error');}finally{busy(b,false);}}
  async function reviewDecision(ideaId,decision){const mine=ratingFor(ideaId,state.user.userId);if(!mine){toast('Rate the idea first','Save your rating before choosing a decision.','error');return;}try{await insights('saveReviewDecision',{ideaId,decision});if(decision==='Park'){await api('archiveIdea',{ideaId});els.detailDialog.close();await refresh();toast('Idea parked');navigate('ideas');return;}await api('updateIdea',{ideaId,status:decision==='Proceed'?'Approved':'Needs Work'});await refresh(false);await reloadCurrentIdea('rating');toast(decision==='Proceed'?'Idea approved':'Sent back for changes');}catch(e){toast('Could not save review',e.message,'error');}}
  async function moveToPlanning(ideaId){const b=$('movePlanningBtn');busy(b,true,'Moving…');try{await api('updateIdea',{ideaId,stage:'Planning',status:'Active'});await refresh(false);await reloadCurrentIdea('planning');toast('Moved to Planning');}catch(e){toast('Could not move idea',e.message,'error');}finally{busy(b,false);}}
  async function startExecution(ideaId){const b=$('startExecutionBtn');busy(b,true,'Starting…');try{await api('updateIdea',{ideaId,stage:'Execution',status:'Active'});await refresh(false);await reloadCurrentIdea('execution');toast('Execution started');}catch(e){toast('Could not start execution',e.message,'error');}finally{busy(b,false);}}
  async function completeIdea(ideaId){const b=$('completeIdeaBtn');busy(b,true,'Completing…');try{await api('updateIdea',{ideaId,status:'Completed'});await refresh(false);await reloadCurrentIdea('execution');toast('Idea completed');}catch(e){toast('Could not complete idea',e.message,'error');}finally{busy(b,false);}}
'''
marker = "  async function addExperiment(ideaId){"
if marker not in s:
    raise SystemExit('workflow insertion marker missing')
s = s.replace(marker, workflow_insert + marker, 1)

s = s.replace("await refresh(false);await reloadCurrentIdea('execution');toast('Task added');", "await refresh(false);await reloadCurrentIdea(state.currentTab);toast('Responsibility added');", 1)
s = s.replace("await refresh(false);await reloadCurrentIdea('execution');}catch(e){toast('Could not update task'", "await refresh(false);await reloadCurrentIdea(state.currentTab);}catch(e){toast('Could not update task'", 1)

p.write_text(s, encoding='utf-8')

# ---------- styles.css ----------
p = Path('styles.css')
s = p.read_text(encoding='utf-8')

# Replace the warm creative-studio palette with cooler slate/blue surfaces.
repls = {
    '--bg:#f4f0e9;--surface:#fffdfa;--soft:#eee9e1;--muted:#e6dfd6;--line:rgba(50,45,39,.10);': '--bg:#edf3f9;--surface:#f9fbff;--soft:#e7eef7;--muted:#dce6f1;--line:rgba(38,55,78,.10);',
    '--stage-plan:#b77a27;--stage-plan-soft:#fff4df;': '--stage-plan:#3f7f9b;--stage-plan-soft:#eaf6fb;',
    '#fffdf9': '#fbfdff', '#fffdfa': '#f9fbff', '#f4f0e9': '#edf3f9', '#f1ede6': '#e8eff7',
    'rgba(50,45,39': 'rgba(38,55,78', 'rgba(45,40,34': 'rgba(38,55,78', 'rgba(45,39,31': 'rgba(38,55,78',
    'rgba(45,38,30': 'rgba(38,55,78', 'rgba(55,46,37': 'rgba(38,55,78'
}
for a,b in repls.items(): s = s.replace(a,b)

cool = r'''

/* Cool lifecycle workspace */
:root{--primary:#526de8;--primary2:#3f58c8;--primarySoft:#edf1ff;--pink:#7669cf;--pinkSoft:#f0edff;--green:#3b7d75;--greenSoft:#e8f5f3;--amber:#4e7fa5;--amberSoft:#eaf4fb}
body{background:radial-gradient(circle at 52% -18%,#fbfdff 0,transparent 40%),linear-gradient(180deg,#edf3f9,#e9f0f7 72%,#edf3f9)}
.sidebar{background:rgba(249,251,255,.94)}
.profile-chip,.panel,.analytics-card,.studio-profile-card{background:rgba(249,251,255,.78)}
.idea-review-board{grid-template-columns:repeat(4,minmax(245px,1fr))}
.lifecycle-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
.status-surface-Draft{--stage-card:#eef3f9;--stage-color:#697a90}
.status-surface-Awaiting-review{--stage-card:#eaf1ff;--stage-color:#4f6fba}
.status-surface-Needs-work{--stage-card:#f0edff;--stage-color:#7465ba}
.status-surface-Approved{--stage-card:#e8f5f3;--stage-color:#397a70}
.status-surface-Completed{--stage-card:#e8f5f3;--stage-color:#397a70}
.board-status-Draft{background:rgba(238,243,249,.58)}.board-status-Awaiting-review{background:rgba(234,241,255,.55)}.board-status-Needs-work{background:rgba(240,237,255,.55)}.board-status-Approved{background:rgba(232,245,243,.60)}
.workflow-panel{margin-top:18px;padding:18px;border:1px solid rgba(82,109,232,.12);border-radius:18px;display:flex;align-items:center;justify-content:space-between;gap:18px;background:linear-gradient(135deg,rgba(237,241,255,.92),rgba(249,251,255,.95))}.workflow-panel h3{margin:2px 0 5px;font:800 17px/1.2 var(--display)}.workflow-panel p{margin:0;max-width:650px;color:var(--sub);font-size:11px}.workflow-panel.approved{background:linear-gradient(135deg,#e8f5f3,#f7fcfb)}.workflow-panel.waiting{background:linear-gradient(135deg,#eaf1ff,#f8fbff)}.workflow-actions{display:flex;gap:8px;flex-wrap:wrap}.eyebrow{color:var(--faint);font-size:9px;font-weight:900;letter-spacing:.12em;text-transform:uppercase}
.rating-form{background:#e8eff7}
.responsibility-section{margin-top:22px}.planning-task-list{display:grid;gap:8px;margin-bottom:12px}.planning-task{padding:12px 14px;border-radius:14px;display:flex;align-items:center;justify-content:space-between;gap:12px;background:#eef3f9}.planning-task>div{display:grid;gap:3px}.planning-task strong{font-size:11px}.planning-task span,.quiet-copy{color:var(--faint);font-size:9px}.planning-task select{height:34px;border:1px solid var(--line);border-radius:9px;background:#f9fbff;padding:0 8px}.stage-action{margin-top:18px;display:flex;justify-content:flex-end}.completed-banner{margin-top:18px;padding:13px 15px;border-radius:14px;background:#e8f5f3;color:#397a70;font-weight:800;text-align:center}.task-card small{display:block;margin:6px 0;color:var(--faint);font-size:8px}
.work-toolbar{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:18px}.work-toolbar h2{margin:3px 0 0;font:800 clamp(27px,3vw,38px)/1 var(--display);letter-spacing:-.045em}.work-root{display:grid;gap:18px}.work-loading{padding:30px;color:var(--faint);text-align:center}.work-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.work-summary>div{padding:16px 18px;border-radius:18px;background:rgba(249,251,255,.76);box-shadow:0 10px 28px rgba(38,55,78,.045)}.work-summary strong{display:block;font:800 25px/1 var(--display)}.work-summary span{display:block;margin-top:5px;color:var(--faint);font-size:9px}.work-group h3{margin:0 0 9px 4px;font:800 13px var(--display)}.work-list{display:grid;gap:8px}.work-item{padding:14px 15px;border-radius:17px;display:flex;align-items:center;justify-content:space-between;gap:18px;background:rgba(249,251,255,.82);box-shadow:0 8px 24px rgba(38,55,78,.045)}.work-item.review-work{background:linear-gradient(135deg,#eaf1ff,#f9fbff)}.work-item-main{min-width:0}.work-item-main strong{display:block;margin-top:3px;font-size:12px}.work-item-main p{margin:3px 0 0;color:var(--sub);font-size:9px}.work-type{color:var(--primary);font-size:8px;font-weight:900;letter-spacing:.1em;text-transform:uppercase}.work-item-meta{display:flex;align-items:center;justify-content:flex-end;gap:7px;flex-wrap:wrap}.work-item-meta>span:first-child{color:var(--faint);font-size:9px}
.analytics-hero{background:radial-gradient(circle at 88% -30%,rgba(82,109,232,.42),transparent 40%),linear-gradient(135deg,#172033,#202a40)}
.detail-hero{background:linear-gradient(145deg,#f9fbff,#eaf1f8)}.detail-tabs,.detail-actions{background:rgba(249,251,255,.94)}.info-card{background:rgba(232,239,247,.72)}.inline-form,.note-card,.comment-card,.experiment-card,.task-card{background:#e8eff7}
.avatar-option{background:#e8eff7}.avatar-option:hover{background:#f9fbff}.data-table tbody tr:hover{background:#eaf1f8}
@media(max-width:1050px){.idea-review-board{grid-template-columns:repeat(4,minmax(230px,1fr));overflow-x:auto}.work-item{align-items:flex-start;flex-direction:column}.work-item-meta{justify-content:flex-start}}
@media(max-width:650px){.work-toolbar{display:block}.work-toggle{margin-top:14px}.work-summary{grid-template-columns:repeat(3,1fr)}.workflow-panel{align-items:flex-start;flex-direction:column}.idea-review-board{grid-template-columns:repeat(4,minmax(260px,1fr))}}
'''
if '/* Cool lifecycle workspace */' not in s:
    s += cool
p.write_text(s, encoding='utf-8')
