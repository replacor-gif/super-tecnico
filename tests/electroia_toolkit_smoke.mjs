import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { callElectroIATool, manifest } from "../electroia-tool-server/src/toolkit.mjs";

const require = createRequire(import.meta.url);
const diagram = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram.js");

assert.equal(manifest.provider_neutral, true);
assert.equal(manifest.embedded_ai_model, false);
assert.equal(manifest.billing_required_by_electroia, false);
assert.equal(manifest.diagram_contract_version, "1.0");

const designBrief = await callElectroIATool("electroia_prepare_design_brief", {
  request: "Diseña el esquema multifilar de un arrancador de motor trifásico con paro de emergencia.",
  document_kind: "multi_line_diagram",
});
assert.equal(designBrief.ok, true);
assert.equal(designBrief.bridge.provider_neutral, true);
assert.equal(designBrief.brief.request.includes("arrancador"), true);
assert.equal(designBrief.brief.document_kind, "multi_line_diagram");
assert.ok(designBrief.brief.mandatory_process.some((item) => item.includes("terminales")));
assert.ok(designBrief.brief.expected_output.required_fields.includes("schema_version"));
await assert.rejects(
  callElectroIATool("electroia_prepare_design_brief", { request: "motor" }),
  /entre 8 y 2000/
);

const diagramContract = await callElectroIATool("electroia_get_diagram_contract", {});
assert.equal(diagramContract.ok, true);
assert.equal(diagramContract.contract.responsibility, "render_only");
assert.equal(diagramContract.contract.calculates_values, false);
assert.equal(diagramContract.contract.selects_components, false);
assert.equal(diagramContract.contract.grid_pitch_mil, 50);
assert.equal(diagramContract.symbol_registry.symbols.length, 504);
assert.equal(diagramContract.symbol_registry.symbols.filter((symbol) => symbol.catalog_id).length, 501);
assert.equal(diagramContract.symbol_registry.symbols.filter((symbol) => symbol.review_status === "engine_reviewed").length, 501);
assert.equal(diagramContract.symbol_registry.symbols.filter((symbol) => symbol.review_status === "auto_draft").length, 0);

const arduinoSymbols = await callElectroIATool("electroia_search_symbols", {query: "Arduino lógica 5V", limit: 5});
assert.equal(arduinoSymbols.search_mode, "ranked_terms");
assert.equal(arduinoSymbols.symbols[0].id, "SYM-0472");
assert.equal(arduinoSymbols.symbols[0].term_coverage, 1);
const relayContactSymbols = await callElectroIATool("electroia_search_symbols", {query: "relé contacto normalmente abierto", limit: 5});
assert.ok(relayContactSymbols.symbols.some((symbol) => symbol.id === "SYM-0120"));
assert.ok(relayContactSymbols.symbols.every((symbol) => symbol.relevance_score > 0));

