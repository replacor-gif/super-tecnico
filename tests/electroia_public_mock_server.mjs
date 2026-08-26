#!/usr/bin/env node
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";

const ROOT = resolve(process.argv[2] || "dist");
const PORT = Number(process.argv[3] || 8767);
const library = JSON.parse(await readFile(resolve(ROOT, "data/electroia/symbol-library.json"), "utf8"));
const release = JSON.parse(await readFile(resolve(ROOT, "data/electroia/public-release-readiness.json"), "utf8"));
const mime = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml; charset=utf-8",
  ".webmanifest": "application/manifest+json; charset=utf-8",
};

function normalize(value) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase().replace(/[^A-Z0-9]+/g, " ").trim();
}

function json(response, payload, status = 200) {
  response.writeHead(status, { "Content-Type": mime[".json"], "Cache-Control": "no-store" });
  response.end(JSON.stringify(payload));
}

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url, `http://127.0.0.1:${PORT}`);
    const action = url.searchParams.get("action");
    if (url.pathname === "/api/index.php" && action === "electroia-public-status") {
      json(response, {
        ok: true,
        public_execution_available: false,
        public_showcase_available: true,
        quality: {
          reviewed_symbols: release.summary.reviewed_symbols,
          professional_examples: release.summary.professional_examples,
          component_overlaps: release.summary.component_overlaps,
          wire_component_conflicts: release.summary.wire_component_conflicts,
          dangerous_warnings: release.summary.dangerous_warnings,
        },
      });
      return;
    }
    if (url.pathname === "/api/index.php" && action === "electroia-symbol-search") {
      const query = url.searchParams.get("q") || "";
      const terms = normalize(query).split(" ").filter((term) => term.length > 1);
      const all = library.symbols.filter((item) => {
        if (!item.catalog_id || item.review_status !== "engine_reviewed") return false;
        const haystack = normalize([item.id, item.name, item.category, item.subcategory, item.aliases, item.keywords, item.description].join(" "));
        return terms.length && terms.every((term) => haystack.includes(term));
      });
      const items = all.slice(0, 8).map((item) => ({
        id: item.id,
        name: item.name,
        category: item.category,
        subcategory: item.subcategory,
        designator: item.designator,
        terminal_names: Object.keys(item.ports || {}),
        terminal_count: Object.keys(item.ports || {}).length,
        terminal_model: item.terminal_model,
        requires_exact_model: item.requires_exact_model === true,
      }));
      json(response, { ok: true, query, total: all.length, limit: 8, items });
      return;
    }

    const pathname = decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname);
    const file = resolve(ROOT, `.${pathname}`);
    if (file !== ROOT && !file.startsWith(`${ROOT}${sep}`)) throw new Error("invalid path");
    const details = await stat(file);
    if (!details.isFile()) throw new Error("not a file");
    const body = await readFile(file);
    response.writeHead(200, { "Content-Type": mime[extname(file).toLowerCase()] || "application/octet-stream", "Cache-Control": "no-store" });
    response.end(body);
  } catch (_) {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
});

server.listen(PORT, "127.0.0.1", () => process.stdout.write(`ElectroIA preview http://127.0.0.1:${PORT}/electroia.html\n`));
