# Body contract (phase 0 and B)

What a reshaped body must satisfy. The method is yours to choose: wrapping to a reference mesh, scripted
displacement, bone scales in a single pose, shape keys, or a mix. Record the choice in `DECISIONS.md`.

## Must hold

- **Same mesh identity:** vertex count and order, UVs, materials, vertex groups and the base's shape keys, all
  identical to the pristine base. Only positions change. Check index-addressed data against the *pristine
  purchased file*, not your last checkpoint.
- **Shape keys keep working.** Every base key (face, body toggles, "squeeze" keys outfits rely on) still does the
  same thing on the new body. Prove it with a key-by-key report.
- **Smooth edits:** every edited region fades out smoothly (continuous in slope and curvature). Displace smoothly;
  don't smooth positions. Hard window edges show up as bands and ledges.
- **Clean mesh:** no new flipped or degenerate triangles beyond the base's own. Watch triangle stretch (e.g. area
  ratio p99 < ~2).
- **Agrees with the texture:** geometry must match the anatomy painted on the body texture (creases, folds,
  highlights). Use UV-space landmarks for that.
- **Skin weights unchanged** unless a gate proves a change helps in motion.
- **Rig:** if proportions change through bones, the result is applied as the new rest exactly once, and connected
  bones never get translations. The converter has to reproduce whatever you do here, so keep it simple and recorded.

## Review views (agree on these with the user in phase A)

Orthographic front, side and rear; both three-quarters; a high rear-three-quarter; close-ups of the regions being
edited; at least one seated and one arms-down pose. Always beside the canon references, at matching scale.

## Done

The independent image-only reviewer finds no blocking issue. Then the **user explicitly approves**. Tag it. Nothing
downstream starts before that.
