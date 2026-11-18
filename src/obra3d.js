// A obra em 3D, desenhada ao vivo no browser (Three.js): a casa de banho exportada do Blender (public/3d/obra.glb)
// e a mesma animação do filme, agora comandada pelo scroll, sem imagens pré-feitas.
// As contas da animação são as de blender/cena.py, em coordenadas do Blender (x, y, z com z para cima);
// a função b() passa-as para o Three.js (y para cima): (x, y, z) do Blender = (x, z, -y) aqui.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const b = (x, y, z) => new THREE.Vector3(x, z, -y);
const fase = (t, a, c) => Math.min(1, Math.max(0, (t - a) / (c - a)));
const suave = (k) => k * k * (3 - 2 * k);
const salta = (k) => { const c = 1.9; return k < 1 ? 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2 : 1; };
const some = (k) => 1 - k * k;
const rad = THREE.MathUtils.degToRad;
// O carregador do glTF troca os espaços por _ e tira os pontos dos nomes; procura-se sempre pelo nome assim tratado.
const nomeGl = (n) => n.replace(/\s/g, "_").replace(/[[\].:/]/g, "");

// A câmara: as mesmas posições-chave do filme (t, ângulo, elevação, distância, alvo), numa só curva.
const CHAVES = [
  [0.00, 40, 47, 98, [-0.6, 0.4, 1.6]],
  [0.24, 33, 37, 62, [1.8, -1.4, 3.8]],
  [0.46, 23, 30, 58, [-0.6, -0.4, 2.0]],
  [0.82, 12, 20, 54, [-0.8, 0.4, 2.2]],
  [1.00, 6, 14, 50, [-0.2, -0.6, 2.4]],
];
let afastar = 1;
function chaveEm(t) {
  const ts = CHAVES.map((c) => c[0]);
  const i = Math.max(0, Math.min(CHAVES.length - 2, ts.filter((x) => x <= t).length - 1));
  const k = (t - ts[i]) / (ts[i + 1] - ts[i]);
  const canal = (f) => {
    const p = [i - 1, i, i + 1, i + 2].map((j) => f(CHAVES[Math.max(0, Math.min(CHAVES.length - 1, j))]));
    return 0.5 * (2 * p[1] + (-p[0] + p[2]) * k + (2 * p[0] - 5 * p[1] + 4 * p[2] - p[3]) * k * k + (-p[0] + 3 * p[1] - 3 * p[2] + p[3]) * k ** 3);
  };
  const az = rad(canal((c) => c[1])), el = rad(canal((c) => c[2])), d = canal((c) => c[3]) * afastar;
  const alvo = [0, 1, 2].map((n) => canal((c) => c[4][n]));
  const olho = [alvo[0] + d * Math.sin(az) * Math.cos(el), alvo[1] - d * Math.cos(az) * Math.cos(el), alvo[2] + d * Math.sin(el)];
  return { olho: b(...olho), alvo: b(...alvo) };
}

const TELE_POS = [2.95, -0.35, 3.3];
const SITIOS = [[-1.6, -3.4], [-1.0, 0.8], [-2.6, -0.4], [-1.4, -3.2]];
const ROTS = [-40, 60, 150, -45];
const FOTOS = [["foto banheira", [2.6, -9.2, 7.8], 7], ["foto lavatorio", [4.6, -8.0, 8.6], -3], ["foto mancha", [6.6, -6.8, 7.8], -9]];
const ENTRADAS = [["base duche", 0.665], ["vidro", 0.69], ["chuveiro", 0.71], ["sanita nova", 0.72], ["movel", 0.73], ["espelho", 0.75], ["toalha", 0.76], ["tapete", 0.77]];

