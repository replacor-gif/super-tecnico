(() => {
  'use strict';

  const API_ENDPOINT = 'https://home-5020945339.app-ionos.space/super-tecnico/api/index.php';
  const CLIENT_KEY = 'st.community.client.v1';
  const ELECTROIA_PATH = 'archivo-tecnico-47097e44267b9cb111636b84823f1d47/';

  function pageKey() {
    const file = location.pathname.split('/').filter(Boolean).pop() || 'index';
    const key = file.replace(/\.html?$/i, '').toLowerCase();
    return key === 'index' ? 'inicio' : key.replace(/[^a-z0-9-]/g, '-').slice(0, 64);
  }

  function clientToken() {
    let token = localStorage.getItem(CLIENT_KEY);
    if (!token) {
      token = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      localStorage.setItem(CLIENT_KEY, token);
    }
    return token;
  }

  function footerTools() {
    const footer = document.querySelector('body > footer:last-of-type') || document.querySelector('.st-page-footer');
    if (!footer) return null;
    let tools = footer.querySelector('.st-footer-tools');
    if (tools) return tools;

    tools = document.createElement('div');
    tools.className = 'st-footer-tools';
    const access = document.createElement('a');
    access.className = 'st-electro-access';
    access.href = ELECTROIA_PATH;
    access.textContent = 'Ω';
    access.setAttribute('aria-label', 'Ω');
    tools.append(access);
    footer.append(tools);
    return tools;
  }

  function showCounter(views) {
    const tools = footerTools();
    if (!tools) return;
    const counter = document.createElement('span');
    counter.className = 'st-page-counter';
    counter.textContent = `Visitas: ${Number(views).toLocaleString('es-ES')}`;
    counter.setAttribute('aria-label', `${Number(views).toLocaleString('es-ES')} visitas a esta página`);
    tools.prepend(counter);
  }

  async function count() {
    const url = new URL(API_ENDPOINT);
    url.searchParams.set('action', 'page-view');
    const token = clientToken();
    try {
      const response = await fetch(url, {
        method: 'POST',
        credentials: 'omit',
        headers: {'Content-Type': 'application/json', 'X-ST-Client': token},
        body: JSON.stringify({page_key: pageKey(), client_token: token}),
      });
      const data = await response.json();
      if (response.ok && data.ok && Number.isFinite(Number(data.views))) showCounter(data.views);
    } catch {
      // El contador no debe interferir con la consulta técnica si la API no responde.
    }
  }

  function start() {
    footerTools();
    count();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
  else start();
})();
