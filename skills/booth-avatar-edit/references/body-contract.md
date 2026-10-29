# Body contract (phase 0 and B)

What a reshaped body must satisfy. The method is yours to choose: wrapping to a reference mesh, scripted
displacement, bone scales in a single pose, shape keys, or a mix. Record the choice in `DECISIONS.md`.

## Must hold

- **Same mesh identity:** vertex count and order, UVs, materials, vertex groups and the base's shape keys (names,
  order, relations), all identical to the pristine base. Only positions change. Added keys are fine; a removed or
  reordered key is damage. Compare weights by vertex-group *name*, not group index (imports rebuild the roster).
  Check index-addressed data against the *pristine purchased file*, not your last checkpoint (`gates/check_vertex_ids.py`).
- **Anything else is a destructive edit** (materials, UVs, deleted geometry, split meshes): ask first, label it as
  such in `DECISIONS.md`, and assert that nothing else changed.
- **Shape keys keep working.** Every base key (face, body toggles, "squeeze" keys outfits rely on) still does the
  same thing on the new body. Prove it with a key-by-key report (`gates/test_preservation.py`).
- **Smooth edits:** every edited region fades out smoothly (continuous in slope and curvature). Displace smoothly;
  don't smooth positions. Hard window edges show up as bands and ledges.
- **Clean mesh:** no new flipped or degenerate triangles beyond the base's own. Watch triangle stretch (e.g. area
  ratio p99 < ~2).
- **Agrees with the texture:** geometry must match the anatomy painted on the body texture (creases, folds,
  highlights). Use UV-space landmarks for that.
- **Skin weights unchanged** unless a gate proves a change helps in motion.
- **Rig:** if proportions change through bones, the result is applied as the new rest exactly once, and connected
  bones never get translations. The converter has to reproduce whatever you do here, so keep it simple and recorded.
- **Carriable:** every mechanism you use must be one the converter can reproduce on an outfit (bones carried exactly,
  keys carried by same-name outfit keys or a field). Before a body is locked, convert one or two real outfits onto it
  provisionally and look.

## Techniques to consider

One line each: what it is good for, and what to watch for. Mix them; record what you used.

- **Bone scale, rotation and (unconnected-only) translation in one pose, applied as rest once.** Good for
  proportions: hips, chest, limbs, height; the converter carries it most easily. Watch: connected bones ignore
  translation; non-uniform scale shears children (handle scale inheritance while posed, restore it after); every
  shape key must survive the apply; physics-bone pivots move with the bones, so the engine setup is redone.
- **Whole-region moves with a smooth falloff** (proportional editing done as maths). Good for anything bones can't
  shape. Watch: if every variant looks lumpy the falloff is too small; the fade must be C²; smooth the displacement,
  never the positions; grow only in the directions you intend (toward a cleft or a touching limb produces flips).
- **New shape keys, or base keys driven past 1.** Good for local shape, softness, folds; keep shape and volume as
  separate controls when the user hints at a later resize. Watch: a body key needs a same-name outfit key or a
  converter field to carry it; keys that rebuild an underside fold flip triangles easily; check with the base's own
  keys mixed in.
- **Wrap toward a reference mesh.** Good for taking a whole region from a measured 3D reference. Watch: align by
  landmark heights (piecewise, not one uniform scale); the parts you are *not* changing must coincide first; bound the
  fit region; repair flips against the base; a stylised reference's clothing compression is not anatomy.
- **Hand sculpt by the user.** Allowed, but exported as a displacement over the same topology and recorded, or it
  can't be regenerated.
- **Avoid:** Shrinkwrap, Surface Deform or remesh on the body (topology or keys die); weight repaint or smoothing by
  default.

## Review views (agree on these with the user in phase A)

Orthographic front, side and rear; both three-quarters; a high rear-three-quarter; close-ups of the regions being
edited; at least one seated and one arms-down pose. Always beside the canon references, at matching scale. Verify
that a generated or supplied reference labelled "back" or "side" actually shows that angle; several did not.

## Done

The independent image-only reviewer finds no blocking issue. Then the **user explicitly approves**. Tag it. Nothing
downstream starts before that.
