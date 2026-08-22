(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
  const fold = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  let csrf = '', kind = 'connectors', currentItems = [], connectorRecords = [];

  function showAdmin() { $('#loginPanel').hidden = true; $('#adminPanel').hidden = false; $('#logoutButton').hidden = false; }
  async function session() { try { const data = await ST_COMMUNITY_API.request('admin-session'); csrf = data.csrf; showAdmin(); await load(); } catch { $('#loginPanel').hidden = false; } }

  function statusOptions(itemKind, current) {
    const values = itemKind === 'proposal' ? ['pending','study','accepted','planned','development','applied','duplicate','discarded'] : ['pending','published','rejected'];
    return values.map(value => `<option value="${value}" ${value === current ? 'selected' : ''}>${value}</option>`).join('');
  }
  function proposalCard(item) { return `<article class="admin-card"><div><div class="admin-meta"><span>${esc(item.type)}</span><span>${esc(item.area)}</span><span>${esc(item.nickname)}</span><span>${esc(item.created_at)}</span><span>${Number(item.supports_count || 0)} apoyos</span></div><h2>${esc(item.title)}</h2><p>${esc(item.description)}</p>${item.proposed_change ? `<p><strong>Cambio:</strong> ${esc(item.proposed_change)}</p>` : ''}</div><div class="admin-controls"><label>Estado<select data-status>${statusOptions('proposal', item.status)}</select></label><label class="check"><input type="checkbox" data-public ${Number(item.is_public) === 1 ? 'checked' : ''}> Visible públicamente</label><label>Respuesta oficial<textarea data-note>${esc(item.official_note || '')}</textarea></label><button type="button" data-save data-kind="proposal" data-id="${item.id}">Guardar revisión</button></div></article>`; }
  function faultCard(item, itemKind) { const title = itemKind === 'fault' ? item.board_reference : `Solución para ${item.board_reference}`; const body = itemKind === 'fault' ? item.symptom : item.solution; return `<article class="admin-card"><div><div class="admin-meta"><span>${esc(item.nickname)}</span><span>${esc(item.created_at)}</span>${item.brand ? `<span>${esc(item.brand)}</span>` : ''}</div><h2>${esc(title)}</h2><p>${esc(body)}</p>${item.solutions ? `<pre>${esc(item.solutions)}</pre>` : ''}</div><div class="admin-controls"><label>Estado<select data-status>${statusOptions(itemKind, item.status)}</select></label><button type="button" data-save data-kind="${itemKind}" data-id="${item.id}">Guardar revisión</button></div></article>`; }

  function effectiveReview(record) {
    return record.admin_review || {review_status:record.review.status, confidence:record.review.confidence, reviewer_alias:'Administrador', evidence_source_id:'', evidence_locator:'', notes:'', contacts_checked:0, orientation_checked:0, variants_checked:0};
  }
  function connectorCard(record) {
    const review = effectiveReview(record), checked = key => Number(review[key]) === 1 ? 'checked' : '';
    const sourceOptions = ['', ...(record.source_ids || [])].map(source => `<option value="${esc(source)}" ${source === review.evidence_source_id ? 'selected' : ''}>${esc(source || 'Seleccionar fuente')}</option>`).join('');
    const rows = (record.contacts || []).map(contact => `<tr><th>${esc(contact.id)}</th><td><strong>${esc(contact.signal)}</strong><small>${esc(contact.description)}</small></td></tr>`).join('');
    return `<article class="connector-review-card" data-connector-id="${esc(record.id)}"><details><summary><span><small>${esc(record.category)} · ${record.contacts.length} contactos</small><strong>${esc(record.canonical_name)}</strong><em>${esc(record.id)}</em></span><span class="status-pill status-${esc(review.review_status)}">${esc(review.review_status)}</span></summary><div class="connector-review-grid"><section class="connector-evidence"><h3>Datos a comprobar</h3><p><strong>Vista:</strong> ${esc(record.view.perspective)} · ${esc(record.view.orientation_note)}</p><details><summary>Contactos y señales</summary><div class="contact-scroll"><table><tbody>${rows}</tbody></table></div></details><details><summary>Variantes y seguridad</summary><ul>${(record.variants || []).map(item => `<li>${esc(item)}</li>`).join('')}</ul><ul class="warning-list">${(record.safety_notes || []).map(item => `<li>${esc(item)}</li>`).join('')}</ul></details></section><form class="connector-review-form"><label>Estado<select data-review-status><option value="pending_review" ${review.review_status === 'pending_review' ? 'selected' : ''}>Pendiente</option><option value="source_identified" ${review.review_status === 'source_identified' ? 'selected' : ''}>Fuente identificada</option><option value="reviewed" ${review.review_status === 'reviewed' ? 'selected' : ''}>Revisado</option><option value="rejected" ${review.review_status === 'rejected' ? 'selected' : ''}>Descartado</option></select></label><div class="two-fields"><label>Confianza<input data-confidence type="number" min="0" max="1" step="0.01" value="${Number(review.confidence || 0).toFixed(2)}"></label><label>Revisor<input data-reviewer maxlength="40" value="${esc(review.reviewer_alias || 'Administrador')}"></label></div><label>Fuente exacta<select data-source>${sourceOptions}</select></label><label>Localizador de evidencia<input data-locator maxlength="180" value="${esc(review.evidence_locator || '')}" placeholder="Edición, tabla, cláusula o página"></label><div class="review-checks"><label><input data-contacts type="checkbox" ${checked('contacts_checked')}> Contactos</label><label><input data-orientation type="checkbox" ${checked('orientation_checked')}> Orientación</label><label><input data-variants type="checkbox" ${checked('variants_checked')}> Variantes</label></div><label>Notas<textarea data-review-notes maxlength="3000">${esc(review.notes || '')}</textarea></label><div class="form-actions"><button type="submit">Guardar revisión</button><button type="button" class="secondary" data-history>Historial</button></div><p data-card-message role="status"></p><div data-history-list class="history-list"></div></form></div></details></article>`;
  }
  function importCard(item) {
    const options = ['uploaded','needs_extractor','extracted','ready_for_review','merged','rejected'].map(status => `<option value="${status}" ${status === item.import_status ? 'selected' : ''}>${status}</option>`).join('');
    return `<article class="import-card" data-import-id="${item.id}"><div><span class="status-pill status-${esc(item.import_status)}">${esc(item.import_status)}</span><h3>${esc(item.original_filename)}</h3><p>${esc(item.summary || 'Sin descripción')}</p><small>${Math.max(1, Math.round(Number(item.file_size) / 1024))} KB · ${esc(item.media_type)} · ${esc(item.created_at)}</small></div><form><label>Flujo<select data-import-status>${options}</select></label><label>Resumen<textarea data-import-summary maxlength="500">${esc(item.summary || '')}</textarea></label><button type="submit">Actualizar</button><p data-card-message role="status"></p></form></article>`;
  }

  function updateConnectorSummary(records) {
    const counts = {pending_review:0, source_identified:0, reviewed:0, rejected:0};
    records.forEach(record => { const status = effectiveReview(record).review_status; counts[status] = (counts[status] || 0) + 1; });
    $('#connectorReviewSummary').innerHTML = `<span>${records.length} fichas</span><span>${counts.reviewed} revisadas</span><span>${counts.source_identified} con fuente</span><span>${counts.pending_review} pendientes</span>`;
  }
  function renderConnectorFilter() {
    const query = fold($('#connectorReviewSearch').value.trim()), status = $('#connectorReviewStatus').value;
    const filtered = connectorRecords.filter(record => (!query || fold([record.id, record.canonical_name, record.category, record.interface, ...(record.aliases || []), ...(record.search_terms || [])].join(' ')).includes(query)) && (!status || effectiveReview(record).review_status === status));
    currentItems = filtered; updateConnectorSummary(connectorRecords); $('#adminMessage').textContent = `${filtered.length} de ${connectorRecords.length} conectores`; $('#adminList').innerHTML = filtered.map(connectorCard).join('') || '<p>No hay conectores con esos filtros.</p>';
  }
  async function loadConnectors() { const data = await ST_COMMUNITY_API.request('admin-connector-catalog'); connectorRecords = data.records; renderConnectorFilter(); }
  async function loadImports() { const data = await ST_COMMUNITY_API.request('admin-connector-imports'); currentItems = data.items; $('#adminMessage').textContent = `${data.items.length} lotes incorporados`; $('#adminList').innerHTML = data.items.map(importCard).join('') || '<p>Todavía no hay documentos en espera.</p>'; }
  async function loadCommunity() { const data = await ST_COMMUNITY_API.request('admin-list', {query:{kind}}); currentItems = data.items; $('#adminMessage').textContent = `${data.items.length} registros`; $('#adminList').innerHTML = data.items.map(item => kind === 'proposals' ? proposalCard(item) : faultCard(item, kind === 'faults' ? 'fault' : 'solution')).join('') || '<p>No hay registros.</p>'; }
  async function load() {
    $('#adminMessage').textContent = 'Cargando…'; $('#connectorToolbar').hidden = kind !== 'connectors'; $('#importWorkspace').hidden = kind !== 'connector-imports';
    try { if (kind === 'connectors') await loadConnectors(); else if (kind === 'connector-imports') await loadImports(); else await loadCommunity(); }
    catch (error) { console.error(error); currentItems = []; $('#adminMessage').textContent = 'No se pudieron cargar los datos.'; $('#adminList').innerHTML = ''; }
  }

  function download(format) {
    if (!currentItems.length) return;
    const date = new Date().toISOString().slice(0, 10); let content, mime, extension;
    if (format === 'csv') { const flattened = currentItems.map(item => kind === 'connectors' ? {id:item.id, name:item.canonical_name, category:item.category, review_status:effectiveReview(item).review_status, contacts:item.contacts.length} : item); const keys = [...new Set(flattened.flatMap(Object.keys))]; const quote = value => `"${String(value ?? '').replaceAll('"', '""')}"`; content = '\ufeff' + [keys.map(quote).join(';'), ...flattened.map(item => keys.map(key => quote(item[key])).join(';'))].join('\r\n'); mime = 'text/csv;charset=utf-8'; extension = 'csv'; }
    else { content = JSON.stringify({kind, exported_at:new Date().toISOString(), items:currentItems}, null, 2); mime = 'application/json;charset=utf-8'; extension = 'json'; }
    const url = URL.createObjectURL(new Blob([content], {type:mime})), link = document.createElement('a'); link.href = url; link.download = `replacor-${kind}-${date}.${extension}`; link.click(); URL.revokeObjectURL(url);
  }

  $('#loginForm').addEventListener('submit', async event => { event.preventDefault(); try { const data = await ST_COMMUNITY_API.request('admin-login', {body:{password:$('#adminPassword').value}}); csrf = data.csrf; showAdmin(); await load(); } catch { $('#loginMessage').textContent = 'Acceso incorrecto o servicio no disponible.'; } });
  document.querySelectorAll('[data-kind]').forEach(button => button.addEventListener('click', () => { kind = button.dataset.kind; document.querySelectorAll('.admin-tabs [data-kind]').forEach(item => item.classList.toggle('is-active', item === button)); load(); }));
  document.querySelectorAll('[data-export]').forEach(button => button.addEventListener('click', () => download(button.dataset.export)));
  $('#connectorReviewSearch').addEventListener('input', renderConnectorFilter); $('#connectorReviewStatus').addEventListener('change', renderConnectorFilter);

  $('#adminList').addEventListener('submit', async event => {
    const connectorForm = event.target.closest('.connector-review-form'), importForm = event.target.closest('.import-card form'); if (!connectorForm && !importForm) return; event.preventDefault(); const message = event.target.querySelector('[data-card-message]');
    try {
      if (connectorForm) { const card = connectorForm.closest('[data-connector-id]'); const body = {connector_id:card.dataset.connectorId, review_status:connectorForm.querySelector('[data-review-status]').value, confidence:Number(connectorForm.querySelector('[data-confidence]').value), reviewer_alias:connectorForm.querySelector('[data-reviewer]').value.trim(), evidence_source_id:connectorForm.querySelector('[data-source]').value, evidence_locator:connectorForm.querySelector('[data-locator]').value.trim(), contacts_checked:connectorForm.querySelector('[data-contacts]').checked, orientation_checked:connectorForm.querySelector('[data-orientation]').checked, variants_checked:connectorForm.querySelector('[data-variants]').checked, notes:connectorForm.querySelector('[data-review-notes]').value.trim()}; await ST_COMMUNITY_API.request('admin-connector-review', {body, headers:{'X-CSRF-Token':csrf}}); message.textContent = 'Revisión guardada ✓'; await loadConnectors(); }
      else { const card = importForm.closest('[data-import-id]'); await ST_COMMUNITY_API.request('admin-connector-import-update', {body:{id:Number(card.dataset.importId), import_status:importForm.querySelector('[data-import-status]').value, summary:importForm.querySelector('[data-import-summary]').value.trim()}, headers:{'X-CSRF-Token':csrf}}); message.textContent = 'Lote actualizado ✓'; await loadImports(); }
    } catch (error) { message.textContent = error.code === 'review_evidence_incomplete' ? 'Para marcar revisado faltan fuente, localizador y las tres comprobaciones.' : 'No se pudo guardar.'; }
  });

  $('#adminList').addEventListener('click', async event => {
    const history = event.target.closest('[data-history]');
    if (history) { const card = history.closest('[data-connector-id]'), target = card.querySelector('[data-history-list]'); try { const data = await ST_COMMUNITY_API.request('admin-connector-history', {query:{connector_id:card.dataset.connectorId}}); target.innerHTML = data.items.length ? data.items.map(item => `<p><strong>${esc(item.review_status)}</strong> · ${esc(item.reviewer_alias)} · ${esc(item.created_at)}<br><small>${esc(item.evidence_source_id || '')} ${esc(item.evidence_locator || '')}</small></p>`).join('') : '<p>Sin revisiones anteriores.</p>'; } catch { target.textContent = 'No se pudo abrir el historial.'; } return; }
    const button = event.target.closest('[data-save]'); if (!button) return; const card = button.closest('.admin-card'), body = {kind:button.dataset.kind, id:Number(button.dataset.id), status:card.querySelector('[data-status]').value}; if (body.kind === 'proposal') { body.is_public = card.querySelector('[data-public]').checked; body.official_note = card.querySelector('[data-note]').value.trim(); } button.disabled = true; try { await ST_COMMUNITY_API.request('admin-update', {body, headers:{'X-CSRF-Token':csrf}}); button.textContent = 'Guardado ✓'; setTimeout(load, 500); } catch (error) { console.error(error); button.disabled = false; button.textContent = 'Error al guardar'; }
  });

  $('#connectorImportForm').addEventListener('submit', async event => {
    event.preventDefault(); const file = $('#connectorImportFile').files[0]; if (!file) return; const message = $('#connectorImportMessage'), form = new FormData(); form.append('document', file); form.append('summary', $('#connectorImportSummary').value.trim());
    if (/\.(json|csv|tsv|txt)$/i.test(file.name) && file.size <= 2 * 1024 * 1024) { const text = await file.text(); let preview = {format:file.name.split('.').pop().toLowerCase(), character_count:text.length}; if (/\.json$/i.test(file.name)) { try { const parsed = JSON.parse(text); preview = {format:'json', root_type:Array.isArray(parsed) ? 'array' : typeof parsed, candidate_count:Array.isArray(parsed) ? parsed.length : Array.isArray(parsed.records) ? parsed.records.length : 0}; } catch { preview.parse_warning = 'invalid_json'; } } form.append('extracted_json', JSON.stringify(preview)); }
    message.textContent = 'Guardando de forma privada…'; try { const data = await ST_COMMUNITY_API.upload('admin-connector-import', form, {headers:{'X-CSRF-Token':csrf}}); message.textContent = `Lote ${data.id} preparado ✓`; event.target.reset(); await loadImports(); } catch (error) { message.textContent = `No se pudo incorporar: ${error.code || 'error'}`; }
  });
  $('#logoutButton').addEventListener('click', async () => { try { await ST_COMMUNITY_API.request('admin-logout', {body:{}, headers:{'X-CSRF-Token':csrf}}); } finally { location.reload(); } });
  session();
})();
