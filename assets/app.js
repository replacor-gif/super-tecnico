'use strict';

const els = {
  brand: document.getElementById('brandSelect'),
  category: document.getElementById('categorySelect'),
  topic: document.getElementById('topicSelect'),
  content: document.getElementById('content'),
  context: document.getElementById('contextPanel'),
  breadcrumb: document.getElementById('breadcrumb'),
  searchForm: document.getElementById('globalSearchForm'),
  search: document.getElementById('globalSearch'),
  coverageButton: document.getElementById('coverageButton'),
  imageDialog: document.getElementById('imageDialog'),
  dialogImage: document.getElementById('dialogImage'),
  dialogCaption: document.getElementById('dialogCaption'),
  closeImageDialog: document.getElementById('closeImageDialog'),
};

const state = { brand: '', brandName: '', categories: [], category: null, topics: [], topic: null };
const cache = new Map();
const fileCache = new Map();

function esc(value) {
  return String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
}
function nl(value) { return esc(value).replace(/\n/g, '<br>'); }

function dataUrl(relativePath) {
  return new URL(relativePath.replace(/^\/+/, ''), document.baseURI);
}

async function fetchJson(relativePath) {
  if (fileCache.has(relativePath)) return fileCache.get(relativePath);
  const request = fetch(dataUrl(relativePath), {headers:{'Accept':'application/json'}})
    .then(async response => {
      if (!response.ok) throw new Error(`No se pudo cargar ${relativePath} (${response.status}).`);
      try { return await response.json(); }
      catch { throw new Error(`El archivo ${relativePath} no contiene JSON válido.`); }
    })
    .catch(error => {
      fileCache.delete(relativePath);
      throw error;
    });
  fileCache.set(relativePath, request);
  return request;
}

function brandSlug(value) {
  const slug = String(value || '').trim().toLowerCase();
  if (!/^[a-z0-9][a-z0-9-]{0,63}$/.test(slug)) throw new Error('Identificador de marca no válido.');
  return slug;
}

function brandWebPath(brand, relativePath) {
  return `data/brands/${brandSlug(brand)}/web/${String(relativePath).replace(/^\/+/, '')}`;
}

