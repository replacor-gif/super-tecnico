const state = {
  request: "",
  extracted: null,
  questions: [],
  index: 0,
  answers: {},
  resourcesPromise: null,
  accessReady: false,
  auditLoaded: false,
};

const $ = (selector) => document.querySelector(selector);
const views = [$("#introView"), $("#questionsView"), $("#resultView")];
const PRIVATE_API_URL = new URL("../api/index.php", document.baseURI);

function showView(view) {
  views.forEach((item) => item.classList.toggle("active", item === view));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setLoading(visible, message = "Validando redes y trazando el plano…") {
  $("#loadingOverlay").classList.toggle("visible", visible);
  $("#loadingOverlay").setAttribute("aria-hidden", String(!visible));
  $("#loadingOverlay p").textContent = message;
}

async function fetchJson(url, label) {
  const response = await fetch(url, { cache: "force-cache" });
  if (!response.ok) throw new Error(`No se ha podido cargar ${label} (${response.status})`);
  return response.json();
}

function clientToken() {
  try {
    const key = "st-electroia-client";
    const existing = window.localStorage.getItem(key);
    if (existing) return existing;
    const created = window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    window.localStorage.setItem(key, created);
    return created;
  } catch (_error) {
    return "private-lab";
  }
}

function setToolMode() {
  $("#engineStatus").classList.remove("ai");
  $("#engineStatus").classList.add("local");
  $("#engineStatusLabel").textContent = "Motor gráfico neutral";
  $("#privacyStatus").lastChild.textContent = " Motor gráfico local · sin IA integrada";
}

function enterPrivateLab() {
  if (state.accessReady) return;
  state.accessReady = true;
  document.body.classList.remove("access-checking");
  $("#pinGate").hidden = true;
  setToolMode();
  loadEngineAudit();
}

async function loadEngineAudit() {
  if (state.auditLoaded) return;
  state.auditLoaded = true;
  try {
    const [report, release] = await Promise.all([
      fetchJson("../data/electroia/engine-audit-report.json", "la auditoría del motor"),
      fetchJson("../data/electroia/public-release-readiness.json", "el estado de publicación"),
    ]);
    const summary = report.summary || {};
    const releaseSummary = release.summary || {};
    const gatesPass = report.status === "pass" && releaseSummary.automated_gates_pass === true;
    $("#engineAuditHeadline").textContent = gatesPass
      ? `Candidata privada · ${releaseSummary.professional_examples || 0} planos sin conflictos`
      : "La auditoría necesita revisión";
    const limitations = (report.known_limitations || []).map((item) => `<li><b>${escapeHtml(item.message)}</b></li>`).join("");
    const blockers = (release.manual_release_blockers || []).map((item) => `<li><b>${escapeHtml(item.exit_criteria)}</b></li>`).join("");
    $("#engineAuditContent").innerHTML = `<div class="engine-audit-metrics">
      <span><b>${Number(summary.public_symbols || 0)}</b> símbolos públicos</span>
      <span><b>${Number(releaseSummary.professional_examples || 0)}</b> planos patrón</span>
      <span><b>${Number(releaseSummary.component_overlaps || 0)}</b> solapes</span>
      <span><b>${Number(releaseSummary.wire_component_conflicts || 0)}</b> cables sobre símbolos</span>
    </div><p>Puertas automáticas: <strong>${gatesPass ? "superadas" : "pendientes"}</strong>. El motor seguirá privado hasta completar:</p><ul>${blockers}</ul><p>Límites técnicos declarados:</p><ul>${limitations}</ul>`;
  } catch (_error) {
    $("#engineAuditHeadline").textContent = "Auditoría no disponible";
    $("#engineAuditContent").innerHTML = "<p>No se ha podido cargar el informe. El motor sigue disponible, pero el estado no se puede confirmar.</p>";
  }
}

function showPinGate(message = "") {
  document.body.classList.remove("access-checking");
  $("#pinGate").hidden = false;
  $("#pinError").textContent = message;
  window.setTimeout(() => $("#pinInput").focus(), 50);
}

async function initializeAccess() {
  const url = new URL(PRIVATE_API_URL);
  url.searchParams.set("action", "electroia-access");
  try {
    const response = await fetch(url, { cache: "no-store", credentials: "same-origin" });
    if (response.status === 404) {
      enterPrivateLab();
      return;
    }
    const data = response.ok ? await response.json() : null;
    if (!data?.ok) throw new Error("access_check_failed");
    if (data.required && !data.unlocked) showPinGate();
    else enterPrivateLab();
  } catch (_error) {
    showPinGate("No se ha podido comprobar el acceso. Inténtalo de nuevo en unos segundos.");
  }
}

$("#pinForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const pin = $("#pinInput").value.trim();
  $("#pinError").textContent = "";
  const button = $("#pinForm button");
  button.disabled = true;
  try {
    const url = new URL(PRIVATE_API_URL);
    url.searchParams.set("action", "electroia-unlock");
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: { "Content-Type": "application/json", "X-ST-Client": clientToken() },
      body: JSON.stringify({ pin, client_token: clientToken() }),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok || !data?.unlocked) {
      showPinGate(response.status === 429 ? "Demasiados intentos. Espera unos minutos." : "PIN incorrecto.");
      return;
    }
    $("#pinInput").value = "";
    enterPrivateLab();
  } catch (_error) {
    showPinGate("No se ha podido comprobar el PIN.");
  } finally {
    button.disabled = false;
  }
});

