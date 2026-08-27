const state = {
  request: "",
  extracted: null,
  questions: [],
  index: 0,
  answers: {},
  resourcesPromise: null,
  accessReady: false,
  auditLoaded: false,
  currentDesign: null,
  currentCaseKey: "",
  currentValidation: { errors: 0, warnings: 0 },
  validationSummary: null,
  activeWorkspace: "quick",
  bridgeDiagnostics: null,
  bridgeResolution: null,
  benchmarkCatalog: null,
  layoutEditMode: false,
  selectedComponentRef: "",
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

function setWorkspace(name) {
  const available = new Set(["quick", "bridge", "integration"]);
  const selected = available.has(name) ? name : "quick";
  state.activeWorkspace = selected;
  document.querySelectorAll("[data-workspace]").forEach((button) => {
    const active = button.dataset.workspace === selected;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll("[data-workspace-panel]").forEach((panel) => {
    const active = panel.dataset.workspacePanel === selected;
    panel.hidden = !active;
    panel.classList.toggle("is-active", active);
  });
}

document.querySelectorAll("[data-workspace]").forEach((button) => {
  button.addEventListener("click", () => setWorkspace(button.dataset.workspace));
});

async function copyText(value) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const field = document.createElement("textarea");
  field.value = value;
  field.style.position = "fixed";
  field.style.opacity = "0";
  document.body.append(field);
  field.select();
  document.execCommand("copy");
  field.remove();
}

function electroiaPublicUrl(relative) {
  return new URL(relative, document.baseURI).href;
}

function buildAiBrief() {
  const request = $("#aiBriefRequest").value.trim();
  if (request.length < 8) throw new Error("Describe con algo más de detalle qué instalación o circuito necesitas.");
  return {
    schema_version: "1.0",
    kind: "electroia_design_brief",
    language: "es",
    request,
    objective: "Diseñar y calcular el circuito, seleccionar componentes y devolver una especificación de alto nivel que ElectroIA resuelva, valide y dibuje.",
    responsibility_boundary: {
      ai: "Interpreta la necesidad, pregunta los datos imprescindibles, realiza los cálculos, selecciona componentes y define todas las redes.",
      electroia: "Resuelve nombres de símbolos y terminales, valida el contrato, separa dominios, enruta sobre la rejilla y genera el plano SVG.",
    },
    resources: {
      status: electroiaPublicUrl("../api/index.php?action=electroia-public-status"),
      symbol_search: electroiaPublicUrl("../api/index.php?action=electroia-symbol-search&q={query}"),
      manifest: electroiaPublicUrl("../data/electroia/tool-manifest.json"),
      schema: electroiaPublicUrl("../data/electroia/diagram-spec.schema.json"),
      profiles: electroiaPublicUrl("../data/electroia/document-profiles.json"),
    },
    mandatory_process: [
      "No inventes terminales ni pinouts.",
      "Puedes indicar symbol_query con un nombre técnico claro; ElectroIA resolverá el symbol_id revisado.",
      "Si un bloque exige modelo exacto, pide fabricante, referencia y documentación.",
      "Separa los cálculos y decisiones técnicas del documento gráfico.",
      "Usa identificadores cortos en components[].id y referencia las redes con {component, port}.",
      "Devuelve solo un objeto JSON válido, sin Markdown ni explicaciones alrededor.",
    ],
    expected_output: {
      title: "Nombre del plano",
      accepted_document_kinds: ["circuit_diagram", "single_line_diagram", "multi_line_diagram"],
      required_fields: ["title", "components", "nets"],
      component_example: { id: "power_supply", symbol_query: "fuente industrial 24 VDC", value: "24 VDC" },
      connection_example: { component: "power_supply", port: "positive" },
    },
  };
}

function aiBriefAsPrompt(brief) {
  return [
    "Actúa como la inteligencia de diseño que alimenta el motor gráfico ElectroIA.",
    "Lee el siguiente encargo y sigue literalmente sus límites y recursos.",
    "Antes de responder, resuelve los datos técnicos que falten o pregunta solo lo imprescindible.",
    "Tu respuesta final debe contener únicamente el documento JSON que valida contra el esquema indicado.",
    "",
    JSON.stringify(brief, null, 2),
  ].join("\n");
}

function setBriefMessage(message, kind = "") {
  const status = $("#aiBriefStatus");
  status.textContent = message;
  status.className = `bridge-message${kind ? ` is-${kind}` : ""}`;
}

function setBridgeStatus(kind, title, message, details = []) {
  const status = $("#aiBridgeStatus");
  status.className = `bridge-status is-${kind}`;
  status.innerHTML = `<span>${escapeHtml(title)}</span><p>${escapeHtml(message)}</p>${details.length ? `<ul>${details.slice(0, 8).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}`;
}

function looksLikeHighLevelSpec(value) {
  return Boolean(value && Array.isArray(value.components) && value.components.length
    && value.components.every((component) => component && component.id && (component.symbol_id || component.symbol_query)));
}

function looksLikeDiagramDocument(value) {
  return Boolean(value && Array.isArray(value.components) && Array.isArray(value.nets)
    && value.components.every((component) => component && component.ref && component.symbol_id));
}

function extractDiagramInput(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const specCandidates = [
    value.spec,
    value.diagram_spec,
    value.structuredContent?.spec,
    value.structuredContent?.diagram_spec,
    value.result?.spec,
    value.result?.diagram_spec,
    value,
  ];
  const spec = specCandidates.find(looksLikeHighLevelSpec);
  if (spec) return { kind: "spec", value: spec };
  const documentCandidates = [
    value,
    value.document,
    value.diagram_document,
    value.structuredContent?.document,
    value.structuredContent?.diagram_document,
    value.result?.document,
    value.result?.diagram_document,
  ];
  const documentData = documentCandidates.find(looksLikeDiagramDocument);
  return documentData ? { kind: "document", value: documentData } : null;
}

async function renderAiDocument() {
  const input = $("#aiDocumentInput").value.trim();
  if (!input) {
    setBridgeStatus("error", "FALTA JSON", "Pega la respuesta estructurada de la IA o importa un archivo.");
    return;
  }
  setLoading(true, "Validando el documento de la IA y trazando el plano…");
  try {
    if (new Blob([input]).size > 262144) throw new Error("El documento supera el límite de 256 KiB.");
    const parsed = JSON.parse(input);
    const diagramInput = extractDiagramInput(parsed);
    if (!diagramInput) throw new Error("No encuentro una especificación ni un documento con componentes y redes.");
    if (typeof ElectroDiagramCore === "undefined") throw new Error("El núcleo gráfico no está disponible.");
    let documentData = diagramInput.value;
    let resolutionDetails = [];
    state.bridgeResolution = null;
    if (diagramInput.kind === "spec") {
      const { compileBrowserDiagramSpec } = await import("./diagram-compiler-browser.mjs?v=1");
      const compiled = compileBrowserDiagramSpec(diagramInput.value);
      state.bridgeResolution = compiled.resolution;
      documentData = compiled.diagram.document;
      resolutionDetails = compiled.resolution.components.map((item) => `${item.component_id} → ${item.symbol_id} ${item.symbol_name}`);
    } else {
      documentData = ElectroDiagramCore.render(documentData).document;
    }
    const validation = ElectroDiagramCore.validate(documentData);
    state.bridgeDiagnostics = {
      errors: validation.errors,
      warnings: [...(state.bridgeResolution?.warnings || []), ...validation.warnings],
    };
    $("#copyAiDiagnostics").hidden = state.bridgeDiagnostics.errors.length === 0 && state.bridgeDiagnostics.warnings.length === 0;
    if (!validation.valid) {
      setBridgeStatus("error", `${validation.errors.length} ERRORES`, "Devuelve estas correcciones a la IA y solicita un nuevo JSON.", validation.errors.map((item) => `${item.code}: ${item.message}`));
      return;
    }
    setBridgeStatus(
      validation.warnings.length ? "warning" : "success",
      diagramInput.kind === "spec" ? "ESPECIFICACIÓN COMPILADA" : (validation.warnings.length ? `${validation.warnings.length} AVISOS` : "DOCUMENTO VÁLIDO"),
      `${documentData.components.length} símbolos · ${documentData.nets.length} redes · ${state.bridgeResolution?.summary?.automatic_symbol_matches || 0} símbolos resueltos por nombre · una sola hoja.`,
      [...resolutionDetails, ...validation.warnings.map((item) => `${item.code}: ${item.message}`)],
    );
    renderPublicResult(publicDesignFromDiagramDocument(documentData));
    showView($("#resultView"));
  } catch (error) {
    state.bridgeDiagnostics = { errors: [{ code: "INVALID_JSON", message: error.message }], warnings: [] };
    $("#copyAiDiagnostics").hidden = false;
    setBridgeStatus("error", "DOCUMENTO NO VÁLIDO", error instanceof SyntaxError ? "El texto no es un JSON válido. Pide a la IA que responda sin bloques Markdown." : error.message);
  } finally {
    setLoading(false);
  }
}

$("#copyAiBrief").addEventListener("click", async () => {
  try {
    await copyText(aiBriefAsPrompt(buildAiBrief()));
    setBriefMessage("Encargo copiado. Pégalo en la IA que prefieras y devuelve aquí su JSON.", "success");
  } catch (error) {
    setBriefMessage(error.message || "No se ha podido copiar el encargo.", "error");
  }
});

$("#downloadAiBrief").addEventListener("click", () => {
  try {
    const brief = buildAiBrief();
    downloadBlob("electroia-encargo-ia.json", `${JSON.stringify(brief, null, 2)}\n`, "application/json;charset=utf-8");
    setBriefMessage("Paquete de diseño guardado.", "success");
  } catch (error) {
    setBriefMessage(error.message || "No se ha podido preparar el paquete.", "error");
  }
});

$("#renderAiDocument").addEventListener("click", renderAiDocument);

$("#aiDocumentFile").addEventListener("change", async (event) => {
  const file = event.currentTarget.files?.[0];
  if (!file) return;
  if (file.size > 262144) {
    setBridgeStatus("error", "ARCHIVO DEMASIADO GRANDE", "El límite de entrada es 256 KiB.");
    return;
  }
  try {
    $("#aiDocumentInput").value = await file.text();
    setBridgeStatus("ready", "ARCHIVO CARGADO", `${file.name} está preparado para validar.`);
  } catch (_error) {
    setBridgeStatus("error", "NO SE PUEDE LEER", "Selecciona un archivo JSON de texto.");
  }
});

$("#loadAiExample").addEventListener("click", async () => {
  try {
    const documentData = await fetchJson("../data/electroia/examples/plc-vfd-motor-system.json", "el ejemplo de integración");
    $("#aiDocumentInput").value = JSON.stringify(documentData, null, 2);
    setBridgeStatus("ready", "EJEMPLO CARGADO", "PLC, variador y motor preparados para validar.");
  } catch (error) {
    setBridgeStatus("error", "EJEMPLO NO DISPONIBLE", error.message);
  }
});

const BENCHMARK_DOMAINS = {
  electrical_panels: "Cuadros eléctricos",
  automation: "Automatización",
  hvac_electronics: "Electrónica HVAC",
  embedded_systems: "Sistemas embebidos",
};

function renderBenchmarkOptions() {
  const selectedDomain = $("#benchmarkDomain").value;
  const cases = (state.benchmarkCatalog?.cases || []).filter((item) => selectedDomain === "all" || item.domain === selectedDomain);
  $("#benchmarkCase").innerHTML = cases.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.title)}</option>`).join("") || '<option value="">Sin casos</option>';
}

async function loadBenchmarkCatalog() {
  try {
    state.benchmarkCatalog = await fetchJson("../data/electroia/professional-benchmark.json", "el banco profesional");
    renderBenchmarkOptions();
  } catch (error) {
    $("#benchmarkCase").innerHTML = '<option value="">Banco no disponible</option>';
    setBridgeStatus("error", "BANCO NO DISPONIBLE", error.message);
  }
}

$("#benchmarkDomain").addEventListener("change", renderBenchmarkOptions);
$("#loadBenchmarkCase").addEventListener("click", () => {
  const selected = (state.benchmarkCatalog?.cases || []).find((item) => item.id === $("#benchmarkCase").value);
  if (!selected) return;
  $("#aiDocumentInput").value = JSON.stringify(selected.spec, null, 2);
  setBridgeStatus("ready", "CASO PROFESIONAL CARGADO", `${BENCHMARK_DOMAINS[selected.domain]} · ${selected.title}. Pulsa «Validar y dibujar».`);
});

$("#copyAiDiagnostics").addEventListener("click", async () => {
  if (!state.bridgeDiagnostics) return;
  const feedback = {
    kind: "electroia_validation_feedback",
    instruction: "Corrige el documento y devuelve únicamente un nuevo JSON completo.",
    errors: state.bridgeDiagnostics.errors || [],
    warnings: state.bridgeDiagnostics.warnings || [],
  };
  try {
    await copyText(JSON.stringify(feedback, null, 2));
    setBridgeStatus("ready", "CORRECCIONES COPIADAS", "Pégalas en la IA para que repare el documento.");
  } catch (_error) {
    setBridgeStatus("error", "NO SE PUDO COPIAR", "Selecciona y copia manualmente los mensajes de validación.");
  }
});

function enterPrivateLab() {
  if (state.accessReady) return;
  state.accessReady = true;
  document.body.classList.remove("access-checking");
  $("#pinGate").hidden = true;
  setToolMode();
  loadEngineAudit();
  loadValidationSummary();
}

async function privateApi(action, { method = "GET", body = null } = {}) {
  const url = new URL(PRIVATE_API_URL);
  url.searchParams.set("action", action);
  const options = { method, credentials: "same-origin", cache: "no-store", headers: { "X-ST-Client": clientToken() } };
  if (body) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify({ ...body, client_token: clientToken() });
  }
  const response = await fetch(url, options);
  const data = await response.json().catch(() => null);
  if (!response.ok || !data?.ok) {
    const error = new Error(data?.error || `request_failed_${response.status}`);
    error.status = response.status;
    throw error;
  }
  return data;
}

