'use strict';

const els = {
  form: document.getElementById('smdSearchForm'),
  marking: document.getElementById('markingInput'),
  package: document.getElementById('packageSelect'),
  pins: document.getElementById('pinSelect'),
  type: document.getElementById('typeSelect'),
  manufacturer: document.getElementById('manufacturerSelect'),
  designator: document.getElementById('designatorSelect'),
  results: document.getElementById('resultsSection'),
  status: document.getElementById('databaseStatus'),
  coverage: document.getElementById('coverageStats'),
};

const state = {
  catalog: null,
  candidates: [],
  confusionPairs: new Set(),
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function compact(value, preserveCase = false) {
  const clean = String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^A-Za-z0-9]/g, '');
  return preserveCase ? clean : clean.toUpperCase();
}

function humanNumber(value) {
  return new Intl.NumberFormat('es-ES').format(Number(value || 0));
}

function setStatus(kind, text) {
  els.status.className = `database-status ${kind || ''}`.trim();
  els.status.querySelector('span:last-child').textContent = text;
}

function addOptions(select, values, formatter = value => value) {
  const current = select.querySelector('option');
  select.replaceChildren(current);
  values.forEach(value => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = formatter(value);
    select.append(option);
  });
  select.disabled = false;
}

function setupFilters() {
  const packages = [...new Set(state.candidates.map(item => item.package.name))]
    .sort((a, b) => a.localeCompare(b, 'es', {numeric: true}));
  const packagePins = new Map();
  state.candidates.forEach(item => {
    if (!packagePins.has(item.package.name)) packagePins.set(item.package.name, new Set());
    packagePins.get(item.package.name).add(item.package.pins);
  });
  addOptions(els.package, packages, name => {
    const pins = [...packagePins.get(name)].filter(Boolean).sort((a, b) => a - b);
    return pins.length === 1 ? `${name} · ${pins[0]} patillas` : name;
  });

  const pins = [...new Set(state.candidates.map(item => Number(item.package.pins)).filter(Boolean))]
    .sort((a, b) => a - b);
  addOptions(els.pins, pins.map(String), value => `${value} patillas`);

  const types = [...new Set(state.candidates.map(item => item.component.type).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'es'));
  addOptions(els.type, types);

  const manufacturers = [...new Set(state.candidates.map(item => item.component.manufacturer).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'es'));
  addOptions(els.manufacturer, manufacturers);
}

function setupCoverage() {
  const meta = state.catalog.meta;
  const values = [
    humanNumber(meta.candidate_count),
    humanNumber(meta.manufacturer_count),
    humanNumber(meta.identification_ready),
  ];
  [...els.coverage.querySelectorAll('dd')].forEach((node, index) => {
    node.textContent = values[index] || '—';
  });
}

function isConfusable(a, b) {
  return state.confusionPairs.has(`${a}>${b}`) || state.confusionPairs.has(`${b}>${a}`);
}

function visualDistance(first, second) {
  const a = compact(first);
  const b = compact(second);
  const rows = a.length + 1;
  const columns = b.length + 1;
  const matrix = Array.from({length: rows}, () => Array(columns).fill(0));
  for (let row = 0; row < rows; row += 1) matrix[row][0] = row;
  for (let column = 0; column < columns; column += 1) matrix[0][column] = column;
  for (let row = 1; row < rows; row += 1) {
    for (let column = 1; column < columns; column += 1) {
      const left = a[row - 1];
      const right = b[column - 1];
      const substitution = left === right ? 0 : (isConfusable(left, right) ? 0.25 : 1);
      matrix[row][column] = Math.min(
        matrix[row - 1][column] + 1,
        matrix[row][column - 1] + 1,
        matrix[row - 1][column - 1] + substitution,
      );
    }
  }
  return matrix[a.length][b.length];
}

