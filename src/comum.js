// O que as páginas da Quakdo partilham: os títulos que se revelam palavra a palavra, as entradas ao descer,
// o scroll suave, o cursor em losango, os botões magnéticos, o "quak" dos patos e os botões das lojas.
import "@fontsource-variable/bricolage-grotesque";
import "@fontsource-variable/lexend";
import "./estilo.css";
import Lenis from "lenis";

// O endereço da app. Em desenvolvimento, a app corre em localhost:5174. Trocar pelo endereço real antes de publicar.
export const ENDERECO_APP = "http://localhost:5174";
// As lojas: a app ainda não está publicada. Trocar pelos endereços reais quando estiver.
const LOJAS = { apple: "#", google: "#" };

export const parado = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
export const limita = (v, a, b) => Math.min(b, Math.max(a, v));
export const $ = (s, el = document) => el.querySelector(s);
export const $$ = (s, el = document) => [...el.querySelectorAll(s)];

// ---- Títulos palavra a palavra: cada palavra sobe de trás de uma máscara ----
function partePalavras(no, conta) {
  for (const filho of [...no.childNodes]) {
    if (filho.nodeType === Node.TEXT_NODE) {
      const frag = document.createDocumentFragment();
      for (const bocado of filho.textContent.split(/(\s+)/)) {
        if (!bocado) continue;
        if (/^\s+$/.test(bocado)) { frag.append(" "); continue; }
        const fora = document.createElement("span"), dentro = document.createElement("span");
        fora.className = "palavra";
        dentro.textContent = bocado;
        dentro.style.transitionDelay = `${conta.n++ * 55}ms`;
        fora.append(dentro);
        frag.append(fora);
      }
      filho.replaceWith(frag);
    } else if (filho.nodeType === Node.ELEMENT_NODE && filho.tagName !== "BR") partePalavras(filho, conta);
  }
}

