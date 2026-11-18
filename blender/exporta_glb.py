# Passa a cena do filme (cena.py) para um ficheiro 3D (GLB) que o site desenha ao vivo, com Three.js.
# Correr: blender -b -P blender/exporta_glb.py -- <ficheiro.glb>
# Monta a cena sem renderizar, pinta o visto do pato como cor dos vértices, simplifica os patos e exporta tudo:
# as posições iniciais e os valores de cada peça (base, rz) seguem como "extras" para o site animar.
import bpy, sys, os
SAIDA_GLB = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
AQUI = os.path.dirname(os.path.abspath(__file__))
os.environ["QUAK_EXPORTA"] = "1"
sys.argv = [sys.argv[0], "--", os.path.join(AQUI, "saida", "nada"), "640", "1", "2"]
exec(compile(open(os.path.join(AQUI, "cena.py"), encoding="utf-8").read(), "cena.py", "exec"))

import patolib as q

# O visto: do atributo 'visto' (0 a 1) para uma cor de vértice, amarelo a mostarda.
me = q._corpo["malha"]
vis = [0.0] * len(me.vertices)
me.attributes["visto"].data.foreach_get("value", vis)
a, b = q.lin(0xFFC01A), q.lin(0xE28E00)
cor = me.color_attributes.new("Col", "BYTE_COLOR", "POINT")
cores = []
for k in vis:
    cores += [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k, 1.0]
cor.data.foreach_set("color", cores)
me.color_attributes.active_color = cor

# Os patos têm muitos polígonos (para o render); para o site chega um quarto.
for o in bpy.data.objects:
    if o.type == "MESH" and o.data == me:
        d = o.modifiers.new("simplifica", "DECIMATE")
        d.ratio = 0.22

# Os objetos ficam com o nome do grupo à frente, para o site os encontrar.
for o in bpy.data.objects:
    for k in ("base", "rz"):
        if k in o.keys():
            o[k] = [float(x) for x in o[k]] if k == "base" else float(o[k])

opcoes = dict(filepath=SAIDA_GLB, export_format="GLB", export_apply=True, export_extras=True, export_yup=True,
              export_cameras=False, export_lights=False, export_materials="EXPORT", export_image_format="WEBP")
try:
    bpy.ops.export_scene.gltf(**opcoes, export_vertex_color="ACTIVE")
except TypeError:
    bpy.ops.export_scene.gltf(**opcoes)
print("EXPORTADO", SAIDA_GLB, os.path.getsize(SAIDA_GLB) // 1024, "KB", flush=True)
