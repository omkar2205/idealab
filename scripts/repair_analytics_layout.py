from pathlib import Path
import re

# Patch Analytics rendering so empty/filtered states look intentional.
p = Path('app.js')
s = p.read_text(encoding='utf-8')
pat = re.compile(r"  function renderAnalytics\(\)\{.*?\n  function bindAnalytics\(\)", re.S)
replacement = r'''  function renderAnalytics(){
    const ideas=analyticsIdeas(),scores=ideas.map(i=>combinedScore(i.IdeaID)).filter(v=>v!=null),paired=ideas.filter(i=>ratingsForIdea(i.IdeaID).length>=2),gaps=paired.map(i=>({i,g:ratingGap(i.IdeaID)})).sort((a,b)=>b.g-a.g).slice(0,5),hasActive=state.ideas.length>0;
    const hero=`<div class="analytics-hero"><div class="analytics-hero-top"><div><span>Analytics</span><h2>Idea pipeline</h2></div>${analyticsFilterBar()}</div>${pipelineHTML(ideas)}<div class="analytics-hero-stats"><div><strong>${ideas.length}</strong><span>Ideas</span></div><div><strong>${scores.length}</strong><span>Rated</span></div><div><strong>${scores.length?avg(scores).toFixed(1):'—'}</strong><span>Average score</span></div><div><strong>${ideas.filter(i=>i.Stage==='Execution').length}</strong><span>Execution</span></div></div></div>`;
    const body=ideas.length?`<div class="analytics-grid"><section class="analytics-card"><h3>Top rated</h3>${topBars(ideas)}</section><section class="analytics-card"><h3>Score distribution</h3>${distributionHTML(ideas)}</section><section class="analytics-card"><h3>Rating comparison</h3>${scatterHTML(ideas)}</section><section class="analytics-card"><h3>Largest disagreements</h3>${gaps.length?`<div class="disagreement-list">${gaps.map(x=>`<div class="disagreement-item" data-open-idea="${esc(x.i.IdeaID)}"><strong>${esc(x.i.Title)}</strong><span class="score-badge">${x.g.toFixed(1)}</span></div>`).join('')}</div>`:'<p style="color:var(--faint);font-size:10px">No paired ratings.</p>'}</section><section class="analytics-card"><h3>Ideas created</h3>${timelineHTML(ideas)}</section><section class="analytics-card"><h3>Category performance</h3>${categoryBars(ideas)}</section><section class="analytics-card full"><h3>Ranked ideas</h3>${analyticsTable(ideas)}</section></div>`:`<section class="analytics-empty"><div class="analytics-empty-mark">${icon.bulb}</div><h3>${hasActive?'No ideas match these filters':'No active ideas yet'}</h3><p>${hasActive?'Change or clear the filters to bring ideas back into view.':'Add a new idea and it will appear in the pipeline as soon as it is saved.'}</p><button id="${hasActive?'analyticsResetFilters':'analyticsAddIdea'}" class="button button-primary">${hasActive?'Clear filters':'Add idea'}</button></section>`;
    wrap(hero+body);bindAnalytics();
    $('analyticsResetFilters')?.addEventListener('click',()=>{state.analyticsFilters={owner:'all',stage:'all',category:'all',score:'all',flow:'all'};renderAnalytics();});
    $('analyticsAddIdea')?.addEventListener('click',openQuickIdea);
  }
  function bindAnalytics()'''
s, n = pat.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('renderAnalytics block not found')
p.write_text(s, encoding='utf-8')

# Add final CSS overrides for the dark analytics hero and six-stage pipeline.
p = Path('styles.css')
s = p.read_text(encoding='utf-8')
marker = '/* Analytics layout repair */'
css = r'''

/* Analytics layout repair */
.analytics-hero-top{align-items:flex-start}
.analytics-hero .analytics-filters{margin:0;padding:0;border:0;background:transparent;box-shadow:none;border-radius:0;display:grid;grid-template-columns:repeat(2,minmax(132px,1fr)) auto;gap:8px;align-items:center;justify-content:stretch;width:min(100%,700px)}
.analytics-hero .analytics-filters select{width:100%;height:38px;padding:0 32px 0 11px;border:1px solid rgba(255,255,255,.16);border-radius:11px;background:rgba(255,255,255,.075);color:#fff;outline:0;backdrop-filter:blur(8px)}
.analytics-hero .analytics-filters select:hover,.analytics-hero .analytics-filters select:focus{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.28)}
.analytics-hero .analytics-actions{margin-left:0;display:flex;gap:7px;white-space:nowrap}
.analytics-hero .analytics-actions .button{height:38px;min-height:38px;background:rgba(255,255,255,.075);border-color:rgba(255,255,255,.16);color:#fff}
.analytics-hero .pipeline{grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;overflow:visible}
.analytics-hero .pipeline-step{min-width:0;min-height:88px;display:grid;place-items:center;align-content:center}
.analytics-empty{min-height:300px;margin-top:16px;padding:44px 24px;border:1px dashed rgba(84,104,140,.20);border-radius:22px;background:rgba(255,255,255,.55);display:grid;place-items:center;align-content:center;text-align:center;box-shadow:0 12px 34px rgba(39,58,89,.035)}
.analytics-empty-mark{width:52px;height:52px;margin-bottom:12px;border-radius:17px;display:grid;place-items:center;background:var(--primarySoft);color:var(--primary)}
.analytics-empty-mark svg{width:23px;height:23px}.analytics-empty h3{margin:0;font:800 20px/1.2 var(--display);letter-spacing:-.03em}.analytics-empty p{max-width:480px;margin:8px 0 18px;color:var(--sub);font-size:11px}
@media(max-width:1250px){.analytics-hero-top{display:block}.analytics-hero .analytics-filters{margin-top:18px;width:100%;max-width:none;grid-template-columns:repeat(4,minmax(120px,1fr))}.analytics-hero .analytics-actions{grid-column:1/-1}.analytics-hero .analytics-actions .button{flex:1}.analytics-hero .pipeline{grid-template-columns:repeat(6,minmax(130px,1fr));overflow-x:auto;padding-bottom:5px}}
@media(max-width:720px){.analytics-hero .analytics-filters{grid-template-columns:repeat(2,minmax(0,1fr))}.analytics-hero .analytics-actions{grid-column:1/-1}.analytics-hero .pipeline{grid-template-columns:repeat(6,128px);overflow-x:auto}.analytics-empty{min-height:250px;padding:34px 18px}}
'''
if marker not in s:
    s += css
p.write_text(s, encoding='utf-8')
