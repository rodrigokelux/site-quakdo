// Capta os ecrãs da app Quakdo (rota /fluxo, que funciona sem servidor) em alta resolução, só o ecrã do telemóvel.
// Precisa da app a correr em localhost:5174 e do Chrome. Uso: node ferramentas/capta-app.mjs <pasta> B D H ...
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { setTimeout as espera } from "node:timers/promises";

const [pasta, ...passos] = process.argv.slice(2);
mkdirSync(pasta, { recursive: true });
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const porta = 9400 + (process.pid % 400);
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${porta}`, `--user-data-dir=${join(tmpdir(), "capta-" + porta)}`, "--hide-scrollbars", "--no-first-run", "about:blank"], { stdio: "ignore" });

let alvos;
for (let i = 0; i < 60 && !alvos; i++) {
  await espera(250);
  try { alvos = await (await fetch(`http://127.0.0.1:${porta}/json`)).json(); } catch {}
}
const ws = new WebSocket(alvos.find((a) => a.type === "page").webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let id = 0;
const pendentes = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pendentes.has(m.id)) { pendentes.get(m.id)(m); pendentes.delete(m.id); } });
const manda = (method, params = {}) => new Promise((r) => { const n = ++id; pendentes.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });

await manda("Emulation.setDeviceMetricsOverride", { width: 1400, height: 1100, deviceScaleFactor: 3, mobile: false });
for (const p of passos) {
  await manda("Page.navigate", { url: `http://localhost:5174/fluxo?c=${p}#${p}` });
  await espera(3500);
  const r = await manda("Runtime.evaluate", {
    expression: `(() => { const el = document.querySelector("figure > div.relative"); const q = el.getBoundingClientRect(); const b = 10; return JSON.stringify({ x: q.x + b, y: q.y + b, w: q.width - 2 * b, h: q.height - 2 * b }); })()`,
    returnByValue: true,
  });
  const q = JSON.parse(r.result.result.value);
  const foto = await manda("Page.captureScreenshot", { format: "png", clip: { x: q.x, y: q.y, width: q.w, height: q.h, scale: 1 }, captureBeyondViewport: false });
  writeFileSync(join(pasta, `${p}.png`), Buffer.from(foto.result.data, "base64"));
  console.log("captado", p, Math.round(q.w), "x", Math.round(q.h));
}
ws.close();
chrome.kill();
