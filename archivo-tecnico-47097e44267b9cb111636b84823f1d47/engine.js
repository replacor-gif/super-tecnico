const ElectroEngine = (function () {
  "use strict";

  const REQUIRED_SYMBOLS = {
    power: "SYM-0014",
    ground: "SYM-0010",
    resistor: "SYM-0023",
    diode: "SYM-0057",
    mosfet: "SYM-0080",
    optocoupler: "SYM-0097",
    relayCoil: "SYM-0119",
    relayContact: "SYM-0120",
  };

  function parseNumber(value, label, optional = false) {
    if ((value === undefined || value === null || value === "") && optional) return null;
    const parsed = Number(String(value).replace(",", "."));
    if (!Number.isFinite(parsed)) throw new Error(`${label} debe ser un número`);
    if (parsed <= 0) throw new Error(`${label} debe ser mayor que cero`);
    return parsed;
  }

  const E12_VALUES = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82];

  function e12AtLeast(target) {
    const safeTarget = Math.max(10, Number(target) || 10);
    const exponent = Math.floor(Math.log10(safeTarget)) - 1;
    const scale = 10 ** exponent;
    const normalized = safeTarget / scale;
    const selected = E12_VALUES.find((value) => value >= normalized);
    return selected ? selected * scale : 100 * scale;
  }

  function formatResistance(ohms) {
    if (ohms >= 1000) {
      const kilo = ohms / 1000;
      return `${Number.isInteger(kilo) ? kilo : kilo.toFixed(1)} kΩ`;
    }
    return `${Math.round(ohms)} Ω`;
  }

  function isolationInputResistor(signalVoltage) {
    const targetCurrentA = 0.005;
    const ledForwardVoltage = 1.2;
    const minimumOhms = (Math.max(signalVoltage, ledForwardVoltage + 0.5) - ledForwardVoltage) / targetCurrentA;
    const ohms = e12AtLeast(minimumOhms);
    return { ohms, label: formatResistance(ohms) };
  }

  function extractRequest(text) {
    const normalized = String(text || "").toLowerCase().replace(/\s+/g, " ").trim();
    const relayPresent = /(?:^|[^a-záéíóúüñ])(?:rel[eé]|relevador)(?=$|[^a-záéíóúüñ])/i.test(normalized);
    let relayVoltage = null;
    let signalVoltage = null;

    const relayPatterns = [
      /(?:rel[eé]|relevador)(?:\s+\S+){0,3}?\s+(\d+(?:[.,]\d+)?)\s*v/i,
      /(\d+(?:[.,]\d+)?)\s*v(?:\s+\S+){0,3}?\s+(?:rel[eé]|relevador)/i,
    ];
    const signalPatterns = [
      /(?:señal|senal|gpio|salida)(?:\s+\S+){0,3}?\s+(\d+(?:[.,]\d+)?)\s*v/i,
      /(?:con|desde|usando|utilizando)\s+(?:una\s+)?(?:señal\s+)?(?:de\s+)?(\d+(?:[.,]\d+)?)\s*v/i,
    ];

    for (const pattern of relayPatterns) {
      const match = normalized.match(pattern);
      if (match) {
        relayVoltage = parseNumber(match[1], "La tensión del relé");
        break;
      }
    }
    for (const pattern of signalPatterns) {
      const match = normalized.match(pattern);
      if (match) {
        signalVoltage = parseNumber(match[1], "La tensión de control");
        break;
      }
    }

    const voltages = Array.from(
      normalized.matchAll(/(\d+(?:[.,]\d+)?)\s*v/gi),
      (match) => Number(match[1].replace(",", "."))
    );
    if (relayPresent && relayVoltage === null && voltages.length) relayVoltage = voltages[0];
    if (relayPresent && signalVoltage === null && voltages.length > 1) signalVoltage = voltages[voltages.length - 1];

    let confidence = 0.25;
    if (relayPresent) confidence += 0.35;
    if (relayVoltage !== null) confidence += 0.2;
    if (signalVoltage !== null) confidence += 0.2;
    return {
      project_type: relayPresent ? "relay_driver" : "unknown",
      relay_voltage: relayVoltage,
      signal_voltage: signalVoltage,
      confidence: Math.min(confidence, 1),
    };
  }

  function buildQuestions(extracted) {
    const questions = [];
    if (extracted.relay_voltage === null) {
      questions.push({
        id: "relay_voltage",
        label: "¿A qué tensión funciona la bobina del relé?",
        help: "Suele aparecer impreso en el relé: 5 V, 12 V o 24 V.",
        type: "number",
        unit: "V",
        required: true,
      });
    }
    if (extracted.signal_voltage === null) {
      questions.push({
        id: "signal_voltage",
        label: "¿Qué tensión tiene la señal de control?",
        help: "Por ejemplo, una salida de Arduino suele ser de 5 V.",
        type: "number",
        unit: "V",
        required: true,
      });
    }
    questions.push(
      {
        id: "controller",
        label: "¿De dónde sale la señal de control?",
        help: "Esto permite comprobar cuánta corriente puede entregar la salida.",
        type: "choice",
        options: [
          { value: "arduino", label: "Arduino o placa de 5 V" },
          { value: "micro_3v3", label: "ESP32, Raspberry Pi u otra placa de 3,3 V" },
          { value: "sensor", label: "Sensor o módulo electrónico" },
          { value: "unknown", label: "No lo sé todavía" },
        ],
        required: true,
      },
      {
        id: "coil_type",
        label: "¿La bobina del relé es de corriente continua?",
        help: "Busca “DC” o el símbolo ⎓ junto a la tensión. Este circuito está pensado para bobinas DC.",
        type: "choice",
        options: [
          { value: "dc", label: "Sí, indica DC / CC" },
          { value: "unknown", label: "No lo sé todavía" },
          { value: "ac", label: "No, indica AC / CA" },
        ],
        required: true,
      },
      {
        id: "coil_current_ma",
        label: "¿Sabes cuánto consume la bobina del relé?",
        help: "Busca “coil current” en la ficha técnica. Si no lo sabes, haremos una propuesta conservadora.",
        type: "choice",
        options: [
          { value: "unknown", label: "No lo sé" },
          { value: "40", label: "Hasta 40 mA" },
          { value: "100", label: "Entre 40 y 100 mA" },
          { value: "300", label: "Entre 100 y 300 mA" },
        ],
        required: true,
      },
      {
        id: "load_kind",
        label: "¿Qué quieres encender con el relé?",
        help: "Solo necesitamos una descripción breve, por ejemplo: lámpara de 12 V.",
        type: "text",
        placeholder: "Ej.: una lámpara de 12 V",
        required: true,
      },
      {
        id: "load_current_a",
        label: "¿Cuánta corriente consume lo que vas a encender?",
        help: "Sirve para elegir la capacidad mínima de los contactos. Puedes dejarlo sin confirmar.",
        type: "number_optional",
        unit: "A",
        placeholder: "Ej.: 2",
        required: false,
      },
      {
        id: "isolation",
        label: "¿Necesitas aislamiento eléctrico entre el control y el relé?",
        help: "Para un primer montaje de baja tensión normalmente no es necesario.",
        type: "choice",
        options: [
          { value: "no", label: "No / no estoy seguro" },
          { value: "yes", label: "Sí, quiero aislamiento" },
        ],
        required: true,
      }
    );
    return questions;
  }

  function normalizeResources(resources) {
    const components = Array.isArray(resources?.components) ? resources.components : [];
    const symbols = Array.isArray(resources?.symbols) ? resources.symbols : [];
    return {
      components,
      symbols,
      componentMeta: resources?.component_meta || {},
      symbolMeta: resources?.symbol_meta || {},
      componentsByPart: new Map(components.map((item) => [String(item.part_number || "").toUpperCase(), item])),
      symbolsById: new Map(symbols.map((item) => [item.id, item])),
    };
  }

  function chooseMosfet(resources, relayVoltage, signalVoltage, coilCurrentMa) {
    const minimumVoltage = Math.max(30, relayVoltage * 2.5);
    const minimumCurrent = Math.max(1, ((coilCurrentMa || 300) / 1000) * 4);
    const preferred = signalVoltage < 4.5
      ? ["AO3400A", "IRLZ44N", "FQP30N06L"]
      : ["IRLZ44N", "FQP30N06L", "AO3400A"];
    const candidates = resources.components.filter((item) =>
      item.category === "MOSFET"
      && /canal n/i.test(String(item.subtype || ""))
      && /l[oó]gico/i.test(String(item.subtype || ""))
      && Number(item.voltage_max_v || 0) >= minimumVoltage
      && Number(item.current_max_a || 0) >= minimumCurrent
    );
    candidates.sort((a, b) => {
      const preferredA = preferred.indexOf(String(a.part_number || "").toUpperCase());
      const preferredB = preferred.indexOf(String(b.part_number || "").toUpperCase());
      const rankA = preferredA === -1 ? 99 : preferredA;
      const rankB = preferredB === -1 ? 99 : preferredB;
      if (rankA !== rankB) return rankA - rankB;
      const throughHoleA = (a.packages || []).includes("TO-220") ? 1 : 0;
      const throughHoleB = (b.packages || []).includes("TO-220") ? 1 : 0;
      if (throughHoleA !== throughHoleB) return throughHoleB - throughHoleA;
      return Number(b.confidence || 0) - Number(a.confidence || 0);
    });
    return { candidate: candidates[0] || null, minimumVoltage, minimumCurrent };
  }

  function catalogComponent(item, ref, name, spec, extra = {}) {
    return {
      ref,
      name,
      spec,
      source_kind: "catalog",
      source_label: "BASE REAL",
      database_id: item.id,
      part_number: item.part_number,
      manufacturer: item.manufacturer,
      confidence: item.confidence,
      quality: item.quality,
      ...extra,
    };
  }

  function specificationComponent(ref, name, spec, extra = {}) {
    return {
      ref,
      name,
      spec,
      source_kind: "specification",
      source_label: "POR ELEGIR",
      ...extra,
    };
  }

  function calculatedComponent(ref, name, spec, calculation, extra = {}) {
    return {
      ref,
      name,
      spec,
      calculation,
      source_kind: "calculated",
      source_label: "CALCULADO",
      ...extra,
    };
  }

  function createCircuitModel(values, componentMap) {
    const loadNodes = [
      { id: "LOAD_COM", label: "Entrada del circuito de carga", kind: "load" },
      { id: "LOAD_NO", label: "Salida conmutada del relé", kind: "load" },
      { id: "LOAD_RETURN", label: "Retorno del circuito de carga", kind: "load" },
    ];
    const powerParts = [
      { ref: "R1", symbol_id: REQUIRED_SYMBOLS.resistor, value: "100 Ω", pins: { "1": values.isolated ? "ISO_OUT" : "CTRL_OUT", "2": "GATE" } },
      { ref: "R2", symbol_id: REQUIRED_SYMBOLS.resistor, value: "100 kΩ", pins: { "1": "GATE", "2": "GND_RELAY" } },
      {
        ref: "Q1",
        symbol_id: REQUIRED_SYMBOLS.mosfet,
        component_id: componentMap.Q1?.database_id || null,
        value: componentMap.Q1?.part_number || "MOSFET N lógico",
        pins: { G: "GATE", D: "COIL_LOW", S: "GND_RELAY" },
      },
      {
        ref: "K1",
        symbol_id: REQUIRED_SYMBOLS.relayCoil,
        value: `Bobina ${values.relay_voltage} V`,
        pins: { A1: "VRELAY_PLUS", A2: "COIL_LOW" },
      },
      {
        ref: "D1",
        symbol_id: REQUIRED_SYMBOLS.diode,
        component_id: componentMap.D1?.database_id || null,
        value: componentMap.D1?.part_number || "Diodo de rueda libre",
        pins: { K: "VRELAY_PLUS", A: "COIL_LOW" },
      },
      { ref: "PS1", symbol_id: REQUIRED_SYMBOLS.power, value: `${values.relay_voltage} V CC`, pins: { "+": "VRELAY_PLUS", "-": "GND_RELAY" } },
      { ref: "GND1", symbol_id: REQUIRED_SYMBOLS.ground, value: "0 V relé", pins: { "1": "GND_RELAY" } },
      { ref: "K1.1", symbol_id: REQUIRED_SYMBOLS.relayContact, value: "Contacto NO", pins: { COM: "LOAD_COM", NO: "LOAD_NO" } },
      { ref: "LOAD1", symbol_id: null, value: values.load_kind, pins: { "1": "LOAD_NO", "2": "LOAD_RETURN" } },
    ];
    const powerNets = [
      { id: "GATE", label: "Mando de puerta", connections: ["R1.2", "R2.1", "Q1.G"] },
      { id: "VRELAY_PLUS", label: `+${values.relay_voltage} V lado relé`, connections: values.isolated ? ["PS1.+", "K1.A1", "D1.K", "U1.C"] : ["PS1.+", "K1.A1", "D1.K"] },
      { id: "COIL_LOW", label: "Bobina / drenador", connections: ["K1.A2", "D1.A", "Q1.D"] },
      { id: "GND_RELAY", label: "0 V lado relé", connections: ["PS1.-", "Q1.S", "R2.2", "GND1.1"] },
      { id: "LOAD_COM", label: "Entrada de carga", connections: ["PORT2.IN", "K1.1.COM"] },
      { id: "LOAD_NO", label: "Salida conmutada", connections: ["K1.1.NO", "LOAD1.1"] },
      { id: "LOAD_RETURN", label: "Retorno de carga", connections: ["LOAD1.2", "PORT2.RETURN"] },
    ];

    if (!values.isolated) {
      return {
        schema_version: "0.4",
        topology: "low_side_relay_driver",
        input_contract: { current: "text", future: ["image", "hand_drawn_sketch"] },
        nodes: [
          { id: "CTRL_OUT", label: `Señal de control ${values.signal_voltage} V`, kind: "signal" },
          { id: "GATE", label: "Puerta Q1", kind: "signal" },
          { id: "VRELAY_PLUS", label: `+${values.relay_voltage} V bobina`, kind: "power" },
          { id: "COIL_LOW", label: "Retorno conmutado de bobina", kind: "power" },
          { id: "GND_RELAY", label: "0 V / masa común", kind: "reference" },
          ...loadNodes,
        ],
        parts: powerParts,
        nets: [
          { id: "CTRL_OUT", label: `Control ${values.signal_voltage} V`, connections: ["PORT1.OUT", "R1.1"] },
          ...powerNets,
        ],
      };
    }

    return {
      schema_version: "0.4",
      topology: "isolated_low_side_relay_driver",
      input_contract: { current: "text", future: ["image", "hand_drawn_sketch"] },
      nodes: [
        { id: "CTRL_OUT", label: `Señal de control ${values.signal_voltage} V`, kind: "signal" },
        { id: "CTRL_LED", label: "Entrada LED del optoacoplador", kind: "signal" },
        { id: "GND_CONTROL", label: "0 V lado control", kind: "reference" },
        { id: "ISO_OUT", label: "Salida aislada hacia la puerta", kind: "signal" },
        { id: "GATE", label: "Puerta Q1", kind: "signal" },
        { id: "VRELAY_PLUS", label: `+${values.relay_voltage} V lado relé`, kind: "power" },
        { id: "COIL_LOW", label: "Retorno conmutado de bobina", kind: "power" },
        { id: "GND_RELAY", label: "0 V lado relé", kind: "reference" },
        ...loadNodes,
      ],
      parts: [
        { ref: "R3", symbol_id: REQUIRED_SYMBOLS.resistor, value: values.isolation_input_resistor_label, pins: { "1": "CTRL_OUT", "2": "CTRL_LED" } },
        {
          ref: "U1",
          symbol_id: REQUIRED_SYMBOLS.optocoupler,
          component_id: componentMap.U1?.database_id || null,
          value: componentMap.U1?.part_number || "PC817",
          pins: { A: "CTRL_LED", K: "GND_CONTROL", C: "VRELAY_PLUS", E: "ISO_OUT" },
        },
        { ref: "GND2", symbol_id: REQUIRED_SYMBOLS.ground, value: "0 V control", pins: { "1": "GND_CONTROL" } },
        ...powerParts,
      ],
      nets: [
        { id: "CTRL_OUT", label: `Control ${values.signal_voltage} V`, connections: ["PORT1.OUT", "R3.1"] },
        { id: "CTRL_LED", label: "Corriente LED U1", connections: ["R3.2", "U1.A"] },
        { id: "GND_CONTROL", label: "0 V lado control", connections: ["U1.K", "PORT1.GND", "GND2.1"] },
        { id: "ISO_OUT", label: "Salida aislada", connections: ["U1.E", "R1.1"] },
        ...powerNets,
      ],
    };
  }

  function generateDesign(requestText, rawAnswers, rawResources) {
    const resources = normalizeResources(rawResources);
    if (!resources.components.length || !resources.symbols.length) {
      throw new Error("No se han podido cargar las bases públicas de componentes y simbología");
    }

    const extracted = extractRequest(requestText);
    const relayVoltage = parseNumber(rawAnswers.relay_voltage ?? extracted.relay_voltage, "La tensión del relé");
    const signalVoltage = parseNumber(rawAnswers.signal_voltage ?? extracted.signal_voltage, "La tensión de control");
    const loadCurrent = parseNumber(rawAnswers.load_current_a, "La corriente de la carga", true);
    const loadKind = String(rawAnswers.load_kind || "").trim();
    if (!loadKind) throw new Error("Indica qué quieres controlar con el relé");

    const controller = String(rawAnswers.controller || "unknown");
    const isolation = rawAnswers.isolation === "yes";
    const coilType = String(rawAnswers.coil_type || "unknown");
    if (coilType === "ac") {
      throw new Error("El Caso 001 solo admite relés con bobina DC/CC. Una bobina AC/CA necesita otra etapa de potencia y no debe usar este esquema.");
    }
    const coilAnswer = String(rawAnswers.coil_current_ma || "unknown");
    const coilCurrent = coilAnswer === "unknown" ? null : parseNumber(coilAnswer, "La corriente de bobina");

    const provisionalReasons = [];
    if (coilType === "unknown") provisionalReasons.push("Falta confirmar que la bobina sea de corriente continua (DC/CC).");
    if (coilCurrent === null) provisionalReasons.push("Falta confirmar el consumo real de la bobina del relé.");
    if (loadCurrent === null) provisionalReasons.push("Falta confirmar la corriente de la carga para dimensionar los contactos.");
    provisionalReasons.push("Falta la referencia exacta del relé: la base actual permite definir sus requisitos, pero no contiene un modelo de relé cualificado.");

    const contactRating = loadCurrent === null ? null : Math.max(loadCurrent * 1.5, loadCurrent + 0.5);
    const signalLabel = `${signalVoltage} V`;
    const relayLabel = `${relayVoltage} V`;
    const relayTypeLabel = coilType === "dc" ? `${relayLabel} CC` : `${relayLabel} (tipo por confirmar)`;
    const mosfetSelection = chooseMosfet(resources, relayVoltage, signalVoltage, coilCurrent);
    const mosfet = mosfetSelection.candidate;
    const diode = resources.componentsByPart.get("1N4007") || null;
    const optocoupler = isolation
      ? (resources.componentsByPart.get("PC817") || resources.componentsByPart.get("EL817") || null)
      : null;
    const isolationResistor = isolation ? isolationInputResistor(signalVoltage) : null;

    if (!mosfet) {
      provisionalReasons.push(`No hay en el catálogo un MOSFET lógico que cumpla VDS ≥ ${mosfetSelection.minimumVoltage.toFixed(0)} V e ID ≥ ${mosfetSelection.minimumCurrent.toFixed(1)} A.`);
    } else {
      provisionalReasons.push(`Q1 es candidato de catálogo, pero hay que confirmar en su ficha RDS(on) a VGS = ${signalLabel} y su patillaje real.`);
    }
    if (!diode) provisionalReasons.push("No se encontró el 1N4007 en la base pública de componentes.");
    if (isolation && !optocoupler) provisionalReasons.push("No se encontró un optoacoplador PC817/EL817 verificable en la base pública.");
    if (isolation && optocoupler) provisionalReasons.push("Confirma el patillaje y el CTR de U1 en la ficha exacta antes de montarlo.");

    const components = [];
    components.push(specificationComponent(
      "K1",
      `Relé con bobina de ${relayTypeLabel}`,
      contactRating === null
        ? "Contactos pendientes de dimensionar; bobina y patillaje por confirmar"
        : `Contactos ≥ ${contactRating.toFixed(1)} A y adecuados a la tensión y tipo de carga`,
      { symbol_id: REQUIRED_SYMBOLS.relayCoil }
    ));

    if (mosfet) {
      components.push(catalogComponent(
        mosfet,
        "Q1",
        `${mosfet.part_number} — MOSFET N de nivel lógico`,
        `VDS ${mosfet.voltage_max_v} V · ID máx. de ficha ${mosfet.current_max_a} A · RDS(on) máx. ${mosfet.rds_on_max_ohm} Ω · ${(mosfet.packages || []).join(", ")}`,
        { symbol_id: REQUIRED_SYMBOLS.mosfet, selection_note: `Elegido entre candidatos con VDS ≥ ${mosfetSelection.minimumVoltage.toFixed(0)} V.` }
      ));
    } else {
      components.push(specificationComponent(
        "Q1",
        "MOSFET N de nivel lógico",
        `VDS ≥ ${mosfetSelection.minimumVoltage.toFixed(0)} V; ID ≥ ${mosfetSelection.minimumCurrent.toFixed(1)} A; RDS(on) especificada a ${signalLabel}`,
        { symbol_id: REQUIRED_SYMBOLS.mosfet }
      ));
    }

    if (diode) {
      components.push(catalogComponent(
        diode,
        "D1",
        `${diode.part_number} — diodo de rueda libre`,
        `${diode.voltage_max_v} V · ${diode.current_max_a} A · ${(diode.packages || []).join(", ")} · banda hacia el positivo`,
        { symbol_id: REQUIRED_SYMBOLS.diode }
      ));
    } else {
      components.push(specificationComponent("D1", "Diodo de rueda libre", "IF ≥ corriente de bobina; VRRM ≥ tensión de bobina", { symbol_id: REQUIRED_SYMBOLS.diode }));
    }

    components.push(
      calculatedComponent("R1", "Resistencia de puerta 100 Ω", "¼ W, valor normalizado", "Limita el pico de corriente de carga de la puerta.", { symbol_id: REQUIRED_SYMBOLS.resistor }),
      calculatedComponent("R2", "Resistencia de 100 kΩ", "¼ W, valor normalizado", "Mantiene Q1 apagado mientras la salida de control está flotante.", { symbol_id: REQUIRED_SYMBOLS.resistor }),
      specificationComponent(
        "PS1",
        `Fuente de ${relayLabel}`,
        isolation
          ? "Debe entregar la corriente de la bobina con margen; su negativo pertenece solo al lado del relé"
          : "Debe entregar la corriente de la bobina con margen y compartir masa con el control",
        { symbol_id: REQUIRED_SYMBOLS.power }
      )
    );
    if (isolation) {
      const isolationComponents = [];
      if (optocoupler) {
        isolationComponents.push(catalogComponent(
          optocoupler,
          "U1",
          `${optocoupler.part_number} — optoacoplador de fototransistor`,
          `${(optocoupler.packages || []).join(", ")} · confirma CTR y patillaje en la ficha exacta`,
          { symbol_id: REQUIRED_SYMBOLS.optocoupler }
        ));
      } else {
        isolationComponents.push(specificationComponent(
          "U1",
          "PC817 o EL817 — optoacoplador",
          "Fototransistor, encapsulado DIP-4; confirma CTR y patillaje",
          { symbol_id: REQUIRED_SYMBOLS.optocoupler }
        ));
      }
      isolationComponents.push(calculatedComponent(
        "R3",
        `Resistencia de entrada ${isolationResistor.label}`,
        "¼ W, valor normalizado",
        "Limita la corriente del LED de U1.",
        { symbol_id: REQUIRED_SYMBOLS.resistor }
      ));
      components.splice(2, 0, ...isolationComponents);
    }

    const componentMap = Object.fromEntries(components.map((item) => [item.ref, item]));
    const circuitModel = createCircuitModel({
      relay_voltage: relayVoltage,
      signal_voltage: signalVoltage,
      isolated: isolation,
      isolation_input_resistor_label: isolationResistor?.label || null,
      load_kind: loadKind,
    }, componentMap);

    const symbolIds = [...new Set(circuitModel.parts.map((part) => part.symbol_id).filter(Boolean))];
    const symbolManifest = symbolIds.map((id) => {
      const symbol = resources.symbolsById.get(id);
      return symbol ? {
        id: symbol.id,
        name: symbol.nombre,
        standard: symbol.norma,
        asset: `../${symbol.archivo_svg}`,
      } : { id, name: "Símbolo no encontrado", standard: "", asset: null };
    });
    const missingSymbols = symbolManifest.filter((item) => !item.asset);
    if (missingSymbols.length) {
      provisionalReasons.push(`Faltan ${missingSymbols.length} símbolos requeridos en la biblioteca pública.`);
    }

    const connections = isolation ? [
      `Lado de control: lleva la señal de ${signalLabel} a R3 (${isolationResistor.label}) y de R3 al ánodo A de U1.`,
      "Lado de control: conecta el cátodo K de U1 al 0 V del controlador.",
      `Lado del relé: conecta +${relayLabel} a K1.A1, al cátodo de D1 y al colector C de U1.`,
      "Lado del relé: conecta el emisor E de U1 a R1 y desde R1 a la puerta G de Q1.",
      "Conecta R2 entre la puerta G de Q1 y el negativo de la fuente del relé.",
      "Conecta K1.A2 al ánodo de D1 y al drenador D de Q1; conecta la fuente S de Q1 al negativo del relé.",
      "Mantén separadas las dos masas: no unas el 0 V del control con el negativo de la fuente del relé.",
      "Cablea la carga únicamente en COM y NO/NC de K1, nunca en los terminales de bobina A1/A2.",
    ] : [
      `Conecta +${relayLabel} a K1.A1 y al cátodo de D1 (el lado de la banda).`,
      "Conecta K1.A2 al ánodo de D1 y al drenador D de Q1.",
      "Conecta la fuente S de Q1 al negativo de la alimentación.",
      `Lleva la señal de ${signalLabel} a R1 y desde R1 a la puerta G de Q1.`,
      "Conecta R2 entre la puerta G de Q1 y masa.",
      "Une la masa del controlador con el negativo de la fuente del relé.",
      "Cablea la carga únicamente en COM y NO/NC de K1, nunca en los terminales de bobina A1/A2.",
    ];

    const warnings = [
      "No conectes la bobina del relé directamente a un pin del microcontrolador.",
      "Comprueba el patillaje real del MOSFET y del relé antes de cablear: el símbolo no fija el orden físico de las patas.",
      "Los valores máximos de catálogo no equivalen a condiciones de uso; revisa temperatura, disipación y tensión de puerta.",
    ];
    if (coilType === "unknown") warnings.unshift("No montes D1 hasta comprobar que la bobina está marcada como DC o CC.");
    if (isolation) warnings.unshift("No unas las masas de control y relé: hacerlo anula el aislamiento eléctrico.");
    if (["230", "220", "red", "enchufe", "mains", "ac"].some((term) => loadKind.toLowerCase().includes(term))) {
      warnings.unshift("La carga parece usar tensión de red. No montes esa parte en protoboard; requiere caja, fusible, distancias de seguridad y revisión profesional.");
    }

    if (controller === "micro_3v3" && signalVoltage > 3.6) {
      warnings.unshift("La placa indicada suele trabajar a 3,3 V; confirma que la salida realmente alcanza la tensión introducida.");
    }

    const componentCount = Number(resources.componentMeta?.counts?.components || resources.components.length);
    const symbolCount = Number(resources.symbolMeta?.count || resources.symbols.length);
    return {
      status: provisionalReasons.length ? "provisional" : "ready",
      title: `${isolation ? "Driver aislado" : "Driver"} para relé de ${relayTypeLabel} controlado con ${signalLabel}`,
      summary: isolation
        ? `Control y relé separados eléctricamente para accionar ${loadKind}.`
        : `Etapa de control para accionar ${loadKind}, seleccionada contra las bases públicas de Super Técnico.`,
      values: {
        relay_voltage: relayVoltage,
        signal_voltage: signalVoltage,
        coil_current_ma: coilCurrent,
        coil_type: coilType,
        load_current_a: loadCurrent,
        contact_rating_a: contactRating,
        isolated: isolation,
        isolation_input_resistor: isolationResistor?.label || null,
      },
      components,
      connections,
      warnings,
      provisional_reasons: [...new Set(provisionalReasons)],
      circuit_model: circuitModel,
      symbol_manifest: symbolManifest,
      database: {
        component_records: componentCount,
        component_version: resources.componentMeta?.data_version || "sin versión",
        symbol_records: symbolCount,
        symbol_version: resources.symbolMeta?.version || "sin versión",
        selected_catalog_components: components.filter((item) => item.source_kind === "catalog").length,
        calculated_values: components.filter((item) => item.source_kind === "calculated").length,
        pending_specifications: components.filter((item) => item.source_kind === "specification").length,
      },
    };
  }

  function callTool(name, rawArguments, resources) {
    const tool = String(name || "");
    const args = rawArguments && typeof rawArguments === "object" ? rawArguments : {};

    if (tool === "electroia_analyze_request") {
      const request = String(args.request || "").trim();
      if (request.length < 8) throw new Error("Cuéntame un poco más sobre lo que quieres construir");
      const extracted = extractRequest(request);
      if (extracted.project_type !== "relay_driver") {
        throw new Error("Esta versión de ElectroIA admite por ahora el controlador de relé DC.");
      }
      return {
        ok: true,
        tool,
        provider_neutral: true,
        extracted,
        questions: buildQuestions(extracted),
      };
    }

    if (tool === "electroia_generate_relay_driver") {
      const relayVoltage = args.relay_voltage;
      const signalVoltage = args.signal_voltage;
      const request = String(args.request || `Controlar un relé de ${relayVoltage} V con una señal de ${signalVoltage} V.`);
      const answers = {
        relay_voltage: relayVoltage,
        signal_voltage: signalVoltage,
        controller: args.controller,
        coil_type: args.coil_type,
        coil_current_ma: args.coil_current_ma ?? "unknown",
        load_kind: args.load_kind,
        load_current_a: args.load_current_a ?? "",
        isolation: args.isolation === true || args.isolation === "yes" ? "yes" : "no",
      };
      return {
        ok: true,
        tool,
        provider_neutral: true,
        source: args.source || { kind: "text" },
        design: generateDesign(request, answers, resources || {}),
      };
    }

    throw new Error(`Herramienta desconocida: ${tool}`);
  }

  return {
    analyze(requestText) {
      const request = String(requestText || "").trim();
      if (request.length < 8) throw new Error("Cuéntame un poco más sobre lo que quieres construir");
      const extracted = extractRequest(request);
      if (extracted.project_type !== "relay_driver") {
        throw new Error("Este primer prototipo todavía está aprendiendo. Prueba con una petición sobre controlar un relé.");
      }
      return { ok: true, extracted, questions: buildQuestions(extracted) };
    },
    design(requestText, answers, resources) {
      return { ok: true, design: generateDesign(String(requestText || ""), answers || {}, resources || {}) };
    },
    callTool,
    buildQuestions,
    extractRequest,
  };
})();

if (typeof globalThis !== "undefined") globalThis.ElectroEngine = ElectroEngine;
if (typeof module !== "undefined" && module.exports) module.exports = ElectroEngine;
