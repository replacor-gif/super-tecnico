(() => {
  'use strict';

  const tools = [
    { href: 'index.html', label: 'Inicio', short: 'Inicio', color: '#ff7a00', icon: 'home', terms: 'inicio portada herramientas' },
    { href: 'climatizacion.html', label: 'Climatización', short: 'Clima', color: '#00c8ff', icon: 'fan', terms: 'clima hvac errores códigos marcas aire acondicionado' },
    { href: 'frigorista.html', label: 'Asistente frigorista', short: 'Frigorista', color: '#00f0d0', icon: 'gauge', terms: 'frigorista refrigerante presión temperatura evaporación condensación recalentamiento subenfriamiento' },
    { href: 'conductos.html', label: 'Diseño de conductos', short: 'Conductos', color: '#51ff7d', icon: 'duct', terms: 'conductos diseño instalación estancias rejillas caudal distribución aire' },
    { href: 'calculadoras.html', label: 'Calculadoras', short: 'Cálculos', color: '#ff8a00', icon: 'calculator', terms: 'cálculo electricidad taller ley ohm electrónica' },
    { href: 'componentes.html', label: 'Componentes', short: 'Componentes', color: '#54ff82', icon: 'chip', terms: 'referencias electrónica encapsulado datasheet ficha rápida' },
    { href: 'smd.html', label: 'Identificador SMD', short: 'SMD', color: '#ff3fa7', icon: 'smd', terms: 'marcado código componente placa' },
    { href: 'averias.html', label: 'Averías reales', short: 'Averías', color: '#ffea36', icon: 'warning', terms: 'avería reparación placa síntoma solución' },
    { href: 'comparador.html', label: 'Comparador', short: 'Comparar', color: '#a66bff', icon: 'compare', terms: 'comparar referencias sustitución equivalencia' },
    { href: 'electronica-placas.html', label: 'Electrónica de placas', short: 'Electrónica', color: '#b46cff', icon: 'signal', terms: 'electrónica formación inverter pcb fuente potencia' },
    { href: 'simbolos.html', label: 'Esquemas y símbolos', short: 'Esquemas', color: '#00e6c7', icon: 'diagram', terms: 'símbolos diagramas esquemas eléctricos electrónicos curso' },
    { href: 'formacion-climatizacion.html', label: 'Formación HVAC', short: 'Formación', color: '#2693ff', icon: 'learn', terms: 'curso formación climatización aprender' },
    { href: 'feedback.html', label: 'Ideas y mejoras', short: 'Mejoras', color: '#ff5e66', icon: 'idea', terms: 'error sugerencia idea ayuda feedback' },
  ];

  const icons = {
    menu: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>',
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 5 14 14M19 5 5 19"/></svg>',
    search: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.5"/><path d="m15.8 15.8 4.2 4.2"/></svg>',
    home: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="m7 23 17-15 17 15v18H29V29H19v12H7z"/><path class="detail" d="M13 20h22"/></svg>',
    fan: '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="5"/><path d="M24 19c-4-9 1-14 6-13 7 2 7 12-1 17M29 24c9-4 14 1 13 6-2 7-12 7-17-1M24 29c4 9-1 14-6 13-7-2-7-12 1-17M19 24c-9 4-14-1-13-6 2-7 12-7 17 1"/><circle class="detail" cx="24" cy="24" r="19"/></svg>',
    gauge: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M8 36a18 18 0 1 1 32 0"/><path d="M24 14v4M12 24h4M32 24h4M16 17l3 3M32 17l-3 3M24 28l10-8"/><circle cx="24" cy="28" r="3"/><path class="detail" d="M13 36h22"/></svg>',
    duct: '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="17" y="17" width="14" height="14" rx="3"/><circle cx="24" cy="24" r="4"/><path d="M4 24h13M31 24h13M10 24V10M38 24v14M5 7h10v5H5zM33 36h10v5H33z"/><path class="detail" d="M24 20c5 2 5 6 0 8M20 24c2 5 6 5 8 0"/></svg>',
    calculator: '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="8" y="5" width="32" height="38" rx="5"/><path d="M14 11h20v8H14zM15 26h3M24 26h3M33 26h1M15 34h3M24 34h3M33 34h1"/><path class="detail" d="M13 22h22"/></svg>',
    chip: '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="12" y="12" width="24" height="24" rx="3"/><rect x="18" y="18" width="12" height="12" rx="1"/><path d="M17 5v7M24 5v7M31 5v7M17 36v7M24 36v7M31 36v7M5 17h7M5 24h7M5 31h7M36 17h7M36 24h7M36 31h7"/></svg>',
    smd: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M10 15h28v18H10zM4 18h6M4 24h6M4 30h6M38 18h6M38 24h6M38 30h6"/><path class="detail" d="M15 20h18M15 25h12M15 29h9"/></svg>',
    warning: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 6 44 41H4zM24 17v12M24 35v1"/><path class="detail" d="M10 38h28"/></svg>',
    compare: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M7 15h29M30 9l6 6-6 6M41 33H12M18 27l-6 6 6 6"/><path class="detail" d="M8 9v12M40 27v12"/></svg>',
    signal: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M5 25h7l4-13 7 25 6-19 4 12h10"/><rect class="detail" x="4" y="6" width="40" height="36" rx="4"/></svg>',
    diagram: '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="9" cy="12" r="4"/><circle cx="39" cy="12" r="4"/><circle cx="9" cy="36" r="4"/><circle cx="39" cy="36" r="4"/><path d="M13 12h10v24H13M27 12h8M23 24h16v8"/><path class="detail" d="M29 9v6M33 9v6"/></svg>',
    learn: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="m5 17 19-9 19 9-19 9zM12 21v12c7 7 17 7 24 0V21M43 17v15"/><circle cx="43" cy="35" r="2"/></svg>',
    idea: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M34 30c4-3 7-8 7-14C41 7 33 1 24 1S7 7 7 16c0 6 3 11 7 14 3 2 4 5 4 8h12c0-3 1-6 4-8zM18 43h12M19 38h10"/><path class="detail" d="M24 8v5M12 16h5M31 16h5"/></svg>',
  };

  function currentFile() {
    return (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  }

  function toolLink(tool, className = 'st-drawer-tool') {
    const active = currentFile() === tool.href;
    return `<a class="${className}${active ? ' is-active' : ''}" href="${tool.href}" style="--tool-color:${tool.color}"${active ? ' aria-current="page"' : ''} data-st-tool data-search="${tool.label} ${tool.terms}"><span class="st-tool-icon">${icons[tool.icon]}</span><span>${tool.label}</span></a>`;
  }

  function installShell() {
    if (document.querySelector('.st-app-drawer')) return;
    document.documentElement.classList.add('st-app-ready');

    const header = document.querySelector('body > header');
    if (header) {
      header.classList.add('st-main-header');
      const trigger = document.createElement('button');
      trigger.className = 'st-menu-trigger';
      trigger.type = 'button';
      trigger.setAttribute('aria-controls', 'stAppDrawer');
      trigger.setAttribute('aria-expanded', 'false');
      trigger.setAttribute('aria-label', 'Abrir menú de herramientas');
      trigger.innerHTML = `${icons.menu}<span>Menú</span>`;
      header.prepend(trigger);
    }

    const shell = document.createElement('div');
    shell.innerHTML = `
      <div class="st-drawer-backdrop" data-st-close hidden></div>
      <aside class="st-app-drawer" id="stAppDrawer" aria-label="Herramientas de Super Técnico" aria-hidden="true">
        <div class="st-drawer-head">
          <a class="st-drawer-brand" href="index.html"><img src="assets/super-tecnico-logo.png" alt=""><span><strong>SUPER <b>TÉCNICO</b></strong><small>REPLACOR · PLATAFORMA PROFESIONAL</small></span></a>
          <button class="st-drawer-close" type="button" data-st-close aria-label="Cerrar menú">${icons.close}</button>
        </div>
        <label class="st-drawer-search"><span>${icons.search}</span><input type="search" autocomplete="off" placeholder="Buscar una herramienta…" aria-label="Buscar una herramienta"></label>
        <div class="st-drawer-status"><span>ACCESO RÁPIDO</span><b>${tools.length - 1} HERRAMIENTAS</b></div>
        <nav class="st-drawer-grid" aria-label="Todas las herramientas">${tools.map(tool => toolLink(tool)).join('')}</nav>
        <div class="st-drawer-foot"><strong>TÉCNICA REAL.</strong><span>DECISIONES RÁPIDAS.</span></div>
      </aside>
      <nav class="st-bottom-nav" aria-label="Navegación rápida">
        ${tools.filter(tool => ['index.html', 'climatizacion.html', 'frigorista.html', 'conductos.html'].includes(tool.href)).map(tool => toolLink(tool, 'st-bottom-link')).join('')}
        <button class="st-bottom-link st-bottom-more" type="button" data-st-open style="--tool-color:#ff3fa7"><span class="st-tool-icon">${icons.menu}</span><span>Más</span></button>
      </nav>`;
    document.body.append(...shell.childNodes);

    const drawer = document.getElementById('stAppDrawer');
    const backdrop = document.querySelector('.st-drawer-backdrop');
    const triggers = document.querySelectorAll('.st-menu-trigger, [data-st-open]');
    const closeButtons = document.querySelectorAll('[data-st-close]');
    const search = drawer.querySelector('input[type="search"]');
    const drawerTools = [...drawer.querySelectorAll('[data-st-tool]')];

    const setOpen = open => {
      document.body.classList.toggle('st-drawer-open', open);
      drawer.classList.toggle('is-open', open);
      drawer.setAttribute('aria-hidden', String(!open));
      backdrop.hidden = !open;
      document.querySelector('.st-menu-trigger')?.setAttribute('aria-expanded', String(open));
      if (open) setTimeout(() => search.focus(), 80);
      else search.value = '';
      drawerTools.forEach(link => { link.hidden = false; });
    };

    triggers.forEach(button => button.addEventListener('click', () => setOpen(true)));
    closeButtons.forEach(button => button.addEventListener('click', () => setOpen(false)));
    document.addEventListener('keydown', event => { if (event.key === 'Escape') setOpen(false); });
    search.addEventListener('input', () => {
      const query = search.value.trim().toLocaleLowerCase('es');
      drawerTools.forEach(link => {
        link.hidden = query && !link.dataset.search.toLocaleLowerCase('es').includes(query);
      });
    });

    const portalSearch = document.querySelector('[data-st-portal-search]');
    if (portalSearch) {
      portalSearch.addEventListener('input', () => {
        const query = portalSearch.value.trim().toLocaleLowerCase('es');
        document.querySelectorAll('.tool-card').forEach(card => {
          card.hidden = query && !card.textContent.toLocaleLowerCase('es').includes(query);
        });
      });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', installShell);
  else installShell();
})();
