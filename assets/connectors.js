(() => {
  'use strict';
  const CATALOG_URL = 'data/connectors/catalog.json';
  const SOURCES_URL = 'data/connectors/sources.json';
  const categoryLabels = {network:'Red',usb:'USB',video:'Vídeo',audio:'Audio',serial_industrial:'Industrial',automotive:'Automoción',storage:'Almacenamiento',power:'Potencia'};
  const statusLabels = {reviewed:'Revisado',source_identified:'Fuente identificada',pending_review:'Pendiente'};
  const statusShort = {reviewed:'OK',source_identified:'FUENTE',pending_review:'REVISAR'};
  const accents = {network:'#00eaff',usb:'#54ff82',video:'#a66bff',audio:'#ff3fa7',serial_industrial:'#ffe438',automotive:'#ff7a00',storage:'#2693ff',power:'#ff5e66'};
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const normalize = value => String(value ?? '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase('es');
  let records = [];
  let sourceMap = new Map();
  let selectedId = '';

  const haystack = record => normalize([record.canonical_name,...(record.aliases||[]),record.interface,record.form_factor,...(record.search_terms||[]),...(record.contacts||[]).flatMap(contact=>[contact.id,contact.signal,contact.description])].join(' '));
  const sourcePdfUrl = record => `recursos/enciclopedia-conectores-pinouts-edicion-${record.source_pdf.edition}-origen.pdf#page=${record.source_pdf.pages[0]}`;

  function visibleRecords() {
    const query = normalize(document.getElementById('connectorQuery').value.trim());
    const category = document.getElementById('connectorCategory').value;
    const review = document.getElementById('connectorReview').value;
    return records.filter(record => (!query || haystack(record).includes(query)) && (!category || record.category === category) && (!review || record.review.status === review));
  }

  function renderResults({autoSelect=false}={}) {
    const list = document.getElementById('connectorResults');
    const visible = visibleRecords();
    document.getElementById('connectorResultCount').textContent = visible.length;
    if (!visible.length) {
      list.innerHTML = '<div class="connector-empty"><h3>Sin coincidencias</h3><p>Prueba otra escritura o propón esta referencia para incorporarla.</p></div>';
      return;
    }
    list.innerHTML = visible.map(record => `<button class="connector-result${record.id===selectedId?' is-active':''}" style="--accent:${accents[record.category]||'#00eaff'}" type="button" data-id="${esc(record.id)}"><strong>${esc(record.canonical_name)}</strong><small>${esc(categoryLabels[record.category]||record.category)} · ${esc(record.form_factor)}</small><em>${esc(statusShort[record.review.status]||record.review.status)}</em></button>`).join('');
    list.querySelectorAll('[data-id]').forEach(button => button.addEventListener('click', () => selectRecord(button.dataset.id, true)));
    if (autoSelect && visible.length === 1) selectRecord(visible[0].id, true);
  }

  function detailSources(record) {
    return record.source_ids.map(id => {
      const source = sourceMap.get(id);
      if (!source) return `<li>${esc(id)}</li>`;
      const title = esc(source.title);
      return `<li><a href="${esc(source.url)}" target="_blank" rel="noopener">${title}</a><br><small>${esc(source.publisher)} · ${esc(source.status)}</small></li>`;
    }).join('');
  }

  function selectRecord(id, scroll=false) {
    const record = records.find(item => item.id === id);
    if (!record) return;
    selectedId = id;
    renderResults();
    const contacts = record.contacts.map(contact => `<tr><td>${esc(contact.id)}</td><td>${esc(contact.signal)}</td><td>${esc(contact.description)}</td></tr>`).join('');
    const variants = (record.variants||[]).map(item=>`<li>${esc(item)}</li>`).join('') || '<li>Sin variantes documentadas en esta ficha.</li>';
    const safety = (record.safety_notes||[]).map(item=>`<li>${esc(item)}</li>`).join('') || '<li>Sin advertencias adicionales.</li>';
    const pages = record.source_pdf.pages.join(', ');
    document.getElementById('connectorDetail').innerHTML = `<article>
      <header class="connector-detail-head"><div><span class="connector-badge ${esc(record.review.status)}">${esc(statusLabels[record.review.status]||record.review.status)}</span><span class="connector-badge">${esc(categoryLabels[record.category]||record.category)}</span></div><h2>${esc(record.canonical_name)}</h2><p>${esc((record.aliases||[]).join(' · '))}</p></header>
      <div class="connector-orientation"><strong>Vista usada en esta ficha</strong><p>${esc(record.view.orientation_note)}</p><small>${esc(record.view.perspective)}${record.view.key_position?` · Referencia: ${esc(record.view.key_position)}`:''}</small></div>
      <div class="connector-quick-grid"><div><span>Interfaz</span><strong>${esc(record.interface)}</strong></div><div><span>Formato</span><strong>${esc(record.form_factor)}</strong></div><div><span>Contactos</span><strong>${record.contacts.length}</strong></div></div>
      <div class="connector-table-wrap"><table class="connector-table"><thead><tr><th>Contacto</th><th>Señal</th><th>Función</th></tr></thead><tbody>${contacts}</tbody></table></div>
      <details><summary>Variantes que pueden cambiar el resultado</summary><div><ul>${variants}</ul></div></details>
      <details><summary>Seguridad y errores habituales</summary><div><ul>${safety}</ul></div></details>
      <details><summary>Procedencia y trazabilidad</summary><div><p>Manual aportado: edición ${record.source_pdf.edition}, página${record.source_pdf.pages.length===1?'':'s'} ${esc(pages)}. <a href="${esc(sourcePdfUrl(record))}" target="_blank" rel="noopener">Abrir en el PDF original</a>.</p><ul class="connector-source-list">${detailSources(record)}</ul></div></details>
      <div class="connector-review-note"><strong>${esc(statusLabels[record.review.status])} · confianza ${Math.round(record.review.confidence*100)} %</strong><br>${esc(record.review.scope)}</div>
    </article>`;
    const url = new URL(location.href); url.searchParams.set('id', record.id); history.replaceState(null,'',url);
    if (scroll && matchMedia('(max-width:900px)').matches) document.getElementById('connectorDetail').scrollIntoView({behavior:'smooth',block:'start'});
  }

  function populateCategories() {
    const select = document.getElementById('connectorCategory');
    [...new Set(records.map(record=>record.category))].sort().forEach(category => select.insertAdjacentHTML('beforeend',`<option value="${esc(category)}">${esc(categoryLabels[category]||category)}</option>`));
  }

  async function load() {
    try {
      const [catalogResponse,sourcesResponse] = await Promise.all([fetch(new URL(CATALOG_URL,document.baseURI)),fetch(new URL(SOURCES_URL,document.baseURI))]);
      if (!catalogResponse.ok || !sourcesResponse.ok) throw new Error(`HTTP ${catalogResponse.status}/${sourcesResponse.status}`);
      const catalog = await catalogResponse.json(); const sources = await sourcesResponse.json();
      records = Array.isArray(catalog.records) ? catalog.records : []; sourceMap = new Map((sources.sources||[]).map(source=>[source.id,source]));
      populateCategories(); renderResults();
      const pulse = document.getElementById('connectorStatus'); pulse.classList.add('ready'); pulse.querySelector('strong').textContent = `${records.length} fichas normalizadas`; pulse.querySelector('small').textContent = `${catalog.counts.contacts} contactos estructurados`;
      const requestedId = new URL(location.href).searchParams.get('id'); if (requestedId && records.some(record=>record.id===requestedId)) selectRecord(requestedId); else if (records[0]) selectRecord(records[0].id);
    } catch (error) {
      console.error(error); const pulse=document.getElementById('connectorStatus'); pulse.classList.add('error'); pulse.querySelector('strong').textContent='No se pudo cargar'; document.getElementById('connectorResults').innerHTML='<p>La base no está disponible en este momento.</p>';
    }
  }

  document.getElementById('connectorSearchButton').addEventListener('click',()=>renderResults({autoSelect:true}));
  document.getElementById('connectorQuery').addEventListener('input',()=>renderResults());
  document.getElementById('connectorQuery').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();renderResults({autoSelect:true});}});
  document.getElementById('connectorCategory').addEventListener('change',()=>renderResults({autoSelect:true}));
  document.getElementById('connectorReview').addEventListener('change',()=>renderResults({autoSelect:true}));
  document.querySelectorAll('[data-query]').forEach(button=>button.addEventListener('click',()=>{document.getElementById('connectorQuery').value=button.dataset.query;renderResults({autoSelect:true});}));
  load();
})();
