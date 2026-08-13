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

  function pressureBracket(rows, pressurePaAbs) {
    if (!Array.isArray(rows) || rows.length < 2) {
      throw new FrigoristaError('invalid_mollier_data', 'Los datos Mollier no contienen suficientes presiones.');
    }
    const target = finite(pressurePaAbs, 'La presión absoluta');
    if (target < rows[0].p || target > rows[rows.length - 1].p) {
      throw new FrigoristaError('mollier_pressure_out_of_range', 'La presión está fuera del diagrama disponible.', {
        minimum_pa_abs: rows[0].p,
        maximum_pa_abs: rows[rows.length - 1].p,
      });
    }
    let low = 0;
    let high = rows.length - 1;
    while (low <= high) {
      const middle = Math.floor((low + high) / 2);
      if (rows[middle].p === target) return [rows[middle], rows[middle], 0];
      if (rows[middle].p < target) low = middle + 1;
      else high = middle - 1;
    }
    const lower = rows[low - 1];
    const upper = rows[low];
    const fraction = (Math.log(target) - Math.log(lower.p)) / (Math.log(upper.p) - Math.log(lower.p));
    return [lower, upper, fraction];
  }

  function interpolateOffsetState(states, offsetK) {
    if (!Array.isArray(states) || states.length < 2) return null;
    const target = finite(offsetK, 'La separación respecto a saturación');
    if (target < states[0][0] || target > states[states.length - 1][0]) return null;
    let low = 0;
    let high = states.length - 1;
    while (low <= high) {
      const middle = Math.floor((low + high) / 2);
      if (states[middle][0] === target) return {enthalpy_kj_kg: states[middle][1], entropy_kj_kg_k: states[middle][2]};
      if (states[middle][0] < target) low = middle + 1;
      else high = middle - 1;
    }
    const lower = states[low - 1];
    const upper = states[low];
    const fraction = (target - lower[0]) / (upper[0] - lower[0]);
    return {
      enthalpy_kj_kg: lower[1] + fraction * (upper[1] - lower[1]),
      entropy_kj_kg_k: lower[2] + fraction * (upper[2] - lower[2]),
    };
  }

  function stateAtPressureRow(row, region, offsetK) {
    const saturation = region === 'vapor' ? row.dew : row.bubble;
    const states = [[0, saturation[1], saturation[2]], ...(row[region] || [])];
    return interpolateOffsetState(states, offsetK);
  }

  function lookupMollierState({mollier, designation, pressurePaAbs, temperatureC, region}) {
    if (!['vapor', 'liquid'].includes(region)) {
      throw new FrigoristaError('invalid_mollier_region', 'La región Mollier debe ser vapor o líquido.');
    }
    const canonical = normalizeDesignation(designation);
    const refrigerant = mollier?.refrigerants?.[canonical];
    if (!refrigerant) {
      throw new FrigoristaError('mollier_unavailable', `No hay propiedades Mollier publicadas para ${canonical}.`);
    }
    const pressure = finite(pressurePaAbs, 'La presión absoluta');
    const temperature = finite(temperatureC, 'La temperatura medida');
    const [lower, upper, pressureFraction] = pressureBracket(refrigerant.pressure_rows, pressure);
    const saturationIndex = region === 'vapor' ? 'dew' : 'bubble';
    const saturationTemperatureC = lower[saturationIndex][0]
      + pressureFraction * (upper[saturationIndex][0] - lower[saturationIndex][0]);
    const offsetK = region === 'vapor'
      ? temperature - saturationTemperatureC
      : saturationTemperatureC - temperature;
    if (offsetK < 0) {
      throw new FrigoristaError(
        region === 'vapor' ? 'not_superheated_vapor' : 'not_subcooled_liquid',
        region === 'vapor'
          ? 'La temperatura introducida no sitúa ese punto en vapor recalentado.'
          : 'La temperatura introducida no sitúa ese punto en líquido subenfriado.',
        {saturation_temperature_c: round(saturationTemperatureC, 2), offset_k: round(offsetK, 2)}
      );
    }
    const lowerState = stateAtPressureRow(lower, region, offsetK);
    const upperState = stateAtPressureRow(upper, region, offsetK);
    if (!lowerState || !upperState) {
      throw new FrigoristaError('mollier_temperature_out_of_range', 'La temperatura está fuera de la zona Mollier publicada.', {
        offset_k: round(offsetK, 2),
      });
    }
    return {
      pressure_pa_abs: round(pressure, 0),
      temperature_c: round(temperature, 2),
      saturation_temperature_c: round(saturationTemperatureC, 2),
      saturation_offset_k: round(offsetK, 2),
      region,
      enthalpy_kj_kg: round(
        lowerState.enthalpy_kj_kg + pressureFraction * (upperState.enthalpy_kj_kg - lowerState.enthalpy_kj_kg),
        2
      ),
      entropy_kj_kg_k: round(
        lowerState.entropy_kj_kg_k + pressureFraction * (upperState.entropy_kj_kg_k - lowerState.entropy_kj_kg_k),
        4
      ),
      source: mollier.engine,
      interpolation: 'log_pressure_and_saturation_offset',
    };
  }

  function mollierPoint(number, label, source, extra = {}) {
    return {number, label, ...source, ...extra};
  }

  function analyzeMollierCycle({mollier, designation, measurements = {}}) {
    const low = measurements.low_pressure;
    const high = measurements.high_pressure;
    const suction = measurements.suction_line_temperature;
    const discharge = measurements.discharge_line_temperature;
    const liquid = measurements.liquid_line_temperature;
    const points = {};
    const evidence = [];
    const missing = [];
    const errors = [];

    if (!low) missing.push('low_pressure');
    if (!suction) missing.push('suction_line_temperature');
    if (!high) missing.push('high_pressure');
    if (!liquid) missing.push('liquid_line_temperature');
    if (!discharge) missing.push('discharge_line_temperature');

    if (low && high && high.result.pressure_pa_abs <= low.result.pressure_pa_abs) {
      errors.push({code: 'invalid_pressure_order', message: 'La presión de alta debe ser mayor que la presión de baja.'});
    }
    if (low && high && low.result.designation !== high.result.designation) {
      errors.push({code: 'mixed_refrigerant_session', message: 'Las presiones de baja y alta pertenecen a refrigerantes diferentes.'});
    }

    function capturePoint(code, number, label, pressureRecord, temperatureRecord, region) {
      if (!pressureRecord || !temperatureRecord) return;
      try {
        points[code] = mollierPoint(number, label, lookupMollierState({
          mollier,
          designation,
          pressurePaAbs: pressureRecord.result.pressure_pa_abs,
          temperatureC: temperatureRecord.value,
          region,
        }), {quality: temperatureRecord.quality || 'measured'});
      } catch (error) {
        errors.push({code: error.code || 'mollier_point_error', message: error.message, point: number, details: error.details || {}});
      }
    }

    capturePoint('suction', 1, 'Aspiración del compresor', low, suction, 'vapor');
    capturePoint('discharge', 2, 'Descarga del compresor', high, discharge, 'vapor');
    capturePoint('liquid', 3, 'Salida de líquido', high, liquid, 'liquid');
    if (points.liquid && low) {
      points.expansion = mollierPoint(4, 'Salida de expansión', {
        pressure_pa_abs: round(low.result.pressure_pa_abs, 0),
        enthalpy_kj_kg: points.liquid.enthalpy_kj_kg,
        entropy_kj_kg_k: null,
        temperature_c: round(low.result.bubble_temperature_c, 2),
        region: 'two_phase',
        source: mollier.engine,
        interpolation: 'isenthalpic_expansion',
      }, {quality: 'derived'});
    }

    const performance = {};
    if (points.suction && points.expansion) {
      performance.evaporator_effect_kj_kg = round(
        points.suction.enthalpy_kj_kg - points.expansion.enthalpy_kj_kg,
        1
      );
      if (performance.evaporator_effect_kj_kg <= 0) {
        errors.push({code: 'nonpositive_evaporator_effect', message: 'Los puntos introducidos no producen un efecto frigorífico positivo.'});
      } else {
        evidence.push({level: 'ok', title: 'Evaporador trazado', detail: 'La diferencia de entalpía entre la salida de expansión y la aspiración es positiva.'});
      }
    }
    if (points.discharge && points.suction) {
      performance.compressor_work_kj_kg = round(
        points.discharge.enthalpy_kj_kg - points.suction.enthalpy_kj_kg,
        1
      );
      if (performance.compressor_work_kj_kg <= 0) {
        errors.push({code: 'nonpositive_compressor_work', message: 'La descarga medida no refleja un aumento positivo de entalpía en el compresor.'});
      }
    }
    if (points.discharge && points.liquid) {
      performance.condenser_heat_kj_kg = round(
        points.discharge.enthalpy_kj_kg - points.liquid.enthalpy_kj_kg,
        1
      );
    }
    if (performance.evaporator_effect_kj_kg > 0 && performance.compressor_work_kj_kg > 0) {
      performance.cop_cycle = round(
        performance.evaporator_effect_kj_kg / performance.compressor_work_kj_kg,
        2
      );
      evidence.push({level: 'ok', title: 'Ciclo energético completo', detail: 'Ya pueden compararse el efecto frigorífico y el trabajo específico del compresor.'});
    } else if (points.suction && points.liquid && !points.discharge) {
      evidence.push({level: 'info', title: 'Diagrama parcial fiable', detail: 'Falta la temperatura de descarga para cerrar la compresión y estimar el COP del ciclo.'});
    }

    errors.forEach(error => evidence.push({level: 'warning', title: 'Dato a revisar', detail: error.message}));
    return {
      schema_version: '1.0.0',
      designation: normalizeDesignation(designation),
      status: errors.length ? 'review' : (performance.cop_cycle ? 'complete' : (points.suction && points.liquid ? 'partial' : 'collecting')),
      points,
      performance,
      missing,
      errors,
      evidence,
      method: 'pressure_enthalpy_mollier',
      limitations: [
        'Las entalpías son relativas y se usan como diferencias dentro del mismo refrigerante y versión de datos.',
        'El resultado describe el ciclo en los puntos medidos; no sustituye los objetivos del fabricante ni confirma por sí solo una avería.',
      ],
    };
  }

  function createMollierPlotModel(mollier, cycle) {
    const data = mollier?.refrigerants?.[cycle?.designation];
    const pointList = Object.values(cycle?.points || {}).filter(point => Number.isFinite(point.enthalpy_kj_kg) && Number.isFinite(point.pressure_pa_abs));
    if (!data || pointList.length < 2) return null;
    const pointPressures = pointList.map(point => point.pressure_pa_abs);
    const pressureMinimum = Math.max(data.pressure_range_pa_abs.minimum, Math.min(...pointPressures) / 1.8);
    const pressureMaximum = Math.min(data.pressure_range_pa_abs.maximum, Math.max(...pointPressures) * 1.8);
    let rows = data.pressure_rows.filter(row => row.p >= pressureMinimum && row.p <= pressureMaximum);
    if (rows.length < 4) rows = data.pressure_rows;
    const enthalpies = pointList.map(point => point.enthalpy_kj_kg);
    rows.forEach(row => enthalpies.push(row.bubble[1], row.dew[1]));
    const rawMinimumH = Math.min(...enthalpies);
    const rawMaximumH = Math.max(...enthalpies);
    const enthalpyPadding = Math.max(15, (rawMaximumH - rawMinimumH) * 0.1);
    const minimumH = rawMinimumH - enthalpyPadding;
    const maximumH = rawMaximumH + enthalpyPadding;
    const minimumLogP = Math.log10(rows[0].p);
    const maximumLogP = Math.log10(rows[rows.length - 1].p);
    const x = value => (value - minimumH) / (maximumH - minimumH);
    const y = value => (Math.log10(value) - minimumLogP) / (maximumLogP - minimumLogP);
    const normalizePoint = point => ({...point, x: x(point.enthalpy_kj_kg), y: y(point.pressure_pa_abs)});
    const normalizedPoints = {};
    Object.entries(cycle.points).forEach(([key, point]) => {
      if (Number.isFinite(point.enthalpy_kj_kg) && Number.isFinite(point.pressure_pa_abs)) normalizedPoints[key] = normalizePoint(point);
    });
    const segmentKeys = cycle.points.discharge
      ? [['suction', 'discharge'], ['discharge', 'liquid'], ['liquid', 'expansion'], ['expansion', 'suction']]
      : [['liquid', 'expansion'], ['expansion', 'suction']];
    return {
      domain: {
        enthalpy_kj_kg: [round(minimumH, 1), round(maximumH, 1)],
        pressure_pa_abs: [round(rows[0].p, 0), round(rows[rows.length - 1].p, 0)],
      },
      bubble: rows.map(row => ({x: x(row.bubble[1]), y: y(row.p)})),
      dew: rows.map(row => ({x: x(row.dew[1]), y: y(row.p)})),
      points: normalizedPoints,
      segments: segmentKeys
        .filter(([from, to]) => normalizedPoints[from] && normalizedPoints[to])
        .map(([from, to]) => ({from, to})),
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
    if (!measurements.discharge_line_temperature) {
      return {code: 'discharge_line_temperature', label: 'Temperatura del tubo de descarga', reason: 'Cierra el ciclo en el diagrama de Mollier y permite estimar su rendimiento.', optional: true};
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
    lookupMollierState,
    analyzeMollierCycle,
    createMollierPlotModel,
    nextUsefulMeasurement,
  });
});
