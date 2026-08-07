'use strict';

(() => {
  const copy = {
    es: {
      title: 'Datasheets y documentación',
      text: 'Busca la referencia exacta en fuentes oficiales y distribuidores autorizados. La búsqueda funciona aunque el componente todavía no esté en nuestra base.',
      exact: 'Búsqueda exacta', official: 'Fabricante', distributor: 'Distribuidor autorizado',
      broad: 'Búsqueda amplia', local: 'Documento registrado', open: 'Consultar',
      warning: 'Confirma siempre fabricante, sufijo, encapsulado y revisión antes de usar los valores.',
      known: 'Documento ya localizado en Super Técnico', sources: 'Fuentes de consulta',
      optional: '¿Necesitas ampliar la información? Buscar datasheet',
      optionalHint: 'Opción secundaria · abre fuentes externas',
    },
    en: {
      title: 'Datasheets and documentation',
      text: 'Search the exact reference in official sources and authorised distributors. Search works even when the part is not yet in our database.',
      exact: 'Exact search', official: 'Manufacturer', distributor: 'Authorised distributor',
      broad: 'Broad search', local: 'Registered document', open: 'Open',
      warning: 'Always confirm manufacturer, suffix, package and revision before using any value.',
      known: 'Document already located by Super Técnico', sources: 'Search sources',
      optional: 'Need more information? Search for a datasheet',
      optionalHint: 'Secondary option · opens external sources',
    },
    pt: {
      title: 'Datasheets e documentação',
      text: 'Procure a referência exata em fontes oficiais e distribuidores autorizados, mesmo que a peça ainda não esteja na nossa base.',
      exact: 'Pesquisa exata', official: 'Fabricante', distributor: 'Distribuidor autorizado',
      broad: 'Pesquisa ampla', local: 'Documento registado', open: 'Consultar',
      warning: 'Confirme sempre fabricante, sufixo, encapsulamento e revisão antes de utilizar os valores.',
      known: 'Documento já localizado pelo Super Técnico', sources: 'Fontes de consulta',
      optional: 'Precisa de mais informação? Procurar datasheet',
      optionalHint: 'Opção secundária · abre fontes externas',
    },
    fr: {
      title: 'Datasheets et documentation',
      text: 'Recherchez la référence exacte dans les sources officielles et chez les distributeurs agréés, même si elle manque dans notre base.',
      exact: 'Recherche exacte', official: 'Fabricant', distributor: 'Distributeur agréé',
      broad: 'Recherche étendue', local: 'Document enregistré', open: 'Consulter',
      warning: 'Vérifiez toujours fabricant, suffixe, boîtier et révision avant d’utiliser les valeurs.',
      known: 'Document déjà localisé par Super Técnico', sources: 'Sources de recherche',
      optional: 'Besoin de plus d’informations ? Rechercher un datasheet',
      optionalHint: 'Option secondaire · ouvre des sources externes',
    },
  };

  const manufacturerSites = [
    [/(INFINEON|INTERNATIONAL RECTIFIER|CYPRESS)/i, 'infineon.com'],
    [/(TEXAS INSTRUMENTS|\bTI\b)/i, 'ti.com'],
    [/(STMICRO|STMICROELECTRONICS|\bST\b)/i, 'st.com'],
    [/(ONSEMI|ON SEMICONDUCTOR|FAIRCHILD)/i, 'onsemi.com'],
    [/(NXP|PHILIPS SEMICONDUCTORS)/i, 'nxp.com'],
    [/(MICROCHIP|ATMEL)/i, 'microchip.com'],
    [/(ANALOG DEVICES|LINEAR TECHNOLOGY|MAXIM)/i, 'analog.com'],
    [/(RENESAS|HITACHI SEMICONDUCTOR|NEC ELECTRONICS)/i, 'renesas.com'],
    [/(ROHM)/i, 'rohm.com'],
    [/(TOSHIBA)/i, 'toshiba.semicon-storage.com'],
    [/(MITSUBISHI ELECTRIC)/i, 'mitsubishielectric.com'],
    [/(FUJI ELECTRIC)/i, 'fujielectric.com'],
    [/(SEMITOP|SEMIKRON|DANFOSS)/i, 'danfoss.com'],
    [/(VISHAY)/i, 'vishay.com'],
    [/(Nexperia)/i, 'nexperia.com'],
    [/(DIODES INC)/i, 'diodes.com'],
    [/(LITTELFUSE|IXYS)/i, 'littelfuse.com'],
    [/(SANKEN)/i, 'sanken-ele.co.jp'],
    [/(POWER INTEGRATIONS)/i, 'power.com'],
    [/(MONOLITHIC POWER|\bMPS\b)/i, 'monolithicpower.com'],
    [/(SILICON LABS)/i, 'silabs.com'],
    [/(NATIONAL SEMICONDUCTOR)/i, 'ti.com'],
  ];

  function language() { return window.ST_I18N?.language || document.documentElement.lang || 'es'; }
  function t(key) { return copy[language()]?.[key] || copy.es[key] || key; }
  function esc(value) {
    return String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  }
  function cleaned(value) { return String(value || '').trim().replace(/\s+/g, ' '); }
  function google(query) { return `https://www.google.com/search?q=${encodeURIComponent(query)}`; }

  function sources(partNumber, manufacturer = '', knownUrl = '') {
    const part = cleaned(partNumber);
    const maker = cleaned(manufacturer);
    const exact = `"${part}" datasheet filetype:pdf`;
    const items = [];
    if (/^https?:\/\//i.test(knownUrl || '')) {
      items.push({name: t('known'), kind: t('local'), confidence: 'official', url: knownUrl});
    }
    const match = manufacturerSites.find(([pattern]) => pattern.test(maker));
    if (match) {
      items.push({
        name: maker || match[1].source,
        kind: t('official'),
        confidence: 'official',
        url: google(`site:${match[1]} ${exact}`),
      });
    }
    items.push(
      {name: 'Mouser', kind: t('distributor'), confidence: 'authorised', url: `https://www.mouser.es/c/?q=${encodeURIComponent(part)}`},
      {name: 'DigiKey', kind: t('distributor'), confidence: 'authorised', url: `https://www.digikey.es/en/products/result?keywords=${encodeURIComponent(part)}`},
      {name: 'Farnell', kind: t('distributor'), confidence: 'authorised', url: `https://es.farnell.com/w/search?st=${encodeURIComponent(part)}`},
      {name: 'TME', kind: t('distributor'), confidence: 'authorised', url: `https://www.tme.eu/es/katalog/?search=${encodeURIComponent(part)}`},
      {name: 'Octopart', kind: t('broad'), confidence: 'broad', url: `https://octopart.com/search?q=${encodeURIComponent(part)}`},
      {name: 'Google PDF', kind: t('exact'), confidence: 'broad', url: google(exact)},
    );
    return items;
  }

  function render(partNumber, manufacturer = '', knownUrl = '', compact = false) {
    const part = cleaned(partNumber);
    if (!part) return '';
    const cards = sources(part, manufacturer, knownUrl).map(source => `
      <a class="datasheet-source datasheet-${esc(source.confidence)}" href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">
        <span><strong>${esc(source.name)}</strong><small>${esc(source.kind)}</small></span>
        <span class="datasheet-open">${esc(t('open'))} ↗</span>
      </a>`).join('');
    return `<section class="datasheet-finder${compact ? ' datasheet-compact' : ''}" data-datasheet-part="${esc(part)}">
      <div class="datasheet-heading">
        <div><p class="datasheet-kicker">${esc(t('exact'))}</p><h3>${esc(t('title'))}: <code>${esc(part)}</code></h3></div>
        <span class="datasheet-free">0 €</span>
      </div>
      ${compact ? '' : `<p>${esc(t('text'))}</p>`}
      <div class="datasheet-sources" aria-label="${esc(t('sources'))}">${cards}</div>
      <p class="datasheet-caution">${esc(t('warning'))}</p>
    </section>`;
  }

  function renderOptional(partNumber, manufacturer = '', knownUrl = '') {
    const part = cleaned(partNumber);
    if (!part) return '';
    return `<details class="datasheet-option">
      <summary><span><strong>${esc(t('optional'))}</strong><small>${esc(t('optionalHint'))}</small></span><span aria-hidden="true">+</span></summary>
      ${render(part, manufacturer, knownUrl)}
    </details>`;
  }

  window.ST_DATASHEETS = {render, renderOptional, sources};
})();
