(() => {
  'use strict';

  const API_URL = new URL('api/index.php', document.baseURI);
  const CLIENT_KEY = 'st.community.client.v1';
  const state = { defaults: {}, metadata: {}, groupNames: {}, order: [], overrides: {}, baseline: {}, drafts: {}, dirty: new Set(), query: '', saving: false, visibleCount: 0 };
  const byId = id => document.getElementById(id);
  const owns = (object, key) => Object.prototype.hasOwnProperty.call(object, key);

  const sectionNames = {
    common: 'Elementos comunes', portal: 'Inicio y navegación', calc: 'Calculadoras', hvac: 'Climatización',
    duct: 'Conductos', ventilation: 'Ventilación y extracción', regulations: 'Normativa', regulator: 'Normativa',
    electroia: 'ElectroIA', components: 'Componentes', component: 'Componentes', smd: 'Códigos SMD',
    faults: 'Averías y soluciones', fault: 'Averías y soluciones', feedback: 'Aportaciones', update: 'Actualizaciones',
    refrigerant: 'Frigorista', refrigeration: 'Instalaciones frigoríficas', electrical: 'Electricidad',
  };

  function clientToken() {
    try {
      let token = localStorage.getItem(CLIENT_KEY);
      if (!token) {
        token = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        localStorage.setItem(CLIENT_KEY, token);
      }
      return token;
    } catch (_) { return 'private-content-editor'; }
  }

  async function request(action, options = {}) {
    const url = new URL(API_URL);
    url.searchParams.set('action', action);
    const config = { cache: 'no-store', credentials: 'same-origin', headers: { 'X-ST-Client': clientToken() } };
    if (options.body) {
      config.method = 'POST';
      config.headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify({ ...options.body, client_token: clientToken() });
    }
    const response = await fetch(url, config);
    const data = await response.json().catch(() => null);
    if (response.status === 401) {
      showGate('La sesión privada ha caducado.');
      throw new Error('locked');
    }
    if (!response.ok || !data?.ok) throw new Error(data?.error || 'request_failed');
    return data;
  }

  function showGate(message = '') {
    document.body.classList.remove('access-checking');
    byId('editorApp').hidden = true;
    byId('editorPinGate').hidden = false;
    byId('editorPinError').textContent = message;
    setTimeout(() => byId('editorPin').focus(), 40);
  }

  function setStatus(message, error = false) {
    byId('editorStatus').textContent = message;
    byId('editorStatus').classList.toggle('is-error', error);
  }

  function groupFor(key) { return key.startsWith('page.') ? `page:${key.split('.')[1]}` : (key.split('.')[0] || 'other'); }
  function humanKey(key) {
    if (state.metadata[key]?.label) return state.metadata[key].label;
    return key.split('.').slice(1).join(' · ').replace(/([a-záéíóúñ])([A-Z])/g, '$1 $2').replace(/[-_]/g, ' ');
  }
  function effectiveValue(key) { return owns(state.overrides, key) ? state.overrides[key] : state.defaults[key]; }
  function currentValue(key) { return owns(state.drafts, key) ? state.drafts[key] : effectiveValue(key); }
  function searchText(key) {
    return `${key} ${humanKey(key)} ${state.metadata[key]?.page_title || ''} ${state.defaults[key]} ${currentValue(key)}`.toLocaleLowerCase('es');
  }

  function updateSummary() {
    byId('editorVisibleCount').textContent = String(state.visibleCount);
    byId('editorChangedCount').textContent = `${Object.keys(state.overrides).length} modificados`;
    const total = state.dirty.size;
    byId('editorDirtyLabel').textContent = total ? `${total} ${total === 1 ? 'cambio pendiente' : 'cambios pendientes'}` : 'No hay cambios pendientes';
    byId('editorSaveAll').disabled = total === 0 || state.saving;
  }

  function applyFilter() {
    const query = state.query.trim().toLocaleLowerCase('es');
    let visible = 0;
    document.querySelectorAll('.editor-group').forEach(group => {
      const keys = group.contentKeys || [];
      const matches = query ? keys.filter(key => searchText(key).includes(query)) : keys;
      group.hidden = matches.length === 0;
      group.open = Boolean(query) ? matches.length > 0 : group.dataset.first === 'true';
      group.querySelector('[data-group-count]').textContent = String(matches.length);
      if (group.open) populateGroup(group, matches);
      visible += matches.length;
    });
    state.visibleCount = visible;
    updateSummary();
  }

  function fieldCard(key) {
    const card = document.createElement('article');
    card.className = 'editor-field';
    card.dataset.key = key;
    card.dataset.search = searchText(key);

    const header = document.createElement('header');
    const label = document.createElement('label');
    label.htmlFor = `content-${key.replace(/[^a-z0-9]/g, '-')}`;
    label.textContent = humanKey(key) || key;
    const badge = document.createElement('span');
    badge.className = 'editor-modified-badge';
    badge.textContent = 'MODIFICADO';
    badge.hidden = !owns(state.overrides, key);
    header.append(label, badge);

    const textarea = document.createElement('textarea');
    textarea.id = label.htmlFor;
    textarea.rows = Math.min(6, Math.max(2, Math.ceil(currentValue(key).length / 75)));
    textarea.maxLength = 4000;
    textarea.value = currentValue(key);
    textarea.dataset.contentKey = key;
    textarea.addEventListener('input', () => {
      if (textarea.value === state.baseline[key]) state.dirty.delete(key);
      else state.dirty.add(key);
      state.drafts[key] = textarea.value;
      card.classList.toggle('is-dirty', state.dirty.has(key));
      card.dataset.search = `${key} ${humanKey(key)} ${state.metadata[key]?.page_title || ''} ${state.defaults[key]} ${textarea.value}`.toLocaleLowerCase('es');
      updateSummary();
    });

    const footer = document.createElement('footer');
    const technicalKey = document.createElement('code');
    technicalKey.textContent = key;
    const reset = document.createElement('button');
    reset.type = 'button';
    reset.textContent = 'Restaurar original';
    reset.disabled = !owns(state.overrides, key) && textarea.value === state.defaults[key];
    reset.addEventListener('click', () => resetField(key, card, textarea, badge, reset));
    footer.append(technicalKey, reset);
    card.append(header, textarea, footer);
    return card;
  }

  function populateGroup(details, keys) {
    const signature = keys.join('|');
    if (details.renderSignature === signature) return;
    const fields = details.querySelector('.editor-field-grid');
    fields.replaceChildren(...keys.map(fieldCard));
    details.renderSignature = signature;
  }

  function render() {
    const container = byId('editorGroups');
    container.replaceChildren();
    const groups = new Map();
    state.order.forEach(key => {
      const prefix = groupFor(key);
      if (!groups.has(prefix)) groups.set(prefix, []);
      groups.get(prefix).push(key);
    });
    const groupEntries = [...groups.entries()].sort(([prefixA], [prefixB]) => {
      if (prefixA === 'page:inicio') return -1;
      if (prefixB === 'page:inicio') return 1;
      const pageA = prefixA.startsWith('page:');
      const pageB = prefixB.startsWith('page:');
      if (pageA !== pageB) return pageA ? -1 : 1;
      const nameA = state.groupNames[prefixA] || sectionNames[prefixA] || prefixA;
      const nameB = state.groupNames[prefixB] || sectionNames[prefixB] || prefixB;
      return nameA.localeCompare(nameB, 'es');
    });
    let index = 0;
    groupEntries.forEach(([prefix, keys]) => {
      const details = document.createElement('details');
      details.className = 'editor-group';
      details.dataset.first = String(index === 0);
      details.contentKeys = keys;
      details.open = index === 0;
      const summary = document.createElement('summary');
      const title = document.createElement('strong');
      title.textContent = state.groupNames[prefix] || sectionNames[prefix] || prefix.replace(/^page:/, '').replace(/[-_]/g, ' ');
      const count = document.createElement('span');
      count.dataset.groupCount = '';
      count.textContent = String(keys.length);
      summary.append(title, count);
      const fields = document.createElement('div');
      fields.className = 'editor-field-grid';
      details.append(summary);
      const pageEntry = keys.map(key => state.metadata[key]).find(Boolean);
      if (pageEntry?.page) {
        const preview = document.createElement('a');
        preview.className = 'editor-page-preview';
        preview.href = pageEntry.page;
        preview.target = '_blank';
        preview.rel = 'noopener';
        preview.textContent = `Abrir ${pageEntry.page_title || pageEntry.page} ↗`;
        details.append(preview);
      }
      details.append(fields);
      details.addEventListener('toggle', () => {
        if (!details.open) return;
        const query = state.query.trim().toLocaleLowerCase('es');
        populateGroup(details, query ? keys.filter(key => searchText(key).includes(query)) : keys);
      });
      container.append(details);
      index += 1;
    });
    applyFilter();
  }

  async function loadEditor() {
    setStatus('Cargando el catálogo de textos…');
    try {
      await window.ST_I18N?.contentReady;
      state.defaults = window.ST_I18N?.catalog?.() || {};
      const translatedOrder = Object.keys(state.defaults).sort((a, b) => a.localeCompare(b, 'es'));
      const pageOrder = [];
      const [data, hardcodedResponse] = await Promise.all([
        request('content-editor'),
        fetch(new URL('data/content/editable-catalog.json', document.baseURI), { cache: 'no-store' }).then(response => response.ok ? response.json() : null),
      ]);
      (hardcodedResponse?.entries || []).forEach(entry => {
        state.defaults[entry.key] = entry.default;
        pageOrder.push(entry.key);
        state.metadata[entry.key] = entry;
        state.groupNames[`page:${entry.page_slug}`] = entry.page_title;
      });
      state.order = [...pageOrder, ...translatedOrder];
      state.overrides = Object.fromEntries((data.items || []).map(item => [item.content_key, item.value_text]));
      state.baseline = Object.fromEntries(Object.keys(state.defaults).map(key => [key, effectiveValue(key)]));
      state.drafts = { ...state.baseline };
      render();
      setStatus(`${Object.keys(state.defaults).length} textos de interfaz disponibles · ${Object.keys(state.overrides).length} personalizados`);
    } catch (error) {
      if (error.message !== 'locked') setStatus('No se ha podido cargar el editor. Vuelve a intentarlo.', true);
    }
  }

  async function enterApp() {
    document.body.classList.remove('access-checking');
    byId('editorPinGate').hidden = true;
    byId('editorApp').hidden = false;
    await loadEditor();
  }

  async function initializeAccess() {
    try {
      const data = await request('electroia-access');
      if (data.required && !data.unlocked) showGate();
      else enterApp();
    } catch (error) {
      if (error.message !== 'locked') showGate('No se ha podido comprobar el acceso. Inténtalo de nuevo.');
    }
  }

  async function resetField(key, card, textarea, badge, button) {
    button.disabled = true;
    try {
      if (owns(state.overrides, key)) await request('content-editor-delete', { body: { content_key: key } });
      delete state.overrides[key];
      state.baseline[key] = state.defaults[key];
      state.drafts[key] = state.defaults[key];
      state.dirty.delete(key);
      textarea.value = state.defaults[key];
      badge.hidden = true;
      card.classList.remove('is-dirty');
      button.disabled = true;
      setStatus(`Texto restaurado: ${humanKey(key)}`);
      updateSummary();
    } catch (error) {
      if (error.message !== 'locked') {
        button.disabled = false;
        setStatus('No se ha podido restaurar el texto.', true);
      }
    }
  }

  async function saveAll() {
    if (!state.dirty.size || state.saving) return;
    state.saving = true;
    updateSummary();
    setStatus('Guardando cambios…');
    const pending = [...state.dirty];
    let saved = 0;
    try {
      for (const key of pending) {
        const value = currentValue(key);
        await request('content-editor', { body: { content_key: key, value_text: value } });
        state.overrides[key] = value;
        state.baseline[key] = value;
        state.drafts[key] = value;
        state.dirty.delete(key);
        const textarea = document.querySelector(`textarea[data-content-key="${CSS.escape(key)}"]`);
        if (!textarea) { saved += 1; continue; }
        const card = textarea.closest('.editor-field');
        card.classList.remove('is-dirty');
        card.querySelector('.editor-modified-badge').hidden = false;
        card.querySelector('button').disabled = false;
        saved += 1;
      }
      setStatus(`${saved} ${saved === 1 ? 'texto guardado' : 'textos guardados'}. Los cambios ya están disponibles.`);
    } catch (error) {
      if (error.message !== 'locked') setStatus(`Se guardaron ${saved}; quedan ${state.dirty.size} pendientes. Inténtalo de nuevo.`, true);
    } finally {
      state.saving = false;
      updateSummary();
    }
  }

  byId('editorPinForm').addEventListener('submit', async event => {
    event.preventDefault();
    const button = event.currentTarget.querySelector('button');
    button.disabled = true;
    byId('editorPinError').textContent = '';
    try {
      const data = await request('electroia-unlock', { body: { pin: byId('editorPin').value.trim() } });
      if (!data.unlocked) throw new Error('invalid');
      byId('editorPin').value = '';
      await enterApp();
    } catch (error) {
      if (error.message !== 'locked') showGate('PIN incorrecto o acceso no disponible.');
    } finally { button.disabled = false; }
  });

  byId('editorSearch').addEventListener('input', event => { state.query = event.target.value; applyFilter(); });
  byId('editorSaveAll').addEventListener('click', saveAll);
  initializeAccess();
})();