const connectorSearch = await callElectroIATool("supertecnico_search_connectors", {query: "USB-C"});
assert.equal(connectorSearch.total, 1);
const connector = await callElectroIATool("supertecnico_get_connector", {connector_id: connectorSearch.items[0].id});
assert.equal(connector.record.contacts.length, 24);
const contact = await callElectroIATool("supertecnico_resolve_connector_contact", {connector_id: connector.record.id, contact_or_signal: "CC1"});
assert.equal(contact.contacts.length, 1);
const platformSearch = await callElectroIATool("supertecnico_search_embedded_platforms", {query: "Matter"});
assert.ok(platformSearch.total >= 3);
const platform = await callElectroIATool("supertecnico_get_embedded_platform", {platform_id: "emb-esp32-c6-devkitc-1"});
assert.equal(platform.record.manufacturer, "Espressif");
assert.equal(platform.record.review.status, "source_identified");
const platformRecommendation = await callElectroIATool("supertecnico_recommend_embedded_platforms", {use_case: "gateway Linux compacto con cámara y Wi-Fi"});
assert.equal(platformRecommendation.decision_status, "preselection_only");
assert.ok(platformRecommendation.items.every((item) => ["single_board_computer", "system_on_module", "edge_ai_computer", "soc_fpga_board"].includes(item.platform.platform_class)));
assert.ok(platformRecommendation.items.every((item) => !item.matched_terms.includes("con")));
const roundTwoDiagram = await callElectroIATool("electroia_render_diagram", {document: {
  schema_version: "1.0", document_kind: "circuit_diagram", standard_profile: "IEC_EXPERIMENTAL", title: "Tanda 2",
  components: [
    {ref: "U1", symbol_id: "SYM-0212", position: {x: 5, y: 5}},
    {ref: "U2", symbol_id: "SYM-0183", position: {x: 15, y: 5}},
    {ref: "U3", symbol_id: "SYM-0268", position: {x: 25, y: 5}},
  ],
  nets: [{id: "N1", connections: ["U1.A"]}, {id: "N2", connections: ["U2.IN+"]}, {id: "N3", connections: ["U3.VIN"]}],
}});
assert.match(roundTwoDiagram.diagram.svg, />&amp;<\/text>/);
assert.match(roundTwoDiagram.diagram.svg, />ƒ<\/text>/);
assert.match(roundTwoDiagram.diagram.svg, />W<\/text>/);
assert.equal(diagramContract.symbol_registry.symbols.filter((symbol) => symbol.review_status === "engine_internal").length, 3);
for (const symbolId of ["SYM-0001", "SYM-0006", "SYM-0011", "SYM-0109", "SYM-0110", "SYM-0114", "SYM-0122", "SYM-0123", "SYM-0125", "SYM-0129", "SYM-0130", "SYM-0139", "SYM-0142", "SYM-0151", "SYM-0160", "SYM-0163", "SYM-0167", "SYM-0168", "SYM-0173", "SYM-0177", "SYM-0256", "SYM-0264", "SYM-0356", "SYM-0439", "SYM-0441", "SYM-0299", "SYM-0387", "SYM-0390", "SYM-0427", "SYM-0445", "SYM-0460"]) {
  assert.ok(diagramContract.symbol_registry.symbols.some((symbol) => symbol.id === symbolId), symbolId);
}

const kelvinSearch = await callElectroIATool("electroia_search_symbols", {
  query: "kelvin",
  category: "conexiones",
  review_status: "engine_reviewed",
});
assert.equal(kelvinSearch.ok, true);
assert.equal(kelvinSearch.total, 1);
assert.equal(kelvinSearch.symbols[0].id, "SYM-0430");
assert.deepEqual(kelvinSearch.symbols[0].terminals.map((item) => item.name), ["I+", "S+", "I-", "S-"]);
const kelvinSymbol = await callElectroIATool("electroia_get_symbol", { symbol_id: "sym-0430" });
assert.equal(kelvinSymbol.symbol.kind, "kelvin_4wire");
assert.equal(kelvinSymbol.symbol.review_status, "engine_reviewed");
const aliasSearch = await callElectroIATool("electroia_search_symbols", { query: "empalme" });
assert.ok(aliasSearch.symbols.some((item) => item.id === "SYM-0002"));
const protectionSearch = await callElectroIATool("electroia_search_symbols", { query: "klixon", review_status: "engine_reviewed" });
assert.equal(protectionSearch.symbols[0].id, "SYM-0447");
assert.deepEqual(protectionSearch.symbols[0].terminals.map((item) => item.name), ["1", "2"]);
await assert.rejects(callElectroIATool("electroia_get_symbol", { symbol_id: "SYM-9999" }), /no encontrado/);

const exactModelDiagram = await callElectroIATool("electroia_render_diagram", {
  document: {
    schema_version: "1.0",
    document_kind: "circuit_diagram",
    standard_profile: "IEC_EXPERIMENTAL",
    title: "Prueba de modelo exacto obligatorio",
    components: [
      { ref: "PLC1", symbol_id: "SYM-0461", position: { x: 4, y: 4 } },
      { ref: "X1", symbol_id: "ST-GENERIC-2P", position: { x: 18, y: 4 } },
    ],
    nets: [{ id: "N1", connections: ["PLC1.IO_BUS", "X1.1"] }],
  },
});
assert.equal(exactModelDiagram.ok, true);
assert.ok(exactModelDiagram.diagram.diagnostics.warnings.some((item) => item.code === "EXACT_MODEL_REQUIRED"));
assert.doesNotMatch(exactModelDiagram.diagram.svg, /class="component review-auto_draft"/);

