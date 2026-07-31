(() => {
  'use strict';
  const API_ENDPOINT = document.documentElement.dataset.apiEndpoint || 'api/index.php';
  const CLIENT_KEY = 'st.community.client.v1';

  function clientToken() {
    let token = localStorage.getItem(CLIENT_KEY);
    if (!token) {
      token = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      localStorage.setItem(CLIENT_KEY, token);
    }
    return token;
  }

  async function request(action, options = {}) {
    const url = new URL(API_ENDPOINT, window.location.href);
    url.searchParams.set('action', action);
    Object.entries(options.query || {}).forEach(([key, value]) => {
      if (value !== '' && value !== undefined && value !== null) url.searchParams.set(key, String(value));
    });
    const init = {
      method: options.method || (options.body ? 'POST' : 'GET'),
      credentials: 'include',
      headers: {'X-ST-Client': clientToken(), ...(options.headers || {})},
    };
    if (options.body) {
      init.headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify({...options.body, client_token: clientToken()});
    }
    let response;
    try {
      response = await fetch(url, init);
    } catch (error) {
      throw Object.assign(new Error('api_unavailable'), {code: 'api_unavailable', cause: error});
    }
    let data;
    try { data = await response.json(); } catch { data = {ok: false, error: 'invalid_response'}; }
    if (!response.ok || data.ok === false) {
      throw Object.assign(new Error(data.error || `http_${response.status}`), {code: data.error || `http_${response.status}`, status: response.status, data});
    }
    return data;
  }

  window.ST_COMMUNITY_API = {request, clientToken, endpoint: API_ENDPOINT};
})();
