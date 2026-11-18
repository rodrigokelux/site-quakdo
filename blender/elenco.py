# O elenco da Quakdo: cada pato sozinho, em fundo transparente, para o site.
# Correr: blender -b -P blender/elenco.py -- <pasta> <largura> <amostras> [nomes...]
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patolib as q

a = sys.argv[sys.argv.index("--") + 1:]
SAIDA, LARG, AMOSTRAS = os.path.abspath(a[0]), int(a[1]), int(a[2])

# nome: (roupa, adereço pousado ao lado)
ELENCO = {
    "cliente": ((), None),
    "tecnico": (("capacete", "macacao"), None),
    "gestor": (("fato",), "tablet"),
    "coordenador": (("camisa", "cracha"), "prancheta"),
    "pintor": (("bone branco", "macacao branco"), "rolo"),
    "eletricista": (("capacete laranja", "macacao"), "cabo"),
    "canalizador": (("bone", "macacao"), "chave"),
}
NOMES = a[3:] or list(ELENCO) + ["empresa"]

bpy.ops.wm.read_factory_settings(use_empty=True)
cena = q.prepara_render(LARG, LARG, AMOSTRAS)
q.mundo(0.36)
q.luz((4.5, -5.5, 8), (9, 9), 950)
q.luz((-6, 4, 4), (6, 6), 300, (0.75, 0.86, 1.0))
cam = q.camara(85)

patos = {}
for n in ELENCO:
    if n in NOMES or ("empresa" in NOMES and n in ("tecnico", "gestor", "coordenador")):
        roupa, coisa = ELENCO[n]
        p = q.faz_pato(n, roupa)
        if coisa:
            q.adereco(coisa, p, (0.95, -1.25, p["zmin"]))
        patos[n] = p
q.chao_sombra(next(iter(patos.values()))["zmin"])
os.makedirs(SAIDA, exist_ok=True)


def tira(nome):
    cena.render.filepath = os.path.join(SAIDA, f"{nome}.png")
    bpy.ops.render.render(write_still=True)
    print("FEITO", nome, flush=True)


for nome in NOMES:
    for p in patos.values():
        q.esconde(p, True)
        p.location, p.rotation_euler, p.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
    if nome == "empresa":                         # os três juntos: uma empresa com vários trabalhadores
        for n, pos, rz, s in (("coordenador", (0.6, 2.1, 0), -8, 0.95), ("gestor", (-2.1, -0.7, 0), 6, 0.95), ("tecnico", (0.3, -0.3, 0), 0, 1.0)):
            q.esconde(patos[n], False)
            patos[n].location, patos[n].rotation_euler, patos[n].scale = pos, (0, 0, math.radians(rz)), (s, s, s)
            patos[n].location.z = patos[n]["zmin"] * (s - 1)
        q.aponta(cam, (11.6, -12.6, 5.2), (-0.3, 0.4, 0.55))
    else:
        q.esconde(patos[nome], False)
        q.aponta(cam, (7.3, -8.1, 3.4), (0.15, -0.25, 0.62))
    tira(nome)
