(() => {
  'use strict';
  const catalogUrl = 'data/regulations/catalog.json';
  const indexCache = new Map();
  let catalog;

  const el = id => document.getElementById(id);
  const escapeHtml = value => String(value).replace(/[&<>"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[char]));
  const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').replace(/[^a-z0-9]+/g, ' ').trim();
  const dateLabel = value => value ? new Date(`${value}T12:00:00Z`).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' }) : 'sin fecha';

  async function getJson(url) {
    const response = await fetch(url, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`No se ha podido abrir ${url}.`);
    return response.json();
  }

  async function getIndex(document) {
    if (!indexCache.has(document.id)) indexCache.set(document.id, getJson(document.index_url));
    return indexCache.get(document.id);
  }

  function renderDocuments() {
    const pages = catalog.documents.reduce((sum, document) => sum + document.page_count, 0);
    el('catalogStatus').textContent = `${catalog.documents.length} REGLAMENTOS · ${pages.toLocaleString('es-ES')} PÁGINAS`;
    el('librarySummary').textContent = `${catalog.documents.length} documentos, ${pages.toLocaleString('es-ES')} páginas con texto consultable. Verificados el ${dateLabel(catalog.verified_at)}.`;
    el('legalNotice').textContent = catalog.notice;
    el('documentSelect').insertAdjacentHTML('beforeend', catalog.documents.map(document => `<option value="${document.id}">${escapeHtml(document.short_title)} · ${escapeHtml(document.legal_reference)}</option>`).join(''));
    el('documentGrid').innerHTML = catalog.documents.map(document => `
      <article class="rg-doc-card">
        <div class="rg-doc-head"><span class="rg-doc-code">${escapeHtml(document.short_title)}</span><span class="rg-doc-date">OFICIAL<br>actualizado ${dateLabel(document.last_official_update)}</span></div>
        <h3>${escapeHtml(document.title)}</h3><p>${escapeHtml(document.legal_reference)} · ${escapeHtml(document.authority)}</p>
        <div class="rg-doc-topics">${document.topics.slice(0, 6).map(topic => `<span>${escapeHtml(topic)}</span>`).join('')}</div>
        <div class="rg-doc-foot"><small>${document.page_count} páginas · copia verificada</small><a href="${document.local_pdf}" target="_blank" rel="noopener">Abrir PDF</a></div>
        <details><summary>Edición, fuente y alcance</summary><div><a href="${document.official_page_url}" target="_blank" rel="noopener">Página oficial</a><a href="${document.local_pdf}" target="_blank" rel="noopener">Copia guardada</a></div>${document.version_note ? `<p>${escapeHtml(document.version_note)}</p>` : ''}</details>
      </article>`).join('');
    el('referencedStandards').innerHTML = (catalog.referenced_not_stored || []).map(item => `<div class="rg-standard-item"><b>${escapeHtml(item.family)}</b><br><small>${escapeHtml(item.reason)}</small></div>`).join('');

    const topics = ['ICT', 'calderas', 'automatismos', 'ventilación', 'recuperación de calor', 'extracción de humos', 'gases fluorados', 'puesta a tierra'];
    el('topicButtons').innerHTML = topics.map(topic => `<button type="button">${topic}</button>`).join('');
    el('topicButtons').querySelectorAll('button').forEach(button => button.addEventListener('click', () => {
      el('queryInput').value = button.textContent;
      el('searchForm').requestSubmit();
    }));
  }

  function score(record, phrase, tokens) {
    const haystack = record.search || normalize(record.text);
    let value = haystack.includes(phrase) ? 120 : 0;
    let matched = 0;
    tokens.forEach(token => {
      const first = haystack.indexOf(token);
      if (first >= 0) {
        matched += 1;
        value += 18;
        if (first < 180) value += 3;
        value += Math.min(12, haystack.split(token).length - 1);
      }
    });
    if (matched !== tokens.length) return 0;
    if (/\b(articulo|it|if|hs)\b/.test(phrase)) value += 8;
    return value;
  }

  function highlighted(text, query) {
    let output = escapeHtml(text);
    const words = [...new Set(String(query).match(/[\p{L}\p{N}]+/gu) || [])].filter(word => word.length >= 3).sort((a, b) => b.length - a.length);
    words.forEach(word => {
      const safe = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      output = output.replace(new RegExp(`(${safe})`, 'giu'), '<mark>$1</mark>');
    });
    return output;
  }

  function renderResults(results, query) {
    el('resultsPanel').hidden = false;
    el('resultCount').textContent = `${results.length} resultado${results.length === 1 ? '' : 's'} mostrado${results.length === 1 ? '' : 's'}`;
    if (!results.length) {
      el('resultList').innerHTML = '<article class="rg-result-card"><p>No aparece esa expresión en los documentos seleccionados. Prueba con menos palabras o con otro término técnico.</p></article>';
      return;
    }
    el('resultList').innerHTML = results.map(item => `
      <article class="rg-result-card">
        <div class="rg-result-meta"><b>${escapeHtml(item.document.short_title)} · ${escapeHtml(item.document.legal_reference)}</b><span>PÁGINA ${item.record.page}</span></div>
        <p>${highlighted(item.record.text, query)}</p>
        <div class="rg-result-actions"><a href="${item.document.local_pdf}#page=${item.record.page}" target="_blank" rel="noopener">Abrir esta página en el PDF</a><a href="${item.document.official_page_url}" target="_blank" rel="noopener">Comprobar fuente oficial</a></div>
      </article>`).join('');
    el('resultsPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function search(event) {
    event.preventDefault();
    const query = el('queryInput').value.trim();
    const phrase = normalize(query);
    const tokens = [...new Set(phrase.split(' ').filter(token => token.length >= 2))];
    if (!tokens.length) return;
    const selected = el('documentSelect').value;
    const documents = selected === 'all' ? catalog.documents : catalog.documents.filter(document => document.id === selected);
    el('searchMessage').textContent = `Buscando en ${documents.length} documento${documents.length === 1 ? '' : 's'}…`;
    try {
      const indexes = await Promise.all(documents.map(getIndex));
      const found = [];
      indexes.forEach((index, indexPosition) => {
        index.records.forEach(record => {
          const rank = score(record, phrase, tokens);
          if (rank) found.push({ rank, record, document: documents[indexPosition] });
        });
      });
      found.sort((a, b) => b.rank - a.rank || a.record.page - b.record.page);
      const uniquePages = [];
      const seen = new Set();
      for (const item of found) {
        const key = `${item.document.id}:${item.record.page}`;
        if (seen.has(key)) continue;
        seen.add(key); uniquePages.push(item);
        if (uniquePages.length === 30) break;
      }
      renderResults(uniquePages, query);
      el('searchMessage').textContent = selected === 'all' ? 'Búsqueda completada en toda la biblioteca.' : `Búsqueda completada en ${documents[0].short_title}.`;
      const url = new URL(location.href); url.searchParams.set('q', query); url.searchParams.set('doc', selected); history.replaceState(null, '', url);
    } catch (error) {
      el('searchMessage').textContent = error.message || 'No se ha podido completar la búsqueda.';
    }
  }

  async function init() {
    try {
      catalog = await getJson(catalogUrl);
      renderDocuments();
      el('searchForm').addEventListener('submit', search);
      const params = new URLSearchParams(location.search);
      const initialQuery = params.get('q');
      const initialDocument = params.get('doc');
      if (initialDocument && (initialDocument === 'all' || catalog.documents.some(document => document.id === initialDocument))) el('documentSelect').value = initialDocument;
      if (initialQuery) { el('queryInput').value = initialQuery; el('searchForm').requestSubmit(); }
    } catch (error) {
      el('catalogStatus').textContent = 'BIBLIOTECA NO DISPONIBLE';
      el('librarySummary').textContent = error.message || 'No se ha podido cargar el catálogo.';
    }
  }

  init();
})();
