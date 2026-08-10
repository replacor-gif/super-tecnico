import assert from "node:assert/strict";
import path from "node:path";
import http from "node:http";
import { mkdir, readFile } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const root = process.cwd();
const mimeTypes = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".json": "application/json", ".svg": "image/svg+xml" };
const server = http.createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
    const target = path.resolve(root, `.${pathname === "/" ? "/calculadoras.html" : pathname}`);
    if (!target.startsWith(root)) throw new Error("Ruta no permitida");
    const data = await readFile(target);
    response.writeHead(200, { "Content-Type": `${mimeTypes[path.extname(target)] || "application/octet-stream"}; charset=utf-8` });
    response.end(data);
  } catch {
    response.writeHead(404);
    response.end("Not found");
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const { port } = server.address();
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  args: ["--no-first-run", "--allow-file-access-from-files"],
});

try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const url = `http://127.0.0.1:${port}/calculadoras.html#/calculadoras/ducts`;
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.locator("#ductMode").waitFor();
  assert.equal(await page.locator("#ductDirectWrap").isVisible(), true);
  assert.equal(await page.locator("#ductRoomWrap").isVisible(), false);
  await page.locator(".calculate").evaluate((button) => button.click());
  await page.waitForTimeout(250);
  if (await page.locator(".result-main").count() === 0) {
    throw new Error(`No se generó el resultado. Panel: ${await page.locator(".result-panel").innerText()} Errores: ${errors.join(" | ")}`);
  }
  assert.match(await page.locator(".result-main").innerText(), /80 × 25 cm/);
  assert.equal(await page.locator(".duct-section-row").count(), 8);
  assert.match(await page.locator(".result-panel").innerText(), /313.*m³\/h/);
  assert.deepEqual(errors, []);
  await mkdir("test-artifacts", { recursive: true });
  await page.screenshot({ path: "test-artifacts/duct-calculator-mobile.png", fullPage: true });
  await page.locator("#ductMode").selectOption("room");
  assert.equal(await page.locator("#ductDirectWrap").isVisible(), false);
  assert.equal(await page.locator("#ductRoomWrap").isVisible(), true);
  await page.locator(".calculate").evaluate((button) => button.click());
  assert.match(await page.locator(".result-panel").innerText(), /1920 m³\/h/);
  process.stdout.write("Duct calculator mobile visual: OK\n");
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
