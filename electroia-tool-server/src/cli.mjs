import { stdin, stdout, stderr } from "node:process";
import { callElectroIATool, manifest } from "./toolkit.mjs";

async function readStdin() {
  const chunks = [];
  for await (const chunk of stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8").trim();
}

try {
  if (process.argv.includes("--manifest")) {
    stdout.write(`${JSON.stringify(manifest, null, 2)}\n`);
  } else {
    const raw = await readStdin();
    if (!raw) throw new Error("Envía por stdin un objeto con tool y arguments");
    const request = JSON.parse(raw);
    const result = await callElectroIATool(request.tool, request.arguments || {});
    stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  }
} catch (error) {
  stderr.write(`ElectroIA: ${error.message}\n`);
  process.exitCode = 1;
}
