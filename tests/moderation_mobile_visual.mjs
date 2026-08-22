import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { extname, join, normalize } from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const root = new URL("../", import.meta.url);
const catalog = JSON.parse(await readFile(new URL("../data/connectors/catalog.json", import.meta.url), "utf8"));
const types = {".html":"text/html; charset=utf-8", ".css":"text/css; charset=utf-8", ".js":"text/javascript; charset=utf-8", ".png":"image/png"};

const server = createServer(async (request, response) => {
  const url = new URL(request.url, "http://127.0.0.1");
  if (url.pathname === "/api/index.php") {
    const action = url.searchParams.get("action");
    const payload = action === "admin-session"
      ? {ok:true, csrf:"visual-token"}
      : action === "admin-connector-catalog"
        ? {ok:true, catalog_version:catalog.catalog_version, records:catalog.records}
        : action === "admin-connector-imports" || action === "admin-list"
          ? {ok:true, items:[]}
          : {ok:false, error:"not_mocked"};
    const body = JSON.stringify(payload);
    response.writeHead(payload.ok ? 200 : 404, {"content-type":"application/json; charset=utf-8"});
    return response.end(body);
  }
  const requested = url.pathname === "/" ? "moderacion.html" : url.pathname.slice(1);
  const safe = normalize(requested).replace(/^(\.\.[/\\])+/, "");
  try {
    const body = await readFile(new URL(safe, root));
    response.writeHead(200, {"content-type":types[extname(safe)] || "application/octet-stream"});
    response.end(body);
  } catch {
    response.writeHead(404).end();
  }
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const {port} = server.address();

const browser = await chromium.launch({headless:true, executablePath:"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", args:["--disable-gpu", "--no-first-run"]});
const page = await browser.newPage({viewport:{width:390, height:844}, deviceScaleFactor:1});
await page.goto(`http://127.0.0.1:${port}/moderacion.html`, {waitUntil:"networkidle"});
assert.equal(await page.locator(".connector-review-card").count(), 17);
assert.equal(await page.locator("#importWorkspace").evaluate(element => getComputedStyle(element).display), "none");
await page.getByLabel("Buscar").fill("USB-C");
assert.equal(await page.locator(".connector-review-card").count(), 1);
await page.locator(".connector-review-card > details > summary").click();
assert.equal(await page.locator(".connector-review-card > details").getAttribute("open"), "");
assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "La mesa genera desplazamiento horizontal en móvil");
await page.screenshot({path:"test-artifacts/moderation-connectors-mobile.png", fullPage:true});
await browser.close();
await new Promise(resolve => server.close(resolve));
process.stdout.write("Connector review desk mobile visual: OK\n");
