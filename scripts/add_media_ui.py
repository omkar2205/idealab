from pathlib import Path

p = Path('app.js')
s = p.read_text()

old = '''  function iconClose(){return'<svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg>'}\n'''
new = '''  function iconClose(){return'<svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg>'}\n  function iconAttach(){return'<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/><path d="M4 19V5a2 2 0 0 1 2-2h8l6 6v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"/></svg>'}\n  function formatBytes(v){const n=Number(v||0);if(!n)return'';if(n<1024)return`${n} B`;if(n<1048576)return`${(n/1024).toFixed(n<10240?1:0)} KB`;return`${(n/1048576).toFixed(n<10485760?1:0)} MB`;}\n  function attachmentRow(a){const url=a.DriveURL||'#',meta=[a.MimeType,formatBytes(a.SizeBytes)].filter(Boolean).join(' · ');return`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 12px;border:1px solid var(--line);border-radius:10px;background:var(--surface)"><span style="min-width:0"><strong style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px">${esc(a.FileName||'Attachment')}</strong>${meta?`<small style="display:block;margin-top:2px;color:var(--faint)">${esc(meta)}</small>`:''}</span><span class="pill">Open</span></a>`;}\n  function fileToBase64(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result||''));r.onerror=()=>reject(new Error('Could not read the selected file.'));r.readAsDataURL(file);});}\n'''
if old not in s:
    raise SystemExit('icon insertion point not found')
s = s.replace(old, new, 1)

old = '''<section class="detail-section"><h3>Progress</h3><div style="display:flex;gap:8px;flex-wrap:wrap"><span class="pill">${tasks.length} tasks</span><span class="pill">${experiments.length} experiments</span><span class="pill">${attachments.length} attachments</span></div></section>'''
new = '''<section class="detail-section"><div style="display:flex;align-items:center;justify-content:space-between;gap:12px"><h3 style="margin:0">Media</h3><button id="attachMediaBtn" class="button button-secondary button-compact" type="button">${iconAttach()} Attach media</button></div><input id="attachmentInput" type="file" multiple hidden accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip">${attachments.length?`<div style="display:grid;gap:7px;margin-top:12px">${attachments.map(attachmentRow).join('')}</div>`:'<div class="detail-text" style="margin-top:10px">No attachments.</div>'}</section><section class="detail-section"><h3>Progress</h3><div style="display:flex;gap:8px;flex-wrap:wrap"><span class="pill">${tasks.length} tasks</span><span class="pill">${experiments.length} experiments</span></div></section>'''
if old not in s:
    raise SystemExit('detail media insertion point not found')
s = s.replace(old, new, 1)

old = '''one('[data-archive-idea]',els.ideaDetailRoot)?.addEventListener('click',()=>archiveIdea(i.IdeaID));$('addBrainstormBtn')?.addEventListener('click',()=>addBrainstorm(i.IdeaID));'''
new = '''one('[data-archive-idea]',els.ideaDetailRoot)?.addEventListener('click',()=>archiveIdea(i.IdeaID));$('addBrainstormBtn')?.addEventListener('click',()=>addBrainstorm(i.IdeaID));$('attachMediaBtn')?.addEventListener('click',()=>$('attachmentInput')?.click());$('attachmentInput')?.addEventListener('change',e=>uploadAttachments(i.IdeaID,e.target.files));'''
if old not in s:
    raise SystemExit('media listener insertion point not found')
s = s.replace(old, new, 1)

old = '''  async function addBrainstorm(ideaId){const input=$('brainstormInput'),btn=$('addBrainstormBtn');if(!input?.value.trim())return;busy(btn,true,'Adding…');try{await api('addBrainstorm',{ideaId,content:input.value.trim(),noteType:'Note'});els.detailDialog.close();await refresh();await openIdea(ideaId);toast('Thought added');}catch(e){toast('Could not add note',e.message,'error');busy(btn,false);}}\n'''
new = '''  async function addBrainstorm(ideaId){const input=$('brainstormInput'),btn=$('addBrainstormBtn');if(!input?.value.trim())return;busy(btn,true,'Adding…');try{await api('addBrainstorm',{ideaId,content:input.value.trim(),noteType:'Note'});els.detailDialog.close();await refresh();await openIdea(ideaId);toast('Thought added');}catch(e){toast('Could not add note',e.message,'error');busy(btn,false);}}\n  async function uploadAttachments(ideaId,fileList){const files=Array.from(fileList||[]);if(!files.length)return;const max=10*1024*1024,tooLarge=files.find(f=>f.size>max);if(tooLarge){toast('File too large','Maximum file size is 10 MB.','error');const input=$('attachmentInput');if(input)input.value='';return;}const btn=$('attachMediaBtn');busy(btn,true,'Uploading…');try{for(const file of files){const base64=await fileToBase64(file);await api('uploadAttachment',{ideaId,fileName:file.name,mimeType:file.type||'application/octet-stream',base64});}els.detailDialog.close();await refresh();await openIdea(ideaId);toast(files.length===1?'File attached':`${files.length} files attached`);}catch(e){toast('Upload failed',e.message,'error');busy(btn,false);}}\n'''
if old not in s:
    raise SystemExit('upload function insertion point not found')
s = s.replace(old, new, 1)

p.write_text(s)
