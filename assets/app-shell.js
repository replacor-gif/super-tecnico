(() => {
  'use strict';

  const REPLACOR_URL = 'https://www.replacor.com/';

  const tools = [
    { href: 'index.html', label: 'Inicio', short: 'Inicio', color: '#ff7a00', icon: 'home', terms: 'inicio portada herramientas' },
    { href: 'proyectos.html', label: 'Mis proyectos técnicos', short: 'Proyectos', color: '#ffe438', icon: 'project', terms: 'proyectos guardar obra instalación resultados mediciones planos pdf' },
    { href: 'climatizacion.html', label: 'Climatización', short: 'Clima', color: '#00c8ff', icon: 'fan', terms: 'clima hvac errores códigos marcas aire acondicionado' },
    { href: 'frigorista.html', label: 'Asistente frigorista', short: 'Frigorista', color: '#00f0d0', icon: 'gauge', terms: 'frigorista refrigerante presión temperatura evaporación condensación recalentamiento subenfriamiento' },
    { href: 'conductos.html', label: 'Diseño de conductos', short: 'Conductos', color: '#51ff7d', icon: 'duct', terms: 'conductos diseño instalación estancias rejillas caudal distribución aire' },
    { href: 'ventilacion.html', label: 'Ventilación y extracción', short: 'Ventilación', color: '#ff3fa7', icon: 'airflow', terms: 'ventilación extracción turbina rejillas caudal volumen renovaciones rite cte hs3 garaje oficina vivienda' },
    { href: 'tuberias-frigorificas.html', label: 'Tuberías frigoríficas', short: 'Tuberías', color: '#00eaff', icon: 'refrigerantPipe', terms: 'tuberías frigoríficas refrigerante cobre sifón aceite doble montante aislamiento armaflex rite rsif presupuesto mediciones' },
    { href: 'desagues-condensados.html', label: 'Desagües de condensados', short: 'Desagües', color: '#00eaff', icon: 'drain', terms: 'desagüe condensados tubería pendiente máquinas aire acondicionado caudal agua' },
    { href: 'normativa.html', label: 'Normativa técnica', short: 'Normativa', color: '#ffe438', icon: 'rules', terms: 'reglamentos legislación rebt rite rsif rat rlat cte fontanería electricidad buscar' },
    { href: 'calculadoras.html', label: 'Calculadoras', short: 'Cálculos', color: '#ff8a00', icon: 'calculator', terms: 'cálculo electricidad taller ley ohm electrónica' },
    { href: 'componentes.html', label: 'Componentes', short: 'Componentes', color: '#54ff82', icon: 'chip', terms: 'referencias electrónica encapsulado datasheet ficha rápida' },
    { href: 'conectores.html', label: 'Conectores y pinouts', short: 'Conectores', color: '#00eaff', icon: 'connector', terms: 'conectores cables pinout contactos usb hdmi ethernet can obd m12 sata audio' },
    { href: 'plataformas-embebidas.html', label: 'Plataformas embebidas', short: 'Embebidas', color: '#ffe438', icon: 'chip', terms: 'arduino esp raspberry stm32 microcontrolador linux fpga tinyml matter placa desarrollo' },
    { href: 'smd.html', label: 'Identificador SMD', short: 'SMD', color: '#ff3fa7', icon: 'smd', terms: 'marcado código componente placa' },
    { href: 'averias.html', label: 'Averías reales', short: 'Averías', color: '#ffea36', icon: 'warning', terms: 'avería reparación placa síntoma solución' },
    { href: 'comparador.html', label: 'Comparador', short: 'Comparar', color: '#a66bff', icon: 'compare', terms: 'comparar referencias sustitución equivalencia' },
    { href: 'electronica-placas.html', label: 'Electrónica de placas', short: 'Electrónica', color: '#b46cff', icon: 'signal', terms: 'electrónica formación inverter pcb fuente potencia' },
    { href: 'electroia.html', label: 'ElectroIA', short: 'ElectroIA', color: '#ffe438', icon: 'omega', terms: 'electroia ia motor diagramas esquemas eléctricos electrónicos unifilar multifilar símbolos json svg' },
    { href: 'simbolos.html', label: 'Esquemas y símbolos', short: 'Esquemas', color: '#00e6c7', icon: 'diagram', terms: 'símbolos diagramas esquemas eléctricos electrónicos curso' },
    { href: 'formacion-climatizacion.html', label: 'Formación HVAC', short: 'Formación', color: '#2693ff', icon: 'learn', terms: 'curso formación climatización aprender' },
    { href: 'feedback.html', label: 'Ideas y mejoras', short: 'Mejoras', color: '#ff5e66', icon: 'idea', terms: 'error sugerencia idea ayuda feedback' },
  ];

  const icons = {
    menu: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>',
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 5 14 14M19 5 5 19"/></svg>',
    search: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.5"/><path d="m15.8 15.8 4.2 4.2"/></svg>',
    home: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="m7 23 17-15 17 15v18H29V29H19v12H7z"/><path class="detail" d="M13 20h22"/></svg>',
    project: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M7 12h13l4 5h17v25H7z"/><path d="M12 24h24M12 31h16M12 37h20"/><circle class="detail" cx="37" cy="12" r="7"/><path class="detail" d="M37 8v8M33 12h8"/></svg>',
    fan: '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="5"/><path d="M24 19c-4-9 1-14 6-13 7 2 7 12-1 17M29 24c9-4 14 1 13 6-2 7-12 7-17-1M24 29c4 9-1 14-6 13-7-2-7-12 1-17M19 24c-9 4-14-1-13-6 2-7 12-7 17 1"/><circle class="detail" cx="24" cy="24" r="19"/></svg>',
    gauge: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M8 36a18 18 0 1 1 32 0"/><path d="M24 14v4M12 24h4M32 24h4M16 17l3 3M32 17l-3 3M24 28l10-8"/><circle cx="24" cy="28" r="3"/><path class="detail" d="M13 36h22"/></svg>',
    duct: '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="17" y="17" width="14" height="14" rx="3"/><circle cx="24" cy="24" r="4"/><path d="M4 24h13M31 24h13M10 24V10M38 24v14M5 7h10v5H5zM33 36h10v5H33z"/><path class="detail" d="M24 20c5 2 5 6 0 8M20 24c2 5 6 5 8 0"/></svg>',
    airflow: '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="6"/><path d="M24 18c-5-11 2-16 8-14 8 3 7 14-2 19M30 24c11-5 16 2 14 8-3 8-14 7-19-2M24 30c5 11-2 16-8 14-8-3-7-14 2-19"/><path d="M3 14h11M8 9l6 5-6 5M45 35H34M40 30l-6 5 6 5"/><path class="detail" d="M5 24h8M43 24h-8"/></svg>',
    refrigerantPipe: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M5 36h13V12h12v24h13"/><path d="M12 36q0 7 6 7t6-7M30 12q0-7 6-7t6 7"/><path class="detail" d="M7 31h7M34 17h7"/><circle cx="24" cy="24" r="4"/></svg>',
    drain: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M5 10h17v11h11v10h10M13 10v7h9M33 21v10"/><path d="M36 35c0 5-3 8-7 8s-7-3-7-8c0-4 7-12 7-12s7 8 7 12z"/><path class="detail" d="M8 6h17M39 27h5"/></svg>',
    rules: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M6 8h13c4 0 5 3 5 6v28c0-4-3-6-7-6H6zM42 8H29c-4 0-5 3-5 6v28c0-4 3-6 7-6h11z"/><path d="M11 16h8M11 22h8M29 16h8M29 22h8M29 28h6"/><path class="detail" d="M24 14v28"/></svg>',
    calculator: '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="8" y="5" width="32" height="38" rx="5"/><path d="M14 11h20v8H14zM15 26h3M24 26h3M33 26h1M15 34h3M24 34h3M33 34h1"/><path class="detail" d="M13 22h22"/></svg>',
    chip: '<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="12" y="12" width="24" height="24" rx="3"/><rect x="18" y="18" width="12" height="12" rx="1"/><path d="M17 5v7M24 5v7M31 5v7M17 36v7M24 36v7M31 36v7M5 17h7M5 24h7M5 31h7M36 17h7M36 24h7M36 31h7"/></svg>',
    connector: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M8 18h13v12H8zM27 15h13v18H27zM21 21h6M21 27h6M12 13V8M17 13V8M31 15v-5M36 15v-5M31 33v5M36 33v5"/><circle class="detail" cx="13" cy="24" r="2"/><circle class="detail" cx="18" cy="24" r="2"/><path class="detail" d="M31 20h5M31 24h5M31 28h5"/></svg>',
    smd: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M10 15h28v18H10zM4 18h6M4 24h6M4 30h6M38 18h6M38 24h6M38 30h6"/><path class="detail" d="M15 20h18M15 25h12M15 29h9"/></svg>',
    warning: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 6 44 41H4zM24 17v12M24 35v1"/><path class="detail" d="M10 38h28"/></svg>',
    compare: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M7 15h29M30 9l6 6-6 6M41 33H12M18 27l-6 6 6 6"/><path class="detail" d="M8 9v12M40 27v12"/></svg>',
    signal: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M5 25h7l4-13 7 25 6-19 4 12h10"/><rect class="detail" x="4" y="6" width="40" height="36" rx="4"/></svg>',
    omega: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M14 40H5v-7h7c-4-4-6-9-6-14C6 9 14 3 24 3s18 6 18 16c0 5-2 10-6 14h7v7h-9v-7c4-3 6-8 6-14 0-8-7-14-16-14S8 11 8 19c0 6 2 11 6 14z"/><path class="detail" d="M18 40h12M24 10v7M17 15l5 5M31 15l-5 5"/></svg>',
    diagram: '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="9" cy="12" r="4"/><circle cx="39" cy="12" r="4"/><circle cx="9" cy="36" r="4"/><circle cx="39" cy="36" r="4"/><path d="M13 12h10v24H13M27 12h8M23 24h16v8"/><path class="detail" d="M29 9v6M33 9v6"/></svg>',
    learn: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="m5 17 19-9 19 9-19 9zM12 21v12c7 7 17 7 24 0V21M43 17v15"/><circle cx="43" cy="35" r="2"/></svg>',
    idea: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M34 30c4-3 7-8 7-14C41 7 33 1 24 1S7 7 7 16c0 6 3 11 7 14 3 2 4 5 4 8h12c0-3 1-6 4-8zM18 43h12M19 38h10"/><path class="detail" d="M24 8v5M12 16h5M31 16h5"/></svg>',
    updates: '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 5v8M24 35v8M5 24h8M35 24h8M10.6 10.6l5.7 5.7M31.7 31.7l5.7 5.7M37.4 10.6l-5.7 5.7M16.3 31.7l-5.7 5.7"/><circle cx="24" cy="24" r="7"/><path class="detail" d="M24 2v3M24 43v3"/></svg>',
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
      if (!header.querySelector('.st-replacor-home')) {
        const replacorLink = document.createElement('a');
        replacorLink.className = 'st-replacor-home';
        replacorLink.href = REPLACOR_URL;
        replacorLink.setAttribute('aria-label', 'Volver a la página principal de REPLACOR');
        replacorLink.innerHTML = '<b>R</b><span>REPLACOR.COM</span>';
        header.append(replacorLink);
      }
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
        <button class="st-install-app" type="button" data-st-install hidden><span>${icons.project}</span><span><strong>Instalar Super Técnico</strong><small>Acceso directo y herramientas disponibles sin cobertura</small></span><b>INSTALAR</b></button>
        <nav class="st-drawer-grid" aria-label="Todas las herramientas">${tools.map(tool => toolLink(tool)).join('')}</nav>
        <a class="st-drawer-updates${currentFile() === 'actualizaciones.html' ? ' is-active' : ''}" href="actualizaciones.html" style="--tool-color:#ffe438"><span class="st-tool-icon">${icons.updates}</span><span><strong>Últimas mejoras</strong><small>Consulta cómo sigue creciendo la aplicación</small></span><b>VER →</b></a>
        <a class="st-drawer-replacor" href="${REPLACOR_URL}"><b>R</b><span><strong>Volver a REPLACOR.COM</strong><small>Página principal del ecosistema</small></span><em>→</em></a>
        <div class="st-drawer-foot"><strong>TÉCNICA REAL.</strong><span>DECISIONES RÁPIDAS.</span></div>
      </aside>
      <nav class="st-bottom-nav" aria-label="Navegación rápida">
        ${tools.filter(tool => ['index.html', 'proyectos.html', 'frigorista.html', 'conductos.html'].includes(tool.href)).map(tool => toolLink(tool, 'st-bottom-link')).join('')}
        <button class="st-bottom-link st-bottom-more" type="button" data-st-open style="--tool-color:#ff3fa7"><span class="st-tool-icon">${icons.menu}</span><span>Más</span></button>
      </nav>`;
    document.body.append(...shell.childNodes);

    const drawer = document.getElementById('stAppDrawer');
    const backdrop = document.querySelector('.st-drawer-backdrop');
    const triggers = document.querySelectorAll('.st-menu-trigger, [data-st-open]');
    const closeButtons = document.querySelectorAll('[data-st-close]');
    const search = drawer.querySelector('input[type="search"]');
    const drawerTools = [...drawer.querySelectorAll('[data-st-tool]')];
    const installButton = drawer.querySelector('[data-st-install]');
    let installPrompt = null;

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

    window.addEventListener('beforeinstallprompt', event => {
      event.preventDefault();
      installPrompt = event;
      installButton.hidden = false;
    });
    installButton.addEventListener('click', async () => {
      if (!installPrompt) return;
      installPrompt.prompt();
      await installPrompt.userChoice;
      installPrompt = null;
      installButton.hidden = true;
    });
    window.addEventListener('appinstalled', () => { installButton.hidden = true; });

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

  function enableProgressiveApp() {
    if (!document.querySelector('link[rel="manifest"]')) {
      const manifest = document.createElement('link');
      manifest.rel = 'manifest';
      manifest.href = 'manifest.webmanifest';
      document.head.appendChild(manifest);
    }
    if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) {
      window.addEventListener('load', () => navigator.serviceWorker.register('service-worker.js').catch(() => {}), { once: true });
    }
  }

  enableProgressiveApp();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', installShell);
  else installShell();
})();
