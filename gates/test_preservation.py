"""Preservation gate (body phase): a body checkpoint against the PRISTINE purchased file.

The body mesh may differ ONLY in coordinates (Basis and every shape key). Topology, UVs, materials, vertex groups and
weights (by group name), shape-key metadata (names, order, relative keys, ranges, mute, vertex-group masks,
interpolation), drivers, modifiers, the rig's bone rests and relation flags, and every OTHER mesh must be identical.
Added shape keys on the body are allowed; removed or reordered ones are not.

Two functional checks on the keys:
  - a key mixture: the transformed mixture must equal the mixture of transformed keys (the keys still combine)
  - per-key delta energy: does each key still do roughly what it did? (ratio new/old, informational)

usage: blender -b checkpoint.blend --python test_preservation.py -- pristine.blend report.json [--config gates_config.json]
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gates_common import args_after_dashes, load_config, fail, write_json, require_object, weights_by_name
import bpy
import numpy as np

a = args_after_dashes()
cfg = load_config(a)
if len(a) != 2:
    fail('usage: checkpoint.blend --python test_preservation.py -- pristine.blend report.json [--config ...]')
orig_path, out = a
BODY, ARMATURE = cfg['body_mesh'], cfg['armature']


def snapshot():
    ob = require_object(bpy, BODY, 'body mesh')
    me = ob.data
    sk = me.shape_keys
    if sk is None:
        fail(f'body mesh "{BODY}" has no shape keys; is body_mesh set to the right object?')
    n = len(me.vertices)
    d = {'nv': n, 'npoly': len(me.polygons),
         'loops': np.array([l.vertex_index for l in me.loops]),
         'polystart': np.array([p.loop_start for p in me.polygons]),
         'matidx': np.array([p.material_index for p in me.polygons]),
         'mats': [m.name if m else None for m in me.materials],
         'vg_names': [g.name for g in ob.vertex_groups],
         'w': weights_by_name(ob),
         'use_relative': sk.use_relative,
         'drivers': [(fc.data_path, fc.array_index) for fc in (sk.animation_data.drivers if sk.animation_data else [])],
         'mods': [(m.name, m.type, m.object.name if getattr(m, 'object', None) else None) for m in ob.modifiers]}
    uv = {}
    for u in me.uv_layers:
        arr = np.empty(len(me.loops) * 2)
        try:
            u.uv.foreach_get('vector', arr)
        except AttributeError:
            u.data.foreach_get('uv', arr)
        uv[u.name] = arr
    d['uv'] = uv
    d['keys'] = [dict(name=k.name, rel=k.relative_key.name, vmin=k.slider_min, vmax=k.slider_max, val=k.value,
                      mute=k.mute, vg=k.vertex_group, interp=k.interpolation) for k in sk.key_blocks]
    d['coords'] = {}
    for k in sk.key_blocks:
        v = np.empty(n * 3); k.data.foreach_get('co', v); d['coords'][k.name] = v.reshape(-1, 3)
    return d


def arm_snapshot():
    arm = require_object(bpy, ARMATURE, 'armature')
    return {b.name: (tuple(round(x, 7) for x in b.head_local), tuple(round(x, 7) for x in b.tail_local),
                     b.inherit_scale, b.use_inherit_rotation, b.use_local_location, b.use_connect,
                     b.parent.name if b.parent else None) for b in arm.data.bones}


def others():
    out = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != BODY and o.users_collection:
            c = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', c)
            out[o.name] = (len(o.data.vertices), float(np.abs(c).sum()))
    return out


new = snapshot(); arm_new = arm_snapshot(); other_new = others()
if not _os.path.exists(orig_path):
    fail(f'pristine file not found: {orig_path}')
bpy.ops.wm.open_mainfile(filepath=orig_path)
old = snapshot(); arm_old = arm_snapshot(); other_old = others()

R = {'checkpoint_keys': len(new['keys']), 'pristine_keys': len(old['keys'])}
R['topology_identical'] = bool(new['nv'] == old['nv'] and new['npoly'] == old['npoly']
                               and np.array_equal(new['loops'], old['loops']) and np.array_equal(new['polystart'], old['polystart']))
if not R['topology_identical']:
    R['PASS'] = False
    write_json(out, R)
    fail(f'topology differs from the pristine file ({old["nv"]} -> {new["nv"]} verts); nothing else can be compared')
R['uv_identical'] = set(new['uv']) == set(old['uv']) and all(np.array_equal(new['uv'][k], old['uv'][k]) for k in old['uv'])
R['materials_identical'] = new['mats'] == old['mats'] and bool(np.array_equal(new['matidx'], old['matidx']))
R['vertex_group_roster_identical'] = new['vg_names'] == old['vg_names']
R['weights_identical'] = new['w'] == old['w']
if not R['weights_identical']:
    diff = [k for k in set(new['w']) | set(old['w']) if new['w'].get(k) != old['w'].get(k)]
    R['weights_changed_entries'] = len(diff)
    R['weights_changed_verts'] = len({k[0] for k in diff})
# keys: the pristine keys must be present, in order, with identical metadata; extra keys appended are allowed
old_names = [k['name'] for k in old['keys']]
new_names = [k['name'] for k in new['keys']]
new_by_name = {k['name']: k for k in new['keys']}
R['keys_removed'] = [k for k in old_names if k not in new_by_name]
R['keys_added'] = [k for k in new_names if k not in old_names]
R['keys_order_preserved'] = [k for k in new_names if k in old_names] == old_names
R['key_metadata_identical'] = all(new_by_name.get(k['name']) == k for k in old['keys'])
R['use_relative_identical'] = new['use_relative'] == old['use_relative']
R['drivers_identical'] = new['drivers'] == old['drivers']
R['modifiers_identical'] = new['mods'] == old['mods']
R['rig_bones_identical'] = arm_new == arm_old
if not R['rig_bones_identical']:
    R['rig_bones_changed'] = sorted(n for n in set(arm_new) | set(arm_old) if arm_new.get(n) != arm_old.get(n))[:40]
R['other_meshes_identical'] = other_new == other_old
if not R['other_meshes_identical']:
    R['other_meshes_changed'] = sorted(n for n in set(other_new) | set(other_old) if other_new.get(n) != other_old.get(n))

# key mixture: for a per-vertex affine carry (or an untouched key set) mixture(transform) == transform(mixture)
Bn, Bo = new['coords']['Basis'] if 'Basis' in new['coords'] else new['coords'][new_names[0]], \
         old['coords']['Basis'] if 'Basis' in old['coords'] else old['coords'][old_names[0]]
energy_old = {k: float(np.linalg.norm(old['coords'][k] - Bo, axis=1).sum()) for k in old_names[1:]}
mix_cfg = cfg.get('mixture_keys', 'auto')
if mix_cfg == 'auto':
    top = sorted((k for k in old_names[1:] if energy_old[k] > 1e-9), key=lambda k: -energy_old[k])[:8]
    mix = {k: 0.5 for k in top}
else:
    mix = {k: float(v) for k, v in mix_cfg.items() if k in old_names}
    dropped = [k for k in mix_cfg if k not in old_names]
    if dropped:
        R['mixture_keys_not_on_base'] = dropped
if not mix:
    R['PASS'] = False
    write_json(out, R)
    fail('key-mixture check has no keys (config mixture_keys names none of this base\'s keys, or the base has no non-empty keys)')
mo = Bo + sum(v * (old['coords'][k] - Bo) for k, v in mix.items())
mn = Bn + sum(v * (new['coords'][k] - Bn) for k, v in mix.items())
R['mixture_keys'] = mix
R['mixture_max_shift_old_vs_new_m'] = float(np.abs(mn - mo).max())      # informational: how far the mixed body moved
ratios = {}
for k in old_names[1:]:
    if energy_old[k] > 1e-9 and k in new['coords']:
        ratios[k] = float(np.linalg.norm(new['coords'][k] - Bn, axis=1).sum() / energy_old[k])
R['key_delta_energy_ratio_new_over_old'] = dict(min=min(ratios.values()), max=max(ratios.values()),
                                                worst=[(k, round(v, 3)) for k, v in sorted(ratios.items(), key=lambda kv: kv[1])[:3]
                                                       + sorted(ratios.items(), key=lambda kv: kv[1])[-3:]]) if ratios else None
R['keys_with_zero_delta_old_but_nonzero_new'] = [k for k in old_names[1:] if energy_old[k] < 1e-9 and k in new['coords']
                                                 and np.linalg.norm(new['coords'][k] - Bn, axis=1).sum() > 1e-6]
R['keys_dead_now'] = [k for k in old_names[1:] if energy_old[k] > 1e-6 and k in new['coords']
                      and np.linalg.norm(new['coords'][k] - Bn, axis=1).sum() < 1e-9]

R['PASS'] = all([R['topology_identical'], R['uv_identical'], R['materials_identical'], R['vertex_group_roster_identical'],
                 R['weights_identical'], not R['keys_removed'], R['keys_order_preserved'], R['key_metadata_identical'],
                 R['use_relative_identical'], R['drivers_identical'], R['modifiers_identical'], R['rig_bones_identical'],
                 R['other_meshes_identical']]) and not R['keys_with_zero_delta_old_but_nonzero_new'] and not R['keys_dead_now']
write_json(out, R)
print('PRESERVATION', 'PASS' if R['PASS'] else 'FAIL',
      {k: v for k, v in R.items() if k not in ('mixture_keys', 'key_delta_energy_ratio_new_over_old') and v is not True})
