#!/usr/bin/env node
import { readFile, readdir, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUTPUT = join(ROOT, "data", "electroia", "public-release-readiness.json");
const core = require(join(ROOT, "archivo-tecnico-47097e44267b9cb111636b84823f1d47", "diagram-core.js"));

async function readJson(relativePath) {
  return JSON.parse(await readFile(join(ROOT, relativePath), "utf8"));
}

function gate(id, passed, evidence) {
  return { id, passed: Boolean(passed), evidence };
}

async function buildReport() {
  const [engineAudit, manifest, discovery, openapi, hiddenHtml, apiSource, electroiaApiSource] = await Promise.all([
    readJson("data/electroia/engine-audit-report.json"),
    readJson("data/electroia/tool-manifest.json"),
    readJson("data/electroia/discovery.json"),
    readJson("data/electroia/discovery.openapi.json"),
    readFile(join(ROOT, "archivo-tecnico-47097e44267b9cb111636b84823f1d47", "index.html"), "utf8"),
    readFile(join(ROOT, "api", "index.php"), "utf8"),
    readFile(join(ROOT, "api", "electroia.php"), "utf8"),
  ]);

  const exampleDirectory = join(ROOT, "data", "electroia", "examples");
  const exampleFiles = (await readdir(exampleDirectory)).filter((name) => name.endsWith(".json")).sort();
  const dangerousWarningCodes = new Set([
    "COMPONENT_OVERLAP",
    "EARTH_DOMAIN_MIX",
    "EXACT_MODEL_REQUIRED",
    "NET_ROLE_MISMATCH",
    "OUTPUT_CONTENTION",
    "SIGNAL_POWER_DOMAIN_MIX",
    "WIRE_THROUGH_COMPONENT",
  ]);
  const examples = [];
  for (const filename of exampleFiles) {
    const document = await readJson(`data/electroia/examples/${filename}`);
    const rendered = core.render(document);
    const warningCodes = rendered.diagnostics.warnings.map((item) => item.code);
    const dangerousWarnings = warningCodes.filter((code) => dangerousWarningCodes.has(code));
    examples.push({
      id: document.document_id,
      file: filename,
      title: document.title,
      document_kind: document.document_kind,
      components: rendered.diagnostics.metrics.symbols,
      nets: rendered.diagnostics.metrics.nets,
      errors: rendered.diagnostics.errors.length,
      warnings: warningCodes.length,
      dangerous_warnings: dangerousWarnings,
      component_overlaps: rendered.diagnostics.metrics.component_overlaps,
      wire_component_conflicts: rendered.diagnostics.metrics.wire_component_conflicts,
      off_grid_terminals: rendered.diagnostics.metrics.off_grid_terminals,
      single_canvas: rendered.diagnostics.metrics.single_canvas,
    });
  }

  const openapiText = JSON.stringify(openapi);
  const technicalGates = [
    gate("engine_audit_passes", engineAudit.status === "pass" && engineAudit.summary?.fatal_failures === 0, `${engineAudit.summary?.fatal_failures ?? "?"} fallos críticos`),
    gate("public_symbols_reviewed", manifest.capabilities?.reviewed_catalog_symbol_count === manifest.capabilities?.catalog_symbol_count && manifest.capabilities?.auto_draft_catalog_symbol_count === 0, `${manifest.capabilities?.reviewed_catalog_symbol_count ?? 0}/${manifest.capabilities?.catalog_symbol_count ?? 0} revisados`),
    gate("five_professional_examples", examples.length >= 5, `${examples.length} planos patrón`),
    gate("examples_have_no_validation_errors", examples.every((item) => item.errors === 0), `${examples.reduce((sum, item) => sum + item.errors, 0)} errores`),
    gate("examples_have_no_dangerous_warnings", examples.every((item) => item.dangerous_warnings.length === 0), `${examples.reduce((sum, item) => sum + item.dangerous_warnings.length, 0)} avisos peligrosos`),
    gate("examples_have_no_component_overlaps", examples.every((item) => item.component_overlaps === 0), `${examples.reduce((sum, item) => sum + item.component_overlaps, 0)} solapes`),
    gate("examples_have_no_wire_component_conflicts", examples.every((item) => item.wire_component_conflicts === 0), `${examples.reduce((sum, item) => sum + item.wire_component_conflicts, 0)} cruces por componentes`),
    gate("examples_stay_on_grid", examples.every((item) => item.off_grid_terminals === 0), `${examples.reduce((sum, item) => sum + item.off_grid_terminals, 0)} terminales fuera de rejilla`),
    gate("examples_use_single_canvas", examples.every((item) => item.single_canvas === true), `${examples.filter((item) => item.single_canvas).length}/${examples.length} en lienzo único`),
  ];
  const exposureGates = [
    gate("private_preview_is_noindex", hiddenHtml.includes("noindex,nofollow,noarchive,nosnippet,noimageindex"), "laboratorio excluido de buscadores"),
    gate("private_execution_requires_access", apiSource.includes("st_require_electroia_access();") && electroiaApiSource.includes("password_verify"), "ejecución protegida por servidor"),
    gate("openapi_does_not_expose_render", !openapiText.includes("electroia_render_diagram"), "solo consulta pública de estado y catálogo"),
    gate("raw_images_are_not_claimed_as_supported", Array.isArray(manifest.capabilities?.raw_inputs_not_yet_supported) && manifest.capabilities.raw_inputs_not_yet_supported.includes("raw_photo"), "foto y boceto se declaran pendientes"),
    gate("remote_execution_remains_disabled", discovery.security?.remote_public_execution === false, "motor remoto no abierto"),
  ];
  const automatedGatesPass = [...technicalGates, ...exposureGates].every((item) => item.passed);

  return {
    schema_version: "1.0",
    generated_on: "2026-08-24",
    engine_version: manifest.diagram_engine_version,
    release_stage: automatedGatesPass ? "private_release_candidate" : "engineering_blocked",
    decision: automatedGatesPass ? "keep_execution_private_until_field_validation" : "do_not_publish",
    summary: {
      automated_gates_pass: automatedGatesPass,
      public_information_surface_ready: automatedGatesPass,
      private_human_preview_ready: automatedGatesPass,
      public_execution_ready: false,
      reviewed_symbols: manifest.capabilities?.reviewed_catalog_symbol_count ?? 0,
      professional_examples: examples.length,
      example_components: examples.reduce((sum, item) => sum + item.components, 0),
      example_nets: examples.reduce((sum, item) => sum + item.nets, 0),
      component_overlaps: examples.reduce((sum, item) => sum + item.component_overlaps, 0),
      wire_component_conflicts: examples.reduce((sum, item) => sum + item.wire_component_conflicts, 0),
      dangerous_warnings: examples.reduce((sum, item) => sum + item.dangerous_warnings.length, 0),
    },
    automated_gates: {
      technical_quality: technicalGates,
      safe_exposure: exposureGates,
    },
    manual_release_blockers: [
      {
        id: "FIELD_VALIDATION_REQUIRED",
        owner: "Administrador y técnicos colaboradores",
        exit_criteria: "Validar en móvil al menos 20 esquemas reales de cuatro ámbitos: cuadros, automatización, electrónica HVAC y sistemas embebidos.",
      },
      {
        id: "IEC_PROFILE_REMAINS_EXPERIMENTAL",
        owner: "ElectroIA",
        exit_criteria: "Separar reglas gráficas generales de los perfiles documentales y verificar el perfil usado para cada clase de esquema.",
      },
      {
        id: "PUBLIC_EXECUTION_GUARDRAILS_REQUIRED",
        owner: "Super Técnico",
        exit_criteria: "Añadir autenticación por clave, cuotas, límites de tamaño, registro de diagnósticos y apagado de emergencia antes de ofrecer renderizado remoto.",
      },
    ],
    allowed_public_scope_now: [
      "estado y capacidades resumidas",
      "búsqueda limitada de símbolos revisados",
      "contrato JSON y ejemplos profesionales revisados",
      "documentación para integrar el servidor MCP local",
    ],
    forbidden_public_scope_now: [
      "ejecución HTTP anónima del renderizador",
      "prometer esquemas listos para montaje sin revisión técnica",
      "interpretar fotos o bocetos directamente",
      "inferir pinouts de bloques funcionales sin modelo exacto",
    ],
    examples,
  };
}

const report = await buildReport();
const content = `${JSON.stringify(report, null, 2)}\n`;
if (process.argv.includes("--check")) {
  const existing = await readFile(OUTPUT, "utf8").catch(() => "");
  if (existing !== content) throw new Error("data/electroia/public-release-readiness.json está desactualizado");
} else {
  await writeFile(OUTPUT, content, "utf8");
}
if (!report.summary.automated_gates_pass) {
  throw new Error("ElectroIA no supera las puertas automáticas de publicación");
}
process.stdout.write(`ElectroIA release gates: ${report.summary.professional_examples} examples, 0 layout conflicts, private execution preserved\n`);