function loadDesignResources() {
  if (!state.resourcesPromise) {
    state.resourcesPromise = Promise.all([
      fetchJson("../data/components/catalog.json", "la base de componentes"),
      fetchJson("../data/symbols/catalog.json", "la base de simbología"),
    ]).then(([componentCatalog, symbolCatalog]) => {
      if (!Array.isArray(componentCatalog.components) || !Array.isArray(symbolCatalog.symbols)) {
        throw new Error("Las bases públicas no tienen el formato esperado");
      }
      return {
        components: componentCatalog.components,
        component_meta: componentCatalog.meta || {},
        symbols: symbolCatalog.symbols,
        symbol_meta: {
          version: symbolCatalog.version,
          count: symbolCatalog.count,
          generated_from: symbolCatalog.generated_from,
        },
      };
    }).catch((error) => {
      state.resourcesPromise = null;
      throw error;
    });
  }
  return state.resourcesPromise;
}

async function api(path, body) {
  await new Promise((resolve) => window.setTimeout(resolve, 180));
  if (typeof ElectroEngine === "undefined") throw new Error("El motor de diseño no está disponible");
  if (path === "/api/analyze") {
    return {
      ...ElectroEngine.callTool("electroia_analyze_request", { request: body.request }),
      can_design: true,
    };
  }
  if (path === "/api/design") {
    const resources = await loadDesignResources();
    const extracted = ElectroEngine.extractRequest(body.request);
    if (extracted.project_type === "temperature_fan_controller") {
      return ElectroEngine.callTool("electroia_generate_temperature_fan", {
        request: body.request,
        fan_voltage: body.answers.fan_voltage ?? extracted.fan_voltage,
        fan_current_a: body.answers.fan_current_a === "unknown" ? null : Number(body.answers.fan_current_a),
        turn_on_temperature_c: body.answers.turn_on_temperature_c ?? extracted.turn_on_temperature_c,
        hysteresis_c: Number(body.answers.hysteresis_c),
        fan_type: body.answers.fan_type,
        source: { kind: "text" },
      }, resources);
    }
    return ElectroEngine.callTool("electroia_generate_relay_driver", {
      request: body.request,
      relay_voltage: body.answers.relay_voltage ?? extracted.relay_voltage,
      signal_voltage: body.answers.signal_voltage ?? extracted.signal_voltage,
      controller: body.answers.controller,
      coil_type: body.answers.coil_type,
      coil_current_ma: body.answers.coil_current_ma === "unknown" ? null : Number(body.answers.coil_current_ma),
      load_kind: body.answers.load_kind,
      load_current_a: body.answers.load_current_a ? Number(body.answers.load_current_a) : null,
      isolation: body.answers.isolation === "yes",
      source: { kind: "text" },
    }, resources);
  }
  throw new Error("Operación desconocida");
}

$("#requestForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const request = $("#requestInput").value.trim();
  setLoading(true);
  try {
    const data = await api("/api/analyze", { request });
    if (data.can_design === false) {
      throw new Error("Esta petición todavía no pertenece a uno de los circuitos disponibles.");
    }
    state.request = request;
    state.extracted = data.extracted;
    state.questions = data.questions;
    state.answers = {};
    state.index = 0;
    $("#requestSummary").textContent = `“${request}”`;
    const bits = [];
    if (data.extracted.relay_voltage) bits.push(`bobina de ${data.extracted.relay_voltage} V`);
    if (data.extracted.signal_voltage) bits.push(`control de ${data.extracted.signal_voltage} V`);
    if (data.extracted.fan_voltage) bits.push(`ventilador de ${data.extracted.fan_voltage} V`);
    if (data.extracted.turn_on_temperature_c) bits.push(`encendido a ${data.extracted.turn_on_temperature_c} °C`);
    $("#detectedText").textContent = bits.length
      ? bits.join(" · ")
      : data.extracted.project_type === "temperature_fan_controller" ? "Control térmico detectado" : "Relé detectado";
    renderQuestion();
    showView($("#questionsView"));
  } catch (error) {
    alert(error.message);
  } finally {
    setLoading(false);
  }
});

