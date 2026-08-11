(() => {
  'use strict';

  const API_URL = new URL('api/index.php', document.baseURI);
  const CLIENT_KEY = 'st.community.client.v1';
  const PAGE_LABELS = {
    inicio: 'Inicio', climatizacion: 'Climatización', conductos: 'Diseño de conductos', calculadoras: 'Calculadoras',
    componentes: 'Componentes', comparador: 'Comparador', smd: 'Identificador SMD', averias: 'Averías compartidas',
    feedback: 'Propuestas', simbolos: 'Simbología', 'electronica-placas': 'Electrónica de placas',
    'formacion-climatizacion': 'Formación de climatización',
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