function normalizeSearch(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function searchScore(haystack, tokens, title='') {
  let score = 0;
  const normalizedTitle = normalizeSearch(title);
  tokens.forEach(token => {
    if (!token) return;
    if (normalizedTitle.includes(token)) score += 12;
    if (normalizedTitle.startsWith(token)) score += 8;
    score += Math.min(haystack.split(token).length - 1, 5) * 2;
  });
  return score;
}

async function navigation(brand) {
  return fetchJson(brandWebPath(brand, 'navigation.json'));
}

async function staticApi(action, params={}) {
  if (action === 'brands') {
    const manifest = await fetchJson('data/brands/index.json');
    return {ok:true, brands:manifest.brands || []};
  }

  const brand = brandSlug(params.brand);

  if (action === 'categories') {
    const nav = await navigation(brand);
    const categories = (nav.categories || [])
      .filter(category => Number(category.active ?? 1) === 1)
      .map(category => ({
        ...category,
        topic_count:(category.topics || []).length,
        variant_count:(category.topics || []).reduce((sum, topic) => sum + Number(topic.variant_count || 0), 0),
      }))
      .filter(category => category.topic_count > 0 || String(params.show_empty || '') === '1');
    return {ok:true, brand, categories};
  }

  if (action === 'topics') {
    const nav = await navigation(brand);
    const category = (nav.categories || []).find(item => item.slug === String(params.category || '').trim());
    if (!category) throw new Error('Categoría no encontrada.');
    return {ok:true, category, topics:category.topics || []};
  }

  if (action === 'topic') {
    const topicId = Number(params.topic_id);
    if (!Number.isInteger(topicId) || topicId < 1) throw new Error('Tema no válido.');
    const topic = await fetchJson(brandWebPath(brand, `topics/${topicId}.json`));
    return {ok:true, topic};
  }

  if (action === 'variant') {
    const variantId = Number(params.variant_id);
    if (!Number.isInteger(variantId) || variantId < 1) throw new Error('Variante no válida.');
    const map = await fetchJson(brandWebPath(brand, 'variant_map.json'));
    const topicId = map[String(variantId)];
    if (!topicId) throw new Error('Variante no encontrada.');
    const topic = await fetchJson(brandWebPath(brand, `topics/${Number(topicId)}.json`));
    const variant = (topic.variants || []).find(item => Number(item.id) === variantId);
    if (!variant) throw new Error('Variante no encontrada.');
    return {ok:true, topic:{id:topic.id, title:topic.title, category:topic.category}, variant};
  }

  if (action === 'errors') {
    const query = String(params.q || '').trim();
    const limit = Math.min(Math.max(Number(params.limit || 50), 1), 100);
    let items = await fetchJson(brandWebPath(brand, 'errors/index.json'));
    if (query) {
      const tokens = normalizeSearch(query).split(' ').filter(Boolean);
      items = items
        .filter(item => tokens.every(token => String(item.search_text || '').includes(token)))
        .map(item => ({item, score:searchScore(String(item.search_text || ''), tokens, `${item.code_display || ''} ${item.short_label || ''}`)}))
        .sort((a,b) => b.score - a.score)
        .slice(0, limit)
        .map(row => row.item);
    } else {
      items = items.slice(0, limit);
    }
    return {ok:true, query, errors:items};
  }

  if (action === 'error') {
    const errorId = Number(params.error_id);
    if (!Number.isInteger(errorId) || errorId < 1) throw new Error('Error técnico no válido.');
    const error = await fetchJson(brandWebPath(brand, `errors/details/${errorId}.json`));
    return {ok:true, error};
  }

  if (action === 'search') {
    const query = String(params.q || '').trim();
    if ([...query].length < 2) throw new Error('Escribe al menos dos caracteres.');
    const limit = Math.min(Math.max(Number(params.limit || 40), 1), 100);
    const category = String(params.category || '').trim();
    const tokens = normalizeSearch(query).split(' ').filter(Boolean);
    const entries = await fetchJson(brandWebPath(brand, 'search.json'));
    const results = entries
      .filter(entry => !category || entry.category_slug === category)
      .filter(entry => tokens.every(token => String(entry.haystack || '').includes(token)))
      .map(entry => ({entry, score:searchScore(String(entry.haystack || ''), tokens, String(entry.title || ''))}))
      .sort((a,b) => (b.score - a.score) || String(a.entry.title || '').localeCompare(String(b.entry.title || ''), 'es'))
      .slice(0, limit)
      .map(row => row.entry);
    return {ok:true, query, results};
  }

  if (action === 'coverage') {
    const coverage = await fetchJson(brandWebPath(brand, 'coverage.json'));
    return {ok:true, coverage};
  }

  if (action === 'health') {
    const manifest = await fetchJson('data/brands/index.json');
    const info = (manifest.brands || []).find(item => item.slug === brand);
    if (!info) throw new Error('Marca no encontrada.');
    return {ok:true, brand:info};
  }

  throw new Error('Consulta no válida.');
}

async function api(action, params={}) {
  const key = action + ':' + JSON.stringify(params);
  if (cache.has(key)) return cache.get(key);
  const request = staticApi(action, params).catch(error => {
    cache.delete(key);
    throw error;
  });
  cache.set(key, request);
  return request;
}
function loading(text='Cargando información…') { els.content.innerHTML = `<div class="loading">${esc(text)}</div>`; }
function showError(error) { els.content.innerHTML = `<div class="error-message">${esc(error.message || error)}</div>`; }
function setBreadcrumb(...items) { els.breadcrumb.innerHTML = items.filter(Boolean).map(x => `<span>${esc(x)}</span>`).join(''); }
function chip(text, className='') { return text ? `<span class="chip ${className}">${esc(text)}</span>` : ''; }
function mediaUrl(path) {
  const segments = String(path || '').replace(/\\/g, '/').split('/').filter(Boolean);
  if (!segments.length || segments.includes('..')) return '';
  return dataUrl(`data/brands/${brandSlug(state.brand)}/media/${segments.map(encodeURIComponent).join('/')}`).href;
}

async function init() {
  try {
    const data = await api('brands');
    els.brand.innerHTML = data.brands.length ? data.brands.map(b => `<option value="${esc(b.slug)}">${esc(b.display_name)}</option>`).join('') : '<option value="">Sin marcas instaladas</option>';
    if (!data.brands.length) return;
    const remembered = localStorage.getItem('st.brand');
    els.brand.value = data.brands.some(b => b.slug === remembered) ? remembered : data.brands[0].slug;
    await selectBrand(els.brand.value);
  } catch (error) { showError(error); }
}

async function selectBrand(slug) {
  state.brand = slug;
  localStorage.setItem('st.brand', slug);
  const option = els.brand.selectedOptions[0];
  state.brandName = option?.textContent || slug;
  els.category.disabled = true; els.topic.disabled = true;
  loading('Cargando categorías…');
  try {
    const data = await api('categories', {brand:slug});
    state.categories = data.categories;
    els.category.innerHTML = '<option value="">Selecciona una categoría</option>' + data.categories.map(c => `<option value="${esc(c.slug)}">${esc(c.name)} (${c.variant_count || 0})</option>`).join('');
    els.category.disabled = false;
    const remembered = localStorage.getItem(`st.category.${slug}`);
    if (data.categories.some(c => c.slug === remembered)) {
      els.category.value = remembered;
      await selectCategory(remembered);
    } else {
      state.category = null; state.topic = null;
      els.topic.innerHTML = '<option value="">Selecciona un tema</option>';
      setBreadcrumb(state.brandName);
      els.context.classList.remove('hidden');
      els.context.innerHTML = `<h2>${esc(state.brandName)}</h2><p>Selecciona una categoría. La marca contiene ${data.categories.length} bloques técnicos.</p>`;
      els.content.innerHTML = `<div class="welcome-card"><h2>Consulta técnica por categorías</h2><p>También puedes utilizar el buscador superior para localizar directamente un código, procedimiento, tensión o componente.</p></div>`;
    }
  } catch (error) { showError(error); }
}

async function selectCategory(slug) {
  state.category = state.categories.find(c => c.slug === slug) || null;
  state.topic = null;
  if (!state.category) return;
  localStorage.setItem(`st.category.${state.brand}`, slug);
  els.topic.disabled = true;
  loading('Cargando temas…');
  try {
    const data = await api('topics', {brand:state.brand, category:slug});
    state.topics = data.topics;
    els.topic.innerHTML = '<option value="">Selecciona un tema</option>' + data.topics.map(t => `<option value="${t.id}">${esc(t.title)} (${t.variant_count || 0})</option>`).join('');
    els.topic.disabled = data.topics.length === 0;
    setBreadcrumb(state.brandName, state.category.name);
    els.context.classList.remove('hidden');
    els.context.innerHTML = `<h2>${esc(state.category.name)}</h2><p>${esc(state.category.description || '')}</p>`;
    if (slug === 'errors') {
      renderErrorFinder(data.topics);
    } else {
      renderTopicChooser(data.topics);
    }
  } catch (error) { showError(error); }
}

function renderTopicChooser(topics) {
  if (!topics.length) { els.content.innerHTML = '<div class="empty">Esta categoría todavía no tiene contenido.</div>'; return; }
  els.content.innerHTML = topics.map(t => `<article class="search-hit"><h3>${esc(t.title)}</h3><p>${esc(t.summary || '')}</p><button type="button" data-open-topic="${t.id}">Abrir ${t.variant_count || 0} variante(s)</button></article>`).join('');
}

function renderErrorFinder(topics) {
  els.content.innerHTML = `
    <section class="result-card"><div class="card-body">
      <h2>Buscar código, subcódigo o significado</h2>
      <form id="errorSearchForm" class="error-search">
        <input id="errorSearchInput" type="search" placeholder="Ejemplos: E12, 12.1, boya, comunicación, IPM">
        <button type="submit">Buscar error</button>
      </form>
      <div id="errorResults" class="search-results"><p class="empty">Escribe un código o una palabra relacionada.</p></div>
    </div></section>
    ${topics.length ? `<section class="result-card"><div class="card-body"><h2>Lectura e interpretación desde placas</h2>${topics.map(t => `<article class="search-hit"><h3>${esc(t.title)}</h3><p>${esc(t.summary || '')}</p><button type="button" data-open-topic="${t.id}">Abrir</button></article>`).join('')}</div></section>` : ''}`;
  document.getElementById('errorSearchForm').addEventListener('submit', async event => {
    event.preventDefault();
    const q = document.getElementById('errorSearchInput').value.trim();
    const box = document.getElementById('errorResults');
    if (!q) { box.innerHTML = '<p class="empty">Escribe un código o una palabra relacionada.</p>'; return; }
    box.innerHTML = '<p class="loading">Buscando…</p>';
    try {
      const data = await api('errors', {brand:state.brand, q});
      box.innerHTML = data.errors.length ? data.errors.map(renderErrorHit).join('') : '<p class="empty">No se han encontrado coincidencias.</p>';
    } catch (error) { box.innerHTML = `<p class="error-message">${esc(error.message)}</p>`; }
  });
}

function renderErrorHit(item) {
  return `<article class="search-hit"><h3><span class="code-badge">${esc(item.code_display)}</span>${esc(item.short_label || 'Código de error')}</h3><p>${esc(scopeLabel(item.unit_scope))} · ${item.interpretation_count || 0} interpretación(es)</p><button type="button" data-open-error="${item.id}">Ver información</button></article>`;
}

async function selectTopic(id) {
  id = Number(id);
  if (!id) return;
  loading('Cargando variantes…');
  try {
    const data = await api('topic', {brand:state.brand, topic_id:id});
    state.topic = data.topic;
    els.topic.value = String(id);
    setBreadcrumb(state.brandName, data.topic.category?.name || state.category?.name, data.topic.title);
    els.context.classList.remove('hidden');
    els.context.innerHTML = `<h2>${esc(data.topic.title)}</h2><p>${esc(data.topic.summary || '')}</p>`;
    renderTopic(data.topic);
  } catch (error) { showError(error); }
}

function renderTopic(topic) {
  const variants = topic.variants || [];
  if (!variants.length) { els.content.innerHTML = '<div class="empty">No hay variantes publicadas.</div>'; return; }
  els.content.innerHTML = variants.map(v => renderVariant(v)).join('');
  bindMediaButtons();
}

function renderVariant(v, forceOpen=false) {
  const chips = [chip(v.system_type), chip(scopeLabel(v.unit_scope)), chip(v.refrigerant), chip(sourceKind(v.source_kind),'official')].join('');
  return `<details class="result-card" ${forceOpen ? 'open' : ''} id="variant-${v.id}">
    <summary><span class="variant-title">${esc(v.title)}</span>${v.recognition ? `<span class="variant-recognition">Cómo reconocerla: ${esc(v.recognition)}</span>` : ''}</summary>
    <div class="card-body">
      ${chips ? `<div class="chips">${chips}</div>` : ''}
      ${v.purpose ? `<p><strong>Finalidad:</strong> ${esc(v.purpose)}</p>` : ''}
      ${v.summary ? `<p>${esc(v.summary)}</p>` : ''}
      ${renderController(v.controller)}
      ${renderSections(v.sections || [])}
      ${renderSteps(v.steps || [])}
      ${renderParameters(v.parameters || [])}
      ${renderMonitoring(v.monitoring_points || [])}
      ${renderMedia(v.media || [])}
      ${renderSources(v.sources || [])}
    </div>
  </details>`;
}

function renderSections(sections) {
  return sections.map(s => `<details class="nested-detail" ${s.collapsed_default === 0 ? 'open' : ''}><summary>${esc(s.title || sectionLabel(s.section_type))}</summary><div class="nested-content">${formatBody(s.body)}</div></details>`).join('');
}
function formatBody(body) {
  const text = String(body || '').trim();
  if (!text) return '';
  const lines = text.split(/\n+/).map(x => x.trim()).filter(Boolean);
  if (lines.length > 1 && lines.every(x => /^[-•*]/.test(x))) return `<ul>${lines.map(x => `<li>${esc(x.replace(/^[-•*]\s*/,''))}</li>`).join('')}</ul>`;
  return `<p>${nl(text)}</p>`;
}
function renderSteps(steps) {
  if (!steps.length) return '';
  const grouped = Object.groupBy ? Object.groupBy(steps, x => x.phase || 'procedure') : steps.reduce((a,x)=>((a[x.phase||'procedure']??=[]).push(x),a),{});
  return Object.entries(grouped).map(([phase, items]) => `<details class="nested-detail" open><summary>${esc(phaseLabel(phase))}</summary><div class="nested-content"><ol class="procedure-list">${items.map(s => `<li class="${s.warning_level === 'danger' ? 'danger-box' : s.warning_level === 'warning' || s.warning_level === 'caution' ? 'warning-box' : ''}">${esc(s.instruction)}${s.expected_result ? `<span class="expected">Resultado esperado: ${esc(s.expected_result)}</span>` : ''}</li>`).join('')}</ol></div></details>`).join('');
}
function renderParameters(parameters) {
  if (!parameters.length) return '';
  return `<details class="nested-detail"><summary>Programaciones y valores</summary><div class="nested-content">${parameters.map(p => `<details class="variant-card"><summary><span class="variant-title">${p.parameter_code ? `${esc(p.parameter_code)} — ` : ''}${esc(p.name)}</span>${p.description ? `<span class="variant-recognition">${esc(p.description)}</span>` : ''}</summary><div class="card-body">${p.factory_value ? `<p><strong>Valor de fábrica:</strong> ${esc(p.factory_value)}</p>` : ''}${p.dependencies ? `<p><strong>Condiciones:</strong> ${esc(p.dependencies)}</p>` : ''}${p.warnings ? `<div class="warning-box">${esc(p.warnings)}</div>` : ''}${renderOptions(p.options || [])}</div></details>`).join('')}</div></details>`;
}
function renderOptions(options) {
  if (!options.length) return '';
  return `<div class="table-wrap"><table><thead><tr><th>Valor</th><th>Selección</th><th>Efecto</th></tr></thead><tbody>${options.map(o => `<tr><td>${esc(o.option_value)}</td><td>${esc(o.option_label)}${o.is_factory ? ' <strong>(fábrica)</strong>' : ''}</td><td>${esc(o.effect || '')}</td></tr>`).join('')}</tbody></table></div>`;
}
function renderController(c) {
  if (!c) return '';
  const rows = [
    ['Interfaz', c.interface_type], ['Familia reconocible', c.controller_family], ['Número de hilos', c.wire_count], ['Polaridad', c.polarity], ['Tensión nominal', c.nominal_voltage], ['Terminales', c.terminals], ['Colores documentados', c.cable_colors], ['Cable recomendado', c.cable_spec], ['Comportamiento al alimentar', c.startup_behavior], ['Alcance', c.maximum_scope], ['Notas', c.notes]
  ].filter(([,v]) => v !== null && v !== undefined && v !== '');
  return `<details class="nested-detail"><summary>Mando, cableado y alimentación</summary><div class="nested-content"><div class="table-wrap"><table><tbody>${rows.map(([a,b]) => `<tr><th>${esc(a)}</th><td>${esc(b)}</td></tr>`).join('')}</tbody></table></div></div></details>`;
}
function renderMonitoring(points) {
  if (!points.length) return '';
  return `<details class="nested-detail"><summary>Valores de monitorización</summary><div class="nested-content"><div class="table-wrap"><table><thead><tr><th>Dispositivo</th><th>ID</th><th>Dato</th><th>Unidad</th><th>Observaciones</th></tr></thead><tbody>${points.map(p => `<tr><td>${esc(p.device_id || '')}</td><td>${esc(p.sensor_id || '')}</td><td>${esc(p.item)}</td><td>${esc(p.unit_label || p.unit_code || '')}</td><td>${esc(p.remarks || '')}</td></tr>`).join('')}</tbody></table></div></div></details>`;
}
function renderMedia(media) {
  if (!media.length) return '';
  return `<details class="nested-detail"><summary>Imágenes técnicas (${media.length})</summary><div class="nested-content"><div class="gallery">${media.map(m => `<figure><button type="button" data-image="${esc(mediaUrl(m.relative_path))}" data-alt="${esc(m.alt_text || m.title || '')}" data-caption="${esc([m.title,m.caption,m.page_no ? `Página ${m.page_no}` : ''].filter(Boolean).join(' — '))}"><img loading="lazy" src="${esc(mediaUrl(m.relative_path))}" alt="${esc(m.alt_text || m.title || '')}"></button><figcaption>${esc(m.title || '')}${m.page_no ? ` · pág. ${esc(m.page_no)}` : ''}</figcaption></figure>`).join('')}</div></div></details>`;
}
function renderSources(sources) {
  if (!sources.length) return '';
  return `<details class="nested-detail"><summary>Fuentes documentales (${sources.length})</summary><div class="nested-content"><ul class="source-list">${sources.map(s => `<li>${s.source_url ? `<a href="${esc(s.source_url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a>` : esc(s.title)}${s.section ? ` — ${esc(s.section)}` : ''}${s.page_start ? ` — pág. ${esc(s.page_start)}${s.page_end && s.page_end !== s.page_start ? `-${esc(s.page_end)}` : ''}` : ''}</li>`).join('')}</ul></div></details>`;
}

async function openError(id) {
  loading('Cargando ficha del error…');
  try {
    const data = await api('error', {brand:state.brand, error_id:id});
    const e = data.error;
    setBreadcrumb(state.brandName, 'Errores y protecciones', e.code_display);
    els.context.classList.remove('hidden');
    els.context.innerHTML = `<h2><span class="code-badge">${esc(e.code_display)}</span>${esc(e.short_label || 'Código de error')}</h2><p>${esc(scopeLabel(e.unit_scope))}. Se muestran todas las interpretaciones documentadas.</p>`;
    els.content.innerHTML = renderErrorDetail(e);
    bindMediaButtons();
  } catch (error) { showError(error); }
}

function renderErrorDetail(e) {
  const aliases = (e.aliases || []).map(a => a.alias_display).filter(a => a !== e.code_display);
  return `<section class="result-card"><div class="card-body">
    <div class="chips">${chip(indicationLabel(e.indication_type))}${chip(scopeLabel(e.unit_scope))}${aliases.length ? chip('Variantes: '+aliases.join(', ')) : ''}</div>
    ${(e.interpretations || []).map((i,idx) => `<details class="variant-card" ${idx === 0 ? 'open' : ''}><summary><span class="variant-title">${esc(i.title)}</span>${i.description ? `<span class="variant-recognition">${esc(i.description)}</span>` : ''}</summary><div class="card-body">
      <div class="chips">${chip(sourceKind(i.source_kind),'official')}${chip('Fiabilidad: '+confidenceLabel(i.confidence))}</div>
      ${renderInfoItems(i.info_items || [])}
      ${renderImpacts(i.operational_impacts || [])}
      ${renderDatasets(i.datasets || [])}
      ${renderSources(i.sources || [])}
    </div></details>`).join('')}
    ${renderMedia(e.media || [])}
  </div></section>`;
}
function renderInfoItems(items) {
  if (!items.length) return '';
  const groups = items.reduce((a,x)=>((a[x.item_type||'observation']??=[]).push(x),a),{});
  return Object.entries(groups).map(([type,rows]) => `<details class="nested-detail" ${['cause','check'].includes(type) ? 'open' : ''}><summary>${esc(itemTypeLabel(type))}</summary><div class="nested-content"><ul>${rows.map(x => `<li>${x.title ? `<strong>${esc(x.title)}:</strong> ` : ''}${esc(x.body)}</li>`).join('')}</ul></div></details>`).join('');
}
function renderImpacts(items) {
  if (!items.length) return '';
  return `<details class="nested-detail" open><summary>Efecto sobre el funcionamiento</summary><div class="nested-content">${items.map(x => `<div class="notice-box"><strong>${esc(x.summary || stopLabel(x.stop_level))}</strong>${x.affected_scope ? `<p><strong>Afecta a:</strong> ${esc(x.affected_scope)}</p>` : ''}${x.unaffected_scope ? `<p><strong>Sigue funcionando:</strong> ${esc(x.unaffected_scope)}</p>` : ''}${x.restart_behavior ? `<p><strong>Recuperación:</strong> ${esc(x.restart_behavior)}</p>` : ''}${x.degraded_behavior ? `<p><strong>Modo degradado:</strong> ${esc(x.degraded_behavior)}</p>` : ''}${x.notes ? `<p>${esc(x.notes)}</p>` : ''}</div>`).join('')}</div></details>`;
}
function renderDatasets(datasets) {
  if (!datasets.length) return '';
  return datasets.map(d => `<details class="nested-detail"><summary>${esc(d.name)}</summary><div class="nested-content">${d.tolerance_text ? `<p><strong>Tolerancia:</strong> ${esc(d.tolerance_text)}</p>` : ''}${d.notes ? `<p>${esc(d.notes)}</p>` : ''}${renderDatasetTable(d)}${renderSources(d.sources || [])}</div></details>`).join('');
}
function renderDatasetTable(d) {
  const points = d.points || [];
  if (!points.length) return '';
  return `<div class="table-wrap"><table><thead><tr><th>${esc(d.variable_name || 'Variable')} ${d.variable_unit ? `(${esc(d.variable_unit)})` : ''}</th><th>Mínimo</th><th>Nominal</th><th>Máximo</th><th>${esc(d.value_name || 'Valor')} ${d.value_unit ? `(${esc(d.value_unit)})` : ''}</th></tr></thead><tbody>${points.map(p => `<tr><td>${esc(p.variable_value ?? '')}</td><td>${esc(p.value_min ?? '')}</td><td>${esc(p.value_nominal ?? '')}</td><td>${esc(p.value_max ?? '')}</td><td>${esc(p.value_text ?? '')}</td></tr>`).join('')}</tbody></table></div>`;
}

async function globalSearch(query) {
  loading('Buscando en toda la marca…');
  try {
    const data = await api('search', {brand:state.brand, q:query});
    setBreadcrumb(state.brandName, `Búsqueda: ${query}`);
    els.context.classList.remove('hidden');
    els.context.innerHTML = `<h2>Resultados de búsqueda</h2><p>${data.results.length} coincidencia(s) para “${esc(query)}”.</p>`;
    els.content.innerHTML = data.results.length ? data.results.map(r => `<article class="search-hit"><h3>${r.type === 'error' ? '<span class="code-badge">Error</span>' : ''}${esc(r.title)}</h3><p>${esc(r.category)}${r.summary ? ` — ${esc(r.summary)}` : ''}</p><button type="button" ${r.type === 'error' ? `data-open-error="${r.id}"` : `data-open-variant="${r.id}"`}>Abrir ficha</button></article>`).join('') : '<div class="empty">No se han encontrado coincidencias.</div>';
  } catch (error) { showError(error); }
}

async function openVariant(id) {
  loading('Cargando ficha técnica…');
  try {
    const data = await api('variant', {brand:state.brand, variant_id:id});
    setBreadcrumb(state.brandName, data.topic.category?.name, data.topic.title, data.variant.title);
    els.context.classList.remove('hidden');
    els.context.innerHTML = `<h2>${esc(data.variant.title)}</h2><p>${esc(data.variant.recognition || data.variant.summary || '')}</p>`;
    els.content.innerHTML = renderVariant(data.variant, true);
    bindMediaButtons();
  } catch (error) { showError(error); }
}

async function showCoverage() {
  if (!state.brand) return;
  loading('Cargando cobertura…');
  try {
    const data = await api('coverage', {brand:state.brand});
    setBreadcrumb(state.brandName, 'Cobertura documental');
    els.context.classList.remove('hidden');
    els.context.innerHTML = '<h2>Cobertura documental</h2><p>Indica qué áreas están cubiertas, parciales o pendientes. No significa que toda la historia de la marca esté documentada.</p>';
    els.content.innerHTML = `<div class="coverage-grid">${data.coverage.map(c => { const status = c.coverage_status || c.status || c.coverage || 'sin estado'; const label = ({covered:'Cubierto',partial:'Parcial',pending:'Pendiente'}[status] || status); return `<article class="coverage-card"><h3>${esc(c.area_name || c.area || c.name || c.category || 'Área')}</h3><div class="chips">${chip(label, status === 'covered' ? 'official' : 'warning')}${c.equipment_scope ? chip(c.equipment_scope) : ''}</div><p>${esc(c.notes || c.description || '')}</p></article>`; }).join('')}</div>`;
  } catch (error) { showError(error); }
}

function bindMediaButtons() {
  document.querySelectorAll('[data-image]').forEach(button => button.addEventListener('click', () => {
    els.dialogImage.src = button.dataset.image;
    els.dialogImage.alt = button.dataset.alt || '';
    els.dialogCaption.textContent = button.dataset.caption || '';
    els.imageDialog.showModal();
  }));
}
function scopeLabel(v) { return ({indoor:'Unidad interior',outdoor:'Unidad exterior',general:'General',unknown:'Ámbito no especificado'}[v] || v || ''); }
function sourceKind(v) { return ({official:'Dato oficial',calculated:'Valor calculado',workshop_experience:'Experiencia de taller',technical_hypothesis:'Hipótesis técnica'}[v] || v || ''); }
function confidenceLabel(v) { return ({high:'alta',medium:'media',low:'baja',unknown:'no indicada'}[v] || v || ''); }
function indicationLabel(v) { return ({display:'Display',led:'LED/parpadeos',remote_controller:'Mando',app:'Aplicación',mixed:'Indicación combinada',other:'Otra indicación'}[v] || v || ''); }
function sectionLabel(v) { return ({wiring:'Cableado',notes:'Observaciones',safety:'Seguridad',operation:'Funcionamiento',checks:'Comprobaciones',behavior:'Comportamiento'}[v] || 'Información'); }
function phaseLabel(v) { return ({procedure:'Procedimiento',precheck:'Comprobaciones previas',check:'Comprobaciones',result:'Interpretación del resultado',finish:'Finalización',cancel:'Cancelación',warning:'Advertencias'}[v] || v || 'Procedimiento'); }
function itemTypeLabel(v) { return ({related_element:'Elementos relacionados',cause:'Posibles causas',check:'Comprobaciones',observation:'Observaciones',safety:'Seguridad',machine_behavior:'Comportamiento de la máquina'}[v] || v); }
function stopLabel(v) { return ({all_system:'Se detiene todo el sistema',affected_unit:'Se detiene la unidad afectada',branch:'Se detiene una rama o grupo',outdoor_only:'Se detiene la unidad exterior',degraded:'Funcionamiento degradado',unknown:'Efecto no especificado'}[v] || v || 'Efecto operativo'); }

els.brand.addEventListener('change', () => selectBrand(els.brand.value));
els.category.addEventListener('change', () => els.category.value && selectCategory(els.category.value));
els.topic.addEventListener('change', () => els.topic.value && selectTopic(els.topic.value));
els.searchForm.addEventListener('submit', event => { event.preventDefault(); const q = els.search.value.trim(); if (q.length >= 2 && state.brand) globalSearch(q); });
els.coverageButton.addEventListener('click', showCoverage);
els.closeImageDialog.addEventListener('click', () => els.imageDialog.close());
els.imageDialog.addEventListener('click', event => { if (event.target === els.imageDialog) els.imageDialog.close(); });
document.addEventListener('click', event => {
  const topicButton = event.target.closest('[data-open-topic]'); if (topicButton) selectTopic(topicButton.dataset.openTopic);
  const errorButton = event.target.closest('[data-open-error]'); if (errorButton) openError(errorButton.dataset.openError);
  const variantButton = event.target.closest('[data-open-variant]'); if (variantButton) openVariant(variantButton.dataset.openVariant);
});

init();
