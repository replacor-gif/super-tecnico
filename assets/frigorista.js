(() => {
  'use strict';

  const engine = window.STFrigorista;
  const state = {
    catalog: null,
    curves: null,
    mollier: null,
    currentSide: 'evaporation',
    currentResult: null,
    measurements: {},
    derived: {},
  };

  const elements = {};

  function byId(id) {
    return document.getElementById(id);
  }

  function parseDecimal(value) {
    return Number(String(value || '').trim().replace(',', '.'));
  }

  function format(value, decimals = 1) {
    return new Intl.NumberFormat('es-ES', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  }

  function setError(element, message = '') {
    element.textContent = message;
    element.hidden = !message;
  }

  function scrollToElement(element) {
    const top = element.getBoundingClientRect().top + window.scrollY - 92;
    window.scrollTo({top, behavior: 'smooth'});
  }

  function selectedValue(name) {
    return document.querySelector(`input[name="${name}"]:checked`)?.value || '';
  }

  function setSide(side) {
    const input = document.querySelector(`input[name="side"][value="${side}"]`);
    if (input) input.checked = true;
    state.currentSide = side;
  }

  function pressureLabel(record) {
    if (!record) return 'Pendiente';
    const suffix = record.input.reference === 'gauge' ? 'man.' : 'abs.';
    return `${format(record.input.value, 2)} ${record.input.unit} ${suffix}`;
  }

  function saturationLabel(record, side) {
    if (!record) return '';
    const temperature = side === 'evaporation'
      ? record.result.dew_temperature_c
      : record.result.bubble_temperature_c;
    return `${format(temperature, 1)} °C ${side === 'evaporation' ? 'evap.' : 'cond.'}`;
  }

  function rememberRefrigerant(designation) {
    try { localStorage.setItem('st.frigorista.lastRefrigerant', designation); } catch (_) { /* optional */ }
  }

  function loadRememberedRefrigerant() {
    try { return localStorage.getItem('st.frigorista.lastRefrigerant') || ''; } catch (_) { return ''; }
  }

  function renderCatalog() {
    const available = state.catalog.refrigerants
      .filter(item => item.selectable && item.pt_available)
      .sort((a, b) => a.designation.localeCompare(b.designation, 'es', {numeric: true}));
    const fragment = document.createDocumentFragment();
    available.forEach(item => {
      const option = document.createElement('option');
      option.value = item.designation;
      option.label = `${item.designation} · ${item.family}`;
      fragment.append(option);
    });
    elements.refrigerantList.replaceChildren(fragment);
    elements.catalogStatus.textContent = `${available.length} refrigerantes P/T disponibles`;
    const remembered = loadRememberedRefrigerant();
    if (remembered && engine.findRefrigerant(state.catalog, remembered)?.selectable) {
      elements.refrigerantInput.value = remembered;
    }
  }

  function renderResult(side, result) {
    const isEvaporation = side === 'evaporation';
    elements.resultEyebrow.textContent = `${result.designation} · ${pressureLabel(state.measurements[isEvaporation ? 'low_pressure' : 'high_pressure'])}`;
    elements.resultTitle.textContent = isEvaporation ? 'Temperatura de evaporación' : 'Temperatura de condensación';
    elements.resultBadges.replaceChildren();

    const sourceBadge = document.createElement('span');
    sourceBadge.textContent = `CoolProp ${result.source.version}`;
    elements.resultBadges.append(sourceBadge);
    if (result.safety_class) {
      const safetyBadge = document.createElement('span');
      safetyBadge.className = 'is-safety';
      safetyBadge.textContent = `Clase ${result.safety_class}`;
      elements.resultBadges.append(safetyBadge);
    }

    const showBlend = result.result_type === 'bubble_dew';
    elements.singleResult.hidden = showBlend;
    elements.blendResult.hidden = !showBlend;
    if (showBlend) {
      elements.dewTemperature.textContent = format(result.dew_temperature_c, 1);
      elements.bubbleTemperature.textContent = format(result.bubble_temperature_c, 1);
      elements.glideValue.textContent = format(result.glide_k, 1);
      elements.resultExplanation.textContent = isEvaporation
        ? `Para estudiar el vapor y calcular recalentamiento se utilizará el punto de rocío: ${format(result.dew_temperature_c, 1)} °C.`
        : `Para estudiar el líquido y calcular subenfriamiento se utilizará el punto de burbuja: ${format(result.bubble_temperature_c, 1)} °C.`;
    } else {
      const temperature = isEvaporation ? result.dew_temperature_c : result.bubble_temperature_c;
      elements.singleTemperature.textContent = format(temperature, 1);
      elements.resultExplanation.textContent = 'Esta consulta ya está terminada. Puedes usar el resultado o añadir otra medición sin empezar de nuevo.';
    }

    elements.lineTemperatureButton.textContent = isEvaporation
      ? 'Calcular recalentamiento'
      : 'Calcular subenfriamiento';
    elements.resultPanel.hidden = false;
    requestAnimationFrame(() => scrollToElement(elements.resultPanel));
  }

  function outOfRangeMessage(error, unit, reference, atmospherePa) {
    const minimum = engine.fromPressurePa(error.details.minimum_pa_abs, unit, reference, atmospherePa);
    const maximum = engine.fromPressurePa(error.details.maximum_pa_abs, unit, reference, atmospherePa);
    return `Fuera del intervalo disponible. Para esta unidad y referencia: ${format(minimum, 2)} a ${format(maximum, 2)} ${unit}. No se extrapola el resultado.`;
  }

  function runConversion(event) {
    event.preventDefault();
    setError(elements.formError);
    const side = selectedValue('side');
    const unit = elements.pressureUnit.value;
    const reference = selectedValue('reference');
    const atmosphericBar = parseDecimal(elements.atmosphericInput.value);
    const atmospherePa = atmosphericBar * 100000;
    const pressure = parseDecimal(elements.pressureInput.value);

    try {
      const result = engine.convertPressureToTemperature({
        catalog: state.catalog,
        curves: state.curves,
        designation: elements.refrigerantInput.value,
        pressure,
        unit,
        reference,
        atmosphericPressurePa: atmospherePa,
      });
      const previousDesignation = state.measurements.low_pressure?.result.designation
        || state.measurements.high_pressure?.result.designation;
      if (previousDesignation && previousDesignation !== result.designation) {
        state.measurements = {};
        state.derived = {};
      }
      const key = side === 'evaporation' ? 'low_pressure' : 'high_pressure';
      state.currentSide = side;
      state.currentResult = result;
      state.measurements[key] = {
        input: {value: pressure, unit, reference, atmospheric_pressure_pa: atmospherePa},
        result,
      };
      rememberRefrigerant(result.designation);
      elements.refrigerantInput.value = result.designation;
      renderResult(side, result);
      renderAnalysis();
    } catch (error) {
      const message = error.code === 'out_of_range'
        ? outOfRangeMessage(error, unit, reference, atmospherePa)
        : error.message || 'No se ha podido realizar la consulta.';
      setError(elements.formError, message);
    }
  }

  function measurementDefinition(code) {
    const definitions = {
      suction_line_temperature: {
        title: 'Temperatura del tubo de aspiración',
        label: 'Temperatura medida en aspiración',
        help: 'Mide sobre el tubo, cerca de la toma de baja y con buen contacto térmico.',
      },
      liquid_line_temperature: {
        title: 'Temperatura de la línea de líquido',
        label: 'Temperatura medida en la línea de líquido',
        help: 'Mide sobre el tubo de líquido, en un punto representativo y con buen contacto térmico.',
      },
      discharge_line_temperature: {
        title: 'Temperatura del tubo de descarga',
        label: 'Temperatura medida a la salida del compresor',
        help: 'Mide sobre el tubo de descarga, cerca del compresor y con buen contacto térmico. Este dato cierra el ciclo Mollier.',
      },
      return_air_temperature: {
        title: 'Temperatura del aire de retorno',
        label: 'Temperatura del aire que entra en la unidad',
        help: 'Es un dato opcional. Si no puedes medirlo, detén aquí el estudio sin perder lo anterior.',
      },
      supply_air_temperature: {
        title: 'Temperatura del aire de impulsión',
        label: 'Temperatura del aire que sale de la unidad',
        help: 'Es un dato opcional y permitirá conocer la diferencia entre retorno e impulsión.',
      },
    };
    return definitions[code] || null;
  }

  function openMeasurement(code) {
    const definition = measurementDefinition(code);
    if (!definition) return;
    elements.measurementForm.dataset.measurement = code;
    elements.measurementTitle.textContent = definition.title;
    elements.measurementLabel.textContent = definition.label;
    elements.measurementHelp.textContent = definition.help;
    elements.measurementInput.value = state.measurements[code]?.value ?? '';
    setError(elements.measurementError);
    elements.measurementPanel.hidden = false;
    requestAnimationFrame(() => {
      scrollToElement(elements.measurementPanel);
      elements.measurementInput.focus({preventScroll: true});
    });
  }

  function saveMeasurement(event) {
    event.preventDefault();
    setError(elements.measurementError);
    const code = elements.measurementForm.dataset.measurement;
    const value = parseDecimal(elements.measurementInput.value);
    if (!Number.isFinite(value) || value < -150 || value > 250) {
      setError(elements.measurementError, 'Introduce una temperatura válida entre −150 y 250 °C.');
      return;
    }
    state.measurements[code] = {value, unit: 'degC', quality: 'measured'};

    if (code === 'suction_line_temperature') {
      const low = state.measurements.low_pressure;
      if (!low) {
        setError(elements.measurementError, 'Primero necesitamos la presión de baja.');
        return;
      }
      state.derived.superheat = engine.calculateSuperheat(low.result.dew_temperature_c, value);
    }
    if (code === 'liquid_line_temperature') {
      const high = state.measurements.high_pressure;
      if (!high) {
        setError(elements.measurementError, 'Primero necesitamos la presión de alta.');
        return;
      }
      state.derived.subcooling = engine.calculateSubcooling(high.result.bubble_temperature_c, value);
    }
    if (state.measurements.return_air_temperature && state.measurements.supply_air_temperature) {
      state.derived.air_delta = {
        value_k: Math.round(Math.abs(
          state.measurements.return_air_temperature.value - state.measurements.supply_air_temperature.value
        ) * 10) / 10,
      };
    }

    elements.measurementPanel.hidden = true;
    elements.analysisPanel.hidden = false;
    renderAnalysis();
    requestAnimationFrame(() => scrollToElement(elements.analysisPanel));
  }

  function summaryItem(label, value, detail, present) {
    return `<article class="fr-summary-item ${present ? 'is-present' : 'is-missing'}"><span>${label}</span><strong>${value}</strong>${detail ? `<small>${detail}</small>` : ''}</article>`;
  }

  function chartPath(points, x, y) {
    return points.map((point, index) => `${index ? 'L' : 'M'} ${x(point.x).toFixed(1)} ${y(point.y).toFixed(1)}`).join(' ');
  }

  function renderMollierChart(model, cycle) {
    const width = 760;
    const height = 470;
    const margin = {left: 76, right: 26, top: 24, bottom: 58};
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const x = normalized => margin.left + normalized * plotWidth;
    const y = normalized => margin.top + (1 - normalized) * plotHeight;
    const xTicks = [];
    const yTicks = [];
    for (let index = 0; index <= 4; index += 1) {
      const fraction = index / 4;
      const enthalpy = model.domain.enthalpy_kj_kg[0]
        + fraction * (model.domain.enthalpy_kj_kg[1] - model.domain.enthalpy_kj_kg[0]);
      const minimumLogP = Math.log10(model.domain.pressure_pa_abs[0]);
      const pressure = 10 ** (minimumLogP + fraction * (Math.log10(model.domain.pressure_pa_abs[1]) - minimumLogP));
      xTicks.push({fraction, label: format(enthalpy, 0)});
      yTicks.push({fraction, label: format(pressure / 100000, pressure / 100000 < 10 ? 1 : 0)});
    }
    const envelope = [...model.bubble, ...[...model.dew].reverse()];
    const segments = model.segments.map(segment => {
      const from = model.points[segment.from];
      const to = model.points[segment.to];
      return `<line class="fr-chart-segment" x1="${x(from.x).toFixed(1)}" y1="${y(from.y).toFixed(1)}" x2="${x(to.x).toFixed(1)}" y2="${y(to.y).toFixed(1)}"/>`;
    }).join('');
    const pointOrder = ['suction', 'discharge', 'liquid', 'expansion'];
    const points = pointOrder.filter(key => model.points[key]).map(key => {
      const point = model.points[key];
      const qualityClass = point.quality === 'derived' ? 'is-derived' : 'is-measured';
      return `<g class="fr-chart-point ${qualityClass}" transform="translate(${x(point.x).toFixed(1)} ${y(point.y).toFixed(1)})"><title>Punto ${point.number}: ${point.label}, ${format(point.enthalpy_kj_kg, 1)} kJ/kg</title><circle r="15"></circle><text y="1">${point.number}</text></g>`;
    }).join('');
    const gridX = xTicks.map(tick => `<line class="fr-chart-grid" x1="${x(tick.fraction)}" y1="${margin.top}" x2="${x(tick.fraction)}" y2="${height - margin.bottom}"/><text class="fr-chart-tick" x="${x(tick.fraction)}" y="${height - margin.bottom + 22}" text-anchor="middle">${tick.label}</text>`).join('');
    const gridY = yTicks.map(tick => `<line class="fr-chart-grid" x1="${margin.left}" y1="${y(tick.fraction)}" x2="${width - margin.right}" y2="${y(tick.fraction)}"/><text class="fr-chart-tick" x="${margin.left - 12}" y="${y(tick.fraction) + 4}" text-anchor="end">${tick.label}</text>`).join('');

    elements.mollierChart.innerHTML = `
      <title id="mollierChartTitle">Diagrama de Mollier de ${cycle.designation}</title>
      <desc id="mollierChartDescription">Diagrama presión entalpía con ${Object.keys(model.points).length} puntos disponibles del ciclo frigorífico.</desc>
      ${gridX}${gridY}
      <line class="fr-chart-axis" x1="${margin.left}" y1="${height - margin.bottom}" x2="${width - margin.right}" y2="${height - margin.bottom}"/>
      <line class="fr-chart-axis" x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${height - margin.bottom}"/>
      <path class="fr-chart-envelope" d="${chartPath(envelope, x, y)} Z"/>
      <path class="fr-chart-dew" d="${chartPath(model.dew, x, y)}"/>
      ${segments}${points}
      <text class="fr-chart-label" x="${margin.left + plotWidth / 2}" y="${height - 10}" text-anchor="middle">ENTALPÍA · kJ/kg</text>
      <text class="fr-chart-label" transform="translate(18 ${margin.top + plotHeight / 2}) rotate(-90)" text-anchor="middle">PRESIÓN ABSOLUTA · bar</text>`;
  }

  function mollierPointCard(key, label, cycle) {
    const point = cycle.points[key];
    if (!point) return `<article class="fr-mollier-point is-missing"><span>PUNTO —</span><strong>${label}</strong><small>Pendiente de medición</small></article>`;
    const temperature = Number.isFinite(point.temperature_c) ? `${format(point.temperature_c, 1)} °C · ` : '';
    return `<article class="fr-mollier-point"><span>PUNTO ${point.number}${point.quality === 'derived' ? ' · CALCULADO' : ' · MEDIDO'}</span><strong>${point.label}</strong><small>${temperature}${format(point.enthalpy_kj_kg, 1)} kJ/kg</small></article>`;
  }

  function performanceCard(label, value, unit, detail) {
    const displayed = Number.isFinite(value) ? `${format(value, unit === 'COP' ? 2 : 1)}${unit === 'COP' ? '' : ` ${unit}`}` : 'Pendiente';
    return `<article class="fr-performance-card"><span>${label}</span><strong>${displayed}</strong><small>${detail}</small></article>`;
  }

  function renderMollier() {
    if (!state.mollier) {
      elements.mollierStatus.textContent = 'DATOS NO DISPONIBLES';
      elements.mollierStatus.className = 'fr-mollier-status is-review';
      elements.mollierEmpty.querySelector('strong').textContent = 'El diagrama no está disponible en esta carga.';
      return;
    }
    const designation = state.measurements.low_pressure?.result.designation
      || state.measurements.high_pressure?.result.designation
      || elements.refrigerantInput.value;
    if (!designation) return;
    const cycle = engine.analyzeMollierCycle({
      mollier: state.mollier,
      designation,
      measurements: state.measurements,
    });
    const model = engine.createMollierPlotModel(state.mollier, cycle);
    if (!model) {
      elements.mollierContent.hidden = true;
      elements.mollierEmpty.hidden = false;
      elements.mollierStatus.textContent = cycle.status === 'review' ? 'REVISAR DATOS' : 'RECOGIENDO DATOS';
      elements.mollierStatus.className = `fr-mollier-status${cycle.status === 'review' ? ' is-review' : ''}`;
      return;
    }

    elements.mollierEmpty.hidden = true;
    elements.mollierContent.hidden = false;
    elements.mollierStatus.textContent = cycle.status === 'complete'
      ? 'CICLO COMPLETO'
      : cycle.status === 'review' ? 'REVISAR DATOS' : 'DIAGRAMA PARCIAL';
    elements.mollierStatus.className = `fr-mollier-status${cycle.status === 'complete' ? ' is-complete' : cycle.status === 'review' ? ' is-review' : ''}`;
    renderMollierChart(model, cycle);
    elements.mollierPoints.innerHTML = [
      mollierPointCard('suction', 'Aspiración del compresor', cycle),
      mollierPointCard('discharge', 'Descarga del compresor', cycle),
      mollierPointCard('liquid', 'Salida de líquido', cycle),
      mollierPointCard('expansion', 'Salida de expansión', cycle),
    ].join('');
    const performance = cycle.performance;
    elements.mollierPerformance.innerHTML = [
      performanceCard('Efecto frigorífico', performance.evaporator_effect_kj_kg, 'kJ/kg', 'ganancia específica en evaporador'),
      performanceCard('Trabajo del compresor', performance.compressor_work_kj_kg, 'kJ/kg', 'a partir de descarga medida'),
      performanceCard('Calor rechazado', performance.condenser_heat_kj_kg, 'kJ/kg', 'diferencia en condensador'),
      performanceCard('COP del ciclo', performance.cop_cycle, 'COP', 'indicador del ciclo medido'),
    ].join('');
    elements.mollierEvidence.innerHTML = cycle.evidence.map(item => `<article class="fr-evidence-item is-${item.level}"><i></i><div><strong>${item.title}</strong><p>${item.detail}</p></div></article>`).join('');
  }

  function renderAnalysis() {
    if (!state.catalog) return;
    const low = state.measurements.low_pressure;
    const high = state.measurements.high_pressure;
    const suction = state.measurements.suction_line_temperature;
    const liquid = state.measurements.liquid_line_temperature;
    const discharge = state.measurements.discharge_line_temperature;
    const returnAir = state.measurements.return_air_temperature;
    const supplyAir = state.measurements.supply_air_temperature;

    elements.measurementSummary.innerHTML = [
      summaryItem('Baja', pressureLabel(low), saturationLabel(low, 'evaporation'), Boolean(low)),
      summaryItem('Tubo de aspiración', suction ? `${format(suction.value, 1)} °C` : 'Pendiente', '', Boolean(suction)),
      summaryItem('Alta', pressureLabel(high), saturationLabel(high, 'condensation'), Boolean(high)),
      summaryItem('Línea de líquido', liquid ? `${format(liquid.value, 1)} °C` : 'Pendiente', '', Boolean(liquid)),
      summaryItem('Tubo de descarga', discharge ? `${format(discharge.value, 1)} °C` : 'Opcional', 'Cierra el ciclo Mollier', Boolean(discharge)),
      summaryItem('Aire de retorno', returnAir ? `${format(returnAir.value, 1)} °C` : 'Opcional', '', Boolean(returnAir)),
      summaryItem('Aire de impulsión', supplyAir ? `${format(supplyAir.value, 1)} °C` : 'Opcional', '', Boolean(supplyAir)),
    ].join('');

    const next = engine.nextUsefulMeasurement(state);
    elements.nextMeasurementTitle.textContent = next.label;
    elements.nextMeasurementReason.textContent = next.reason;
    elements.nextMeasurementButton.dataset.measurement = next.code;
    elements.nextMeasurementButton.hidden = next.code === 'context_complete';

    const derived = [];
    if (state.derived.superheat) {
      derived.push(`<article class="fr-derived-item"><span>Recalentamiento</span><strong>${format(state.derived.superheat.value_k, 1)} K</strong><small>Calculado con rocío</small></article>`);
    }
    if (state.derived.subcooling) {
      derived.push(`<article class="fr-derived-item"><span>Subenfriamiento</span><strong>${format(state.derived.subcooling.value_k, 1)} K</strong><small>Calculado con burbuja</small></article>`);
    }
    if (state.derived.air_delta) {
      derived.push(`<article class="fr-derived-item"><span>Diferencia del aire</span><strong>${format(state.derived.air_delta.value_k, 1)} K</strong><small>Retorno frente a impulsión</small></article>`);
    }
    elements.derivedSummary.innerHTML = derived.length
      ? derived.join('')
      : '<article class="fr-derived-item"><span>Resultados adicionales</span><strong>—</strong><small>Aparecerán al añadir las mediciones necesarias.</small></article>';
    renderMollier();
  }

  function askNextMeasurement() {
    const code = elements.nextMeasurementButton.dataset.measurement;
    if (code === 'low_pressure' || code === 'high_pressure') {
      setSide(code === 'low_pressure' ? 'evaporation' : 'condensation');
      elements.pressureInput.value = '';
      setError(elements.formError);
      scrollToElement(elements.ptForm);
      elements.pressureInput.focus({preventScroll: true});
      return;
    }
    openMeasurement(code);
  }

  function openAnalysis() {
    elements.analysisPanel.hidden = false;
    renderAnalysis();
    requestAnimationFrame(() => scrollToElement(elements.analysisPanel));
  }

  function addCurrentLineTemperature() {
    openMeasurement(state.currentSide === 'evaporation'
      ? 'suction_line_temperature'
      : 'liquid_line_temperature');
  }

  function resetSession() {
    state.currentResult = null;
    state.measurements = {};
    state.derived = {};
    elements.pressureInput.value = '';
    elements.resultPanel.hidden = true;
    elements.measurementPanel.hidden = true;
    elements.analysisPanel.hidden = true;
    setError(elements.formError);
    scrollToElement(elements.ptForm);
    elements.pressureInput.focus({preventScroll: true});
  }

  async function initialize() {
    Object.assign(elements, {
      catalogStatus: byId('catalogStatus'),
      ptForm: byId('ptForm'),
      refrigerantInput: byId('refrigerantInput'),
      refrigerantList: byId('refrigerantList'),
      pressureInput: byId('pressureInput'),
      pressureUnit: byId('pressureUnit'),
      atmosphericInput: byId('atmosphericInput'),
      formError: byId('formError'),
      resultPanel: byId('resultPanel'),
      resultEyebrow: byId('resultEyebrow'),
      resultTitle: byId('resultTitle'),
      resultBadges: byId('resultBadges'),
      singleResult: byId('singleResult'),
      singleTemperature: byId('singleTemperature'),
      blendResult: byId('blendResult'),
      dewTemperature: byId('dewTemperature'),
      bubbleTemperature: byId('bubbleTemperature'),
      glideValue: byId('glideValue'),
      resultExplanation: byId('resultExplanation'),
      lineTemperatureButton: byId('lineTemperatureButton'),
      analyzeButton: byId('analyzeButton'),
      newQueryButton: byId('newQueryButton'),
      measurementPanel: byId('measurementPanel'),
      measurementForm: byId('measurementForm'),
      measurementTitle: byId('measurementTitle'),
      measurementHelp: byId('measurementHelp'),
      measurementLabel: byId('measurementLabel'),
      measurementInput: byId('measurementInput'),
      measurementError: byId('measurementError'),
      closeMeasurementButton: byId('closeMeasurementButton'),
      analysisPanel: byId('analysisPanel'),
      measurementSummary: byId('measurementSummary'),
      nextMeasurementTitle: byId('nextMeasurementTitle'),
      nextMeasurementReason: byId('nextMeasurementReason'),
      nextMeasurementButton: byId('nextMeasurementButton'),
      derivedSummary: byId('derivedSummary'),
      mollierPanel: byId('mollierPanel'),
      mollierStatus: byId('mollierStatus'),
      mollierEmpty: byId('mollierEmpty'),
      mollierContent: byId('mollierContent'),
      mollierChart: byId('mollierChart'),
      mollierPoints: byId('mollierPoints'),
      mollierPerformance: byId('mollierPerformance'),
      mollierEvidence: byId('mollierEvidence'),
    });

    elements.ptForm.addEventListener('submit', runConversion);
    elements.lineTemperatureButton.addEventListener('click', addCurrentLineTemperature);
    elements.analyzeButton.addEventListener('click', openAnalysis);
    elements.newQueryButton.addEventListener('click', resetSession);
    elements.measurementForm.addEventListener('submit', saveMeasurement);
    elements.closeMeasurementButton.addEventListener('click', () => { elements.measurementPanel.hidden = true; });
    elements.nextMeasurementButton.addEventListener('click', askNextMeasurement);
    document.querySelectorAll('[data-refrigerant]').forEach(button => {
      button.addEventListener('click', () => {
        elements.refrigerantInput.value = button.dataset.refrigerant;
        elements.pressureInput.focus();
      });
    });

    try {
      const [catalogResponse, curvesResponse, mollierResponse] = await Promise.all([
        fetch('data/frigorista/catalog.json'),
        fetch('data/frigorista/pt-curves.json'),
        fetch('data/frigorista/mollier-data.json'),
      ]);
      if (!catalogResponse.ok || !curvesResponse.ok || !mollierResponse.ok) throw new Error('No se han podido cargar los datos termodinámicos.');
      [state.catalog, state.curves, state.mollier] = await Promise.all([
        catalogResponse.json(), curvesResponse.json(), mollierResponse.json(),
      ]);
      if (state.catalog.dataset_version !== state.curves.dataset_version
        || state.catalog.dataset_version !== state.mollier.dataset_version) {
        throw new Error('Las versiones de los datos termodinámicos no coinciden.');
      }
      renderCatalog();
    } catch (error) {
      elements.catalogStatus.textContent = 'Datos P/T no disponibles';
      elements.catalogStatus.classList.add('is-error');
      setError(elements.formError, error.message || 'No se ha podido iniciar el asistente.');
      byId('calculateButton').disabled = true;
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
  else initialize();
})();
