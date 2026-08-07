(() => {
  'use strict';

  const API_ENDPOINT = new URL('api/index.php', document.baseURI).href;
  const CLIENT_KEY = 'st.community.client.v1';

  function pageKey() {
    const file = location.pathname.endsWith('/')
      ? 'index'
      : location.pathname.split('/').filter(Boolean).pop() || 'index';
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
    const counter = footer.querySelector('.st-page-counter') || document.createElement('span');
    const labels = {
      es: ['Visitas', 'visitas a esta página'],
      en: ['Views', 'views of this page'],
      pt: ['Visitas', 'visitas a esta página'],
      fr: ['Vues', 'vues de cette page'],
    };
    const language = (document.documentElement.lang || 'es').slice(0, 2).toLowerCase();
    const [shortLabel, ariaLabel] = labels[language] || labels.es;
    const locale = language === 'en' ? 'en-US' : language === 'pt' ? 'pt-PT' : language === 'fr' ? 'fr-FR' : 'es-ES';
    const formattedViews = Number(views).toLocaleString(locale);
    counter.className = 'st-page-counter';
    counter.textContent = `${shortLabel}: ${formattedViews}`;
    counter.setAttribute('aria-label', `${formattedViews} ${ariaLabel}`);
    if (!counter.isConnected) footer.append(counter);
  }

  async function count() {
    const url = new URL(API_ENDPOINT, window.location.href);
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