$("#requestInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    $("#requestForm").requestSubmit();
  }
});

document.querySelectorAll(".example").forEach((button) => {
  button.addEventListener("click", async () => {
    if (button.dataset.diagramExample) {
      setLoading(true, "Validando el esquema patrón y trazando potencia y mando…");
      try {
        const document = await fetchJson(button.dataset.diagramExample, "el esquema patrón");
        renderPublicResult(publicDesignFromDiagramDocument(document));
        showView($("#resultView"));
      } catch (error) {
        alert(error.message);
      } finally {
        setLoading(false);
      }
      return;
    }
    $("#requestInput").value = button.dataset.request || button.textContent.trim();
    $("#requestInput").focus();
  });
});

function publicDesignFromDiagramDocument(document) {
  if (typeof ElectroDiagramCore === "undefined") throw new Error("El registro normalizado no está disponible");
  const registry = new Map(ElectroDiagramCore.getRegistry().symbols.map((symbol) => [symbol.id, symbol]));
  const singleLine = document.document_kind === "single_line_diagram";
  const summaries = {
    "ELECTROIA-DOL-001": "Esquema patrón de arranque directo con potencia, mando, enclavamiento, parada de emergencia y protección térmica en una sola hoja.",
    "ELECTROIA-DB-001": "Esquema patrón unifilar con alimentación, contador, protección general, diferencial y circuitos derivados en una sola hoja.",
    "ELECTROIA-PLC-VFD-001": "Arquitectura patrón de automatización con alimentación trifásica, PLC, seguridad, variador, motor y comunicaciones industriales.",
    "ELECTROIA-ARDUINO-IND-001": "Interfaz patrón para integrar una plataforma Arduino con alimentación, protección y señales de campo industriales.",
    "ELECTROIA-BMS-AHU-001": "Arquitectura patrón de control de climatizador mediante BMS, sensores, actuadores y red de edificio.",
  };
  return {
    title: document.title,
    summary: summaries[document.document_id] || (singleLine
      ? "Esquema patrón unifilar trazado sobre una única rejilla normalizada."
      : "Esquema patrón multifilar trazado sobre una única rejilla normalizada."),
    status: "provisional",
    components: document.components.map((component) => {
      const symbol = registry.get(component.symbol_id);
      return {
        ref: component.display_ref || component.ref,
        name: symbol?.name || component.symbol_id,
        spec: component.value || "Símbolo normalizado sobre rejilla de 50 mil",
        source_kind: "normalized_symbol",
      };
    }),
    connections: document.nets.map((net) => `${net.label || net.id}: ${net.connections.join(" · ")}`),
    warnings: [
      "Es un patrón gráfico: la IA o el proyectista debe aportar tensiones, secciones, calibres, protecciones y referencias reales.",
      "Antes del montaje deben verificarse el modelo exacto, los datos de placa, las protecciones, la coordinación y la normativa aplicable.",
    ],
    circuit_model: {
      schema_version: "1.0",
      topology: singleLine ? "residential_distribution_single_line" : "direct_on_line_motor_starter",
    },
    diagram_document: document,
  };
}

function renderQuestion() {
  const question = state.questions[state.index];
  const total = state.questions.length;
  $("#progressText").textContent = `Pregunta ${state.index + 1} de ${total}`;
  $("#progressBar").style.width = `${((state.index + 1) / total) * 100}%`;
  $("#previousQuestion").style.visibility = state.index === 0 ? "hidden" : "visible";
  $("#nextQuestion").innerHTML = state.index === total - 1 ? "Generar circuito <span>→</span>" : "Siguiente <span>→</span>";
  $("#questionError").textContent = "";

  const card = document.createElement("div");
  card.className = "question-card";
  card.innerHTML = `
    <div class="question-number">${String(state.index + 1).padStart(2, "0")}</div>
    <h2>${escapeHtml(question.label)}</h2>
    <p class="question-help">${escapeHtml(question.help || "")}</p>
  `;

  if (question.type === "choice") {
    const choices = document.createElement("div");
    choices.className = "choices";
    question.options.forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `choice${state.answers[question.id] === option.value ? " selected" : ""}`;
      button.textContent = option.label;
      button.dataset.value = option.value;
      button.addEventListener("click", () => {
        state.answers[question.id] = option.value;
        choices.querySelectorAll(".choice").forEach((item) => item.classList.toggle("selected", item === button));
        $("#questionError").textContent = "";
      });
      choices.appendChild(button);
    });
    card.appendChild(choices);
  } else {
    const field = document.createElement("div");
    field.className = `field-wrap${question.type === "text" ? " text-field" : ""}`;
    const input = document.createElement("input");
    input.id = `answer-${question.id}`;
    input.type = question.type.startsWith("number") ? "number" : "text";
    input.step = "any";
    input.min = question.type.startsWith("number") ? "0" : "";
    input.placeholder = question.placeholder || "";
    input.value = state.answers[question.id] || "";
    input.addEventListener("input", () => {
      state.answers[question.id] = input.value;
      $("#questionError").textContent = "";
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        $("#nextQuestion").click();
      }
    });
    field.appendChild(input);
    if (question.unit) {
      const unit = document.createElement("span");
      unit.textContent = question.unit;
      field.appendChild(unit);
    }
    card.appendChild(field);
    setTimeout(() => input.focus(), 50);
  }

  $("#questionMount").replaceChildren(card);
}

