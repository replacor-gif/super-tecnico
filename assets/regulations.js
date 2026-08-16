(() => {
  'use strict';
  const catalogUrl = 'data/regulations/catalog.json';
  const indexCache = new Map();
  const state = { catalog: null, requestId: '', serverSearch: false };
  const searchStopWords = new Set(['a','al','ante','bajo','con','contra','de','del','desde','durante','e','el','en','entre','hacia','hasta','la','las','lo','los','o','para','por','que','segun','sin','sobre','tras','un','una','unos','unas','y','como','cual','cuales','cuando','cuanto','cuantos','donde','quien','quienes','debe','deben','deberia','deberian','puedo','puede','pueden','necesito','necesita','necesitan','tener','tiene','tienen','hay','saber','dime','indica','indicar','exige','exigido','norma','normativa','reglamento','tecnico','tecnica']);
  const termAliases = {
    cable: ['conductor','conductores'], cables: ['conductor','conductores'], conductor: ['cable','cables'], conductores: ['cable','cables'],
    voltaje: ['tension'], tension: ['voltaje'], diferencial: ['interruptor diferencial','proteccion diferencial'],
    magnetotermico: ['interruptor automatico','pequeno interruptor automatico','pia'], tierra: ['puesta a tierra'], aterramiento: ['puesta a tierra'],
    desague: ['evacuacion de aguas','saneamiento'], desagues: ['evacuacion de aguas','saneamiento'], acondicionado: ['climatizacion'], climatizacion: ['aire acondicionado'],
    extractor: ['extraccion','ventilacion'], extraccion: ['extractor','ventilacion'], refrigerante: ['gas fluorado'], refrigerantes: ['gases fluorados'],
    frigorias: ['potencia frigorifica','carga termica'], seccion: ['dimensionado'], dimensionado: ['seccion'], caudal: ['flujo'], flujo: ['caudal'],
  };

  const el = id => document.getElementById(id);
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').replace(/[^a-z0-9]+/g, ' ').trim();
  const dateLabel = value => value ? new Date(`${value}T12:00:00Z`).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' }) : 'sin fecha';
  const domainLabel = value => String(value || '').replaceAll('_', ' ').replace(/\b\p{L}/gu, letter => letter.toLocaleUpperCase('es'));
  const escapeRegExp = value => String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  function tokenVariants(token) {
    const variants = [token, ...(termAliases[token] || [])];
    if (token.length > 5 && token.endsWith('es')) variants.push(token.slice(0, -2));
    if (token.length > 4 && token.endsWith('s')) variants.push(token.slice(0, -1));
    return [...new Set(variants.filter(value => value.length >= 2))];
  }

  function queryTokens(phrase) {
    const raw = [...new Set(phrase.split(' ').filter(token => token.length >= 2))];
    const useful = raw.filter(token => !searchStopWords.has(token));
    return useful.length ? useful : raw;
  }

  function termPosition(haystack, term) {
    for (const variant of tokenVariants(term)) {
      const suffix = variant.length === 2 || variant.endsWith('s') ? '' : '(?:es|s)?';
      const position = haystack.search(new RegExp(`(?:^| )${escapeRegExp(variant)}${suffix}(?: |$)`));
      if (position >= 0) return position;
    }
    return -1;
  }

  function matchDetails(haystack, tokens) {
    const positions = tokens.map(token => termPosition(haystack, token)).filter(position => position >= 0);
    return {
      matched: positions.length,
      first: positions.length ? Math.min(...positions) : Number.MAX_SAFE_INTEGER,
      span: positions.length > 1 ? Math.max(...positions) - Math.min(...positions) : Number.MAX_SAFE_INTEGER,
      coverage: tokens.length ? positions.length / tokens.length : 0,
    };
  }

  function regulationLocator(text) {
    const heading = String(text || '').match(/\b((?:ITC|IF)[-\s]?[A-Z]{0,5}[-\s]?\d{1,3}(?:\.\d+)?)\s+[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{4,}/u);
    if (heading) return heading[1].replace(/\s+/g, ' ').trim();
    const patterns = [/\bArt[ií]culo\s+\d+(?:\.\d+)?(?:\s*[a-z])?/iu, /\b(?:Apartado|Secci[oó]n|Tabla)\s+[A-Z]{0,3}\s*\d+(?:\.\d+)*/iu];
    for (const pattern of patterns) {
      const match = String(text || '').match(pattern);
      if (match) return match[0].replace(/\s+/g, ' ').trim();
    }
    return '';
  }

  function specificScope(haystack, query) {
    const scopes = {
      mueble: 'muebles eléctricos', 'vehiculo electrico': 'recarga de vehículo eléctrico', 'alumbrado exterior': 'alumbrado exterior',
      piscina: 'piscinas y fuentes', caravana: 'caravanas', sauna: 'saunas', quirofano: 'quirófanos',
      'instalacion provisional': 'instalaciones provisionales', feria: 'ferias y stands', puerto: 'puertos y marinas', tierra: 'puesta a tierra', proyecto: 'documentación y proyecto', 'unidad tematica': 'programa formativo',
    };
    for (const [needle, label] of Object.entries(scopes)) {
      if (haystack.includes(needle) && !query.includes(needle)) return {penalty: 65, hint: label};
    }
    return {penalty: 0, hint: ''};
  }

  function queryRefinement(query) {
    if (query.includes('seccion') && (query.includes('cable') || query.includes('conductor'))) {
      return {message: 'La sección depende del circuito y del uso. Añade el destino para acotar la prescripción aplicable.', suggested_terms: ['alumbrado','tomas de corriente','derivación individual','tierra','recarga de vehículo']};
    }
    if (query.includes('ventilacion') && !query.includes('local') && !query.includes('vivienda')) {
      return {message: 'La ventilación cambia según el uso del recinto. Añade el tipo de edificio o local.', suggested_terms: ['vivienda','garaje','local comercial','sala de máquinas']};
    }
    return null;
  }

  async function getJson(url) {
    const response = await fetch(url, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`No se ha podido abrir ${url}.`);
    return response.json();
  }

  async function getIndex(document) {
    if (!indexCache.has(document.id)) indexCache.set(document.id, getJson(document.index_url));
    return indexCache.get(document.id);
  }

  function filteredDocuments() {
    const domain = el('domainSelect').value;
    return domain === 'all' ? state.catalog.documents : state.catalog.documents.filter(document => document.domain === domain);
  }

  function refreshDocumentOptions(preserve = true) {
    const previous = preserve ? el('documentSelect').value : 'all';
    const documents = filteredDocuments();
    el('documentSelect').innerHTML = '<option value="all">Todos los reglamentos</option>' + documents.map(document => `<option value="${document.id}">${escapeHtml(document.short_title)} · ${escapeHtml(document.legal_reference)}</option>`).join('');
    el('documentSelect').value = documents.some(document => document.id === previous) ? previous : 'all';
  }

  function renderDocuments() {
    const catalog = state.catalog;
    const pages = catalog.documents.reduce((sum, document) => sum + document.page_count, 0);
    el('catalogStatus').textContent = `${catalog.documents.length} REGLAMENTOS · ${pages.toLocaleString('es-ES')} PÁGINAS`;
    el('librarySummary').textContent = `${catalog.documents.length} documentos y ${pages.toLocaleString('es-ES')} páginas con texto consultable. Verificados el ${dateLabel(catalog.verified_at)}.`;
    el('legalNotice').textContent = catalog.notice;
    const domains = [...new Set(catalog.documents.map(document => document.domain))].sort((left, right) => domainLabel(left).localeCompare(domainLabel(right), 'es'));
    el('domainSelect').insertAdjacentHTML('beforeend', domains.map(domain => `<option value="${domain}">${escapeHtml(domainLabel(domain))}</option>`).join(''));
    refreshDocumentOptions(false);
    el('documentGrid').innerHTML = catalog.documents.map(document => `
      <article class="rg-doc-card">
        <div class="rg-doc-head"><span class="rg-doc-code">${escapeHtml(document.short_title)}</span><span class="rg-doc-date">OFICIAL<br>actualizado ${dateLabel(document.last_official_update)}</span></div>
        <h3>${escapeHtml(document.title)}</h3><p>${escapeHtml(document.legal_reference)} · ${escapeHtml(document.authority)}</p>
        <div class="rg-doc-topics">${document.topics.slice(0, 6).map(topic => `<span>${escapeHtml(topic)}</span>`).join('')}</div>
        <div class="rg-doc-foot"><small>${document.page_count} páginas · copia verificada</small><a href="${document.local_pdf}" target="_blank" rel="noopener">Abrir PDF</a></div>
        <details><summary>Edición, fuente y alcance</summary><div><a href="${document.official_page_url}" target="_blank" rel="noopener">Página oficial</a><a href="${document.local_pdf}" target="_blank" rel="noopener">Copia guardada</a></div>${document.version_note ? `<p>${escapeHtml(document.version_note)}</p>` : ''}</details>
      </article>`).join('');
    el('referencedStandards').innerHTML = (catalog.referenced_not_stored || []).map(item => `<div class="rg-standard-item"><b>${escapeHtml(item.family)}</b><br><small>${escapeHtml(item.reason)}</small></div>`).join('');

    const topics = ['caída de tensión', 'puesta a tierra', 'ventilación', 'recuperación de calor', 'extracción de humos', 'gases fluorados', 'calderas', 'ICT'];
    el('topicButtons').innerHTML = topics.map(topic => `<button type="button">${topic}</button>`).join('');
    el('topicButtons').querySelectorAll('button').forEach(button => button.addEventListener('click', () => {
      el('queryInput').value = button.textContent;
      el('searchForm').requestSubmit();
    }));
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

  function resultModeLabel(mode) {
    if (mode === 'exact') return 'Frase exacta';
    if (mode === 'related') return 'Coincidencias relacionadas';
    if (mode === 'all_terms') return 'Todas las palabras';
    return 'Sin coincidencias';
  }

  function relevanceLabel(item, mode) {
    if (mode === 'exact') return 'TEXTO EXACTO';
    if (Number(item.term_coverage) >= .999) return 'COINCIDEN TODOS LOS CONCEPTOS';
    if (Number(item.term_coverage) >= .7) return 'COINCIDENCIA ALTA';
    return 'RESULTADO RELACIONADO';
  }

  function renderResults(payload, query) {
    const result = payload.result || { items: [], returned: 0, candidate_pages: 0, match_mode: 'none' };
    const items = result.items || [];
    state.requestId = payload.request_id || '';
    state.serverSearch = Boolean(payload.request_id);
    el('resultsPanel').hidden = false;
    el('resultCount').textContent = items.length ? `${resultModeLabel(result.match_mode)} · ${items.length} mostrados de ${result.candidate_pages || items.length}` : 'Sin resultados';
    if (!items.length) {
      el('resultList').innerHTML = `<article class="rg-result-card rg-empty-result"><b>No aparece esa consulta en la selección actual.</b><p>Prueba a quitar una palabra, desactivar «frase exacta» o buscar en todas las áreas.</p><div class="rg-empty-actions"><button type="button" data-broaden>Buscar en toda la biblioteca</button></div></article>`;
      el('resultList').querySelector('[data-broaden]').addEventListener('click', () => {
        el('domainSelect').value = 'all'; refreshDocumentOptions(false); el('exactPhrase').checked = false; el('searchForm').requestSubmit();
      });
      return;
    }
    const refinement = result.refinement ? `<aside class="rg-refinement"><b>Para afinar la respuesta</b><p>${escapeHtml(result.refinement.message)}</p><div>${(result.refinement.suggested_terms || []).map(term => `<button type="button" data-refine="${escapeHtml(term)}">+ ${escapeHtml(term)}</button>`).join('')}</div></aside>` : '';
    el('resultList').innerHTML = refinement + items.map((item, index) => `
      <article class="rg-result-card${index === 0 ? ' is-best' : ''}">
        <div class="rg-result-rank"><span>${index === 0 ? 'PRIMERA COINCIDENCIA' : relevanceLabel(item, result.match_mode)}</span><div>${item.scope_hint ? `<em>Ámbito: ${escapeHtml(item.scope_hint)}</em>` : ''}${item.locator ? `<b>${escapeHtml(item.locator)}</b>` : ''}</div></div>
        <div class="rg-result-meta"><b>${escapeHtml(item.short_title)} · ${escapeHtml(item.legal_reference)}</b><span>PÁGINA ${item.page}</span></div>
        <p>${highlighted(item.text, query)}</p>
        <div class="rg-evidence-row"><span>EVIDENCIA DOCUMENTAL</span><small>${escapeHtml(item.authority)} · ${escapeHtml(domainLabel(item.domain))} · ${relevanceLabel(item, result.match_mode).toLocaleLowerCase('es')}</small></div>
        <div class="rg-result-actions"><a data-result-open href="${escapeHtml(item.local_pdf_path)}${escapeHtml(item.local_pdf_fragment || `#page=${item.page}`)}" target="_blank" rel="noopener">Abrir esta página en el PDF</a><a href="${escapeHtml(item.official_page_url)}" target="_blank" rel="noopener">Comprobar fuente oficial</a></div>
      </article>`).join('');
    el('resultList').querySelectorAll('[data-refine]').forEach(button => button.addEventListener('click', () => {
      const addition = button.dataset.refine || '';
      if (!normalize(el('queryInput').value).includes(normalize(addition))) el('queryInput').value = `${el('queryInput').value.trim()} ${addition}`;
      el('searchForm').requestSubmit();
    }));
    el('resultList').querySelectorAll('[data-result-open]').forEach(link => link.addEventListener('click', recordResultOpen, { once: true }));
    el('resultsPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function recordResultOpen() {
    if (!state.serverSearch || !state.requestId || !window.ST_COMMUNITY_API) return;
    try { await window.ST_COMMUNITY_API.request('regulation-result-open', { method: 'POST', body: { request_id: state.requestId } }); } catch (_) { /* La apertura nunca debe bloquear el documento. */ }
  }

  function localScore(record, phrase, tokens, exactPhrase, related = false) {
    const haystack = record.search || normalize(record.text);
    const phraseFound = haystack.includes(phrase);
    if (exactPhrase) return phraseFound ? {rank: 320, matched: tokens.length, coverage: 1} : null;
    const details = matchDetails(haystack, tokens);
    const minimum = related ? Math.max(2, Math.ceil(tokens.length * .55)) : tokens.length;
    if (details.matched < minimum) return null;
    let rank = (phraseFound ? 220 : 0) + (details.matched * 28) + (details.first < 180 ? 10 : 0);
    if (details.span <= 350) rank += 28;
    else if (details.span <= 900) rank += 12;
    if (haystack.includes('indice')) rank -= Number(record.page) <= 6 ? 90 : 35;
    const scope = specificScope(haystack, phrase);
    rank -= scope.penalty;
    return {rank, matched: details.matched, coverage: details.coverage, scopeHint: scope.hint};
  }

  async function localSearch(query, documentId, domain, exactPhrase, limit) {
    const phrase = normalize(query);
    const tokens = queryTokens(phrase);
    const documents = state.catalog.documents.filter(document => (documentId === 'all' || document.id === documentId) && (domain === 'all' || document.domain === domain));
    const indexes = await Promise.all(documents.map(getIndex));
    const found = [];
    let matchMode = exactPhrase ? 'exact' : 'all_terms';
    const collect = related => indexes.forEach((index, indexPosition) => index.records.forEach(record => {
      const score = localScore(record, phrase, tokens, exactPhrase, related);
      if (!score) return;
      const document = documents[indexPosition];
      const metadata = normalize([document.short_title, document.title, document.legal_reference, document.domain, ...(document.topics || [])].join(' '));
      let metadataBoost = 0;
      tokens.forEach(token => { if (termPosition(metadata, token) >= 0) metadataBoost += 3; });
      found.push({rank: score.rank + metadataBoost, matched: score.matched, coverage: score.coverage, scopeHint: score.scopeHint, document, record});
    }));
    collect(false);
    if (!found.length && !exactPhrase && tokens.length >= 3) {
      matchMode = 'related';
      collect(true);
    }
    found.sort((left, right) => right.rank - left.rank || left.record.page - right.record.page);
    const seen = new Set();
    const items = [];
    found.forEach(item => {
      const key = `${item.document.id}:${item.record.page}`;
      if (seen.has(key)) return;
      seen.add(key);
      if (items.length >= limit) return;
      items.push({
        document_id: item.document.id, document_title: item.document.title, short_title: item.document.short_title,
        legal_reference: item.document.legal_reference, authority: item.document.authority, domain: item.document.domain,
        page: item.record.page, text: item.record.text, locator: regulationLocator(item.record.text), scope_hint: item.scopeHint || '',
        matched_terms: item.matched, term_coverage: item.coverage, relevance_score: Math.max(0, Math.min(1, item.rank / 320)), local_pdf_path: item.document.local_pdf,
        local_pdf_fragment: `#page=${item.record.page}`, official_page_url: item.document.official_page_url,
        source_sha256: item.document.sha256, source_content_sha256: item.document.content_sha256, evidence_level: 'document_hit',
      });
    });
    return { ok: true, status: items.length ? 'success' : 'not_found', result: { items, returned: items.length, candidate_pages: seen.size, match_mode: items.length ? matchMode : 'none', refinement: queryRefinement(phrase) }, warnings: [] };
  }

  async function search(event) {
    event.preventDefault();
    const query = el('queryInput').value.trim();
    if (query.length < 2) return;
    const documentId = el('documentSelect').value;
    const domain = el('domainSelect').value;
    const exactPhrase = el('exactPhrase').checked;
    el('searchMessage').textContent = 'Buscando en la biblioteca oficial…';
    el('searchForm').classList.add('is-searching');
    try {
      let payload;
      try {
        if (!window.ST_COMMUNITY_API) throw Object.assign(new Error('api_unavailable'), { code: 'api_unavailable' });
        payload = await window.ST_COMMUNITY_API.request('regulation-search', { query: {
          q: query, document_id: documentId === 'all' ? '' : documentId, domain: domain === 'all' ? '' : domain,
          exact_phrase: exactPhrase ? '1' : '0', limit: 20, client_type: 'human',
        }, headers: { 'X-ST-Client-Type': 'human' } });
      } catch (error) {
        const fallbackCodes = ['api_unavailable', 'invalid_response', 'server_not_configured', 'database_unavailable'];
        if (!fallbackCodes.includes(error.code) && error.status !== 404) throw error;
        payload = await localSearch(query, documentId, domain, exactPhrase, 20);
        el('searchMessage').textContent = 'Búsqueda local completada. Las estadísticas anónimas no están disponibles en esta copia.';
      }
      renderResults(payload, query);
      if (payload.request_id) {
        const time = payload.usage?.latency_ms ? ` en ${payload.usage.latency_ms} ms` : '';
        el('searchMessage').textContent = payload.result.match_mode === 'related' ? `No aparecieron todas las palabras juntas; mostramos páginas relacionadas${time}.` : `Búsqueda completada con fuentes y páginas verificables${time}.`;
      }
      const url = new URL(location.href);
      url.searchParams.set('q', query); url.searchParams.set('doc', documentId); url.searchParams.set('domain', domain);
      exactPhrase ? url.searchParams.set('exact', '1') : url.searchParams.delete('exact');
      history.replaceState(null, '', url);
    } catch (error) {
      el('searchMessage').textContent = error.code === 'rate_limited' ? 'Has alcanzado el límite temporal de la fase gratuita. Podrás volver a buscar dentro de una hora.' : 'No se ha podido completar la búsqueda. Inténtalo de nuevo en unos segundos.';
    } finally {
      el('searchForm').classList.remove('is-searching');
    }
  }

  async function init() {
    try {
      state.catalog = await getJson(catalogUrl);
      renderDocuments();
      el('domainSelect').addEventListener('change', () => refreshDocumentOptions());
      el('searchForm').addEventListener('submit', search);
      const params = new URLSearchParams(location.search);
      const initialDomain = params.get('domain');
      if (initialDomain && (initialDomain === 'all' || state.catalog.documents.some(document => document.domain === initialDomain))) {
        el('domainSelect').value = initialDomain; refreshDocumentOptions(false);
      }
      const initialDocument = params.get('doc');
      if (initialDocument && (initialDocument === 'all' || state.catalog.documents.some(document => document.id === initialDocument))) el('documentSelect').value = initialDocument;
      el('exactPhrase').checked = params.get('exact') === '1';
      const initialQuery = params.get('q');
      if (initialQuery) { el('queryInput').value = initialQuery; el('searchForm').requestSubmit(); }
    } catch (error) {
      el('catalogStatus').textContent = 'BIBLIOTECA NO DISPONIBLE';
      el('librarySummary').textContent = error.message || 'No se ha podido cargar el catálogo.';
    }
  }

  init();
})();
