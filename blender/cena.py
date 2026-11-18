# O filme do site: uma casa de banho em miniatura que se renova, do pedido à obra feita.
# Em ecrã inteiro (16:9), com fundo transparente: o azul da marca é posto pelo site.
# A câmara desce e aproxima-se a cada passo, sempre no mesmo sentido, numa só curva.
# Correr: blender -b -P blender/cena.py -- <pasta> <largura> <amostras> <n.º de imagens> [índices...]
# Sem índices, faz o filme todo; as imagens já feitas saltam-se (um render interrompido continua de onde parou).
import bpy, bmesh, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mathutils import Vector, Quaternion
import patolib as q

a = sys.argv[sys.argv.index("--") + 1:]
SAIDA, LARG, AMOSTRAS, N = os.path.abspath(a[0]), int(a[1]), int(a[2]), int(a[3])
INDICES = [int(x) for x in a[4:]] or list(range(N))

bpy.ops.wm.read_factory_settings(use_empty=True)
cena = q.prepara_render(LARG, LARG * 9 // 16, AMOSTRAS)

# ---------------- Curvas de movimento ----------------
def fase(t, a, b):
    return min(1, max(0, (t - a) / (b - a)))

def suave(k):
    return k * k * (3 - 2 * k)

def salta(k):            # entra com um pequeno excesso e assenta
    c = 1.9
    return 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2 if k < 1 else 1

def some(k):             # encolhe até desaparecer
    return 1 - k * k

# ---------------- Azulejos portugueses, pintados aqui ----------------
AZUL = np.array([0x2D, 0x55, 0xB4]) / 255
AZUL_CLARO = np.array([0x8F, 0xAE, 0xE6]) / 255
VIDRADO = np.array([0xF7, 0xF4, 0xEC]) / 255


def motivo(tipo, n=1024):
    s = np.linspace(-1, 1, n)
    u, v = np.meshgrid(s, s)
    r, ang = np.hypot(u, v), np.arctan2(v, u)
    azul = np.zeros(u.shape, bool)
    claro = np.zeros(u.shape, bool)
    if tipo == "flor":
        claro |= np.abs(np.abs(u) + np.abs(v) - 1.0) < 0.035                     # losango fino
        claro |= np.abs(r - 0.8) < 0.03                                            # anel
        azul |= (r < 0.6 * (0.3 + 0.7 * np.abs(np.cos(2 * ang)) ** 0.7)) & (r > 0.13)   # flor de quatro pétalas
        azul |= (r > 0.04) & (r < 0.08)
        for cx in (-1, 1):                                                         # quartos de círculo nos cantos:
            for cy in (-1, 1):                                                     # juntos, fazem um círculo entre azulejos
                d = np.hypot(u - cx, v - cy)
                claro |= (d > 0.34) & (d < 0.4)
                azul |= d < 0.27
                folha = np.hypot((u - cx * 0.55) * 1.6, (v - cy * 0.55) * 1.6)
                azul |= (folha < 0.16) & (np.abs(u * cy - v * cx) < 0.12)
    else:                                                                          # friso: a fiada de cima
        onda = v - 0.22 * np.sin(u * np.pi * 2)
        azul |= np.abs(onda) < 0.11
        claro |= (np.abs(onda) > 0.2) & (np.abs(onda) < 0.25)
        azul |= np.abs(v) > 0.86
        claro |= (np.abs(v) > 0.7) & (np.abs(v) < 0.76)
        for cx in (-0.5, 0.5):
            azul |= np.hypot(u - cx, v + 0.5) < 0.1
    img = np.empty(u.shape + (3,))
    img[:] = VIDRADO
    img[claro] = AZUL_CLARO
    img[azul] = AZUL
    img = img.reshape(n // 2, 2, n // 2, 2, 3).mean(axis=(1, 3))                   # suaviza as arestas
    rgba = np.concatenate([img, np.ones(img.shape[:2] + (1,))], axis=2)
    # Grava-se num PNG e volta-se a ler: uma imagem só em memória não chega ao render sem janela.
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "texturas", f"azulejo-{tipo}.png")
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    im = bpy.data.images.new("tmp " + tipo, n // 2, n // 2, alpha=False)
    im.pixels.foreach_set(rgba[::-1].astype(np.float32).ravel())
    im.filepath_raw, im.file_format = caminho, "PNG"
    im.save()
    bpy.data.images.remove(im)
    return bpy.data.images.load(caminho)


def material_azulejo(tipo):
    m = q.material("azulejo " + tipo, 0xFFFFFF, rug=0.12, verniz=0.7)
    nt = m.node_tree
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = motivo(tipo)
    tx.interpolation = "Cubic"
    nt.links.new(tx.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return m


# ---------------- Materiais ----------------
M = q.material
BASE = M("base", 0xFAC518, rug=0.38, verniz=0.4)
PAREDE = M("parede", 0xF2F2EE, rug=0.7)
REBOCO = M("reboco", 0xDCDDE2, rug=0.85)
VELHO = [M("velho1", 0xD2C196, rug=0.75), M("velho2", 0xC6B487, rug=0.75)]
HUMIDADE = [M("humidade1", 0xA48F62, rug=0.9), M("humidade2", 0x978359, rug=0.9)]
NOVO_FLOR, NOVO_FRISO = material_azulejo("flor"), material_azulejo("friso")
CHAO_V = [M("chao velho1", 0xA9987A, rug=0.8), M("chao velho2", 0x9C8B6E, rug=0.8)]
CHAO_N = [M("chao novo1", 0xEDE7DD, rug=0.3, verniz=0.4), M("chao novo2", 0xE2DACC, rug=0.3, verniz=0.4)]
LOUCA_V = M("louca velha", 0xC7C2A4, rug=0.5)
LOUCA_V2 = M("louca velha escura", 0x8F8A72, rug=0.6)
LOUCA = M("louca", 0xFFFFFF, rug=0.1, verniz=0.8)
CROMADO = M("cromado", 0xD8DEE8, rug=0.1, metal=1.0)
VIDRO = M("vidro", 0xDCEEFF, rug=0.02, vidro=1.0)
MADEIRA = M("madeira", 0xB97A3E, rug=0.45, verniz=0.25)
ESPELHO = M("espelho", 0xC8DDF3, rug=0.03, metal=1.0)
TAPETE = M("tapete", 0x2D55B4, rug=0.9)
TAPETE_ORLA = M("tapete orla", 0xF2F2EE, rug=0.9)
TOALHA = M("toalha", 0x2D55B4, rug=0.95)
VERDE = M("planta", 0x2E9C52, rug=0.5)
OURO = M("ouro", 0xFFB400, rug=0.25, verniz=0.5, emite=0.25)
MANCHA = M("mancha", 0xB8A270, rug=0.95)
MANCHA2 = M("mancha escura", 0xA48D5E, rug=0.95)
ECRA = M("ecra", 0x8FBCFF, emite=1.2)
FLASH = M("flash", 0xFFFFFF, emite=40)

# ---------------- A divisão ----------------
T = 6.0                      # meia largura do chão
ALT = 6.0                    # altura das paredes
q.caixa("base", (2 * T + 0.9, 2 * T + 0.9, 0.9), (-0.2, 0.2, -0.47), BASE, canto=0.3)
q.caixa("soalho", (2 * T, 2 * T, 0.1), (0, 0, -0.06), REBOCO, canto=0.0)
q.caixa("parede fundo", (2 * T + 0.5, 0.5, ALT + 0.2), (-0.25, T + 0.25, ALT / 2 - 0.1), PAREDE, canto=0.1)
q.caixa("parede esq", (0.5, 2 * T, ALT + 0.2), (-T - 0.25, 0, ALT / 2 - 0.1), PAREDE, canto=0.1)

azulejos = []   # (objeto, tipo, atraso)


def azulejo(dim, mats):
    """Placa fina de arestas boleadas: a face da frente (-Y, ou +Z no chão) é a velha, a de trás é a nova."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co = Vector((v.co.x * dim[0], v.co.y * dim[1], v.co.z * dim[2]))
    eixo = 1 if dim[1] < dim[2] else 2
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        n = f.normal[eixo]
        f.material_index = (0 if (n < -0.5 if eixo == 1 else n > 0.5) else 1 if abs(n) > 0.5 else 2)
        for l in f.loops:
            a_, b_ = (0, 2) if eixo == 1 else (0, 1)
            l[uv].uv = (0.5 - l.vert.co[a_] / dim[a_], 0.5 + l.vert.co[b_] / dim[b_])
    me = bpy.data.meshes.new("azulejo")
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    o = q.liga(bpy.data.objects.new("azulejo", me))
    b = o.modifiers.new("canto", "BEVEL")
    b.width, b.segments = 0.035, 3
    o.modifiers.new("normais", "WEIGHTED_NORMAL")
    for p in me.polygons:
        p.use_smooth = True
    return o


COLS, LINS, LADO = 8, 4, 1.5
for parede in ("fundo", "esq"):
    for c in range(COLS):
        for l in range(LINS):
            humido = parede == "esq" and (c, l) in ((1, 2), (2, 2), (1, 3), (2, 3), (2, 1))
            o = azulejo((LADO - 0.05, 0.1, LADO - 0.05), [(HUMIDADE if humido else VELHO)[(c + l) % 2], NOVO_FRISO if l == LINS - 1 else NOVO_FLOR, REBOCO])
            z = LADO / 2 + l * LADO + 0.02
            u = -T + LADO / 2 + c * LADO
            if parede == "fundo":
                o.location, o["rz"] = (u, T - 0.06, z), 0.0
                atraso = (c + (LINS - 1 - l)) / (COLS + LINS)
            else:
                o.location, o["rz"] = (-T + 0.06, -u, z), math.pi / 2
                atraso = ((COLS - 1 - c) + (LINS - 1 - l)) / (COLS + LINS)
            o["base"] = list(o.location)
            azulejos.append((o, parede, atraso))
NC = 6
LC = 2 * T / NC
for i in range(NC):
    for j in range(NC):
        o = azulejo((LC - 0.05, LC - 0.05, 0.1), [CHAO_V[(i + j) % 2], CHAO_N[(i + j) % 2], REBOCO])
        o.location = (-T + LC / 2 + i * LC, -T + LC / 2 + j * LC, 0.04)
        o["base"] = list(o.location)
        azulejos.append((o, "chao", (i + (NC - 1 - j)) / (2 * NC)))


def grupo(nome, pos):
    g = q.vazio(nome)
    g.location = pos
    g["base"] = list(pos)
    return g


def sanita(g, mat, mat2, moderna):
    """Sanita virada para +X, encostada à parede da esquerda. A moderna é suspensa, com o autoclismo na parede."""
    z = 1.35 if moderna else 1.1
    q.esfera("bacia", 1, (0.35, 0, z), mat, g, escala=(1.0, 0.72, 0.5), seg=48)
    q.cilindro("assento", 0.8, 0.1, (0.4, 0, z + 0.46), mat, g, canto=0.04).scale = (1.22, 0.88, 1)
    q.caixa("costas", (0.5, 1.25, 0.9 if moderna else 0.6), (-0.42, 0, z + 0.05), mat, g, canto=0.2)
    if moderna:
        q.caixa("placa", (0.05, 0.8, 0.5), (-0.62, 0, z + 1.55), mat, g, canto=0.04)
        q.caixa("botao", (0.06, 0.32, 0.22), (-0.6, 0, z + 1.55), CROMADO, g, canto=0.04)
    else:
        q.cilindro("pe", 0.42, z, (0.25, 0, z / 2), mat, g, raio2=0.55)
        q.caixa("tanque", (0.6, 1.6, 1.4), (-0.4, 0, z + 1.05), mat, g, canto=0.12)
        q.caixa("tampa", (0.66, 1.66, 0.12), (-0.4, 0, z + 1.8), mat2, g, canto=0.05)


# O que sai: banheira velha, lavatório velho, sanita velha e uma mancha de humidade.
banheira = grupo("banheira velha", (-2.6, 4.45, 0.1))
q.caixa("corpo", (6.2, 2.7, 1.9), (0, 0, 0.95), LOUCA_V, banheira, canto=0.45)
q.caixa("dentro", (5.5, 2.0, 0.3), (0, 0, 1.78), LOUCA_V2, banheira, canto=0.14)
q.cilindro("torneira", 0.1, 0.9, (2.4, 0.9, 2.3), LOUCA_V2, banheira)
lavatorio = grupo("lavatorio velho", (-5.1, -2.2, 0.1))
q.cilindro("pe", 0.32, 2.3, (0, 0, 1.15), LOUCA_V, lavatorio, raio2=0.45)
q.caixa("bacia", (1.5, 2.1, 0.6), (0.1, 0, 2.5), LOUCA_V, lavatorio, canto=0.28)
q.caixa("fundo", (1.0, 1.6, 0.1), (0.15, 0, 2.78), LOUCA_V2, lavatorio, canto=0.04)
sanita_v = grupo("sanita velha", (-5.2, 1.9, 0.1))
sanita(sanita_v, LOUCA_V, LOUCA_V2, False)
mancha = grupo("mancha", (-5.84, 2.4, 4.3))

# O que entra: base de duche com vidro e chuveiro, sanita suspensa, móvel com lavatório, espelho, toalha, tapete e planta.
duche = grupo("base duche", (-3.7, 3.7, 0.1))
q.caixa("tabuleiro", (4.4, 4.4, 0.24), (0, 0, 0.12), LOUCA, duche, canto=0.1)
q.caixa("ralo", (0.14, 2.6, 0.04), (1.4, 0, 0.25), CROMADO, duche, canto=0.02)
vidro = grupo("vidro", (-1.42, 3.7, 0.3))
q.caixa("vidro", (0.07, 4.4, 4.9), (0, 0, 2.45), VIDRO, vidro, canto=0.02)
q.caixa("perfil", (0.12, 0.08, 4.9), (0, -2.18, 2.45), CROMADO, vidro, canto=0.02)
chuveiro = grupo("chuveiro", (-3.7, 5.86, 0.1))
q.cilindro("tubo", 0.07, 4.6, (0, 0, 2.6), CROMADO, chuveiro)
braco = q.cilindro("braco", 0.07, 1.3, (0, -0.6, 4.9), CROMADO, chuveiro)
braco.rotation_euler = (math.pi / 2, 0, 0)
q.cilindro("cabeca", 0.62, 0.08, (0, -1.25, 4.82), CROMADO, chuveiro, canto=0.03)
q.cilindro("misturadora", 0.2, 0.16, (0, -0.1, 2.3), CROMADO, chuveiro).rotation_euler = (math.pi / 2, 0, 0)
sanita_n = grupo("sanita nova", (-5.35, 1.9, 0.1))
sanita(sanita_n, LOUCA, LOUCA, True)
movel = grupo("movel", (-5.05, -2.3, 0.1))
q.caixa("armario", (1.7, 3.2, 1.3), (0, 0, 1.25), MADEIRA, movel, canto=0.06)
q.caixa("tampo", (1.86, 3.36, 0.18), (0.04, 0, 1.98), LOUCA, movel, canto=0.06)
q.caixa("cuba", (1.1, 1.5, 0.26), (0.1, 0.2, 2.18), LOUCA, movel, canto=0.12)
q.cilindro("torneira", 0.06, 0.6, (-0.55, 0.2, 2.38), CROMADO, movel)
q.caixa("frincha", (0.04, 3.0, 0.03), (0.86, 0, 1.2), M("frincha", 0x6E4220, rug=0.6), movel, canto=0.0)
q.cilindro("vaso", 0.26, 0.42, (0.1, -1.15, 2.3), LOUCA, movel, raio2=0.2)
for dx, dy, dz, r in ((0, 0, 0.42, 0.32), (0.16, 0.12, 0.66, 0.24), (-0.14, -0.1, 0.7, 0.22), (0.02, -0.04, 0.92, 0.2)):
    q.esfera("folha", r, (0.1 + dx, -1.15 + dy, 2.3 + dz), VERDE, movel, seg=20)
espelho = grupo("espelho", (-5.92, -2.3, 4.35))
e1 = q.cilindro("moldura", 1.32, 0.12, (0, 0, 0), MADEIRA, espelho, canto=0.04)
e1.rotation_euler = (0, math.pi / 2, 0)
e2 = q.cilindro("vidro", 1.18, 0.05, (0.06, 0, 0), ESPELHO, espelho)
e2.rotation_euler = (0, math.pi / 2, 0)
toalha = grupo("toalha", (2.1, 5.84, 3.6))
q.cilindro("barra", 0.05, 2.0, (0, -0.2, 0.4), CROMADO, toalha).rotation_euler = (0, math.pi / 2, 0)
q.caixa("pano", (1.6, 0.14, 2.0), (0, -0.25, -0.5), TOALHA, toalha, canto=0.06)
q.caixa("risca", (1.62, 0.15, 0.16), (0, -0.25, -1.2), TAPETE_ORLA, toalha, canto=0.03)
tapete = grupo("tapete", (1.6, -1.6, 0.1))
q.cilindro("orla", 2.3, 0.07, (0, 0, 0.035), TAPETE_ORLA, tapete, canto=0.03)
q.cilindro("tapete", 2.05, 0.09, (0, 0, 0.045), TAPETE, tapete, canto=0.03)

# Os patos.
cliente = q.faz_pato("cliente")
tecnico = q.faz_pato("tecnico", ("capacete", "macacao"))
ZP = 0.1 - cliente["zmin"]                    # altura a que o pato assenta no chão
for p in (cliente, tecnico):
    p.rotation_mode = "XYZ"

# Telemóvel do cliente e o clarão da fotografia.
TELE_POS = (2.95, -0.35, 3.3)
tele = grupo("telemovel", TELE_POS)
q.caixa("corpo", (0.14, 1.0, 1.9), (0, 0, 0), M("telemovel", 0x16223F, rug=0.3), tele, canto=0.12)
ecra_tele = q.caixa("ecra", (0.02, 0.88, 1.74), (-0.075, 0, 0), ECRA, tele, canto=0.0)
foto_tele = None
q.cilindro("lente", 0.09, 0.04, (0.08, 0.28, 0.72), M("lente", 0x0A0D16, rug=0.05, verniz=1.0), tele).rotation_euler = (0, math.pi / 2, 0)
tele.rotation_euler = (0, math.radians(-8), math.radians(60))
clarao = q.esfera("clarao", 0.5, (TELE_POS[0] + 0.3, TELE_POS[1] + 0.5, TELE_POS[2] + 0.8), FLASH)


# As fotografias: três retratos da casa de banho velha, tirados aqui antes do filme, que saem do telemóvel.
PAPEL = M("papel foto", 0xFBFBF8, rug=0.5)
FOTOS = [  # nome, alvo, de onde se olha (relativo ao alvo)
    ("banheira", (-2.6, 4.3, 1.3), (5.0, -7.5, 4.0)),
    ("lavatorio", (-4.9, -0.2, 1.9), (7.5, -4.0, 2.6)),
    ("mancha", (-5.9, 2.5, 4.1), (6.0, -2.2, 0.6)),
]


def material_foto(img, brilho=0.0):
    m = bpy.data.materials.new("foto " + img.name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.35
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"])
    if brilho:
        nt.links.new(tx.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = brilho
    return m


def plano_foto(nome, lado, mat, pai):
    bm = bmesh.new()
    bm.loops.layers.uv.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=lado / 2, calc_uvs=True)
    return q.de_bmesh(nome, bm, mat, pai)


def polaroide(nome, mat):
    g = q.vazio(nome)
    g.rotation_mode = "QUATERNION"
    q.caixa("moldura", (1.7, 2.0, 0.05), (0, 0, 0), PAPEL, g, canto=0.015)
    o = plano_foto("foto", 1.48, mat, g)
    o.location = (0, 0.15, 0.03)
    g["base"] = [0, 0, 0]
    return g
estrelas = [q.estrela("estrela", (0, 0, 0), OURO, raio=0.62) for _ in range(3)]

# ---------------- Luz e câmara ----------------
q.mundo(0.5, (0.86, 0.9, 1.0, 1))                 # o céu puxa ao azul do fundo do site
q.luz((22, -18, 28), (22, 22), 9500, (1.0, 0.97, 0.92), alvo=(0, 0, 2))
q.luz((-14, -26, 8), (14, 14), 1500, (0.8, 0.88, 1.0), alvo=(0, 0, 2))
q.chao_sombra(-0.93)
cam = q.camara(90)
cam.data.shift_x = -0.17                          # a obra fica à direita; o texto do site vive à esquerda

# A câmara: posições-chave (t, ângulo, elevação, distância, alvo). Tudo desce e aproxima-se sem voltar atrás.
CHAVES = [
    (0.00, 40, 47, 98, (-0.6, 0.4, 1.6)),
    (0.20, 33, 37, 52, (1.5, -1.2, 3.6)),
    (0.46, 23, 30, 49, (-0.4, -0.6, 2.0)),
    (0.82, 12, 20, 46, (-0.6, 0.3, 2.1)),
    (1.00, 5, 13, 42, (0.2, -1.2, 2.0)),
]


def camara_em(t):
    """Catmull-Rom pelas posições-chave: uma só curva, sem quebras de velocidade."""
    ts = [c[0] for c in CHAVES]
    i = max(0, min(len(CHAVES) - 2, sum(1 for x in ts if x <= t) - 1))
    k = (t - ts[i]) / (ts[i + 1] - ts[i])
    def canal(f):
        p = [f(CHAVES[max(0, min(len(CHAVES) - 1, j))]) for j in (i - 1, i, i + 1, i + 2)]
        return 0.5 * (2 * p[1] + (-p[0] + p[2]) * k + (2 * p[0] - 5 * p[1] + 4 * p[2] - p[3]) * k * k + (-p[0] + 3 * p[1] - 3 * p[2] + p[3]) * k ** 3)
    az, el, d = math.radians(canal(lambda c: c[1])), math.radians(canal(lambda c: c[2])), canal(lambda c: c[3])
    alvo = Vector([canal(lambda c, n=n: c[4][n]) for n in range(3)])
    olho = alvo + d * Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    q.aponta(cam, olho, alvo)


def poe(g, k, alt=0.0):
    """Escala de entrada/saída de um grupo; alt levanta-o um pouco enquanto entra."""
    g.scale = (max(k, 0.0001),) * 3
    b = g["base"]
    g.location = (b[0], b[1], b[2] + alt)
    g.hide_render = k <= 0.001
    for o in g.children_recursive:
        o.hide_render = k <= 0.001


def cena_em(t):
    camara_em(t)

    # 1. O cliente mostra o que precisa: pega no telemóvel, tira três fotografias (três clarões) e elas ficam a flutuar.
    poe(tele, salta(fase(t, 0.09, 0.15)) * some(fase(t, 0.31, 0.35)))
    clarao.hide_render = True
    for i, (g, destino, rolo) in enumerate(polaroides):
        ini = 0.15 + 0.045 * i
        fl = fase(t, ini, ini + 0.02)
        if 0 < fl < 1:
            clarao.hide_render = False
            clarao.scale = (max(math.sin(math.pi * fl), 0.0001) * 1.8,) * 3
        k = fase(t, ini + 0.005, ini + 0.06)
        sai = fase(t, 0.31, 0.35)
        if k <= 0 or sai >= 1:
            poe(g, 0)
            continue
        s = suave(k)
        de = Vector(TELE_POS)
        pos = de + (Vector(destino) - de) * s + Vector((0, 0, math.sin(math.pi * k) * 0.8))
        pos += Vector((0, 0, math.sin(t * 40 + i * 2) * 0.06))
        g.location = pos
        g.hide_render = False
        for o in g.children_recursive:
            o.hide_render = False
        g.scale = (max(1.25 * salta(k) * some(sai), 0.0001),) * 3
        para_cam = (cam.location - g.location).to_track_quat("Z", "Y")
        g.rotation_quaternion = para_cam @ Quaternion((0, 0, 1), math.radians(rolo) * s + (1 - s) * 1.2)
    olha = suave(fase(t, 0.08, 0.16)) - suave(fase(t, 0.28, 0.36))          # vira-se para a banheira
    festa = fase(t, 0.84, 0.97)
    pulo = abs(math.sin(festa * math.pi * 2)) * 0.9 * (1 - festa * 0.3)
    cliente.location = (2.0, -2.0, ZP + pulo)
    cliente.rotation_euler = (0, 0, math.radians(-48 + 108 * olha))
    cliente.scale = (1.25,) * 3

    # 2. Chega o técnico: cai de cima e assenta.
    ch = fase(t, 0.31, 0.42)
    queda = (1 - ch) ** 2 * 16
    ressalto = math.sin(fase(t, 0.42, 0.47) * math.pi) * 0.5
    # 3. Durante a obra, anda de um sítio para outro aos saltos.
    sitios = [(-1.6, -3.4), (-1.0, 0.8), (-2.6, -0.4), (-1.4, -3.2)]
    rots = [-40, 60, 150, -45]
    tempos = [0.47, 0.56, 0.66]
    x, y, salto, rz = sitios[0][0], sitios[0][1], 0.0, rots[0]
    for i in range(3):
        kk = fase(t, tempos[i], tempos[i] + 0.07)
        if kk > 0:
            s = suave(kk)
            x = sitios[i][0] + (sitios[i + 1][0] - sitios[i][0]) * s
            y = sitios[i][1] + (sitios[i + 1][1] - sitios[i][1]) * s
            salto = math.sin(kk * math.pi) * 1.3
            rz = rots[i] + (rots[i + 1] - rots[i]) * s
    tecnico.location = (x, y, ZP + queda + ressalto + salto + pulo * 0.8 * (1 if festa > 0.12 else 0))
    tecnico.rotation_euler = (0, 0, math.radians(rz))
    tecnico.scale = (1.15,) * 3
    for o in tecnico.children_recursive:
        o.hide_render = t < 0.305
    tecnico.hide_render = t < 0.305

    # 3. A obra: sai o velho, os azulejos viram-se em onda, entra o novo.
    poe(banheira, some(fase(t, 0.47, 0.55)))
    poe(lavatorio, some(fase(t, 0.49, 0.57)))
    poe(sanita_v, some(fase(t, 0.50, 0.58)))
    poe(mancha, some(fase(t, 0.50, 0.56)))
    for o, tipo, atraso in azulejos:
        ini = (0.52 if tipo != "chao" else 0.56) + atraso * 0.13
        kk = suave(fase(t, ini, ini + 0.07))
        fora = math.sin(kk * math.pi) * 0.75
        b = o["base"]
        if tipo == "chao":
            o.rotation_euler = (kk * math.pi, 0, 0)
            o.location = (b[0], b[1], b[2] + fora)
        else:
            o.rotation_euler = (0, 0, o["rz"] + kk * math.pi)
            o.location = (b[0] + (fora if tipo == "esq" else 0), b[1] - (fora if tipo == "fundo" else 0), b[2])
    entradas = [(duche, 0.665), (vidro, 0.69), (chuveiro, 0.71), (sanita_n, 0.72), (movel, 0.73), (espelho, 0.75), (toalha, 0.76), (tapete, 0.77)]
    for g, ini in entradas:
        kk = fase(t, ini, ini + 0.075)
        poe(g, salta(kk) if kk > 0 else 0, (1 - suave(kk)) * 0.8)

    # 4. Obra feita: estrelas por cima dos patos.
    for i, e in enumerate(estrelas):
        kk = fase(t, 0.85 + i * 0.025, 0.93 + i * 0.025)
        e.hide_render = kk <= 0
        e.scale = (max(salta(kk), 0.0001),) * 3
        an = math.radians(-50 + i * 38) + t * 3
        e.location = (0.4 + math.cos(an) * 0.3 + (i - 1) * 1.2, -2.6 + (i - 1) * 1.2, 4.4 + (0.5 if i == 1 else 0) + kk * 0.4)
        e.rotation_euler = (0, 0, math.radians(-40) + (1 - kk) * 3)


PASTA_TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "texturas")
os.makedirs(PASTA_TEX, exist_ok=True)
falta = [nome for nome, *_ in FOTOS if not os.path.exists(os.path.join(PASTA_TEX, f"foto-{nome}.png"))]
polaroides = []
if falta:
    cena_em(0.0)
    for o in (cliente, tele, clarao):
        o.hide_render = True
        for c in o.children_recursive:
            c.hide_render = True
    guarda = (cena.render.resolution_x, cena.render.resolution_y, cena.render.film_transparent, cam.data.shift_x, cam.data.lens)
    cena.render.resolution_x = cena.render.resolution_y = 640
    cena.render.film_transparent, cam.data.shift_x, cam.data.lens = False, 0.0, 40
    for nome, alvo, de in FOTOS:
        if nome not in falta:
            continue
        q.aponta(cam, Vector(alvo) + Vector(de), alvo)
        cena.render.filepath = os.path.join(PASTA_TEX, f"foto-{nome}.png")
        bpy.ops.render.render(write_still=True)
    cena.render.resolution_x, cena.render.resolution_y, cena.render.film_transparent, cam.data.shift_x, cam.data.lens = guarda
for o in [cliente] + list(cliente.children_recursive):
    o.hide_render = False
imagens_foto = {nome: bpy.data.images.load(os.path.join(PASTA_TEX, f"foto-{nome}.png")) for nome, *_ in FOTOS}
foto_tele = plano_foto("foto ecra", 1.0, material_foto(imagens_foto["banheira"], brilho=1.1), tele)
foto_tele.location = (-0.09, 0, 0)
foto_tele.rotation_euler = (0, -math.pi / 2, math.pi / 2)
foto_tele.scale = (1.7, 0.86, 1)
# Destinos em leque, à frente e por cima do cliente, virados para a câmara.
polaroides = [
    (polaroide("foto banheira", material_foto(imagens_foto["banheira"])), (2.6, -9.2, 7.8), 7),
    (polaroide("foto lavatorio", material_foto(imagens_foto["lavatorio"])), (4.6, -8.0, 8.6), -3),
    (polaroide("foto mancha", material_foto(imagens_foto["mancha"])), (6.6, -6.8, 7.8), -9),
]

os.makedirs(SAIDA, exist_ok=True)
# Com QUAK_EXPORTA, a cena só se monta (para blender/exporta_glb.py a passar para o site); não se renderiza nada.
for i in ([] if os.environ.get("QUAK_EXPORTA") else INDICES):
    caminho = os.path.join(SAIDA, f"{i:03d}.png")
    if os.path.exists(caminho) and os.path.getsize(caminho) > 0:
        continue
    cena_em(i / (N - 1))
    cena.render.filepath = caminho
    bpy.ops.render.render(write_still=True)
    print("IMAGEM", i, flush=True)
