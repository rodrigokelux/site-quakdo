// A página principal da Quakdo (para clientes): o filme da obra que avança com o scroll, a faixa das áreas,
// o telemóvel da app e a secção dos especialistas. O que é comum às páginas está em comum.js.
// O filme e os patos são imagens feitas no Blender (pasta blender/); aqui só se mostram e animam.
import { iniciaComum, parado, limita, $, $$ } from "./comum.js";
import { iniciaObra } from "./obra3d.js";

// O número de imagens do filme vem de /filme/n.json (o filme interpolado); sem ele, são as 100 do render.
let N_IMAGENS = 100;
// Onde está a obra na imagem (0 a 1): é o ponto que fica sempre à vista quando o ecrã corta o filme.
const FOCO = { x: 0.64, y: 0.5 };
const AREAS = ["Obras", "Cozinhas", "Pintura", "Casas de banho", "Pavimentos", "Canalização", "Eletricidade", "Janelas e portas", "Climatização", "Roupeiros", "Reparações"];

const lenis = iniciaComum();

// ---- A entrada: o título revela-se palavra a palavra logo ao abrir ----
window.setTimeout(() => {
  document.body.classList.add("aberto");
  $(".passos h1")?.classList.add("visivel");
}, parado ? 0 : 150);

// ---- O filme ----
const seccao = $(".filme");
const tela = $("#filme");
const pincel = tela.getContext("2d");
const passos = $$(".passo");
const marcas = $$(".trilho li");
const trilhoCheio = $("#trilho-cheio");
const textosPasso = $$(".passo-texto");
// No telemóvel o texto dos passos não sobe pela página: fica numa legenda presa por baixo da obra e troca de passo
// em passo (os originais continuam na página só para dar o comprimento do scroll).
const legenda = document.createElement("div");
legenda.className = "legenda";
legenda.setAttribute("aria-hidden", "true");
const legendas = textosPasso.map((tx) => {
  const c = tx.cloneNode(true);
  c.classList.add("legenda-item");
  c.querySelectorAll("a").forEach((a) => a.setAttribute("tabindex", "-1"));
  legenda.append(c);
  return c;
});
$(".palco").append(legenda);
// No telemóvel, os quatro passos do filme em barras que se enchem com o scroll (no ecrã largo há a régua do lado).
const barrasFilme = document.createElement("div");
barrasFilme.className = "filme-barras";
barrasFilme.setAttribute("aria-hidden", "true");
barrasFilme.innerHTML = "<i></i><i></i><i></i><i></i>";
$(".palco").append(barrasFilme);
const barras = $$("i", barrasFilme);
let legendaAtiva = -1;
const andamento = $("#andamento");
const barra = $("#barra");
let imagens = [];
let desenhada = "", alvo = 0, atual = 0;

function carrega(i) {
  const img = new Image();
  img.decoding = "async";
  img.src = `/filme/${String(i).padStart(3, "0")}.webp`;
  img.onload = () => { imagens[i] = img; desenhada = ""; };
}
// Primeiro uma em cada quatro (para haver logo filme inteiro), depois as restantes.
// O filme é um vídeo (public/filme.mp4, só imagens-chave): o scroll escolhe o tempo e o browser salta logo para lá.
// O vídeo é descarregado inteiro antes de começar, para os saltos não esperarem pela rede.
// Sem vídeo, usa-se a sequência de imagens em public/filme/.
let video = null, duracao = 0, tempoAtual = 0, tFilme = 0;
// A obra em 3D ao vivo (Three.js). Sem WebGL, fica o vídeo ou a sequência de imagens.
const obra = parado ? null : iniciaObra($(".palco"), { aoPronto: () => { tela.remove(); document.body.classList.add("obra-viva"); } });
let tSuave = 0;
(obra ? Promise.resolve(null) : fetch("/filme.mp4")).then((r) => (r.ok && (r.headers.get("content-type") || "").includes("video") ? r.blob() : null)).catch(() => null).then((b) => {
  if (obra) return;
  if (b) {
    const v = document.createElement("video");
    v.muted = true; v.playsInline = true; v.preload = "auto";
    v.setAttribute("muted", ""); v.setAttribute("playsinline", "");
    v.className = "filme-video";
    v.setAttribute("aria-hidden", "true");
    v.addEventListener("loadeddata", () => {
      duracao = v.duration;
      video = v;
      tela.replaceWith(v);
    }, { once: true });
    v.src = URL.createObjectURL(b);
    v.load();
    return;
  }
  return fetch("/filme/n.json").then((r) => (r.ok ? r.json() : null)).catch(() => null).then((j) => {
  if (j?.n) N_IMAGENS = j.n;
  imagens = new Array(N_IMAGENS);
  // Primeiro uma em cada oito (para haver logo filme inteiro), depois as restantes.
  for (let i = 0; i < N_IMAGENS; i += 8) carrega(i);
  for (let i = 0; i < N_IMAGENS; i++) if (i % 8) carrega(i);
  aoDescer();
  });
});

