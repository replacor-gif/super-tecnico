import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");
const registryResult = core.getRegistry();
const registry = registryResult.symbols;

assert.equal(registryResult.engine_version, "1.14.0-alpha.1");
assert.equal(registry.length, 504);
assert.equal(registry.filter((item) => item.catalog_id).length, 501);
assert.equal(registry.filter((item) => item.review_status === "engine_reviewed").length, 501);
assert.equal(registry.filter((item) => item.review_status === "auto_draft").length, 0);
assert.equal(registry.filter((item) => item.id.startsWith("ST-AUTO-")).length, 0);
assert.equal(registry.filter((item) => item.category === "Automatización y control programable").length, 20);
assert.equal(registry.filter((item) => item.category === "Accionamientos y maniobra").length, 12);
assert.equal(registry.filter((item) => item.category === "Control técnico de edificios").length, 8);

const vfd = registry.find((item) => item.id === "SYM-0481");
const arduino = registry.find((item) => item.id === "SYM-0472");
const supply = registry.find((item) => item.id === "SYM-0501");
assert.deepEqual(Object.keys(vfd.ports), ["R_L1", "S_L2", "T_L3", "DI_AI", "STO", "BUS", "U", "V", "W", "AO_RELAY", "DC_BUS", "PE"]);
assert.deepEqual(Object.keys(arduino.ports), ["VIN", "5V", "GND", "GPIO", "ADC", "PWM", "I2C", "SPI_UART"]);
assert.deepEqual(Object.keys(supply.ports), ["L1", "L2", "L3", "N", "PE"]);
assert.equal(vfd.terminal_model, "functional_group");
assert.equal(vfd.requires_exact_model, true);

const exampleNames = [
  "plc-vfd-motor-system.json",
  "arduino-industrial-interface.json",
  "bms-ahu-building-control.json",
];
const rendered = [];
for (const name of exampleNames) {
  const document = JSON.parse(await readFile(new URL(`../data/electroia/examples/${name}`, import.meta.url), "utf8"));
  const result = core.render(document);
  assert.equal(result.diagnostics.errors.length, 0, name);
  assert.equal(result.diagnostics.metrics.component_overlaps, 0, name);
  assert.equal(result.diagnostics.metrics.wire_component_conflicts, 0, name);
  assert.doesNotMatch(result.svg, /class="component review-auto_draft"/, name);
  assert.match(result.svg, /data-grid-pitch-mil="50"/, name);
  rendered.push(result.svg);
}

const exactModelWarning = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "Modelo exacto obligatorio",
  components: [
    {ref:"MCU1",symbol_id:"SYM-0472",position:{x:5,y:5}},
    {ref:"X1",symbol_id:"ST-GENERIC-2P",position:{x:20,y:5}},
  ],
  nets: [{id:"GPIO",connections:["MCU1.GPIO","X1.1"]}],
});
assert.ok(exactModelWarning.diagnostics.warnings.some((item) => item.code === "EXACT_MODEL_REQUIRED"));

const contention = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "Detección de contención",
  components: [
    {ref:"DO1",symbol_id:"SYM-0464",model:"TEST",position:{x:5,y:5}},
    {ref:"DO2",symbol_id:"SYM-0464",model:"TEST",position:{x:25,y:5}},
  ],
  nets: [{id:"BAD_OUTPUTS",connections:["DO1.Q0","DO2.Q0"]}],
});
assert.ok(contention.diagnostics.warnings.some((item) => item.code === "OUTPUT_CONTENTION"));

const signalPowerMix = core.validate({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "Dominio de señal unido a potencia",
  components: [
    {ref:"DO1",symbol_id:"SYM-0464",model:"TEST"},
    {ref:"T1",symbol_id:"SYM-0047"},
  ],
  nets: [{id:"BAD_DOMAIN",connections:["DO1.Q0","T1.L1"]}],
});
assert.ok(signalPowerMix.warnings.some((item) => item.code === "SIGNAL_POWER_DOMAIN_MIX"));

const noConnect = core.validate({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "Terminal no conectable",
  components: [
    {ref:"NC1",symbol_id:"SYM-0428"},
    {ref:"X1",symbol_id:"ST-GENERIC-2P"},
  ],
  nets: [{id:"BAD_NC",connections:["NC1.1","X1.1"]}],
});
assert.equal(noConnect.valid, false);
assert.ok(noConnect.errors.some((item) => item.code === "NO_CONNECT_USED"));

const duplicateConnection = core.validate({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "Conexión repetida",
  components: [{ref:"X1",symbol_id:"ST-GENERIC-2P"}],
  nets: [{id:"BAD_DUP",connections:["X1.1","X1.1"]}],
});
assert.equal(duplicateConnection.valid, false);
assert.ok(duplicateConnection.errors.some((item) => item.code === "DUPLICATE_CONNECTION"));

const overlap = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "Detección de solape",
  components: [
    {ref:"PLC1",symbol_id:"SYM-0461",model:"TEST",position:{x:10,y:10}},
    {ref:"HMI1",symbol_id:"SYM-0468",model:"TEST",position:{x:10,y:10}},
  ],
  nets: [{id:"ETH",connections:["PLC1.ETH","HMI1.ETH"]}],
});
assert.ok(overlap.diagnostics.warnings.some((item) => item.code === "COMPONENT_OVERLAP"));
assert.ok(overlap.diagnostics.metrics.component_overlaps >= 1);

await mkdir("test-artifacts", { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  args: ["--disable-gpu", "--no-first-run"],
});
const page = await browser.newPage({viewport:{width:1800,height:1200},deviceScaleFactor:1});
await page.setContent(`<style>body{margin:0;padding:20px;background:#dfe5e2}section{margin:0 0 28px;background:white;border:1px solid #aeb8b3}svg{display:block;width:100%;height:auto}</style>${rendered.map((svg) => `<section>${svg}</section>`).join("")}`);
await page.screenshot({path:"test-artifacts/electroia-professional-systems.png",fullPage:true});
await browser.close();
process.stdout.write("ElectroIA professional audit visual: 501 public symbols and 3 systems OK\n");
