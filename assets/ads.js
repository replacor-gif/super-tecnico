(() => {
  'use strict';

  const CONFIG_URL = 'data/ads-config.json';
  const PUBLISHER_RE = /^ca-pub-\d+$/;
  const SLOT_RE = /^\d+$/;

  function loadAdSenseScript(publisherId) {
    const existing = document.getElementById('super-tecnico-adsense');
    if (existing) return Promise.resolve(existing);

    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.async = true;
      script.crossOrigin = 'anonymous';
      script.id = 'super-tecnico-adsense';
      script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(publisherId)}`;
      script.addEventListener('load', () => resolve(script), {once: true});
      script.addEventListener('error', reject, {once: true});
      document.head.append(script);
    });
  }

  function prepareManualSlots(config) {
    const placements = document.querySelectorAll('[data-ad-placement]');
    const initialized = [];

    placements.forEach(container => {
      const placement = container.dataset.adPlacement || '';
      const slotId = String(config.slots?.[placement] || '').trim();
      if (!SLOT_RE.test(slotId)) return;

      const unit = document.createElement('ins');
      unit.className = 'adsbygoogle';
      unit.style.display = 'block';
      unit.dataset.adClient = config.publisher_id;
      unit.dataset.adSlot = slotId;
      unit.dataset.adFormat = 'auto';
      unit.dataset.fullWidthResponsive = 'true';
      container.replaceChildren(unit);
      container.hidden = false;
      initialized.push(unit);
    });

    return initialized;
  }

  async function initializeAdvertising() {
    try {
      const response = await fetch(CONFIG_URL, {cache: 'no-store'});
      if (!response.ok) return;
      const config = await response.json();
      const publisherId = String(config.publisher_id || '').trim();
      if (config.enabled !== true || !PUBLISHER_RE.test(publisherId)) return;

      config.publisher_id = publisherId;
      const manualSlots = prepareManualSlots(config);
      if (config.auto_ads !== true && manualSlots.length === 0) return;

      await loadAdSenseScript(publisherId);
      manualSlots.forEach(() => {
        try {
          (window.adsbygoogle = window.adsbygoogle || []).push({});
        } catch (error) {
          console.warn('No se pudo inicializar una unidad publicitaria.', error);
        }
      });
    } catch (error) {
      console.warn('La configuración publicitaria no está disponible.', error);
    }
  }

  initializeAdvertising();
})();