function updateValidationSummary(summary) {
  if (!summary) return;
  state.validationSummary = summary;
  const progress = summary.progress || {};
  $("#validationApproved").textContent = String(progress.approved || 0);
  $("#validationProgressBar").style.width = `${Math.max(0, Math.min(100, Number(progress.percent || 0)))}%`;
  $("#validationDomains").innerHTML = (summary.domains || []).map((item) => `
    <span><b>${escapeHtml(item.label)}</b><em>${Number(item.approved || 0)}/5</em></span>
  `).join("");
}

async function loadValidationSummary() {
  try {
    updateValidationSummary(await privateApi("electroia-validation-summary"));
  } catch (_error) {
    $("#validationMessage").textContent = "El registro de pruebas no está disponible todavía.";
  }
}

function detectedDevice() {
  const width = Math.min(window.innerWidth || 0, window.screen?.width || window.innerWidth || 0);
  if (width <= 600) return "mobile";
  if (width <= 1024) return "tablet";
  return "desktop";
}

function suggestedDomain(design) {
  const text = `${design?.title || ""} ${design?.summary || ""}`.toLowerCase();
  if (/arduino|raspberry|esp32|embebid|microcontrol/.test(text)) return "embedded_systems";
  if (/bms|climat|hvac|ventil|compresor|frigor/.test(text)) return "hvac_electronics";
  if (/cuadro|unifilar|distribuci|protecci.n general/.test(text)) return "electrical_panels";
  if (/plc|variador|motor|automat|contactor|arranque/.test(text)) return "automation";
  return "";
}

