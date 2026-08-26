import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const port = Number(process.env.ST_BACKLOG_TEST_PORT || 8766);
const items = [
  { id: 3, item_type: "bug", area: "ElectroIA", title: "Evitar cruces en planos grandes", details: "Añadir más casos reales de cuadros con maniobra y control.", priority: "urgent", status: "in_progress", author_alias: "Administrador", created_at: "2026-08-23 10:00:00", updated_at: "2026-08-23 18:00:00", completed_at: null },
  { id: 2, item_type: "improvement", area: "Conductos", title: "Afinar movimiento táctil de rejillas", details: "Comprobar arrastre con un dedo y recálculo inmediato.", priority: "high", status: "pending", author_alias: "Administrador", created_at: "2026-08-23 09:00:00", updated_at: "2026-08-23 17:00:00", completed_at: null },
  { id: 1, item_type: "content", area: "Normativa", title: "Convertir consultas repetidas en reglas revisadas", details: "Guardar ámbito, excepciones y fuente exacta.", priority: "normal", status: "done", author_alias: "Administrador", created_at: "2026-08-22 09:00:00", updated_at: "2026-08-23 16:00:00", completed_at: "2026-08-23 16:00:00" },
];
const proposals = [
  { id: 12, nickname: "Técnico Málaga", description: "Haría más grande el botón de guardar en el móvil.", language: "es", source_page: "feedback.html", created_at: "2026-08-26 09:30:00" },
  { id: 11, nickname: "Usuario anónimo", description: "Añadir una guía rápida para las rejillas.", language: "es", source_page: "conductos.html", created_at: "2026-08-26 08:10:00" },
];

function json(response, status, payload) {
  response.writeHead(status, { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
  response.end(JSON.stringify(payload));
}

function counts() {
  return items.reduce((result, item) => { result[item.status] = (result[item.status] || 0) + 1; return result; }, { pending: 0, in_progress: 0, done: 0, archived: 0 });
}

function body(request) {
  return new Promise((resolve, reject) => {
    let raw = "";
    request.on("data", chunk => { raw += chunk; if (raw.length > 100000) reject(new Error("too_large")); });
    request.on("end", () => { try { resolve(JSON.parse(raw || "{}")); } catch (error) { reject(error); } });
    request.on("error", reject);
  });
}

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url || "/", `http://${request.headers.host || "127.0.0.1"}`);
    if (url.pathname === "/api/index.php") {
      const action = url.searchParams.get("action");
      if (action === "electroia-access") return json(response, 200, { ok: true, required: false, unlocked: true });
      if (action === "private-backlog" && request.method === "GET") {
        const status = url.searchParams.get("status");
        return json(response, 200, { ok: true, items: status && status !== "all" ? items.filter(item => item.status === status) : items, counts: counts(), privacy: "test" });
      }
      if (action === "private-backlog" && request.method === "POST") {
        const input = await body(request);
        items.unshift({ id: Math.max(...items.map(item => item.id)) + 1, item_type: input.item_type, area: input.area, title: input.title, details: input.details || null, priority: input.priority, status: "pending", author_alias: "Administrador", created_at: "2026-08-23 19:00:00", updated_at: "2026-08-23 19:00:00", completed_at: null });
        return json(response, 201, { ok: true, id: items[0].id, status: "pending" });
      }
      if (action === "private-backlog-update" && request.method === "POST") {
        const input = await body(request);
        const item = items.find(row => row.id === Number(input.id));
        if (!item) return json(response, 404, { ok: false, error: "not_found" });
        Object.assign(item, input, { updated_at: "2026-08-23 19:05:00" });
        return json(response, 200, { ok: true, id: item.id, status: item.status });
      }
      if (action === "private-backlog-delete" && request.method === "POST") {
        const input = await body(request); const index = items.findIndex(row => row.id === Number(input.id));
        if (index < 0) return json(response, 404, { ok: false, error: "not_found" });
        items.splice(index, 1); return json(response, 200, { ok: true, deleted: true });
      }
      if (action === "proposals" && request.method === "GET") return json(response, 200, { ok: true, items: proposals });
      if (action === "proposal-submit" && request.method === "POST") {
        const input = await body(request); const id = Math.max(...proposals.map(item => item.id), 0) + 1;
        proposals.unshift({ id, nickname: input.nickname || "Usuario anónimo", description: input.comment || "Aportación sin comentario.", language: input.language || "es", source_page: input.source_page || null, created_at: "2026-08-26 10:00:00" });
        return json(response, 201, { ok: true, id, status: "pending" });
      }
      if (action === "private-proposal-delete" && request.method === "POST") {
        const input = await body(request); const index = proposals.findIndex(row => row.id === Number(input.id));
        if (index < 0) return json(response, 404, { ok: false, error: "not_found" });
        proposals.splice(index, 1); return json(response, 200, { ok: true, deleted: true });
      }
      return json(response, 404, { ok: false, error: "not_found" });
    }
    const requested = url.pathname === "/" ? "index.html" : decodeURIComponent(url.pathname.slice(1));
    const safe = normalize(join(root, requested));
    if (relative(root, safe).startsWith("..")) return json(response, 403, { ok: false });
    const info = await stat(safe);
    const file = info.isDirectory() ? join(safe, "index.html") : safe;
    const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml" };
    response.writeHead(200, { "content-type": types[extname(file).toLowerCase()] || "application/octet-stream" });
    response.end(await readFile(file));
  } catch (_) {
    json(response, 404, { ok: false, error: "not_found" });
  }
});

server.listen(port, "127.0.0.1", () => process.stdout.write(`Backlog test server http://127.0.0.1:${port}\n`));
