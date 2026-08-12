(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.CondensateDrainEngine = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const PIPE_INTERNAL_DIAMETERS_MM = Object.freeze([16, 20, 25, 32, 40, 50, 63, 75, 90, 110]);
  const LATENT_FRACTIONS = Object.freeze({ normal: 0.25, humid: 0.35, very_humid: 0.45 });

  function number(value, field) {
    const parsed = typeof value === 'number' ? value : Number(String(value ?? '').replace(',', '.'));
    if (!Number.isFinite(parsed) || parsed < 0) throw new Error(`${field} debe ser un número igual o mayor que cero.`);
    return parsed;
  }

  function capacityToKw(value, unit) {
    const amount = number(value, 'La potencia');
    if (unit === 'kw') return amount;
    if (unit === 'frig_h') return amount * 0.001163;
    if (unit === 'btu_h') return amount * 0.00029307107;
    throw new Error('Unidad de potencia no reconocida.');
  }

  function estimateCondensateLh(capacity, unit, climate) {
    const fraction = LATENT_FRACTIONS[climate];
    if (!fraction) throw new Error('Selecciona una condición de humedad válida.');
    return capacityToKw(capacity, unit) * fraction * 3600 / 2450;
  }

  function manningHalfFullCapacityLh(diameterMm, slopePercent, roughness = 0.011) {
    const diameter = number(diameterMm, 'El diámetro') / 1000;
    const slope = number(slopePercent, 'La pendiente') / 100;
    const n = number(roughness, 'La rugosidad');
    if (!diameter || !slope || !n) return 0;
    const area = Math.PI * diameter * diameter / 8;
    const hydraulicRadius = diameter / 4;
    const cubicMetresPerSecond = (1 / n) * area * Math.pow(hydraulicRadius, 2 / 3) * Math.sqrt(slope);
    return cubicMetresPerSecond * 3600000;
  }

  function normaliseUnit(unit, index) {
    const name = String(unit.name || `Equipo ${index + 1}`).trim();
    const mode = unit.mode === 'known_flow' ? 'known_flow' : 'capacity';
    const connectionMm = number(unit.connection_mm ?? 16, `La conexión de ${name}`);
    const segmentLengthM = number(unit.segment_length_m ?? 0, `La longitud de ${name}`);
    let rawFlowLh;
    let margin;
    let source;
    if (mode === 'known_flow') {
      rawFlowLh = number(unit.flow_l_h, `El caudal de ${name}`);
      margin = 1.15;
      source = 'measured_or_manufacturer';
    } else {
      rawFlowLh = estimateCondensateLh(unit.capacity, unit.capacity_unit || 'kw', unit.climate || 'humid');
      margin = 1.25;
      source = 'estimated';
    }
    if (!rawFlowLh) throw new Error(`${name} debe aportar un caudal mayor que cero.`);
    return {
      id: String(unit.id || `unit-${index + 1}`),
      name,
      mode,
      raw_flow_l_h: rawFlowLh,
      design_flow_l_h: rawFlowLh * margin,
      margin,
      source,
      connection_mm: connectionMm,
      segment_length_m: segmentLengthM,
    };
  }

  function selectDiameter(flowLh, slopePercent, minimumMm) {
    const minimum = number(minimumMm, 'El diámetro mínimo');
    return PIPE_INTERNAL_DIAMETERS_MM.find(diameter => (
      diameter >= minimum && manningHalfFullCapacityLh(diameter, slopePercent) * 0.25 >= flowLh
    )) || null;
  }

  function designNetwork(input) {
    const units = Array.isArray(input?.units) ? input.units.map(normaliseUnit) : [];
    if (!units.length) throw new Error('Añade al menos un equipo a la red de desagüe.');
    const slopePercent = number(input.slope_percent ?? 1, 'La pendiente');
    if (slopePercent <= 0) throw new Error('La pendiente debe ser mayor que cero.');

    let cumulativeRaw = 0;
    let cumulativeDesign = 0;
    let minimumConnection = 0;
    const segments = units.map((unit, index) => {
      cumulativeRaw += unit.raw_flow_l_h;
      cumulativeDesign += unit.design_flow_l_h;
      minimumConnection = Math.max(minimumConnection, unit.connection_mm);
      const diameterMm = selectDiameter(cumulativeDesign, slopePercent, minimumConnection);
      const hydraulicCapacityLh = diameterMm ? manningHalfFullCapacityLh(diameterMm, slopePercent) : null;
      const usableCapacityLh = hydraulicCapacityLh ? hydraulicCapacityLh * 0.25 : null;
      return {
        index,
        from: unit.name,
        to: index === units.length - 1 ? 'Desagüe' : `Unión con ${units[index + 1].name}`,
        segment_length_m: unit.segment_length_m,
        fall_cm: unit.segment_length_m * slopePercent,
        cumulative_raw_flow_l_h: cumulativeRaw,
        cumulative_design_flow_l_h: cumulativeDesign,
        minimum_connection_mm: minimumConnection,
        recommended_internal_diameter_mm: diameterMm,
        half_full_hydraulic_capacity_l_h: hydraulicCapacityLh,
        usable_design_capacity_l_h: usableCapacityLh,
        capacity_ratio: usableCapacityLh ? cumulativeDesign / usableCapacityLh : null,
      };
    });
    const last = segments[segments.length - 1];
    const warnings = [];
    if (!last.recommended_internal_diameter_mm) warnings.push('El caudal supera la tabla de diámetros disponible; requiere cálculo específico.');
    if (slopePercent < 1) warnings.push('Pendiente inferior al 1 %: revisa trazado, nivelación, accesibilidad y riesgo de depósitos.');
    if (units.some(unit => unit.source === 'estimated')) warnings.push('Hay caudales estimados. Sustitúyelos por datos de fabricante o mediciones cuando estén disponibles.');
    return {
      schema_version: '1.0.0',
      method: 'gravity_manning_half_full',
      assumptions: {
        roughness_manning: 0.011,
        fill: 'half_full',
        usable_capacity_factor: 0.25,
        latent_fractions: LATENT_FRACTIONS,
        margins: { estimated: 1.25, measured_or_manufacturer: 1.15 },
      },
      slope_percent: slopePercent,
      units,
      segments,
      total_raw_flow_l_h: last.cumulative_raw_flow_l_h,
      total_design_flow_l_h: last.cumulative_design_flow_l_h,
      collector_internal_diameter_mm: last.recommended_internal_diameter_mm,
      total_length_m: units.reduce((sum, unit) => sum + unit.segment_length_m, 0),
      total_fall_cm: units.reduce((sum, unit) => sum + unit.segment_length_m * slopePercent, 0),
      warnings,
    };
  }

  return {
    PIPE_INTERNAL_DIAMETERS_MM,
    LATENT_FRACTIONS,
    capacityToKw,
    estimateCondensateLh,
    manningHalfFullCapacityLh,
    selectDiameter,
    designNetwork,
  };
}));
