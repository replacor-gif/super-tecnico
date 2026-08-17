import assert from "node:assert/strict";
import { createServer } from "node:http";
import { mkdir, readFile } from "node:fs/promises";
import { extname, resolve } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const ROOT = resolve(import.meta.dirname, "..");
const ARTIFACTS = resolve(ROOT, "test-artifacts");
const mime = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8" };

await mkdir(ARTIFACTS, { recursive: true });
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

async function verify(viewport, filename) {
  const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(`http://127.0.0.1:${port}/tuberias-frigorificas.html`, { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelectorAll("#rpRefrigerant option").length >= 20);
  await page.locator("#rpExample").click();
  await page.locator("#rpResults:not([hidden])").waitFor();
  assert.equal(await page.locator("#rpDiagram svg").count(), 1);
  assert((await page.locator("#rpMeasurements tr").count()) >= 5);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1), true);
  assert.deepEqual(errors, []);
  await page.screenshot({ path: resolve(ARTIFACTS, filename), fullPage: true });
  await page.close();
}

try {
  await verify({ width: 1440, height: 1000 }, "refrigerant-piping-desktop.png");
  await verify({ width: 390, height: 844 }, "refrigerant-piping-mobile.png");
} finally {
  await browser.close();
  await new Promise(resolveClose => server.close(resolveClose));
}

process.stdout.write("Refrigerant piping visual: desktop and mobile OK\n");
