"""Export round-trip gate: export the file to FBX, re-import it, and check that meshes, bones and blend shapes survive.

What it compares after the round trip, by object/bone/key NAME:
  - mesh count, vertex count per mesh
  - blend-shape count per mesh and each key's per-vertex delta magnitude (the key still does the same thing)
  - bone count and every bone's rest HEAD position in world space (tails are informational: an importer without leaf
    bones guesses them)
Before exporting it also records Blender-side readiness facts (transforms at identity, pose at rest, guard property,
one Armature modifier per mesh, unweighted vertices, humanoid bones present, triangle count).

usage: blender -b avatar_or_outfit.blend --python export_check.py -- out_dir report.json
         [--tol-mm 1.0] [--config gates_config.json] [--fbx-name roundtrip.fbx]
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gates_common import args_after_dashes, pop_option, load_config, fail, write_json
import bpy, os
import numpy as np

a = args_after_dashes()
cfg = load_config(a)
tol = float(pop_option(a, '--tol-mm', 1.0)) / 1000.0
fbx_name = pop_option(a, '--fbx-name', 'roundtrip.fbx')
if len(a) != 2:
    fail('usage: file.blend --python export_check.py -- out_dir report.json [--tol-mm 1.0] [--config ...]')
outdir, report_path = a
os.makedirs(outdir, exist_ok=True)
R = {'blender': bpy.app.version_string, 'file': bpy.data.filepath, 'checks': {}, 'notes': []}
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.users_collection]
if not arms:
    fail('no armature in the file')
arm = next((o for o in arms if o.name == cfg['armature']), arms[0])
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.users_collection]
if not meshes:
    fail('no meshes in the file')
C = R['checks']
C['armature_used'] = arm.name
C['armature_transform_identity'] = bool(np.abs(np.array(arm.matrix_world) - np.eye(4)).max() < 1e-6)
C['mesh_transforms_identity'] = all(np.abs(np.array(o.matrix_world) - np.eye(4)).max() < 1e-6 for o in meshes)
C['scene_unit_scale'] = bpy.context.scene.unit_settings.scale_length
C['pose_position'] = arm.data.pose_position
C['pose_is_rest'] = all(np.abs(np.array(pb.matrix_basis) - np.eye(4)).max() < 1e-6 for pb in arm.pose.bones)
C['guard_property_set'] = bool(arm.get(cfg['guard_property']))
C['meshes_with_one_armature_modifier'] = all(len([m for m in o.modifiers if m.type == 'ARMATURE']) == 1 for o in meshes)
# The exporter applies non-armature modifiers and then CANNOT export that mesh's shape keys. A leftover Subdivision or
# Mirror modifier ships a different mesh with no blend shapes. Listed here; the round trip below catches the result.
C['meshes_with_non_armature_modifiers'] = {o.name: [m.type for m in o.modifiers if m.type != 'ARMATURE']
                                           for o in meshes if any(m.type != 'ARMATURE' for m in o.modifiers)}
C['unweighted_vertices'] = {o.name: int(sum(1 for v in o.data.vertices if not any(g.weight > 0 for g in v.groups))) for o in meshes}
C['unweighted_vertices'] = {k: v for k, v in C['unweighted_vertices'].items() if v}
C['materials'] = len(bpy.data.materials)
C['bones'] = len(arm.data.bones)
C['deform_bones'] = sum(1 for b in arm.data.bones if b.use_deform)
tris = 0
for o in meshes:
    o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
C['total_triangles_all_visible'] = tris
C['total_shape_keys'] = sum(len(o.data.shape_keys.key_blocks) for o in meshes if o.data.shape_keys)
hb = cfg.get('humanoid_bones', {})
C['humanoid_bones_missing'] = {role: name for role, name in hb.items() if name not in arm.data.bones}
if 'upper_leg_L' in hb and 'upper_leg_R' in hb and hb['upper_leg_L'] in arm.data.bones and hb['upper_leg_R'] in arm.data.bones:
    C['leg_rest_asymmetry_m'] = float(abs(arm.data.bones[hb['upper_leg_L']].head_local.x + arm.data.bones[hb['upper_leg_R']].head_local.x))


def world_bones(a_):
    mw = a_.matrix_world
    return {b.name: (np.array(mw @ b.head_local), np.array(mw @ b.tail_local)) for b in a_.data.bones}


def key_deltas(o):
    """Per key: magnitude of each vertex's delta from Basis, in world space (survives importer axis/scale conversion)."""
    me = o.data
    if not me.shape_keys:
        return {}
    n = len(me.vertices)
    mw = np.array(o.matrix_world)[:3, :3]
    kb = me.shape_keys.key_blocks
    b = np.empty(n * 3); kb[0].data.foreach_get('co', b); b = b.reshape(-1, 3)
    out = {}
    for k in kb[1:]:
        c = np.empty(n * 3); k.data.foreach_get('co', c); c = c.reshape(-1, 3)
        out[k.name] = np.linalg.norm((c - b) @ mw.T, axis=1)
    return out


