# Gates: the acceptance measurements

A reference implementation of the gates in the skill's `references/converter-spec.md` §5 and
`references/body-contract.md`. They measure outcomes; they contain no converter and no body tool. Your agent may use them as they
are or rewrite them, but the **behaviour** is the spec: baseline on the original base first, thresholds set by flag
before looking, every result written to a report file, a pass only when something was actually measured.

MIT licensed (see `LICENSE` in this folder). Tested with Blender 5.1 headless; the Blender API calls used go back to 3.5.

## Setup

1. The skill copies this folder into your project as `gates/` (keep the scripts together; they find each other by
   location). Without the skill, copy it yourself.
2. `cp gates_config.example.json gates_config.json` and fill in your base's names: body mesh, face mesh, armature,
   humanoid bone map, the key patterns outfits may expect, the guard property your converter sets.
3. `cp poses.example.json poses.json`; add poses for the regions you changed, and check the signs once with `--render`.
4. `cp accepted_regressions.example.json accepted_regressions.json` and **empty the `accepted` list**.

Every gate takes `--config path` (default: `gates_config.json` beside the scripts). Every gate exits 2 with
`GATE ERROR` when it cannot measure (wrong names, missing bones, nothing to compare): that is never a pass.

```
B="C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"      # or `blender` on your PATH
```

## The gates

| Gate | Script | Proves | Cannot see |
|---|---|---|---|
| Vertex IDs | `check_vertex_ids.py` | Nothing addressed by vertex index changed between the pristine file and the current body: topology, UVs, weights (all groups, by name), key names and order. Added keys are fine. Has a positive control. | Whether the shape is good. |
| Preservation | `test_preservation.py` | A body checkpoint keeps everything but coordinates: UVs, materials, weights, key metadata, drivers, modifiers, rig rests and flags, other meshes. Key-mixture and per-key-energy checks show the keys still work. | Visual quality of the carried keys (render them). |
| Non-destructive | `check_nondestructive.py` | A converted outfit differs from its source only in coordinates: topology, UVs, materials, groups, weights, custom normals, key structure identical. | Where the coordinates went (fit gate). |
| Fit under motion | `test_garment_fit.py` + `compare_garment_fit.py` | Garment vertices inside the body, per mesh and per pose, **compared with the same outfits on the original base**. Flags expected-body-key dependencies. | In-game physics, 4-influence truncation (in-engine check). |
| Rest match | `check_rest_match.py` | Shared bones of a converted outfit sit on the custom avatar's rest (head and orientation), counting only the deviation the conversion introduced. | Outfit-only bones (compare them with their cloth yourself). |
| Export round trip | `export_check.py` | After FBX export and re-import: meshes, vertex counts, blend-shape counts and per-key deltas, bone count and bone heads survive. Lists leftover modifiers, unweighted vertices, missing humanoid bones. | Engine import settings, performance rank, physics. |

### Vertex IDs (body phase, every checkpoint)
```
$B -b --python check_vertex_ids.py -- pristine.blend checkpoint.blend reports/vertex_ids.json
```
Compare against the **pristine purchased file**, never your last checkpoint. `CONTROL FAILED` means the two files have
identical positions: you compared the wrong pair.

### Preservation (body phase, phase B gate)
```
$B -b checkpoint.blend --python test_preservation.py -- pristine.blend reports/preservation.json
```
`mixture_keys` in the config: `"auto"` picks the eight strongest keys; an explicit map is better once you know which
keys your outfits rely on. `key_delta_energy_ratio_new_over_old` far from 1 on a key you did not mean to change is
worth a render.

### Non-destructive (every conversion)
```
$B -b converted.blend --python check_nondestructive.py -- source.fbx reports/nondestructive.json [--prefix P] [--allow-weights Mesh]
```
`--allow-weights` is the only loophole and it is per mesh and visible in the report: use it only for a weight change the
converter's own report declares (spec §3.8), and only if the fit gate still passes.