function currentAnswerIsValid() {
  const question = state.questions[state.index];
  const value = state.answers[question.id];
  if (!question.required && (value === undefined || value === "")) return true;
  if (value === undefined || String(value).trim() === "") {
    $("#questionError").textContent = "Necesito esta respuesta para continuar.";
    return false;
  }
  if (question.type.startsWith("number") && Number(value) <= 0) {
    $("#questionError").textContent = "Introduce un valor mayor que cero.";
    return false;
  }
  return true;
}

$("#nextQuestion").addEventListener("click", async () => {
  if (!currentAnswerIsValid()) return;
  if (state.index < state.questions.length - 1) {
    state.index += 1;
    renderQuestion();
    return;
  }

  setLoading(true, "Preparando el documento y trazando el plano…");
  try {
    const data = await api("/api/design", { request: state.request, answers: state.answers });
    renderPublicResult(data.design);
    showView($("#resultView"));
  } catch (error) {
    $("#questionError").textContent = error.message;
  } finally {
    setLoading(false);
  }
});

$("#previousQuestion").addEventListener("click", () => {
  if (state.index > 0) {
    state.index -= 1;
    renderQuestion();
  }
});

$("#backToIntro").addEventListener("click", () => showView($("#introView")));
$("#startOver").addEventListener("click", () => {
  state.index = 0;
  state.answers = {};
  showView($("#introView"));
  $("#requestInput").focus();
});

function renderPublicResult(design) {
  $("#designTitle").textContent = design.title;
  $("#designSummary").textContent = design.summary;

  let validation = null;
  let relevantWarnings = [];
  if (design.diagram_document && typeof ElectroDiagramCore !== "undefined") {
    validation = ElectroDiagramCore.validate(design.diagram_document);
    if (!validation.valid) {
      throw new Error(`El documento no supera la validación: ${validation.errors.map((item) => item.message).join(" ")}`);
    }
    relevantWarnings = validation.warnings.filter((item) => ["EXACT_MODEL_REQUIRED", "OUTPUT_CONTENTION", "EARTH_DOMAIN_MIX", "SIGNAL_POWER_DOMAIN_MIX", "NET_ROLE_MISMATCH"].includes(item.code));
    design.warnings = [...new Set([...(design.warnings || []), ...relevantWarnings.map((item) => item.message)])];
  }

  const banner = $("#statusBanner");
  banner.className = `status-banner ${design.status}`;
  const validationText = validation ? ` Validación: 0 errores · ${relevantWarnings.length} avisos relevantes.` : "";
  banner.innerHTML = design.status === "ready"
    ? `<b>Circuito preparado.</b> Revisa las conexiones antes de montarlo.${validationText}`
    : `<b>Esquema generado.</b> Confirma las piezas marcadas como «por confirmar» antes de montarlo.${validationText}`;

  $("#componentsList").innerHTML = design.components.map((item) => {
    const pending = item.source_kind === "specification"
      ? '<em class="result-status">Por confirmar</em>'
      : "";
    return `
      <div class="component">
        <span class="component-ref">${escapeHtml(item.ref)}</span>
        <div class="component-name"><b>${escapeHtml(item.name)}</b>${pending}</div>
        <small>${escapeHtml(item.spec)}</small>
      </div>
    `;
  }).join("");
  $("#connectionsList").innerHTML = design.connections.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  $("#warningsList").innerHTML = design.warnings.map((item) => `<li>${escapeHtml(item)}</li>`).join("");

  if (typeof ElectroDiagram === "undefined") throw new Error("El generador de esquemas no está disponible");
  const schematic = ElectroDiagram.render(design);
  $("#schematic").innerHTML = schematic;
  $("#expandedSchematic").innerHTML = schematic;
}

$("#expandDiagram").addEventListener("click", () => $("#diagramDialog").showModal());
$("#closeDiagram").addEventListener("click", () => $("#diagramDialog").close());
$("#diagramDialog").addEventListener("click", (event) => {
  if (event.target === $("#diagramDialog")) $("#diagramDialog").close();
});

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

initializeAccess();
