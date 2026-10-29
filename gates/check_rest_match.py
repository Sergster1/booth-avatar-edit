"""Rest-match gate: a converted outfit's skeleton must land on the custom avatar's skeleton.

Avatar-merging tools bind the garment to the AVATAR's bones by name and discard the outfit's own copies of shared
bones. A shared bone whose rest sits somewhere else deforms wrongly in game, with no warning in the engine.

For every bone the outfit shares with the avatar: world-space head and bone-axis orientation are compared (they fail
the gate); tails are reported only, because FBX carries no tails and an importer guesses them for leaf bones. If the
ORIGINAL outfit and the ORIGINAL base are given too, only the deviation the conversion INTRODUCED counts: outfit
files routinely ship twist/helper bones that were already off the base rest, and flagging those is a false alarm.
They are listed separately.

Run it on the converted .blend AND on an FBX export of it re-imported: the second is the one that matters.

usage: blender -b --python check_rest_match.py -- converted_outfit.blend|.fbx avatar.blend out.json
         [--original-outfit source.fbx|.blend --original-base pristine.blend]
         [--tol-mm 1.0] [--tol-deg 1.0] [--outfit-armature NAME] [--config gates_config.json]
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gates_common import args_after_dashes, pop_option, load_config, fail, write_json
import bpy, math
import numpy as np

a = args_after_dashes()
cfg = load_config(a)
tol = float(pop_option(a, '--tol-mm', 1.0)) / 1000.0
tol_deg = float(pop_option(a, '--tol-deg', 1.0))
orig_outfit = pop_option(a, '--original-outfit')
orig_base = pop_option(a, '--original-base')
outfit_arm_name = pop_option(a, '--outfit-armature')
if len(a) != 3:
    fail('usage: --python check_rest_match.py -- converted_outfit avatar.blend out.json [options]')
conv_path, avatar_path, out_json = a
if (orig_outfit is None) != (orig_base is None):
    fail('--original-outfit and --original-base must be given together')


def load(path):
    if not _os.path.exists(path):
        fail(f'file not found: {path}')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.lower().endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.wm.open_mainfile(filepath=path)


def pick_armature(preferred):
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if not arms:
        fail(f'no armature in {bpy.data.filepath}')
    if preferred:
        for o in arms:
            if o.name == preferred:
                return o
    if len(arms) == 1:
        return arms[0]
    # several armatures: prefer the one with the most bones (the outfit rig, not a prop)
    return max(arms, key=lambda o: len(o.data.bones))


def bones_world(a_):
    mw = a_.matrix_world
    out = {}
    for b in a_.data.bones:
        m = mw @ b.matrix_local
        out[b.name] = (np.array(mw @ b.head_local), np.array(mw @ b.tail_local), np.array(m.col[0][:3]), np.array(m.col[1][:3]))
    return out


def angle(u, v):
    u = u / (np.linalg.norm(u) + 1e-12); v = v / (np.linalg.norm(v) + 1e-12)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(u, v))))))


def deviation(bo, ba):
    """outfit bone vs avatar bone: (head m, tail m, axis deg)"""
    return (float(np.linalg.norm(bo[0] - ba[0])), float(np.linalg.norm(bo[1] - ba[1])),
            max(angle(bo[2], ba[2]), angle(bo[3], ba[3])))


load(conv_path)
oa = pick_armature(outfit_arm_name)
conv = bones_world(oa)
conv_arm_name = oa.name
load(avatar_path)
av = bones_world(pick_armature(cfg['armature']))
shared = sorted(set(conv) & set(av))
if not shared:
    fail(f'the outfit armature "{conv_arm_name}" shares no bone names with the avatar armature')

pre = {}
if orig_outfit:
    load(orig_outfit)
    oo = bones_world(pick_armature(outfit_arm_name))
    load(orig_base)
    ob = bones_world(pick_armature(cfg['armature']))
    for n in shared:
        if n in oo and n in ob:
            pre[n] = deviation(oo[n], ob[n])

rep = {'converted': conv_path, 'avatar': avatar_path, 'outfit_armature': conv_arm_name, 'shared_bones': len(shared),
       'outfit_only_bones': sorted(set(conv) - set(av)), 'tolerance_mm': tol * 1000, 'tolerance_deg': tol_deg,
       'baseline_given': bool(orig_outfit), 'over_tolerance': {}, 'pre_existing_offsets_ignored': {}, 'worst_mm': 0.0,
       'tail_deviations_informational_mm': {}}
for n in shared:
    h, t, ang = deviation(conv[n], av[n])
    h0, t0, ang0 = pre.get(n, (0.0, 0.0, 0.0))
    intro_h, intro_t, intro_a = max(0.0, h - h0), max(0.0, t - t0), max(0.0, ang - ang0)
    rep['worst_mm'] = max(rep['worst_mm'], intro_h * 1000)
    if h0 > tol or ang0 > tol_deg:
        rep['pre_existing_offsets_ignored'][n] = {'head_mm_before': round(h0 * 1000, 2), 'head_mm_after': round(h * 1000, 2)}
    if intro_t > tol:
        rep['tail_deviations_informational_mm'][n] = round(t * 1000, 2)
    if intro_h > tol or intro_a > tol_deg:
        rep['over_tolerance'][n] = {'head_mm': round(h * 1000, 2), 'axis_deg': round(ang, 2),
                                    'introduced_head_mm': round(intro_h * 1000, 2)}
rep['worst_mm'] = round(rep['worst_mm'], 3)
rep['PASS'] = not rep['over_tolerance']
write_json(out_json, rep)
print('RESTMATCH', 'PASS' if rep['PASS'] else 'FAIL', 'shared', len(shared), 'worst introduced %.2f mm' % rep['worst_mm'],
      'over tol:', list(rep['over_tolerance'])[:12], 'pre-existing ignored:', len(rep['pre_existing_offsets_ignored']))