// A tela ocupa o ecrã todo, à resolução do ecrã; a imagem cobre-a sem deformar, com a obra sempre à vista.
function ajustaTela() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  tela.width = Math.round(tela.clientWidth * dpr);
  tela.height = Math.round(tela.clientHeight * dpr);
  desenhada = "";
}
ajustaTela();
window.addEventListener("resize", ajustaTela);

function mais_proxima(i) {
  for (let d = 0; d < N_IMAGENS; d++) {
    if (imagens[i - d]) return i - d;
    if (imagens[i + d]) return i + d;
  }
  return -1;
}

function poe(img, alfa) {
  const W = tela.width, H = tela.height, iw = img.naturalWidth, ih = img.naturalHeight;
  const estreito = W / H < 1;
  // Em ecrã largo cobre; em ecrã alto (telemóvel) a obra fica maior, presa ao topo do véu.
  const k = estreito ? Math.max(H * 0.62 / ih, W / iw) * 1.35 : Math.max(W / iw, H / ih);
  const w = iw * k, h = ih * k;
  const x = Math.min(0, Math.max(W - w, W * (estreito ? 0.5 : FOCO.x) - w * FOCO.x));
  const y = estreito ? H * 0.36 - h * FOCO.y : Math.min(0, Math.max(H - h, H / 2 - h * FOCO.y));
  pincel.globalAlpha = alfa;
  pincel.drawImage(img, x, y, w, h);
}

function desenha() {
  // Entre duas imagens, mistura-as: o movimento fica contínuo mesmo com o scroll lento.
  const a = mais_proxima(Math.floor(atual));
  if (a < 0) return;
  const b = imagens[a + 1] && a === Math.floor(atual) ? a + 1 : a;
  const mistura = b === a ? 0 : Math.round((atual - a) * 12) / 12;
  const chave = a + ":" + b + ":" + mistura + ":" + tela.width;
  if (chave === desenhada) return;
  pincel.clearRect(0, 0, tela.width, tela.height);
  poe(imagens[a], 1);
  if (mistura > 0) poe(imagens[b], mistura);
  pincel.globalAlpha = 1;
  desenhada = chave;
}

// ---- A faixa das áreas: corre sempre e acelera com o scroll ----
const faixa = $("#faixa");
faixa.innerHTML = Array.from({ length: 2 }, () => AREAS.map((a) => `<span>${a}</span><i>✓</i>`).join("")).join("");
let faixaX = 0, ultimoY = window.scrollY, embalo = 0;

// ---- Deslizes: imagens com data-desliza sobem ou descem um pouco com a página ----
const deslizes = $$("[data-desliza]");

