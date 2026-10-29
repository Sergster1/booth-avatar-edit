"""Fit-under-motion gate: do the garments still sit on the body once it MOVES?

Flip counts cannot see this (a thigh can sag away from its stocking with zero flipped triangles), so this test poses the
rig and counts garment vertices that end up INSIDE the body, per pose and per mesh. It is always used as a PAIR of
reports: the same outfits on the ORIGINAL base (the baseline) and on the custom body, compared by
compare_garment_fit.py. The absolute count means nothing on its own.

usage: blender -b avatar.blend --python test_garment_fit.py -- LABEL out.json
         [--poses poses.json] [--depth-mm 0.05] [--render dir] [--import-fbx outfit.fbx] [--keys Key=1.0,Key2=0.5]
         [--config gates_config.json]

--depth-mm   how far inside the surface a vertex must be to count. Default 0.05 mm: a tight garment (bra, swimsuit,
             stocking) sitting 0.05-1 mm under the skin z-fights in game, and a 1 mm threshold hid exactly that in the
             project this gate comes from (0 inside at 1 mm; 72 inside and thousands within 0.8 mm at 0.05 mm). Use
             --depth-mm 1.0 only as a second, looser report for loose layers, and never compare reports made with
             different thresholds.
--import-fbx baseline mode: import an UNCONVERTED outfit onto whatever body this file holds (the pristine base).
--keys       evaluate with these body keys set (and the same-named keys on every garment), e.g. for outfits that
             expect a squeeze key to be on.

Errors (exit 2), never a silent pass: a pose role missing from the config or from the main armature, no garments
found, body or armature not found.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gates_common import (args_after_dashes, pop_option, load_config, fail, write_json, require_object, load_json,
                          bone_for_role, match_key_group, HERE)
import bpy, math, os
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = args_after_dashes()
cfg = load_config(a)
poses_path = pop_option(a, '--poses')
depth_mm = float(pop_option(a, '--depth-mm', 0.05))
render_dir = pop_option(a, '--render')
import_fbx = pop_option(a, '--import-fbx')
explicit = pop_option(a, '--keys')
if len(a) != 2:
    fail('usage: avatar.blend --python test_garment_fit.py -- LABEL out.json [options]')
label, out_json = a
DEPTH = depth_mm / 1000.0

if poses_path is None:
    for cand in (os.path.join(HERE, 'poses.json'), os.path.join(HERE, 'poses.example.json')):
        if os.path.exists(cand):
            poses_path = cand; break
POSES = load_json(poses_path, 'poses file')['poses']
if not POSES:
    fail('poses file has no poses')

if import_fbx:
    if not os.path.exists(import_fbx):
        fail(f'--import-fbx file not found: {import_fbx}')
    bpy.ops.import_scene.fbx(filepath=import_fbx)
body = require_object(bpy, cfg['body_mesh'], 'body mesh')
ARMS = [o for o in bpy.data.objects if o.type == 'ARMATURE']
if not ARMS:
    fail('no armature in the file')
arm = next((o for o in ARMS if o.name == cfg['armature']), None)
if arm is None:
    fail(f'armature "{cfg["armature"]}" not found; armatures present: {[o.name for o in ARMS]}')

# every pose role must resolve to a bone on the MAIN armature before anything is measured
needed = sorted({op[0] for p in POSES for op in p['ops']})
missing = [(r, bone_for_role(cfg, r)) for r in needed if bone_for_role(cfg, r) not in arm.data.bones]
if missing:
    fail(f'pose bones missing on armature "{arm.name}": {missing}. Fix humanoid_bones in {cfg["_path"]}; '
         f'a pose that skips bones would silently measure the rest pose.')
outfit_arms_missing = {}
for a_ in ARMS:
    if a_ is arm:
        continue
    m = [bone_for_role(cfg, r) for r in needed if bone_for_role(cfg, r) not in a_.data.bones]
    if m:
        outfit_arms_missing[a_.name] = m     # that outfit will not follow those bones; reported, not fatal

_sk = body.data.shape_keys
_all = [k.name for k in _sk.key_blocks if k.name != 'Basis'] if _sk else []
KEY_GROUPS = [(g['name'], match_key_group(_all, g)) for g in cfg['expected_body_key_groups']]
KEY_GROUPS = [(n, g) for n, g in KEY_GROUPS if g]


def set_body_keys(mapping):
    """Set body keys AND the matching key on every garment (outfits carry same-named keys)."""
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.data.shape_keys:
            continue
        for nm, val in mapping.items():
            kb = o.data.shape_keys.key_blocks.get(nm)
            if kb is not None:
                kb.value = val
    bpy.context.view_layer.update()


baseline_key_values = {k.name: k.value for k in _sk.key_blocks} if _sk else {}
if explicit:
    mapping = {}
    for kv in explicit.split(','):
        k, v = kv.split('=')
        if _sk is None or k not in _sk.key_blocks:
            fail(f'--keys names "{k}", which the body does not have')
        mapping[k] = float(v)
    set_body_keys(mapping)


def reset():
    for a_ in ARMS:
        for pb in a_.pose.bones:
            pb.matrix_basis = Matrix.Identity(4)
    for _ in range(3):      # some rigs have dependency cycles that need a few evaluations to settle
        bpy.context.view_layer.update()
        for a_ in ARMS:
            for pb in a_.pose.bones:
                pb.matrix_basis = pb.matrix_basis.copy()
    bpy.context.view_layer.update()


def rot(role, deg, axis):
    name = bone_for_role(cfg, role)
    for a_ in ARMS:
        pb = a_.pose.bones.get(name)
        if pb is None:
            continue        # already reported in outfit_arms_missing; the main armature was checked above
        piv = a_.matrix_world @ a_.data.bones[name].matrix_local.translation
        pb.matrix = a_.matrix_world.inverted() @ Matrix.Translation(piv) @ Matrix.Rotation(math.radians(deg), 4, axis) \
            @ Matrix.Translation(-piv) @ a_.matrix_world @ pb.matrix
    bpy.context.view_layer.update()


def ev_coords(o):
    """WORLD-space evaluated vertices (an outfit straight from an FBX often still carries an object transform)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg); m = ev.to_mesh()
    n = len(m.vertices)
    c = np.empty(n * 3); m.vertices.foreach_get('co', c); c = c.reshape(-1, 3)
    ev.to_mesh_clear()
    mw = np.array(o.matrix_world)
    return c @ mw[:3, :3].T + mw[:3, 3]


