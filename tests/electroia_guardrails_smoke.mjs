import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const core = require(join(root, "archivo-tecnico-47097e44267b9cb111636b84823f1d47", "diagram-core.js"));

const contract = core.getContract();
assert.deepEqual(contract.limits, {
  request_body_bytes: 262144,
  components_per_document: 200,
  nets_per_document: 400,
  connections_per_net: 100,
  total_connections: 2000,
});

const oversized = {
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "Documento que debe rechazarse por límites",
  components: Array.from({ length: 201 }, (_, index) => ({ ref: `R${index + 1}`, symbol_id: "SYM-0001" })),
  nets: [{ id: "N1", connections: ["R1.1", "R2.1"] }],
};
const componentResult = core.validate(oversized);
assert.equal(componentResult.valid, false);
assert.ok(componentResult.errors.some((item) => item.code === "COMPONENT_LIMIT"));

const huge = {
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "Documento demasiado grande",
  notes: ["x".repeat(270000)],
  components: [{ ref: "R1", symbol_id: "SYM-0001" }],
  nets: [{ id: "N1", connections: ["R1.1"] }],
};
const sizeResult = core.validate(huge);
assert.equal(sizeResult.valid, false);
assert.ok(sizeResult.errors.some((item) => item.code === "DOCUMENT_TOO_LARGE"));

process.stdout.write("ElectroIA guardrails smoke: OK\n");
