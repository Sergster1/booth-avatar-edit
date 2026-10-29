"""Vertex-ID gate: did vertex IDs move between the pristine purchased file and the current body?

Shape keys, UV maps, vertex groups and engine blendshape data are all stored BY VERTEX INDEX. If index 4211 means a
different point than it used to, the rig still skins, the mesh still renders, and every blendshape quietly deforms
the wrong place. Position cannot answer this (the body was reshaped on purpose); everything addressed by index must
be identical:

  topology      each polygon's tuple of vertex indices
  loop UVs      full precision, every layer
  weights       which vertex indices carry which bone weights, and how much, keyed by group NAME, all groups
  key names     the shape-key list and its ORDER (added keys are fine; removed or reordered keys are damage)

A positive control is included: if positions come back identical too, the comparison is looking at the same
geometry twice and proves nothing.

usage: blender -b --python check_vertex_ids.py -- PRISTINE.blend|.fbx CURRENT.blend|.fbx [out.json]
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gates_common import args_after_dashes, pop_option, fail, write_json, weights_by_name
import bpy
import numpy as np

a = args_after_dashes()
pop_option(a, '--config')      # accepted for a uniform command line; not needed here
if len(a) < 2:
    fail('usage: --python check_vertex_ids.py -- PRISTINE CURRENT [out.json]')
ORIG, CUR = a[0], a[1]
OUT = a[2] if len(a) > 2 else None


def snapshot(path):
    if not _os.path.exists(path):
        fail(f'file not found: {path}')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.lower().endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.wm.open_mainfile(filepath=path)
    snap = {}
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        me = o.data
        nv, nl = len(me.vertices), len(me.loops)
        co = np.empty(nv * 3)
        me.vertices.foreach_get('co', co)
        topo = np.array([i for p in me.polygons for i in p.vertices], dtype=np.int64)
        ploop = np.array([p.loop_total for p in me.polygons], dtype=np.int64)
        uvs = {}
        for u in me.uv_layers:
            arr = np.empty(nl * 2)
            try:
                u.uv.foreach_get('vector', arr)
            except AttributeError:
                u.data.foreach_get('uv', arr)
            uvs[u.name] = arr
        snap[o.name] = {
            'nv': nv, 'nl': nl, 'npoly': len(me.polygons),
            'co': co, 'topo': topo, 'ploop': ploop, 'uvs': uvs,
            'w': weights_by_name(o),
            'keys': [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [],
            'groups': [g.name for g in o.vertex_groups],
        }
    return snap


A = snapshot(ORIG)
B = snapshot(CUR)
if not A or not B:
    fail('one of the files has no meshes')

rep = {'original': ORIG, 'current': CUR, 'meshes': {}, 'verdict': None}
shared = [n for n in A if n in B]
if not shared:
    fail(f'no mesh names in common. original: {sorted(A)[:12]} current: {sorted(B)[:12]}')
print('\nORIGINAL %s\n CURRENT %s' % (ORIG, CUR))
print('meshes in both files: %d   (original %d, current %d)\n' % (len(shared), len(A), len(B)))

broken, moved_any = [], False
for name in sorted(shared):
    x, y = A[name], B[name]
    r = {}
    r['count_same'] = (x['nv'], x['nl'], x['npoly']) == (y['nv'], y['nl'], y['npoly'])
    if not r['count_same']:
        r['counts'] = {'orig': [x['nv'], x['nl'], x['npoly']], 'cur': [y['nv'], y['nl'], y['npoly']]}
        rep['meshes'][name] = r
        broken.append(name)
        print('%-30s VERTEX COUNT CHANGED  %s -> %s' % (name, r['counts']['orig'], r['counts']['cur']))
        continue
    r['topology_same'] = bool(np.array_equal(x['topo'], y['topo']) and np.array_equal(x['ploop'], y['ploop']))
    r['uv_layers_same'] = sorted(x['uvs']) == sorted(y['uvs'])
    uvmax = 0.0
    for k in x['uvs']:
        if k in y['uvs'] and x['uvs'][k].shape == y['uvs'][k].shape and x['uvs'][k].size:
            uvmax = max(uvmax, float(np.abs(x['uvs'][k] - y['uvs'][k]).max()))
    r['uv_max_delta'] = uvmax
    r['groups_same'] = x['groups'] == y['groups']      # roster order is NOT an identity (imports rebuild it); reported only
    xw, yw = x['w'], y['w']
    allk = set(xw) | set(yw)
    r['weight_entries_missing'] = int(sum(1 for k in allk if k not in xw or k not in yw))
    r['weight_max_delta'] = max((abs(xw[k] - yw[k]) for k in allk if k in xw and k in yw), default=0.0)
    r['weighted_verts'] = len({k[0] for k in xw})
    ka, kb = x['keys'], y['keys']
    sa, sb = set(ka), set(kb)
    r['keys_same'] = ka == kb
    r['keys_removed'] = sorted(sa - sb)
    r['keys_added'] = len(sb - sa)
    r['keys_order_preserved'] = [k for k in kb if k in sa] == ka
    r['n_keys'] = len(ka)
    r['pos_max_delta'] = float(np.abs(x['co'] - y['co']).max()) if x['co'].size else 0.0
    if r['pos_max_delta'] > 1e-6:
        moved_any = True
    ok = (r['topology_same'] and r['uv_layers_same'] and r['uv_max_delta'] == 0.0
          and not r['keys_removed'] and r['keys_order_preserved']
          and r['weight_entries_missing'] == 0 and r['weight_max_delta'] == 0.0)
    r['ids_preserved'] = ok
    if not ok:
        broken.append(name)
    rep['meshes'][name] = r
    print('%-30s %s  topo=%-5s uvD=%-9.3g wD=%-9.3g wmiss=%-5d keys=%-10s -%d roster=%-5s posD=%.4f m'
          % (name, 'OK  ' if ok else 'FAIL', r['topology_same'], r['uv_max_delta'], r['weight_max_delta'],
             r['weight_entries_missing'],
             ('%d' % r['n_keys']) + (('+%d' % r['keys_added']) if r['keys_added'] else ''),
             len(r['keys_removed']), r['groups_same'], r['pos_max_delta']))

rep['only_in_original'] = sorted(set(A) - set(B))
rep['only_in_current'] = sorted(set(B) - set(A))
print()
if not moved_any:
    print('CONTROL FAILED: no vertex moved anywhere. The two files are the same geometry; this proves nothing.')
    rep['verdict'] = 'inconclusive'
elif broken:
    print('VERTEX IDS CHANGED on: %s' % ', '.join(broken))
    rep['verdict'] = 'changed'
else:
    print('VERTEX IDS PRESERVED on all %d shared meshes. Only coordinates differ.' % len(shared))
    rep['verdict'] = 'preserved'
rep['PASS'] = rep['verdict'] == 'preserved'
if rep['only_in_original']:
    print('  only in original: %s' % ', '.join(rep['only_in_original'][:12]))
if rep['only_in_current']:
    print('  only in current : %s' % ', '.join(rep['only_in_current'][:12]))
if OUT:
    rep['meshes'] = {k: {kk: vv for kk, vv in v.items() if not isinstance(vv, (np.ndarray, dict))}
                     for k, v in rep['meshes'].items()}
    write_json(OUT, rep)
    print('wrote', OUT)
print('VERTEXIDS', 'PASS' if rep['PASS'] else 'FAIL', rep['verdict'])