### Fit under motion (the gate that matters)
```
# 1. baseline: the UNCONVERTED outfit on the PRISTINE base, same poses, same threshold
$B -b pristine.blend --python test_garment_fit.py -- baseline reports/fit_baseline.json --import-fbx outfit.fbx --poses poses.json
# 2. the converted outfit on the custom avatar
$B -b custom_with_outfit.blend --python test_garment_fit.py -- custom reports/fit_custom.json --poses poses.json
# 3. the comparison is the gate
python compare_garment_fit.py reports/fit_baseline.json reports/fit_custom.json reports/fit_delta.json accepted_regressions.json
```
- Default depth **0.05 mm**. Tight garments that sit 0.05-1 mm under the skin z-fight in game; a 1 mm threshold once
  reported "0 inside" while 72 vertices were inside and thousands within 0.8 mm. Use `--depth-mm 1.0` only as a second
  report for loose layers; the compare script refuses to compare reports made with different thresholds.
- The absolute count is meaningless (inner layers and linings are inside the body on the original too). Only the
  per-mesh, per-pose **regression** against the baseline counts. Tolerances (`--tol-verts 25 --tol-depth-mm 3.0`) are
  noise in deep folds, not a budget.
- Anything over tolerance must be on `accepted_regressions.json` with meshes, poses, a budget, the reason and the
  evidence, approved by the user, or the gate fails. Loosening the tolerance instead is how a defect ships.
- `expects_body_keys` in the report means that mesh is designed for a base key being on (a sock band's squeeze key).
  That is not a converter defect: the engine setup drives the key. Re-run with `--keys Key=1.0` to judge it fairly.
- A pose role missing from the config or the armature is an error, not a skipped pose: a pose that silently skipped
  its bones would measure the rest pose and pass.
- `--render dir` writes one side view per pose; use it once to confirm your pose signs.

### Rest match (every conversion, and again after FBX re-import)
```
$B -b --python check_rest_match.py -- converted.blend custom_avatar.blend reports/rest_match.json \
     --original-outfit outfit.fbx --original-base pristine.blend [--tol-mm 1.0] [--tol-deg 1.0]
$B -b --python check_rest_match.py -- exported/converted.fbx custom_avatar.blend reports/rest_match_fbx.json ...
```
Why it matters: avatar-merging tools bind the garment to the avatar's bones by name and discard the outfit's copies. A
shared bone resting somewhere else deforms silently in game. With the originals given, bones that were already off on
the shipped outfit (twist and helper bones often are) are listed under `pre_existing_offsets_ignored` instead of
failing. Tails are informational: FBX carries no tails.

### Export round trip (the avatar and every outfit, before anything goes to the engine)
```
$B -b file.blend --python export_check.py -- out_dir reports/export.json [--tol-mm 1.0]
```
Exports with modifiers applied (what you would ship), re-imports, compares by name. A mesh with a leftover
non-armature modifier loses its blend shapes on export; the report lists them under
`meshes_with_non_armature_modifiers` and the vertex count mismatch fails the gate.

## The zero test (run it before trusting the converter on anything)

Set the custom body equal to the original base (same pose data, same body coordinates) and convert one real outfit:

1. Build your conversion data from the pristine base as both "original" and "custom".
2. Convert an outfit with it.
3. `check_nondestructive.py` must PASS, and the converted coordinates must equal the source to floating-point noise
   (≤ 1e-5 m; measure it, don't eyeball it).
4. `check_rest_match.py` against the pristine base must report 0.00 mm.

Anything else means the converter moves things the body did not move. Fix that before the first real conversion.
Then re-run it after every converter change: byte-identical output after a fix means the fix isn't running.

## Reading a report

- A healthy **baseline** fit report lists inner layers and the hair inside the body at rest; the face mesh must be
  absent (if it appears, `face_mesh` in the config is wrong).
- A healthy **delta** report has negative or small positive per-mesh deltas and an empty `regressions` list.
- `examples/` holds trimmed real reports, one passing and one failing per gate, so you know what to expect.

## What these gates do not replace

The image-only review and the user's eyes, the in-engine check with the engine's influence limit, and the in-game
test. A metric can improve while the result gets worse; when the renders and the numbers disagree, the renders win and
the metric gets fixed.
