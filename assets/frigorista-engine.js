(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.STFrigorista = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  const DEFAULT_ATMOSPHERIC_PRESSURE_PA = 101325;
  const PRESSURE_FACTORS = Object.freeze({
    bar: 100000,
    psi: 6894.757293168,
    kpa: 1000,
    mpa: 1000000,
  });

  class FrigoristaError extends Error {
    constructor(code, message, details = {}) {
      super(message);
      this.name = 'FrigoristaError';
      this.code = code;
      this.details = details;
    }
  }

  function finite(value, label) {
    const parsed = typeof value === 'string'
      ? Number(value.trim().replace(',', '.'))
      : Number(value);
    if (!Number.isFinite(parsed)) {
      throw new FrigoristaError('invalid_number', `${label} no contiene un número válido.`);
    }
    return parsed;
  }

  function round(value, decimals = 1) {
    const factor = 10 ** decimals;
    return Math.round((value + Number.EPSILON) * factor) / factor;
  }

  function normalizeDesignation(value) {
    const normalized = String(value || '')
      .trim()
      .replace(/^r[-\s]*/i, 'R')
      .replace(/\s+/g, '');
    if (!normalized) return '';
    return `R${normalized.slice(1)}`;
  }

  function toAbsolutePressurePa(value, unit = 'bar', reference = 'gauge', atmosphericPressurePa = DEFAULT_ATMOSPHERIC_PRESSURE_PA) {
    const amount = finite(value, 'La presión');
    const factor = PRESSURE_FACTORS[String(unit).toLowerCase()];
    if (!factor) throw new FrigoristaError('unsupported_unit', `Unidad de presión no disponible: ${unit}`);
    const atmosphere = finite(atmosphericPressurePa, 'La presión atmosférica');
    if (atmosphere <= 0) throw new FrigoristaError('invalid_atmosphere', 'La presión atmosférica debe ser positiva.');
    const pressurePa = amount * factor + (reference === 'gauge' ? atmosphere : 0);
    if (pressurePa <= 0) {
      throw new FrigoristaError('invalid_absolute_pressure', 'La presión absoluta resultante debe ser mayor que cero.');
    }
    return pressurePa;
  }

  function fromPressurePa(pressurePa, unit = 'bar', reference = 'gauge', atmosphericPressurePa = DEFAULT_ATMOSPHERIC_PRESSURE_PA) {
    const factor = PRESSURE_FACTORS[String(unit).toLowerCase()];
    if (!factor) throw new FrigoristaError('unsupported_unit', `Unidad de presión no disponible: ${unit}`);
    const absolute = finite(pressurePa, 'La presión absoluta');
    const displayedPa = absolute - (reference === 'gauge' ? atmosphericPressurePa : 0);
    return displayedPa / factor;
  }

  function interpolatePressureCurve(points, pressurePa) {
    if (!Array.isArray(points) || points.length < 2) {
      throw new FrigoristaError('invalid_curve', 'La curva P/T no contiene suficientes datos.');
    }
    const target = finite(pressurePa, 'La presión absoluta');
    const minimum = points[0][0];
    const maximum = points[points.length - 1][0];
    if (target < minimum || target > maximum) {
      throw new FrigoristaError(
        'out_of_range',
        'La presión está fuera del intervalo calculable para este refrigerante.',
        {minimum_pa_abs: minimum, maximum_pa_abs: maximum}
      );
    }

    let low = 0;
    let high = points.length - 1;
    while (low <= high) {
      const middle = Math.floor((low + high) / 2);
      const current = points[middle][0];
      if (current === target) return points[middle][1];
      if (current < target) low = middle + 1;
      else high = middle - 1;
    }

    const upper = points[low];
    const lower = points[low - 1];
    const fraction = (target - lower[0]) / (upper[0] - lower[0]);
    return lower[1] + fraction * (upper[1] - lower[1]);
  }

  function findRefrigerant(catalog, designation) {
    const canonical = normalizeDesignation(designation).toLocaleLowerCase('es');
    return (catalog?.refrigerants || []).find(item => item.designation.toLocaleLowerCase('es') === canonical) || null;
  }

  function convertPressureToTemperature({
    catalog,
    curves,
    designation,
    pressure,
    unit = 'bar',
    reference = 'gauge',
    atmosphericPressurePa = DEFAULT_ATMOSPHERIC_PRESSURE_PA,
  }) {
    const refrigerant = findRefrigerant(catalog, designation);
    if (!refrigerant) {
      throw new FrigoristaError('unknown_refrigerant', 'No encuentro ese refrigerante en el catálogo.');
    }
    if (!refrigerant.selectable || !refrigerant.pt_available) {
      throw new FrigoristaError(
        'unsupported_refrigerant',
        refrigerant.excluded_reason || 'Este refrigerante está identificado, pero todavía no tiene una curva P/T validada.',
        {refrigerant_id: refrigerant.id}
      );
    }
    const curve = curves?.curves?.[refrigerant.designation];
    if (!curve) {
      throw new FrigoristaError('missing_curve', 'Falta la curva P/T publicada para este refrigerante.');
    }

    const pressurePaAbs = toAbsolutePressurePa(pressure, unit, reference, atmosphericPressurePa);
    const bubbleC = interpolatePressureCurve(curve.bubble, pressurePaAbs);
    const dewC = interpolatePressureCurve(curve.dew, pressurePaAbs);
    const isGlide = ['zeotropic', 'near_azeotropic'].includes(refrigerant.mixture_type)
      && Math.abs(dewC - bubbleC) >= 0.05;

    return {
      schema_version: '1.0.0',
      refrigerant_id: refrigerant.id,
      designation: refrigerant.designation,
      mixture_type: refrigerant.mixture_type,
      safety_class: refrigerant.safety_class,
      pressure_input: {value: Number(pressure), unit, reference},
      atmospheric_pressure_pa: Number(atmosphericPressurePa),
      pressure_pa_abs: round(pressurePaAbs, 0),
      result_type: isGlide ? 'bubble_dew' : 'single',
      saturation_temperature_c: round((bubbleC + dewC) / 2, 2),
      bubble_temperature_c: round(bubbleC, 2),
      dew_temperature_c: round(dewC, 2),
      glide_k: round(Math.abs(dewC - bubbleC), 2),
      source: curves.engine,
      warnings: [],
    };
  }

  function calculateSuperheat(dewTemperatureC, suctionLineTemperatureC) {
    const saturation = finite(dewTemperatureC, 'La temperatura de rocío');
    const measured = finite(suctionLineTemperatureC, 'La temperatura del tubo de aspiración');
    return {
      value_k: round(measured - saturation, 1),
      reference: 'dew',
      measured_temperature_c: measured,
      saturation_temperature_c: saturation,
    };
  }

  function calculateSubcooling(bubbleTemperatureC, liquidLineTemperatureC) {
    const saturation = finite(bubbleTemperatureC, 'La temperatura de burbuja');
    const measured = finite(liquidLineTemperatureC, 'La temperatura de la línea de líquido');
    return {
      value_k: round(saturation - measured, 1),
      reference: 'bubble',
      measured_temperature_c: measured,
      saturation_temperature_c: saturation,
    };
  }

  function nextUsefulMeasurement(session = {}) {
    const measurements = session.measurements || {};
    if (!measurements.low_pressure) {
      return {code: 'low_pressure', label: 'Presión de baja', reason: 'Permite conocer la evaporación.'};
    }
    if (!measurements.suction_line_temperature) {
      return {code: 'suction_line_temperature', label: 'Temperatura del tubo de aspiración', reason: 'Completa el recalentamiento.'};
    }
    if (!measurements.high_pressure) {
      return {code: 'high_pressure', label: 'Presión de alta', reason: 'Permite conocer la condensación.'};
    }
    if (!measurements.liquid_line_temperature) {
      return {code: 'liquid_line_temperature', label: 'Temperatura de la línea de líquido', reason: 'Completa el subenfriamiento.'};
    }
    if (!measurements.return_air_temperature) {
      return {code: 'return_air_temperature', label: 'Temperatura del aire de retorno', reason: 'Inicia la comprobación del intercambio de aire.', optional: true};
    }
    if (!measurements.supply_air_temperature) {
      return {code: 'supply_air_temperature', label: 'Temperatura del aire de impulsión', reason: 'Permite calcular el salto térmico del aire.', optional: true};
    }
    return {code: 'context_complete', label: 'Mediciones básicas completas', reason: 'Ya puede prepararse un análisis contextual.'};
  }

  return Object.freeze({
    DEFAULT_ATMOSPHERIC_PRESSURE_PA,
    PRESSURE_FACTORS,
    FrigoristaError,
    normalizeDesignation,
    toAbsolutePressurePa,
    fromPressurePa,
    interpolatePressureCurve,
    findRefrigerant,
    convertPressureToTemperature,
    calculateSuperheat,
    calculateSubcooling,
    nextUsefulMeasurement,
  });
});
