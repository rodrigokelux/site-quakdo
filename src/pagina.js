// As páginas dos técnicos e das empresas: usa o que é comum a todas as páginas (comum.js)
// e só acrescenta a barra por cima da abertura azul, a linha de andamento e as imagens que deslizam.
import { iniciaComum, parado, $, $$ } from "./comum.js";

const lenis = iniciaComum();
const barra = $("#barra");
const heroi = $(".tec-heroi");
const andamento = $("#andamento");
const deslizes = $$("[data-desliza]");

window.setTimeout(() => $("h1")?.classList.add("visivel"), parado ? 0 : 150);

function aoDescer() {
  // Enquanto a abertura azul está por baixo da barra, a barra fica transparente e com o logótipo branco.
  document.body.classList.toggle("no-filme", heroi.getBoundingClientRect().bottom > 70);
  barra.classList.toggle("descida", window.scrollY > 8);
  const total = document.documentElement.scrollHeight - window.innerHeight;
  andamento.style.scale = `${total > 0 ? window.scrollY / total : 0} 1`;
}
aoDescer();
window.addEventListener("scroll", aoDescer, { passive: true });
window.addEventListener("resize", aoDescer);
lenis?.on("scroll", aoDescer);

(function quadro(agora) {
  requestAnimationFrame(quadro);
  lenis?.raf(agora);
  if (parado) return;
  for (const el of deslizes) {
    const r = el.parentElement.getBoundingClientRect();
    if (r.bottom < 0 || r.top > window.innerHeight) continue;
    const k = (r.top + r.height / 2 - window.innerHeight / 2) / window.innerHeight;
    el.style.translate = `0 ${k * Number(el.dataset.desliza)}%`;
  }
})();
