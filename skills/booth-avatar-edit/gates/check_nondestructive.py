"""Non-destructive gate: a converted outfit against its ORIGINAL source file.

Everything that is not a vertex position must be bit-identical: topology, UVs (every layer, full precision), materials
and per-face material slots, vertex-group roster, skin weights (keyed by group NAME), custom split normals (presence
and values when the file carries them) and the shape-key structure (names and order). ONLY coordinates may differ.

usage: blender -b converted.blend --python check_nondestructive.py -- source.fbx|source.blend out.json
                [--prefix P] [--config gates_config.json] [--allow-weights Mesh1,Mesh2]

--prefix P           converted objects may be renamed with a prefix; it is stripped before matching names
--allow-weights ...  meshes whose weights were changed ON PURPOSE (opt-in, per mesh, declared in the converter's
                     report; see the spec, section 3.8). Their weights are reported but do not fail the gate.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gates_common import args_after_dashes, pop_option, load_config, fail, write_json, weights_by_name
import bpy
import numpy as np

a = args_after_dashes()
cfg = load_config(a)
prefix = pop_option(a, '--prefix', '')
allow_w = set(filter(None, (pop_option(a, '--allow-weights', '') or '').split(',')))
if len(a) != 2:
    fail('usage: converted.blend --python check_nondestructive.py -- source out.json [--prefix P] [--allow-weights M1,M2]')
src, out_json = a


def custom_normals(me):
    """(has_flag, array or None). Custom split normals live in a corner-domain attribute on recent Blender versions."""
    flag = bool(getattr(me, 'has_custom_normals', False))
    attr = me.attributes.get('custom_normal')
    if attr is None:
        return flag, None
    n = len(attr.data)
    for width in (2, 3):
        try:
            arr = np.empty(n * width)
            attr.data.foreach_get('value', arr)
            return flag, arr
        except (RuntimeError, TypeError, ValueError):
            continue
    return flag, None


def snapshot():
    """Per-mesh fingerprint of everything that is NOT vertex position."""
    snap = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.users_collection:
            continue
        me = o.data
        d = {'verts': len(me.vertices), 'polys': len(me.polygons), 'loops': len(me.loops),
             'materials': [m.name if m else None for m in me.materials],
             'uv_layers': [u.name for u in me.uv_layers],
             'vertex_groups': [g.name for g in o.vertex_groups],
             'keys': [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else []}
        d['topo'] = np.array([i for p in me.polygons for i in p.vertices], dtype=np.int64)
        d['mat_idx'] = np.array([p.material_index for p in me.polygons], dtype=np.int64)
        uvs = {}
        for u in me.uv_layers:
            arr = np.empty(len(me.loops) * 2)
            try:
                u.uv.foreach_get('vector', arr)
            except AttributeError:
                u.data.foreach_get('uv', arr)
            uvs[u.name] = arr
        d['_uvs'] = uvs
        d['_weights'] = weights_by_name(o)
        d['cn_flag'], d['_cn'] = custom_normals(me)
        snap[o.name] = d
    return snap


conv = snapshot()
if not conv:
    fail('no meshes in the converted file')
bpy.ops.wm.read_factory_settings(use_empty=True)
if not _os.path.exists(src):
    fail(f'source not found: {src}')
if src.lower().endswith('.fbx'):
    bpy.ops.import_scene.fbx(filepath=src)
else:
    bpy.ops.wm.open_mainfile(filepath=src)
orig = snapshot()
if not orig:
    fail('no meshes in the source file')

rep = {'source': src, 'checked': [], 'missing_in_source': [], 'uv_mismatches': {}, 'topology_mismatches': [],
       'material_mismatches': [], 'weight_mismatches': {}, 'weight_changes_allowed': {}, 'key_structure_mismatches': [],
       'vertex_group_mismatches': [], 'custom_normal_mismatches': {}, 'custom_normals_compared': False}


def match_name(n):
    if n in orig:
        return n
    base = n[len(prefix):] if prefix and n.startswith(prefix) else n
    for cand in (base, base.split('.')[0]):
        if cand in orig:
            return cand
    hits = [k for k in orig if k.startswith(base.split('.')[0])]
    return hits[0] if len(hits) == 1 else None


for name, c in conv.items():
    o = match_name(name)
    if o is None:
        rep['missing_in_source'].append(name)
        continue
    s = orig[o]
    rep['checked'].append([name, o])
    if c['verts'] != s['verts'] or c['polys'] != s['polys'] or not np.array_equal(c['topo'], s['topo']):
        rep['topology_mismatches'].append(name)
    if c['materials'] != s['materials'] or not np.array_equal(c['mat_idx'], s['mat_idx']):
        rep['material_mismatches'].append(name)
    if c['vertex_groups'] != s['vertex_groups']:
        rep['vertex_group_mismatches'].append(name)
    if c['keys'] != s['keys']:
        rep['key_structure_mismatches'].append(name)
    if c['uv_layers'] != s['uv_layers']:
        rep['uv_mismatches'][name] = f'layer names differ: {c["uv_layers"]} vs {s["uv_layers"]}'
    else:
        for u in c['uv_layers']:
            ca, sa = c['_uvs'][u], s['_uvs'][u]
            if ca.shape != sa.shape:
                rep['uv_mismatches'][name] = f'{u}: length {ca.shape} vs {sa.shape}'
            else:
                md = float(np.abs(ca - sa).max()) if ca.size else 0.0
                if md > 0:
                    rep['uv_mismatches'][name] = {'layer': u, 'max_abs_delta': md,
                                                  'loops_changed': int((np.abs(ca - sa) > 0).sum())}
    if c['_weights'] != s['_weights']:
        diffs = [k for k in set(c['_weights']) | set(s['_weights'])
                 if c['_weights'].get(k) != s['_weights'].get(k)]
        base_name = o
        if name in allow_w or base_name in allow_w:
            rep['weight_changes_allowed'][name] = len(diffs)
        else:
            rep['weight_mismatches'][name] = len(diffs)
    if c['cn_flag'] != s['cn_flag']:
        rep['custom_normal_mismatches'][name] = f'has_custom_normals {s["cn_flag"]} -> {c["cn_flag"]}'
    elif c['_cn'] is not None and s['_cn'] is not None:
        rep['custom_normals_compared'] = True
        if c['_cn'].shape != s['_cn'].shape or not np.array_equal(c['_cn'], s['_cn']):
            rep['custom_normal_mismatches'][name] = 'custom normal values differ'

if not rep['checked']:
    fail('no converted mesh could be matched to a source mesh (names differ? use --prefix)')

rep['PASS'] = not (rep['uv_mismatches'] or rep['topology_mismatches'] or rep['material_mismatches']
                   or rep['weight_mismatches'] or rep['key_structure_mismatches'] or rep['vertex_group_mismatches']
                   or rep['custom_normal_mismatches'])
write_json(out_json, rep)
print('NONDESTRUCTIVE', 'PASS' if rep['PASS'] else 'FAIL',
      {k: v for k, v in rep.items() if k not in ('checked', 'source') and v})
print('  meshes compared:', len(rep['checked']), ' custom normals compared:', rep['custom_normals_compared'])