async function sha256Hex(value) {
  const bytes = new TextEncoder().encode(value);
  if (window.crypto?.subtle) {
    const digest = await window.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  }
  let hash = 2166136261;
  bytes.forEach((byte) => { hash = Math.imul(hash ^ byte, 16777619); });
  return (hash >>> 0).toString(16).padStart(8, "0").repeat(8);
}

async function prepareFieldValidation(design) {
  state.currentDesign = design;
  state.currentCaseKey = "";
  $("#saveValidation").disabled = true;
  $("#validationMessage").textContent = "Preparando la huella del plano…";
  $("#fieldValidationForm").reset();
  $("#validationTester").value = "Administrador";
  $("#validationDomain").value = suggestedDomain(design);
  try {
    const source = design.diagram_document || design;
    const caseKey = await sha256Hex(JSON.stringify(source));
    if (state.currentDesign !== design) return;
    state.currentCaseKey = caseKey;
    $("#validationMessage").textContent = "La comprobación quedará ligada a la huella de este plano.";
  } catch (_error) {
    $("#validationMessage").textContent = "No se ha podido identificar el plano para registrarlo.";
  } finally {
    if (state.currentDesign === design) $("#saveValidation").disabled = !state.currentCaseKey;
  }
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
      ? `Candidata privada · ${releaseSummary.professional_benchmark_cases || 0} casos automáticos sin conflictos`
      : "La auditoría necesita revisión";
    const limitations = (report.known_limitations || []).map((item) => `<li><b>${escapeHtml(item.message)}</b></li>`).join("");
    const blockers = (release.manual_release_blockers || []).map((item) => `<li><b>${escapeHtml(item.exit_criteria)}</b></li>`).join("");
    $("#engineAuditContent").innerHTML = `<div class="engine-audit-metrics">
      <span><b>${Number(summary.public_symbols || 0)}</b> símbolos públicos</span>
      <span><b>${Number(releaseSummary.professional_examples || 0)}</b> planos patrón</span>
      <span><b>${Number(releaseSummary.professional_benchmark_cases || 0)}</b> casos regresivos</span>
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
  if (design.diagram_document && typeof ElectroDiagramCore !== "undefined") {
    design.diagram_document = ElectroDiagramCore.render(design.diagram_document).document;
  }
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
  state.currentValidation = {
    errors: validation?.errors?.length || 0,
    warnings: relevantWarnings.length,
  };
  prepareFieldValidation(design);
  $("#toggleLayoutEditor").hidden = !design.diagram_document;
  if (design.diagram_document) {
    updateLayoutEditorMetrics(ElectroDiagramCore.render(design.diagram_document).diagnostics.metrics);
    attachLayoutEditor();
  } else {
    setLayoutEditMode(false);
  }
}

function updateLayoutEditorMetrics(metrics = {}) {
  const domains = Array.isArray(metrics.layout_domains) ? metrics.layout_domains.length : 0;
  $("#layoutEditorMetrics").textContent = `${domains} zonas · ${metrics.component_overlaps || 0} solapes · ${metrics.wire_component_conflicts || 0} cables sobre símbolos · ${metrics.bridged_crossings || 0} cruces salvados`;
}

function markSelectedComponents() {
  document.querySelectorAll("#schematic g.component, #expandedSchematic g.component").forEach((group) => {
    group.classList.toggle("editable", state.layoutEditMode);
    group.classList.toggle("is-edit-selected", group.dataset.ref === state.selectedComponentRef);
  });
  $("#selectedComponentLabel").textContent = state.selectedComponentRef || "Toca un símbolo";
}

function attachLayoutEditor() {
  $("#schematic").classList.toggle("is-editing", state.layoutEditMode);
  document.querySelectorAll("#schematic g.component, #expandedSchematic g.component").forEach((group) => {
    if (group.dataset.layoutBound === "true") return;
    group.dataset.layoutBound = "true";
    group.addEventListener("click", (event) => {
      if (!state.layoutEditMode) return;
      event.preventDefault();
      event.stopPropagation();
      state.selectedComponentRef = group.dataset.ref || "";
      markSelectedComponents();
    });
  });
  markSelectedComponents();
}

function refreshCurrentDiagram() {
  const documentData = state.currentDesign?.diagram_document;
  if (!documentData) return;
  const result = ElectroDiagramCore.render(documentData);
  state.currentDesign.diagram_document = result.document;
  $("#schematic").innerHTML = result.svg;
  $("#expandedSchematic").innerHTML = result.svg;
  state.currentValidation = {
    errors: result.diagnostics.errors.length,
    warnings: result.diagnostics.warnings.length,
  };
  updateLayoutEditorMetrics(result.diagnostics.metrics);
  attachLayoutEditor();
  prepareFieldValidation(state.currentDesign);
}

function setLayoutEditMode(enabled) {
  state.layoutEditMode = Boolean(enabled);
  if (!state.layoutEditMode) state.selectedComponentRef = "";
  $("#layoutEditor").hidden = !state.layoutEditMode;
  $("#toggleLayoutEditor").setAttribute("aria-pressed", String(state.layoutEditMode));
  $("#toggleLayoutEditor").textContent = state.layoutEditMode ? "Finalizar ajuste" : "Ajustar plano";
  attachLayoutEditor();
}

$("#toggleLayoutEditor").addEventListener("click", () => setLayoutEditMode(!state.layoutEditMode));

document.querySelectorAll("[data-move-x][data-move-y]").forEach((button) => {
  button.addEventListener("click", () => {
    const component = state.currentDesign?.diagram_document?.components?.find((item) => item.ref === state.selectedComponentRef);
    if (!component?.position) {
      $("#selectedComponentLabel").textContent = "Selecciona primero un símbolo";
      return;
    }
    component.position.x += Number(button.dataset.moveX || 0);
    component.position.y += Number(button.dataset.moveY || 0);
    refreshCurrentDiagram();
  });
});

$("#autoArrangeDiagram").addEventListener("click", () => {
  const components = state.currentDesign?.diagram_document?.components;
  if (!components) return;
  components.forEach((component) => { delete component.position; delete component.layout_lane; });
  state.selectedComponentRef = "";
  refreshCurrentDiagram();
});

function downloadBlob(filename, content, type) {
  const link = document.createElement("a");
  const url = URL.createObjectURL(new Blob([content], { type }));
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function designFilename(extension) {
  const source = state.currentDesign?.diagram_document || state.currentDesign || {};
  const base = String(source.document_id || source.title || "electroia-plano")
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 70);
  return `${base || "electroia-plano"}.${extension}`;
}

$("#downloadSvg").addEventListener("click", () => {
  const svg = $("#schematic svg");
  if (!svg) return;
  downloadBlob(designFilename("svg"), `<?xml version="1.0" encoding="UTF-8"?>\n${svg.outerHTML}`, "image/svg+xml;charset=utf-8");
});

$("#downloadJson").addEventListener("click", () => {
  const documentData = state.currentDesign?.diagram_document || state.currentDesign;
  if (!documentData) return;
  downloadBlob(designFilename("json"), `${JSON.stringify(documentData, null, 2)}\n`, "application/json;charset=utf-8");
});

$("#fieldValidationForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const outcome = new FormData(event.currentTarget).get("validationOutcome");
  const domain = $("#validationDomain").value;
  const notes = $("#validationNotes").value.trim();
  if (!state.currentDesign || !state.currentCaseKey) {
    $("#validationMessage").textContent = "Genera primero un plano identificable.";
    return;
  }
  if (!domain || !outcome) {
    $("#validationMessage").textContent = "Selecciona el ámbito y el resultado.";
    return;
  }
  if (outcome === "needs_changes" && notes.length < 6) {
    $("#validationMessage").textContent = "Indica brevemente qué debemos corregir.";
    $("#validationNotes").focus();
    return;
  }
  const button = $("#saveValidation");
  button.disabled = true;
  $("#validationMessage").textContent = "Guardando comprobación…";
  const documentData = state.currentDesign.diagram_document || {};
  try {
    const data = await privateApi("electroia-validation", {
      method: "POST",
      body: {
        case_key: state.currentCaseKey,
        document_id: documentData.document_id || "",
        title: state.currentDesign.title || documentData.title || "Plano ElectroIA",
        domain,
        outcome,
        device: detectedDevice(),
        tester_alias: $("#validationTester").value.trim() || "Administrador",
        notes,
        engine_version: ElectroDiagramCore?.getContract?.().engine_version || "",
        validation_errors: state.currentValidation.errors,
        relevant_warnings: state.currentValidation.warnings,
      },
    });
    updateValidationSummary(data.summary);
    $("#validationMessage").textContent = outcome === "approved"
      ? "Comprobación guardada. Este plano cuenta en el progreso real."
      : "Fallo registrado. Este plano no contará como aprobado hasta corregirlo.";
  } catch (error) {
    const messages = {
      notes_required_for_changes: "Indica brevemente qué debemos corregir.",
      validation_errors_prevent_approval: "El motor ha detectado errores y no permite aprobar este plano.",
      rate_limited: "Se han enviado demasiadas comprobaciones. Espera unos minutos.",
    };
    $("#validationMessage").textContent = messages[error.message] || "No se ha podido guardar la comprobación.";
  } finally {
    button.disabled = false;
  }
});

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

loadBenchmarkCatalog();
initializeAccess();
