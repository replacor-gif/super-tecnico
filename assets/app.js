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
  brandStatus: document.getElementById('brandStatus'),
  quickAccess: document.getElementById('quickAccessPanel'),
  homeButton: document.getElementById('homeButton'),
  coverageButton: document.getElementById('coverageButton'),
  oemFinderButton: document.getElementById('oemFinderButton'),
  imageDialog: document.getElementById('imageDialog'),
  dialogImage: document.getElementById('dialogImage'),
  dialogCaption: document.getElementById('dialogCaption'),
  closeImageDialog: document.getElementById('closeImageDialog'),
};

const state = {
  brand: '',
  brandName: '',
  brandInfo: null,
  categories: [],
  category: null,
  topics: [],
  topic: null,
  errorCatalog: [],
  oemCatalog: null,
};
const cache = new Map();
const fileCache = new Map();
const installedBrands = new Map();

function esc(value) {
  return String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
}
function nl(value) { return esc(value).replace(/\n/g, '<br>'); }
function localizedText(record, field, fallback='') {
  if (!record) return fallback;
  const language = window.ST_I18N?.language || 'es';
  return record.translations?.[language]?.[field]
    || record[`${field}_${language}`]
    || record[field]
    || fallback;
}

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
  const compactHaystack = haystack.replace(/\s+/g, '');
  const compactTitle = normalizedTitle.replace(/\s+/g, '');
  tokens.forEach(token => {
    if (!token) return;
    if (normalizedTitle.includes(token) || compactTitle.includes(token)) score += 12;
    if (normalizedTitle.startsWith(token) || compactTitle.startsWith(token)) score += 8;
    const occurrences = Math.max(
      haystack.split(token).length - 1,
      compactHaystack.split(token).length - 1,
    );
    score += Math.min(occurrences, 5) * 2;
  });
  return score;
}

