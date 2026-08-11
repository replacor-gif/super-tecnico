(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.STCalc = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const EIA96_VALUES = [
    100,102,105,107,110,113,115,118,121,124,127,130,133,137,140,143,
    147,150,154,158,162,165,169,174,178,182,187,191,196,200,205,210,
    215,221,226,232,237,243,249,255,261,267,274,280,287,294,301,309,
    316,324,332,340,348,357,365,374,383,392,402,412,422,432,442,453,
    464,475,487,499,511,523,536,549,562,576,590,604,619,634,649,665,
    681,698,715,732,750,768,787,806,825,845,866,887,909,931,953,976
  ];
  const EIA96_MULTIPLIERS = {
    Z: 0.001, Y: 0.01, R: 0.01, X: 0.1, S: 0.1,
    A: 1, B: 10, H: 10, C: 100, D: 1000,
    E: 10000, F: 100000
  };

  const COLOR_DIGITS = {
    negro: 0, marron: 1, rojo: 2, naranja: 3, amarillo: 4,
    verde: 5, azul: 6, violeta: 7, gris: 8, blanco: 9
  };
  const COLOR_MULTIPLIERS = {
    plata: 0.01, oro: 0.1, negro: 1, marron: 10, rojo: 100,
    naranja: 1000, amarillo: 10000, verde: 100000,
    azul: 1000000, violeta: 10000000, gris: 100000000,
    blanco: 1000000000
  };
  const COLOR_TOLERANCES = {
    marron: 1, rojo: 2, verde: 0.5, azul: 0.25, violeta: 0.1,
    gris: 0.05, oro: 5, plata: 10, ninguno: 20
  };

  function normalizeText(value) {
    return String(value ?? '')
      .trim()
      .replace(/\s+/g, '')
      .replace(',', '.')
      .replace(/Ω|ohms?|ohmios?/gi, '');
  }

  function parseEngineering(value, baseUnit) {
    const text = normalizeText(value);
    if (!text) return NaN;
    const normalized = text.replace(/µ/g, 'u').replace(/μ/g, 'u');
    const match = normalized.match(/^([+-]?(?:\d+(?:\.\d*)?|\.\d+))(meg|[tgkmunpf]?)([a-z]*)$/i);
    if (!match) return NaN;
    const num = Number(match[1]);
    if (!Number.isFinite(num)) return NaN;
    const prefix = match[2];
    const exactPrefix = prefix === 'M' ? 'M' : prefix.toLowerCase();
    const factors = {
      '': 1, t: 1e12, g: 1e9, meg: 1e6, M: 1e6, k: 1e3,
      m: 1e-3, u: 1e-6, n: 1e-9, p: 1e-12, f: 1e-15
    };
    if (!(exactPrefix in factors)) return NaN;
    return num * factors[exactPrefix];
  }

  function formatEngineering(value, unit = '', decimals = 3) {
    if (!Number.isFinite(value)) return '—';
    if (value === 0) return `0 ${unit}`.trim();
    const abs = Math.abs(value);
    const prefixes = [
      [1e12, 'T'], [1e9, 'G'], [1e6, 'M'], [1e3, 'k'],
      [1, ''], [1e-3, 'm'], [1e-6, 'µ'], [1e-9, 'n'],
      [1e-12, 'p'], [1e-15, 'f']
    ];
    let factor = 1;
    let prefix = '';
    for (const [f, p] of prefixes) {
      if (abs >= f) { factor = f; prefix = p; break; }
    }
    const scaled = value / factor;
    const digits = Math.max(0, decimals - Math.floor(Math.log10(Math.abs(scaled))) - 1);
    const language = typeof window !== 'undefined' && window.ST_I18N
      ? window.ST_I18N.language
      : 'es';
    const locale = { es: 'es-ES', en: 'en-US', pt: 'pt-PT', fr: 'fr-FR' }[language] || 'es-ES';
    return `${scaled.toLocaleString(locale, { maximumFractionDigits: Math.min(6, digits), minimumFractionDigits: 0 })} ${prefix}${unit}`.trim();
  }

  function ohmsLaw(mode, a, b) {
    const x = Number(a), y = Number(b);
    if (![x, y].every(v => Number.isFinite(v) && v >= 0)) throw new Error('Introduce valores válidos y no negativos.');
    let V, I, R, P;
    switch (mode) {
      case 'VI': V = x; I = y; R = I === 0 ? Infinity : V / I; P = V * I; break;
      case 'VR': V = x; R = y; I = R === 0 ? Infinity : V / R; P = V * I; break;
      case 'IR': I = x; R = y; V = I * R; P = I * I * R; break;
      case 'PV': P = x; V = y; I = V === 0 ? Infinity : P / V; R = I === 0 ? Infinity : V / I; break;
      case 'PI': P = x; I = y; V = I === 0 ? Infinity : P / I; R = I === 0 ? Infinity : P / (I * I); break;
      case 'PR': P = x; R = y; I = R === 0 ? Infinity : Math.sqrt(P / R); V = Math.sqrt(P * R); break;
      default: throw new Error('Modo no reconocido.');
    }
    if (![V, I, R, P].every(Number.isFinite)) throw new Error('La combinación produce una división por cero.');
    return { V, I, R, P };
  }

  function resistorColors(bands) {
    const count = bands.length;
    if (count !== 4 && count !== 5) throw new Error('Solo se admiten 4 o 5 bandas.');
    const significantColors = count === 4 ? bands.slice(0, 2) : bands.slice(0, 3);
    const multiplierColor = bands[count - 2];
    const toleranceColor = bands[count - 1];
    if (significantColors.some(c => !(c in COLOR_DIGITS))) throw new Error('Color significativo no válido.');
    if (!(multiplierColor in COLOR_MULTIPLIERS)) throw new Error('Multiplicador no válido.');
    if (!(toleranceColor in COLOR_TOLERANCES)) throw new Error('Tolerancia no válida.');
    const significant = Number(significantColors.map(c => COLOR_DIGITS[c]).join(''));
    const value = significant * COLOR_MULTIPLIERS[multiplierColor];
    const tolerance = COLOR_TOLERANCES[toleranceColor];
    return {
      value,
      tolerance,
      min: value * (1 - tolerance / 100),
      max: value * (1 + tolerance / 100)
    };
  }

  function smdResistorCode(code) {
    const raw = normalizeText(code).toUpperCase();
    if (!raw) throw new Error('Introduce un código.');
    if (/^0+$/.test(raw)) return { value: 0, system: 'Puente de 0 Ω', normalized: raw };

    if (/^\d{2}[A-Z]$/.test(raw)) {
      const index = Number(raw.slice(0, 2));
      const letter = raw[2];
      if (index < 1 || index > 96 || !(letter in EIA96_MULTIPLIERS)) throw new Error('Código EIA-96 no válido.');
      const value = EIA96_VALUES[index - 1] * EIA96_MULTIPLIERS[letter];
      return { value, system: 'EIA-96', normalized: raw };
    }

    if (/^\d*R\d+$/.test(raw) || /^R\d+$/.test(raw)) {
      const value = Number(raw.replace('R', '.'));
      if (!Number.isFinite(value)) throw new Error('Código con R no válido.');
      return { value, system: 'Decimal con R', normalized: raw };
    }

    if (/^\d{3}$/.test(raw)) {
      const value = Number(raw.slice(0, 2)) * Math.pow(10, Number(raw[2]));
      return { value, system: 'Código de 3 cifras', normalized: raw };
    }
    if (/^\d{4}$/.test(raw)) {
      const value = Number(raw.slice(0, 3)) * Math.pow(10, Number(raw[3]));
      return { value, system: 'Código de 4 cifras', normalized: raw };
    }
    throw new Error('Formato no reconocido. Prueba 472, 1001, 4R7, R22 o 01C.');
  }

  function capacitorCode(code) {
    const raw = normalizeText(code).toUpperCase();
    const match = raw.match(/^(\d{3})([A-Z])?$/);
    if (!match) throw new Error('Formato no reconocido. Ejemplos: 104, 472J, 225K.');
    const digits = match[1];
    const toleranceCode = match[2] || '';
    const pf = Number(digits.slice(0, 2)) * Math.pow(10, Number(digits[2]));
    const toleranceMap = { B: 0.1, C: 0.25, D: 0.5, F: 1, G: 2, J: 5, K: 10, M: 20, Z: '−20/+80' };
    return {
      farads: pf * 1e-12,
      pf,
      toleranceCode,
      tolerance: toleranceCode ? (toleranceMap[toleranceCode] ?? 'No identificada') : null,
      normalized: raw
    };
  }

  function equivalent(values, componentType, connection) {
    const list = values.map(Number);
    if (!list.length || list.some(v => !Number.isFinite(v) || v < 0)) {
      throw new Error('Introduce valores válidos en todos los elementos.');
    }
    if (componentType === 'R') {
      if (connection === 'series') return list.reduce((a, b) => a + b, 0);
      if (list.some(v => v === 0)) return 0;
      return 1 / list.reduce((sum, v) => sum + 1 / v, 0);
    }
    if (componentType === 'C') {
      if (connection === 'parallel') return list.reduce((a, b) => a + b, 0);
      if (list.some(v => v === 0)) return 0;
      return 1 / list.reduce((sum, v) => sum + 1 / v, 0);
    }
    throw new Error('Tipo de componente no válido.');
  }

  function voltageDivider(vin, r1, r2, load) {
    [vin, r1, r2].forEach(v => { if (!Number.isFinite(v) || v < 0) throw new Error('Valores no válidos.'); });
    if (r1 + r2 === 0) throw new Error('R1 y R2 no pueden ser ambas cero.');
    const noLoad = vin * r2 / (r1 + r2);
    const dividerCurrent = vin / (r1 + r2);
    let loaded = noLoad, r2eq = r2, loadCurrent = 0;
    if (Number.isFinite(load) && load > 0) {
      r2eq = r2 * load / (r2 + load);
      loaded = vin * r2eq / (r1 + r2eq);
      loadCurrent = loaded / load;
    }
    const p1 = Math.pow(vin - loaded, 2) / r1;
    const p2 = loaded * loaded / r2;
    return {
      noLoad, loaded, dividerCurrent, loadCurrent, r2eq,
      errorPercent: noLoad === 0 ? 0 : ((loaded - noLoad) / noLoad) * 100,
      p1: Number.isFinite(p1) ? p1 : 0,
      p2: Number.isFinite(p2) ? p2 : 0
    };
  }

  function rcTime(r, c) {
    if (![r, c].every(v => Number.isFinite(v) && v > 0)) throw new Error('R y C deben ser mayores que cero.');
    const tau = r * c;
    return {
      tau,
      t632: tau,
      t90: -tau * Math.log(0.10),
      t95: -tau * Math.log(0.05),
      t99: -tau * Math.log(0.01),
      t999: -tau * Math.log(0.001)
    };
  }

  function rectifiedBus(vac, diodeDrop = 0.9, diodeCount = 2, mainsHz = 50, current = 0, capacitance = 0, topology = 'single') {
    if (![vac, diodeDrop, diodeCount, mainsHz, current, capacitance].every(v => Number.isFinite(v) && v >= 0)) throw new Error('Valores no válidos.');
    if (!['single', 'three'].includes(topology)) throw new Error('Topología de red no válida.');
    const peak = vac * Math.SQRT2;
    const noLoad = Math.max(0, peak - diodeDrop * diodeCount);
    const rippleFrequency = mainsHz * (topology === 'three' ? 6 : 2);
    const averageRectified = Math.max(0, (topology === 'three' ? 1.35 : 0.9) * vac - diodeDrop * diodeCount);
    const ripple = current > 0 && capacitance > 0 ? current / (rippleFrequency * capacitance) : 0;
    const approximateLoaded = Math.max(0, noLoad - ripple / 2);
    const minimum = Math.max(0, noLoad - ripple);
    return { topology, peak, noLoad, averageRectified, rippleFrequency, ripple, approximateLoaded, minimum };
  }

  function ledArray(vs, vf, current, ledsSeries = 1, parallelBranches = 1) {
    const values = [vs, vf, current, ledsSeries, parallelBranches].map(Number);
    if (!values.every(Number.isFinite) || vs <= 0 || vf <= 0 || current <= 0) throw new Error('Tensión y corriente deben ser mayores que cero.');
    if (!Number.isInteger(ledsSeries) || ledsSeries < 1 || !Number.isInteger(parallelBranches) || parallelBranches < 1) throw new Error('La cantidad de LED y ramas debe ser un número entero positivo.');
    const ledVoltage = vf * ledsSeries;
    const resistorVoltage = vs - ledVoltage;
    if (resistorVoltage <= 0) throw new Error('La alimentación debe superar la suma de las tensiones directas de los LED de cada rama.');
    const resistance = resistorVoltage / current;
    const resistorPower = resistorVoltage * current;
    return {
      ledVoltage, resistorVoltage, resistance, resistorPower,
      totalCurrent: current * parallelBranches,
      totalPower: vs * current * parallelBranches,
      totalLeds: ledsSeries * parallelBranches,
      resistorsRequired: parallelBranches
    };
  }

  function zenerResistor(vs, vz, loadCurrent, zenerCurrent) {
    [vs, vz, loadCurrent, zenerCurrent].forEach(v => { if (!Number.isFinite(v) || v < 0) throw new Error('Introduce valores válidos y no negativos.'); });
    if (vs <= vz) throw new Error('La tensión de entrada debe ser mayor que la tensión Zener.');
    if (zenerCurrent <= 0) throw new Error('La corriente mínima del Zener debe ser mayor que cero.');
    const sourceCurrent = loadCurrent + zenerCurrent;
    const resistorVoltage = vs - vz;
    const resistance = resistorVoltage / sourceCurrent;
    const resistorPower = resistorVoltage * sourceCurrent;
    const zenerPowerAtLoad = vz * zenerCurrent;
    const zenerPowerNoLoad = vz * sourceCurrent;
    return { sourceCurrent, resistorVoltage, resistance, resistorPower, zenerPowerAtLoad, zenerPowerNoLoad };
  }

  function timer555Astable(ra, rb, capacitance) {
    [ra, rb, capacitance].forEach(v => { if (!Number.isFinite(v) || v <= 0) throw new Error('RA, RB y C deben ser mayores que cero.'); });
    const high = Math.LN2 * (ra + rb) * capacitance;
    const low = Math.LN2 * rb * capacitance;
    const period = high + low;
    return {
      high, low, period,
      frequency: 1 / period,
      duty: high / period * 100
    };
  }

  function timer555Bistable(vcc, setPullup, resetPulldown) {
    [vcc, setPullup, resetPulldown].forEach(v => { if (!Number.isFinite(v) || v <= 0) throw new Error('VCC y las resistencias deben ser mayores que cero.'); });
    return {
      setThreshold: vcc / 3,
      resetThreshold: vcc * 2 / 3,
      setButtonCurrent: vcc / setPullup,
      resetButtonCurrent: vcc / resetPulldown,
      setPullPower: vcc * vcc / setPullup,
      resetPullPower: vcc * vcc / resetPulldown
    };
  }

  function capacitorHealth(nominal, measured, tolerance = 5) {
    if (![nominal, measured, tolerance].every(v => Number.isFinite(v) && v >= 0) || nominal === 0) throw new Error('Valores no válidos.');
    const deviation = ((measured - nominal) / nominal) * 100;
    const absDeviation = Math.abs(deviation);
    let status = 'Correcto';
    let severity = 'ok';
    if (absDeviation > tolerance && absDeviation <= tolerance * 2) { status = 'Fuera de tolerancia'; severity = 'warn'; }
    if (absDeviation > tolerance * 2) { status = 'Desviación elevada'; severity = 'danger'; }
    return {
      deviation, status, severity,
      min: nominal * (1 - tolerance / 100),
      max: nominal * (1 + tolerance / 100)
    };
  }

  function ntcTemperatureFromResistance(r, r0, beta, t0C = 25) {
    if (![r, r0, beta].every(v => Number.isFinite(v) && v > 0)) throw new Error('R, R0 y Beta deben ser mayores que cero.');
    const t0K = t0C + 273.15;
    const tK = 1 / (1 / t0K + Math.log(r / r0) / beta);
    return tK - 273.15;
  }

  function ntcResistanceFromTemperature(tempC, r0, beta, t0C = 25) {
    if (![r0, beta].every(v => Number.isFinite(v) && v > 0) || !Number.isFinite(tempC)) throw new Error('Valores no válidos.');
    const tK = tempC + 273.15;
    const t0K = t0C + 273.15;
    if (tK <= 0) throw new Error('Temperatura inferior al cero absoluto.');
    return r0 * Math.exp(beta * (1 / tK - 1 / t0K));
  }

  function windingBalance(values) {
    const list = values.map(Number);
    if (list.length !== 3 || list.some(v => !Number.isFinite(v) || v <= 0)) throw new Error('Introduce tres resistencias mayores que cero.');
    const average = list.reduce((a, b) => a + b, 0) / 3;
    const deviations = list.map(v => ((v - average) / average) * 100);
    const maxDeviation = Math.max(...deviations.map(Math.abs));
    const spread = ((Math.max(...list) - Math.min(...list)) / average) * 100;
    let status = 'Equilibrado';
    let severity = 'ok';
    if (maxDeviation > 2 && maxDeviation <= 5) { status = 'Revisar medición y conexiones'; severity = 'warn'; }
    if (maxDeviation > 5) { status = 'Desequilibrio significativo'; severity = 'danger'; }
    return { average, deviations, maxDeviation, spread, status, severity };
  }

  function frequencyData(frequency, pulsesPerRev = 1, polePairs = null) {
    if (!Number.isFinite(frequency) || frequency <= 0) throw new Error('La frecuencia debe ser mayor que cero.');
    const period = 1 / frequency;
    const rpmFromPulses = Number.isFinite(pulsesPerRev) && pulsesPerRev > 0 ? frequency * 60 / pulsesPerRev : null;
    const synchronousRpm = Number.isFinite(polePairs) && polePairs > 0 ? frequency * 60 / polePairs : null;
    return { period, rpmFromPulses, synchronousRpm, angular: 2 * Math.PI * frequency };
  }

  return {
    parseEngineering, formatEngineering, ohmsLaw, resistorColors,
    smdResistorCode, capacitorCode, equivalent, voltageDivider, rcTime,
    rectifiedBus, ledArray, zenerResistor, timer555Astable, timer555Bistable,
    capacitorHealth, ntcTemperatureFromResistance,
    ntcResistanceFromTemperature, windingBalance, frequencyData,
    constants: {
      EIA96_VALUES, EIA96_MULTIPLIERS, COLOR_DIGITS, COLOR_MULTIPLIERS,
      COLOR_TOLERANCES,
    }
  };
});
