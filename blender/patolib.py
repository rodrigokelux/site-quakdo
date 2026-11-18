# Biblioteca do pato da Quakdo para o Blender: materiais, formas, o pato e o seu guarda-roupa.
# Usada por cena.py (o filme da obra) e elenco.py (os patos sozinhos). O pato olha para +X; Z é para cima.
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_MATS = {}


def lin(h):  # cor sRGB (hex) para linear, que é o que o Blender espera
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (c(h >> 16 & 255), c(h >> 8 & 255), c(h & 255), 1)


def material(nome, cor, rug=0.35, verniz=0.0, sss=0.0, emite=0.0, metal=0.0, vidro=0.0):
    if nome in _MATS:
        return _MATS[nome]
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = lin(cor)
    p.inputs["Roughness"].default_value = rug
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = verniz
    p.inputs["Coat Roughness"].default_value = 0.15
    p.inputs["Subsurface Weight"].default_value = sss
    p.inputs["Subsurface Radius"].default_value = (0.6, 0.35, 0.1)
    p.inputs["Subsurface Scale"].default_value = 0.25
    p.inputs["Transmission Weight"].default_value = vidro
    if emite:
        p.inputs["Emission Color"].default_value = lin(cor)
        p.inputs["Emission Strength"].default_value = emite
    _MATS[nome] = m
    return m


def liga(o, pai=None):
    bpy.context.scene.collection.objects.link(o)
    o.parent = pai
    return o


def vazio(nome, pai=None):
    return liga(bpy.data.objects.new(nome, None), pai)


def suave(o, niveis=0):
    for p in o.data.polygons:
        p.use_smooth = True
    if niveis:
        s = o.modifiers.new("sub", "SUBSURF")
        s.levels = s.render_levels = niveis
    return o


def de_bmesh(nome, bm, mat, pai=None):
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    if mat:
        me.materials.append(mat)
    return liga(bpy.data.objects.new(nome, me), pai)


def esfera(nome, raio, pos, mat, pai=None, escala=(1, 1, 1), seg=40):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=raio)
    o = suave(de_bmesh(nome, bm, mat, pai))
    o.location, o.scale = pos, escala
    return o


