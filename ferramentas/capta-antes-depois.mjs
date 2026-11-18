// Gera as imagens do "antes e depois" da casa de banho, a partir da obra 3D do site.
// Uso: node ferramentas/capta-antes-depois.mjs <pasta> [parâmetros da câmara, ex.: "az=28&el=30&d=60"]
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { setTimeout as espera } from "node:timers/promises";

const [pasta, camara = ""] = process.argv.slice(2);
mkdirSync(pasta, { recursive: true });
const porta = 9500 + (process.pid % 400);
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", ["--headless=new", `--remote-debugging-port=${porta}`, `--user-data-dir=${join(tmpdir(), "ad-" + porta)}`,
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

await manda("Emulation.setDeviceMetricsOverride", { width: 1600, height: 1200, deviceScaleFactor: 1, mobile: false });
await manda("Page.navigate", { url: "http://localhost:5181/ferramentas/antes-depois.html?" + camara });
let imagens;
for (let i = 0; i < 120 && !imagens; i++) { await espera(500); imagens = await avalia("window.__imagens"); }
if (!imagens) { console.log("sem imagens"); process.exitCode = 1; }
else for (const [nome, dados] of Object.entries(imagens)) writeFileSync(join(pasta, nome + ".png"), Buffer.from(dados.split(",")[1], "base64"));
ws.close();
chrome.kill();
console.log("ok");
