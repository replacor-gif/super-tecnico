(() => {
  'use strict';

  const API_URL = new URL('api/index.php', document.baseURI);
  const CLIENT_KEY = 'st.community.client.v1';
  const PAGE_LABELS = {
    inicio: 'Inicio', climatizacion: 'Climatización', conductos: 'Diseño de conductos', ventilacion: 'Ventilación y extracción', calculadoras: 'Calculadoras',
    componentes: 'Componentes', comparador: 'Comparador', smd: 'Identificador SMD', averias: 'Averías compartidas',
    feedback: 'Propuestas', simbolos: 'Simbología', 'electronica-placas': 'Electrónica de placas', normativa: 'Normativa técnica',
    'formacion-climatizacion': 'Formación de climatización', 'plataformas-embebidas': 'Plataformas embebidas',
  };
  const REGULATION_LABELS = {
    rebt: 'REBT', rite: 'RITE', rsif: 'RSIF', rat: 'RAT', rlat: 'RLAT', 'cte-db-hs': 'CTE DB-HS', ict: 'ICT',
    gas: 'Reglamento de gas', 'pressure-equipment': 'Equipos a presión', 'machinery-safety': 'Seguridad de máquinas',
    'work-equipment': 'Equipos de trabajo', 'cte-db-he': 'CTE DB-HE', 'cte-db-si': 'CTE DB-SI', rsciei: 'RSCIEI',
    ripci: 'RIPCI', 'f-gas-eu': 'Gases fluorados UE', 'f-gas-es': 'Gases fluorados España', 'water-quality': 'Agua de consumo',
  };
  const state = { days: 30, loading: false };
  const byId = id => document.getElementById(id);

  function clientToken() {
    try {
      let token = localStorage.getItem(CLIENT_KEY);
      if (!token) {
        token = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        localStorage.setItem(CLIENT_KEY, token);
      }
      return token;
    } catch (_) {
      return 'analytics-private';
    }
  }

  function number(value) {
    return Number(value || 0).toLocaleString('es-ES');
  }

  function dateLabel(value, options = { day: '2-digit', month: 'short' }) {
    if (!value) return '—';
    return new Date(`${value}T12:00:00`).toLocaleDateString('es-ES', options);
  }

  function pageLabel(key) {
    return PAGE_LABELS[key] || key.replaceAll('-', ' ').replace(/^./, letter => letter.toUpperCase());
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  function showGate(message = '') {
    document.body.classList.remove('access-checking');
    byId('analyticsApp').hidden = true;
    byId('analyticsPinGate').hidden = false;
    byId('analyticsPinError').textContent = message;
    setTimeout(() => byId('analyticsPin').focus(), 40);
  }

  function enterDashboard() {
    document.body.classList.remove('access-checking');
    byId('analyticsPinGate').hidden = true;
    byId('analyticsApp').hidden = false;
    loadSummary();
  }

  async function initializeAccess() {
    const url = new URL(API_URL);
    url.searchParams.set('action', 'electroia-access');
    try {
      const response = await fetch(url, { cache: 'no-store', credentials: 'same-origin' });
      const data = await response.json();
      if (!response.ok || !data?.ok) throw new Error('access');
      if (data.required && !data.unlocked) showGate();
      else enterDashboard();
    } catch (_) {
      showGate('No se ha podido comprobar el acceso. Inténtalo de nuevo.');
    }
  }

  function renderMetrics(data) {
    const period = `${data.days} días`;
    const metrics = [
      ['Visitas históricas', data.totals.lifetime_views, 'Desde que se activó el contador', '#ffe438'],
      [`Visitas · ${period}`, data.totals.period_views, 'Aperturas de páginas en el periodo', '#00c8ff'],
      ['Visitantes aproximados', data.totals.period_unique, 'Dispositivos distintos por página y día', '#51ff7d'],
      ['Páginas activas', data.totals.active_pages, 'Apartados consultados en el periodo', '#ff3fa7'],
    ];
    byId('analyticsMetrics').innerHTML = metrics.map(([label, value, note, color]) =>
      `<article class="analytics-metric" style="--metric-color:${color}"><span>${label}</span><strong>${number(value)}</strong><small>${note}</small></article>`
    ).join('');
  }

  function renderChart(data) {
    const rows = data.daily || [];
    const maximum = Math.max(1, ...rows.map(row => Number(row.views || 0)));
    const width = 900;
    const height = 260;
    const plotTop = 24;
    const plotBottom = 222;
    const plotHeight = plotBottom - plotTop;
    const gap = rows.length > 45 ? 2 : rows.length > 15 ? 5 : 10;
    const barWidth = Math.max(3, (width - 56) / Math.max(1, rows.length) - gap);
    const step = (width - 56) / Math.max(1, rows.length);
    const labelEvery = Math.max(1, Math.ceil(rows.length / 6));
    const bars = rows.map((row, index) => {
      const value = Number(row.views || 0);
      const barHeight = value ? Math.max(3, value / maximum * plotHeight) : 0;
      const x = 38 + index * step + (step - barWidth) / 2;
      const y = plotBottom - barHeight;
      const label = index % labelEvery === 0 || index === rows.length - 1
        ? `<text class="chart-label" x="${x + barWidth / 2}" y="246" text-anchor="middle">${dateLabel(row.date)}</text>` : '';
      const valueLabel = value > 0 && rows.length <= 31
        ? `<text class="chart-value" x="${x + barWidth / 2}" y="${Math.max(15, y - 6)}" text-anchor="middle">${value}</text>` : '';
      return `<g><title>${dateLabel(row.date, { day: 'numeric', month: 'long' })}: ${number(value)} visitas</title><rect class="chart-bar" x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="${Math.min(5, barWidth / 2)}"/>${valueLabel}${label}</g>`;
    }).join('');
    const grid = [0, .5, 1].map(ratio => {
      const y = plotBottom - ratio * plotHeight;
      return `<line class="chart-grid" x1="38" y1="${y}" x2="888" y2="${y}"/><text class="chart-label" x="30" y="${y + 4}" text-anchor="end">${Math.round(maximum * ratio)}</text>`;
    }).join('');
    byId('analyticsChart').innerHTML = rows.length
      ? `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Visitas diarias"><defs><linearGradient id="chartGradient" x1="0" y1="1" x2="0" y2="0"><stop stop-color="#006bff"/><stop offset="1" stop-color="#00ead0"/></linearGradient></defs>${grid}${bars}</svg>`
      : '<p class="chart-empty">Todavía no hay datos diarios.</p>';
    byId('trendPeriod').textContent = `Últimos ${data.days} días`;
  }

  function renderDevices(data) {
    const devices = data.devices || {};
    const total = Math.max(1, Number(devices.mobile || 0) + Number(devices.tablet || 0) + Number(devices.desktop || 0));
    const mobile = Number(devices.mobile || 0) / total * 100;
    const tabletEnd = mobile + Number(devices.tablet || 0) / total * 100;
    const rows = [
      ['Móvil', devices.mobile, '#00c8ff'], ['Tablet', devices.tablet, '#ff3fa7'], ['Ordenador', devices.desktop, '#51ff7d'],
    ];
    byId('analyticsDevices').innerHTML = `<div class="device-visual" style="--mobile:${mobile}%;--tablet:${tabletEnd}%"><strong>${number(total === 1 && !data.totals.period_views ? 0 : data.totals.period_views)}</strong></div><div class="device-list">${rows.map(([label, value, color]) => `<div class="device-row" style="--row-color:${color}"><i></i><span>${label}</span><strong>${number(value)}</strong></div>`).join('')}</div>`;
  }

  function renderRanking(data) {
    const pages = (data.pages || []).slice(0, 20);
    const maximum = Math.max(1, ...pages.map(page => Number(page.period_views || 0)));
    byId('analyticsRanking').innerHTML = pages.length ? pages.map(page => {
      const width = Number(page.period_views || 0) / maximum * 100;
      return `<div class="ranking-row"><div class="ranking-name"><strong>${pageLabel(page.page_key)}</strong><small>${number(page.lifetime_views)} visitas históricas</small></div><div class="ranking-track"><i style="width:${width}%"></i></div><div class="ranking-value"><strong>${number(page.period_views)}</strong><small>${number(page.period_unique)} visitantes</small></div></div>`;
    }).join('') : '<p class="chart-empty">Todavía no hay páginas registradas.</p>';
    byId('rankingPeriod').textContent = `${data.days} días`;
  }

  function renderSources(data) {
    const sources = data.sources || {};
    const rows = [
      ['Navegación interna', sources.internal, '#00ead0'],
      ['Acceso directo', sources.direct, '#ffe438'],
      ['Enlace externo', sources.external, '#ff7a00'],
    ];
    byId('analyticsSources').innerHTML = rows.map(([label, value, color]) => `<div class="source-row" style="--row-color:${color}"><i></i><span>${label}</span><strong>${number(value)}</strong></div>`).join('');
  }

  function renderRatings(data) {
    const ratings = data.ratings || { likes: 0, dislikes: 0, pages: [], feedback: [] };
    const total = Number(ratings.likes || 0) + Number(ratings.dislikes || 0);
    const approval = total ? Math.round(Number(ratings.likes || 0) / total * 100) : 0;
    byId('ratingTotals').textContent = total ? `${number(total)} votos · ${approval}% positivos` : 'Sin votos todavía';
    byId('analyticsRatings').innerHTML = (ratings.pages || []).length ? ratings.pages.map(page => {
      const pageTotal = Number(page.likes || 0) + Number(page.dislikes || 0);
      const positive = pageTotal ? Number(page.likes || 0) / pageTotal * 100 : 0;
      return `<div class="rating-page-row"><div><strong>${escapeHtml(pageLabel(page.page_key))}</strong><small>${number(pageTotal)} votos</small></div><span class="rating-page-like">👍 ${number(page.likes)}</span><span class="rating-page-dislike">👎 ${number(page.dislikes)}</span><div class="rating-balance"><i style="width:${positive}%"></i></div></div>`;
    }).join('') : '<p class="chart-empty">Las valoraciones aparecerán aquí cuando llegue el primer voto.</p>';
    byId('analyticsComments').innerHTML = (ratings.feedback || []).length ? ratings.feedback.map(item =>
      `<article class="rating-comment"><header><strong>${escapeHtml(pageLabel(item.page_key))}</strong><time>${new Date(item.updated_at.replace(' ', 'T')).toLocaleDateString('es-ES')}</time></header><p>${escapeHtml(item.feedback)}</p></article>`
    ).join('') : '<p class="chart-empty">Todavía no hay comentarios sobre qué mejorar.</p>';
  }

  function renderRegulationSearch(data) {
    const regulation = data.regulation_search || { totals: {}, popular_queries: [], top_documents: [] };
    const totals = regulation.totals || {};
    const searches = Number(totals.searches || 0);
    const noResults = Number(totals.no_result_searches || 0);
    const rows = [
      ['Búsquedas', searches], ['Personas', totals.human_searches], ['IAs', totals.ai_searches],
      ['Usuarios aproximados', totals.clients], ['Páginas abiertas', totals.result_opens], ['Tiempo medio', `${number(totals.average_latency_ms)} ms`],
    ];
    byId('regulationSearchMetrics').innerHTML = rows.map(([label, value]) => `<div class="regulation-search-metric"><span>${label}</span><strong>${typeof value === 'number' ? number(value) : value}</strong></div>`).join('');
    byId('regulationSearchPeriod').textContent = `${data.days} días · ${searches ? Math.round(noResults / searches * 100) : 0}% sin resultado`;
    byId('regulationTopDocuments').innerHTML = (regulation.top_documents || []).length ? regulation.top_documents.map(item => `<span class="regulation-doc-pill">${escapeHtml(REGULATION_LABELS[item.document_id] || item.document_id)} <strong>${number(item.appearances)}</strong></span>`).join('') : '<p class="chart-empty">Aún no hay reglamentos destacados.</p>';
    byId('regulationPopularQueries').innerHTML = (regulation.popular_queries || []).length ? regulation.popular_queries.map(item => `<div class="regulation-query-row"><strong title="${escapeHtml(item.query)}">${escapeHtml(item.query || 'Consulta sin muestra')}</strong><span>${number(item.searches)} búsquedas</span><small>${number(item.no_results)} sin resultado · ${number(item.result_opens)} aperturas</small></div>`).join('') : '<p class="chart-empty">Las consultas más repetidas aparecerán aquí.</p>';
    byId('regulationQueryTotals').textContent = `${number(searches)} consultas`;
    byId('regulationPrivacy').textContent = regulation.privacy || '';
  }

  async function loadSummary() {
    if (state.loading) return;
    state.loading = true;
    byId('analyticsStatus').className = 'analytics-status';
    byId('analyticsStatus').textContent = 'Actualizando el panel…';
    try {
      const url = new URL(API_URL);
      url.searchParams.set('action', 'analytics-summary');
      url.searchParams.set('days', String(state.days));
      const response = await fetch(url, { cache: 'no-store', credentials: 'same-origin' });
      if (response.status === 401) { showGate('La sesión privada ha caducado.'); return; }
      const data = await response.json();
      if (!response.ok || !data?.ok) throw new Error('summary');
      renderMetrics(data);
      renderChart(data);
      renderDevices(data);
      renderRanking(data);
      renderSources(data);
      renderRatings(data);
      renderRegulationSearch(data);
      byId('analyticsStatus').textContent = data.totals.period_views ? 'Datos actualizados correctamente.' : 'El registro diario comienza con esta versión; los totales históricos se conservan.';
      byId('analyticsUpdated').textContent = `Actualizado ${new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}`;
      byId('analyticsTrackingNote').textContent = data.tracking_since
        ? `El desglose diario está disponible desde ${dateLabel(data.tracking_since, { day: 'numeric', month: 'long', year: 'numeric' })}. Los contadores históricos anteriores siguen apareciendo en el total de cada página.`
        : 'El desglose diario comenzará a completarse con las próximas visitas.';
    } catch (_) {
      byId('analyticsStatus').className = 'analytics-status is-error';
      byId('analyticsStatus').textContent = 'No se han podido cargar las visitas. Vuelve a intentarlo en unos segundos.';
    } finally {
      state.loading = false;
    }
  }

  byId('analyticsPinForm').addEventListener('submit', async event => {
    event.preventDefault();
    const pin = byId('analyticsPin').value.trim();
    const button = event.currentTarget.querySelector('button');
    button.disabled = true;
    byId('analyticsPinError').textContent = '';
    try {
      const url = new URL(API_URL);
      url.searchParams.set('action', 'electroia-unlock');
      const response = await fetch(url, {
        method: 'POST', credentials: 'same-origin', cache: 'no-store',
        headers: { 'Content-Type': 'application/json', 'X-ST-Client': clientToken() },
        body: JSON.stringify({ pin, client_token: clientToken() }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok || !data?.unlocked) {
        showGate(response.status === 429 ? 'Demasiados intentos. Espera unos minutos.' : 'PIN incorrecto.');
        return;
      }
      byId('analyticsPin').value = '';
      enterDashboard();
    } catch (_) {
      showGate('No se ha podido comprobar el PIN.');
    } finally {
      button.disabled = false;
    }
  });

  document.querySelectorAll('[data-days]').forEach(button => button.addEventListener('click', () => {
    state.days = Number(button.dataset.days);
    document.querySelectorAll('[data-days]').forEach(item => item.classList.toggle('is-active', item === button));
    loadSummary();
  }));
  byId('analyticsRefresh').addEventListener('click', loadSummary);
  initializeAccess();
})();
