// Fotografa o site em vários pontos do scroll, com o Chrome invisível (para rever sem o browser à frente).
// Uso: node ferramentas/fotografa-site.mjs <pasta> <largura> <altura> <passo1> <passo2> ...
// Cada passo é um número: o índice do passo do filme (0 a 4), ou "#id" de uma secção, ou "y=1234".
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { setTimeout as espera } from "node:timers/promises";

const [pasta, L, A, ...pontos] = process.argv.slice(2);
mkdirSync(pasta, { recursive: true });
const porta = 9500 + (process.pid % 400);
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", ["--headless=new", `--remote-debugging-port=${porta}`, `--user-data-dir=${join(tmpdir(), "foto-" + porta)}`,
  "--hide-scrollbars", "--no-first-run", "--enable-unsafe-swiftshader", "--use-angle=swiftshader", "about:blank"], { stdio: "ignore" });
let alvos;
for (let i = 0; i < 60 && !alvos; i++) { await espera(250); try { alvos = await (await fetch(`http://127.0.0.1:${porta}/json`)).json(); } catch {} }
const ws = new WebSocket(alvos.find((a) => a.type === "page").webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let id = 0;
const pend = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const manda = (method, params = {}) => new Promise((r) => { const n = ++id; pend.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
const avalia = async (expression) => (await manda("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result?.result?.value;

await manda("Emulation.setDeviceMetricsOverride", { width: +L, height: +A, deviceScaleFactor: 1, mobile: +L < 700 });
await manda("Page.navigate", { url: "http://localhost:5181/" + (process.env.PAGINA || "") });
await espera(9000);
let n = 0;
for (const p of pontos) {
  const js = p.startsWith("#") ? `document.querySelector("${p}").offsetTop + 2`
    : p.startsWith("y=") ? p.slice(2)
    : `(() => { const q = [...document.querySelectorAll(".passo")][${p}]; return q.offsetTop + q.offsetHeight / 2 - innerHeight / 2; })()`;
  await avalia(`window.scrollTo(0, ${js}); 1`);
  await espera(+process.env.ESPERA || 2500);
  const f = await manda("Page.captureScreenshot", { format: "jpeg", quality: 80 });
  writeFileSync(join(pasta, `${String(n++).padStart(2, "0")}-${p.replace(/[^a-z0-9]+/gi, "").slice(0, 24)}.jpg`), Buffer.from(f.result.data, "base64"));
}
console.log("erros:", await avalia("JSON.stringify(window.__erros || [])"));
ws.close();
chrome.kill();
