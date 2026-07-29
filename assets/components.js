'use strict';

(() => {
  const messages = {
    es: {
      subtitle: 'Referencias electrónicas',
      smdTool: 'Identificador SMD',
      eyebrow: 'Electrónica · consulta documental',
      hero: 'Busca una referencia o marcado',
      heroText: 'Localiza candidatos, compara fabricante, encapsulado, parámetros y fuente. Ningún resultado se considera sustituto directo automáticamente.',
      loading: 'Cargando catálogo…',
      ready: '{components} referencias · {reviewed} revisadas',
      loadError: 'No se pudo cargar el catálogo',
      searchTitle: 'Referencia, componente o marcado SMD',
      searchText: 'Escribe el código completo cuando lo conozcas. Para marcados cortos mostraremos todas las coincidencias posibles.',
      queryLabel: 'Referencia o marcado',
      try: 'Prueba:',
      filters: 'Filtros opcionales',
      category: 'Categoría',
      manufacturer: 'Fabricante',
      package: 'Encapsulado',
      minVoltage: 'Tensión mínima documentada',
      minCurrent: 'Corriente mínima documentada',
      reviewedOnly: 'Solo registros oficiales o revisados',
      searchButton: 'Buscar referencias',
      emptyTitle: 'Aquí aparecerán las coincidencias',
      emptyText: 'La aplicación mostrará primero la lista completa. Tú decides qué ficha abrir y contrastar.',
      method: 'Método recomendado',
      confirm: 'Confirma antes de sustituir',
      function: 'Función y tecnología',
      functionText: 'No compares solo tensión y corriente.',
      pinout: 'Patillaje',
      pinoutText: 'Comprueba símbolo, orden y orientación.',
      packageText: 'Verifica huella, aislamiento y disipación.',
      conditions: 'Condiciones',
      conditionsText: 'Respeta temperatura, tensión de mando y condiciones de ensayo.',
      coverage: 'Cobertura de esta versión',
      references: 'Referencias',
      reviewed: 'Oficiales o revisadas',
      historical: 'Históricas pendientes',
      parameters: 'Parámetros',
      important: 'Importante',
      warning: 'Los registros históricos ayudan a localizar candidatos, pero deben cotejarse con el datasheet del fabricante exacto. Una coincidencia no demuestra compatibilidad.',
      footer: 'Catálogo técnico de consulta; no recomienda sustituciones automáticas.',
      all: 'Todos',
      results: '{count} coincidencias para “{query}”',
      noResults: 'No hay coincidencias con esos datos.',
      noResultsText: 'Prueba otra escritura, elimina filtros o comunica la referencia para incorporarla.',
      limited: 'Se muestran los primeros {shown} de {total} resultados. Añade fabricante, encapsulado o más caracteres para acotar.',
      exactPart: 'Referencia exacta',
      exactAlias: 'Alias exacto',
      exactMarking: 'Marcado SMD exacto',
      partPrefix: 'Familia o referencia relacionada',
      textMatch: 'Coincidencia documental',
      open: 'Abrir ficha',
      loadingDetail: 'Cargando ficha completa…',
      detailError: 'No se pudo cargar la ficha completa.',
      confirmed: 'Confirmado',
      high: 'Alta confianza',
      probable: 'Probable',
      pending: 'Pendiente de verificar',
      pendingWarning: 'Registro histórico pendiente de verificación. Úsalo para localizar candidatos y comprueba fabricante, encapsulado, patillaje y datasheet antes de decidir.',
      substitutionWarning: 'La ficha es informativa. No implica equivalencia ni sustitución directa.',
      identification: 'Identificación',
      electrical: 'Datos eléctricos',
      packagesPinout: 'Encapsulados y patillaje',
      markings: 'Marcados SMD',
      applications: 'Aplicaciones',
      source: 'Fuente documental',
      related: 'Relacionados o equivalentes',
      verification: 'Revisión pendiente',
      description: 'Descripción',
      subtype: 'Subtipo',
      lifecycle: 'Estado del ciclo de vida',
      confidence: 'Confianza interna',
      datasheet: 'Abrir datasheet',
      sourceOpen: 'Abrir fuente',
      compareSmd: 'Comprobar este marcado en el identificador SMD',
      noElectrical: 'No hay parámetros eléctricos estructurados para esta variante.',
      min: 'Mínimo',
      typical: 'Típico',
      max: 'Máximo',
      value: 'Valor',
      unit: 'Unidad',
      testConditions: 'Condiciones de medida',
      pin: 'Pin',
      symbol: 'Símbolo',
      role: 'Función',
      compatibility: 'Nivel de relación',
      exactManufacturer: 'Confirma el fabricante exacto: una misma referencia puede cambiar de patillaje o parámetros.',
    },
    en: {
      subtitle: 'Electronic references', smdTool: 'SMD identifier', eyebrow: 'Electronics · document lookup',
      hero: 'Search a reference or marking', heroText: 'Find candidates and compare manufacturer, package, parameters and source. Results are never treated as automatic direct replacements.',
      loading: 'Loading catalogue…', ready: '{components} references · {reviewed} reviewed', loadError: 'The catalogue could not be loaded',
      searchTitle: 'Reference, component or SMD marking', searchText: 'Enter the full code when known. Short markings return every possible match.',
      queryLabel: 'Reference or marking', try: 'Try:', filters: 'Optional filters', category: 'Category', manufacturer: 'Manufacturer',
      package: 'Package', minVoltage: 'Minimum documented voltage', minCurrent: 'Minimum documented current',
      reviewedOnly: 'Official or reviewed records only', searchButton: 'Search references',
      emptyTitle: 'Matches will appear here', emptyText: 'The complete list is shown first. You decide which record to open and verify.',
      method: 'Recommended method', confirm: 'Confirm before replacing', function: 'Function and technology',
      functionText: 'Do not compare voltage and current only.', pinout: 'Pinout', pinoutText: 'Check symbols, order and orientation.',
      packageText: 'Verify footprint, insulation and dissipation.', conditions: 'Conditions',
      conditionsText: 'Respect temperature, drive voltage and test conditions.', coverage: 'Current coverage',
      references: 'References', reviewed: 'Official or reviewed', historical: 'Historical, pending', parameters: 'Parameters',
      important: 'Important', warning: 'Historical records help locate candidates, but must be checked against the exact manufacturer datasheet. A match does not prove compatibility.',
      footer: 'Technical lookup catalogue; it does not recommend automatic replacements.', all: 'All',
      results: '{count} matches for “{query}”', noResults: 'No matches with those details.',
      noResultsText: 'Try another spelling, remove filters or report the missing reference.', limited: 'Showing the first {shown} of {total} results. Add a manufacturer, package or more characters.',
      exactPart: 'Exact reference', exactAlias: 'Exact alias', exactMarking: 'Exact SMD marking',
      partPrefix: 'Related family or reference', textMatch: 'Document match', open: 'Open record',
      loadingDetail: 'Loading full record…', detailError: 'The full record could not be loaded.',
      confirmed: 'Confirmed', high: 'High confidence', probable: 'Probable', pending: 'Pending verification',
      pendingWarning: 'Historical record pending verification. Use it to locate candidates and check manufacturer, package, pinout and datasheet before deciding.',
      substitutionWarning: 'This record is informative. It does not imply equivalence or a direct replacement.',
      identification: 'Identification', electrical: 'Electrical data', packagesPinout: 'Packages and pinout',
      markings: 'SMD markings', applications: 'Applications', source: 'Document source', related: 'Related or equivalent',
      verification: 'Pending review', description: 'Description', subtype: 'Subtype', lifecycle: 'Lifecycle status',
      confidence: 'Internal confidence', datasheet: 'Open datasheet', sourceOpen: 'Open source',
      compareSmd: 'Check this marking in the SMD identifier', noElectrical: 'No structured electrical parameters are available for this variant.',
      min: 'Minimum', typical: 'Typical', max: 'Maximum', value: 'Value', unit: 'Unit', testConditions: 'Test conditions',
      pin: 'Pin', symbol: 'Symbol', role: 'Function', compatibility: 'Relationship level',
      exactManufacturer: 'Confirm the exact manufacturer: the same reference may use different pinouts or parameters.',
    },
    pt: {
      subtitle: 'Referências eletrónicas', smdTool: 'Identificador SMD', eyebrow: 'Eletrónica · consulta documental',
      hero: 'Procure uma referência ou marcação', heroText: 'Localize candidatos e compare fabricante, encapsulamento, parâmetros e fonte. Nenhum resultado é considerado substituto direto automaticamente.',
      loading: 'A carregar catálogo…', ready: '{components} referências · {reviewed} revistas', loadError: 'Não foi possível carregar o catálogo',
      searchTitle: 'Referência, componente ou marcação SMD', searchText: 'Introduza o código completo quando o conhecer. As marcações curtas mostram todas as coincidências.',
      queryLabel: 'Referência ou marcação', try: 'Experimente:', filters: 'Filtros opcionais', category: 'Categoria', manufacturer: 'Fabricante',
      package: 'Encapsulamento', minVoltage: 'Tensão mínima documentada', minCurrent: 'Corrente mínima documentada',
      reviewedOnly: 'Apenas registos oficiais ou revistos', searchButton: 'Procurar referências',
      emptyTitle: 'As coincidências aparecerão aqui', emptyText: 'Primeiro verá a lista completa. Decida qual ficha abrir e verificar.',
      method: 'Método recomendado', confirm: 'Confirme antes de substituir', function: 'Função e tecnologia',
      functionText: 'Não compare apenas tensão e corrente.', pinout: 'Pinagem', pinoutText: 'Verifique símbolos, ordem e orientação.',
      packageText: 'Verifique footprint, isolamento e dissipação.', conditions: 'Condições',
      conditionsText: 'Respeite temperatura, tensão de comando e condições de ensaio.', coverage: 'Cobertura desta versão',
      references: 'Referências', reviewed: 'Oficiais ou revistas', historical: 'Históricas pendentes', parameters: 'Parâmetros',
      important: 'Importante', warning: 'Os registos históricos ajudam a localizar candidatos, mas devem ser confirmados no datasheet do fabricante exato. Uma coincidência não prova compatibilidade.',
      footer: 'Catálogo técnico de consulta; não recomenda substituições automáticas.', all: 'Todos',
      results: '{count} coincidências para “{query}”', noResults: 'Não há coincidências com esses dados.',
      noResultsText: 'Experimente outra escrita, retire filtros ou comunique a referência em falta.', limited: 'São mostrados os primeiros {shown} de {total}. Adicione fabricante, encapsulamento ou mais caracteres.',
      exactPart: 'Referência exata', exactAlias: 'Alias exato', exactMarking: 'Marcação SMD exata',
      partPrefix: 'Família ou referência relacionada', textMatch: 'Coincidência documental', open: 'Abrir ficha',
      loadingDetail: 'A carregar ficha completa…', detailError: 'Não foi possível carregar a ficha completa.',
      confirmed: 'Confirmado', high: 'Alta confiança', probable: 'Provável', pending: 'Pendente de verificação',
      pendingWarning: 'Registo histórico pendente de verificação. Use-o para localizar candidatos e confirme fabricante, encapsulamento, pinagem e datasheet.',
      substitutionWarning: 'A ficha é informativa. Não implica equivalência nem substituição direta.',
      identification: 'Identificação', electrical: 'Dados elétricos', packagesPinout: 'Encapsulamentos e pinagem',
      markings: 'Marcações SMD', applications: 'Aplicações', source: 'Fonte documental', related: 'Relacionados ou equivalentes',
      verification: 'Revisão pendente', description: 'Descrição', subtype: 'Subtipo', lifecycle: 'Estado do ciclo de vida',
      confidence: 'Confiança interna', datasheet: 'Abrir datasheet', sourceOpen: 'Abrir fonte',
      compareSmd: 'Verificar esta marcação no identificador SMD', noElectrical: 'Não existem parâmetros elétricos estruturados para esta variante.',
      min: 'Mínimo', typical: 'Típico', max: 'Máximo', value: 'Valor', unit: 'Unidade', testConditions: 'Condições de medida',
      pin: 'Pino', symbol: 'Símbolo', role: 'Função', compatibility: 'Nível de relação',
      exactManufacturer: 'Confirme o fabricante exato: a mesma referência pode ter pinagem ou parâmetros diferentes.',
    },
    fr: {
      subtitle: 'Références électroniques', smdTool: 'Identificateur SMD', eyebrow: 'Électronique · recherche documentaire',
      hero: 'Recherchez une référence ou un marquage', heroText: 'Trouvez les candidats et comparez fabricant, boîtier, paramètres et source. Aucun résultat n’est considéré automatiquement comme remplacement direct.',
      loading: 'Chargement du catalogue…', ready: '{components} références · {reviewed} vérifiées', loadError: 'Impossible de charger le catalogue',
      searchTitle: 'Référence, composant ou marquage SMD', searchText: 'Saisissez le code complet si vous le connaissez. Un marquage court affiche toutes les correspondances.',
      queryLabel: 'Référence ou marquage', try: 'Essayez :', filters: 'Filtres facultatifs', category: 'Catégorie', manufacturer: 'Fabricant',
      package: 'Boîtier', minVoltage: 'Tension minimale documentée', minCurrent: 'Courant minimal documenté',
      reviewedOnly: 'Uniquement les fiches officielles ou vérifiées', searchButton: 'Rechercher des références',
      emptyTitle: 'Les correspondances apparaîtront ici', emptyText: 'La liste complète s’affiche d’abord. Vous choisissez la fiche à ouvrir et à vérifier.',
      method: 'Méthode recommandée', confirm: 'Vérifiez avant de remplacer', function: 'Fonction et technologie',
      functionText: 'Ne comparez pas seulement tension et courant.', pinout: 'Brochage', pinoutText: 'Vérifiez symboles, ordre et orientation.',
      packageText: 'Vérifiez empreinte, isolation et dissipation.', conditions: 'Conditions',
      conditionsText: 'Respectez température, tension de commande et conditions d’essai.', coverage: 'Couverture de cette version',
      references: 'Références', reviewed: 'Officielles ou vérifiées', historical: 'Historiques en attente', parameters: 'Paramètres',
      important: 'Important', warning: 'Les fiches historiques aident à trouver des candidats, mais doivent être vérifiées dans le datasheet du fabricant exact. Une correspondance ne prouve pas la compatibilité.',
      footer: 'Catalogue technique de consultation ; il ne recommande pas de remplacement automatique.', all: 'Tous',
      results: '{count} correspondances pour « {query} »', noResults: 'Aucune correspondance avec ces critères.',
      noResultsText: 'Essayez une autre écriture, retirez les filtres ou signalez la référence manquante.', limited: 'Affichage des {shown} premiers résultats sur {total}. Ajoutez fabricant, boîtier ou caractères.',
      exactPart: 'Référence exacte', exactAlias: 'Alias exact', exactMarking: 'Marquage SMD exact',
      partPrefix: 'Famille ou référence liée', textMatch: 'Correspondance documentaire', open: 'Ouvrir la fiche',
      loadingDetail: 'Chargement de la fiche complète…', detailError: 'Impossible de charger la fiche complète.',
      confirmed: 'Confirmé', high: 'Confiance élevée', probable: 'Probable', pending: 'À vérifier',
      pendingWarning: 'Fiche historique en attente de vérification. Utilisez-la pour trouver des candidats puis vérifiez fabricant, boîtier, brochage et datasheet.',
      substitutionWarning: 'Cette fiche est informative. Elle n’implique ni équivalence ni remplacement direct.',
      identification: 'Identification', electrical: 'Données électriques', packagesPinout: 'Boîtiers et brochage',
      markings: 'Marquages SMD', applications: 'Applications', source: 'Source documentaire', related: 'Liés ou équivalents',
      verification: 'Vérification en attente', description: 'Description', subtype: 'Sous-type', lifecycle: 'État du cycle de vie',
      confidence: 'Confiance interne', datasheet: 'Ouvrir le datasheet', sourceOpen: 'Ouvrir la source',
      compareSmd: 'Vérifier ce marquage dans l’identificateur SMD', noElectrical: 'Aucun paramètre électrique structuré pour cette variante.',
      min: 'Minimum', typical: 'Typique', max: 'Maximum', value: 'Valeur', unit: 'Unité', testConditions: 'Conditions de mesure',
      pin: 'Broche', symbol: 'Symbole', role: 'Fonction', compatibility: 'Niveau de relation',
      exactManufacturer: 'Confirmez le fabricant exact : une même référence peut avoir un brochage ou des paramètres différents.',
    },
  };

  const els = {
    status: document.getElementById('componentDatabaseStatus'),
    form: document.getElementById('componentSearchForm'),
    query: document.getElementById('componentQuery'),
    category: document.getElementById('componentCategory'),
    manufacturer: document.getElementById('componentManufacturer'),
    package: document.getElementById('componentPackage'),
    voltage: document.getElementById('componentVoltage'),
    current: document.getElementById('componentCurrent'),
    reviewed: document.getElementById('componentReviewed'),
    results: document.getElementById('componentResults'),
    coverage: document.getElementById('componentCoverage'),
  };
  const state = {catalog: null, results: [], query: '', chunks: new Map()};

  function lang() { return window.ST_I18N?.language || 'es'; }
  function tr(key, variables = {}) {
    const template = messages[lang()]?.[key] || messages.es[key] || key;
    return String(template).replace(/\{(\w+)\}/g, (_, name) => String(variables[name] ?? ''));
  }
  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
    })[character]);
  }
  function normalize(value) {
    return String(value ?? '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toUpperCase().replace(/[^A-Z0-9]+/g, '');
  }
  function locale() { return ({en: 'en-US', pt: 'pt-PT', fr: 'fr-FR', es: 'es-ES'})[lang()] || 'es-ES'; }
  function formatNumber(value, digits = 3) {
    return Number.isFinite(Number(value))
      ? Number(value).toLocaleString(locale(), {maximumFractionDigits: digits})
      : '—';
  }
  function formatSpecNumber(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return '—';
    const absolute = Math.abs(number);
    if (absolute !== 0 && (absolute < 1e-6 || absolute >= 1e9)) {
      return number.toExponential(4).replace(/\.?0+e/, 'e');
    }
    return number.toLocaleString(locale(), {maximumSignificantDigits: 7});
  }
  function applyOwnTranslations() {
    document.querySelectorAll('[data-component-i18n]').forEach(element => {
      element.textContent = tr(element.dataset.componentI18n);
    });
  }
  function optionMarkup(values) {
    return `<option value="">${escapeHtml(tr('all'))}</option>${values.map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join('')}`;
  }
  function qualityInfo(item) {
    if (item.official && String(item.quality).startsWith('oficial')) {
      return {label: tr('confirmed'), className: 'quality-confirmed'};
    }
    if (String(item.quality).startsWith('oficial') || item.quality === 'curado') {
      return {label: tr('high'), className: 'quality-high'};
    }
    if (item.quality === 'curado_serie') {
      return {label: tr('probable'), className: 'quality-probable'};
    }
    return {label: tr('pending'), className: 'quality-pending'};
  }
  function matchScore(item, query) {
    const normalizedQuery = normalize(query);
    const part = normalize(item.part_number);
    const aliases = (item.aliases || []).map(normalize);
    const markings = (item.markings || []).map(normalize);
    const haystack = normalize([
      item.part_number, item.manufacturer, item.category, item.subtype,
      item.description, ...(item.packages || []), ...(item.markings || []), ...(item.aliases || []),
    ].filter(Boolean).join(' '));
    let score = 0;
    let reason = '';
    if (part === normalizedQuery) { score = 1000; reason = tr('exactPart'); }
    else if (aliases.includes(normalizedQuery)) { score = 920; reason = tr('exactAlias'); }
    else if (markings.includes(normalizedQuery)) { score = 850; reason = tr('exactMarking'); }
    else if (part.startsWith(normalizedQuery) || aliases.some(value => value.startsWith(normalizedQuery))) {
      score = 650; reason = tr('partPrefix');
    } else if (haystack.includes(normalizedQuery)) {
      score = 400; reason = tr('textMatch');
    }
    if (!score) return null;
    score += item.official ? 90 : 0;
    score += Number(item.quality_rank || 0) * 8;
    score += Math.round(Number(item.confidence || 0) * 20);
    return {score, reason};
  }
  function passesFilters(item) {
    if (els.category.value && item.category !== els.category.value) return false;
    if (els.manufacturer.value && item.manufacturer !== els.manufacturer.value) return false;
    if (els.package.value && !(item.packages || []).includes(els.package.value)) return false;
    if (els.reviewed.checked && item.quality === 'histórico_extraído') return false;
    const minimumVoltage = Number(els.voltage.value);
    if (els.voltage.value && (!Number.isFinite(Number(item.voltage_max_v)) || Number(item.voltage_max_v) < minimumVoltage)) return false;
    const minimumCurrent = Number(els.current.value);
    if (els.current.value && (!Number.isFinite(Number(item.current_max_a)) || Number(item.current_max_a) < minimumCurrent)) return false;
    return true;
  }
  function updateUrl(query) {
    const url = new URL(window.location.href);
    if (query) url.searchParams.set('q', query);
    else url.searchParams.delete('q');
    history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
  }
  function resultMarkup(entry) {
    const item = entry.item;
    const quality = qualityInfo(item);
    const description = item.description || item.subtype || item.category || '';
    const packages = (item.packages || []).slice(0, 3);
    return `<details class="component-result" data-component-id="${item.id}">
      <summary>
        <span class="result-identity">
          <span class="result-reference">
            <strong>${escapeHtml(item.part_number)}</strong>
            <span class="quality-badge ${quality.className}">${escapeHtml(quality.label)}</span>
            <span class="meta-chip">${escapeHtml(entry.reason)}</span>
          </span>
          <p>${escapeHtml(item.manufacturer || '—')} · ${escapeHtml(item.category || '—')}${description ? ` · ${escapeHtml(description)}` : ''}</p>
          <span class="result-meta">
            ${packages.map(value => `<span class="meta-chip">${escapeHtml(value)}</span>`).join('')}
            ${(item.markings || []).slice(0, 4).map(value => `<span class="meta-chip">SMD ${escapeHtml(value)}</span>`).join('')}
            ${item.voltage_max_v != null && Number.isFinite(Number(item.voltage_max_v)) ? `<span class="meta-chip">${formatNumber(item.voltage_max_v)} V</span>` : ''}
            ${item.current_max_a != null && Number.isFinite(Number(item.current_max_a)) ? `<span class="meta-chip">${formatNumber(item.current_max_a)} A</span>` : ''}
          </span>
        </span>
        <span class="open-label" aria-label="${escapeHtml(tr('open'))}"></span>
      </summary>
      <div class="result-detail"><p class="loading-detail">${escapeHtml(tr('loadingDetail'))}</p></div>
    </details>`;
  }
  function renderResults() {
    const total = state.results.length;
    if (!total) {
      els.results.innerHTML = `<div class="component-empty"><div class="component-symbol" aria-hidden="true">?</div><h2>${escapeHtml(tr('noResults'))}</h2><p>${escapeHtml(tr('noResultsText'))}</p></div>`;
      return;
    }
    const visible = state.results.slice(0, 60);
    els.results.innerHTML = `
      <div class="results-heading"><div><h2>${escapeHtml(tr('results', {count: total, query: state.query}))}</h2><p>${escapeHtml(tr('substitutionWarning'))}</p></div></div>
      <div class="result-list">${visible.map(resultMarkup).join('')}</div>
      ${total > visible.length ? `<p class="results-limit">${escapeHtml(tr('limited', {shown: visible.length, total}))}</p>` : ''}`;
  }
  function runSearch() {
    if (!state.catalog) return;
    const query = els.query.value.trim();
    if (normalize(query).length < 2) {
      els.query.setCustomValidity('Introduce al menos dos caracteres.');
      els.query.reportValidity();
      return;
    }
    els.query.setCustomValidity('');
    state.query = query;
    state.results = state.catalog.components
      .filter(passesFilters)
      .map(item => {
        const match = matchScore(item, query);
        return match ? {item, ...match} : null;
      })
      .filter(Boolean)
      .sort((a, b) => b.score - a.score || String(a.item.part_number).localeCompare(String(b.item.part_number)));
    updateUrl(query);
    renderResults();
    els.results.scrollIntoView({behavior: 'smooth', block: 'start'});
  }
  function valueCell(specification) {
    if (specification.text_value) return escapeHtml(specification.text_value);
    const values = [
      specification.minimum_value,
      specification.typical_value,
      specification.maximum_value,
    ].filter(value => value !== null && value !== undefined);
    return values.length === 1 ? formatSpecNumber(values[0]) : '—';
  }
  function detailSection(title, body, open = false) {
    if (!body) return '';
    return `<details class="detail-block" ${open ? 'open' : ''}><summary>${escapeHtml(title)}</summary><div class="detail-content">${body}</div></details>`;
  }
  function renderSpecifications(items) {
    if (!items.length) return `<p>${escapeHtml(tr('noElectrical'))}</p>`;
    return `<div class="table-wrap"><table><thead><tr><th>${escapeHtml(tr('parameters'))}</th><th>${escapeHtml(tr('min'))}</th><th>${escapeHtml(tr('typical'))}</th><th>${escapeHtml(tr('max'))}</th><th>${escapeHtml(tr('value'))}</th><th>${escapeHtml(tr('unit'))}</th><th>${escapeHtml(tr('testConditions'))}</th></tr></thead><tbody>
      ${items.map(item => `<tr><td>${escapeHtml(item.name_es || item.spec_key)}</td><td>${item.minimum_value == null ? '—' : formatSpecNumber(item.minimum_value)}</td><td>${item.typical_value == null ? '—' : formatSpecNumber(item.typical_value)}</td><td>${item.maximum_value == null ? '—' : formatSpecNumber(item.maximum_value)}</td><td>${valueCell(item)}</td><td>${escapeHtml(item.unit || '')}</td><td>${escapeHtml(item.conditions || '')}</td></tr>`).join('')}
    </tbody></table></div>`;
  }
  function renderDetail(item) {
    const quality = qualityInfo(item);
    const identification = `
      <p><strong>${escapeHtml(item.part_number)}</strong> · ${escapeHtml(item.manufacturer || '—')}</p>
      ${item.description ? `<p><strong>${escapeHtml(tr('description'))}:</strong> ${escapeHtml(item.description)}</p>` : ''}
      ${item.subtype ? `<p><strong>${escapeHtml(tr('subtype'))}:</strong> ${escapeHtml(item.subtype)}</p>` : ''}
      ${item.lifecycle_status ? `<p><strong>${escapeHtml(tr('lifecycle'))}:</strong> ${escapeHtml(item.lifecycle_status)}</p>` : ''}
      <p><strong>${escapeHtml(tr('confidence'))}:</strong> ${formatNumber(Number(item.confidence || 0) * 100, 1)} % · <span class="quality-badge ${quality.className}">${escapeHtml(quality.label)}</span></p>
      <p>${escapeHtml(tr('exactManufacturer'))}</p>`;
    const packageRows = (item.package_details || []).map(value => `<li><strong>${escapeHtml(value.name)}</strong>${value.pin_count ? ` · ${escapeHtml(value.pin_count)} pins` : ''}${value.mount_type ? ` · ${escapeHtml(value.mount_type)}` : ''}${value.pinout_variant ? ` · ${escapeHtml(value.pinout_variant)}` : ''}</li>`).join('');
    const pinoutRows = (item.pinouts || []).length ? `<div class="table-wrap"><table><thead><tr><th>${escapeHtml(tr('package'))}</th><th>${escapeHtml(tr('pin'))}</th><th>${escapeHtml(tr('symbol'))}</th><th>${escapeHtml(tr('role'))}</th></tr></thead><tbody>${item.pinouts.map(pin => `<tr><td>${escapeHtml(pin.package || '')}</td><td>${escapeHtml(pin.pin_number)}</td><td>${escapeHtml(pin.pin_symbol || '')}</td><td>${escapeHtml(pin.function_es || '')}</td></tr>`).join('')}</tbody></table></div>` : '';
    const packageBody = packageRows || pinoutRows ? `${packageRows ? `<ul>${packageRows}</ul>` : ''}${pinoutRows}` : '';
    const markingBody = (item.marking_details || []).map(marking => `<li><strong>${escapeHtml(marking.marking)}</strong>${marking.package ? ` · ${escapeHtml(marking.package)}` : ''}${marking.pattern_kind ? ` · ${escapeHtml(marking.pattern_kind)}` : ''}</li>`).join('');
    const applicationsBody = (item.applications || []).map(application => `<li>${escapeHtml(application)}</li>`).join('');
    const source = item.source || {};
    const sourceBody = source.title || item.datasheet_url ? `
      ${source.title ? `<p><strong>${escapeHtml(source.title)}</strong>${source.publisher ? ` · ${escapeHtml(source.publisher)}` : ''}${source.type ? ` · ${escapeHtml(source.type)}` : ''}</p>` : ''}
      ${source.url ? `<a class="source-link" href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(tr('sourceOpen'))}</a>` : ''}
      ${item.datasheet_url ? `<a class="source-link" href="${escapeHtml(item.datasheet_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(tr('datasheet'))}</a>` : ''}` : '';
    const relatedBody = (item.equivalents || []).map(related => `<li><strong>${escapeHtml(related.part_number)}</strong>${related.manufacturer ? ` · ${escapeHtml(related.manufacturer)}` : ''} · ${escapeHtml(tr('compatibility'))}: ${escapeHtml(related.compatibility_level)}${related.notes_es ? ` · ${escapeHtml(related.notes_es)}` : ''}</li>`).join('');
    const verificationBody = (item.verification || []).map(entry => `<li>${escapeHtml(entry.reason_es)} · ${escapeHtml(entry.status)}</li>`).join('');
    const firstMarking = item.markings?.[0];
    return `
      ${item.quality === 'histórico_extraído' ? `<div class="detail-warning"><strong>${escapeHtml(tr('pending'))}</strong><p>${escapeHtml(tr('pendingWarning'))}</p></div>` : `<div class="detail-warning"><strong>${escapeHtml(tr('important'))}</strong><p>${escapeHtml(tr('substitutionWarning'))}</p></div>`}
      <div class="detail-grid">
        ${detailSection(tr('identification'), identification, true)}
        ${detailSection(tr('electrical'), renderSpecifications(item.specifications || []), true)}
        ${detailSection(tr('packagesPinout'), packageBody)}
        ${detailSection(tr('markings'), markingBody ? `<ul>${markingBody}</ul>${firstMarking ? `<a class="smd-cross-link" href="smd.html?q=${encodeURIComponent(firstMarking)}">${escapeHtml(tr('compareSmd'))}</a>` : ''}` : '')}
        ${detailSection(tr('applications'), applicationsBody ? `<ul>${applicationsBody}</ul>` : '')}
        ${detailSection(tr('source'), sourceBody)}
        ${detailSection(tr('related'), relatedBody ? `<ul>${relatedBody}</ul>` : '')}
        ${detailSection(tr('verification'), verificationBody ? `<ul>${verificationBody}</ul>` : '')}
      </div>`;
  }
  async function loadDetail(componentId) {
    const chunkId = Number(componentId) % Number(state.catalog.meta.chunk_count);
    if (!state.chunks.has(chunkId)) {
      state.chunks.set(chunkId, fetch(`data/components/details/${chunkId}.json`).then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      }));
    }
    const chunk = await state.chunks.get(chunkId);
    return chunk[String(componentId)];
  }
  async function openDetail(details) {
    const host = details.querySelector('.result-detail');
    if (details.dataset.loaded === 'true' || details.dataset.loading === 'true') return;
    details.dataset.loading = 'true';
    try {
      const item = await loadDetail(details.dataset.componentId);
      if (!item) throw new Error('missing detail');
      host.innerHTML = renderDetail(item);
      details.dataset.loaded = 'true';
    } catch (error) {
      console.error(error);
      host.innerHTML = `<div class="detail-warning">${escapeHtml(tr('detailError'))}</div>`;
    } finally {
      delete details.dataset.loading;
    }
  }
  function bindEvents() {
    els.form.addEventListener('submit', event => {
      event.preventDefault();
      runSearch();
    });
    document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
      els.query.value = button.dataset.example;
      runSearch();
    }));
    els.results.addEventListener('toggle', event => {
      const details = event.target.closest('.component-result');
      if (details?.open) openDetail(details);
    }, true);
    document.addEventListener('st:languagechange', () => {
      applyOwnTranslations();
      if (state.catalog) {
        const counts = state.catalog.meta.counts;
        els.status.querySelector('span:last-child').textContent = tr('ready', {components: formatNumber(counts.components, 0), reviewed: formatNumber(counts.reviewed, 0)});
        if (state.query) {
          state.results = state.results.map(entry => ({
            ...entry,
            reason: matchScore(entry.item, state.query)?.reason || entry.reason,
          }));
          renderResults();
        }
      }
    });
  }
  async function init() {
    applyOwnTranslations();
    bindEvents();
    try {
      const response = await fetch('data/components/catalog.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.catalog = await response.json();
      els.category.innerHTML = optionMarkup(state.catalog.filters.categories || []);
      els.manufacturer.innerHTML = optionMarkup(state.catalog.filters.manufacturers || []);
      els.package.innerHTML = optionMarkup(state.catalog.filters.packages || []);
      const counts = state.catalog.meta.counts;
      const coverageValues = [
        counts.components, counts.reviewed, counts.historical, counts.specifications,
      ];
      els.coverage.querySelectorAll('dd').forEach((element, index) => {
        element.textContent = formatNumber(coverageValues[index], 0);
      });
      els.status.classList.add('ready');
      els.status.querySelector('span:last-child').textContent = tr('ready', {components: formatNumber(counts.components, 0), reviewed: formatNumber(counts.reviewed, 0)});
      const params = new URLSearchParams(window.location.search);
      const initialQuery = params.get('q');
      if (initialQuery) {
        els.query.value = initialQuery;
        runSearch();
      }
    } catch (error) {
      console.error(error);
      els.status.classList.add('error');
      els.status.querySelector('span:last-child').textContent = tr('loadError');
      els.results.innerHTML = `<div class="component-empty"><h2>${escapeHtml(tr('loadError'))}</h2></div>`;
    }
  }

  init();
})();