def body_bvh():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); m = ev.to_mesh()
    m.calc_loop_triangles()
    mw = body.matrix_world
    verts = [mw @ v.co for v in m.vertices]
    tris = [t.vertices[:] for t in m.loop_triangles]
    bvh = BVHTree.FromPolygons(verts, tris)
    ev.to_mesh_clear()
    return bvh


def count_inside(bvh, pts):
    inside = 0; deep = 0.0
    for p in pts:
        loc, nor, idx, dist = bvh.find_nearest(Vector(p), 0.05)
        if loc is None:
            continue
        sd = (Vector(p) - loc).dot(nor)
        if sd < -DEPTH:
            inside += 1
            deep = max(deep, -sd)
    return inside, deep


# The face mesh is not a garment: it sits inside the head by design. Leaving it in makes the gate react to the face
# EXPRESSION instead of the outfits.
face = cfg.get('face_mesh') or None
garments = [o for o in bpy.data.objects
            if o.type == 'MESH' and o is not body and o.name != face and not o.hide_render and o.users_collection
            and any(mo.type == 'ARMATURE' and mo.object in ARMS for mo in o.modifiers)]
if not garments:
    fail('no garments found: no mesh other than the body/face has an Armature modifier pointing at an armature in this file')

rep = {'label': label, 'file': bpy.data.filepath, 'imported_fbx': import_fbx, 'depth_threshold_m': DEPTH,
       'poses_file': poses_path, 'garments': [o.name for o in garments], 'armatures': [o.name for o in ARMS],
       'outfit_armatures_missing_pose_bones': outfit_arms_missing, 'explicit_keys': explicit, 'poses': {}}
for pose in POSES:
    pname = pose['name']
    reset()
    for role, dg_, ax in pose['ops']:
        rot(role, dg_, ax)
    bvh = body_bvh()
    per = {}
    tot = 0; worst = 0.0
    for o in garments:
        inside, deep = count_inside(bvh, ev_coords(o))
        if inside:
            per[o.name] = {'verts_inside': inside, 'max_depth_mm': round(deep * 1000, 2)}
            tot += inside; worst = max(worst, deep)
    rep['poses'][pname] = {'total_verts_inside': tot, 'max_depth_mm': round(worst * 1000, 2), 'per_mesh': per}
    print('GARMENTFIT %-22s inside %5d  max depth %6.2f mm  %s' % (pname, tot, worst * 1000, sorted(per)))
    # diagnosis: would turning on one of the base's expected body keys resolve what is left?
    if per and KEY_GROUPS and not explicit:
        diag = {}
        for gname, gkeys in KEY_GROUPS:
            set_body_keys({k: 1.0 for k in gkeys})
            bvh2 = body_bvh()
            for mname in per:
                cnt, _ = count_inside(bvh2, ev_coords(bpy.data.objects[mname]))
                was = per[mname]['verts_inside']
                if cnt < was * 0.5 and mname not in diag:
                    diag[mname] = {'group': gname, 'without': was, 'with_keys_on': cnt}
            set_body_keys(baseline_key_values)
        if diag:
            rep['poses'][pname]['expects_body_keys'] = diag
            print('    body-key diagnosis: these meshes are DESIGNED for a body key that is off:',
                  {k: f"{v['without']}->{v['with_keys_on']} via {v['group']}" for k, v in diag.items()})
    if render_dir:
        os.makedirs(render_dir, exist_ok=True)
        sc = bpy.context.scene
        sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
        sc.render.resolution_x, sc.render.resolution_y = 700, 800
        cam = bpy.data.objects.get('_gf_cam') or bpy.data.objects.new('_gf_cam', bpy.data.cameras.new('_gf_cam'))
        if cam.name not in sc.collection.objects:
            sc.collection.objects.link(cam)
        bb = ev_coords(body)
        lo, hi = bb.min(axis=0), bb.max(axis=0)
        cen = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2))
        sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(hi[2] - lo[2]) * 1.15
        cam.location = cen + Vector((5.2, -2.6, 0))
        cam.rotation_euler = (cen - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{render_dir}/{label}_{pname}.png'
        bpy.ops.render.render(write_still=True)

rep['total_all_poses'] = sum(p['total_verts_inside'] for p in rep['poses'].values())
write_json(out_json, rep)
print('GARMENTFIT TOTAL', label, rep['total_all_poses'], '(compare against the baseline with compare_garment_fit.py)')
