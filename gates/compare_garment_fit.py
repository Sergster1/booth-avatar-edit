"""Compare two test_garment_fit.py reports and FAIL on any garment that penetrates the body more than on the BASELINE.

Only the delta matters. The original avatar already has inner layers (linings, the face mesh, inner garments) inside
the body on purpose, so an absolute count is meaningless; a REGRESSION on the same mesh in the same pose is not.

usage: python compare_garment_fit.py baseline.json new.json out.json [accepted_regressions.json]
                                     [--tol-verts 25] [--tol-depth-mm 3.0]

The tolerances are measurement noise in deep folds, not a budget. Anything over them must be on the accepted list
(meshes, poses, budget, reason, evidence) or the gate fails. Both reports must have been made with the same poses
and the same --depth-mm.
"""
import json, sys, os

args = sys.argv[1:]


def opt(name, default):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return float(v)
    return default


ABS_TOL = int(opt('--tol-verts', 25))
DEPTH_TOL = opt('--tol-depth-mm', 3.0)
if len(args) < 3:
    print('usage: compare_garment_fit.py baseline.json new.json out.json [accepted.json] [--tol-verts N] [--tol-depth-mm X]')
    sys.exit(2)
base_p, new_p, out_p = args[0], args[1], args[2]
accepted_p = args[3] if len(args) > 3 else None
for p in (base_p, new_p):
    if not os.path.exists(p):
        print('GATE ERROR: report not found:', p); sys.exit(2)
base, new = json.load(open(base_p)), json.load(open(new_p))
if base.get('depth_threshold_m') != new.get('depth_threshold_m'):
    print('GATE ERROR: the two reports used different depth thresholds (%s vs %s); re-run with the same --depth-mm'
          % (base.get('depth_threshold_m'), new.get('depth_threshold_m'))); sys.exit(2)
missing_poses = [p for p in new['poses'] if p not in base['poses']]
if missing_poses:
    print('GATE ERROR: poses in the new report but not in the baseline:', missing_poses); sys.exit(2)

ACCEPTED = []
if accepted_p:
    try:
        ACCEPTED = json.load(open(accepted_p))['accepted']
    except (OSError, ValueError, KeyError) as ex:
        print('GATE ERROR: could not read the accepted-regression list:', ex); sys.exit(2)
    for e in ACCEPTED:
        for k in ('meshes', 'poses', 'max_delta_verts', 'max_delta_depth_mm', 'reason'):
            if k not in e:
                print('GATE ERROR: accepted entry missing', k, ':', e); sys.exit(2)


def allowance(pose, mesh):
    for e in ACCEPTED:
        if mesh in e['meshes'] and (pose in e['poses'] or '*' in e['poses']):
            return e
    return None


rep = {'baseline': base['label'], 'new': new['label'], 'tol_verts': ABS_TOL, 'tol_depth_mm': DEPTH_TOL,
       'depth_threshold_m': new.get('depth_threshold_m'), 'poses': {}, 'regressions': [], 'accepted_regressions': []}
for pose, nd in new['poses'].items():
    bd = base['poses'][pose]
    rows = {}
    for mesh in sorted(set(nd['per_mesh']) | set(bd['per_mesh'])):
        b = bd['per_mesh'].get(mesh, {'verts_inside': 0, 'max_depth_mm': 0.0})
        n = nd['per_mesh'].get(mesh, {'verts_inside': 0, 'max_depth_mm': 0.0})
        dv = n['verts_inside'] - b['verts_inside']
        dd = n['max_depth_mm'] - b['max_depth_mm']
        if dv or dd:
            rows[mesh] = {'verts_inside': [b['verts_inside'], n['verts_inside']], 'delta_verts': dv,
                          'max_depth_mm': [b['max_depth_mm'], n['max_depth_mm']], 'delta_depth_mm': round(dd, 2)}
        if dv > ABS_TOL or dd > DEPTH_TOL:
            acc = allowance(pose, mesh)
            item = {'pose': pose, 'mesh': mesh, 'delta_verts': dv, 'delta_depth_mm': round(dd, 2)}
            if acc and dv <= acc['max_delta_verts'] and dd <= acc['max_delta_depth_mm']:
                item['accepted_reason'] = acc['reason']
                rep['accepted_regressions'].append(item)
            else:
                if acc:
                    item['over_accepted_budget'] = {'verts': acc['max_delta_verts'], 'depth_mm': acc['max_delta_depth_mm']}
                rep['regressions'].append(item)
    rep['poses'][pose] = {'delta_total': nd['total_verts_inside'] - bd.get('total_verts_inside', 0), 'per_mesh': rows}

rep['PASS'] = not rep['regressions']
os.makedirs(os.path.dirname(os.path.abspath(out_p)), exist_ok=True)
json.dump(rep, open(out_p, 'w'), indent=1)
for pose, d in rep['poses'].items():
    print('  %-22s total delta %+6d' % (pose, d['delta_total']))
for r in rep['accepted_regressions']:
    print('   accepted  %-22s %-34s %+5d verts, %+.1f mm' % (r['pose'], r['mesh'], r['delta_verts'], r['delta_depth_mm']))
if rep['regressions']:
    print('GATE FAIL: garment penetration regressions vs', base['label'])
    for r in rep['regressions']:
        print('   %-22s %-34s %+5d verts, %+.1f mm deeper %s' % (r['pose'], r['mesh'], r['delta_verts'], r['delta_depth_mm'],
                                                                 'OVER ACCEPTED BUDGET' if 'over_accepted_budget' in r else ''))
    sys.exit(1)
print('GATE PASS: no unexplained garment penetration vs %s (%d accepted, documented regressions)'
      % (base['label'], len(rep['accepted_regressions'])))
