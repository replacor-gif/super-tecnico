#!/usr/bin/env node
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";

const ROOT = resolve(process.argv[2] || ".");
const PORT = Number(process.argv[3] || 8768);
const overrides = new Map();
const mime = {
  ".css": "text/css; charset=utf-8", ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
  ".png": "image/png", ".svg": "image/svg+xml; charset=utf-8",
};

function json(response, payload, status = 200) {
  response.writeHead(status, { "content-type": mime[".json"], "cache-control": "no-store" });
  response.end(JSON.stringify(payload));
}

function readBody(request) {
  return new Promise((resolveBody, reject) => {
    let raw = "";
    request.on("data", chunk => { raw += chunk; });
    request.on("end", () => {
      try { resolveBody(JSON.parse(raw || "{}")); } catch (error) { reject(error); }
    });
    request.on("error", reject);
  });
}

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url || "/", `http://127.0.0.1:${PORT}`);
    if (url.pathname === "/api/index.php") {
      const action = url.searchParams.get("action");
      if (action === "electroia-access") return json(response, { ok: true, required: false, unlocked: true });
      if (action === "content-overrides") return json(response, { ok: true, items: Object.fromEntries(overrides) });
      if (action === "content-editor" && request.method === "GET") {
        const items = [...overrides].map(([content_key, value_text], index) => ({ id: index + 1, content_key, value_text }));
        return json(response, { ok: true, items });
      }
      if (action === "content-editor" && request.method === "POST") {
        const input = await readBody(request);
        overrides.set(String(input.content_key || ""), String(input.value_text || ""));
        return json(response, { ok: true, content_key: input.content_key });
      }
      if (action === "content-editor-delete" && request.method === "POST") {
        const input = await readBody(request);
        overrides.delete(String(input.content_key || ""));
        return json(response, { ok: true, deleted: true });
      }
      return json(response, { ok: false, error: "not_found" }, 404);
    }

    const pathname = decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname);
    const file = resolve(ROOT, `.${pathname}`);
    if (file !== ROOT && !file.startsWith(`${ROOT}${sep}`)) throw new Error("invalid path");
    const details = await stat(file);
    if (!details.isFile()) throw new Error("not a file");
    response.writeHead(200, { "content-type": mime[extname(file).toLowerCase()] || "application/octet-stream", "cache-control": "no-store" });
    response.end(await readFile(file));
  } catch (_) {
    json(response, { ok: false, error: "not_found" }, 404);
  }
});

server.listen(PORT, "127.0.0.1", () => process.stdout.write(`Content editor test server http://127.0.0.1:${PORT}\n`));
