import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, resolve } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const ROOT = resolve(import.meta.dirname, "..");
const mime = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webmanifest": "application/manifest+json; charset=utf-8",
  ".png": "image/png",
};

const server = createServer(async (request, response) => {
  try {
    const pathname = new URL(request.url, "http://127.0.0.1").pathname;
    const filePath = resolve(ROOT, `.${pathname === "/" ? "/index.html" : pathname}`);
    if (!filePath.startsWith(ROOT)) throw new Error("invalid path");
    const content = await readFile(filePath);
    response.writeHead(200, { "Content-Type": mime[extname(filePath)] || "application/octet-stream" });
    response.end(content);
  } catch (_error) {
    response.writeHead(404).end("Not found");
  }
});

await new Promise(resolveListen => server.listen(0, "127.0.0.1", resolveListen));
const { port } = server.address();
const browser = await chromium.launch({ headless: true, executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", args: ["--disable-gpu", "--no-first-run"] });
const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", error => errors.push(error.message));

try {
  await page.goto(`http://127.0.0.1:${port}/index.html`, { waitUntil: "networkidle" });
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload({ waitUntil: "networkidle" });
  assert.equal(await page.evaluate(() => Boolean(navigator.serviceWorker.controller)), true);

  await context.setOffline(true);
  await page.goto(`http://127.0.0.1:${port}/proyectos.html`, { waitUntil: "domcontentloaded" });
  await page.locator("#projectCreateForm").waitFor();
  assert.match(await page.locator("h1").innerText(), /proyecto técnico/i);
  assert.equal(await page.locator("link[rel=manifest]").count(), 1);
  assert.deepEqual(errors, []);
} finally {
  await context.setOffline(false);
  await browser.close();
  await new Promise(resolveClose => server.close(resolveClose));
}

process.stdout.write("Super Técnico PWA: project workspace available offline OK\n");
