const state = {
  request: "",
  extracted: null,
  questions: [],
  index: 0,
  answers: {},
  resourcesPromise: null,
  intelligenceConfigured: false,
  analysisSource: "local",
  accessReady: false,
};

const $ = (selector) => document.querySelector(selector);
const views = [$("#introView"), $("#questionsView"), $("#resultView")];
const PRIVATE_API_URL = new URL("../api/index.php", document.baseURI);

function showView(view) {
  views.forEach((item) => item.classList.toggle("active", item === view));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setLoading(visible, message = "Traduciendo tu idea a electrónica…") {
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

function setEngineMode(mode) {
  const usingAi = mode === "ai";
  $("#engineStatus").classList.toggle("ai", usingAi);
  $("#engineStatus").classList.toggle("local", !usingAi);
  $("#engineStatusLabel").textContent = usingAi ? "IA privada" : "Motor local";
  $("#privacyStatus").lastChild.textContent = usingAi
    ? " Petición cifrada al motor privado"
    : " Tu petición se procesa localmente";
}

function enterPrivateLab() {
  if (state.accessReady) return;
  state.accessReady = true;
  document.body.classList.remove("access-checking");
  $("#pinGate").hidden = true;
  initializeIntelligence();
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

async function initializeIntelligence() {
  const url = new URL(PRIVATE_API_URL);
  url.searchParams.set("action", "electroia-status");
  try {
    const response = await fetch(url, { cache: "no-store", credentials: "same-origin" });
    const data = response.ok ? await response.json() : null;
    state.intelligenceConfigured = data?.engine?.configured === true;
  } catch (_error) {
    state.intelligenceConfigured = false;
  }
  setEngineMode(state.intelligenceConfigured ? "ai" : "local");
}

async function analyzeWithPrivateAi(request) {
  const url = new URL(PRIVATE_API_URL);
  url.searchParams.set("action", "electroia-analyze");
  const response = await fetch(url, {
    method: "POST",
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-ST-Client": clientToken(),
    },
    body: JSON.stringify({ request, client_token: clientToken() }),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok || !data?.ok || !data?.extracted) throw new Error("private_ai_unavailable");
  return {
    ...data,
    questions: data.can_design ? ElectroEngine.buildQuestions(data.extracted) : [],
  };
}

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
    if (state.intelligenceConfigured) {
      try {
        const result = await analyzeWithPrivateAi(body.request);
        state.analysisSource = "openai";
        setEngineMode("ai");
        return result;
      } catch (_error) {
        state.intelligenceConfigured = false;
        setEngineMode("local");
      }
    }
    state.analysisSource = "local";
    return { ...ElectroEngine.analyze(body.request), source: "local", can_design: true };
  }
  if (path === "/api/design") {
    const resources = await loadDesignResources();
    return ElectroEngine.design(body.request, body.answers, resources);
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
      throw new Error(`He entendido tu idea: ${data.understanding} El diseño automático de este caso será uno de los próximos módulos; ahora mismo está activo el controlador de relé.`);
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
    $("#detectedText").textContent = bits.length ? bits.join(" · ") : "Relé detectado";
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

$(".example").addEventListener("click", () => {
  $("#requestInput").value = "Quiero encender un relé de 12 V utilizando una señal de 5 V.";
  $("#requestInput").focus();
});

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

  setLoading(true, "Consultando componentes y construyendo el esquema…");
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

  const banner = $("#statusBanner");
  banner.className = `status-banner ${design.status}`;
  banner.innerHTML = design.status === "ready"
    ? "<b>Circuito preparado.</b> Revisa las conexiones antes de montarlo."
    : "<b>Esquema generado.</b> Confirma las piezas marcadas como «por confirmar» antes de montarlo.";

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

function renderDesign(design) {
  $("#designTitle").textContent = design.title;
  $("#designSummary").textContent = design.summary;
  $("#databaseMeta").textContent = state.analysisSource === "openai" ? "IA + DATOS REALES" : "MOTOR LOCAL + DATOS REALES";

  const banner = $("#statusBanner");
  banner.className = `status-banner ${design.status}`;
  banner.innerHTML = design.status === "ready"
    ? "<b>Propuesta lista para revisar.</b> Los datos esenciales y las referencias están confirmados."
    : `<b>Diseño provisional y honesto.</b> ${design.provisional_reasons.map(escapeHtml).join(" ")}`;

  $("#decisionsList").innerHTML = design.decisions.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  $("#componentsList").innerHTML = design.components.map((item) => {
    const metadata = item.source_kind === "catalog"
      ? `<span>${escapeHtml(item.manufacturer || "Fabricante no indicado")} · ID ${escapeHtml(item.database_id)} · confianza ${Math.round(Number(item.confidence || 0) * 100)}%</span>`
      : item.calculation
        ? `<span>${escapeHtml(item.calculation)}</span>`
        : "";
    return `
      <div class="component">
        <span class="component-ref">${escapeHtml(item.ref)}</span>
        <div class="component-name">
          <b>${escapeHtml(item.name)}</b>
          <em class="source-badge ${escapeHtml(item.source_kind)}">${escapeHtml(item.source_label)}</em>
        </div>
        <small>${escapeHtml(item.spec)}${metadata}</small>
      </div>
    `;
  }).join("");
  $("#connectionsList").innerHTML = design.connections.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  $("#warningsList").innerHTML = design.warnings.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  $("#schematic").innerHTML = buildSchematic(design);
  renderDatabaseSummary(design.database);
  renderCircuitModel(design.circuit_model);
}

function renderDatabaseSummary(database) {
  $("#databaseSummary").innerHTML = `
    <div><b>${formatNumber(database.component_records)}</b><span>componentes consultables</span><small>versión ${escapeHtml(database.component_version)}</small></div>
    <div><b>${formatNumber(database.symbol_records)}</b><span>símbolos normalizados</span><small>versión ${escapeHtml(database.symbol_version)}</small></div>
    <div><b>${database.selected_catalog_components}</b><span>piezas tomadas de catálogo</span><small>${database.calculated_values} valores calculados · ${database.pending_specifications} por elegir</small></div>
  `;
}

function renderCircuitModel(model) {
  $("#modelMeta").textContent = `Modelo ${model.schema_version} · ${model.topology}`;
  $("#netsList").innerHTML = model.nets.map((net) => `
    <div class="net-row">
      <span>${escapeHtml(net.id)}</span>
      <b>${escapeHtml(net.label)}</b>
      <small>${net.connections.map(escapeHtml).join(" · ")}</small>
    </div>
  `).join("");
}

function symbolAsset(design, symbolId) {
  return design.symbol_manifest.find((item) => item.id === symbolId)?.asset || "";
}

function symbolImage(design, symbolId, x, y, width = 132, height = 72, options = {}) {
  const asset = symbolAsset(design, symbolId);
  if (!asset) return `<rect class="missing-symbol" x="${x}" y="${y}" width="${width}" height="${height}" rx="7"/>`;
  const image = `<image href="${escapeHtml(asset)}" x="0" y="0" width="${width}" height="${height}" preserveAspectRatio="none"/>`;
  if (options.flip) return `<g transform="translate(${x + width} ${y}) scale(-1 1)">${image}</g>`;
  return `<g transform="translate(${x} ${y})">${image}</g>`;
}

function buildSchematic(design) {
  const values = design.values;
  const signal = `${values.signal_voltage} V`;
  const relay = `${values.relay_voltage} V${values.coil_type === "dc" ? " CC" : ""}`;
  const q1 = design.components.find((item) => item.ref === "Q1");
  const q1Name = q1?.part_number || "MOSFET por elegir";
  const isolated = values.isolated;
  const controlStart = isolated ? 248 : 185;

  return `
  <svg viewBox="0 0 900 510" role="img" aria-label="Esquema eléctrico estructurado de control de un relé con MOSFET">
    <defs>
      <filter id="soft"><feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity=".07"/></filter>
      <marker id="controlArrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4 0 8z" fill="#77a426"/></marker>
    </defs>
    <style>
      .wire{fill:none;stroke:#66706c;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}.control{stroke:#77a426}.power{stroke:#ef7540}.box{fill:#fffefa;stroke:#b8bcb8;stroke-width:1.3}.pending{fill:#fff8ed;stroke:#d49a57;stroke-dasharray:5 4}.t{font:600 13px Inter,Arial,sans-serif;fill:#262a29}.s{font:11px Inter,Arial,sans-serif;fill:#707875}.ref{font:700 10px ui-monospace,monospace;fill:#62841f}.net{font:700 9px ui-monospace,monospace;fill:#a84c26}.node{fill:#1f2422}.missing-symbol{fill:#fff4e4;stroke:#cf7e31;stroke-dasharray:4 3}
    </style>

    <text class="ref" x="34" y="35">CONTROL</text>
    <rect class="box" filter="url(#soft)" x="32" y="62" rx="11" width="142" height="76"/>
    <text class="t" x="49" y="90">Salida digital</text>
    <text class="s" x="49" y="113">Señal ${escapeHtml(signal)}</text>
    <circle cx="174" cy="101" r="4" fill="#77a426"/>
    <path class="wire control" d="M178 101H${controlStart}" marker-end="url(#controlArrow)"/>
    ${isolated ? `
      <rect class="pending" x="250" y="61" rx="9" width="126" height="80"/>
      ${symbolImage(design, "SYM-0097", 250, 64, 126, 69)}
      <text class="ref" x="259" y="57">U1 · OPTO PENDIENTE</text>
      <text class="s" x="260" y="151">faltan referencia y fuente aislada</text>
      <path class="wire control" d="M376 101H405"/>
    ` : ""}

    <text class="ref" x="${isolated ? 405 : 185}" y="78">R1 · 100 Ω</text>
    ${symbolImage(design, "SYM-0023", isolated ? 390 : 170, 65)}
    <path class="wire control" d="M${isolated ? 510 : 290} 101H565"/>
    <circle class="node" cx="565" cy="101" r="4"/>
    <text class="net" x="515" y="91">GATE</text>

    <text class="ref" x="466" y="35">ETAPA DE POTENCIA · SÍMBOLOS REPLACOR</text>
    <text class="net" x="460" y="52">VRELAY_PLUS</text>
    ${symbolImage(design, "SYM-0014", 394, 0)}
    <path class="wire power" d="M460 60V106H507"/>

    <text class="ref" x="520" y="83">K1 · BOBINA ${escapeHtml(relay)}</text>
    ${symbolImage(design, "SYM-0119", 495, 70)}
    <path class="wire power" d="M507 106V178"/>
    <path class="wire power" d="M615 106V178"/>
    <circle class="node" cx="507" cy="106" r="4"/>
    <circle class="node" cx="615" cy="106" r="4"/>

    <text class="ref" x="520" y="161">D1 · 1N4007</text>
    ${symbolImage(design, "SYM-0057", 495, 142, 132, 72, { flip: true })}
    <text class="s" x="488" y="198">K</text><text class="s" x="622" y="198">A</text>
    <path class="wire power" d="M615 178V252H667"/>
    <text class="net" x="622" y="230">COIL_LOW</text>

    <text class="ref" x="676" y="237">Q1 · ${escapeHtml(q1Name)}</text>
    ${symbolImage(design, "SYM-0080", 550, 240)}
    <path class="wire control" d="M565 101V276"/>
    <path class="wire" d="M667 300V410"/>

    <text class="ref" x="413" y="333">R2 · 100 kΩ</text>
    ${symbolImage(design, "SYM-0023", 400, 320)}
    <path class="wire" d="M520 356H545V276H565"/>
    <path class="wire" d="M412 356V430H667V410"/>
    <circle class="node" cx="565" cy="276" r="4"/>
    ${symbolImage(design, "SYM-0010", 601, 398)}
    <text class="net" x="680" y="439">GND</text>

    <rect class="box" x="704" y="70" width="164" height="148" rx="12" filter="url(#soft)"/>
    <text class="ref" x="721" y="94">K1.1 · CONTACTO NO</text>
    ${symbolImage(design, "SYM-0120", 719, 98, 132, 72)}
    <text class="s" x="722" y="191">Carga: circuito separado</text>
    <text class="s" x="722" y="207">Dimensionado pendiente</text>

    <rect x="32" y="456" width="836" height="34" rx="8" fill="#f3f1e9" stroke="#d6d8d3"/>
    <text class="s" x="49" y="478">Las redes mostradas proceden del modelo eléctrico: CTRL_OUT → GATE → Q1 · VRELAY_PLUS → K1/D1 · COIL_LOW → Q1 · GND común.</text>
  </svg>`;
}

function formatNumber(value) {
  return new Intl.NumberFormat("es-ES").format(Number(value || 0));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

initializeAccess();
