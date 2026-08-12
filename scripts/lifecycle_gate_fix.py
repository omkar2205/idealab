from pathlib import Path

p=Path('app.js')
s=p.read_text(encoding='utf-8')
old="  function detailTabs(){return[['overview','Overview'],['brainstorm','Discussion'],['rating','Rating'],['validation','Validation'],['planning','Plan'],['execution','Execute'],['media','Media']];}"
new="  function detailTabs(){const i=state.currentIdea||{},tabs=[['overview','Overview'],['brainstorm','Discussion'],['rating','Rating']];if(['Planning','Execution'].includes(i.Stage))tabs.push(['validation','Validation'],['planning','Plan']);if(i.Stage==='Execution')tabs.push(['execution','Execute']);tabs.push(['media','Media']);return tabs;}"
if old not in s: raise SystemExit('detailTabs marker missing')
s=s.replace(old,new,1)
s=s.replace('<h3 class="section-title">Brainstorm notes</h3>','<h3 class="section-title">Notes</h3>',1)
p.write_text(s,encoding='utf-8')