// ---- Os números que contam até ao valor quando aparecem (data-conta="12480", data-casas="1") ----
function contaAte(el) {
  const fim = Number(el.dataset.conta), casas = Number(el.dataset.casas || 0);
  const formata = (v) => v.toLocaleString("pt-PT", { minimumFractionDigits: casas, maximumFractionDigits: casas });
  if (parado) { el.textContent = formata(fim); return; }
  const inicio = performance.now(), dura = 1600;
  (function passo(agora) {
    const p = limita((agora - inicio) / dura, 0, 1);
    el.textContent = formata(fim * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(passo);
  })(inicio);
}

// ---- Os botões das lojas (App Store e Google Play), desenhados aqui para ficarem iguais em todo o lado ----
const ICONE_APPLE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M16.4 12.6c0-2.5 2-3.7 2.1-3.8-1.2-1.7-3-1.9-3.6-2-1.5-.2-3 .9-3.8.9-.8 0-2-.9-3.3-.9-1.7 0-3.3 1-4.1 2.5-1.8 3.1-.5 7.6 1.3 10.1.8 1.2 1.8 2.6 3.1 2.5 1.2 0 1.7-.8 3.2-.8s1.9.8 3.2.8c1.3 0 2.2-1.2 3-2.4.9-1.4 1.3-2.7 1.3-2.8 0 0-2.4-1-2.4-4.1zM14 5.2c.7-.8 1.1-1.9 1-3-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.5z"/></svg>';
const ICONE_GOOGLE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#00d7fe" d="M3.6 2.3 13.4 12l-9.8 9.7c-.4-.2-.6-.6-.6-1.1V3.4c0-.5.2-.9.6-1.1z"/><path fill="#ffce00" d="m16.7 15.3-3.3-3.3 3.3-3.3 3.8 2.2c1 .6 1 1.6 0 2.2z"/><path fill="#ff3a44" d="M16.7 15.3 13.4 12l-9.8 9.7c.4.2.9.2 1.4-.1z"/><path fill="#00f076" d="M16.7 8.7 5 2.4c-.5-.3-1-.3-1.4-.1l9.8 9.7z"/></svg>';
function poeLojas() {
  for (const caixa of $$("[data-lojas]")) {
    caixa.classList.add("lojas");
    caixa.innerHTML = `
      <a class="loja" href="${LOJAS.apple}" aria-label="Descarregar na App Store">${ICONE_APPLE}<span><small>Descarregar na</small>App Store</span></a>
      <a class="loja" href="${LOJAS.google}" aria-label="Disponível no Google Play">${ICONE_GOOGLE}<span><small>Disponível no</small>Google Play</span></a>`;
  }
}

// ---- O "quak": dois sopros curtos feitos com o Web Audio, e um balão de fala ----
const FRASES = ["Quak!", "Tu dizes.", "Nós fazemos!", "Quak, quak!", "Bora a essa obra?", "Conta comigo."];
let audio;
function somQuak() {
  try {
    audio ??= new (window.AudioContext || window.webkitAudioContext)();
    if (audio.state === "suspended") audio.resume();
    [0, 0.16].forEach((atraso, i) => {
      const o = audio.createOscillator(), filtro = audio.createBiquadFilter(), ganho = audio.createGain();
      const t = audio.currentTime + atraso, f = i ? 420 : 470;
      o.type = "sawtooth";
      o.frequency.setValueAtTime(f, t);
      o.frequency.exponentialRampToValueAtTime(f * 0.62, t + 0.12);
      filtro.type = "bandpass"; filtro.frequency.value = 1150; filtro.Q.value = 2.4;
      ganho.gain.setValueAtTime(0.0001, t);
      ganho.gain.exponentialRampToValueAtTime(0.16, t + 0.015);
      ganho.gain.exponentialRampToValueAtTime(0.0001, t + 0.13);
      o.connect(filtro).connect(ganho).connect(audio.destination);
      o.start(t); o.stop(t + 0.15);
    });
  } catch { /* sem som, o pato faz quak na mesma */ }
}
function ativaQuak() {
  const balao = document.createElement("div");
  balao.className = "balao";
  balao.setAttribute("aria-hidden", "true");
  document.body.appendChild(balao);
  let fimBalao, frase = 0;
  for (const pato of $$(".pato")) {
    pato.addEventListener("click", () => {
      somQuak();
      const r = pato.getBoundingClientRect();
      balao.textContent = FRASES[frase++ % FRASES.length];
      balao.style.left = `${r.left + r.width * 0.7 + window.scrollX}px`;
      balao.style.top = `${r.top + r.height * 0.12 + window.scrollY}px`;
      balao.classList.remove("visivel");
      pato.classList.remove("quak");
      void balao.offsetWidth;
      balao.classList.add("visivel");
      pato.classList.add("quak");
      clearTimeout(fimBalao);
      fimBalao = setTimeout(() => balao.classList.remove("visivel"), 1400);
    });
  }
}

// ---- O cursor: um losango amarelo que segue o rato e cresce por cima do que se carrega ----
function ativaCursor() {
  if (parado || !window.matchMedia("(pointer: fine)").matches) return;
  const cursor = document.createElement("i");
  cursor.className = "cursor";
  document.body.appendChild(cursor);
  let cx = -100, cy = -100, rx = -100, ry = -100;
  window.addEventListener("pointermove", (e) => {
    cx = e.clientX; cy = e.clientY;
    cursor.classList.add("visivel");
    cursor.classList.toggle("grande", !!e.target.closest("a, button, summary, .pato"));
  }, { passive: true });
  document.addEventListener("pointerleave", () => cursor.classList.remove("visivel"));
  (function segue() {
    requestAnimationFrame(segue);
    rx += (cx - rx) * 0.22; ry += (cy - ry) * 0.22;
    cursor.style.translate = `${rx}px ${ry}px`;
  })();
  // Botões magnéticos: puxam-se um pouco para o rato.
  for (const b of $$(".botao, .loja")) {
    b.addEventListener("pointermove", (e) => {
      const q = b.getBoundingClientRect();
      b.style.translate = `${(e.clientX - q.left - q.width / 2) * 0.18}px ${(e.clientY - q.top - q.height / 2) * 0.3}px`;
    });
    b.addEventListener("pointerleave", () => { b.style.translate = ""; });
  }
}

// ---- O menu do telemóvel: um botão na barra que abre os mesmos links em ecrã inteiro ----
function ativaMenu(lenis) {
  const nav = $(".barra-nav"), barra = $(".barra-dentro");
  if (!nav || !barra) return;
  const botao = document.createElement("button");
  botao.type = "button";
  botao.className = "menu-botao";
  botao.setAttribute("aria-expanded", "false");
  botao.setAttribute("aria-controls", "menu-movel");
  botao.innerHTML = '<span class="sr">Abrir o menu</span><i></i><i></i>';
  barra.append(botao);
  const painel = document.createElement("div");
  painel.className = "menu-movel";
  painel.id = "menu-movel";
  painel.innerHTML = `<nav aria-label="Menu">${nav.innerHTML}</nav>`;
  const comecar = $(".barra .botao")?.cloneNode(true);
  if (comecar) { comecar.className = "botao botao-amarelo botao-grande"; painel.append(comecar); }
  document.body.append(painel);
  const abre = (sim) => {
    document.body.classList.toggle("menu-aberto", sim);
    botao.setAttribute("aria-expanded", String(sim));
    $(".sr", botao).textContent = sim ? "Fechar o menu" : "Abrir o menu";
    if (sim) lenis?.stop(); else lenis?.start();
  };
  botao.addEventListener("click", () => abre(!document.body.classList.contains("menu-aberto")));
  painel.addEventListener("click", (e) => {
    const a = e.target.closest("a");
    if (!a) return;
    abre(false);
    // Um link para esta mesma página: desliza até à secção (o scroll estava parado com o menu aberto).
    const url = new URL(a.href, location.href);
    if (url.pathname === location.pathname && url.hash && document.querySelector(url.hash)) {
      e.preventDefault();
      e.stopPropagation();
      if (lenis) lenis.scrollTo(url.hash, { offset: -66 });
      else document.querySelector(url.hash).scrollIntoView();
    }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") abre(false); });
  window.addEventListener("resize", () => { if (window.innerWidth >= 900) abre(false); });
}

// Liga tudo o que é comum. Devolve o Lenis (ou null), para a página o fazer andar no seu próprio ciclo.
export function iniciaComum() {
  for (const a of $$("[data-app]")) a.href = ENDERECO_APP;
  poeLojas();
  $$("[data-palavras]").forEach((t) => partePalavras(t, { n: 0 }));
  const vigia = new IntersectionObserver((entradas) => {
    for (const en of entradas) {
      if (!en.isIntersecting) continue;
      en.target.classList.add("visivel");
      for (const n of $$("[data-conta]", en.target)) contaAte(n);
      vigia.unobserve(en.target);
    }
  }, { threshold: 0.25 });
  $$(".revela, [data-palavras]:not(h1)").forEach((el) => vigia.observe(el));
  ativaCursor();
  ativaQuak();
  const lenis = parado ? null : new Lenis({ lerp: 0.09, anchors: { offset: -66 } });
  ativaMenu(lenis);
  return lenis;
}
