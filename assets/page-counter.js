(() => {
  'use strict';

  const API_ENDPOINT = 'https://home-5020945339.app-ionos.space/super-tecnico/api/index.php';
  const CLIENT_KEY = 'st.community.client.v1';

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

  function showCounter(views) {
    const footer = document.querySelector('body > footer:last-of-type') || document.querySelector('.st-page-footer');
    if (!footer) return;
    const counter = document.createElement('span');
    counter.className = 'st-page-counter';
    counter.textContent = `Visitas: ${Number(views).toLocaleString('es-ES')}`;
    counter.setAttribute('aria-label', `${Number(views).toLocaleString('es-ES')} visitas a esta página`);
    footer.append(counter);
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

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', count, {once: true});
  else count();
})();
