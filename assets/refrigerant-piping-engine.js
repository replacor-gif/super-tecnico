(() => {
  'use strict';

  const PI = Math.PI;
  const G = 9.80665;

  function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, Number(value)));
  }

  function round(value, digits = 2) {
    const factor = 10 ** digits;
    return Math.round((Number(value) + Number.EPSILON) * factor) / factor;
  }

  function interpolate(states, axis, target) {
    const ordered = states.slice().sort((a, b) => a[axis] - b[axis]);
    if (!ordered.length) throw new Error('No hay estados termodinámicos disponibles.');
    if (target <= ordered[0][axis]) return { ...ordered[0], extrapolated: target < ordered[0][axis] };
    if (target >= ordered.at(-1)[axis]) return { ...ordered.at(-1), extrapolated: target > ordered.at(-1)[axis] };
    const upperIndex = ordered.findIndex(item => item[axis] >= target);
    const lower = ordered[upperIndex - 1];
    const upper = ordered[upperIndex];
    const ratio = (target - lower[axis]) / (upper[axis] - lower[axis]);
    const result = { extrapolated: false };
    new Set([...Object.keys(lower), ...Object.keys(upper)]).forEach(key => {
      if (typeof lower[key] === 'number' && typeof upper[key] === 'number') {
        result[key] = lower[key] + (upper[key] - lower[key]) * ratio;
      } else {
        result[key] = lower[key] ?? upper[key];
      }
    });
    result[axis] = target;
    return result;
  }

  function dewPointC(temperatureC, relativeHumidityPercent) {
    const rh = clamp(relativeHumidityPercent, 1, 100) / 100;
    const a = 17.62;
    const b = 243.12;
    const gamma = Math.log(rh) + (a * temperatureC) / (b + temperatureC);
    return (b * gamma) / (a - gamma);
  }

  function frictionFactor(reynolds, roughnessM, diameterM) {
    if (!Number.isFinite(reynolds) || reynolds <= 0) return 0;
    if (reynolds < 2300) return 64 / reynolds;
    const term = roughnessM / (3.7 * diameterM) + 5.74 / (reynolds ** 0.9);
    return 0.25 / (Math.log10(term) ** 2);
  }

  function hydraulic(size, massFlowKgS, densityKgM3, viscosityPaS, equivalentLengthM, roughnessM) {
    const insideDiameterM = (size.od_mm - 2 * size.wall_mm) / 1000;
    const areaM2 = PI * insideDiameterM ** 2 / 4;
    const velocityMS = massFlowKgS / Math.max(0.0000001, densityKgM3 * areaM2);
    const reynolds = densityKgM3 * velocityMS * insideDiameterM / Math.max(viscosityPaS, 0.00000001);
    const factor = frictionFactor(reynolds, roughnessM, insideDiameterM);
    const pressureDropPa = factor * (equivalentLengthM / insideDiameterM) * densityKgM3 * velocityMS ** 2 / 2;
    return { insideDiameterM, areaM2, velocityMS, reynolds, factor, pressureDropPa };
  }

  function evaluateGasSize(size, context) {
    const full = hydraulic(size, context.massFlowFull, context.density, context.viscosity, context.equivalentLength, context.roughness);
    const minimum = hydraulic(size, context.massFlowMinimum, context.density, context.viscosity, context.equivalentLength, context.roughness);
    const saturationDropK = full.pressureDropPa / 1000 / Math.max(0.1, context.dpdtKpaK);
    const valid = full.velocityMS <= context.profile.maximum
      && minimum.velocityMS >= context.minimumVelocity
      && saturationDropK <= context.profile.max_saturation_drop_k;
    const penalty = Math.max(0, full.velocityMS - context.profile.maximum) * 3
      + Math.max(0, context.minimumVelocity - minimum.velocityMS) * 4
      + Math.max(0, saturationDropK - context.profile.max_saturation_drop_k) * 8;
    return { size, full, minimum, saturationDropK, valid, penalty };
  }

  function findDoubleRiser(sizes, context) {
    if (context.verticalRiseM < context.doubleRiserMinHeightM) return null;
    const candidates = [];
    sizes.forEach((small, smallIndex) => {
      const smallMinimum = hydraulic(small, context.massFlowMinimum, context.density, context.viscosity, context.equivalentLength, context.roughness);
      if (smallMinimum.velocityMS < context.minimumVelocity || smallMinimum.velocityMS > context.profile.maximum) return;
      sizes.slice(smallIndex + 1).forEach(large => {
        const smallId = (small.od_mm - 2 * small.wall_mm) / 1000;
        const largeId = (large.od_mm - 2 * large.wall_mm) / 1000;
        const totalArea = PI * (smallId ** 2 + largeId ** 2) / 4;
        const fullVelocity = context.massFlowFull / (context.density * totalArea);
        if (fullVelocity < context.minimumVelocity || fullVelocity > context.profile.maximum) return;
        const equivalentId = Math.sqrt(4 * totalArea / PI);
        const virtualSize = { od_mm: equivalentId * 1000 + 2, wall_mm: 1 };
        const full = hydraulic(virtualSize, context.massFlowFull, context.density, context.viscosity, context.equivalentLength, context.roughness);
        const saturationDropK = full.pressureDropPa / 1000 / Math.max(0.1, context.dpdtKpaK);
        if (saturationDropK > context.profile.max_saturation_drop_k) return;
        candidates.push({ small, large, smallMinimum, fullVelocity, saturationDropK });
      });
    });
    return candidates.sort((a, b) => a.saturationDropK - b.saturationDropK || a.large.od_mm - b.large.od_mm)[0] || null;
  }

  function chooseGasLine(kind, sizes, context, rules) {
    const evaluations = sizes.map(size => evaluateGasSize(size, context));
    const valid = evaluations.filter(item => item.valid).sort((a, b) => b.size.od_mm - a.size.od_mm);
    const selected = valid[0] || evaluations.slice().sort((a, b) => a.penalty - b.penalty)[0];
    let doubleRiser = null;
    if (!valid.length && context.allowDoubleRiser && context.massFlowMinimum < context.massFlowFull * 0.55) {
      doubleRiser = findDoubleRiser(sizes, { ...context, doubleRiserMinHeightM: rules.oil_management.double_riser_min_height_m });
    }
    return {
      kind,
      size: selected.size,
      displaySize: doubleRiser ? `${doubleRiser.small.label} + ${doubleRiser.large.label}` : selected.size.label,
      odMm: selected.size.od_mm,
      insideDiameterMm: round(selected.full.insideDiameterM * 1000, 2),
      velocityFullMS: round(doubleRiser ? doubleRiser.fullVelocity : selected.full.velocityMS, 2),
      velocityMinimumMS: round(doubleRiser ? doubleRiser.smallMinimum.velocityMS : selected.minimum.velocityMS, 2),
      saturationDropK: round(doubleRiser ? doubleRiser.saturationDropK : selected.saturationDropK, 2),
      pressureDropKpa: round(selected.full.pressureDropPa / 1000, 2),
      oilVelocityPass: Boolean(doubleRiser || selected.minimum.velocityMS >= context.minimumVelocity),
      pressureDropPass: (doubleRiser ? doubleRiser.saturationDropK : selected.saturationDropK) <= context.profile.max_saturation_drop_k,
      doubleRiser: doubleRiser ? {
        small: doubleRiser.small,
        large: doubleRiser.large,
        operatingPrinciple: 'El montante pequeño trabaja a carga mínima y ambos montantes a carga alta.'
      } : null,
    };
  }

  function chooseLiquidLine(sizes, context) {
    const evaluations = sizes.map(size => {
      const full = hydraulic(size, context.massFlowFull, context.density, context.viscosity, context.equivalentLength, context.roughness);
      const frictionPa = full.pressureDropPa;
      const staticPa = context.density * G * context.liquidRiseM;
      const totalPa = frictionPa + staticPa;
      const saturationDropK = totalPa / 1000 / Math.max(0.1, context.dpdtKpaK);
      const valid = full.velocityMS <= context.profile.maximum && saturationDropK <= context.profile.max_saturation_drop_k;
      const penalty = Math.max(0, full.velocityMS - context.profile.maximum) * 5
        + Math.max(0, saturationDropK - context.profile.max_saturation_drop_k) * 10;
      return { size, full, frictionPa, staticPa, totalPa, saturationDropK, valid, penalty };
    });
    const selected = evaluations.find(item => item.valid) || evaluations.slice().sort((a, b) => a.penalty - b.penalty)[0];
    return {
      kind: 'liquid',
      size: selected.size,
      displaySize: selected.size.label,
      odMm: selected.size.od_mm,
      insideDiameterMm: round(selected.full.insideDiameterM * 1000, 2),
      velocityFullMS: round(selected.full.velocityMS, 2),
      saturationDropK: round(selected.saturationDropK, 2),
      pressureDropKpa: round(selected.totalPa / 1000, 2),
      staticHeadKpa: round(selected.staticPa / 1000, 2),
      flashMarginK: round(5 - Math.max(0, selected.saturationDropK), 2),
      flashRisk: 5 - Math.max(0, selected.saturationDropK) < 1,
    };
  }

  function riteReferenceThickness(odMm, location, rules) {
    const row = rules.insulation.rite_climatization_minimum_mm.find(item => odMm <= item.max_od_mm);
    return location === 'outside' ? row.outside_mm : row.inside_mm;
  }

  function conductivityAdjustedThickness(odMm, referenceThicknessMm, conductivity, referenceConductivity) {
    if (!referenceThicknessMm) return 0;
    const ratio = (odMm + 2 * referenceThicknessMm) / odMm;
    return odMm * (ratio ** (conductivity / referenceConductivity) - 1) / 2;
  }

  function surfaceTemperature(odMm, thicknessMm, fluidTemperatureC, ambientTemperatureC, conductivity, outsideH) {
    if (thicknessMm <= 0) return fluidTemperatureC;
    const r1 = odMm / 2000;
    const r2 = r1 + thicknessMm / 1000;
    const conduction = Math.log(r2 / r1) / (2 * PI * conductivity);
    const convection = 1 / (outsideH * 2 * PI * r2);
    const heatPerM = (ambientTemperatureC - fluidTemperatureC) / (conduction + convection);
    return ambientTemperatureC - heatPerM * convection;
  }

  function sizeInsulation(line, fluidTemperatureC, input, rules, climatizationCircuit) {
    const conductivity = clamp(input.insulationConductivityWMK || rules.insulation.default_elastomeric_conductivity_w_mk, 0.025, 0.06);
    const dewPoint = dewPointC(input.ambientTemperatureC, input.relativeHumidityPercent);
    const requiredSurface = dewPoint + rules.insulation.surface_margin_above_dew_point_k;
    const regulatoryReference = climatizationCircuit ? riteReferenceThickness(line.odMm, input.location, rules) : 0;
    const regulatoryAdjusted = conductivityAdjustedThickness(
      line.odMm,
      regulatoryReference,
      conductivity,
      rules.insulation.conductivity_reference_w_mk,
    );
    const candidates = rules.insulation.commercial_thickness_mm;
    const condensationThickness = candidates.find(thickness => surfaceTemperature(
      line.odMm,
      thickness,
      fluidTemperatureC,
      input.ambientTemperatureC,
      conductivity,
      rules.insulation.outside_heat_transfer_w_m2k,
    ) >= requiredSurface) || candidates.at(-1);
    const minimum = Math.max(regulatoryAdjusted, condensationThickness);
    const selected = candidates.find(item => item >= minimum) || candidates.at(-1);
    const surface = surfaceTemperature(
      line.odMm,
      selected,
      fluidTemperatureC,
      input.ambientTemperatureC,
      conductivity,
      rules.insulation.outside_heat_transfer_w_m2k,
    );
    return {
      line: line.kind,
      thicknessMm: selected,
      regulatoryReferenceMm: regulatoryReference,
      regulatoryAdjustedMm: round(regulatoryAdjusted, 1),
      condensationControlMm: condensationThickness,
      conductivityWMK: conductivity,
      dewPointC: round(dewPoint, 1),
      surfaceTemperatureC: round(surface, 1),
      condensationMarginK: round(surface - dewPoint, 1),
      vapourBarrierRequired: fluidTemperatureC < dewPoint,
      weatherProtectionRequired: input.location === 'outside',
    };
  }

  function oilManagement(input, suctionLine, rules, profile) {
    const rise = Math.max(0, input.verticalRiseM);
    if (!profile.generic_oil_design) {
      return {
        lowerTraps: 0,
        intermediateTraps: 0,
        totalProposedTraps: 0,
        doubleRiser: null,
        status: 'fabricante_obligatorio',
        notes: ['La disposición de sifones y elementos de retorno de aceite debe obtenerse del manual del modelo seleccionado.'],
        manufacturerConfirmationRequired: true,
      };
    }
    const threshold = rules.oil_management.riser_trap_threshold_m;
    const intermediateSpacing = rules.oil_management.intermediate_trap_spacing_m;
    const lowerTraps = rise >= threshold ? 1 : 0;
    const intermediateTraps = rise > intermediateSpacing ? Math.floor((rise - 0.1) / intermediateSpacing) : 0;
    const notes = [];
    if (!rise) notes.push('El retorno no incluye un montante ascendente de aspiración.');
    if (lowerTraps) notes.push('Sifón inferior propuesto al pie del montante de aspiración.');
    if (intermediateTraps) notes.push(`${intermediateTraps} sifón/es intermedio/s propuestos para el montante largo.`);
    if (suctionLine.doubleRiser) notes.push('Se propone doble montante por el rango de carga y el compromiso entre retorno de aceite y pérdida de presión.');
    if (!suctionLine.oilVelocityPass) notes.push('La velocidad mínima calculada no garantiza retorno de aceite con una sola tubería.');
    return {
      lowerTraps,
      intermediateTraps,
      totalProposedTraps: lowerTraps + intermediateTraps,
      doubleRiser: suctionLine.doubleRiser,
      status: suctionLine.oilVelocityPass ? 'propuesta_compatible' : 'revision_obligatoria',
      notes,
      manufacturerConfirmationRequired: true,
    };
  }

  function billOfQuantities(input, lines, insulation, oil) {
    const installedLength = round(input.lengthM * 1.05, 1);
    const items = [];
    lines.forEach(line => {
      if (!line) return;
      if (line.doubleRiser) {
        const riserLength = round(Math.max(0, input.verticalRiseM) * 1.05, 1);
        const commonLength = round(Math.max(0, input.lengthM - Math.max(0, input.verticalRiseM)) * 1.05, 1);
        if (commonLength) items.push({ code: `RP-CU-${String(Math.round(line.size.od_mm * 100)).padStart(5, '0')}`, family: 'refrigerant_piping', description: `Tubo frigorífico ${line.size.label} en tramo común de ${line.kind}`, unit: 'm', quantity: commonLength, line: line.kind });
        [line.doubleRiser.small, line.doubleRiser.large].forEach(pipe => {
          items.push({ code: `RP-CU-${String(Math.round(pipe.od_mm * 100)).padStart(5, '0')}`, family: 'refrigerant_piping', description: `Tubo frigorífico ${pipe.label} en doble montante`, unit: 'm', quantity: riserLength, line: line.kind });
        });
        items.push({ code: 'RP-DOUBLE-RISER', family: 'refrigerant_piping', description: 'Montaje de doble montante con transición', unit: 'ud', quantity: 1, line: line.kind });
      } else {
        items.push({ code: `RP-CU-${String(Math.round(line.odMm * 100)).padStart(5, '0')}`, family: 'refrigerant_piping', description: `Tubo frigorífico ${line.displaySize}`, unit: 'm', quantity: installedLength, line: line.kind });
      }
    });
    insulation.forEach(item => {
      const line = lines.find(candidate => candidate?.kind === item.line);
      if (!line || item.thicknessMm <= 0) return;
      items.push({ code: `RP-INS-${item.thicknessMm}`, family: 'technical_insulation', description: `Aislamiento elastomérico ${item.thicknessMm} mm para ${line.displaySize}`, unit: 'm', quantity: installedLength, line: item.line });
    });
    if (oil.totalProposedTraps) items.push({ code: 'RP-OIL-TRAP', family: 'oil_management', description: 'Sifón de aceite conformado y soldado', unit: 'ud', quantity: oil.totalProposedTraps, line: 'suction' });
    items.push({ code: 'RP-SUPPORT', family: 'supports', description: 'Soporte compatible con barrera de vapor', unit: 'ud', quantity: Math.ceil(installedLength / 1.5) * 2 });
    if (input.location === 'outside') items.push({ code: 'RP-WEATHER', family: 'weather_protection', description: 'Protección exterior continua del aislamiento', unit: 'm', quantity: installedLength * 2 });
    return items;
  }

  function design(input, datasets) {
    const { properties, rules } = datasets;
    const profile = rules.system_profiles[input.systemType];
    if (!profile) throw new Error('Selecciona un tipo de instalación válido.');
    const fluid = properties.fluids.find(item => item.designation.toLowerCase() === String(input.refrigerant).toLowerCase());
    if (!fluid) throw new Error('Este refrigerante todavía no dispone de propiedades para dimensionar tuberías.');

    const capacityKw = clamp(input.capacityKw, 0.5, 1000);
    const minimumLoadPercent = clamp(input.minimumLoadPercent || profile.default_min_load_percent, 5, 100);
    const teC = clamp(input.evaporatingC, -40, 15);
    const tcC = clamp(input.condensingC, 25, 60);
    if (tcC - teC < 15) throw new Error('La condensación debe estar al menos 15 K por encima de la evaporación.');
    const evap = interpolate(fluid.evaporating_states, 'te_c', teC);
    const cond = interpolate(fluid.condensing_states, 'tc_c', tcC);
    const refrigerationEffect = evap.h_suction_kj_kg - cond.h_liquid_kj_kg;
    if (refrigerationEffect <= 20) throw new Error('El régimen elegido no produce un efecto frigorífico válido.');

    const massFlowFull = capacityKw / refrigerationEffect;
    const massFlowMinimum = massFlowFull * minimumLoadPercent / 100;
    const lengthM = clamp(input.lengthM, 1, 300);
    const verticalRiseM = clamp(input.verticalRiseM || 0, -80, 80);
    const route = rules.route_factors[input.routeComplexity] || rules.route_factors.normal;
    const equivalentLength = lengthM * route.equivalent_length_factor;
    const sizes = rules.pipe_material.sizes;
    const suctionProfile = rules.velocity_profiles_m_s.suction;
    const suctionMinimumVelocity = verticalRiseM > rules.oil_management.riser_trap_threshold_m ? suctionProfile.riser_min : suctionProfile.horizontal_min;
    const baseGasContext = {
      massFlowFull,
      massFlowMinimum,
      equivalentLength,
      roughness: rules.pipe_material.roughness_m,
      verticalRiseM: Math.max(0, verticalRiseM),
      minimumVelocity: suctionMinimumVelocity,
      profile: suctionProfile,
      density: evap.suction_density_kg_m3,
      viscosity: evap.suction_viscosity_pa_s,
      dpdtKpaK: evap.dpdt_evap_kpa_k,
      allowDoubleRiser: Boolean(profile.allow_double_riser),
    };
    const suction = chooseGasLine('suction', sizes, baseGasContext, rules);
    const liquid = chooseLiquidLine(sizes, {
      massFlowFull,
      equivalentLength,
      roughness: rules.pipe_material.roughness_m,
      density: cond.liquid_density_kg_m3,
      viscosity: cond.liquid_viscosity_pa_s,
      dpdtKpaK: cond.dpdt_cond_kpa_k,
      liquidRiseM: -verticalRiseM,
      profile: rules.velocity_profiles_m_s.liquid,
    });
    let discharge = null;
    if (profile.show_discharge || input.includeDischarge) {
      const dischargeProfile = rules.velocity_profiles_m_s.discharge;
      discharge = chooseGasLine('discharge', sizes, {
        ...baseGasContext,
        verticalRiseM: Math.max(0, Number(input.dischargeRiseM) || 0),
        minimumVelocity: Number(input.dischargeRiseM) > rules.oil_management.riser_trap_threshold_m ? dischargeProfile.riser_min : dischargeProfile.horizontal_min,
        profile: dischargeProfile,
        density: cond.discharge_density_kg_m3,
        viscosity: cond.discharge_viscosity_pa_s,
        dpdtKpaK: cond.dpdt_cond_kpa_k,
      }, rules);
    }

    const normalizedInput = {
      ...input,
      capacityKw,
      minimumLoadPercent,
      evaporatingC: teC,
      condensingC: tcC,
      lengthM,
      verticalRiseM,
      ambientTemperatureC: clamp(input.ambientTemperatureC || 30, -10, 50),
      relativeHumidityPercent: clamp(input.relativeHumidityPercent || 65, 10, 100),
      location: input.location === 'outside' ? 'outside' : 'inside',
    };
    const climatizationCircuit = ['split', 'vrf'].includes(input.systemType);
    const insulation = [
      sizeInsulation(suction, teC + properties.cycle_assumptions.superheat_k, normalizedInput, rules, climatizationCircuit),
      sizeInsulation(liquid, tcC - properties.cycle_assumptions.subcooling_k, normalizedInput, rules, climatizationCircuit),
    ];
    if (discharge) insulation.push({ line: 'discharge', thicknessMm: 0, reason: 'La descarga caliente se revisa por protección de personas, recuperación de calor y fabricante.' });
    const oil = oilManagement(normalizedInput, suction, rules, profile);
    const lines = [suction, liquid, discharge].filter(Boolean);
    const warnings = [];
    if (profile.manufacturer_priority && !String(input.model || '').trim()) warnings.push('Indica marca y modelo para convertir la propuesta en una comprobación contra los límites reales del fabricante.');
    if (profile.manufacturer_priority) warnings.push('En este tipo de equipo los diámetros y longitudes admisibles del fabricante tienen prioridad.');
    if (evap.extrapolated || cond.extrapolated) warnings.push('El régimen está en el límite de la tabla termodinámica; se requiere revisión específica.');
    if (!suction.oilVelocityPass) warnings.push('No queda garantizado el retorno de aceite a carga mínima con una tubería única.');
    if (!suction.pressureDropPass) warnings.push('La pérdida de presión de aspiración supera el objetivo interno del predimensionado.');
    if (discharge && !discharge.oilVelocityPass) warnings.push('La descarga necesita revisión de velocidad y retorno de aceite en todo el rango de carga.');
    if (discharge && !discharge.pressureDropPass) warnings.push('La pérdida de presión de descarga supera el objetivo interno del predimensionado.');
    if (liquid.flashRisk) warnings.push('El margen de subenfriamiento restante es pequeño: existe riesgo de gas flash antes de la expansión.');
    if (fluid.safety_class === 'A2L' || fluid.safety_class === 'A2' || fluid.safety_class === 'A3') warnings.push(`Refrigerante ${fluid.safety_class}: comprobar carga admisible, emplazamiento, ventilación, fuentes de ignición y medidas RSIF.`);
    if (normalizedInput.location === 'outside') warnings.push('La barrera de vapor y el aislamiento exterior necesitan acabado continuo resistente a intemperie y radiación UV.');
    warnings.push('Confirmar espesor y presión admisible del tubo, uniones, soportación, dilatación, pruebas y requisitos autonómicos o locales.');

    return {
      schemaVersion: '1.0.0',
      resultLevel: profile.manufacturer_priority ? 'manufacturer_required' : 'reviewed_preliminary',
      input: normalizedInput,
      fluid: { designation: fluid.designation, safetyClass: fluid.safety_class, mixtureType: fluid.mixture_type },
      thermodynamicSummary: {
        refrigerationEffectKjKg: round(refrigerationEffect, 1),
        massFlowKgS: round(massFlowFull, 4),
        evaporatingPressureBarAbs: round(evap.p_evap_bar_abs, 2),
        condensingPressureBarAbs: round(cond.p_cond_bar_abs, 2),
      },
      route: { actualLengthM: lengthM, equivalentLengthM: round(equivalentLength, 1), verticalDifferenceM: verticalRiseM },
      lines,
      oilManagement: oil,
      insulation,
      warnings: [...new Set(warnings)],
      billOfQuantities: billOfQuantities(normalizedInput, lines, insulation, oil),
      sources: rules.sources,
      assumptions: properties.cycle_assumptions,
    };
  }

  window.RefrigerantPipingEngine = { design, dewPointC, interpolate, surfaceTemperature };
})();