function matchesSearchTokens(haystack, tokens) {
  const compactHaystack = String(haystack || '').replace(/\s+/g, '');
  return tokens.every(token => haystack.includes(token) || compactHaystack.includes(token));
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
    const limit = Math.min(Math.max(Number(params.limit || 50), 1), 500);
    let items = await fetchJson(brandWebPath(brand, 'errors/index.json'));
    if (query) {
      const tokens = normalizeSearch(query).split(' ').filter(Boolean);
      items = items
        .filter(item => matchesSearchTokens(String(item.search_text || ''), tokens))
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
      .filter(entry => matchesSearchTokens(String(entry.haystack || ''), tokens))
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
function revealResults() {
  window.requestAnimationFrame(() => els.context.scrollIntoView({behavior:'smooth', block:'start'}));
}
function chip(text, className='') { return text ? `<span class="chip ${className}">${esc(text)}</span>` : ''; }
function mediaUrl(path) {
  const segments = String(path || '').replace(/\\/g, '/').split('/').filter(Boolean);
  if (!segments.length || segments.includes('..')) return '';
  return dataUrl(`data/brands/${brandSlug(state.brand)}/media/${segments.map(encodeURIComponent).join('/')}`).href;
}

function categoryIcon(slug) {
  return ({
    errors:'ERR', diagnostic_access:'COD', service_modes:'TEST', configuration:'CFG',
    commissioning:'INI', history_reset:'HIS', controllers_buses:'BUS', monitoring:'MON',
    external_io:'I/O', controls:'CTL', drainage_overflow:'H₂O', vrf_network:'VRF',
    normal_states:'OK', service_tools:'PC', component_checks:'CMP',
    technical_values:'VAL', symptom_diagnosis:'DIA', board_replacement:'PCB',
  }[slug] || 'TEC');
}
function countLabel(value, singular, plural=`${singular}s`) {
  const count = Number(value || 0);
  return `${count} ${count === 1 ? singular : plural}`;
}

function recentKey() { return `st.recents.${state.brand}`; }
function readRecents() {
  try { return JSON.parse(localStorage.getItem(recentKey()) || '[]').slice(0, 6); }
  catch { return []; }
}
function rememberRecent(item) {
  if (!state.brand || !item?.id || !item?.type) return;
  const rows = readRecents().filter(row => !(row.type === item.type && Number(row.id) === Number(item.id)));
  rows.unshift({...item, id:Number(item.id)});
  localStorage.setItem(recentKey(), JSON.stringify(rows.slice(0, 6)));
}
function renderRecents() {
  const rows = readRecents();
  if (!rows.length) return '';
  return `<section class="recent-panel context-panel"><h2>Consultado recientemente</h2><div class="recent-list">${rows.map(row => `<button type="button" class="recent-link" ${row.type === 'error' ? `data-open-error="${row.id}"` : `data-open-variant="${row.id}"`}>${row.code ? `<span class="code-badge">${esc(row.code)}</span>` : ''}${esc(row.title)}</button>`).join('')}</div></section>`;
}

const primaryAccess = [
  {slug:'errors', label:'Errores y protecciones', hint:'Seleccionar un código o consultar sus posibles significados', icon:'ERR'},
  {slug:'diagnostic_access', label:'Obtener códigos', hint:'Mandos, displays, placas, historiales y subcódigos', icon:'COD'},
  {slug:'service_modes', label:'Marchas forzadas y pruebas', hint:'Test Run, Pump Down y funciones de servicio', icon:'TEST'},
  {slug:'configuration', label:'Programación y ajustes', hint:'Mandos, microinterruptores, parámetros y direcciones', icon:'CFG'},
  {slug:'component_checks', label:'Comprobar componentes', hint:'Sondas, ventiladores, bombas, válvulas y electrónica', icon:'CMP'},
  {slug:'technical_values', label:'Valores técnicos', hint:'Tensiones, resistencias, presiones y tablas', icon:'VAL'},
];

function errorCatalogOptions(catalog, placeholder='Selecciona un código de error') {
  const rows = [...catalog].sort((a, b) => String(a.code_display || '').localeCompare(
    String(b.code_display || ''), 'es', {numeric:true, sensitivity:'base'},
  ));
  return `<option value="">${esc(placeholder)}</option>${rows.map(item => {
    const detail = Number(item.interpretation_count || 0) > 1
      ? `${item.interpretation_count} posibles significados`
      : (item.short_label || 'Código de error');
    return `<option value="${item.id}">${esc(item.code_display)} — ${esc(detail)}</option>`;
  }).join('')}`;
}

function renderQuickAccess() {
  if (!els.quickAccess) return;
  const availableCategories = new Map(state.categories.map(category => [category.slug, category]));
  const taskButtons = primaryAccess
    .filter(item => availableCategories.has(item.slug))
    .map(item => `<button type="button" class="task-card" data-open-category="${esc(item.slug)}">
      <span class="task-icon">${esc(item.icon)}</span>
      <span><strong>${esc(item.label)}</strong><small>${esc(item.hint)}</small></span>
    </button>`).join('') + `<button type="button" class="task-card task-card-oem" data-open-oem>
      <span class="task-icon">PCB</span>
      <span><strong>¿No aparece la marca comercial?</strong><small>Localiza el fabricante probable por el código impreso en la placa y consulta después el error.</small></span>
    </button>`;
  const errorCount = state.errorCatalog.length;
  els.quickAccess.innerHTML = `
    <div class="quick-access-heading">
      <span class="step-label">Paso 2</span>
      <h2>¿Qué necesitas hacer?</h2>
      <p>Para consultar una avería, elige directamente el código. Para otro trabajo técnico, abre uno de los accesos.</p>
    </div>
    <form id="quickErrorForm" class="quick-error-form">
      <div class="field">
        <label for="quickErrorSelect">Código de error</label>
        <select id="quickErrorSelect" ${errorCount ? '' : 'disabled'}>
          ${errorCatalogOptions(state.errorCatalog, errorCount ? `Selecciona uno de los ${errorCount} códigos` : 'No hay códigos publicados')}
        </select>
      </div>
      <button id="quickErrorButton" type="submit" disabled>Abrir ficha</button>
    </form>
    <div class="task-grid">${taskButtons}</div>`;

  const select = document.getElementById('quickErrorSelect');
  const button = document.getElementById('quickErrorButton');
  select?.addEventListener('change', () => { button.disabled = !select.value; });
  document.getElementById('quickErrorForm')?.addEventListener('submit', event => {
    event.preventDefault();
    if (select.value) openError(select.value);
  });
}

function renderBrandDashboard() {
  state.category = null;
  state.topic = null;
  els.category.value = '';
  els.topic.innerHTML = '<option value="">Selecciona un tema</option>';
  els.topic.disabled = true;
  setBreadcrumb(state.brandName);
  els.context.classList.add('hidden');
  const cards = state.categories.map(category => {
    const topics = category.topics || [];
    const topicButtons = topics.map(topic => `<button type="button" class="topic-link" data-open-topic="${topic.id}"><span>${esc(localizedText(topic, 'title'))}</span><small>${esc(countLabel(topic.variant_count, 'ficha'))}</small></button>`).join('');
    const primary = category.slug === 'errors'
      ? `<button type="button" class="category-primary" data-open-category="errors">Buscar código o significado</button>`
      : '';
    return `<details class="category-card" ${category.slug === 'errors' ? 'open' : ''}>
      <summary><span class="category-icon">${esc(categoryIcon(category.slug))}</span><span><span class="category-title">${esc(localizedText(category, 'name'))}</span><span class="category-description">${esc(localizedText(category, 'description'))}</span></span><span class="category-count">${esc(countLabel(category.variant_count, 'ficha'))}</span></summary>
      <div class="topic-menu">${topicButtons || '<p class="empty">Sin temas publicados.</p>'}</div>${primary}
    </details>`;
  }).join('');
  els.content.innerHTML = `${renderRecents()}<details class="library-explorer"><summary>Ver todos los apartados técnicos (${state.categories.length})</summary><div class="library-explorer-body"><p><strong>No se ha eliminado información.</strong> Aquí siguen disponibles todos los temas, errores, procedimientos, programaciones, pruebas y valores técnicos de la marca, organizados por categorías.</p><section class="category-grid">${cards}</section></div></details>`;
}

function showHome() {
  if (!state.brand || !state.categories.length) return;
  renderBrandDashboard();
  window.scrollTo({top:0, behavior:'smooth'});
}

async function init() {
  try {
    const data = await api('brands');
    data.brands.forEach(brand => installedBrands.set(brand.slug, brand));
    els.brand.innerHTML = data.brands.length ? data.brands.map(b => `<option value="${esc(b.slug)}">${esc(b.display_name)}</option>`).join('') : '<option value="">Sin marcas instaladas</option>';
    if (!data.brands.length) return;
    const remembered = localStorage.getItem('st.brand');
    const referenceBrand = [...data.brands].sort((a,b) => Number(b.counts?.variants || 0) - Number(a.counts?.variants || 0))[0];
    els.brand.value = data.brands.some(b => b.slug === remembered) ? remembered : referenceBrand.slug;
    await selectBrand(els.brand.value);
  } catch (error) { showError(error); }
}

async function selectBrand(slug) {
  state.brand = slug;
  state.brandInfo = installedBrands.get(slug) || null;
  state.errorCatalog = [];
  localStorage.setItem('st.brand', slug);
  const option = els.brand.selectedOptions[0];
  state.brandName = option?.textContent || slug;
  els.category.disabled = true; els.topic.disabled = true;
  if (els.quickAccess) els.quickAccess.innerHTML = '<div class="loading">Preparando accesos rápidos…</div>';
  loading('Cargando categorías…');
  try {
    const [data, errorData] = await Promise.all([
      api('categories', {brand:slug}),
      api('errors', {brand:slug, limit:500}),
    ]);
    state.categories = data.categories;
    state.errorCatalog = errorData.errors || [];
    els.category.innerHTML = '<option value="">Selecciona una categoría</option>' + data.categories.map(c => `<option value="${esc(c.slug)}">${esc(c.name)} (${c.variant_count || 0})</option>`).join('');
    els.category.disabled = false;
    const remembered = localStorage.getItem(`st.category.${slug}`);
    els.category.value = data.categories.some(c => c.slug === remembered) ? remembered : '';
    const counts = state.brandInfo?.counts || {};
    els.brandStatus.removeAttribute('data-i18n');
    els.brandStatus.textContent = `${data.categories.length} categorías disponibles · ${counts.errors || 0} errores · ${counts.variants || 0} fichas técnicas`;
    renderQuickAccess();
    renderBrandDashboard();
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
    els.context.innerHTML = `<h2>${esc(localizedText(state.category, 'name'))}</h2><p>${esc(localizedText(state.category, 'description'))}</p>`;
    if (slug === 'errors') {
      await renderErrorFinder(data.topics);
    } else {
      renderTopicChooser(data.topics);
    }
    revealResults();
  } catch (error) { showError(error); }
}

function renderTopicChooser(topics) {
  if (!topics.length) { els.content.innerHTML = '<div class="empty">Esta categoría todavía no tiene contenido.</div>'; return; }
  els.content.innerHTML = topics.map(t => `<article class="search-hit"><h3>${esc(localizedText(t, 'title'))}</h3><p>${esc(localizedText(t, 'summary'))}</p><button type="button" data-open-topic="${t.id}">Abrir ${t.variant_count || 0} variante(s)</button></article>`).join('');
}

async function renderErrorFinder(topics) {
  const catalog = state.errorCatalog.length
    ? state.errorCatalog
    : ((await api('errors', {brand:state.brand, limit:500})).errors || []);
  state.errorCatalog = catalog;
  const availableCodes = catalog.map(item => item.code_display).filter(Boolean);
  const compactCodes = availableCodes.length <= 20 ? availableCodes.join(', ') : '';
  const catalogSummary = catalog.length
    ? `La base actual contiene ${catalog.length} código(s)${compactCodes ? `: ${compactCodes}` : ''}.`
    : 'La base actual todavía no contiene códigos de error.';
  els.content.innerHTML = `
    <section class="result-card"><div class="card-body">
      <h2>Buscar código, subcódigo o significado</h2>
      <div class="notice-box"><strong>Cobertura disponible:</strong> ${esc(catalogSummary)} Los códigos que todavía no se hayan incorporado no devolverán una ficha.</div>
      <form id="errorSearchForm" class="error-search">
        <input id="errorSearchInput" type="search" placeholder="Ejemplos: E12, 12.1, boya, comunicación, IPM">
        <button type="submit">Buscar error</button>
      </form>
      <div id="errorResults" class="search-results"><p class="empty">Escribe un código o una palabra relacionada.</p></div>
      ${catalog.length ? `<form id="errorCatalogForm" class="error-catalog-form"><div class="field"><label for="errorCatalogSelect">O elegir de la lista completa</label><select id="errorCatalogSelect">${errorCatalogOptions(catalog)}</select></div><button id="errorCatalogButton" type="submit" disabled>Abrir ficha</button></form>` : ''}
      <aside class="oem-callout">
        <div><strong>¿La marca de la máquina no está en Super Técnico?</strong><p>Busca el fabricante electrónico por el código serigrafiado o la etiqueta de su placa.</p></div>
        <button type="button" data-open-oem>Identificar por placa</button>
      </aside>
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
      box.innerHTML = data.errors.length
        ? data.errors.map(renderErrorHit).join('')
        : `<div class="empty"><strong>“${esc(q)}” todavía no está incluido en la base de ${esc(state.brandName)}.</strong><p>El buscador funciona, pero no puede mostrar una ficha que aún no se ha cargado.${compactCodes ? ` Prueba con uno de los códigos disponibles: ${esc(compactCodes)}.` : ''}</p></div>`;
    } catch (error) { box.innerHTML = `<p class="error-message">${esc(error.message)}</p>`; }
  });
  const catalogSelect = document.getElementById('errorCatalogSelect');
  const catalogButton = document.getElementById('errorCatalogButton');
  catalogSelect?.addEventListener('change', () => { catalogButton.disabled = !catalogSelect.value; });
  document.getElementById('errorCatalogForm')?.addEventListener('submit', event => {
    event.preventDefault();
    if (catalogSelect.value) openError(catalogSelect.value);
  });
}

function renderErrorHit(item) {
  return `<article class="search-hit"><h3><span class="code-badge">${esc(item.code_display)}</span>${esc(localizedText(item, 'short_label', 'Código de error'))}</h3><p>${esc(scopeLabel(item.unit_scope))} · ${item.interpretation_count || 0} interpretación(es)</p><button type="button" data-open-error="${item.id}">Ver información</button></article>`;
}

async function loadOemCatalog() {
  if (state.oemCatalog) return state.oemCatalog;
  state.oemCatalog = await fetchJson('data/oem/pcb_patterns.json');
  return state.oemCatalog;
}

function normalizePcbCode(value) {
  return String(value || '').toUpperCase().replace(/\s+/g, '').trim();
}

function compactErrorCode(value) {
  return normalizeSearch(value).replace(/\s+/g, '');
}

function oemPatternOptions(patterns) {
  const groups = new Map();
  [...patterns]
    .sort((a, b) => String(a.oem).localeCompare(String(b.oem), 'es')
      || String(a.visible_pattern).localeCompare(String(b.visible_pattern), 'es', {numeric:true}))
    .forEach(pattern => {
      if (!groups.has(pattern.oem)) groups.set(pattern.oem, []);
      groups.get(pattern.oem).push(pattern);
    });
  return '<option value="">Selecciona el patrón que ves en la PCB</option>'
    + [...groups.entries()].map(([oem, rows]) => `<optgroup label="${esc(oem)}">${
      rows.map(row => `<option value="${row.id}">${esc(row.visible_pattern)} · ${row.confidence === 'alta' ? 'confianza alta' : 'confirmar con otra pista'}</option>`).join('')
    }</optgroup>`).join('');
}

function identifyOemByCode(catalog, rawCode) {
  const code = normalizePcbCode(rawCode);
  const matches = (catalog.patterns || []).filter(item => {
    try { return new RegExp(item.regex, 'i').test(code); }
    catch { return false; }
  }).sort((a, b) => {
    const confidence = {alta:2, media:1};
    return (confidence[b.confidence] || 0) - (confidence[a.confidence] || 0)
      || String(b.search_prefix || '').length - String(a.search_prefix || '').length;
  });
  if (matches.length) return {status:'identified', code, matches};
  const ambiguous = (catalog.ambiguous_patterns || []).find(item => {
    try { return new RegExp(item.regex, 'i').test(code); }
    catch { return false; }
  });
  if (ambiguous) return {status:'ambiguous', code, ambiguous, matches:[]};
  return {status:'not_found', code, matches:[]};
}

async function findOemErrorCandidates(pattern, rawErrorCode) {
  const brand = pattern.brand_slug;
  if (!brand || !installedBrands.has(brand)) {
    return {available:false, exact:[], related:[]};
  }
  const query = compactErrorCode(rawErrorCode);
  const catalog = await fetchJson(brandWebPath(brand, 'errors/index.json'));
  const exact = catalog.filter(item => compactErrorCode(item.code_normalized || item.code_display) === query);
  if (exact.length || query.length < 2) return {available:true, exact, related:[]};
  const tokens = normalizeSearch(rawErrorCode).split(' ').filter(Boolean);
  const related = catalog
    .filter(item => matchesSearchTokens(String(item.search_text || ''), tokens))
    .map(item => ({item, score:searchScore(String(item.search_text || ''), tokens, item.code_display)}))
    .sort((a, b) => b.score - a.score)
    .slice(0, 8)
    .map(row => row.item);
  return {available:true, exact:[], related};
}

function oemConfidenceLabel(value) {
  return value === 'alta' ? 'Coincidencia fuerte' : 'Coincidencia probable';
}

function oemAuthorityLabel(value) {
  return ({
    primary:'Fuente oficial localizada',
    documented:'Manual o documentación técnica',
    indirect:'Evidencia de catálogo; confirmar',
  }[value] || 'Evidencia aportada');
}

function renderOemErrorRows(pattern, result, errorCode) {
  if (!result.available) {
    return `<div class="empty oem-error-empty"><strong>La tabla de ${esc(pattern.recommended_error_table)} todavía no está incorporada.</strong><p>La placa puede quedar orientada hacia ${esc(pattern.oem)}, pero Super Técnico aún no puede relacionar de forma segura el error ${esc(errorCode)} con una ficha técnica.</p></div>`;
  }
  const rows = result.exact.length ? result.exact : result.related;
  if (!rows.length) {
    return `<div class="empty oem-error-empty"><strong>No hay una ficha para ${esc(errorCode)} en la base de ${esc(pattern.recommended_error_table)}.</strong><p>Esto significa “no documentado todavía”, no “código inexistente”. Comprueba también dónde se leyó el error y envía una sugerencia si dispones del manual.</p></div>`;
  }
  const relatedNotice = result.exact.length ? '' : `<div class="warning-box"><strong>No existe una coincidencia exacta.</strong> Estas fichas solo mencionan ${esc(errorCode)} dentro de su documentación; deben tratarse como referencias relacionadas.</div>`;
  return `${relatedNotice}<div class="oem-error-list">${rows.map(item => `<article class="search-hit">
    <h4><span class="code-badge">${esc(item.code_display)}</span>${esc(item.short_label || 'Código de error')}</h4>
    <p>${esc(scopeLabel(item.unit_scope))} · ${item.interpretation_count || 0} posible(s) significado(s). Ninguno se abrirá automáticamente.</p>
    <button type="button" data-open-oem-error="${item.id}" data-oem-brand="${esc(pattern.brand_slug)}">Ver todos los significados</button>
  </article>`).join('')}</div>`;
}

function renderOemMatch(pattern, result, errorCode, readLocation) {
  const source = pattern.source || {};
  return `<article class="result-card oem-match-card"><div class="card-body">
    <div class="oem-match-heading">
      <div><span class="step-label">${pattern.confidence === 'alta' ? 'OEM identificado' : 'OEM probable'}</span><h3>${esc(pattern.oem)}</h3></div>
      <span class="code-badge">${esc(pattern.visible_pattern)}</span>
    </div>
    <div class="chips">${chip(oemConfidenceLabel(pattern.confidence), pattern.confidence === 'alta' ? 'official' : 'warning')}${chip(oemAuthorityLabel(source.authority))}${chip(`Tabla recomendada: ${pattern.recommended_error_table}`)}</div>
    <p>${esc(pattern.explanation)}</p>
    <div class="warning-box"><strong>Confirmación necesaria:</strong> ${esc(pattern.exceptions)}</div>
    <dl class="oem-facts">
      <div><dt>Dónde suele estar</dt><dd>${esc(pattern.usual_location)}</dd></div>
      <div><dt>Ejemplo de formato</dt><dd>${esc(pattern.example)}</dd></div>
      <div><dt>Error introducido</dt><dd>${esc(errorCode)}${readLocation ? ` · leído en ${esc(readLocation)}` : ''}</dd></div>
    </dl>
    <section class="oem-error-section"><h4>Resultados posibles para el error ${esc(errorCode)}</h4>${renderOemErrorRows(pattern, result, errorCode)}</section>
    ${source.url ? `<details class="nested-detail"><summary>Fuente del patrón de placa</summary><div class="nested-content"><p>${esc(source.title || 'Documento de referencia')}</p><a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">Abrir fuente ↗</a><p class="source-caution">La fuente respalda el patrón de placa; la aplicabilidad del error debe confirmarse con la familia y el lugar donde se leyó.</p></div></details>` : ''}
  </div></article>`;
}

async function runOemLookup(catalog) {
  const codeInput = document.getElementById('oemBoardCode');
  const patternSelect = document.getElementById('oemPatternSelect');
  const errorInput = document.getElementById('oemErrorCode');
  const locationSelect = document.getElementById('oemErrorLocation');
  const results = document.getElementById('oemResults');
  const rawCode = codeInput.value.trim();
  const errorCode = errorInput.value.trim().toUpperCase();
  if (!rawCode && !patternSelect.value) {
    results.innerHTML = '<div class="error-message">Escribe el código completo de la placa o selecciona su patrón en la lista.</div>';
    codeInput.focus();
    return;
  }
  if (!errorCode) {
    results.innerHTML = '<div class="error-message">Indica también el código de error que muestra la máquina.</div>';
    errorInput.focus();
    return;
  }

  let identification;
  if (rawCode) {
    identification = identifyOemByCode(catalog, rawCode);
  } else {
    const selected = (catalog.patterns || []).find(item => String(item.id) === patternSelect.value);
    identification = selected
      ? {status:'selected_pattern', code:selected.visible_pattern, matches:[selected]}
      : {status:'not_found', code:'', matches:[]};
  }

  if (identification.status === 'ambiguous') {
    const item = identification.ambiguous;
    results.innerHTML = `<div class="warning-box oem-blocked"><strong>El código ${esc(identification.code)} no basta para identificar el fabricante.</strong><p>${esc(item.reason)}</p><p><strong>Siguiente paso:</strong> ${esc(item.recommended_action)}</p></div>`;
    return;
  }
  if (identification.status === 'not_found') {
    results.innerHTML = `<div class="empty"><strong>No se reconoce el código de placa ${esc(identification.code)}.</strong><p>No elijas una plataforma por parecido. Busca otra referencia completa en la serigrafía o etiqueta de la PCB y conserva una fotografía de conjunto.</p></div>`;
    return;
  }

  results.innerHTML = '<div class="loading">Relacionando la placa con las bases de errores…</div>';
  const matchesWithResults = await Promise.all(identification.matches.map(async pattern => ({
    pattern,
    result:await findOemErrorCandidates(pattern, errorCode),
  })));
  const readLocation = locationSelect.value;
  results.innerHTML = `<div class="oem-results-intro"><strong>${matchesWithResults.length} plataforma(s) electrónica(s) posible(s)</strong><p>Revisa todas. Ninguna ficha se abre automáticamente y la marca de la carcasa no se usa como prueba.</p></div>${
    matchesWithResults.map(({pattern, result}) => renderOemMatch(pattern, result, errorCode, readLocation)).join('')
  }`;
}

async function showOemFinder() {
  state.category = null;
  state.topic = null;
  setBreadcrumb('Identificación por placa', 'Marca comercial no disponible');
  els.context.classList.remove('hidden');
  els.context.innerHTML = '<h2>Localizar errores por fabricante electrónico</h2><p>Úsalo cuando la marca comercial no esté en la lista o sospeches que la electrónica procede de otro fabricante.</p>';
  loading('Cargando patrones de placas…');
  try {
    const catalog = await loadOemCatalog();
    els.content.innerHTML = `<section class="result-card oem-finder"><div class="card-body">
      <div class="notice-box"><strong>Este método orienta; no certifica el modelo.</strong><p>${esc(catalog.meta.warning)}</p></div>
      <details class="nested-detail oem-guide" open>
        <summary>Cómo localizar correctamente el código de la placa</summary>
        <div class="nested-content">
          <ol class="procedure-list">
            <li class="danger-box"><strong>Desconecta la alimentación.</strong> Respeta el tiempo de descarga indicado por el fabricante y verifica ausencia de tensión antes de acercarte a la electrónica.</li>
            <li>Haz una fotografía general de la placa y otra de cada etiqueta antes de desconectar cables.</li>
            <li>Busca un código alfanumérico impreso en la serigrafía o en una etiqueta adherida a la propia PCB. Puede estar cerca del borde, de los relés o del conector principal.</li>
            <li>No uses el modelo de la máquina, el número de serie, el código del compresor ni la referencia de un componente aislado como si fueran el código de la placa.</li>
            <li>Escribe el código completo. Si no puedes leerlo entero, selecciona abajo el patrón que coincida visualmente y confirma después con otra pista.</li>
          </ol>
        </div>
      </details>
      <form id="oemLookupForm" class="oem-lookup-form">
        <div class="field oem-code-field">
          <label for="oemBoardCode"><span class="step-label">Paso 1 recomendado</span>Código completo impreso en la placa</label>
          <input id="oemBoardCode" type="text" maxlength="80" autocomplete="off" placeholder="Ejemplo: MCC-1606">
        </div>
        <div class="field">
          <label for="oemPatternSelect">O elige el patrón que reconoces</label>
          <select id="oemPatternSelect">${oemPatternOptions(catalog.patterns || [])}</select>
        </div>
        <div class="field">
          <label for="oemErrorCode"><span class="step-label">Paso 2</span>Código de error que da la máquina</label>
          <input id="oemErrorCode" type="text" maxlength="40" autocomplete="off" placeholder="Ejemplo: E8">
        </div>
        <div class="field">
          <label for="oemErrorLocation">Dónde aparece el error (opcional)</label>
          <select id="oemErrorLocation">
            <option value="">No lo sé</option>
            <option value="mando de pared">Mando de pared</option>
            <option value="display de la unidad interior">Display de la unidad interior</option>
            <option value="placa interior o sus pilotos">Placa interior o sus pilotos</option>
            <option value="display de la unidad exterior">Display de la unidad exterior</option>
            <option value="placa exterior o sus pilotos">Placa exterior o sus pilotos</option>
          </select>
        </div>
        <button type="submit">Buscar errores posibles</button>
      </form>
      <p class="oem-coverage">${catalog.meta.pattern_count} patrones · ${catalog.meta.oem_count} fabricantes/plataformas · ${catalog.meta.ambiguous_pattern_count} formatos bloqueados por ser insuficientes.</p>
      <div id="oemResults" class="oem-results"><div class="empty"><strong>Aquí aparecerán todas las posibilidades.</strong><p>La aplicación no decidirá por ti ni abrirá automáticamente el primer significado.</p></div></div>
    </div></section>`;
    document.getElementById('oemLookupForm').addEventListener('submit', event => {
      event.preventDefault();
      runOemLookup(catalog).catch(showError);
    });
    revealResults();
  } catch (error) { showError(error); }
}

async function selectTopic(id) {
  id = Number(id);
  if (!id) return;
  loading('Cargando variantes…');
  try {
    const data = await api('topic', {brand:state.brand, topic_id:id});
    state.topic = data.topic;
    if (data.topic.category?.slug) {
      state.category = state.categories.find(item => item.slug === data.topic.category.slug) || state.category;
      els.category.value = data.topic.category.slug;
      state.topics = state.category?.topics || state.topics;
      els.topic.innerHTML = '<option value="">Selecciona un tema</option>' + state.topics.map(topic => `<option value="${topic.id}">${esc(topic.title)} (${topic.variant_count || 0})</option>`).join('');
      els.topic.disabled = state.topics.length === 0;
    }
    els.topic.value = String(id);
    setBreadcrumb(state.brandName, data.topic.category?.name || state.category?.name, data.topic.title);
    els.context.classList.remove('hidden');
    els.context.innerHTML = `<h2>${esc(localizedText(data.topic, 'title'))}</h2><p>${esc(localizedText(data.topic, 'summary'))}</p>`;
    renderTopic(data.topic);
    revealResults();
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
    <summary><span class="variant-title">${esc(localizedText(v, 'title'))}</span>${localizedText(v, 'recognition') ? `<span class="variant-recognition">Cómo reconocerla: ${esc(localizedText(v, 'recognition'))}</span>` : ''}</summary>
    <div class="card-body">
      ${chips ? `<div class="chips">${chips}</div>` : ''}
      ${localizedText(v, 'purpose') ? `<p><strong>Finalidad:</strong> ${esc(localizedText(v, 'purpose'))}</p>` : ''}
      ${localizedText(v, 'summary') ? `<p>${esc(localizedText(v, 'summary'))}</p>` : ''}
      ${renderController(v.controller)}
      ${renderSections(v.sections || [])}
      ${renderLedPatternTable(v.led_patterns || [])}
      ${renderSteps(v.steps || [])}
      ${renderParameters(v.parameters || [])}
      ${renderMonitoring(v.monitoring_points || [])}
      ${renderMedia(v.media || [])}
      ${renderSources(v.sources || [])}
    </div>
  </details>`;
}

function renderSections(sections) {
  return sections.map(s => `<details class="nested-detail" ${s.collapsed_default === 0 ? 'open' : ''}><summary>${esc(localizedText(s, 'title', sectionLabel(s.section_type)))}</summary><div class="nested-content">${formatBody(localizedText(s, 'body'))}</div></details>`).join('');
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
  return Object.entries(grouped).map(([phase, items]) => `<details class="nested-detail" open><summary>${esc(phaseLabel(phase))}</summary><div class="nested-content"><ol class="procedure-list">${items.map(s => `<li class="${s.warning_level === 'danger' ? 'danger-box' : s.warning_level === 'warning' || s.warning_level === 'caution' ? 'warning-box' : ''}">${esc(localizedText(s, 'instruction'))}${localizedText(s, 'expected_result') ? `<span class="expected">Resultado esperado: ${esc(localizedText(s, 'expected_result'))}</span>` : ''}</li>`).join('')}</ol></div></details>`).join('');
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
    rememberRecent({type:'error', id:e.id, code:e.code_display, title:localizedText(e, 'short_label', 'Código de error')});
    setBreadcrumb(state.brandName, 'Errores y protecciones', e.code_display);
    els.context.classList.remove('hidden');
    els.context.innerHTML = `<h2><span class="code-badge">${esc(e.code_display)}</span>${esc(localizedText(e, 'short_label', 'Código de error'))}</h2><p>${esc(scopeLabel(e.unit_scope))}. Se muestran todas las interpretaciones documentadas.</p>`;
    els.content.innerHTML = renderErrorDetail(e);
    bindMediaButtons();
    revealResults();
  } catch (error) { showError(error); }
}

function renderErrorDetail(e) {
  const aliases = (e.aliases || []).map(a => a.alias_display).filter(a => a !== e.code_display);
  const interpretations = e.interpretations || [];
  const hasMultipleInterpretations = interpretations.length > 1;
  return `<section class="result-card"><div class="card-body">
    <div class="chips">${chip(indicationLabel(e.indication_type))}${chip(scopeLabel(e.unit_scope))}${aliases.length ? chip('Variantes: '+aliases.join(', ')) : ''}</div>
    ${hasMultipleInterpretations ? `<div class="notice-box interpretation-choice"><strong>${interpretations.length} posibles significados documentados</strong><p>Ninguno está preseleccionado. Revise la lista y abra la interpretación que mejor coincida con la máquina y el lugar donde se ha leído el código.</p></div>` : ''}
    ${interpretations.map(i => `<details class="variant-card" ${hasMultipleInterpretations ? '' : 'open'}><summary><span class="variant-title">${esc(localizedText(i, 'title'))}</span>${localizedText(i, 'description') ? `<span class="variant-recognition">${esc(localizedText(i, 'description'))}</span>` : ''}</summary><div class="card-body">
      <div class="chips">${chip(sourceKind(i.source_kind),'official')}${chip('Fiabilidad: '+confidenceLabel(i.confidence))}</div>
      ${renderIndicationContexts(i.indication_contexts || [])}
      ${renderRelatedErrors(i)}
      ${renderInfoItems(i.info_items || [])}
      ${renderImpacts(i.operational_impacts || [])}
      ${renderDatasets(i.datasets || [])}
      ${renderSources(i.sources || [])}
    </div></details>`).join('')}
    ${renderMedia(e.media || [])}
  </div></section>`;
}
function renderIndicationContexts(items) {
  if (!items.length) return '';
  const hasEquivalent = items.some(item => item.related_error_id);
  const hasLedPatterns = items.some(item => Array.isArray(item.led_indicators) && item.led_indicators.length);
  return `<details class="nested-detail info-priority" open><summary>${hasEquivalent ? 'Dónde aparece y qué código equivalente buscar' : 'Dónde aparece este código'}</summary><div class="nested-content">
    ${hasEquivalent ? '<div class="notice-box"><strong>El código puede cambiar según dónde se lea</strong><p>Compruebe si el dato procede del mando, del display de la unidad o de una placa antes de elegir la interpretación.</p></div>' : ''}
    <div class="table-wrap"><table><thead><tr><th>Código mostrado</th><th>Dónde se lee</th><th>Familia o pista</th><th>Relación</th></tr></thead><tbody>${items.map(item => `<tr>
      <td>${item.related_error_id ? `<button type="button" data-open-error="${esc(item.related_error_id)}"><span class="code-badge">${esc(item.code_display)}</span></button>` : `<span class="code-badge">${esc(item.code_display)}</span>`}</td>
      <td>${esc(item.display_location || '')}</td>
      <td>${esc(item.family_hint || '')}</td>
      <td>${esc(item.relationship || '')}</td>
    </tr>`).join('')}</tbody></table></div>
    ${hasLedPatterns ? renderLedPatternTable(items.filter(item => Array.isArray(item.led_indicators) && item.led_indicators.length)) : ''}
  </div></details>`;
}
function renderLedPatternTable(items) {
  const stateLabel = value => ({
    on:'Encendido fijo', off:'Apagado', blink:'Parpadea',
    fast_blink:'Parpadeo rápido', slow_blink:'Parpadeo lento',
    pulse:'Número de destellos', alternate:'Alterna',
  }[value] || value || 'No indicado');
  const indicator = row => {
    const color = String(row.color || 'neutral').toLowerCase();
    const state = String(row.state || 'off').toLowerCase();
    const detail = row.detail ? ` · ${row.detail}` : '';
    return `<span class="led-pattern-item"><span class="led-indicator led-${esc(color)} led-state-${esc(state)}" aria-hidden="true"></span><span><strong>${esc(row.label || row.color || 'LED')}:</strong> ${esc(stateLabel(state))}${esc(detail)}</span></span>`;
  };
  return `<details class="nested-detail led-pattern-detail" open><summary>Tabla de pilotos de la placa exterior</summary><div class="nested-content">
    <div class="notice-box"><strong>Lea el ciclo completo antes de decidir</strong><p>Fijo, apagado y parpadeando son estados distintos. Anote también el orden, la pausa y el número de destellos si el manual los utiliza.</p></div>
    <div class="table-wrap"><table class="led-pattern-table"><thead><tr><th>Código o estado</th><th>Patrón de pilotos</th><th>Significado y lectura</th></tr></thead><tbody>${items.map(item => `<tr>
      <td><span class="code-badge">${esc(item.code_display || '')}</span><br>${esc(item.display_location || '')}</td>
      <td><div class="led-pattern">${item.led_indicators.map(indicator).join('')}</div></td>
      <td>${item.relationship ? `<p class="led-meaning"><strong>Significado:</strong> ${esc(item.relationship)}</p>` : ''}${item.counting_rule || item.cycle_note || item.sequence ? `<details class="led-reading-note"><summary>Cómo leer esta fila</summary>${item.counting_rule ? `<p><strong>Conteo:</strong> ${esc(item.counting_rule)}</p>` : ''}${item.cycle_note ? `<p><strong>Ciclo:</strong> ${esc(item.cycle_note)}</p>` : ''}${item.sequence ? `<p><strong>Secuencia:</strong> ${esc(item.sequence)}</p>` : ''}</details>` : ''}</td>
    </tr>`).join('')}</tbody></table></div>
  </div></details>`;
}
function renderRelatedErrors(interpretation) {
  const related = interpretation.related_errors || [];
  if (!related.length) return '';
  return `<div class="notice-box"><strong>Este código agrupa variantes más concretas</strong>${interpretation.routing_note ? `<p>${esc(interpretation.routing_note)}</p>` : ''}<div class="chips">${related.map(item => `<button type="button" data-open-error="${esc(item.id)}"><span class="code-badge">${esc(item.code_display)}</span>${esc(item.label || 'Abrir subcódigo')}</button>`).join('')}</div></div>`;
}
function renderInfoItems(items) {
  if (!items.length) return '';
  const groups = items.reduce((a,x)=>((a[x.item_type||'observation']??=[]).push(x),a),{});
  const order = ['machine_behavior', 'related_element', 'cause', 'check', 'safety', 'observation'];
  return order.filter(type => groups[type]?.length).map(type => {
    const rows = groups[type];
    const open = ['machine_behavior', 'cause', 'check'].includes(type) ? 'open' : '';
    const priority = type === 'machine_behavior' ? ' info-priority' : '';
    return `<details class="nested-detail${priority}" ${open}><summary>${esc(itemTypeLabel(type))}</summary><div class="nested-content"><ul>${rows.map(x => `<li>${localizedText(x, 'title') ? `<strong>${esc(localizedText(x, 'title'))}:</strong> ` : ''}${esc(localizedText(x, 'body'))}</li>`).join('')}</ul></div></details>`;
  }).join('');
}
function renderImpacts(items) {
  if (!items.length) return '';
  return `<details class="nested-detail" open><summary>Efecto sobre el funcionamiento</summary><div class="nested-content">${items.map(x => `<div class="notice-box"><strong>${esc(localizedText(x, 'summary', stopLabel(x.stop_level)))}</strong>${localizedText(x, 'affected_scope') ? `<p><strong>Afecta a:</strong> ${esc(localizedText(x, 'affected_scope'))}</p>` : ''}${localizedText(x, 'unaffected_scope') ? `<p><strong>Sigue funcionando:</strong> ${esc(localizedText(x, 'unaffected_scope'))}</p>` : ''}${localizedText(x, 'restart_behavior') ? `<p><strong>Recuperación:</strong> ${esc(localizedText(x, 'restart_behavior'))}</p>` : ''}${localizedText(x, 'degraded_behavior') ? `<p><strong>Modo degradado:</strong> ${esc(localizedText(x, 'degraded_behavior'))}</p>` : ''}${localizedText(x, 'notes') ? `<p>${esc(localizedText(x, 'notes'))}</p>` : ''}</div>`).join('')}</div></details>`;
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
    els.content.innerHTML = data.results.length ? data.results.map(r => `<article class="search-hit"><h3>${r.type === 'error' ? '<span class="code-badge">Error</span>' : ''}${esc(r.title)}</h3><p>${esc(r.category)}${r.summary ? ` — ${esc(r.summary)}` : ''}</p><button type="button" ${r.type === 'error' ? `data-open-error="${r.id}"` : `data-open-variant="${r.id}"`}>Abrir ficha</button></article>`).join('') : `<div class="empty"><strong>“${esc(query)}” no está incluido todavía en la base de ${esc(state.brandName)}.</strong><p>No es un fallo del buscador: será necesario añadir la ficha correspondiente a los datos de esta marca.</p></div>`;
    revealResults();
  } catch (error) { showError(error); }
}

