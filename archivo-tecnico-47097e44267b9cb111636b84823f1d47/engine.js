const ElectroEngine = (function () {
  "use strict";

  function parseNumber(value, label, optional = false) {
    if ((value === undefined || value === null || value === "") && optional) return null;
    const parsed = Number(String(value).replace(",", "."));
    if (!Number.isFinite(parsed)) throw new Error(`${label} debe ser un número`);
    if (parsed <= 0) throw new Error(`${label} debe ser mayor que cero`);
    return parsed;
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

    const voltages = Array.from(normalized.matchAll(/(\d+(?:[.,]\d+)?)\s*v/gi), (match) => Number(match[1].replace(",", ".")));
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

  function generateDesign(requestText, rawAnswers) {
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

    const contactRating = loadCurrent === null ? null : Math.max(loadCurrent * 1.5, loadCurrent + 0.5);
    const signalLabel = `${signalVoltage} V`;
    const relayLabel = `${relayVoltage} V`;
    const relayTypeLabel = coilType === "dc" ? `${relayLabel} CC` : `${relayLabel} (tipo por confirmar)`;
    const driverName = isolation ? "Módulo optoacoplado con MOSFET de nivel lógico" : "MOSFET N de nivel lógico";
    const topology = isolation
      ? "Control aislado con optoacoplador y MOSFET en el lado de la bobina"
      : "Conmutación por el lado negativo con MOSFET y masa común";

    const components = [
      {
        ref: "K1",
        name: `Relé con bobina de ${relayTypeLabel}`,
        spec: contactRating === null
          ? "Capacidad de contactos pendiente de confirmar"
          : `Contactos ≥ ${contactRating.toFixed(1)} A y adecuados a la tensión de la carga`,
      },
      { ref: "Q1", name: driverName, spec: "VDS ≥ 30 V; RDS(on) especificada con la tensión de control disponible" },
      { ref: "D1", name: "Diodo de rueda libre 1N4007", spec: "En paralelo con la bobina; banda hacia el positivo" },
      { ref: "R1", name: "Resistencia de puerta 100 Ω", spec: "Entre la señal y la puerta del MOSFET" },
      { ref: "R2", name: "Resistencia de 100 kΩ", spec: "Entre puerta y masa para mantener el relé apagado al arrancar" },
      { ref: "PS1", name: `Fuente de ${relayLabel}`, spec: "Debe poder entregar la corriente de la bobina con margen" },
    ];
    if (isolation) components.splice(2, 0, { ref: "U1", name: "Optoacoplador", spec: "Con resistencia de entrada calculada para la señal de control" });

    const connections = [
      `Conecta el positivo de la fuente de ${relayLabel} a un extremo de la bobina K1.`,
      "Conecta el otro extremo de la bobina al drenador de Q1.",
      "Conecta la fuente de Q1 al negativo de la alimentación del relé.",
      isolation
        ? `Lleva la señal de ${signalLabel} a la entrada del optoacoplador; su salida gobierna Q1.`
        : `Lleva la señal de ${signalLabel} a la puerta de Q1 a través de R1.`,
      "Coloca R2 entre la puerta de Q1 y masa.",
      "Coloca D1 en paralelo con la bobina, con la banda del diodo hacia el positivo.",
    ];
    if (!isolation) connections.push("Une la masa del controlador con el negativo de la fuente del relé.");

    const warnings = [
      "No conectes la bobina del relé directamente a un pin del microcontrolador.",
      "Comprueba el patillaje real del MOSFET y del relé antes de cablear.",
      "Los contactos del relé y la bobina son circuitos distintos: no confundas sus terminales.",
    ];
    if (coilType === "unknown") warnings.unshift("No montes D1 hasta comprobar que la bobina está marcada como DC o CC.");
    if (["230", "220", "red", "enchufe", "mains", "ac"].some((term) => loadKind.toLowerCase().includes(term))) {
      warnings.unshift("La carga parece usar tensión de red. No montes esa parte en protoboard; requiere caja, fusible, distancias de seguridad y revisión profesional.");
    }

    const decisions = [
      `La bobina necesita ${relayLabel}, pero la orden solo entrega ${signalLabel}; se añade una etapa de potencia.`,
      `Topología elegida: ${topology}.`,
      "El diodo D1 absorbe el pico de tensión que produce la bobina al apagarse.",
    ];
    if (controller === "micro_3v3" && signalVoltage > 3.6) {
      decisions.push("La placa indicada suele trabajar a 3,3 V; conviene confirmar que la señal realmente alcanza la tensión introducida.");
    }

    return {
      status: provisionalReasons.length ? "provisional" : "ready",
      title: `Driver para relé de ${relayTypeLabel} controlado con ${signalLabel}`,
      summary: `Etapa de control para accionar ${loadKind} sin exigir corriente de bobina a la salida de control.`,
      values: {
        relay_voltage: relayVoltage,
        signal_voltage: signalVoltage,
        coil_current_ma: coilCurrent,
        coil_type: coilType,
        load_current_a: loadCurrent,
        contact_rating_a: contactRating,
        isolated: isolation,
      },
      components,
      connections,
      warnings,
      decisions,
      provisional_reasons: provisionalReasons,
    };
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
    design(requestText, answers) {
      return { ok: true, design: generateDesign(String(requestText || ""), answers || {}) };
    },
    extractRequest,
  };
})();