function markingMatch(candidate, query) {
  const queryCase = compact(query, true);
  const queryUpper = compact(query);
  const coreCase = compact(candidate.marking.core, true);
  const coreUpper = compact(candidate.marking.core);
  const rawUpper = compact(candidate.marking.raw);
  const partUpper = compact(candidate.component.part_number);
  const aliases = candidate.component.aliases.map(alias => compact(alias));
  const pattern = candidate.marking.pattern;

  if (!queryUpper) return null;
  if (queryUpper === partUpper || aliases.includes(queryUpper)) {
    return {score: 112, kind: 'part_exact', reason: 'La referencia introducida coincide exactamente con el componente.'};
  }
  if (queryCase === coreCase) {
    return {score: 104, kind: 'mark_exact_case', reason: 'El marcaje coincide exactamente, incluida la combinación de mayúsculas y minúsculas.'};
  }
  if (queryUpper === coreUpper) {
    const caseWarning = candidate.marking.case_sensitive && queryCase !== coreCase;
    return {
      score: caseWarning ? 94 : 100,
      kind: caseWarning ? 'mark_exact_case_warning' : 'mark_exact',
      reason: caseWarning
        ? 'Los caracteres coinciden, pero el fabricante distingue mayúsculas y minúsculas.'
        : 'El código fijo coincide exactamente con el marcaje oficial.',
    };
  }
  if (queryUpper === rawUpper) {
    return {score: 98, kind: 'raw_exact', reason: 'Coincide con la forma completa publicada por el fabricante.'};
  }

  const extraLength = Math.max(0, queryUpper.length - coreUpper.length);
  if (
    pattern === 'prefix_site_optional'
    && queryUpper.endsWith(coreUpper)
    && extraLength <= 3
  ) {
    return {score: 91, kind: 'site_prefix', reason: 'El final coincide; los caracteres iniciales pueden ser un código de planta.'};
  }
  if (
    ['suffix_site_optional', 'suffix_date_optional'].includes(pattern)
    && queryUpper.startsWith(coreUpper)
    && extraLength <= 4
  ) {
    return {
      score: 91,
      kind: 'verified_suffix',
      reason: pattern === 'suffix_date_optional'
        ? 'El inicio coincide; los caracteres finales pueden corresponder a fecha o lote.'
        : 'El inicio coincide; el carácter final puede corresponder a la planta de fabricación.',
    };
  }
  if (
    queryUpper.length > coreUpper.length
    && queryUpper.includes(coreUpper)
    && extraLength <= 4
  ) {
    return {score: 78, kind: 'embedded_core', reason: 'El marcaje contiene el código fijo, acompañado por otros caracteres.'};
  }

  if (Math.abs(queryUpper.length - coreUpper.length) <= 1) {
    const distance = visualDistance(queryUpper, coreUpper);
    if (distance <= 0.5) {
      return {score: 76, kind: 'visual_confusion', reason: 'Coincidencia visual: puede existir confusión entre caracteres como 0/O, 1/I o 5/S.'};
    }
    if (distance <= 1 && queryUpper.length >= 2) {
      return {score: 58, kind: 'one_character_difference', reason: 'El código difiere en un solo carácter; se muestra únicamente para que lo compares.'};
    }
  }

  if (
    queryUpper.length >= 2
    && (coreUpper.includes(queryUpper) || partUpper.includes(queryUpper))
  ) {
    return {score: 46, kind: 'partial', reason: 'Coincidencia parcial con el código o la referencia.'};
  }
  return null;
}

function designatorMatches(candidate, designator) {
  const type = compact(`${candidate.component.type} ${candidate.component.subtype}`);
  if (designator === 'Q') return type.includes('MOSFET') || type.includes('TRANSISTOR');
  if (designator === 'D') return type.includes('DIODO') || type.includes('TVS') || type.includes('ZENER');
  if (designator === 'U') return type.includes('CIRCUITOINTEGRADO') || type.includes('IC');
  return false;
}

function rankCandidate(candidate, filters) {
  const match = markingMatch(candidate, filters.query);
  if (!match) return null;
  let score = match.score;
  const reasons = [match.reason];
  let filterMatches = 0;
  let filterMismatches = 0;

  if (filters.package) {
    if (candidate.package.name === filters.package) {
      score += 30;
      filterMatches += 1;
      reasons.push(`El encapsulado coincide: ${candidate.package.name}.`);
    } else {
      score -= 12;
      filterMismatches += 1;
    }
  }
  if (filters.pins) {
    if (Number(candidate.package.pins) === Number(filters.pins)) {
      score += 20;
      filterMatches += 1;
      reasons.push(`Coincide el número de patillas: ${candidate.package.pins}.`);
    } else {
      score -= 9;
      filterMismatches += 1;
    }
  }
  if (filters.type) {
    if (candidate.component.type === filters.type) {
      score += 16;
      filterMatches += 1;
      reasons.push(`Coincide el tipo sospechado: ${candidate.component.type}.`);
    } else {
      score -= 5;
      filterMismatches += 1;
    }
  }
  if (filters.manufacturer) {
    if (candidate.component.manufacturer === filters.manufacturer) {
      score += 18;
      filterMatches += 1;
      reasons.push(`Coincide el fabricante o logotipo: ${candidate.component.manufacturer}.`);
    } else {
      score -= 6;
      filterMismatches += 1;
    }
  }
  if (filters.designator) {
    if (designatorMatches(candidate, filters.designator)) {
      score += 12;
      filterMatches += 1;
      reasons.push(`El tipo es compatible con la referencia ${filters.designator} de la placa.`);
    } else {
      score -= 4;
      filterMismatches += 1;
    }
  }
  return {...candidate, _match: {...match, score, reasons, filterMatches, filterMismatches}};
}