function aoDescer() {
  const r = seccao.getBoundingClientRect();
  // Cada passo marca um momento do filme (data-t) quando o seu meio passa pelo meio do ecrã; entre dois passos,
  // o filme avança em linha reta. Assim a obra anda ao ritmo do texto que vai subindo.
  const meio = window.innerHeight / 2;
  const marcos = passos.map((p, i) => {
    const q = p.getBoundingClientRect();
    return { y: i === 0 ? 0 : q.top + q.height / 2 - meio, t: Number(p.dataset.t) };
  });
  // marcos[i].y é a distância (em px) que falta descer até ao passo i; o primeiro conta a partir do topo.
  const desceu = -r.top;
  const pos = marcos.map((m, i) => (i === 0 ? 0 : desceu + m.y));
  let t = 1;
  for (let i = 0; i < pos.length - 1; i++) {
    if (desceu <= pos[i + 1]) { t = marcos[i].t + (marcos[i + 1].t - marcos[i].t) * limita((desceu - pos[i]) / (pos[i + 1] - pos[i]), 0, 1); break; }
  }
  tFilme = limita(t, 0, 1);
  alvo = tFilme * (N_IMAGENS - 1);
  const passo = pos.filter((y) => desceu >= y - meio * 0.5).length - 2;
  marcas.forEach((m, i) => { m.classList.toggle("feito", i < passo); m.classList.toggle("ativo", i === passo); });
  trilhoCheio.style.scale = `1 ${limita(t, 0, 1)}`;
  // Cada barra enche-se entre o momento do seu passo e o do anterior.
  barras.forEach((bar, i) => {
    const de = marcos[i].t, ate = marcos[i + 1].t;
    bar.style.setProperty("--enche", String(limita((tFilme - de) / (ate - de), 0, 1)));
  });
  seccao.classList.toggle("a-andar", desceu > 40);
  // Telemóvel: a legenda por baixo da obra troca para o passo cujo momento está mais perto (a meio caminho entre dois).
  let k = 0;
  for (let i = 1; i < pos.length; i++) if (desceu >= (pos[i - 1] + pos[i]) / 2) k = i;
  if (k !== legendaAtiva) {
    legendaAtiva = k;
    legendas.forEach((l, i) => {
      l.classList.toggle("ativo", i === k);
      l.querySelectorAll(".revela, [data-palavras]").forEach((e) => e.classList.toggle("visivel", i === k));
    });
  }
  document.body.classList.toggle("no-filme", r.bottom > 70);
  barra.classList.toggle("descida", window.scrollY > 8);
  const total = document.documentElement.scrollHeight - window.innerHeight;
  andamento.style.scale = `${total > 0 ? window.scrollY / total : 0} 1`;
}
aoDescer();
window.addEventListener("scroll", aoDescer, { passive: true });

lenis?.on("scroll", aoDescer);

window.addEventListener("resize", aoDescer);

(function quadro(agora) {
  requestAnimationFrame(quadro);
  lenis?.raf(agora);
  // O filme segue o scroll com um ligeiro atraso, para não dar saltos.
  atual = parado ? alvo : atual + (alvo - atual) * 0.14;
  if (Math.abs(alvo - atual) < 0.01) atual = alvo;
  if (obra) {
    // A obra segue o scroll com um ligeiro atraso, para o movimento ficar contínuo, como um filme.
    tSuave += (tFilme - tSuave) * 0.12;
    if (Math.abs(tFilme - tSuave) < 0.0002) tSuave = tFilme;
    obra.define(tSuave);
  } else if (video) {
    // O tempo do vídeo segue o scroll com um ligeiro atraso; só se pede outro salto quando o anterior acabou.
    const alvoT = tFilme * Math.max(0, duracao - 0.05);
    tempoAtual = parado ? alvoT : tempoAtual + (alvoT - tempoAtual) * 0.16;
    if (!video.seeking && Math.abs(video.currentTime - tempoAtual) > 0.01) video.currentTime = tempoAtual;
  } else desenha();
  if (parado) return;
  const y = window.scrollY;
  embalo += (y - ultimoY - embalo) * 0.1;
  ultimoY = y;
  faixaX -= 0.6 + Math.abs(embalo) * 0.35;
  const meia = faixa.scrollWidth / 2;
  if (meia && -faixaX > meia) faixaX += meia;
  faixa.style.translate = `${faixaX}px 0`;
  faixa.style.transform = `skewX(${limita(-embalo * 0.25, -8, 8)}deg)`;
  for (const el of deslizes) {
    const r = el.parentElement.getBoundingClientRect();
    if (r.bottom < 0 || r.top > window.innerHeight) continue;
    const k = (r.top + r.height / 2 - window.innerHeight / 2) / window.innerHeight;
    el.style.translate = `0 ${k * Number(el.dataset.desliza)}%`;
  }
})();

