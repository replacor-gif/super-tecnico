(() => {
  'use strict';

  const FEED_URL = 'data/updates/feed.json';
  const ROADMAP_URL = 'data/core/project-roadmap.json';
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
  const normalize = value => String(value ?? '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase('es');
  const formatDate = value => new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T12:00:00Z`));
  let entries = [];

  function renderRoadmap(data) {
    const summary = document.getElementById('roadmapSummary');
    const priorities = document.getElementById('roadmapPriorities');
    const status = document.getElementById('roadmapStatus');
    if (!summary || !priorities || !status) return;
    const metrics = data.summary || {};
    summary.innerHTML = [
      ['ElectroIA revisado', `${metrics.electroia_reviewed_symbols || 0} / ${metrics.electroia_catalog_symbols || 0}`, `${metrics.electroia_reviewed_percent || 0}%`],
      ['Familias completas', `${metrics.electroia_complete_families || 0} / ${metrics.electroia_total_families || 0}`, `${metrics.electroia_pending_symbols || 0} símbolos pendientes`],
      ['Herramientas para IAs', String(metrics.public_ai_tools || 0), 'consultas públicas gratuitas'],
      ['Preparación técnica IA', `${metrics.ai_readiness_percent || 0}%`, 'servicio remoto aún planificado'],
    ].map(([label, value, detail]) => `<article><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(detail)}</small></article>`).join('');
    const labels = data.status_labels || {};
    priorities.innerHTML = (data.priorities || []).map((item, index) => {
      const progress = item.progress;
      const percent = progress?.total ? Math.round(progress.done * 1000 / progress.total) / 10 : null;
      return `<article class="roadmap-item" style="--roadmap-order:'${String(index + 1).padStart(2, '0')}'"><div><span>${esc(item.area)}</span><em>${esc(labels[item.status] || item.status)}</em></div><h3>${esc(item.title)}</h3>${progress ? `<div class="roadmap-progress" aria-label="${esc(`${progress.done} de ${progress.total} ${progress.unit}`)}"><i style="width:${percent}%"></i></div><small>${esc(`${progress.done} de ${progress.total} ${progress.unit} · ${percent}%`)}</small>` : ''}<p>${esc(item.next_action)}</p></article>`;
    }).join('');
    const remaining = (data.remaining_electroia_families || []).map(item => `${item.family} (${item.pending_symbols})`).join(', ');
    status.textContent = remaining ? `ElectroIA: solo quedan ${remaining}.` : 'ElectroIA no tiene familias pendientes.';
  }

  function entryCard(entry, compact = false) {
    const author = entry.author?.label || 'Usuario anónimo';
    const authorType = ['maintainer', 'community', 'anonymous'].includes(entry.author?.type) ? entry.author.type : 'anonymous';
    const areas = (entry.areas || []).map(area => `<span>${esc(area)}</span>`).join('');
    return `<article class="update-entry${compact ? ' is-compact' : ''}">
      <div class="update-date"><time datetime="${esc(entry.date)}">${esc(formatDate(entry.date))}</time><i aria-hidden="true"></i></div>
      <div class="update-card"><div class="update-areas">${areas}</div><h3>${esc(entry.title)}</h3><p>${esc(entry.summary)}</p><div class="update-author update-author-${authorType}"><span aria-hidden="true">${authorType === 'maintainer' ? 'ST' : authorType === 'community' ? '★' : '○'}</span><small>Aportación de</small><strong>${esc(author)}</strong></div></div>
    </article>`;
  }

  function renderPreview() {
    document.querySelectorAll('[data-st-updates-preview]').forEach(container => {
      container.innerHTML = entries.slice(0, Number(container.dataset.limit || 3)).map(entry => entryCard(entry, true)).join('');
    });
  }

  function renderFull() {
    const list = document.querySelector('[data-st-updates-list]');
    if (!list) return;
    const search = document.getElementById('updatesSearch');
    const area = document.getElementById('updatesArea');
    const status = document.getElementById('updatesStatus');
    const query = normalize(search?.value);
    const selectedArea = area?.value || 'all';
    const visible = entries.filter(entry => {
      const haystack = normalize([entry.title, entry.summary, ...(entry.areas || []), entry.author?.label].join(' '));
      return (!query || haystack.includes(query)) && (selectedArea === 'all' || entry.areas?.includes(selectedArea));
    });
    list.innerHTML = visible.map(entry => entryCard(entry)).join('');
    status.textContent = visible.length ? `${visible.length} mejora${visible.length === 1 ? '' : 's'} publicada${visible.length === 1 ? '' : 's'}.` : 'No hay mejoras que coincidan con la búsqueda.';
  }

  function populateAreas() {
    const select = document.getElementById('updatesArea');
    if (!select) return;
    const areas = [...new Set(entries.flatMap(entry => entry.areas || []))].sort((a, b) => a.localeCompare(b, 'es'));
    select.insertAdjacentHTML('beforeend', areas.map(area => `<option value="${esc(area)}">${esc(area)}</option>`).join(''));
  }

  async function load() {
    try {
      const response = await fetch(new URL(FEED_URL, document.baseURI), { headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      entries = Array.isArray(data.entries) ? data.entries.slice() : [];
      populateAreas();
      renderPreview();
      renderFull();
      if (document.getElementById('roadmapSummary')) {
        try {
          const roadmapResponse = await fetch(new URL(ROADMAP_URL, document.baseURI), { headers: { Accept: 'application/json' } });
          if (!roadmapResponse.ok) throw new Error(`HTTP ${roadmapResponse.status}`);
          renderRoadmap(await roadmapResponse.json());
        } catch (roadmapError) {
          console.error(roadmapError);
          document.getElementById('roadmapStatus').textContent = 'No se pudo cargar el estado medible en este momento.';
        }
      }
    } catch (error) {
      console.error(error);
      const status = document.getElementById('updatesStatus');
      if (status) status.textContent = 'No se pudo cargar el historial en este momento.';
    }
  }

  document.getElementById('updatesSearch')?.addEventListener('input', renderFull);
  document.getElementById('updatesArea')?.addEventListener('change', renderFull);
  load();
})();