for (const symbol of diagramContract.symbol_registry.symbols) {
  const firstPort = Object.keys(symbol.ports)[0];
  const isNoConnect = symbol.ports[firstPort].electrical_type === "no_connect";
  const rendered = await callElectroIATool("electroia_render_diagram", {
    document: {
      schema_version: "1.0",
      document_kind: "circuit_diagram",
      standard_profile: "IEC_EXPERIMENTAL",
      title: symbol.name,
      components: [
        { ref: "X1", symbol_id: symbol.id, position: { x: 6, y: 6 } },
        ...(isNoConnect ? [{ ref: "Y1", symbol_id: "ST-GENERIC-2P", position: { x: 16, y: 6 } }] : []),
      ],
      nets: [{ id: "N1", show_label: false, connections: [isNoConnect ? "Y1.1" : `X1.${firstPort}`] }],
    },
  });
  assert.equal(rendered.ok, true, symbol.id);
  assert.match(rendered.diagram.svg, new RegExp(`data-symbol-id="${symbol.id}"`));
}

const motorStarterDocument = JSON.parse(await readFile(
  new URL("../data/electroia/examples/motor-starter-direct.json", import.meta.url),
  "utf8"
));
const motorStarter = await callElectroIATool("electroia_render_diagram", { document: motorStarterDocument });
assert.equal(motorStarter.ok, true);
assert.equal(motorStarter.diagram.document.document_kind, "multi_line_diagram");
assert.equal(motorStarter.diagram.diagnostics.metrics.symbols, 18);
assert.equal(motorStarter.diagram.diagnostics.metrics.pages, 1);
assert.equal(motorStarter.diagram.diagnostics.metrics.off_grid_terminals, 0);
assert.match(motorStarter.diagram.svg, /data-symbol-id="SYM-0387"/);
assert.match(motorStarter.diagram.svg, /data-symbol-id="SYM-0151"/);
assert.match(motorStarter.diagram.svg, />KM1</);
assert.doesNotMatch(motorStarter.diagram.svg, /class="zone/);

const singleLineDocument = JSON.parse(await readFile(
  new URL("../data/electroia/examples/distribution-board-single-line.json", import.meta.url),
  "utf8"
));
const singleLine = await callElectroIATool("electroia_render_diagram", { document: singleLineDocument });
assert.equal(singleLine.ok, true);
assert.equal(singleLine.diagram.document.document_kind, "single_line_diagram");
assert.equal(singleLine.diagram.diagnostics.metrics.symbols, 11);
assert.equal(singleLine.diagram.diagnostics.metrics.nets, 10);
assert.equal(singleLine.diagram.diagnostics.metrics.terminals, 20);
assert.equal(singleLine.diagram.diagnostics.metrics.pages, 1);
assert.equal(singleLine.diagram.diagnostics.metrics.off_grid_terminals, 0);
assert.match(singleLine.diagram.svg, /data-document-kind="single_line_diagram"/);
assert.match(singleLine.diagram.svg, /data-symbol-id="SYM-0299"/);
assert.match(singleLine.diagram.svg, /data-symbol-id="SYM-0390"/);
assert.match(singleLine.diagram.svg, /3 conductores/);
assert.doesNotMatch(singleLine.diagram.svg, /class="zone/);

const neutralDiagram = await callElectroIATool("electroia_render_diagram", {
  document: {
    schema_version: "1.0",
    document_kind: "circuit_diagram",
    standard_profile: "IEC_EXPERIMENTAL",
    title: "Prueba neutral",
    grid: { pitch_mil: 50, show: true },
    layout: { single_canvas: true },
    components: [
      { ref: "PS1", symbol_id: "SYM-0018", value: "12 V", position: { x: 2, y: 6 } },
      { ref: "R1", symbol_id: "SYM-0023", value: "1 kΩ", position: { x: 8, y: 3 }, rotation: 90 },
      { ref: "LOAD1", symbol_id: "ST-GENERIC-2P", value: "Carga", position: { x: 14, y: 7 }, rotation: 90 },
    ],
    nets: [
      { id: "VCC", role: "power", connections: ["PS1.+", "R1.1"] },
      { id: "OUT", role: "signal", connections: ["R1.2", "LOAD1.1"] },
      { id: "GND", role: "ground", connections: ["LOAD1.2", "PS1.-"] },
    ],
  },
});
assert.equal(neutralDiagram.ok, true);
assert.equal(neutralDiagram.diagram.diagnostics.metrics.pages, 1);
assert.equal(neutralDiagram.diagram.diagnostics.metrics.single_canvas, true);
assert.equal(neutralDiagram.diagram.diagnostics.metrics.off_grid_terminals, 0);
assert.match(neutralDiagram.diagram.svg, /data-grid-pitch-mil="50"/);
assert.match(neutralDiagram.diagram.svg, /LIENZO ÚNICO/);

const analysis = await callElectroIATool("electroia_analyze_request", {
  request: "Quiero encender un relé de 12 V utilizando una señal de 5 V.",
});
assert.equal(analysis.ok, true);
assert.equal(analysis.extracted.project_type, "relay_driver");
assert.equal(analysis.extracted.relay_voltage, 12);
assert.equal(analysis.extracted.signal_voltage, 5);

const generated = await callElectroIATool("electroia_generate_relay_driver", {
  relay_voltage: 12,
  signal_voltage: 5,
  controller: "arduino",
  coil_type: "dc",
  coil_current_ma: 80,
  load_kind: "lámpara de 12 V",
  load_current_a: 2,
  isolation: true,
  source: { kind: "hand_drawn_sketch_analysis" },
});

assert.equal(generated.ok, true);
assert.equal(generated.tool, "electroia_generate_relay_driver");
assert.equal(generated.design.circuit_model.topology, "isolated_low_side_relay_driver");
assert.equal(generated.design.circuit_model.schema_version, "0.4");
assert.ok(generated.design.components.some((item) => item.part_number === "PC817"));
assert.ok(generated.design.warnings.some((item) => item.includes("masas")));
const relaySvg = diagram.render(generated.design);
assert.match(relaySvg, /data-topology="isolated_low_side_relay_driver"/);
assert.match(relaySvg, /data-contract-version="1.0"/);
assert.match(relaySvg, /NO UNIR GND_CONTROL Y GND_RELAY/);
assert.doesNotMatch(relaySvg, /class="domain/);

const fanAnalysis = await callElectroIATool("electroia_analyze_request", {
  request: "Quiero que un ventilador de 12 V se encienda cuando llegue a 40 °C.",
});
assert.equal(fanAnalysis.ok, true);
assert.equal(fanAnalysis.extracted.project_type, "temperature_fan_controller");
assert.equal(fanAnalysis.extracted.fan_voltage, 12);
assert.equal(fanAnalysis.extracted.turn_on_temperature_c, 40);

const fanGenerated = await callElectroIATool("electroia_generate_temperature_fan", {
  fan_voltage: 12,
  fan_current_a: 0.35,
  turn_on_temperature_c: 40,
  hysteresis_c: 3,
  fan_type: "dc_2wire",
  source: { kind: "image_analysis" },
});
assert.equal(fanGenerated.ok, true);
assert.equal(fanGenerated.design.circuit_model.topology, "thermostatic_dc_fan_controller");
assert.equal(fanGenerated.design.circuit_model.schema_version, "0.5");
assert.equal(fanGenerated.design.values.turn_off_temperature_c, 37);
assert.ok(fanGenerated.design.components.some((item) => item.part_number === "LM393"));
assert.ok(fanGenerated.design.symbol_manifest.some((item) => item.id === "SYM-0156" && item.asset));
const comparatorPart = fanGenerated.design.circuit_model.parts.find((item) => item.ref === "U1");
assert.equal(comparatorPart.pins["+"], "TEMP_REF");
assert.equal(comparatorPart.pins["-"], "TEMP_SENSE");
assert.deepEqual(
  fanGenerated.design.circuit_model.nets.find((item) => item.id === "TEMP_REF").connections,
  ["RV1.2", "U1.+", "R5.2"]
);
const fanSvg = diagram.render(fanGenerated.design);
assert.match(fanSvg, /data-topology="thermostatic_dc_fan_controller"/);
assert.match(fanSvg, /data-contract-version="1.0"/);
assert.match(fanSvg, /data-grid-pitch-mil="50"/);
assert.match(fanSvg, /Control de ventilador 12 V por temperatura/);
assert.doesNotMatch(fanSvg, /class="zone/);
await assert.rejects(
  callElectroIATool("electroia_generate_temperature_fan", {
    fan_voltage: 12,
    fan_current_a: 0.3,
    turn_on_temperature_c: 40,
    hysteresis_c: 3,
    fan_type: "pwm_4wire",
  }),
  /cuatro cables/
);

process.stdout.write("ElectroIA provider-neutral toolkit smoke: OK\n");
