(() => {
  'use strict';
  const API_URL = new URL('api/index.php', document.baseURI);
  const CLIENT_KEY = 'st.community.client.v1';
  const state = { items: [], counts: {}, loading: false, queryTimer: 0 };
  const byId = id => document.getElementById(id);
  const LABELS = {
    type: { idea: 'Idea', improvement: 'Mejora', bug: 'Fallo', content: 'Contenido' },
    status: { pending: 'Pendiente', in_progress: 'En curso', done: 'Terminado', archived: 'Archivado' },
    priority: { normal: 'Normal', high: 'Alta', urgent: 'Urgente' },
    colors: { pending: '#ffe438', in_progress: '#27e8ff', done: '#69ff91', archived: '#8792a4' },
  };

  function clientToken() {
    try {
      let token = localStorage.getItem(CLIENT_KEY);
      if (!token) { token = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`; localStorage.setItem(CLIENT_KEY, token); }
      return token;
    } catch (_) { return 'private-backlog'; }
  }
  function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, character => ({ '&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;' }[character])); }
  function formatDate(value) { if (!value) return '—'; return new Date(value.replace(' ', 'T')).toLocaleString('es-ES', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' }); }
  function setStatus(message, error = false) { byId('backlogStatus').textContent = message; byId('backlogStatus').classList.toggle('is-error', error); }
  function showGate(message = '') { document.body.classList.remove('access-checking'); byId('backlogApp').hidden = true; byId('backlogPinGate').hidden = false; byId('backlogPinError').textContent = message; setTimeout(() => byId('backlogPin').focus(), 40); }
  function enterApp() { document.body.classList.remove('access-checking'); byId('backlogPinGate').hidden = true; byId('backlogApp').hidden = false; loadItems(); }
  async function request(action, options = {}) {
    const url = new URL(API_URL); url.searchParams.set('action', action);
    Object.entries(options.query || {}).forEach(([key, value]) => { if (value !== '' && value !== undefined) url.searchParams.set(key, value); });
    const config = { cache:'no-store', credentials:'same-origin', headers:{ 'X-ST-Client':clientToken() } };
    if (options.body) { config.method = 'POST'; config.headers['Content-Type'] = 'application/json'; config.body = JSON.stringify({ ...options.body, client_token:clientToken() }); }
    const response = await fetch(url, config); const data = await response.json().catch(() => null);
    if (response.status === 401) { showGate('La sesión privada ha caducado.'); throw new Error('locked'); }
    if (!response.ok || !data?.ok) throw new Error(data?.error || 'request_failed');
    return data;
  }
  async function initializeAccess() {
    try { const data = await request('electroia-access'); if (data.required && !data.unlocked) showGate(); else enterApp(); }
    catch (error) { if (error.message !== 'locked') showGate('No se ha podido comprobar el acceso. Inténtalo de nuevo.'); }
  }
  function renderSummary() {
    const rows = [['Pendientes',state.counts.pending,'#ffe438'],['En curso',state.counts.in_progress,'#27e8ff'],['Terminadas',state.counts.done,'#69ff91']];
    byId('backlogSummary').innerHTML = rows.map(([label,value,color]) => `<article style="--accent:${color}"><strong>${Number(value || 0).toLocaleString('es-ES')}</strong><span>${label}</span></article>`).join('');
  }
  function populateAreas() {
    const select = byId('backlogAreaFilter'); const current = select.value;
    const areas = [...new Set(state.items.map(item => item.area).filter(Boolean))].sort((a,b) => a.localeCompare(b,'es'));
    select.innerHTML = '<option value="">Todas</option>' + areas.map(area => `<option value="${escapeHtml(area)}">${escapeHtml(area)}</option>`).join('');
    if (areas.includes(current)) select.value = current;
  }
  function renderItems() {
    const list = byId('backlogList');
    if (!state.items.length) { list.innerHTML = '<div class="backlog-empty"><strong>No hay coincidencias.</strong>Anota una idea o cambia los filtros.</div>'; return; }
    list.innerHTML = state.items.map(item => {
      const color = LABELS.colors[item.status] || '#8792a4';
      const next = item.status === 'pending' ? ['in_progress','Empezar'] : item.status === 'in_progress' ? ['done','Terminar'] : item.status === 'done' ? ['pending','Reabrir'] : ['pending','Recuperar'];
      return `<article class="backlog-item" style="--item-color:${color}" data-id="${Number(item.id)}">
        <div class="backlog-item-main"><div class="backlog-item-head"><span class="backlog-tag" style="--tag-color:${color}">${escapeHtml(LABELS.status[item.status])}</span><span class="backlog-tag" style="--tag-color:#ff8a24">${escapeHtml(LABELS.priority[item.priority])}</span><span class="backlog-tag" style="--tag-color:#ff4bb2">${escapeHtml(LABELS.type[item.item_type])}</span><span class="backlog-tag" style="--tag-color:#9ea8ff">${escapeHtml(item.area)}</span></div>
        <h2>${escapeHtml(item.title)}</h2>${item.details ? `<p>${escapeHtml(item.details)}</p>` : ''}<div class="backlog-meta"><span>#${Number(item.id)}</span><span>${escapeHtml(item.author_alias)}</span><span>Actualizado ${formatDate(item.updated_at)}</span></div></div>
        <div class="backlog-actions"><button type="button" data-action="advance" data-next="${next[0]}">${next[1]}</button><button type="button" data-action="edit">Editar</button><button type="button" data-action="archive">${item.status === 'archived' ? 'Recuperar' : 'Archivar'}</button></div></article>`;
    }).join('');
  }
  async function loadItems() {
    if (state.loading) return; state.loading = true; setStatus('Actualizando la bitácora…');
    try {
      const data = await request('private-backlog', { query:{ status:byId('backlogStatusFilter').value, area:byId('backlogAreaFilter').value, q:byId('backlogSearch').value.trim() } });
      state.items = data.items || []; state.counts = data.counts || {}; renderSummary(); populateAreas(); renderItems(); setStatus(`${state.items.length} anotaciones visibles · guardado compartido y privado`);
    } catch (error) { if (error.message !== 'locked') setStatus('No se ha podido cargar la bitácora. Vuelve a intentarlo.', true); }
    finally { state.loading = false; }
  }
  function openDialog(item = null) {
    byId('backlogDialogTitle').textContent = item ? 'Editar anotación' : 'Nueva idea'; byId('backlogId').value = item?.id || ''; byId('backlogTitle').value = item?.title || ''; byId('backlogType').value = item?.item_type || 'idea'; byId('backlogArea').value = item?.area || ''; byId('backlogPriority').value = item?.priority || 'normal'; byId('backlogItemStatus').value = item?.status || 'pending'; byId('backlogDetails').value = item?.details || ''; byId('backlogStatusField').hidden = !item; byId('backlogFormError').textContent = ''; byId('backlogDialog').showModal(); setTimeout(() => byId('backlogTitle').focus(), 40);
  }
  function formBody() { return { id:byId('backlogId').value || undefined, title:byId('backlogTitle').value.trim(), item_type:byId('backlogType').value, area:byId('backlogArea').value.trim(), priority:byId('backlogPriority').value, status:byId('backlogItemStatus').value, details:byId('backlogDetails').value.trim(), author_alias:'Administrador' }; }
  async function saveUpdate(item, status) { await request('private-backlog-update', { body:{ ...item, status } }); await loadItems(); }
  async function exportJson() {
    try {
      setStatus('Preparando una copia completa…');
      const data = await request('private-backlog', { query:{ status:'all' } });
      const payload = { exported_at:new Date().toISOString(), purpose:'Bitácora privada de Super Técnico para próximas sesiones de trabajo', counts:data.counts || {}, items:data.items || [] };
      const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'})); link.download = `super-tecnico-pendientes-${new Date().toISOString().slice(0,10)}.json`; link.click(); setTimeout(() => URL.revokeObjectURL(link.href),1000);
      setStatus(`${payload.items.length} anotaciones incluidas en la copia completa`);
    } catch (error) {
      if (error.message !== 'locked') setStatus('No se ha podido exportar la bitácora.', true);
    }
  }
  byId('backlogPinForm').addEventListener('submit', async event => { event.preventDefault(); const button = event.currentTarget.querySelector('button'); button.disabled = true; byId('backlogPinError').textContent = ''; try { const data = await request('electroia-unlock',{body:{pin:byId('backlogPin').value.trim()}}); if (!data.unlocked) throw new Error('invalid'); byId('backlogPin').value=''; enterApp(); } catch (error) { if (error.message !== 'locked') showGate('PIN incorrecto o acceso no disponible.'); } finally { button.disabled=false; } });
  byId('backlogNew').addEventListener('click',()=>openDialog()); byId('backlogExport').addEventListener('click',exportJson); byId('backlogClose').addEventListener('click',()=>byId('backlogDialog').close()); byId('backlogCancel').addEventListener('click',()=>byId('backlogDialog').close());
  byId('backlogForm').addEventListener('submit', async event => { event.preventDefault(); const body=formBody(); const button=byId('backlogSave'); button.disabled=true; byId('backlogFormError').textContent=''; try { await request(body.id ? 'private-backlog-update':'private-backlog',{body}); byId('backlogDialog').close(); await loadItems(); } catch (_) { byId('backlogFormError').textContent='No se ha podido guardar. Comprueba el título y el área.'; } finally { button.disabled=false; } });
  byId('backlogList').addEventListener('click', async event => { const button=event.target.closest('button[data-action]'); if(!button)return; const item=state.items.find(row=>Number(row.id)===Number(button.closest('[data-id]').dataset.id)); if(!item)return; button.disabled=true; try { if(button.dataset.action==='edit') openDialog(item); else if(button.dataset.action==='advance') await saveUpdate(item,button.dataset.next); else await saveUpdate(item,item.status==='archived'?'pending':'archived'); } catch (_) { setStatus('No se ha podido actualizar la anotación.',true); } finally { button.disabled=false; } });
  byId('backlogStatusFilter').addEventListener('change',loadItems); byId('backlogAreaFilter').addEventListener('change',loadItems); byId('backlogSearch').addEventListener('input',()=>{ clearTimeout(state.queryTimer); state.queryTimer=setTimeout(loadItems,250); });
  initializeAccess();
})();
