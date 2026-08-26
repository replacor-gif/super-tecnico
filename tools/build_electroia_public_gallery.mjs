#!/usr/bin/env node
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const EXAMPLES = join(ROOT, "data", "electroia", "examples");
const OUTPUT_DIRECTORY = join(ROOT, "assets", "electroia-gallery");
const OUTPUT_MANIFEST = join(ROOT, "data", "electroia", "public-gallery.json");
const core = require(join(ROOT, "archivo-tecnico-47097e44267b9cb111636b84823f1d47", "diagram-core.js"));

const dangerousWarningCodes = new Set([
  "COMPONENT_OVERLAP",
  "EARTH_DOMAIN_MIX",
  "EXACT_MODEL_REQUIRED",
  "NET_ROLE_MISMATCH",
  "OUTPUT_CONTENTION",
  "SIGNAL_POWER_DOMAIN_MIX",
  "WIRE_THROUGH_COMPONENT",
]);

function kindLabel(kind) {
  return {
    circuit_diagram: "Circuito electrónico",
    single_line_diagram: "Esquema unifilar",
    multi_line_diagram: "Esquema multifilar",
  }[kind] || "Diagrama técnico";
}

function asStandaloneSvg(svg) {
  const content = svg.trim();
  if (!content.startsWith("<svg ")) throw new Error("El motor no ha devuelto un SVG válido");
  return content.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ');
}

async function buildGallery() {
  const files = (await readdir(EXAMPLES)).filter((name) => name.endsWith(".json")).sort();
  if (files.length < 5) throw new Error(`Se esperaban al menos 5 planos patrón y hay ${files.length}`);
  await mkdir(OUTPUT_DIRECTORY, { recursive: true });

  const items = [];
  for (const filename of files) {
    const sourcePath = join(EXAMPLES, filename);
    const document = JSON.parse(await readFile(sourcePath, "utf8"));
    const rendered = core.render(document);
    const metrics = rendered.diagnostics.metrics;
    const warningCodes = rendered.diagnostics.warnings.map((item) => item.code);
    const dangerousWarnings = warningCodes.filter((code) => dangerousWarningCodes.has(code));
    if (rendered.diagnostics.errors.length || dangerousWarnings.length || metrics.component_overlaps || metrics.wire_component_conflicts || metrics.off_grid_terminals || metrics.single_canvas !== true) {
      throw new Error(`El plano ${filename} no supera la puerta de publicación`);
    }

    const slug = basename(filename, ".json");
    const svgFile = `${slug}.svg`;
    await writeFile(join(OUTPUT_DIRECTORY, svgFile), `${asStandaloneSvg(rendered.svg)}\n`, "utf8");
    items.push({
      id: document.document_id,
      title: document.title,
      document_kind: document.document_kind,
      document_kind_label: kindLabel(document.document_kind),
      standard_profile: document.standard_profile,
      revision: document.revision || "A",
      components: metrics.symbols,
      nets: metrics.nets,
      terminals: metrics.terminals,
      pages: metrics.pages,
      single_canvas: metrics.single_canvas,
      validation: {
        errors: rendered.diagnostics.errors.length,
        dangerous_warnings: dangerousWarnings.length,
        component_overlaps: metrics.component_overlaps,
        wire_component_conflicts: metrics.wire_component_conflicts,
        off_grid_terminals: metrics.off_grid_terminals,
      },
      image: `assets/electroia-gallery/${svgFile}`,
      source: `data/electroia/examples/${filename}`,
    });
  }

  return {
    schema_version: "1.0",
    generated_on: "2026-08-26",
    engine_version: core.getContract().engine_version,
    status: "automated_review_passed_field_validation_pending",
    notice: "Los ejemplos superan las puertas automáticas del motor, pero no sustituyen la revisión profesional ni cuentan todavía como validación de campo.",
    count: items.length,
    items,
  };
}

const gallery = await buildGallery();
const content = `${JSON.stringify(gallery, null, 2)}\n`;
if (process.argv.includes("--check")) {
  const existing = await readFile(OUTPUT_MANIFEST, "utf8").catch(() => "");
  if (existing !== content) throw new Error("data/electroia/public-gallery.json está desactualizado");
  for (const item of gallery.items) {
    const generated = await readFile(join(ROOT, item.image), "utf8").catch(() => "");
    const document = JSON.parse(await readFile(join(ROOT, item.source), "utf8"));
    const expected = `${asStandaloneSvg(core.render(document).svg)}\n`;
    if (generated !== expected) throw new Error(`${item.image} está desactualizado`);
  }
} else {
  await writeFile(OUTPUT_MANIFEST, content, "utf8");
}
process.stdout.write(`ElectroIA public gallery: ${gallery.count} reviewed single-canvas diagrams\n`);
