(() => {
  'use strict';

  const FEED_URL = 'data/updates/feed.json';
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
  const normalize = value => String(value ?? '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase('es');
  const formatDate = value => new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T12:00:00Z`));
  let entries = [];

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
