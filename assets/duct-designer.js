(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.STDuctDesigner = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const STORAGE_KEY = 'st.ductDesigner.v1';
  const SIDES = ['left', 'right'];
  const DEFAULTS = Object.freeze({
    projectName: 'Vivienda de prueba',
    ductHeightCm: 25,
    grilleHeightCm: 15,
    machineCapacityFg: 0,
    loadPerM2: 150,
    airflowPer9000: 1200,
    areaPer9000: 900,
    grilleMultiplier: 2,
    minimumDuctWidthCm: 10,
    minimumGrilleWidthCm: 20,
  });

  const EXAMPLE_ROOMS = Object.freeze([
    { id: 'example-l1', side: 'left', name: 'Dormitorio 1', widthM: 3.6, lengthM: 3.2, manualLoadFg: 0 },
    { id: 'example-l2', side: 'left', name: 'Dormitorio 2', widthM: 3.2, lengthM: 3, manualLoadFg: 0 },
    { id: 'example-l3', side: 'left', name: 'Despacho', widthM: 3, lengthM: 2.6, manualLoadFg: 0 },
    { id: 'example-r1', side: 'right', name: 'Salón', widthM: 6, lengthM: 4.2, manualLoadFg: 0 },
    { id: 'example-r2', side: 'right', name: 'Cocina', widthM: 4, lengthM: 3.2, manualLoadFg: 0 },
    { id: 'example-r3', side: 'right', name: 'Dormitorio 3', widthM: 3.4, lengthM: 3.1, manualLoadFg: 0 },
  ]);

  function finite(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function roundUp(value, step = 1) {
    return Math.ceil((value - 1e-9) / step) * step;
  }

  function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
  }

  function normalizeState(input = {}) {
    const rooms = Array.isArray(input.rooms) ? input.rooms : [];
    return {
      projectName: String(input.projectName || DEFAULTS.projectName).slice(0, 70),
      ductHeightCm: clamp(finite(input.ductHeightCm, DEFAULTS.ductHeightCm), 10, 80),
      grilleHeightCm: clamp(finite(input.grilleHeightCm, DEFAULTS.grilleHeightCm), 8, 80),
      machineCapacityFg: Math.max(0, finite(input.machineCapacityFg, 0)),
      loadPerM2: clamp(finite(input.loadPerM2, DEFAULTS.loadPerM2), 50, 350),
      airflowPer9000: clamp(finite(input.airflowPer9000, DEFAULTS.airflowPer9000), 500, 2500),
      areaPer9000: clamp(finite(input.areaPer9000, DEFAULTS.areaPer9000), 300, 1800),
      grilleMultiplier: clamp(finite(input.grilleMultiplier, DEFAULTS.grilleMultiplier), 1, 4),
      minimumDuctWidthCm: clamp(finite(input.minimumDuctWidthCm, DEFAULTS.minimumDuctWidthCm), 5, 40),
      minimumGrilleWidthCm: clamp(finite(input.minimumGrilleWidthCm, DEFAULTS.minimumGrilleWidthCm), 10, 60),
      rooms: rooms
        .filter(room => room && SIDES.includes(room.side))
        .slice(0, 14)
        .map((room, index) => ({
          id: String(room.id || `room-${index + 1}`),
          side: room.side,
          name: String(room.name || `Estancia ${index + 1}`).slice(0, 35),
          widthM: clamp(finite(room.widthM, 1), .5, 50),
          lengthM: clamp(finite(room.lengthM, 1), .5, 50),
          manualLoadFg: Math.max(0, finite(room.manualLoadFg, 0)),
        })),
    };
  }

  function emptyState() {
    return normalizeState({ ...DEFAULTS, rooms: [] });
  }

  function exampleState() {
    return normalizeState({ ...DEFAULTS, rooms: EXAMPLE_ROOMS.map(room => ({ ...room })) });
  }

  function airflowForLoad(loadFg, state) {
    return loadFg * state.airflowPer9000 / 9000;
  }

  function areaForLoad(loadFg, state) {
    return loadFg * state.areaPer9000 / 9000;
  }

  function sizeDuct(loadFg, state) {
    const requiredAreaCm2 = areaForLoad(loadFg, state);
    const rawWidthCm = requiredAreaCm2 / state.ductHeightCm;
    const widthCm = roundUp(Math.max(state.minimumDuctWidthCm, rawWidthCm), 1);
    const actualAreaM2 = widthCm * state.ductHeightCm / 10000;
    const airflowM3h = airflowForLoad(loadFg, state);
    const velocityMps = actualAreaM2 > 0 ? airflowM3h / (actualAreaM2 * 3600) : 0;
    return { widthCm, heightCm: state.ductHeightCm, requiredAreaCm2, airflowM3h, velocityMps };
  }

  function enrichRoom(room, state, sideNumber) {
    const areaM2 = room.widthM * room.lengthM;
    const loadFg = room.manualLoadFg > 0 ? room.manualLoadFg : areaM2 * state.loadPerM2;
    const airflowM3h = airflowForLoad(loadFg, state);
    const branchDuct = sizeDuct(loadFg, state);
    const grilleAreaCm2 = branchDuct.requiredAreaCm2 * state.grilleMultiplier;
    const grilleWidthCm = roundUp(Math.max(state.minimumGrilleWidthCm, grilleAreaCm2 / state.grilleHeightCm), 5);
    return {
      ...room,
      number: sideNumber,
      areaM2,
      loadFg,
      airflowM3h,
      branchDuct,
      grille: { widthCm: grilleWidthCm, heightCm: state.grilleHeightCm },
      source: room.manualLoadFg > 0 ? 'manual' : 'surface',
    };
  }

  function calculateSide(side, rooms, state) {
    const enrichedRooms = rooms.map((room, index) => enrichRoom(room, state, index + 1));
    const sections = enrichedRooms.map((room, index) => {
      const downstreamRooms = enrichedRooms.slice(index);
      const loadFg = downstreamRooms.reduce((sum, item) => sum + item.loadFg, 0);
      return {
        id: `${side}-section-${index + 1}`,
        side,
        number: index + 1,
        roomId: room.id,
        roomName: room.name,
        loadFg,
        roomsRemaining: downstreamRooms.length,
        ...sizeDuct(loadFg, state),
      };
    });
    return {
      side,
      rooms: enrichedRooms,
      sections,
      loadFg: enrichedRooms.reduce((sum, room) => sum + room.loadFg, 0),
      airflowM3h: enrichedRooms.reduce((sum, room) => sum + room.airflowM3h, 0),
    };
  }

  function calculateProject(input = {}) {
    const state = normalizeState(input);
    const left = calculateSide('left', state.rooms.filter(room => room.side === 'left'), state);
    const right = calculateSide('right', state.rooms.filter(room => room.side === 'right'), state);
    const loadFg = left.loadFg + right.loadFg;
    const airflowM3h = left.airflowM3h + right.airflowM3h;
    const suggestedCapacityFg = loadFg > 0 ? roundUp(loadFg, 500) : 0;
    const mainDuct = sizeDuct(loadFg, state);
    const warnings = [];
    if (!state.rooms.length) warnings.push({ level: 'info', text: 'Añade al menos una estancia para construir la red.' });
    if (state.machineCapacityFg > 0 && state.machineCapacityFg < loadFg) {
      warnings.push({ level: 'danger', text: `La máquina indicada queda por debajo de la necesidad estimada en ${Math.ceil(loadFg - state.machineCapacityFg).toLocaleString('es-ES')} frg/h.` });
    } else if (state.machineCapacityFg > 0) {
      warnings.push({ level: 'ok', text: 'La capacidad indicada cubre la necesidad estimada de las estancias.' });
    }
    if (left.loadFg > 0 && right.loadFg > 0) {
      const imbalance = Math.abs(left.loadFg - right.loadFg) / Math.max(left.loadFg, right.loadFg);
      if (imbalance > .45) warnings.push({ level: 'warn', text: 'Los dos lados están muy desequilibrados; revisa el recorrido y el reparto de estancias.' });
    }
    [...left.sections, ...right.sections].forEach(section => {
      if (section.velocityMps > 5.2) warnings.push({ level: 'warn', text: `${sideLabel(section.side)} · tramo ${section.number}: velocidad elevada (${formatNumber(section.velocityMps, 1)} m/s).` });
      if (section.velocityMps > 0 && section.velocityMps < 1.8) warnings.push({ level: 'info', text: `${sideLabel(section.side)} · tramo ${section.number}: velocidad baja (${formatNumber(section.velocityMps, 1)} m/s).` });
    });
    [...left.rooms, ...right.rooms].forEach(room => {
      if (room.grille.widthCm > 120) warnings.push({ level: 'warn', text: `${room.name}: la rejilla resultante es muy ancha; conviene repartirla en dos salidas.` });
    });
    return {
      state,
      sides: { left, right },
      totals: { rooms: state.rooms.length, loadFg, airflowM3h, suggestedCapacityFg, mainDuct },
      warnings: uniqueWarnings(warnings),
    };
  }

  function uniqueWarnings(warnings) {
    const seen = new Set();
    return warnings.filter(item => {
      if (seen.has(item.text)) return false;
      seen.add(item.text);
      return true;
    });
  }

  function sideLabel(side) {
    return side === 'left' ? 'Ramal izquierdo' : 'Ramal derecho';
  }

  function formatNumber(value, decimals = 0) {
    return finite(value).toLocaleString('es-ES', { maximumFractionDigits: decimals, minimumFractionDigits: decimals });
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  function escapeXml(value) {
    return escapeHtml(value);
  }

  function diagramGeometry(result) {
    const maxRooms = Math.max(1, result.sides.left.rooms.length, result.sides.right.rooms.length);
    const spacing = 190;
    const half = 180 + maxRooms * spacing;
    return { width: half * 2, height: 760, centerX: half, centerY: 370, spacing, maxRooms };
  }

  function renderDiagramSvg(result) {
    const geometry = diagramGeometry(result);
    const { width, height, centerX, centerY, spacing } = geometry;
    const machineLoad = formatNumber(result.totals.loadFg, 0);
    const machineFlow = formatNumber(result.totals.airflowM3h, 0);
    const parts = [`<svg class="duct-network-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Plano completo de conductos de ${escapeXml(result.state.projectName)}">`,
      '<defs><filter id="ductGlow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter><linearGradient id="machineFill" x1="0" x2="1"><stop stop-color="#ff7a00"/><stop offset="1" stop-color="#ffb332"/></linearGradient></defs>',
      `<g class="machine-node inspectable" tabindex="0" data-inspect-kind="machine"><rect x="${centerX - 85}" y="${centerY - 52}" width="170" height="104" rx="19"/><circle cx="${centerX}" cy="${centerY}" r="25"/><path d="M${centerX} ${centerY - 25}c15 5 19 13 9 24M${centerX + 25} ${centerY}c-5 15-13 19-24 9M${centerX} ${centerY + 25}c-15-5-19-13-9-24M${centerX - 25} ${centerY}c5-15 13-19 24-9"/><text x="${centerX}" y="${centerY - 68}" text-anchor="middle" class="machine-title">MÁQUINA</text><text x="${centerX}" y="${centerY + 76}" text-anchor="middle" class="machine-data">${machineLoad} frg/h · ${machineFlow} m³/h</text></g>`];

    SIDES.forEach(side => {
      const direction = side === 'left' ? -1 : 1;
      const sideResult = result.sides[side];
      let previousX = centerX + direction * 85;
      sideResult.sections.forEach((section, index) => {
        const nodeX = centerX + direction * (150 + index * spacing);
        const room = sideResult.rooms[index];
        const isTop = index % 2 === 0;
        const roomY = isTop ? 74 : 570;
        const roomCentreY = roomY + 58;
        const connectorEndY = isTop ? roomY + 118 : roomY;
        const segmentWidth = clamp(10 + section.widthCm * .42, 13, 34);
        const segmentLabelX = (previousX + nodeX) / 2;
        const labelWidth = 106;
        parts.push(`<g class="duct-segment inspectable" tabindex="0" data-inspect-kind="section" data-side="${side}" data-index="${index}"><line x1="${previousX}" y1="${centerY}" x2="${nodeX}" y2="${centerY}" style="--segment-width:${segmentWidth}px"/><rect class="segment-label-bg" x="${segmentLabelX - labelWidth / 2}" y="${centerY - 48}" width="${labelWidth}" height="28" rx="8"/><text class="segment-label" x="${segmentLabelX}" y="${centerY - 29}" text-anchor="middle">${section.widthCm} × ${section.heightCm} cm</text></g>`);
        parts.push(`<g class="room-output inspectable" tabindex="0" data-inspect-kind="room" data-side="${side}" data-index="${index}"><line class="outlet-line" x1="${nodeX}" y1="${centerY}" x2="${nodeX}" y2="${connectorEndY}"/><rect class="grille-symbol" x="${nodeX - 27}" y="${isTop ? connectorEndY - 8 : connectorEndY - 2}" width="54" height="10" rx="3"/><circle class="junction" cx="${nodeX}" cy="${centerY}" r="7"/><rect class="room-card-svg" x="${nodeX - 74}" y="${roomY}" width="148" height="116" rx="14"/><text class="room-number-svg" x="${nodeX - 58}" y="${roomY + 23}">${side === 'left' ? 'I' : 'D'}${room.number}</text><text class="room-name-svg" x="${nodeX}" y="${roomY + 47}" text-anchor="middle">${escapeXml(room.name)}</text><text class="room-data-svg" x="${nodeX}" y="${roomY + 69}" text-anchor="middle">${formatNumber(room.areaM2, 1)} m² · ${formatNumber(room.loadFg, 0)} frg/h</text><text class="room-grille-svg" x="${nodeX}" y="${roomY + 94}" text-anchor="middle">Rejilla ${room.grille.widthCm} × ${room.grille.heightCm} cm</text></g>`);
        previousX = nodeX;
      });
      if (!sideResult.rooms.length) {
        const emptyX = centerX + direction * 185;
        parts.push(`<g class="empty-branch"><line x1="${centerX + direction * 85}" y1="${centerY}" x2="${emptyX}" y2="${centerY}"/><text x="${emptyX}" y="${centerY - 24}" text-anchor="middle">Sin estancias</text></g>`);
      }
    });
    parts.push('</svg>');
    return { svg: parts.join(''), ...geometry };
  }

  function initBrowser() {
    if (typeof document === 'undefined' || !document.getElementById('ductDiagram')) return;

    const elements = {
      projectName: document.getElementById('projectName'),
      ductHeight: document.getElementById('ductHeight'),
      grilleHeight: document.getElementById('grilleHeight'),
      machineCapacity: document.getElementById('machineCapacity'),
      loadPerM2: document.getElementById('loadPerM2'),
      airflowPer9000: document.getElementById('airflowPer9000'),
      areaPer9000: document.getElementById('areaPer9000'),
      grilleMultiplier: document.getElementById('grilleMultiplier'),
      leftRooms: document.getElementById('leftRooms'),
      rightRooms: document.getElementById('rightRooms'),
      leftCount: document.getElementById('leftCount'),
      rightCount: document.getElementById('rightCount'),
      resultProjectName: document.getElementById('resultProjectName'),
      resultStatus: document.getElementById('resultStatus'),
      resultSummary: document.getElementById('resultSummary'),
      alerts: document.getElementById('ductAlerts'),
      diagram: document.getElementById('ductDiagram'),
      diagramScroll: document.getElementById('diagramScroll'),
      inspector: document.getElementById('diagramInspector'),
      branchResults: document.getElementById('branchResults'),
      saveState: document.getElementById('saveState'),
      roomDialog: document.getElementById('roomDialog'),
      roomForm: document.getElementById('roomForm'),
      roomId: document.getElementById('roomId'),
      roomName: document.getElementById('roomName'),
      roomWidth: document.getElementById('roomWidth'),
      roomLength: document.getElementById('roomLength'),
      roomManualLoad: document.getElementById('roomManualLoad'),
      roomDialogTitle: document.getElementById('roomDialogTitle'),
    };

    let state = loadSavedState();
    let currentResult = calculateProject(state);
    let selected = { kind: 'machine' };
    let zoom = .72;

    function loadSavedState() {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved ? normalizeState(JSON.parse(saved)) : exampleState();
      } catch (_) {
        return exampleState();
      }
    }

    function save() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        elements.saveState.textContent = 'Guardado';
        elements.saveState.classList.add('is-saved');
        setTimeout(() => elements.saveState.classList.remove('is-saved'), 650);
      } catch (_) {
        elements.saveState.textContent = 'Sin guardar';
      }
    }

    function syncInputs() {
      elements.projectName.value = state.projectName;
      elements.ductHeight.value = state.ductHeightCm;
      elements.grilleHeight.value = state.grilleHeightCm;
      elements.machineCapacity.value = state.machineCapacityFg || '';
      elements.loadPerM2.value = state.loadPerM2;
      elements.airflowPer9000.value = state.airflowPer9000;
      elements.areaPer9000.value = state.areaPer9000;
      elements.grilleMultiplier.value = state.grilleMultiplier;
    }

    function updateFromInputs() {
      state = normalizeState({
        ...state,
        projectName: elements.projectName.value,
        ductHeightCm: elements.ductHeight.value,
        grilleHeightCm: elements.grilleHeight.value,
        machineCapacityFg: elements.machineCapacity.value,
        loadPerM2: elements.loadPerM2.value,
        airflowPer9000: elements.airflowPer9000.value,
        areaPer9000: elements.areaPer9000.value,
        grilleMultiplier: elements.grilleMultiplier.value,
      });
      render();
    }

    function roomCard(room, index, sideRooms) {
      const calculated = currentResult.sides[room.side].rooms[index];
      return `<article class="room-list-card" data-room-id="${escapeHtml(room.id)}"><div class="room-order"><b>${index + 1}</b><span>${index === 0 ? 'Más próxima' : index === sideRooms.length - 1 ? 'Final' : 'Después'}</span></div><div class="room-list-copy"><strong>${escapeHtml(room.name)}</strong><small>${formatNumber(calculated.areaM2, 1)} m² · ${formatNumber(calculated.loadFg, 0)} frg/h</small></div><div class="room-buttons"><button type="button" data-room-action="up" aria-label="Subir ${escapeHtml(room.name)}" ${index === 0 ? 'disabled' : ''}>↑</button><button type="button" data-room-action="down" aria-label="Bajar ${escapeHtml(room.name)}" ${index === sideRooms.length - 1 ? 'disabled' : ''}>↓</button><button type="button" data-room-action="edit" aria-label="Editar ${escapeHtml(room.name)}">✎</button><button type="button" data-room-action="remove" aria-label="Eliminar ${escapeHtml(room.name)}">×</button></div></article>`;
    }

    function renderRooms() {
      SIDES.forEach(side => {
        const sideRooms = state.rooms.filter(room => room.side === side);
        const target = side === 'left' ? elements.leftRooms : elements.rightRooms;
        target.innerHTML = sideRooms.length ? sideRooms.map((room, index) => roomCard(room, index, sideRooms)).join('') : '<p class="empty-room-list">Todavía no hay salidas en este lado.</p>';
        (side === 'left' ? elements.leftCount : elements.rightCount).textContent = sideRooms.length;
        document.querySelector(`[data-add-side="${side}"]`).disabled = sideRooms.length >= 7;
      });
    }

    function renderSummary() {
      const totals = currentResult.totals;
      const machineValue = state.machineCapacityFg > 0 ? state.machineCapacityFg : totals.suggestedCapacityFg;
      const capacityLabel = state.machineCapacityFg > 0 ? 'Máquina indicada' : 'Capacidad mínima';
      const main = totals.mainDuct;
      elements.resultSummary.innerHTML = [
        summaryMetric('Estancias', totals.rooms, 'salidas distribuidas', 'blue'),
        summaryMetric(capacityLabel, `${formatNumber(machineValue, 0)} frg/h`, state.machineCapacityFg > 0 ? 'comparada con la instalación' : 'redondeada para seleccionar equipo', 'orange'),
        summaryMetric('Caudal total', `${formatNumber(totals.airflowM3h, 0)} m³/h`, 'caudal aproximado de impulsión', 'green'),
        summaryMetric('Salida general', totals.rooms ? `${main.widthCm} × ${main.heightCm} cm` : '—', totals.rooms ? `${formatNumber(main.velocityMps, 1)} m/s` : 'pendiente de estancias', 'pink'),
      ].join('');
      elements.resultProjectName.textContent = state.projectName || 'Proyecto sin nombre';
      const underCapacity = state.machineCapacityFg > 0 && state.machineCapacityFg < totals.loadFg;
      elements.resultStatus.textContent = !totals.rooms ? 'AÑADE ESTANCIAS' : underCapacity ? 'REVISAR MÁQUINA' : 'LISTO PARA REVISAR';
      elements.resultStatus.className = `result-status${underCapacity ? ' is-danger' : !totals.rooms ? ' is-empty' : ''}`;
    }

    function summaryMetric(label, value, note, color) {
      return `<article class="summary-metric metric-${color}"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`;
    }

    function renderAlerts() {
      elements.alerts.innerHTML = currentResult.warnings.map(item => `<p class="duct-alert alert-${item.level}"><span>${item.level === 'danger' ? '!' : item.level === 'warn' ? '△' : item.level === 'ok' ? '✓' : 'i'}</span>${escapeHtml(item.text)}</p>`).join('');
    }

    function renderDiagram() {
      const rendered = renderDiagramSvg(currentResult);
      elements.diagram.innerHTML = rendered.svg;
      elements.diagram.dataset.width = rendered.width;
      applyZoom();
      renderInspector();
    }

    function applyZoom() {
      const width = finite(elements.diagram.dataset.width, 1000);
      const svg = elements.diagram.querySelector('svg');
      if (!svg) return;
      svg.style.width = `${Math.max(640, width * zoom)}px`;
      svg.style.maxWidth = 'none';
    }

    function fitDiagram() {
      const width = finite(elements.diagram.dataset.width, 1000);
      const available = Math.max(300, elements.diagramScroll.clientWidth - 8);
      zoom = clamp(available / width, .35, 1);
      applyZoom();
      requestAnimationFrame(() => {
        elements.diagramScroll.scrollLeft = Math.max(0, (elements.diagramScroll.scrollWidth - elements.diagramScroll.clientWidth) / 2);
      });
    }

    function renderInspector() {
      const totals = currentResult.totals;
      if (selected.kind === 'section') {
        const section = currentResult.sides[selected.side]?.sections[selected.index];
        if (section) {
          elements.inspector.innerHTML = `<span class="inspector-kicker">${sideLabel(section.side)} · tramo ${section.number}</span><strong>${section.widthCm} × ${section.heightCm} cm</strong><div><span>${formatNumber(section.airflowM3h, 0)} m³/h</span><span>${formatNumber(section.velocityMps, 1)} m/s</span><span>${section.roomsRemaining} ${section.roomsRemaining === 1 ? 'estancia pendiente' : 'estancias pendientes'}</span></div>`;
          return;
        }
      }
      if (selected.kind === 'room') {
        const room = currentResult.sides[selected.side]?.rooms[selected.index];
        if (room) {
          elements.inspector.innerHTML = `<span class="inspector-kicker">${escapeHtml(room.name)} · salida ${room.number} ${selected.side === 'left' ? 'izquierda' : 'derecha'}</span><strong>Rejilla ${room.grille.widthCm} × ${room.grille.heightCm} cm</strong><div><span>${formatNumber(room.airflowM3h, 0)} m³/h</span><span>Conducto ${room.branchDuct.widthCm} × ${room.branchDuct.heightCm} cm</span><span>${formatNumber(room.loadFg, 0)} frg/h</span></div>`;
          return;
        }
      }
      elements.inspector.innerHTML = `<span class="inspector-kicker">Máquina y salida general</span><strong>${totals.rooms ? `${totals.mainDuct.widthCm} × ${totals.mainDuct.heightCm} cm` : 'Proyecto pendiente'}</strong><div><span>${formatNumber(totals.loadFg, 0)} frg/h</span><span>${formatNumber(totals.airflowM3h, 0)} m³/h</span><span>${totals.rooms} estancias</span></div>`;
    }

    function renderBranchResults() {
      elements.branchResults.innerHTML = SIDES.map(side => {
        const branch = currentResult.sides[side];
        if (!branch.rooms.length) return `<article class="branch-result is-empty"><header><div><span>${side === 'left' ? '←' : '→'} ${sideLabel(side)}</span><strong>Sin salidas</strong></div></header><p>Añade estancias para dimensionar este lado.</p></article>`;
        const rows = branch.sections.map((section, index) => {
          const room = branch.rooms[index];
          return `<button class="section-row" type="button" data-result-side="${side}" data-result-index="${index}"><span class="section-number">${section.number}</span><span class="section-destination"><strong>Hasta ${escapeHtml(room.name)}</strong><small>${formatNumber(section.airflowM3h, 0)} m³/h · ${formatNumber(section.velocityMps, 1)} m/s</small></span><span class="section-size"><strong>${section.widthCm} × ${section.heightCm} cm</strong><small>Rejilla ${room.grille.widthCm} × ${room.grille.heightCm} cm</small></span></button>`;
        }).join('');
        return `<article class="branch-result"><header><div><span>${side === 'left' ? '←' : '→'} ${sideLabel(side)}</span><strong>${formatNumber(branch.loadFg, 0)} frg/h</strong></div><small>${formatNumber(branch.airflowM3h, 0)} m³/h</small></header>${rows}</article>`;
      }).join('');
    }

    function render() {
      currentResult = calculateProject(state);
      renderRooms();
      renderSummary();
      renderAlerts();
      renderDiagram();
      renderBranchResults();
      save();
    }

    function openRoomDialog(side, room = null) {
      const sideRooms = state.rooms.filter(item => item.side === side);
      if (!room && sideRooms.length >= 7) return;
      elements.roomDialogTitle.textContent = room ? 'Editar estancia' : 'Añadir estancia';
      elements.roomId.value = room?.id || '';
      elements.roomName.value = room?.name || '';
      elements.roomWidth.value = room?.widthM || '';
      elements.roomLength.value = room?.lengthM || '';
      elements.roomManualLoad.value = room?.manualLoadFg || '';
      const radio = elements.roomForm.querySelector(`input[name="roomSide"][value="${room?.side || side}"]`);
      if (radio) radio.checked = true;
      elements.roomDialog.showModal();
      setTimeout(() => elements.roomName.focus(), 60);
    }

    function reorderRoom(roomId, direction) {
      const room = state.rooms.find(item => item.id === roomId);
      if (!room) return;
      const sameSide = state.rooms.filter(item => item.side === room.side);
      const sideIndex = sameSide.findIndex(item => item.id === roomId);
      const target = sameSide[sideIndex + direction];
      if (!target) return;
      const roomIndex = state.rooms.findIndex(item => item.id === roomId);
      const targetIndex = state.rooms.findIndex(item => item.id === target.id);
      [state.rooms[roomIndex], state.rooms[targetIndex]] = [state.rooms[targetIndex], state.rooms[roomIndex]];
      render();
    }

    function handleRoomListClick(event) {
      const button = event.target.closest('[data-room-action]');
      const card = event.target.closest('[data-room-id]');
      if (!button || !card) return;
      const room = state.rooms.find(item => item.id === card.dataset.roomId);
      if (!room) return;
      if (button.dataset.roomAction === 'edit') openRoomDialog(room.side, room);
      if (button.dataset.roomAction === 'remove') {
        state.rooms = state.rooms.filter(item => item.id !== room.id);
        selected = { kind: 'machine' };
        render();
      }
      if (button.dataset.roomAction === 'up') reorderRoom(room.id, -1);
      if (button.dataset.roomAction === 'down') reorderRoom(room.id, 1);
    }

    [elements.projectName, elements.ductHeight, elements.grilleHeight, elements.machineCapacity, elements.loadPerM2, elements.airflowPer9000, elements.areaPer9000, elements.grilleMultiplier].forEach(input => {
      input.addEventListener('input', updateFromInputs);
      input.addEventListener('change', updateFromInputs);
    });

    document.querySelectorAll('[data-add-side]').forEach(button => button.addEventListener('click', () => openRoomDialog(button.dataset.addSide)));
    elements.leftRooms.addEventListener('click', handleRoomListClick);
    elements.rightRooms.addEventListener('click', handleRoomListClick);
    document.getElementById('closeRoomDialog').addEventListener('click', () => elements.roomDialog.close());
    elements.roomDialog.addEventListener('click', event => { if (event.target === elements.roomDialog) elements.roomDialog.close(); });
    elements.roomForm.addEventListener('submit', event => {
      event.preventDefault();
      const side = elements.roomForm.querySelector('input[name="roomSide"]:checked')?.value || 'left';
      const room = {
        id: elements.roomId.value || `room-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`,
        side,
        name: elements.roomName.value.trim(),
        widthM: elements.roomWidth.value,
        lengthM: elements.roomLength.value,
        manualLoadFg: elements.roomManualLoad.value,
      };
      const existingIndex = state.rooms.findIndex(item => item.id === room.id);
      const sideCount = state.rooms.filter(item => item.side === side && item.id !== room.id).length;
      if (sideCount >= 7) return;
      if (existingIndex >= 0) state.rooms[existingIndex] = room;
      else state.rooms.push(room);
      state = normalizeState(state);
      elements.roomDialog.close();
      selected = { kind: 'room', side, index: state.rooms.filter(item => item.side === side).findIndex(item => item.id === room.id) };
      render();
    });

    document.getElementById('loadExample').addEventListener('click', () => {
      state = exampleState();
      selected = { kind: 'machine' };
      syncInputs();
      render();
      setTimeout(fitDiagram, 40);
    });
    document.getElementById('clearProject').addEventListener('click', () => {
      if (!confirm('¿Quieres borrar las estancias de este proyecto de prueba?')) return;
      state = emptyState();
      selected = { kind: 'machine' };
      syncInputs();
      render();
    });
    document.getElementById('printProject').addEventListener('click', () => window.print());
    document.getElementById('zoomIn').addEventListener('click', () => { zoom = clamp(zoom + .12, .35, 1.6); applyZoom(); });
    document.getElementById('zoomOut').addEventListener('click', () => { zoom = clamp(zoom - .12, .35, 1.6); applyZoom(); });
    document.getElementById('zoomFit').addEventListener('click', fitDiagram);
    elements.diagram.addEventListener('click', event => {
      const target = event.target.closest('[data-inspect-kind]');
      if (!target) return;
      selected = { kind: target.dataset.inspectKind, side: target.dataset.side, index: finite(target.dataset.index, 0) };
      elements.diagram.querySelectorAll('.is-selected').forEach(node => node.classList.remove('is-selected'));
      target.classList.add('is-selected');
      renderInspector();
    });
    elements.diagram.addEventListener('keydown', event => {
      if (!['Enter', ' '].includes(event.key)) return;
      const target = event.target.closest('[data-inspect-kind]');
      if (target) { event.preventDefault(); target.dispatchEvent(new MouseEvent('click', { bubbles: true })); }
    });
    elements.branchResults.addEventListener('click', event => {
      const button = event.target.closest('[data-result-side]');
      if (!button) return;
      selected = { kind: 'section', side: button.dataset.resultSide, index: finite(button.dataset.resultIndex, 0) };
      renderInspector();
      document.querySelector('.diagram-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    window.addEventListener('resize', () => { if (window.innerWidth < 700) fitDiagram(); });

    syncInputs();
    render();
    requestAnimationFrame(fitDiagram);
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initBrowser);
    else initBrowser();
  }

  return { DEFAULTS, EXAMPLE_ROOMS, normalizeState, emptyState, exampleState, sizeDuct, calculateProject, renderDiagramSvg, roundUp };
});