ref = {o.name: {'nv': len(o.data.vertices), 'keys': key_deltas(o)} for o in meshes}
ref_bones = {a_.name: world_bones(a_) for a_ in arms}

# Hidden objects cannot be selected, and a selection-based export then drops them silently (an avatar once shipped
# with 0 bones because the armature was hidden for convenience). Unhide for the export.
for _o in bpy.context.view_layer.objects:
    if _o.hide_get():
        _o.hide_set(False)
fbx = os.path.join(outdir, fbx_name)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, add_leaf_bones=False, bake_anim=False,
                         object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=True, mesh_smooth_type='FACE',
                         apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', embed_textures=False, path_mode='COPY')
R['fbx'] = fbx
R['fbx_bytes'] = os.path.getsize(fbx)
in_view = {o.name for o in bpy.context.view_layer.objects}
R['excluded_from_view_layer_not_exported'] = sorted(o.name for o in meshes if o.name not in in_view)
ref = {k: v for k, v in ref.items() if k in in_view}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
imp = [o for o in bpy.data.objects if o.type == 'MESH']
iarm = [o for o in bpy.data.objects if o.type == 'ARMATURE']
rt = R['fbx_roundtrip'] = {'meshes_exported': len(ref), 'meshes_imported': len(imp), 'armatures_imported': len(iarm),
                          'bones_exported': sum(len(v) for v in ref_bones.values()),
                          'bones_imported': sum(len(a_.data.bones) for a_ in iarm)}


def variants(n):
    return {n, n.replace(' ', '_'), n.replace('.', '_'), n.replace(' ', '_').replace('.', '_')}


vmis, kcount_mis, kdelta_mis, unmatched = [], [], {}, []
for o in imp:
    cand = [k for k in ref if o.name in variants(k)]
    if not cand:
        unmatched.append(o.name); continue
    r = ref[cand[0]]
    if len(o.data.vertices) != r['nv']:
        vmis.append((o.name, len(o.data.vertices), r['nv'])); continue
    kd = key_deltas(o)
    if len(kd) != len(r['keys']):
        kcount_mis.append((o.name, len(kd), len(r['keys'])))
    worst = 0.0
    for kname, before in r['keys'].items():
        after = kd.get(kname) if kname in kd else kd.get(kname.replace(' ', '_'))
        if after is None:
            kdelta_mis.setdefault(o.name, {})[kname] = 'missing after import'; continue
        worst = max(worst, float(np.abs(after - before).max()))
    if worst > tol:
        kdelta_mis.setdefault(o.name, {})['max_key_delta_change_m'] = worst
rt['unmatched_imported_meshes'] = unmatched
rt['vertex_count_mismatches'] = vmis
rt['blendshape_count_mismatches'] = kcount_mis
rt['blendshape_delta_mismatches'] = kdelta_mis

# bones: compare every exported bone's world head with the re-imported one, by name
bone_dev = {}; tail_dev = 0.0; bones_missing = []
imp_bones = {}
for a_ in iarm:
    imp_bones.update(world_bones(a_))
for aname, bones in ref_bones.items():
    for bname, (h, t) in bones.items():
        if bname not in imp_bones:
            bones_missing.append(bname); continue
        h2, t2 = imp_bones[bname]
        d = float(np.linalg.norm(h - h2))
        if d > tol:
            bone_dev[bname] = round(d * 1000, 3)
        tail_dev = max(tail_dev, float(np.linalg.norm(t - t2)))
rt['bones_missing_after_import'] = bones_missing
rt['bone_head_deviation_over_tol_mm'] = bone_dev
rt['bone_tail_max_deviation_mm_informational'] = round(tail_dev * 1000, 3)
rt['tolerance_mm'] = tol * 1000
rt['PASS'] = (len(imp) == len(ref) and not vmis and not kcount_mis and not kdelta_mis and not unmatched
              and not bones_missing and not bone_dev and rt['bones_imported'] == rt['bones_exported'])
R['notes'] += ['FBX validated in Blender only. Engine-side steps (humanoid mapping, performance rank, physics bones, '
               'expression setup, texture import settings, importer normal settings) are not checked here.']
R['PASS'] = rt['PASS']
write_json(report_path, R)
print('EXPORTCHECK', 'PASS' if R['PASS'] else 'FAIL', {k: v for k, v in rt.items() if v not in (True, [], {}, 0)})
