(() => {
  'use strict';

  const API_ENDPOINT = new URL('api/index.php', document.baseURI).href;
  const CLIENT_KEY = 'st.community.client.v1';
  const RATING_DISMISS_KEY = 'st.rating.dismissed.v1.';
  const ELECTROIA_PATH = 'archivo-tecnico-47097e44267b9cb111636b84823f1d47/';
  const ANALYTICS_PATH = 'analitica-privada.html';
  const BACKLOG_PATH = 'bitacora-privada.html';
  const CONTENT_EDITOR_PATH = 'editor-contenidos.html';

  const RATING_TEXT = {
    es: {
      question: '¿Te ha resultado útil?', like: 'Me gusta', dislike: 'No me gusta', close: 'Cerrar valoración',
      thanks: 'Gracias. Tu voto ya está contado.', improve: '¿Qué mejorarías?',
      improveHelp: 'Cuéntamelo en una frase. Tu comentario servirá para decidir el próximo cambio.',
      placeholder: 'Por ejemplo: haría más sencillo…', send: 'Enviar mejora', later: 'Ahora no', sent: 'Gracias. Leeremos tu propuesta.', error: 'No se ha podido guardar. Inténtalo de nuevo.',
    },
    en: {
      question: 'Was this useful?', like: 'Like', dislike: 'Dislike', close: 'Close rating', thanks: 'Thanks. Your vote has been counted.',
      improve: 'What would you improve?', improveHelp: 'Tell us briefly. Your comment will help decide the next change.',
      placeholder: 'For example: I would simplify…', send: 'Send suggestion', later: 'Not now', sent: 'Thanks. We will read your suggestion.', error: 'Could not save it. Please try again.',
    },
    pt: {
      question: 'Foi útil?', like: 'Gosto', dislike: 'Não gosto', close: 'Fechar avaliação', thanks: 'Obrigado. O seu voto foi registado.',
      improve: 'O que melhoraria?', improveHelp: 'Conte-nos numa frase. O comentário ajudará a decidir a próxima melhoria.',
      placeholder: 'Por exemplo: tornaria mais simples…', send: 'Enviar melhoria', later: 'Agora não', sent: 'Obrigado. Vamos ler a sua proposta.', error: 'Não foi possível guardar. Tente novamente.',
    },
    fr: {
      question: 'Cela vous a-t-il été utile ?', like: 'J’aime', dislike: 'Je n’aime pas', close: 'Fermer l’évaluation', thanks: 'Merci. Votre vote est enregistré.',
      improve: 'Que faudrait-il améliorer ?', improveHelp: 'Dites-le en une phrase. Votre avis guidera la prochaine amélioration.',
      placeholder: 'Par exemple : je simplifierais…', send: 'Envoyer', later: 'Plus tard', sent: 'Merci. Nous lirons votre proposition.', error: 'Enregistrement impossible. Réessayez.',
    },
  };

  function pageKey() {
    const file = location.pathname.endsWith('/')
      ? 'index'
      : location.pathname.split('/').filter(Boolean).pop() || 'index';
    const key = file.replace(/\.html?$/i, '').toLowerCase();
    return key === 'index' ? 'inicio' : key.replace(/[^a-z0-9-]/g, '-').slice(0, 64);
  }

  function language() {
    const code = (document.documentElement.lang || 'es').slice(0, 2).toLowerCase();
    return RATING_TEXT[code] ? code : 'es';
  }

  function clientToken() {
    try {
      let token = localStorage.getItem(CLIENT_KEY);
      if (!token) {
        token = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        localStorage.setItem(CLIENT_KEY, token);
      }
      return token;
    } catch (_) {
      return `anonymous-${Date.now()}`;
    }
  }

  function editableText(value) {
    const normalized = String(value || '').replace(/\s+/g, ' ').trim();
    return normalized.length >= 3 && /[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]/.test(normalized) ? normalized : '';
  }

  function contentHash(value) {
    let current = 2166136261;
    for (let index = 0; index < value.length; index += 1) {
      current ^= value.charCodeAt(index);
      current = Math.imul(current, 16777619) >>> 0;
    }
    return current.toString(16).padStart(8, '0');
  }

  function hardcodedContentKey(kind, value, occurrences) {
    const digest = contentHash(`${kind}|${value}`);
    const occurrenceKey = `${kind}.${digest}`;
    occurrences[occurrenceKey] = (occurrences[occurrenceKey] || 0) + 1;
    return `page.${pageKey()}.${kind}.${digest}.${occurrences[occurrenceKey]}`;
  }

  function blockedContentNode(element) {
    return !element || Boolean(element.closest('script,style,template,svg,noscript,[aria-hidden="true"],[data-i18n]'));
  }

  function replaceTextNode(node, value) {
    const original = node.nodeValue || '';
    const leading = original.match(/^\s*/)?.[0] || '';
    const trailing = original.match(/\s*$/)?.[0] || '';
    node.nodeValue = `${leading}${value}${trailing}`;
  }

  async function applyHardcodedContentOverrides() {
    const url = new URL(API_ENDPOINT, window.location.href);
    url.searchParams.set('action', 'content-overrides');
    try {
      const contentOverridesRequest = window.ST_CONTENT_OVERRIDES_REQUEST || fetch(url, {
        cache: 'no-store',
        credentials: 'same-origin',
      }).then(response => response.ok ? response.json() : null).catch(() => null);
      window.ST_CONTENT_OVERRIDES_REQUEST = contentOverridesRequest;
      const data = await contentOverridesRequest;
      if (!data?.ok || !data.items) return;
      const pagePrefix = `page.${pageKey()}.`;
      const overrides = Object.fromEntries(Object.entries(data.items).filter(([key]) => key.startsWith(pagePrefix)));
      if (!Object.keys(overrides).length) return;
      const occurrences = {};
      const textTags = new Set(['A','B','BUTTON','DD','DT','EM','FIGCAPTION','H1','H2','H3','H4','H5','H6','I','LABEL','LEGEND','LI','OPTION','P','SMALL','SPAN','STRONG','SUMMARY','TD','TH']);
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        const parent = node.parentElement;
        if (!parent || !textTags.has(parent.tagName) || blockedContentNode(parent)) continue;
        const value = editableText(node.nodeValue);
        if (!value) continue;
        const key = hardcodedContentKey('text', value, occurrences);
        if (Object.prototype.hasOwnProperty.call(overrides, key)) replaceTextNode(node, String(overrides[key]));
      }
      document.querySelectorAll('[placeholder]:not([data-i18n-placeholder])').forEach(element => {
        if (blockedContentNode(element)) return;
        const value = editableText(element.getAttribute('placeholder'));
        if (!value) return;
        const key = hardcodedContentKey('placeholder', value, occurrences);
        if (Object.prototype.hasOwnProperty.call(overrides, key)) element.setAttribute('placeholder', String(overrides[key]));
      });
      document.querySelectorAll('[aria-label]:not([data-i18n-aria])').forEach(element => {
        if (blockedContentNode(element)) return;
        const value = editableText(element.getAttribute('aria-label'));
        if (!value) return;
        const key = hardcodedContentKey('aria', value, occurrences);
        if (Object.prototype.hasOwnProperty.call(overrides, key)) element.setAttribute('aria-label', String(overrides[key]));
      });
      document.dispatchEvent(new CustomEvent('st:hardcodedcontentready'));
    } catch {
      // Los textos originales permanecen intactos si la API no está disponible.
    }
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
    access.textContent = '\u03a9';
    access.setAttribute('aria-label', 'Acceso privado a ElectroIA');
    const analytics = document.createElement('a');
    analytics.className = 'st-electro-access st-analytics-access';
    analytics.href = ANALYTICS_PATH;
    analytics.textContent = '\u03b2';
    analytics.setAttribute('aria-label', 'Panel privado de análisis de visitas');
    const backlog = document.createElement('a');
    backlog.className = 'st-electro-access st-backlog-access';
    backlog.href = BACKLOG_PATH;
    backlog.textContent = '\u03a3';
    backlog.setAttribute('aria-label', 'Lista privada de ideas y trabajo pendiente');
    tools.append(access, analytics, backlog);
    const editor = document.createElement('a');
    editor.className = 'st-electro-access st-content-editor-access';
    editor.href = CONTENT_EDITOR_PATH;
    editor.textContent = '\u03b5';
    editor.setAttribute('aria-label', 'Editor privado de textos');
    tools.append(editor);
    footer.append(tools);
    return tools;
  }

  function showCounter(views) {
    const tools = footerTools();
    if (!tools) return;
    const counter = tools.querySelector('.st-page-counter') || document.createElement('span');
    const labels = {
      es: ['Visitas', 'visitas a esta página'], en: ['Views', 'views of this page'],
      pt: ['Visitas', 'visitas a esta página'], fr: ['Vues', 'vues de cette page'],
    };
    const code = language();
    const [shortLabel, ariaLabel] = labels[code] || labels.es;
    const locale = code === 'en' ? 'en-US' : code === 'pt' ? 'pt-PT' : code === 'fr' ? 'fr-FR' : 'es-ES';
    const formattedViews = Number(views).toLocaleString(locale);
    counter.className = 'st-page-counter';
    counter.textContent = `${shortLabel}: ${formattedViews}`;
    counter.setAttribute('aria-label', `${formattedViews} ${ariaLabel}`);
    if (!counter.isConnected) tools.prepend(counter);
  }

  async function count() {
    const url = new URL(API_ENDPOINT, window.location.href);
    url.searchParams.set('action', 'page-view');
    const token = clientToken();
    try {
      const response = await fetch(url, {
        method: 'POST', credentials: 'omit',
        headers: { 'Content-Type': 'application/json', 'X-ST-Client': token },
        body: JSON.stringify({ page_key: pageKey(), client_token: token }),
      });
      const data = await response.json();
      if (response.ok && data.ok && Number.isFinite(Number(data.views))) showCounter(data.views);
    } catch {
      // El contador no debe interferir con la consulta técnica si la API no responde.
    }
  }

  function ratingMarkup(copy) {
    return `<button class="st-rating-close" type="button" aria-label="${copy.close}">×</button>
      <div class="st-rating-question"><span>PARTICIPA</span><strong>${copy.question}</strong></div>
      <div class="st-rating-actions">
        <button class="st-rating-vote st-rating-like" type="button" data-rating-vote="like" aria-label="${copy.like}" aria-pressed="false"><i>👍</i><span>${copy.like}</span><b data-rating-count="like">0</b></button>
        <button class="st-rating-vote st-rating-dislike" type="button" data-rating-vote="dislike" aria-label="${copy.dislike}" aria-pressed="false"><i>👎</i><span>${copy.dislike}</span><b data-rating-count="dislike">0</b></button>
      </div>
      <p class="st-rating-status" role="status"></p>
      <form class="st-rating-feedback" hidden>
        <strong>${copy.improve}</strong><p>${copy.improveHelp}</p>
        <textarea name="feedback" rows="3" minlength="3" maxlength="600" required placeholder="${copy.placeholder}"></textarea>
        <div><button type="submit">${copy.send}</button><button type="button" data-rating-later>${copy.later}</button></div>
      </form>`;
  }

  function renderRating(widget, data) {
    widget.querySelector('[data-rating-count="like"]').textContent = Number(data.likes || 0).toLocaleString();
    widget.querySelector('[data-rating-count="dislike"]').textContent = Number(data.dislikes || 0).toLocaleString();
    widget.querySelectorAll('[data-rating-vote]').forEach(button => {
      const active = button.dataset.ratingVote === data.user_vote;
      button.classList.toggle('is-selected', active);
      button.setAttribute('aria-pressed', String(active));
    });
  }

  async function ratingRequest(method, payload = {}) {
    const url = new URL(API_ENDPOINT, window.location.href);
    url.searchParams.set('action', 'page-rating');
    const token = clientToken();
    if (method === 'GET') url.searchParams.set('page_key', pageKey());
    const options = { method, credentials: 'omit', cache: 'no-store', headers: { 'X-ST-Client': token } };
    if (method === 'POST') {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify({ page_key: pageKey(), client_token: token, ...payload });
    }
    const response = await fetch(url, options);
    const data = await response.json().catch(() => null);
    if (!response.ok || !data?.ok) throw new Error(data?.error || 'rating_error');
    return data;
  }

  async function startRating() {
    const key = `${RATING_DISMISS_KEY}${pageKey()}`;
    try { if (sessionStorage.getItem(key)) return; } catch (_) {}
    let data;
    try { data = await ratingRequest('GET'); } catch (_) { return; }
    const copy = RATING_TEXT[language()];
    const widget = document.createElement('aside');
    widget.className = 'st-rating-widget';
    widget.setAttribute('aria-label', copy.question);
    widget.innerHTML = ratingMarkup(copy);
    renderRating(widget, data);
    document.body.append(widget);
    const status = widget.querySelector('.st-rating-status');
    const feedbackForm = widget.querySelector('.st-rating-feedback');
    const setBusy = busy => widget.querySelectorAll('button').forEach(button => { button.disabled = busy; });

    widget.querySelector('.st-rating-close').addEventListener('click', () => {
      widget.classList.remove('is-visible');
      try { sessionStorage.setItem(key, '1'); } catch (_) {}
      setTimeout(() => widget.remove(), 260);
    });
    widget.querySelectorAll('[data-rating-vote]').forEach(button => button.addEventListener('click', async () => {
      const vote = button.dataset.ratingVote;
      setBusy(true);
      status.textContent = '';
      try {
        data = await ratingRequest('POST', { vote, feedback: '' });
        renderRating(widget, data);
        status.textContent = copy.thanks;
        feedbackForm.hidden = vote !== 'dislike';
        if (vote === 'dislike') setTimeout(() => feedbackForm.querySelector('textarea').focus(), 50);
      } catch (_) {
        status.textContent = copy.error;
      } finally {
        setBusy(false);
      }
    }));
    feedbackForm.addEventListener('submit', async event => {
      event.preventDefault();
      const feedback = new FormData(feedbackForm).get('feedback')?.toString().trim() || '';
      if (feedback.length < 3) return;
      setBusy(true);
      try {
        data = await ratingRequest('POST', { vote: 'dislike', feedback });
        renderRating(widget, data);
        feedbackForm.hidden = true;
        status.textContent = copy.sent;
      } catch (_) {
        status.textContent = copy.error;
      } finally {
        setBusy(false);
      }
    });
    widget.querySelector('[data-rating-later]').addEventListener('click', () => { feedbackForm.hidden = true; });
    setTimeout(() => widget.classList.add('is-visible'), 2800);
  }

  function start() {
    applyHardcodedContentOverrides();
    footerTools();
    count();
    startRating();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
