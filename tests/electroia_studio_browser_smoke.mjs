import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const origin = process.env.ELECTROIA_TEST_ORIGIN || "http://127.0.0.1:8097";
const defaultWindowsChrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const executablePath = process.env.ELECTROIA_BROWSER_PATH
  || (process.platform === "win32" && existsSync(defaultWindowsChrome) ? defaultWindowsChrome : undefined);
const browser = await chromium.launch({
  headless: true,
  ...(executablePath ? { executablePath } : {}),
});

try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto(`${origin}/archivo-tecnico-47097e44267b9cb111636b84823f1d47/`, { waitUntil: "networkidle" });
  await page.evaluate(() => enterPrivateLab());
  await page.getByRole("button", { name: /Diseño desde cualquier IA/ }).click();
  await page.waitForFunction(() => document.querySelectorAll("#benchmarkCase option").length === 20);
  await page.selectOption("#benchmarkCase", "AUT-001");
  await page.click("#loadBenchmarkCase");
  await page.click("#renderAiDocument");
  await page.waitForSelector("#resultView.active #schematic svg.electroia-core-diagram");

  assert.match(await page.locator("#aiBridgeStatus").innerText(), /ESPECIFICACIÓN COMPILADA/);
  assert.match(await page.locator("#schematic svg").getAttribute("data-engine-version"), /^1\.16\./);
  assert.match(await page.locator("#layoutEditorMetrics").innerText(), /0 solapes · 0 cables sobre símbolos/);

  const before = await page.locator("#schematic svg").innerHTML();
  await page.click("#toggleLayoutEditor");
  await page.locator("#schematic g.component").first().click();
  assert.notEqual(await page.locator("#selectedComponentLabel").innerText(), "Toca un símbolo");
  await page.locator('[data-move-x="1"][data-move-y="0"]').click();
  const after = await page.locator("#schematic svg").innerHTML();
  assert.notEqual(after, before, "Mover un símbolo debe regenerar el plano");
  assert.equal(pageErrors.length, 0, pageErrors.join("\n"));
  console.log("ElectroIA Studio mobile browser smoke: OK · compilación IA + banco 20 + ajuste táctil");
} finally {
  await browser.close();
}