function matchLevel(item) {
  const {score, kind, filterMatches} = item._match;
  const exactKinds = new Set(['part_exact', 'mark_exact_case', 'mark_exact', 'raw_exact']);
  if (score >= 128 && exactKinds.has(kind) && filterMatches >= 1) {
    return {label: 'Coincidencia muy alta', className: ''};
  }
  if (score >= 90) return {label: 'Marcaje coincidente', className: ''};
  if (score >= 66) return {label: 'Posible coincidencia', className: 'possible'};
  return {label: 'Coincidencia aproximada', className: 'approximate'};
}

function getFilters() {
  return {
    query: els.marking.value.trim(),
    package: els.package.value,
    pins: els.pins.value,
    type: els.type.value,
    manufacturer: els.manufacturer.value,
    designator: els.designator.value,
  };
}

function parameterRows(parameters) {
  if (!parameters.length) return '<p>No hay parámetros publicados en esta ficha.</p>';
  return `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Parámetro</th><th>Valor</th><th>Condiciones</th></tr></thead>
        <tbody>
          ${parameters.map(item => `
            <tr>
              <td>${escapeHtml(item.name)}</td>
              <td><strong>${escapeHtml(item.value)}</strong></td>
              <td>${escapeHtml(item.conditions || '—')}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>`;
}

function pinoutRows(pinout) {
  if (!pinout.length) return '<p>El patillaje todavía no está disponible.</p>';
  return `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Pin</th><th>Símbolo</th><th>Función</th></tr></thead>
        <tbody>
          ${pinout.map(item => `
            <tr>
              <td><strong>${escapeHtml(item.pin)}</strong></td>
              <td>${escapeHtml(item.symbol || '—')}</td>
              <td>${escapeHtml(item.function || '—')}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>`;
}

function packageDescription(item) {
  const dimensions = [item.package.length_mm, item.package.width_mm, item.package.height_mm]
    .filter(value => value !== null && value !== undefined);
  const size = dimensions.length >= 2 ? `${dimensions.join(' × ')} mm` : 'Medidas no indicadas';
  return `${item.package.name} · ${item.package.pins} patillas · ${size}`;
}

function markingLayouts(item) {
  return item.marking.layouts.map(layout => `
    <div class="marking-layout">
      <code>${escapeHtml(
        [layout.line1, layout.line2, layout.line3].filter(Boolean).join(' / ')
        || item.marking.display
      )}</code>
      ${layout.logo ? `<p><strong>Logotipo o fabricante:</strong> ${escapeHtml(layout.logo)}</p>` : ''}
      ${layout.orientation_hint ? `<p><strong>Orientación:</strong> ${escapeHtml(layout.orientation_hint)}</p>` : ''}
      ${layout.case_sensitive ? '<p><strong>Atención:</strong> distingue mayúsculas y minúsculas.</p>' : ''}
      ${layout.notes ? `<p>${escapeHtml(layout.notes)}</p>` : ''}
    </div>
  `).join('');
}

function renderCandidate(item) {
  const level = matchLevel(item);
  const aliases = item.component.aliases.length
    ? `<div class="overview-item"><span>Otras referencias</span><strong>${escapeHtml(item.component.aliases.join(', '))}</strong></div>`
    : '';
  const lifecycle = item.component.lifecycle
    ? `<div class="overview-item"><span>Estado</span><strong>${escapeHtml(item.component.lifecycle)}</strong></div>`
    : '';
  const sourceUrl = item.source.datasheet_url || item.source.url;
  return `
    <details class="candidate-card">
      <summary class="candidate-summary">
        <div class="candidate-mark">${escapeHtml(item.marking.core)}</div>
        <div class="candidate-title">
          <h3>${escapeHtml(item.component.part_number)}</h3>
          <p>${escapeHtml(item.component.manufacturer)}</p>
          <div class="candidate-meta">
            <span class="meta-pill">${escapeHtml(item.component.type)}</span>
            <span class="meta-pill">${escapeHtml(item.package.name)}</span>
            <span class="meta-pill">${escapeHtml(item.package.pins)} patillas</span>
          </div>
        </div>
        <div class="match-column">
          <span class="match-pill ${level.className}">${escapeHtml(level.label)}</span>
          <span class="open-label"></span>
        </div>
      </summary>
      <div class="candidate-body">
        <div class="match-reasons">
          <strong>Por qué aparece:</strong>
          <ul>${item._match.reasons.map(reason => `<li>${escapeHtml(reason)}</li>`).join('')}</ul>
        </div>
        <div class="candidate-overview">
          <div class="overview-item">
            <span>Componente</span>
            <strong>${escapeHtml(item.component.type)} · ${escapeHtml(item.component.subtype || 'Sin subtipo')}</strong>
          </div>
          <div class="overview-item">
            <span>Encapsulado</span>
            <strong>${escapeHtml(packageDescription(item))}</strong>
          </div>
          <div class="overview-item">
            <span>Marcaje oficial</span>
            <strong>${escapeHtml(item.marking.display)}</strong>
          </div>
          ${aliases}
          ${lifecycle}
        </div>
        <p class="candidate-description">${escapeHtml(item.component.description || '')}</p>
        <div class="technical-details">
          <details>
            <summary>Cómo reconocer el marcaje</summary>
            <div class="detail-content">
              ${markingLayouts(item)}
              <p><strong>Patrón registrado:</strong> ${escapeHtml(item.marking.pattern)}</p>
            </div>
          </details>
          <details>
            <summary>Patillaje</summary>
            <div class="detail-content">${pinoutRows(item.pinout)}</div>
          </details>
          <details>
            <summary>Valores y límites eléctricos</summary>
            <div class="detail-content">${parameterRows(item.parameters)}</div>
          </details>
          <details>
            <summary>Fuente y nivel de comprobación</summary>
            <div class="detail-content">
              <div class="source-box">
                <strong>${escapeHtml(item.source.title)}</strong>
                <span>${escapeHtml(item.source.publisher || item.component.manufacturer)}</span>
                ${item.source.page_or_section ? `<span>${escapeHtml(item.source.page_or_section)}</span>` : ''}
                <a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">Abrir documento oficial ↗</a>
              </div>
              <p>Marcaje, encapsulado, patillaje y datos eléctricos están contrastados en documentación oficial. La identificación sobre una placa concreta sigue requiriendo comprobación.</p>
            </div>
          </details>
        </div>
        <div class="replacement-warning">
          <strong>No sustituyas solo por el marcaje.</strong> Confirma patillaje, polaridad, función, tensiones, corrientes y características dinámicas. Dos componentes con el mismo código visible pueden no ser equivalentes.
        </div>
      </div>
    </details>`;
}

function exactAmbiguity(results) {
  if (results.length < 2) return false;
  const first = results[0];
  return results.some(item =>
    item.id !== first.id
    && compact(item.marking.core, true) === compact(first.marking.core, true)
    && item.package.name === first.package.name
  );
}

function updateUrl(filters) {
  const url = new URL(window.location.href);
  ['q', 'package', 'pins', 'type', 'manufacturer', 'designator'].forEach(key => url.searchParams.delete(key));
  Object.entries(filters).forEach(([key, value]) => {
    if (value) url.searchParams.set(key === 'query' ? 'q' : key, value);
  });
  window.history.replaceState(null, '', url);
}

function renderResults(results, filters) {
  const queryLabel = escapeHtml(filters.query);
  if (!results.length) {
    els.results.innerHTML = `
      <div class="no-results">
        <div class="empty-chip" aria-hidden="true">?</div>
        <h2>No hay candidatos oficiales para “${queryLabel}”</h2>
        <p>Comprueba 0/O, 1/I, 5/S, 8/B, 2/Z y 6/G. Prueba también solo con el bloque fijo del marcaje y deja los filtros opcionales vacíos.</p>
        <button type="button" id="clearFiltersButton">Quitar filtros opcionales</button>
      </div>`;
    document.getElementById('clearFiltersButton').addEventListener('click', () => {
      [els.package, els.pins, els.type, els.manufacturer, els.designator].forEach(select => { select.value = ''; });
      runSearch();
    });
    return;
  }

  const ambiguous = exactAmbiguity(results);
  els.results.innerHTML = `
    <div class="results-heading">
      <div>
        <h2>Posibles componentes para “${queryLabel}”</h2>
        <p>La lista está ordenada por coincidencia. Ninguna ficha se abre automáticamente.</p>
      </div>
      <span class="result-count" aria-label="${results.length} resultados">${results.length}</span>
    </div>
    ${ambiguous ? `
      <p class="ambiguity-notice">
        <strong>Marcaje ambiguo:</strong> existen varias piezas oficiales con el mismo código y encapsulado. Revisa todas las posibilidades antes de decidir.
      </p>` : ''}
    <div class="result-list">
      ${results.map(renderCandidate).join('')}
    </div>`;
}

function runSearch() {
  if (!state.catalog) return;
  const filters = getFilters();
  if (!compact(filters.query)) {
    els.marking.focus();
    els.marking.setCustomValidity('Introduce el marcaje o la referencia del componente.');
    els.marking.reportValidity();
    return;
  }
  els.marking.setCustomValidity('');
  els.results.setAttribute('aria-busy', 'true');
  const ranked = state.candidates
    .map(candidate => rankCandidate(candidate, filters))
    .filter(Boolean)
    .filter(candidate => candidate._match.score >= 42)
    .sort((a, b) =>
      b._match.score - a._match.score
      || b._match.filterMatches - a._match.filterMatches
      || a._match.filterMismatches - b._match.filterMismatches
      || a.component.manufacturer.localeCompare(b.component.manufacturer, 'es')
      || a.component.part_number.localeCompare(b.component.part_number, 'es', {numeric: true})
    );
  const directKinds = new Set([
    'part_exact',
    'mark_exact_case',
    'mark_exact_case_warning',
    'mark_exact',
    'raw_exact',
    'site_prefix',
    'verified_suffix',
  ]);
  const direct = ranked.filter(candidate => directKinds.has(candidate._match.kind));
  const visible = (direct.length ? direct : ranked).slice(0, 80);
  renderResults(visible, filters);
  updateUrl(filters);
  els.results.setAttribute('aria-busy', 'false');
  els.results.scrollIntoView({behavior: 'smooth', block: 'start'});
}

function applyUrlState() {
  const params = new URLSearchParams(window.location.search);
  const mapping = {
    q: els.marking,
    package: els.package,
    pins: els.pins,
    type: els.type,
    manufacturer: els.manufacturer,
    designator: els.designator,
  };
  Object.entries(mapping).forEach(([key, element]) => {
    const value = params.get(key);
    if (value) element.value = value;
  });
  if (params.get('q')) runSearch();
}

async function init() {
  try {
    const response = await fetch('data/smd/catalog.json', {
      headers: {'Accept': 'application/json'},
      cache: 'no-cache',
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const catalog = await response.json();
    if (!catalog?.meta || !Array.isArray(catalog.candidates)) {
      throw new Error('Formato de catálogo no válido');
    }
    state.catalog = catalog;
    state.candidates = catalog.candidates;
    catalog.character_confusions.forEach(pair => {
      state.confusionPairs.add(`${compact(pair.observed)}>${compact(pair.possible)}`);
    });
    setupFilters();
    setupCoverage();
    setStatus(
      'ready',
      `${humanNumber(catalog.meta.candidate_count)} candidatos verificados · ${humanNumber(catalog.meta.manufacturer_count)} fabricantes`,
    );
    applyUrlState();
  } catch (error) {
    console.error(error);
    setStatus('error', 'No se pudo cargar la base SMD');
    els.results.innerHTML = `
      <div class="no-results">
        <h2>No se pudo cargar el identificador</h2>
        <p>Recarga la página. Si el problema continúa, la publicación puede estar actualizándose.</p>
      </div>`;
  }
}

els.form.addEventListener('submit', event => {
  event.preventDefault();
  runSearch();
});

document.querySelectorAll('[data-example]').forEach(button => {
  button.addEventListener('click', () => {
    els.marking.value = button.dataset.example;
    runSearch();
  });
});

init();
