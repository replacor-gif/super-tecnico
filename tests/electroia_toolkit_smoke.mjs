import assert from "node:assert/strict";
import { callElectroIATool, manifest } from "../electroia-tool-server/src/toolkit.mjs";

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

process.stdout.write("ElectroIA provider-neutral toolkit smoke: OK\n");
