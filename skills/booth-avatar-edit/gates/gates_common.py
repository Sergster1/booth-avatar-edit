"""Shared helpers for the gates: config loading, argument parsing, loud failure.

Every gate reads one JSON config (`--config path`, else `gates_config.json` beside this file). The config holds the
names that differ between base avatars: the body and face meshes, the armature, the humanoid bone map, the guard
property, the shape-key patterns. Nothing base-specific lives in the scripts themselves.

Usage from a gate:

    from gates_common import load_config, args_after_dashes, fail, bone_for_role
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

REQUIRED = ('body_mesh', 'face_mesh', 'armature')

HUMANOID_ROLES = ('hips', 'spine', 'chest', 'neck', 'head',
                  'upper_arm_L', 'lower_arm_L', 'hand_L', 'upper_arm_R', 'lower_arm_R', 'hand_R',
                  'upper_leg_L', 'lower_leg_L', 'foot_L', 'upper_leg_R', 'lower_leg_R', 'foot_R')


def fail(msg, code=2):
    """Stop the gate with a clear message. A gate that cannot measure must never report a pass."""
    print('GATE ERROR:', msg)
    sys.stdout.flush()
    sys.exit(code)


def args_after_dashes():
    """Arguments after `--` (Blender passes everything before it to Blender itself)."""
    if '--' in sys.argv:
        return sys.argv[sys.argv.index('--') + 1:]
    return sys.argv[1:]


def pop_option(args, name, default=None, flag=False):
    """Remove `--name value` (or a bare `--name` flag) from the argument list and return the value."""
    if name in args:
        i = args.index(name)
        if flag:
            del args[i]
            return True
        if i + 1 >= len(args):
            fail(f'{name} needs a value')
        val = args[i + 1]
        del args[i:i + 2]
        return val
    return default


def load_config(args):
    """Load the gates config. `--config path` wins; else gates_config.json beside the scripts."""
    path = pop_option(args, '--config')
    if path is None:
        path = os.path.join(HERE, 'gates_config.json')
    if not os.path.exists(path):
        fail(f'config not found: {path}. Copy gates_config.example.json to gates_config.json and fill in your base\'s names.')
    try:
        cfg = json.load(open(path, encoding='utf-8'))
    except ValueError as ex:
        fail(f'config is not valid JSON: {path}: {ex}')
    cfg = {k: v for k, v in cfg.items() if not k.startswith('_')}
    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        fail(f'config {path} is missing {missing}')
    cfg.setdefault('guard_property', 'outfit_conversion_complete')
    cfg.setdefault('humanoid_bones', {})
    cfg.setdefault('expected_body_key_groups', [])
    cfg.setdefault('mixture_keys', 'auto')
    cfg['_path'] = path
    return cfg


def bone_for_role(cfg, role):
    """Map a humanoid role (e.g. 'upper_leg_L') to this base's bone name, or fail."""
    m = cfg.get('humanoid_bones', {})
    if role in m:
        return m[role]
    fail(f'humanoid role "{role}" is not in the config\'s humanoid_bones map ({cfg["_path"]})')


def require_object(bpy, name, what):
    ob = bpy.data.objects.get(name)
    if ob is None:
        fail(f'{what} "{name}" not found in {bpy.data.filepath or "the current file"}. Objects present: '
             f'{sorted(o.name for o in bpy.data.objects)[:40]}')
    return ob


def load_json(path, what):
    if not os.path.exists(path):
        fail(f'{what} not found: {path}')
    try:
        return json.load(open(path, encoding='utf-8'))
    except ValueError as ex:
        fail(f'{what} is not valid JSON: {path}: {ex}')


def write_json(path, data):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, default=str)


def weights_by_name(ob):
    """Skin weights keyed by (vertex index, group NAME). Never by group index: an FBX import builds its own group
    roster, so positional arrays misalign and invent weight deltas that do not exist."""
    gname = {g.index: g.name for g in ob.vertex_groups}
    w = {}
    for v in ob.data.vertices:
        for g in v.groups:
            n = gname.get(g.group)
            # An exact-zero entry is no skin influence: exporters and cleanup steps drop them freely, so
            # comparing them would fail on a change nothing can see. Any non-zero weight still counts.
            if n is not None and g.weight != 0.0:
                w[(v.index, n)] = round(g.weight, 6)
    return w


def match_key_group(key_names, group):
    """Select shape keys for an expected-body-key group from the config.
    group = {"name": ..., "match": {"contains": [...], "startswith": [...], "exact": [...]}}"""
    m = group.get('match', {})
    out = []
    for k in key_names:
        kl = k.lower()
        if any(s.lower() in kl for s in m.get('contains', [])):
            out.append(k)
        elif any(kl.startswith(s.lower()) for s in m.get('startswith', [])):
            out.append(k)
        elif k in m.get('exact', []):
            out.append(k)
    return out
