const state = {
  request: "",
  extracted: null,
  questions: [],
  index: 0,
  answers: {},
};

const $ = (selector) => document.querySelector(selector);
const views = [$("#introView"), $("#questionsView"), $("#resultView")];

function showView(view) {
  views.forEach((item) => item.classList.toggle("active", item === view));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setLoading(visible) {
  $("#loadingOverlay").classList.toggle("visible", visible);
  $("#loadingOverlay").setAttribute("aria-hidden", String(!visible));
}

async function api(path, body) {
  await new Promise((resolve) => window.setTimeout(resolve, 220));
  if (typeof ElectroEngine === "undefined") throw new Error("El motor de diseño no está disponible");
  if (path === "/api/analyze") return ElectroEngine.analyze(body.request);
  if (path === "/api/design") return ElectroEngine.design(body.request, body.answers);
  throw new Error("Operación desconocida");
}

$("#requestForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const request = $("#requestInput").value.trim();
  setLoading(true);
  try {
    const data = await api("/api/analyze", { request });
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
    <div class="question-number">0${state.index + 1}</div>
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

  setLoading(true);
  try {
    const data = await api("/api/design", { request: state.request, answers: state.answers });
    renderDesign(data.design);
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

function renderDesign(design) {
  $("#designTitle").textContent = design.title;
  $("#designSummary").textContent = design.summary;

  const banner = $("#statusBanner");
  banner.className = `status-banner ${design.status}`;
  banner.innerHTML = design.status === "ready"
    ? "<b>Propuesta lista para revisar.</b> Ya tenemos los valores esenciales para seleccionar los componentes."
    : `<b>Diseño provisional.</b> ${design.provisional_reasons.map(escapeHtml).join(" ")}`;

  $("#decisionsList").innerHTML = design.decisions.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  $("#componentsList").innerHTML = design.components.map((item) => `
    <div class="component">
      <span class="component-ref">${escapeHtml(item.ref)}</span>
      <b>${escapeHtml(item.name)}</b>
      <small>${escapeHtml(item.spec)}</small>
    </div>
  `).join("");
  $("#connectionsList").innerHTML = design.connections.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  $("#warningsList").innerHTML = design.warnings.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  $("#schematic").innerHTML = buildSchematic(design.values);
}

function buildSchematic(values) {
  const signal = `${values.signal_voltage} V`;
  const relay = `${values.relay_voltage} V${values.coil_type === "dc" ? " CC" : ""}`;
  const isolation = values.isolated;
  return `
  <svg viewBox="0 0 760 390" role="img" aria-label="Esquema funcional de control de un relé con MOSFET">
    <defs>
      <filter id="soft"><feDropShadow dx="0" dy="5" stdDeviation="7" flood-opacity=".08"/></filter>
      <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4 0 8z" fill="#77a426"/></marker>
    </defs>
    <style>
      .wire{fill:none;stroke:#7b8581;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}.control{stroke:#77a426}.power{stroke:#ef7540}.box{fill:#fffefa;stroke:#b8bcb8;stroke-width:1.3}.t{font:600 13px Inter,Arial,sans-serif;fill:#262a29}.s{font:11px Inter,Arial,sans-serif;fill:#707875}.ref{font:700 10px ui-monospace,monospace;fill:#62841f}.node{fill:#1f2422}.plus{font:700 17px Inter,Arial,sans-serif;fill:#ef7540}
    </style>

    <text class="ref" x="30" y="36">CONTROL</text>
    <rect class="box" filter="url(#soft)" x="28" y="58" rx="11" width="142" height="82"/>
    <text class="t" x="47" y="88">Salida digital</text>
    <text class="s" x="47" y="112">Señal ${signal}</text>
    <circle cx="170" cy="99" r="4" fill="#77a426"/>

    <path class="wire control" d="M174 99H250" marker-end="url(#arrow)"/>
    <rect class="box" x="253" y="82" rx="6" width="74" height="34"/>
    <text class="ref" x="264" y="103">R1 · 100Ω</text>
    ${isolation ? `
      <path class="wire control" d="M327 99H363"/>
      <rect class="box" x="363" y="60" rx="9" width="96" height="78"/>
      <text class="ref" x="378" y="88">U1 · OPTO</text>
      <text class="s" x="378" y="111">aislamiento</text>
      <path class="wire control" d="M459 99H499"/>
    ` : `<path class="wire control" d="M327 99H499"/>`}

    <text class="ref" x="480" y="36">ETAPA DE POTENCIA</text>
    <circle class="node" cx="500" cy="99" r="4"/>
    <path class="wire" d="M500 99V164"/>
    <rect class="box" filter="url(#soft)" x="463" y="164" rx="10" width="76" height="80"/>
    <text class="ref" x="482" y="190">Q1</text>
    <text class="t" x="475" y="213">MOSFET</text>
    <text class="s" x="478" y="231">N lógico</text>

    <path class="wire" d="M500 244V310H500"/>
    <path class="wire" d="M475 310H525M483 318H517M491 326H509"/>
    <text class="s" x="535" y="319">GND</text>
    ${isolation ? "" : `<path class="wire" d="M98 140V310H475"/><circle class="node" cx="98" cy="140" r="3"/><text class="s" x="37" y="303">Masa común</text>`}

    <path class="wire power" d="M500 164V135H590V100"/>
    <rect class="box" filter="url(#soft)" x="555" y="55" rx="10" width="125" height="62"/>
    <text class="ref" x="571" y="80">K1 · BOBINA</text>
    <path d="M575 97c8-18 16 18 24 0s16 18 24 0 16 18 24 0" fill="none" stroke="#ef7540" stroke-width="2"/>
    <path class="wire power" d="M618 55V28H704"/>
    <text class="plus" x="708" y="34">+ ${relay}</text>

    <path class="wire" d="M555 128H680V55"/>
    <rect class="box" x="574" y="121" rx="5" width="70" height="27"/>
    <text class="ref" x="584" y="139">D1 · 1N4007</text>
    <text class="s" x="651" y="143">banda ↑</text>

    <path class="wire" d="M500 99H420V278"/>
    <rect class="box" x="384" y="278" rx="5" width="72" height="30"/>
    <text class="ref" x="395" y="297">R2 · 100k</text>
    <path class="wire" d="M420 308V318H475"/>

    <rect x="561" y="194" width="153" height="92" rx="10" fill="#f3f1e9" stroke="#b8bcb8" stroke-dasharray="5 4"/>
    <text class="ref" x="578" y="218">CONTACTOS DEL RELÉ</text>
    <circle class="node" cx="586" cy="252" r="4"/><circle class="node" cx="688" cy="252" r="4"/>
    <path class="wire power" d="M590 252L673 226"/>
    <text class="s" x="596" y="275">Circuito de la carga</text>
  </svg>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