export function iniciaObra(palco, { aoPronto } = {}) {
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  } catch {
    return null;
  }
  const estreito = () => window.innerWidth / window.innerHeight < 1;
  const tela = renderer.domElement;
  tela.className = "obra3d";
  tela.setAttribute("aria-hidden", "true");
  palco.prepend(tela);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const cena = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  cena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  cena.environmentIntensity = 0.45;
  cena.add(new THREE.HemisphereLight(0xe8eeff, 0xd8c8a8, 1.1));
  const sol = new THREE.DirectionalLight(0xfff6ea, 2.6);
  sol.position.copy(b(22, -18, 28));
  sol.castShadow = true;
  sol.shadow.mapSize.set(estreito() ? 1024 : 2048, estreito() ? 1024 : 2048);
  Object.assign(sol.shadow.camera, { left: -14, right: 14, top: 14, bottom: -14, near: 1, far: 90 });
  sol.shadow.bias = -0.0004;
  sol.shadow.normalBias = 0.03;
  sol.shadow.radius = 4;
  const contra = new THREE.DirectionalLight(0xcfdcff, 0.55);
  contra.position.copy(b(-14, -26, 8));
  cena.add(sol, contra);

  const camara = new THREE.PerspectiveCamera(22, 1, 1, 400);
  camara.filmGauge = 36;

  const obj = {};
  let pronto = false, tAtual = -1, sujo = true, azulejosProntos = false;

  function ajusta() {
    const L = palco.clientWidth, A = palco.clientHeight;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, estreito() ? 1.5 : 2));
    renderer.setSize(L, A, false);
    camara.aspect = L / A;
    afastar = estreito() ? 1 : 1.18;
    if (estreito()) {
      // Telemóvel: a obra mais pequena e no topo, por cima do texto.
      camara.fov = 34;
      camara.filmOffset = 0;
      camara.setViewOffset(L, A, 0, A * 0.11, L, A);
    } else {
      // Ecrã largo: o mesmo enquadramento do Blender (objetiva de 90 mm), com a obra à direita do texto.
      camara.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(Math.atan(18 / 90)) / camara.aspect));
      camara.filmOffset = 0;
      camara.setViewOffset(L, A, -L * 0.25, 0, L, A);
    }
    camara.updateProjectionMatrix();
    sujo = true;
  }
  ajusta();
  window.addEventListener("resize", ajusta);

  new GLTFLoader().load("/3d/obra.glb", (gltf) => {
    const raiz = gltf.scene;
    raiz.traverse((o) => {
      if (o.name && !obj[o.name]) obj[o.name] = o;
      if (!o.isMesh) return;
      o.castShadow = true;
      o.receiveShadow = true;
      const m = o.material;
      if (!m) return;
      if (m.name === "vidro") {
        o.material = new THREE.MeshPhysicalMaterial({ color: 0xdceeff, roughness: 0.05, metalness: 0, transparent: true, opacity: 0.22, clearcoat: 1 });
        o.castShadow = false;
      } else if (m.name === "flash") {
        o.material = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false });
        o.castShadow = false;
      } else if (m.name === "amarelo visto") {
        // O cliente leva o visto do logótipo (cor dos vértices); o técnico, com roupa, fica liso.
        const doCliente = o.parent?.name === "cliente" || o.name.startsWith("cliente");
        o.material = m.clone();
        o.material.vertexColors = doCliente;
        o.material.color.set(doCliente ? 0xffffff : 0xffc01a);
      }
    });
    // O chão que só apanha a sombra.
    const chao = pega("chao");
    if (chao) chao.traverse((o) => { if (o.isMesh) { o.material = new THREE.ShadowMaterial({ opacity: 0.28 }); o.castShadow = false; } });
    // Guarda a posição, rotação e escala de partida de cada peça animada.
    for (const o of Object.values(obj)) { o.userData.p0 = o.position.clone(); o.userData.q0 = o.quaternion.clone(); }
    cena.add(raiz);
    pronto = true;
    sujo = true;
    aoPronto?.();
  });

  const lista = (prefixo) => { const p = nomeGl(prefixo); return Object.values(obj).filter((o) => o.name.startsWith(p) && (prefixo !== "azulejo" || o.userData.base)); };
  const pega = (nome) => obj[nomeGl(nome)];

  function poe(nome, k, alt = 0) {
    const g = pega(nome);
    if (!g) return;
    g.visible = k > 0.001;
    g.scale.setScalar(Math.max(k, 0.0001));
    g.position.copy(g.userData.p0);
    g.position.y += alt;
  }

  function posa(t) {
    const { olho, alvo } = chaveEm(t);
    camara.position.copy(olho);
    camara.lookAt(alvo);

    // 1. O cliente pega no telemóvel e tira três fotografias, que ficam a flutuar.
    poe("telemovel", salta(fase(t, 0.09, 0.15)) * some(fase(t, 0.31, 0.35)));
    const clarao = pega("clarao");
    clarao.visible = false;
    FOTOS.forEach(([nome, destino, rolo], i) => {
      const g = pega(nome);
      const ini = 0.15 + 0.045 * i;
      const fl = fase(t, ini, ini + 0.02);
      if (fl > 0 && fl < 1) { clarao.visible = true; clarao.scale.setScalar(Math.max(Math.sin(Math.PI * fl), 0.0001) * 1.8); }
      const k = fase(t, ini + 0.005, ini + 0.06), sai = fase(t, 0.31, 0.35);
      if (k <= 0 || sai >= 1) { g.visible = false; return; }
      g.visible = true;
      const s = suave(k);
      const de = new THREE.Vector3(...TELE_POS), para = new THREE.Vector3(...destino);
      const p = de.lerp(para, s);
      g.position.copy(b(p.x, p.y, p.z + Math.sin(Math.PI * k) * 0.8));
      g.scale.setScalar(Math.max(1.25 * salta(k) * some(sai), 0.0001));
      // A fotografia (face +Z no Blender, +Y aqui) vira-se para a câmara, com o seu topo para cima.
      const n = camara.position.clone().sub(g.position).normalize();
      const z = new THREE.Vector3(0, 1, 0).sub(n.clone().multiplyScalar(n.y)).normalize().negate();
      const x = new THREE.Vector3().crossVectors(n, z);
      g.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, n, z));
      g.rotateY(rad(rolo) * s + (1 - s) * 1.2);
    });

    const olha = suave(fase(t, 0.08, 0.16)) - suave(fase(t, 0.28, 0.36));
    const festa = fase(t, 0.84, 0.97);
    const pulo = Math.abs(Math.sin(festa * Math.PI * 2)) * 0.9 * (1 - festa * 0.3);
    const ZP = 0.1 - (pega("cliente").userData.zmin ?? -0.66);
    const cl = pega("cliente");
    cl.position.copy(b(2.0, -2.0, ZP + pulo));
    cl.rotation.set(0, rad(-48 + 108 * olha), 0);
    cl.scale.setScalar(1.25);

    // 2. Chega o técnico; 3. anda pela obra aos saltos.
    const tec = pega("tecnico");
    const ch = fase(t, 0.31, 0.42);
    const queda = (1 - ch) ** 2 * 16, ressalto = Math.sin(fase(t, 0.42, 0.47) * Math.PI) * 0.5;
    let [x, y] = SITIOS[0], salto = 0, rz = ROTS[0];
    [0.47, 0.56, 0.66].forEach((ini, i) => {
      const kk = fase(t, ini, ini + 0.07);
      if (kk <= 0) return;
      const s = suave(kk);
      x = SITIOS[i][0] + (SITIOS[i + 1][0] - SITIOS[i][0]) * s;
      y = SITIOS[i][1] + (SITIOS[i + 1][1] - SITIOS[i][1]) * s;
      salto = Math.sin(kk * Math.PI) * 1.3;
      rz = ROTS[i] + (ROTS[i + 1] - ROTS[i]) * s;
    });
    tec.visible = t >= 0.305;
    tec.position.copy(b(x, y, ZP + queda + ressalto + salto + (festa > 0.12 ? pulo * 0.8 : 0)));
    tec.rotation.set(0, rad(rz), 0);
    tec.scale.setScalar(1.15);

    // 3. Sai o velho, os azulejos viram-se em onda, entra o novo.
    poe("banheira velha", some(fase(t, 0.47, 0.55)));
    poe("lavatorio velho", some(fase(t, 0.49, 0.57)));
    poe("sanita velha", some(fase(t, 0.50, 0.58)));
    poe("mancha", some(fase(t, 0.50, 0.56)));
    for (const o of lista("azulejo")) {
      const { base: bb, rz: r0 = 0 } = o.userData;
      const chao = bb[2] < 0.5;
      const parede = chao ? "chao" : Math.abs(bb[1] - 5.94) < 0.01 ? "fundo" : "esq";
      const atraso = o.userData.atraso ?? 0;
      const ini = (parede === "chao" ? 0.56 : 0.52) + atraso * 0.13;
      const kk = suave(fase(t, ini, ini + 0.07));
      const fora = Math.sin(kk * Math.PI) * 0.75;
      if (parede === "chao") {
        o.rotation.set(kk * Math.PI, 0, 0);
        o.position.copy(b(bb[0], bb[1], bb[2] + fora));
      } else {
        o.rotation.set(0, r0 + kk * Math.PI, 0);
        o.position.copy(b(bb[0] + (parede === "esq" ? fora : 0), bb[1] - (parede === "fundo" ? fora : 0), bb[2]));
      }
    }
    for (const [nome, ini] of ENTRADAS) {
      const kk = fase(t, ini, ini + 0.075);
      poe(nome, kk > 0 ? salta(kk) : 0, (1 - suave(kk)) * 0.8);
    }

    // 4. Obra feita: estrelas por cima dos patos.
    lista("estrela").forEach((e, i) => {
      const kk = fase(t, 0.85 + i * 0.025, 0.93 + i * 0.025);
      e.visible = kk > 0;
      e.scale.setScalar(Math.max(salta(kk), 0.0001));
      const an = rad(-50 + i * 38) + t * 3;
      e.position.copy(b(0.4 + Math.cos(an) * 0.3 + (i - 1) * 1.5, -3.2 + (i - 1) * 1.2, 4.0 + (i === 1 ? 0.5 : 0) + kk * 0.3));
      e.rotation.set(0, rad(-40) + (1 - kk) * 3, 0);
    });
  }

  // Os azulejos: o atraso da onda depende do sítio de cada um (como no Blender).
  function preparaAzulejos() {
    for (const o of lista("azulejo")) {
      const bb = o.userData.base;
      if (!bb) continue;
      if (bb[2] < 0.5) {
        const i = Math.round((bb[0] + 6 - 1) / 2), j = Math.round((bb[1] + 6 - 1) / 2);
        o.userData.atraso = (i + (5 - j)) / 12;
      } else {
        const l = Math.round((bb[2] - 0.77) / 1.5);
        if (Math.abs(bb[1] - 5.94) < 0.01) { const c = Math.round((bb[0] + 5.25) / 1.5); o.userData.atraso = (c + (3 - l)) / 12; }
        else { const c = Math.round((-bb[1] + 5.25) / 1.5); o.userData.atraso = ((7 - c) + (3 - l)) / 12; }
      }
    }
  }

  const api = {
    obj, camara, cena, renderer,
    // t vai de 0 (início) a 1 (obra feita). Só se volta a desenhar quando alguma coisa muda.
    define(t) {
      if (!pronto) return;
      if (!azulejosProntos) { preparaAzulejos(); azulejosProntos = true; }
      if (Math.abs(t - tAtual) < 1e-5 && !sujo) return;
      tAtual = t;
      posa(t);
      renderer.render(cena, camara);
      sujo = false;
    },
  };
  if (import.meta.env?.DEV) window.__obra = api;
  return api;
}
