(() => {
  'use strict';

  const $ = selector => document.querySelector(selector);
  const form = $('#rpForm');
  if (!form) return;

  const elements = {
    system: $('#rpSystem'), refrigerant: $('#rpRefrigerant'), capacity: $('#rpCapacity'), minimumLoad: $('#rpMinimumLoad'),
    manufacturer: $('#rpManufacturer'), model: $('#rpModel'), evaporating: $('#rpEvaporating'), condensing: $('#rpCondensing'),
    length: $('#rpLength'), rise: $('#rpRise'), complexity: $('#rpComplexity'), location: $('#rpLocation'),
    ambient: $('#rpAmbient'), humidity: $('#rpHumidity'), conductivity: $('#rpConductivity'), error: $('#rpError'),
    results: $('#rpResults'), status: $('#rpStatus'), title: $('#rpResultTitle'), subtitle: $('#rpResultSubtitle'),
    gasSize: $('#rpGasSize'), gasDetail: $('#rpGasDetail'), liquidSize: $('#rpLiquidSize'), liquidDetail: $('#rpLiquidDetail'),
    dischargeSummary: $('#rpDischargeSummary'), dischargeSize: $('#rpDischargeSize'), dischargeDetail: $('#rpDischargeDetail'),
    oilStatus: $('#rpOilStatus'), oilDetail: $('#rpOilDetail'), insulation: $('#rpInsulation'), insulationDetail: $('#rpInsulationDetail'),
    diagram: $('#rpDiagram'), diagramCaption: $('#rpDiagramCaption'), oilPlan: $('#rpOilPlan'), insulationPlan: $('#rpInsulationPlan'),
    warnings: $('#rpWarnings'), measurements: $('#rpMeasurements'), technicalRows: $('#rpTechnicalRows'), saveProject: $('#rpSaveProject'),
  };
  let datasets = null;
  let lastResult = null;

  const lineNames = { suction: 'Aspiración / gas', liquid: 'Líquido', discharge: 'Descarga' };

  function numberValue(element) {
    return Number(String(element.value).replace(',', '.'));
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
  }

  function showError(message) {
    elements.error.textContent = message;
    elements.error.hidden = false;
  }

  function hideError() {
    elements.error.hidden = true;
    elements.error.textContent = '';
  }

  function fillSelectors() {
    elements.system.innerHTML = Object.entries(datasets.rules.system_profiles)
      .map(([id, item]) => `<option value="${id}">${escapeHtml(item.title)}</option>`).join('');
    elements.refrigerant.innerHTML = datasets.properties.fluids
      .map(item => `<option value="${escapeHtml(item.designation)}">${escapeHtml(item.designation)}${item.safety_class ? ` · ${escapeHtml(item.safety_class)}` : ''}</option>`).join('');
    elements.refrigerant.value = 'R410A';
    applyProfileDefaults();
  }

  function applyProfileDefaults() {
    if (!datasets) return;
    const profile = datasets.rules.system_profiles[elements.system.value];
    if (!profile) return;
    elements.minimumLoad.value = profile.default_min_load_percent;
    elements.evaporating.value = profile.default_te_c;
    elements.condensing.value = profile.default_tc_c;
  }

  function readInput() {
    return {
      systemType: elements.system.value,
      refrigerant: elements.refrigerant.value,
      capacityKw: numberValue(elements.capacity),
      minimumLoadPercent: numberValue(elements.minimumLoad),
      manufacturer: elements.manufacturer.value.trim(),
      model: elements.model.value.trim(),
      evaporatingC: numberValue(elements.evaporating),
      condensingC: numberValue(elements.condensing),
      lengthM: numberValue(elements.length),
      verticalRiseM: numberValue(elements.rise),
      routeComplexity: elements.complexity.value,
      location: elements.location.value,
      ambientTemperatureC: numberValue(elements.ambient),
      relativeHumidityPercent: numberValue(elements.humidity),
      insulationConductivityWMK: numberValue(elements.conductivity),
    };
  }

  function validate(input) {
    const numeric = ['capacityKw', 'minimumLoadPercent', 'evaporatingC', 'condensingC', 'lengthM', 'verticalRiseM', 'ambientTemperatureC', 'relativeHumidityPercent'];
    if (numeric.some(key => !Number.isFinite(input[key]))) return 'Revisa los campos numéricos.';
    if (input.capacityKw <= 0 || input.lengthM <= 0) return 'La potencia y la longitud deben ser mayores que cero.';
    if (input.condensingC - input.evaporatingC < 15) return 'La condensación debe estar al menos 15 °C por encima de la evaporación.';
    return '';
  }

  function decision(text) {
    return `<div class="rp-decision"><b>✓</b><span>${escapeHtml(text)}</span></div>`;
  }

  function renderDiagram(result) {
    const suction = result.lines.find(item => item.kind === 'suction');
    const liquid = result.lines.find(item => item.kind === 'liquid');
    const discharge = result.lines.find(item => item.kind === 'discharge');
    const oil = result.oilManagement;
    const rise = result.route.verticalDifferenceM;
    const elevated = rise > 1;
    const yOutdoor = elevated ? 70 : 170;
    const yIndoor = elevated ? 205 : 58;
    const riserX = 450;
    const doublePipe = suction.doubleRiser
      ? `<path d="M${riserX - 18} ${yIndoor - 13}V${yOutdoor + 80}" class="rp-svg-gas rp-svg-secondary"/><text x="${riserX - 65}" y="130" class="rp-svg-note">DOBLE</text>` : '';
    const trap = oil.totalProposedTraps
      ? `<path d="M${riserX} ${yIndoor - 13}q0 32 24 32t24-32" class="rp-svg-gas" fill="none"/><text x="${riserX + 15}" y="${yIndoor + 42}" class="rp-svg-note">SIFÓN</text>` : '';
    const intermediate = oil.intermediateTraps
      ? `<path d="M${riserX} 125q0 20 18 20t18-20" class="rp-svg-gas" fill="none"/><text x="${riserX + 42}" y="150" class="rp-svg-note">INTERMEDIO</text>` : '';
    const outdoorEquipment = discharge
      ? `<rect x="550" y="${yOutdoor - 30}" width="105" height="98" rx="12" class="rp-svg-machine"/><rect x="577" y="${yOutdoor - 1}" width="50" height="50" rx="25" class="rp-svg-compressor"/><text x="602" y="${yOutdoor - 44}" text-anchor="middle" class="rp-svg-label">COMPRESOR</text><rect x="700" y="${yOutdoor - 30}" width="105" height="98" rx="12" class="rp-svg-machine"/><circle cx="752" cy="${yOutdoor + 18}" r="27" class="rp-svg-fan"/><path d="M752 ${yOutdoor - 2}q27 20 0 40q-27-20 0-40" class="rp-svg-fan-blade"/><text x="752" y="${yOutdoor - 44}" text-anchor="middle" class="rp-svg-label">CONDENSADOR</text>`
      : `<rect x="632" y="${yOutdoor - 30}" width="170" height="98" rx="12" class="rp-svg-machine"/><circle cx="682" cy="${yOutdoor + 18}" r="27" class="rp-svg-fan"/><path d="M682 ${yOutdoor - 2}q27 20 0 40q-27-20 0-40" class="rp-svg-fan-blade"/><rect x="732" y="${yOutdoor - 2}" width="42" height="42" rx="21" class="rp-svg-compressor"/><text x="717" y="${yOutdoor - 44}" text-anchor="middle" class="rp-svg-label">COMPRESOR / CONDENSADOR</text>`;
    const suctionEnd = discharge ? 550 : 632;
    const liquidStart = discharge ? 700 : 632;
    const dischargePath = discharge
      ? `<path d="M655 ${yOutdoor + 18}H700" class="rp-svg-discharge" marker-end="url(#rpArrowDischarge)" filter="url(#rpGlow)"/><rect x="625" y="214" width="180" height="42" rx="8" class="rp-svg-tag rp-svg-tag-discharge"/><text x="715" y="231" text-anchor="middle" class="rp-svg-tag-title">DESCARGA ${escapeHtml(discharge.displaySize)}</text><text x="715" y="247" text-anchor="middle" class="rp-svg-tag-small">${String(discharge.velocityFullMS).replace('.', ',')} m/s</text>`
      : '';
    elements.diagram.innerHTML = `<svg class="rp-pipe-svg" viewBox="0 0 840 270" role="img" aria-label="Esquema funcional de las tuberías frigoríficas propuestas">
      <defs><filter id="rpGlow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter><marker id="rpArrowGas" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0L6 3 0 6" fill="#00eaff"/></marker><marker id="rpArrowLiquid" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0L6 3 0 6" fill="#ffe438"/></marker><marker id="rpArrowDischarge" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0L6 3 0 6" fill="#ff48a8"/></marker></defs>
      <rect x="38" y="${yIndoor - 38}" width="170" height="88" rx="12" class="rp-svg-machine"/><path d="M62 ${yIndoor - 5}h120M62 ${yIndoor + 10}h120M62 ${yIndoor + 25}h120" class="rp-svg-coil"/><text x="123" y="${yIndoor - 53}" text-anchor="middle" class="rp-svg-label">EVAPORADOR</text>
      ${outdoorEquipment}
      <path d="M208 ${yIndoor - 13}H${riserX}V${yOutdoor + 18}H${suctionEnd}" class="rp-svg-gas" marker-end="url(#rpArrowGas)" filter="url(#rpGlow)"/>${doublePipe}${trap}${intermediate}${dischargePath}
      <path d="M${liquidStart} ${yOutdoor + 48}H${riserX + 70}V${yIndoor + 28}H208" class="rp-svg-liquid" marker-end="url(#rpArrowLiquid)" filter="url(#rpGlow)"/>
      <rect x="278" y="16" width="185" height="42" rx="8" class="rp-svg-tag rp-svg-tag-gas"/><text x="370" y="33" text-anchor="middle" class="rp-svg-tag-title">GAS ${escapeHtml(suction.displaySize)}</text><text x="370" y="49" text-anchor="middle" class="rp-svg-tag-small">AISLAMIENTO ${result.insulation.find(item => item.line === 'suction').thicknessMm} mm</text>
      <rect x="278" y="214" width="185" height="42" rx="8" class="rp-svg-tag rp-svg-tag-liquid"/><text x="370" y="231" text-anchor="middle" class="rp-svg-tag-title">LÍQUIDO ${escapeHtml(liquid.displaySize)}</text><text x="370" y="247" text-anchor="middle" class="rp-svg-tag-small">MARGEN ${String(liquid.flashMarginK).replace('.', ',')} K</text>
      <text x="525" y="${elevated ? 105 : 118}" class="rp-svg-rise">${rise > 0 ? '+' : ''}${String(rise).replace('.', ',')} m</text>
    </svg>`;
    elements.diagramCaption.textContent = elevated ? 'El compresor está por encima: se comprueba especialmente el retorno de aceite.' : 'El recorrido no presenta un montante ascendente principal de aspiración.';
  }

  function render(result) {
    lastResult = result;
    elements.saveProject.disabled = false;
    try { localStorage.setItem('st.refrigerantPiping.v1', JSON.stringify({ saved_at: new Date().toISOString(), input: result.input, result })); } catch (_) {}
    const suction = result.lines.find(item => item.kind === 'suction');
    const liquid = result.lines.find(item => item.kind === 'liquid');
    const discharge = result.lines.find(item => item.kind === 'discharge');
    const suctionInsulation = result.insulation.find(item => item.line === 'suction');
    const liquidInsulation = result.insulation.find(item => item.line === 'liquid');
    const profile = datasets.rules.system_profiles[result.input.systemType];
    const equipment = [result.input.manufacturer, result.input.model].filter(Boolean).join(' ') || profile.title;
    elements.title.textContent = equipment;
    elements.subtitle.textContent = `${result.fluid.designation} · ${String(result.input.capacityKw).replace('.', ',')} kW · ${String(result.route.actualLengthM).replace('.', ',')} m`;
    elements.status.textContent = result.resultLevel === 'manufacturer_required' ? 'COMPROBAR FABRICANTE' : 'PREDISEÑO REVISADO';
    elements.gasSize.textContent = suction.displaySize;
    elements.gasDetail.textContent = suction.doubleRiser ? 'doble montante propuesto' : `${String(suction.odMm).replace('.', ',')} mm exterior`;
    elements.liquidSize.textContent = liquid.displaySize;
    elements.liquidDetail.textContent = `${String(liquid.odMm).replace('.', ',')} mm exterior`;
    elements.dischargeSummary.hidden = !discharge;
    if (discharge) {
      elements.dischargeSize.textContent = discharge.displaySize;
      elements.dischargeDetail.textContent = `${String(discharge.odMm).replace('.', ',')} mm exterior`;
    }
    elements.oilStatus.textContent = result.oilManagement.status === 'fabricante_obligatorio' ? 'Según fabricante' : (suction.doubleRiser ? 'Doble montante' : (suction.oilVelocityPass ? 'Compatible' : 'Revisar'));
    elements.oilDetail.textContent = result.oilManagement.status === 'fabricante_obligatorio' ? 'modelo necesario' : `${result.oilManagement.totalProposedTraps} sifón/es propuesto/s`;
    elements.insulation.textContent = `${suctionInsulation.thicknessMm} mm`;
    elements.insulationDetail.textContent = `espesor comercial · margen ${String(suctionInsulation.condensationMarginK).replace('.', ',')} K`;

    renderDiagram(result);
    const oilDecisions = [...result.oilManagement.notes];
    if (!oilDecisions.length) oilDecisions.push('No se requieren elementos especiales en el recorrido descrito.');
    oilDecisions.push('Confirmar la solución con el fabricante del compresor o equipo.');
    elements.oilPlan.innerHTML = oilDecisions.map(decision).join('');
    const insulationDecisions = [
      `Aspiración: ${suctionInsulation.thicknessMm} mm de aislamiento elastomérico.`,
      `Líquido: ${liquidInsulation.thicknessMm} mm en el recorrido indicado.`,
      `Punto de rocío calculado: ${String(suctionInsulation.dewPointC).replace('.', ',')} °C.`,
    ];
    if (suctionInsulation.vapourBarrierRequired) insulationDecisions.push('Barrera de vapor continua, sellada en juntas, soportes y accesorios.');
    if (suctionInsulation.weatherProtectionRequired) insulationDecisions.push('Protección exterior estanca y resistente a radiación UV.');
    elements.insulationPlan.innerHTML = insulationDecisions.map(decision).join('');
    elements.warnings.innerHTML = result.warnings.map(item => `<div class="rp-warning">${escapeHtml(item)}</div>`).join('');
    elements.measurements.innerHTML = result.billOfQuantities.map(item => `<tr><td>${escapeHtml(item.description)}</td><td>${escapeHtml(item.unit)}</td><td>${String(item.quantity).replace('.', ',')}</td></tr>`).join('');
    elements.technicalRows.innerHTML = result.lines.map(line => `<tr><td>${escapeHtml(lineNames[line.kind] || line.kind)}</td><td>${escapeHtml(line.displaySize)} · Ø ext. ${String(line.odMm).replace('.', ',')} mm</td><td>${String(line.velocityFullMS).replace('.', ',')} m/s</td><td>${line.velocityMinimumMS == null ? '—' : `${String(line.velocityMinimumMS).replace('.', ',')} m/s`}</td><td>${String(line.saturationDropK).replace('.', ',')} K</td></tr>`).join('');
    elements.results.hidden = false;
    elements.results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function saveInProject() {
    const API = window.SuperTecnicoProjects;
    if (!API || !lastResult) return;
    const suction = lastResult.lines.find(item => item.kind === 'suction');
    const liquid = lastResult.lines.find(item => item.kind === 'liquid');
    const saved = API.attachArtifact({
      module_id: 'refrigerant_piping', discipline: 'refrigeracion', title: elements.title.textContent || 'Tuberías frigoríficas', source_page: 'tuberias-frigorificas.html', status: 'predesign',
      summary: `${lastResult.fluid.designation} · gas ${suction.displaySize} · líquido ${liquid.displaySize} · ${lastResult.route.actualLengthM} m`,
      warnings: lastResult.warnings, measurements: lastResult.billOfQuantities,
      snapshot: { input: lastResult.input, fluid: lastResult.fluid, route: lastResult.route, lines: lastResult.lines, oilManagement: lastResult.oilManagement, insulation: lastResult.insulation, resultLevel: lastResult.resultLevel },
    });
    elements.saveProject.textContent = `Guardado · ${saved.project.name}`;
    setTimeout(() => { elements.saveProject.textContent = 'Guardar en Proyecto'; }, 2600);
  }

  function calculate(event) {
    event?.preventDefault();
    hideError();
    if (!datasets || !window.RefrigerantPipingEngine) {
      showError('La base técnica todavía se está cargando. Inténtalo de nuevo en unos segundos.');
      return;
    }
    const input = readInput();
    const error = validate(input);
    if (error) {
      showError(error);
      return;
    }
    try {
      render(window.RefrigerantPipingEngine.design(input, datasets));
    } catch (calculationError) {
      showError(calculationError.message || 'No se ha podido completar el diseño.');
    }
  }

  function loadExample() {
    elements.system.value = 'central';
    elements.refrigerant.value = 'R449A';
    elements.capacity.value = '45';
    elements.minimumLoad.value = '15';
    elements.manufacturer.value = '';
    elements.model.value = '';
    elements.evaporating.value = '-10';
    elements.condensing.value = '40';
    elements.length.value = '38';
    elements.rise.value = '12';
    elements.complexity.value = 'normal';
    elements.location.value = 'inside';
    elements.ambient.value = '30';
    elements.humidity.value = '70';
    calculate();
  }

  async function start() {
    try {
      const [propertiesResponse, rulesResponse] = await Promise.all([
        fetch('data/refrigerant-piping/property-grid.json'),
        fetch('data/refrigerant-piping/design-rules.json'),
      ]);
      if (!propertiesResponse.ok || !rulesResponse.ok) throw new Error('No se han podido cargar los datos técnicos.');
      datasets = { properties: await propertiesResponse.json(), rules: await rulesResponse.json() };
      fillSelectors();
    } catch (error) {
      showError(error.message);
    }
  }

  elements.system.addEventListener('change', applyProfileDefaults);
  form.addEventListener('submit', calculate);
  $('#rpExample').addEventListener('click', loadExample);
  elements.saveProject.addEventListener('click', saveInProject);
  $('#rpPrint').addEventListener('click', () => window.print());
  start();
})();
