(() => {
  'use strict';

  const API_URL = new URL('api/index.php', document.baseURI);
  const CLIENT_KEY = 'st.community.client.v1';
  const state = { defaults: {}, overrides: {}, baseline: {}, dirty: new Set(), query: '', saving: false };
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

  function groupFor(key) { return key.split('.')[0] || 'other'; }
  function humanKey(key) {
    return key.split('.').slice(1).join(' · ').replace(/([a-záéíóúñ])([A-Z])/g, '$1 $2').replace(/[-_]/g, ' ');
  }
  function effectiveValue(key) { return owns(state.overrides, key) ? state.overrides[key] : state.defaults[key]; }

  function updateSummary() {
    const visible = document.querySelectorAll('.editor-field:not([hidden])').length;
    byId('editorVisibleCount').textContent = String(visible);
    byId('editorChangedCount').textContent = `${Object.keys(state.overrides).length} modificados`;
    const total = state.dirty.size;
    byId('editorDirtyLabel').textContent = total ? `${total} ${total === 1 ? 'cambio pendiente' : 'cambios pendientes'}` : 'No hay cambios pendientes';
    byId('editorSaveAll').disabled = total === 0 || state.saving;
  }

  function applyFilter() {
    const query = state.query.trim().toLocaleLowerCase('es');
    document.querySelectorAll('.editor-group').forEach(group => {
      let visible = 0;
      group.querySelectorAll('.editor-field').forEach(card => {
        const match = !query || card.dataset.search.includes(query);
        card.hidden = !match;
        if (match) visible += 1;
      });
      group.hidden = visible === 0;
      group.open = Boolean(query) || group.dataset.first === 'true';
      group.querySelector('[data-group-count]').textContent = String(visible);
    });
    updateSummary();
  }

  function fieldCard(key) {
    const card = document.createElement('article');
    card.className = 'editor-field';
    card.dataset.key = key;
    card.dataset.search = `${key} ${humanKey(key)} ${state.defaults[key]} ${effectiveValue(key)}`.toLocaleLowerCase('es');

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
    textarea.rows = Math.min(6, Math.max(2, Math.ceil(effectiveValue(key).length / 75)));
    textarea.maxLength = 4000;
    textarea.value = effectiveValue(key);
    textarea.dataset.contentKey = key;
    textarea.addEventListener('input', () => {
      if (textarea.value === state.baseline[key]) state.dirty.delete(key);
      else state.dirty.add(key);
      card.classList.toggle('is-dirty', state.dirty.has(key));
      card.dataset.search = `${key} ${humanKey(key)} ${state.defaults[key]} ${textarea.value}`.toLocaleLowerCase('es');
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

  function render() {
    const container = byId('editorGroups');
    container.replaceChildren();
    const groups = new Map();
    Object.keys(state.defaults).sort((a, b) => a.localeCompare(b, 'es')).forEach(key => {
      const prefix = groupFor(key);
      if (!groups.has(prefix)) groups.set(prefix, []);
      groups.get(prefix).push(key);
    });
    let index = 0;
    groups.forEach((keys, prefix) => {
      const details = document.createElement('details');
      details.className = 'editor-group';
      details.dataset.first = String(index === 0);
      details.open = index === 0;
      const summary = document.createElement('summary');
      const title = document.createElement('strong');
      title.textContent = sectionNames[prefix] || prefix.replace(/[-_]/g, ' ');
      const count = document.createElement('span');
      count.dataset.groupCount = '';
      count.textContent = String(keys.length);
      summary.append(title, count);
      const fields = document.createElement('div');
      fields.className = 'editor-field-grid';
      keys.forEach(key => fields.append(fieldCard(key)));
      details.append(summary, fields);
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
      const data = await request('content-editor');
      state.overrides = Object.fromEntries((data.items || []).map(item => [item.content_key, item.value_text]));
      state.baseline = Object.fromEntries(Object.keys(state.defaults).map(key => [key, effectiveValue(key)]));
      render();
      setStatus(`${Object.keys(state.defaults).length} textos disponibles · ${Object.keys(state.overrides).length} personalizados`);
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
        const textarea = document.querySelector(`textarea[data-content-key="${CSS.escape(key)}"]`);
        if (!textarea) continue;
        await request('content-editor', { body: { content_key: key, value_text: textarea.value } });
        state.overrides[key] = textarea.value;
        state.baseline[key] = textarea.value;
        state.dirty.delete(key);
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