// ---- Especialistas: a lista troca o pato do palco; avança sozinha até alguém lhe tocar ----
const itens = $$("#esp-lista li");
const patosEsp = $$("#esp-palco img");
const numero = $("#esp-num");
let espAtivo = -1, relogioEsp;
function mostraEsp(i) {
  if (i === espAtivo) return;
  espAtivo = i;
  itens.forEach((li, k) => li.classList.toggle("ativo", k === i));
  patosEsp.forEach((img) => img.classList.toggle("ativo", img.dataset.pato === itens[i].dataset.pato));
  numero.textContent = String(i + 1).padStart(2, "0");
}
function rodaEsp() {
  clearInterval(relogioEsp);
  if (!parado) relogioEsp = setInterval(() => mostraEsp((espAtivo + 1) % itens.length), 4600);
}
itens.forEach((li, i) => {
  const escolhe = () => { mostraEsp(i); rodaEsp(); };
  li.addEventListener("pointerenter", escolhe);
  $("button", li).addEventListener("click", escolhe);
  $("button", li).addEventListener("focus", escolhe);
});
mostraEsp(0);
rodaEsp();

// ---- A app: o item da lista mais perto do meio do ecrã escolhe o ecrã do telemóvel; o telemóvel roda devagar ----
const appSec = $("#app");
const appItens = $$(".app-item");
const appEcras = $$("#telemovel .telemovel-ecra img");
const appNum = $("#app-num");
const telemovel = $("#telemovel");
const appGrelha = $(".app-grelha");
const appPassos = document.createElement("li");
appPassos.className = "app-passos";
appPassos.setAttribute("aria-hidden", "true");
appPassos.innerHTML = appItens.map(() => "<i></i>").join("");
$(".app-lista").prepend(appPassos);
const appSegmentos = $$("i", appPassos);
// No telemóvel, o título da secção fica preso por cima; o telemóvel e o texto arrumam-se por baixo dele.
const appCabeca = $(".app > .largura > .cabeca");
const medeCabeca = () => appGrelha.style.setProperty("--app-cab", `${appCabeca.offsetHeight}px`);
medeCabeca();
window.addEventListener("resize", medeCabeca);
document.fonts?.ready.then(medeCabeca);
let appAtivo = 0;
function veApp() {
  const r = appSec.getBoundingClientRect();
  if (r.bottom < 0 || r.top > window.innerHeight) return;
  // O passo da app vem do quanto já se desceu na grelha (que é alta só para dar este percurso).
  const g = appGrelha.getBoundingClientRect();
  const pg = limita((90 - g.top) / Math.max(1, g.height - window.innerHeight), 0, 0.9999);
  const melhor = Math.floor(pg * appItens.length);
  appSegmentos.forEach((s, i) => s.classList.toggle("feito", i <= melhor));
  const p = limita(-r.top / Math.max(1, r.height - window.innerHeight), 0, 1);
  telemovel.style.setProperty("--gira", `${-16 + p * 30}deg`);
  if (melhor === appAtivo) return;
  appAtivo = melhor;
  appItens.forEach((it, i) => it.classList.toggle("ativo", i === melhor));
  appEcras.forEach((im, i) => im.classList.toggle("ativo", i === melhor));
  appNum.textContent = String(melhor + 1).padStart(2, "0");
}
veApp();
window.addEventListener("scroll", veApp, { passive: true });
window.addEventListener("resize", veApp);

// ---- Antes e depois: a pega corta as duas imagens; ao aparecer, mostra sozinha que se pode arrastar ----
const comparador = $("#comparador");
if (comparador) {
  const controlo = $(".ad-controlo", comparador);
  const poeCorte = (v) => {
    comparador.style.setProperty("--corte", `${v}%`);
    comparador.dataset.lado = v < 12 ? "depois" : v > 88 ? "antes" : "";
  };
  controlo.addEventListener("input", () => { mexeu = true; poeCorte(+controlo.value); });
  let mexeu = false;
  const mostra = new IntersectionObserver(([en]) => {
    if (!en.isIntersecting || parado) return;
    mostra.disconnect();
    const inicio = performance.now();
    (function vai(agora) {
      if (mexeu) return;
      const p = Math.min(1, (agora - inicio) / 2600);
      const v = 50 + Math.sin(p * Math.PI * 2) * 32 * (1 - p);
      controlo.value = v;
      poeCorte(v);
      if (p < 1) requestAnimationFrame(vai);
    })(inicio);
  }, { threshold: 0.6 });
  mostra.observe(comparador);
}