async function openVariant(id) {
  loading('Cargando ficha técnica…');
  try {
    const data = await api('variant', {brand:state.brand, variant_id:id});
    rememberRecent({type:'variant', id:data.variant.id, title:data.variant.title});
    setBreadcrumb(state.brandName, data.topic.category?.name, data.topic.title, data.variant.title);
    els.context.classList.remove('hidden');
    els.context.innerHTML = `<h2>${esc(data.variant.title)}</h2><p>${esc(data.variant.recognition || data.variant.summary || '')}</p>`;
    els.content.innerHTML = renderVariant(data.variant, true);
    bindMediaButtons();
    revealResults();
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
    revealResults();
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
function scopeLabel(v) { return ({
  indoor:'Unidad interior', outdoor:'Unidad exterior', controller:'Mando o controlador',
  system:'Sistema', general:'General', mixed:'Varios ámbitos',
  unknown:'Ámbito no especificado'
}[v] || v || ''); }
function sourceKind(v) { return ({official:'Dato oficial',calculated:'Valor calculado',workshop_experience:'Experiencia de taller',technical_hypothesis:'Hipótesis técnica'}[v] || v || ''); }
function confidenceLabel(v) { return ({high:'alta',medium:'media',low:'baja',unknown:'no indicada'}[v] || v || ''); }
function indicationLabel(v) { return ({
  display:'Display', outdoor_display:'Display exterior', led:'LED/parpadeos',
  outdoor_led:'Pilotos de la exterior', controller:'Mando', remote_controller:'Mando',
  app:'Aplicación', mixed:'Indicación combinada', other:'Otra indicación'
}[v] || v || ''); }
function sectionLabel(v) { return ({wiring:'Cableado',notes:'Observaciones',safety:'Seguridad',operation:'Funcionamiento',checks:'Comprobaciones',behavior:'Comportamiento'}[v] || 'Información'); }
function phaseLabel(v) { return ({
  access:'Acceso', active_error:'Error activo', address:'Direccionamiento', cancel:'Cancelación',
  check:'Comprobaciones', checklist:'Lista de comprobación', classification:'Clasificación', classify:'Clasificación',
  configure:'Configuración', connection:'Conexión', cooling:'En frío o deshumidificación', correct:'Corrección',
  diagnosis:'Diagnóstico', erase:'Borrado', erase_automatic:'Borrado automático', erase_manual:'Borrado manual',
  exit:'Salir', finish:'Finalización', group:'Control de grupo', history:'Historial', interpret:'Interpretación',
  interpretation:'Interpretación', isolation:'Aislamiento de la avería', measurement:'Medición', monitoring:'Monitorización',
  navigation:'Navegación', network:'Red de comunicación', observation:'Observación', other_modes:'Otros modos',
  power:'Alimentación', precheck:'Comprobaciones previas', prepare:'Preparación', prerequisites:'Antes de empezar',
  procedure:'Procedimiento', programming:'Programación', read:'Lectura', recognition:'Cómo reconocerlo',
  record:'Registrar datos', recovery:'Recuperación', restart:'Reinicio', result:'Interpretación del resultado',
  safety:'Seguridad', start:'Inicio', stop:'Parada', timing:'Temporización', verification:'Verificación',
  verify:'Verificación', warning:'Advertencias',
}[v] || v || 'Procedimiento'); }
function itemTypeLabel(v) { return ({related_element:'Elementos relacionados',cause:'Posibles causas',check:'Comprobaciones',observation:'Observaciones',safety:'Seguridad',machine_behavior:'Comportamiento de la máquina'}[v] || v); }
function stopLabel(v) { return ({all_system:'Se detiene todo el sistema',affected_unit:'Se detiene la unidad afectada',branch:'Se detiene una rama o grupo',outdoor_only:'Se detiene la unidad exterior',degraded:'Funcionamiento degradado',unknown:'Efecto no especificado'}[v] || v || 'Efecto operativo'); }

els.brand.addEventListener('change', () => selectBrand(els.brand.value));
els.category.addEventListener('change', () => els.category.value && selectCategory(els.category.value));
els.topic.addEventListener('change', () => els.topic.value && selectTopic(els.topic.value));
els.searchForm.addEventListener('submit', event => { event.preventDefault(); const q = els.search.value.trim(); if (q.length >= 2 && state.brand) globalSearch(q); });
els.homeButton.addEventListener('click', showHome);
els.coverageButton.addEventListener('click', showCoverage);
els.oemFinderButton?.addEventListener('click', showOemFinder);
els.closeImageDialog.addEventListener('click', () => els.imageDialog.close());
els.imageDialog.addEventListener('click', event => { if (event.target === els.imageDialog) els.imageDialog.close(); });
document.addEventListener('click', event => {
  const quickButton = event.target.closest('[data-quick-query]');
  if (quickButton) {
    const query = quickButton.dataset.quickQuery || '';
    els.search.value = query;
    if (query.length >= 2 && state.brand) globalSearch(query);
  }
  const categoryButton = event.target.closest('[data-open-category]');
  if (categoryButton) {
    els.category.value = categoryButton.dataset.openCategory;
    selectCategory(categoryButton.dataset.openCategory);
  }
  const oemButton = event.target.closest('[data-open-oem]');
  if (oemButton) showOemFinder();
  const oemErrorButton = event.target.closest('[data-open-oem-error]');
  if (oemErrorButton) {
    const brand = oemErrorButton.dataset.oemBrand;
    const errorId = oemErrorButton.dataset.openOemError;
    if (brand && installedBrands.has(brand) && errorId) {
      els.brand.value = brand;
      selectBrand(brand).then(() => openError(errorId)).catch(showError);
    }
  }
  const topicButton = event.target.closest('[data-open-topic]'); if (topicButton) selectTopic(topicButton.dataset.openTopic);
  const errorButton = event.target.closest('[data-open-error]'); if (errorButton) openError(errorButton.dataset.openError);
  const variantButton = event.target.closest('[data-open-variant]'); if (variantButton) openVariant(variantButton.dataset.openVariant);
});

init();