def caixa(nome, dim, pos, mat, pai=None, canto=0.12):
    """Caixa (dim = x, y, z). canto arredonda as arestas; 0 deixa-as vivas."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co = Vector((v.co.x * dim[0], v.co.y * dim[1], v.co.z * dim[2]))
    o = de_bmesh(nome, bm, mat, pai)
    o.location = pos
    if canto:
        suave(o)
        b = o.modifiers.new("canto", "BEVEL")
        b.width, b.segments = min(canto, min(dim) * 0.49), 5
        o.modifiers.new("normais", "WEIGHTED_NORMAL")
    return o


def cilindro(nome, raio, alt, pos, mat, pai=None, seg=48, raio2=None, canto=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=raio, radius2=raio if raio2 is None else raio2, depth=alt)
    o = suave(de_bmesh(nome, bm, mat, pai))
    o.location = pos
    if canto:
        b = o.modifiers.new("canto", "BEVEL")
        b.width, b.segments, b.limit_method, b.angle_limit = canto, 4, "ANGLE", math.radians(40)
    o.modifiers.new("normais", "WEIGHTED_NORMAL")
    return o


def toro(nome, raio, tubo, pos, mat, pai=None):
    bm = bmesh.new()
    seg, lados = 48, 14
    vs = [[bm.verts.new(((raio + tubo * math.cos(b)) * math.cos(a), (raio + tubo * math.cos(b)) * math.sin(a), tubo * math.sin(b)))
           for b in [j / lados * math.tau for j in range(lados)]] for a in [i / seg * math.tau for i in range(seg)]]
    for i in range(seg):
        for j in range(lados):
            bm.faces.new((vs[i][j], vs[(i + 1) % seg][j], vs[(i + 1) % seg][(j + 1) % lados], vs[i][(j + 1) % lados]))
    o = suave(de_bmesh(nome, bm, mat, pai))
    o.location = pos
    return o


def tubo(nome, pontos, raio, mat, pai=None):
    cu = bpy.data.curves.new(nome, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps = raio, 8, True
    s = cu.splines.new("POLY")
    s.points.add(len(pontos) - 1)
    for q, p in zip(s.points, pontos):
        q.co = (p[0], p[1], p[2], 1)
    cu.materials.append(mat)
    return liga(bpy.data.objects.new(nome, cu), pai)


def estrela(nome, pos, mat, pai=None, raio=0.5):
    bm = bmesh.new()
    vs = []
    for i in range(10):
        r = raio * (0.46 if i % 2 else 1)
        an = i / 10 * math.tau + math.pi / 2
        vs.append(bm.verts.new((0, math.cos(an) * r, math.sin(an) * r)))
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.x += raio * 0.34
    o = de_bmesh(nome, bm, mat, pai)
    o.location = pos
    b = o.modifiers.new("canto", "BEVEL")
    b.width, b.segments = raio * 0.09, 4
    return o


# ---------------- O pato ----------------
CAB = Vector((0.52, 0, 0.98))  # centro da cabeça
RC = 0.79                      # raio da cabeça
_corpo = {}


def _deforma_corpo(x, y, z):
    px, py, pz = x * 1.34, y * 1.12, z * 0.88
    t = min(1, max(0, (-x - 0.3) / 0.7))
    s = t * t * (3 - 2 * t)
    return px - 0.12 * s, py * (1 - 0.82 * s), pz + 1.05 * s * t ** 1.3


VISTO_PTS = [(-0.42, -0.02), (-0.16, -0.26), (0.3, 0.2)]   # o visto do logótipo, em (u, z) no flanco


def _pinta_visto(me):
    """O visto do logótipo pintado na pele (atributo 'visto', 0 a 1), como uma impressão, nos dois flancos."""
    me.update()
    at = me.attributes.new("visto", "FLOAT", "POINT")
    vals = []
    for v in me.vertices:
        c, n = v.co, v.normal
        if abs(n.y) < 0.15 or abs(c.y) < 0.12:
            vals.append(0.0)
            continue
        u = c.x - 0.12 if c.y < 0 else 0.12 - c.x
        d = 9.0
        for (x0, z0), (x1, z1) in zip(VISTO_PTS, VISTO_PTS[1:]):
            dx, dz = x1 - x0, z1 - z0
            k = max(0.0, min(1.0, ((u - x0) * dx + (c.z - z0) * dz) / (dx * dx + dz * dz)))
            d = min(d, math.hypot(u - x0 - k * dx, c.z - z0 - k * dz))
        w = 0.07
        vals.append(max(0.0, min(1.0, (w + 0.012 - d) / 0.024)))
    at.data.foreach_set("value", vals)


def _entrada(no, ident, saida=False):
    for s in (no.outputs if saida else no.inputs):
        if s.identifier == ident:
            return s
    raise KeyError(ident)


def _material_pato(com_visto):
    """O vinil amarelo do pato. Com o visto, lê o atributo 'visto' para a cor e para um relevo leve."""
    nome = "amarelo visto" if com_visto else "amarelo"
    if nome in _MATS:
        return _MATS[nome]
    m = material(nome, 0xFFC01A, rug=0.4, verniz=0.22, sss=0.14)
    if com_visto:
        nt = m.node_tree
        p = nt.nodes["Principled BSDF"]
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "visto"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        nt.links.new(at.outputs["Fac"], _entrada(mix, "Factor_Float"))
        _entrada(mix, "A_Color").default_value = lin(0xFFC01A)
        _entrada(mix, "B_Color").default_value = lin(0xE28E00)
        nt.links.new(_entrada(mix, "Result_Color", True), p.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.invert = True
        bump.inputs["Strength"].default_value = 0.35
        bump.inputs["Distance"].default_value = 0.03
        nt.links.new(at.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def _malha_corpo():
    """Corpo, cabeça e cauda fundidos numa só peça e alisados. Feito uma vez e partilhado por todos os patos."""
    if _corpo:
        return _corpo
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=72, v_segments=44, radius=1)
    for v in bm.verts:
        v.co = Vector(_deforma_corpo(*v.co))
    for v in bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=40, radius=RC)["verts"]:
        v.co += CAB
    bruto = de_bmesh("bruto", bm, None)
    rm = bruto.modifiers.new("funde", "REMESH")
    rm.mode, rm.voxel_size = "VOXEL", 0.018
    sm = bruto.modifiers.new("alisa", "SMOOTH")
    sm.factor, sm.iterations = 1.0, 45
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(bruto.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(bruto)
    for v in me.vertices:                       # base achatada, para assentar no chão
        if v.co.z < -0.58:
            v.co.z = -0.58 + (v.co.z + 0.58) * 0.28
    for p in me.polygons:
        p.use_smooth = True
    _pinta_visto(me)
    me.materials.append(_material_pato(True))
    _corpo["malha"] = me
    _corpo["zmin"] = min(v.co.z for v in me.vertices)
    _corpo["frente"] = max(v.co.x for v in me.vertices if v.co.z > CAB.z - 0.2)
    tmp = liga(bpy.data.objects.new("tmp", me))
    bpy.context.view_layer.update()
    _corpo["arvore"] = BVHTree.FromObject(tmp, bpy.context.evaluated_depsgraph_get())
    bpy.data.objects.remove(tmp)
    return _corpo


def na_pele(de, direcao=(-1, 0, 0)):
    """O ponto da pele do pato atingido por um raio lançado de 'de'. Serve para pousar botões, bolsos, crachás."""
    toque, normal, *_ = _malha_corpo()["arvore"].ray_cast(Vector(de), Vector(direcao))
    return (toque, normal) if toque else (Vector(de), Vector((1, 0, 0)))


def _bico(nome, baixo, mat, pai):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1)
    for v in bm.verts:
        x, y, z = v.co.z, v.co.x, v.co.y
        xx = math.copysign(abs(x) ** 0.7, x)
        u = (xx + 1) / 2
        ly = y * 0.5 * (1 + 0.14 * math.sin(math.pi * min(1, u * 1.1))) * (0.92 if baixo else 1)
        if baixo:
            lz = z * 0.05 if z > 0 else z * 0.24 * (1 - 0.3 * u)
        else:
            lz = z * (0.46 * (1 - u) ** 2 + 0.15) if z > 0 else z * 0.07
        v.co = Vector((xx * (0.44 if baixo else 0.54), ly, lz + 0.2 * u * u)) * 0.8
    return suave(de_bmesh(nome, bm, mat, pai), 1)


def _casca(planos, mat, pai, k=1.028):
    """Roupa justa ao corpo: a pele do pato cortada por planos (cortes limpos) e posta um pouco para fora.
    Cada plano é (ponto, normal); fica o lado contrário à normal. Ex.: ((0, 0, 0.4), (0, 0, 1)) fica com z < 0.4."""
    bm = bmesh.new()
    bm.from_mesh(_malha_corpo()["malha"])
    for co, no in planos:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(co), plane_no=Vector(no).normalized(), clear_outer=True)
    c = Vector((0.1, 0, 0.1))
    for v in bm.verts:
        v.co = c + (v.co - c) * k
    return suave(de_bmesh("roupa", bm, mat, pai))


CIMA, BAIXO, FRENTE, TRAS, ESQ, DIR = (0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)


def _abaixo(z):
    return ((0, 0, z), CIMA)


def _caixa_planos(x0=None, x1=None, y0=None, y1=None, z0=None, z1=None):
    p = []
    if x0 is not None: p.append(((x0, 0, 0), TRAS))
    if x1 is not None: p.append(((x1, 0, 0), FRENTE))
    if y0 is not None: p.append(((0, y0, 0), DIR))
    if y1 is not None: p.append(((0, y1, 0), ESQ))
    if z0 is not None: p.append(((0, 0, z0), BAIXO))
    if z1 is not None: p.append(((0, 0, z1), CIMA))
    return p


def _botao(pos_raio, mat, pai, raio=0.065):
    p, n = na_pele(pos_raio)
    esfera("botao", raio, p + n * 0.045, mat, pai, escala=(1, 1, 1), seg=16)


def _capacete(pai, cor_nome, cor):
    m = material(cor_nome, cor, rug=0.3, verniz=0.5)
    ch = vazio("capacete", pai)
    ch.location = CAB + Vector((-0.06, 0, RC * 0.5))
    ch.rotation_euler = (0, math.radians(-7), 0)
    R = RC * 1.035
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=56, v_segments=28, radius=R)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.01], context="VERTS")
    suave(de_bmesh("cupula", bm, m, ch)).scale = (1.02, 1, 0.7)
    cilindro("rebordo", R * 1.07, 0.09, (0, 0, 0.0), m, ch, canto=0.035)
    pala = cilindro("pala", R * 0.82, 0.075, (R * 0.55, 0, -0.005), m, ch, canto=0.03)
    pala.scale = (1, 1.12, 1)
    for dy, alt in ((0, 0.9), (0.3, 0.84), (-0.3, 0.84)):                   # nervuras por cima
        esfera("nervura", 1, (0.0, dy, 0.0), m, ch, escala=(R * 0.96, 0.075, R * alt * 0.86), seg=32)
    return ch


def _bone(pai, cor_nome, cor):
    m = material(cor_nome, cor, rug=0.6)
    ch = vazio("bone", pai)
    ch.location = CAB + Vector((-0.05, 0, RC * 0.52))
    ch.rotation_euler = (0, math.radians(-6), 0)
    R = RC * 1.03
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=56, v_segments=28, radius=R)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.01], context="VERTS")
    suave(de_bmesh("cupula", bm, m, ch)).scale = (1, 1, 0.64)
    pala = cilindro("pala", R * 0.7, 0.07, (R * 0.72, 0, 0.0), m, ch, canto=0.03)
    pala.scale = (1.05, 1, 1)
    esfera("botao", 0.07, (0, 0, R * 0.64), m, ch, seg=16)
    return ch


def _macacao(pai, cor_nome, cor, ferramenta=True):
    """Jardineiras: calças, peitilho, alças com botões e bolso no peito (com uma chave de fendas)."""
    m = material(cor_nome, cor, rug=0.65)
    esc = material(cor_nome + " escuro", cor, rug=0.8)
    _casca([_abaixo(-0.04)], m, pai)                                                   # calças
    _casca(_caixa_planos(x0=0.3, y0=-0.5, y1=0.5, z0=-0.1, z1=0.4), m, pai)            # peitilho
    for lado in (1, -1):                                                               # alças
        _casca(_caixa_planos(x1=0.95, y0=min(0.3 * lado, 0.46 * lado), y1=max(0.3 * lado, 0.46 * lado), z0=-0.1, z1=0.66), m, pai, 1.03)
    _casca(_caixa_planos(x0=0.8, y0=-0.27, y1=0.27, z0=-0.03, z1=0.26), esc, pai, 1.05)  # bolso
    lat = material("latao", 0xFFD25A, rug=0.25, metal=1.0)
    for lado in (1, -1):
        _botao((3, 0.385 * lado, 0.36), lat, pai)
    if ferramenta:
        p, n = na_pele((3, 0.1, 0.28))
        cabo = cilindro("chave fendas", 0.06, 0.3, p + n * 0.1 + Vector((0, 0, 0.12)), material("cabo laranja", 0xFF7410, rug=0.4), pai, seg=20, canto=0.02)
        cabo.rotation_euler = (0, math.radians(14), 0)
        p2, n2 = na_pele((3, -0.1, 0.28))
        lap = cilindro("lapis", 0.032, 0.26, p2 + n2 * 0.08 + Vector((0, 0, 0.1)), material("lapis", 0xFFC928, rug=0.5), pai, seg=12)
        lap.rotation_euler = (0, math.radians(14), 0)


def _visto(pai):
    """O visto do logótipo, grande e meio embutido nos dois flancos."""
    C = _malha_corpo()
    m = material("visto", 0xE59A00, rug=0.5, verniz=0.1)
    for lado in (-1, 1):
        pts = [(-0.6, 0.02), (-0.2, -0.36), (0.62, 0.42)]
        dens = [(x0 + (x1 - x0) * i / 16, z0 + (z1 - z0) * i / 16) for (x0, z0), (x1, z1) in zip(pts, pts[1:]) for i in range(16)] + [pts[-1]]
        pontos = []
        for u, z in dens:
            x = (u if lado == -1 else -u) + 0.2
            toque, *_ = C["arvore"].ray_cast(Vector((x, lado * 4, z - 0.02)), Vector((0, -lado, 0)))
            toque = toque or Vector((x, lado, z))
            pontos.append((toque.x, toque.y - lado * 0.07, toque.z))
        tubo("visto", pontos, 0.11, m, pai)


def faz_pato(nome="pato", roupa=()):
    """Devolve o vazio-pai do pato. roupa: ver ROUPAS em elenco.py."""
    C = _malha_corpo()
    pai = vazio(nome)
    corpo = liga(bpy.data.objects.new(nome + "_corpo", C["malha"]), pai)
    fr = C["frente"]
    _bico("bico", False, material("bico", 0xFF7A14, rug=0.38, verniz=0.2, sss=0.1), pai).location = (fr + 0.06, 0, CAB.z - 0.14)
    esc = material("bico escuro", 0xD44700, rug=0.45, verniz=0.1)
    _bico("bico_baixo", True, esc, pai).location = (fr + 0.01, 0, CAB.z - 0.215)
    for lado in (1, -1):
        esfera("narina", 0.03, (fr + 0.12, 0.09 * lado, CAB.z + 0.03), esc, pai, seg=16)
        d = Vector((0.7, 0.6 * lado, 0.26)).normalized()
        p = CAB + d * (RC * 0.955)
        olho = esfera("olho", 0.15, p, material("olho", 0x0A0D16, rug=0.06, verniz=1.0), pai)
        olho.rotation_mode = "QUATERNION"
        olho.rotation_quaternion = d.to_track_quat("Z", "Y")
        olho.scale = (1, 1, 0.5)
        esfera("brilho", 0.042, p + d * 0.046 + Vector((0.04, 0, 0.06)), material("brilho", 0xFFFFFF, emite=3.0), pai, seg=16)

    r = set(roupa)
    vestido = r & {"macacao", "macacao branco", "fato", "camisa"}
    if vestido:                                   # com roupa, o vinil fica liso (o visto ficaria meio tapado)
        corpo.material_slots[0].link = "OBJECT"
        corpo.material_slots[0].material = _material_pato(False)
    if "macacao" in r:
        _macacao(pai, "ganga", 0x1E5FC4)
    if "macacao branco" in r:                    # pintor: jardineiras brancas com pingos de tinta
        _macacao(pai, "pano branco", 0xF4F6FA, ferramenta=False)
        for (y, z), cor in zip(((0.34, -0.2), (-0.2, -0.32), (0.05, 0.12), (-0.42, 0.0), (0.5, -0.38)), (0x2D55B3, 0xFFC928, 0xFF7410, 0x2D55B3, 0xFFC928)):
            p, n = na_pele((3, y, z))
            pingo = esfera("pingo", 0.1, p + n * 0.02, material(f"tinta {cor:x}", cor, rug=0.3, verniz=0.6), pai, seg=16)
            pingo.scale = (0.3, 1 + abs(y), 1.2)
    if "camisa" in r or "fato" in r:
        _casca([_abaixo(0.5)], material("camisa", 0xFBFCFE, rug=0.7), pai)
        for lado in (1, -1):                      # gola
            p, n = na_pele((3, 0.2 * lado, 0.47))
            g = caixa("gola", (0.05, 0.3, 0.2), p + n * 0.03, material("camisa", 0xFBFCFE, rug=0.7), pai, canto=0.02)
            g.rotation_euler = (math.radians(28 * lado), math.radians(-18), 0)
    if "fato" in r:                               # casaco escuro aberto à frente e gravata
        fato = material("fato", 0x16223F, rug=0.75)
        _casca([_abaixo(0.46), ((0.35, 0, 0), FRENTE)], fato, pai, 1.045)                      # costas e lados
        for lado in (1, -1):                                                           # as duas abas da frente, em V
            _casca([_abaixo(0.46), ((0.3, 0, 0), TRAS), ((0, 0.1 * lado, -0.1), (0, -lado, 0.45))], fato, pai, 1.045)
        p, n = na_pele((3, 0, 0.16))
        esfera("gravata", 1, p + n * 0.03 + Vector((0, 0, 0.0)), material("gravata", 0x2D55B3, rug=0.5), pai, escala=(0.05, 0.085, 0.3), seg=24)
        p, n = na_pele((3, 0, 0.43))
        esfera("no", 0.075, p + n * 0.04, material("gravata", 0x2D55B3, rug=0.5), pai, seg=16)
    if "cracha" in r:                             # cordão azul ao pescoço, com crachá
        az = material("cordao", 0x2D55B3, rug=0.5)
        pontos = []
        for i in range(21):
            k = i / 20
            y = -0.4 + 0.8 * k
            z = 0.5 - 0.42 * (1 - abs(2 * k - 1))
            p, n = na_pele((3, y, z))
            pontos.append(tuple(p + n * 0.05))
        tubo("cordao", pontos, 0.028, az, pai)
        p, n = na_pele((3, 0, -0.06))
        c = caixa("cracha", (0.04, 0.26, 0.34), p + n * 0.06, material("cartao", 0xFFFFFF, rug=0.4), pai, canto=0.02)
        c.rotation_euler = (0, math.radians(-16), 0)
        caixa("cracha risca", (0.045, 0.2, 0.08), p + n * 0.065 + Vector((0, 0, 0.06)), az, pai, canto=0.0).rotation_euler = (0, math.radians(-16), 0)
    if "capacete" in r:
        _capacete(pai, "capacete branco", 0xF4F6FA)
    if "capacete laranja" in r:
        _capacete(pai, "capacete laranja", 0xFF7410)
    if "bone" in r:
        _bone(pai, "bone azul", 0x2D55B3)
    if "bone branco" in r:
        _bone(pai, "bone branco", 0xF4F6FA)
    pai["zmin"] = C["zmin"]
    return pai


# ---------------- Adereços pousados ao lado do pato ----------------
def adereco(tipo, pai, pos):
    g = vazio(tipo, pai)
    g.location = pos
    M = material
    aco = M("aco", 0xD3D9E4, rug=0.2, metal=1.0)
    if tipo == "tablet":
        caixa("corpo", (0.07, 0.95, 0.7), (0, 0, 0.35), M("tablet", 0x9AA3B5, rug=0.3, metal=0.6), g, canto=0.04)
        caixa("ecra", (0.02, 0.84, 0.59), (0.04, 0, 0.35), M("ecra", 0x8FBCFF, emite=1.0), g, canto=0.0)
        g.rotation_euler = (0, math.radians(-24), math.radians(-18))
    elif tipo == "prancheta":
        caixa("tabua", (0.06, 0.8, 1.05), (0, 0, 0.52), M("prancheta", 0x3A4254, rug=0.6), g, canto=0.03)
        caixa("folha", (0.02, 0.66, 0.84), (0.04, 0, 0.48), M("papel", 0xFFFFFF, rug=0.8), g, canto=0.0)
        caixa("mola", (0.07, 0.3, 0.12), (0.03, 0, 1.0), aco, g, canto=0.03)
        for i in range(4):
            caixa("linha", (0.022, 0.5 if i < 3 else 0.3, 0.045), (0.05, 0 if i < 3 else 0.1, 0.72 - i * 0.14), M("cordao", 0x2D55B3, rug=0.5) if i == 0 else M("linha", 0xB9C2D6, rug=0.8), g, canto=0.0)
        g.rotation_euler = (0, math.radians(-20), math.radians(-14))
    elif tipo == "rolo":
        r = cilindro("rolo", 0.17, 0.66, (0, 0, 1.25), M("rolo", 0x2D55B3, rug=0.9), g, canto=0.03)
        r.rotation_euler = (math.pi / 2, 0, 0)
        tubo("arame", [(0, 0.33, 1.25), (0, 0.44, 1.25), (0, 0.44, 0.98), (0, 0, 0.9), (0, 0, 0.7)], 0.028, aco, g)
        cilindro("cabo", 0.06, 0.72, (0, 0, 0.36), M("cabo laranja", 0xFF7410, rug=0.4), g, seg=20, canto=0.02)
        b = cilindro("balde", 0.34, 0.5, (0.2, -0.75, 0.25), M("balde", 0xF4F6FA, rug=0.35), g, raio2=0.4, canto=0.02)
        cilindro("tinta", 0.36, 0.03, (0.2, -0.75, 0.47), M("rolo", 0x2D55B3, rug=0.3), g)
        g.rotation_euler = (0, math.radians(6), 0)
    elif tipo == "cabo":
        for i in range(3):
            toro("cabo", 0.36, 0.07, (0, 0, 0.08 + i * 0.13), M("cabo eletrico", 0xFF7410, rug=0.5), g)
        caixa("ficha", (0.2, 0.26, 0.16), (0.42, 0.25, 0.4), M("ficha", 0x16223F, rug=0.4), g, canto=0.04)
        for dy in (-0.07, 0.07):
            cilindro("pino", 0.022, 0.14, (0.56, 0.25 + dy, 0.4), aco, g, seg=12).rotation_euler = (0, math.pi / 2, 0)
    elif tipo == "chave":
        verm = M("chave vermelha", 0xD8362B, rug=0.4, verniz=0.3)
        caixa("cabo", (0.13, 0.2, 1.0), (0, 0, 0.5), verm, g, canto=0.05)
        caixa("cabeca", (0.15, 0.46, 0.2), (0, 0.1, 1.05), verm, g, canto=0.04)
        caixa("mordente", (0.14, 0.34, 0.12), (0, 0.16, 1.28), aco, g, canto=0.03)
        caixa("haste", (0.1, 0.1, 0.34), (0, 0.27, 1.15), aco, g, canto=0.02)
        g.rotation_euler = (math.radians(-14), 0, math.radians(20))
        cano = M("cano", 0xB9C2D0, rug=0.3, metal=1.0)
        tubo("cano", [(0.25, -0.95, 0.14), (0.25, -0.45, 0.14), (0.25, -0.45, 0.62)], 0.13, cano, g)
        toro("uniao", 0.14, 0.045, (0.25, -0.45, 0.62), cano, g)
    return g


# ---------------- Render ----------------
def prepara_render(larg, alt, amostras):
    cena = bpy.context.scene
    cena.render.engine = "CYCLES"
    pr = bpy.context.preferences.addons["cycles"].preferences
    cena.cycles.device = "CPU"
    for tipo in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            pr.compute_device_type = tipo
            pr.get_devices()
            if [d for d in pr.devices if d.type == tipo]:
                for d in pr.devices:
                    d.use = d.type == tipo
                cena.cycles.device = "GPU"
                break
        except Exception:
            pass
    print("render em", cena.cycles.device, flush=True)
    cena.cycles.samples = amostras
    cena.cycles.use_denoising = True
    cena.cycles.use_adaptive_sampling = True
    cena.cycles.adaptive_threshold = 0.03
    cena.cycles.max_bounces = 5
    cena.render.use_persistent_data = True
    cena.render.resolution_x, cena.render.resolution_y = larg, alt
    cena.render.film_transparent = True
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_mode = "RGBA"
    cena.view_settings.view_transform = "Standard"
    cena.view_settings.look = "None"
    return cena


def luz(pos, tam, forca, cor=(1, 1, 1), alvo=(0, 0, 0.5)):
    d = bpy.data.lights.new("luz", "AREA")
    d.shape, d.size, d.size_y, d.energy, d.color = "RECTANGLE", tam[0], tam[1], forca, cor
    o = liga(bpy.data.objects.new("luz", d))
    o.location = pos
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = (Vector(alvo) - Vector(pos)).to_track_quat("-Z", "Y")
    return o


def mundo(forca=0.38, cor=(1, 0.97, 0.92, 1)):
    cena = bpy.context.scene
    cena.world = bpy.data.worlds.new("mundo")
    cena.world.use_nodes = True
    f = cena.world.node_tree.nodes["Background"]
    f.inputs[0].default_value, f.inputs[1].default_value = cor, forca


def chao_sombra(z, tam=80):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=tam)
    o = de_bmesh("chao", bm, None)
    o.location.z = z
    o.is_shadow_catcher = True
    return o


def camara(lente=85):
    cena = bpy.context.scene
    cam = liga(bpy.data.objects.new("cam", bpy.data.cameras.new("cam")))
    cam.data.lens = lente
    cam.rotation_mode = "QUATERNION"
    cena.camera = cam
    return cam


def aponta(cam, olho, alvo):
    cam.location = olho
    cam.rotation_quaternion = (Vector(alvo) - Vector(olho)).to_track_quat("-Z", "Y")


def esconde(pato, sim):
    pato.hide_render = sim
    for o in pato.children_recursive:
        o.hide_render = sim
