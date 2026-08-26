(() => {
  'use strict';

  const STATUS_ENDPOINT = 'api/index.php?action=electroia-public-status';
  const SEARCH_ENDPOINT = 'api/index.php?action=electroia-symbol-search';
  const RELEASE_REPORT = 'data/electroia/public-release-readiness.json';
  const GALLERY_MANIFEST = 'data/electroia/public-gallery.json';
  const SYMBOL_LIBRARY = 'data/electroia/symbol-library.json';
  const elements = {};

  async function readJson(url, options = {}) {
    const response = await fetch(url, { credentials: 'same-origin', ...options });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  function normalize(value) {
    return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleUpperCase('es').replace(/[^A-Z0-9]+/g, ' ').trim();
  }

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = String(value);
  }

  async function loadStatus() {
    try {
      const payload = await readJson(STATUS_ENDPOINT, { headers: { 'X-ST-Client-Type': 'human' } });
      const quality = payload.quality || {};
      setText('eiaReviewedCount', quality.reviewed_symbols ?? 501);
      setText('eiaExampleCount', quality.professional_examples ?? 5);
      setText('eiaConflictCount', Number(quality.component_overlaps || 0) + Number(quality.wire_component_conflicts || 0) + Number(quality.dangerous_warnings || 0));
    } catch (_) {
      try {
        const report = await readJson(RELEASE_REPORT);
        setText('eiaReviewedCount', report.summary?.reviewed_symbols ?? 501);
        setText('eiaExampleCount', report.summary?.professional_examples ?? 5);
        setText('eiaConflictCount', Number(report.summary?.component_overlaps || 0) + Number(report.summary?.wire_component_conflicts || 0) + Number(report.summary?.dangerous_warnings || 0));
      } catch (_) {}
    }
  }

  function createMetric(text, className = '') {
    const span = document.createElement('span');
    span.textContent = text;
    if (className) span.className = className;
    return span;
  }

  function openDiagram(item) {
    elements.dialogTitle.textContent = item.title;
    elements.dialogKind.textContent = `${item.document_kind_label} · ${item.standard_profile.replace('_', ' ')}`;
    elements.dialogImage.src = item.image;
    elements.dialogImage.alt = `Plano patrón: ${item.title}`;
    elements.dialogMetrics.textContent = `${item.components} componentes · ${item.nets} redes · ${item.terminals} terminales · 1 lienzo`;
    elements.dialogSource.href = item.source;
    if (typeof elements.dialog.showModal === 'function') elements.dialog.showModal();
    else elements.dialog.setAttribute('open', '');
  }

  function renderGalleryItem(item) {
    const article = document.createElement('article');
    article.className = 'eia-diagram-card';
    const preview = document.createElement('button');
    preview.type = 'button';
    preview.className = 'eia-diagram-preview';
    preview.setAttribute('aria-label', `Ampliar ${item.title}`);
    const image = document.createElement('img');
    image.src = item.image;
    image.alt = `Vista previa del plano ${item.title}`;
    image.loading = 'lazy';
    preview.append(image);
    preview.addEventListener('click', () => openDiagram(item));

    const copy = document.createElement('div');
    copy.className = 'eia-diagram-copy';
    const kind = document.createElement('small');
    kind.textContent = `${item.document_kind_label} · REV. ${item.revision}`;
    const title = document.createElement('h3');
    title.textContent = item.title;
    const metrics = document.createElement('div');
    metrics.className = 'eia-diagram-metrics';
    metrics.append(
      createMetric(`${item.components} componentes`),
      createMetric(`${item.nets} redes`),
      createMetric('0 errores', 'is-pass'),
      createMetric('1 lienzo', 'is-pass'),
    );
    const actions = document.createElement('div');
    actions.className = 'eia-diagram-actions';
    const expand = document.createElement('button');
    expand.type = 'button';
    expand.textContent = 'Ampliar plano';
    expand.addEventListener('click', () => openDiagram(item));
    const source = document.createElement('a');
    source.href = item.source;
    source.textContent = 'Ver JSON';
    actions.append(expand, source);
    copy.append(kind, title, metrics, actions);
    article.append(preview, copy);
    return article;
  }

  async function loadGallery() {
    try {
      const manifest = await readJson(GALLERY_MANIFEST);
      elements.gallery.replaceChildren(...manifest.items.map(renderGalleryItem));
      if (manifest.notice) elements.galleryNotice.textContent = manifest.notice;
    } catch (_) {
      elements.gallery.innerHTML = '<div class="eia-gallery-loading">No se han podido cargar los planos. Inténtalo de nuevo cuando recuperes la conexión.</div>';
    }
  }

  function renderSymbol(item) {
    const article = document.createElement('article');
    article.className = 'eia-symbol-card';
    const header = document.createElement('header');
    const title = document.createElement('h3');
    title.textContent = item.name;
    const id = document.createElement('small');
    id.textContent = item.id;
    title.append(id);
    const reviewed = document.createElement('span');
    reviewed.textContent = 'REVISADO';
    header.append(title, reviewed);
    const category = document.createElement('p');
    category.textContent = [item.category, item.subcategory].filter(Boolean).join(' · ');
    const meta = document.createElement('div');
    meta.className = 'eia-symbol-meta';
    meta.append(
      createMetric(`Designador ${item.designator || '—'}`),
      createMetric(`${item.terminal_count || 0} terminales`),
    );
    if (Array.isArray(item.terminal_names) && item.terminal_names.length) meta.append(createMetric(item.terminal_names.join(' · ')));
    article.append(header, category, meta);
    if (item.requires_exact_model) {
      const warning = document.createElement('p');
      warning.className = 'eia-symbol-warning';
      warning.textContent = 'Bloque funcional: exige el modelo exacto antes de asignar pines físicos.';
      article.append(warning);
    }
    return article;
  }

  async function localSymbolSearch(query) {
    const library = await readJson(SYMBOL_LIBRARY);
    const terms = normalize(query).split(' ').filter((term) => term.length > 1);
    const items = (library.symbols || []).filter((item) => {
      if (item.review_status !== 'engine_reviewed' || !item.catalog_id) return false;
      const haystack = normalize([item.id, item.name, item.category, item.subcategory, item.aliases, item.keywords, item.description].join(' '));
      return terms.every((term) => haystack.includes(term));
    }).slice(0, 8).map((item) => ({
      id: item.id,
      name: item.name,
      category: item.category,
      subcategory: item.subcategory,
      designator: item.designator,
      terminal_names: Object.keys(item.ports || {}),
      terminal_count: Object.keys(item.ports || {}).length,
      requires_exact_model: item.requires_exact_model === true,
    }));
    return { items, total: items.length, offline: true };
  }

  async function searchSymbols(query) {
    const clean = query.trim();
    elements.searchHelp.classList.remove('is-error');
    if (clean.length < 2) {
      elements.searchHelp.textContent = 'Escribe al menos dos caracteres para buscar.';
      elements.searchHelp.classList.add('is-error');
      elements.query.focus();
      return;
    }
    elements.searchButton.disabled = true;
    elements.searchButton.textContent = 'Buscando…';
    elements.resultTitle.textContent = `Buscando “${clean}”`;
    elements.resultCount.textContent = '';
    try {
      let payload;
      try {
        payload = await readJson(`${SEARCH_ENDPOINT}&q=${encodeURIComponent(clean)}&limit=8`, { headers: { 'X-ST-Client-Type': 'human' } });
      } catch (_) {
        payload = await localSymbolSearch(clean);
      }
      const items = payload.items || [];
      elements.resultTitle.textContent = items.length ? `Resultados para “${clean}”` : `Sin coincidencias para “${clean}”`;
      elements.resultCount.textContent = `${payload.total ?? items.length} ${Number(payload.total ?? items.length) === 1 ? 'coincidencia' : 'coincidencias'}${payload.offline ? ' · modo local' : ''}`;
      elements.searchHelp.textContent = payload.offline ? 'La API no respondió; se ha consultado la copia local revisada.' : 'Consulta registrada de forma anónima para ayudarnos a priorizar mejoras.';
      if (items.length) elements.results.replaceChildren(...items.map(renderSymbol));
      else elements.results.innerHTML = '<div class="eia-empty"><span aria-hidden="true">?</span><p>Prueba con la función, la familia o un nombre más general.</p></div>';
    } catch (_) {
      elements.resultTitle.textContent = 'No se pudo completar la búsqueda';
      elements.results.innerHTML = '<div class="eia-empty"><span aria-hidden="true">!</span><p>Comprueba la conexión e inténtalo de nuevo.</p></div>';
      elements.searchHelp.textContent = 'La biblioteca no está disponible en este momento.';
      elements.searchHelp.classList.add('is-error');
    } finally {
      elements.searchButton.disabled = false;
      elements.searchButton.textContent = 'Buscar';
    }
  }

  function init() {
    Object.assign(elements, {
      form: document.getElementById('eiaSearchForm'),
      query: document.getElementById('eiaQuery'),
      searchButton: document.querySelector('#eiaSearchForm button[type="submit"]'),
      searchHelp: document.getElementById('eiaSearchHelp'),
      resultTitle: document.getElementById('eiaResultTitle'),
      resultCount: document.getElementById('eiaResultCount'),
      results: document.getElementById('eiaSymbolResults'),
      gallery: document.getElementById('eiaGallery'),
      galleryNotice: document.getElementById('eiaGalleryNotice'),
      dialog: document.getElementById('eiaDiagramDialog'),
      dialogTitle: document.getElementById('eiaDialogTitle'),
      dialogKind: document.getElementById('eiaDialogKind'),
      dialogImage: document.getElementById('eiaDialogImage'),
      dialogMetrics: document.getElementById('eiaDialogMetrics'),
      dialogSource: document.getElementById('eiaDialogSource'),
    });
    elements.form.addEventListener('submit', (event) => { event.preventDefault(); searchSymbols(elements.query.value); });
    document.querySelectorAll('[data-eia-query]').forEach((button) => button.addEventListener('click', () => {
      elements.query.value = button.dataset.eiaQuery;
      searchSymbols(elements.query.value);
    }));
    document.getElementById('eiaDialogClose').addEventListener('click', () => elements.dialog.close());
    elements.dialog.addEventListener('click', (event) => { if (event.target === elements.dialog) elements.dialog.close(); });
    loadStatus();
    loadGallery();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
