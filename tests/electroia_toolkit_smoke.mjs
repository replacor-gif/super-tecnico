import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { callElectroIATool, manifest } from "../electroia-tool-server/src/toolkit.mjs";

const require = createRequire(import.meta.url);
const diagram = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram.js");

assert.equal(manifest.provider_neutral, true);
assert.equal(manifest.embedded_ai_model, false);
assert.equal(manifest.billing_required_by_electroia, false);

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
assert.match(fanSvg, /1 · MEDIR TEMPERATURA/);
assert.match(fanSvg, /2 · DECIDIR SIN OSCILAR/);
assert.match(fanSvg, /3 · MOVER EL VENTILADOR/);
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
