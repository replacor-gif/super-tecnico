import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, resolve } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const ROOT = resolve(import.meta.dirname, "..");
const mime = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".png": "image/png" };

const server = createServer(async (request, response) => {
  try {
    const pathname = new URL(request.url, "http://127.0.0.1").pathname;
    const path = resolve(ROOT, `.${pathname === "/" ? "/index.html" : pathname}`);
    if (!path.startsWith(ROOT)) throw new Error("invalid path");
    const content = await readFile(path);
    response.writeHead(200, { "Content-Type": mime[extname(path)] || "application/octet-stream" });
    response.end(content);
  } catch (_error) {
    response.writeHead(404).end("Not found");
  }
});
await new Promise((resolveListen) => server.listen(0, "127.0.0.1", resolveListen));
const { port } = server.address();
const base = `http://127.0.0.1:${port}`;
const browser = await chromium.launch({ headless: true, executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", args: ["--disable-gpu", "--no-first-run"] });

try {
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  await desktop.goto(`${base}/actualizaciones.html`, { waitUntil: "networkidle" });
  assert.equal(await desktop.locator(".update-entry").count(), 9);
  assert.equal((await desktop.locator(".update-entry").first().textContent()).includes("Administrador"), true);
  await desktop.screenshot({ path: "test-artifacts/updates-desktop.png", fullPage: true });

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  await mobile.goto(`${base}/index.html`, { waitUntil: "networkidle" });
  assert.equal(await mobile.locator("[data-st-updates-preview] .update-entry").count(), 3);
  await mobile.locator(".portal-updates").screenshot({ path: "test-artifacts/updates-home-mobile.png" });
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}

process.stdout.write("Super Técnico updates visual: desktop and mobile OK\n");
