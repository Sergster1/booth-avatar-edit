# Troubleshooting (agent-only)

Read this when the user reports a visual problem or a gate fails. Match their words to a symptom below, confirm the
cause with a render or a measurement **before** changing anything, explain it back in plain words, then fix it. Log
in `HANDOFF.md` which symptom each fix addressed. Causes are listed as diagnoses to rule out, most likely first.

Two rules that apply to every entry:
- Never call something an artefact without looking: re-render with the obstruction removed (the other leg, the hair,
  the garment) and from the user's exact view (pose, camera, editor or in game).
- Compare with a working original (the pristine base, the same outfit on the unedited base, another avatar the user
  owns) before reasoning about causes.

---

## Body

### "Lumpy", "bumpy", "dented", "pushed in one spot", "all of these look bad"
- **The edit is too local.** A region was moved with a small radius or per-vertex nudges instead of a whole-region move
  with a smooth falloff. Confirm: render a displacement map (edited minus base, colour by magnitude); lumps show as
  islands. Fix with a wider, smooth falloff; re-render the whole set.
- **Positions were smoothed, not the displacement.** Smoothing vertex positions ripples on an irregular stylised mesh.
  Confirm: ripples follow the mesh's edge flow rather than the shape. Smooth the displacement field from the base
  surface instead.
- **Several keys or edits stacked without blending** (a lift plus a fill plus a pad). Confirm by toggling each one
  alone in a render.

### "A band", "a ridge", "a ledge", "a line around the thigh/waist", "a step"
- **The fade window is not smooth enough** (hard window edge, or a cubic ramp where a C² one is needed). Confirm: the
  band sits exactly at the edge of your region mask; render with the mask boundary overlaid. Replace the window.
- **A sub-region was excluded from smoothing to protect it.** The boundary becomes a ridge. Weight it down smoothly
  instead of excluding it.
- **Horizontal banding** responds to vertical-only smoothing of the displacement or a per-slice radial correction
  (measure each thin horizontal slice's mean radial offset, smooth that profile along the height, re-apply the
  difference). Isotropic smoothing blurs the shape without removing the band.
- **It is the texture, not the geometry.** Painted creases, stocking tops or seams read as ledges. Confirm with a
  clay render; if it vanishes, it is painted.

### "A seam", "a crease where there shouldn't be one", "a mask edge", "a plateau"
- **Two regions edited with masks that meet without a feather.** Confirm by rendering each mask alone. Feather both so
  they overlap smoothly; never let two masks share a hard edge.
- **Mirror asymmetry**: left and right edited with different masks. Confirm by comparing left and right displacement.

### "Flips", "black triangles", "spikes", "a dent at the cleft / under the breast / in the crotch fold"
- **Growth toward a cleft or a touching limb.** Scaling a region about its own centre pushes faces into the neighbour.
  Confirm with a flipped-triangle count against the base (the base has its own; count only new ones) and a close-up.
  Grow only outward, backward and up; never toward the cleft.
- **A new underside fold key or a sag key rebuilt the fold too sharply.** Confirm: flips appear only with that key on.
  Rebuild the fold from the structure beneath it (pull the chest wall in to make room), then the surface.
- **Triangle stretch**: area ratio p99 > ~2 shows as stretched texture and shading. Measure it; redistribute the
  displacement tangentially.

### "Right from the front, wrong from the side" (or the reverse), "torpedoes, not pumpkins", "too much mass on top"
- **The edit was judged from one view.** Projection and width are separate axes; the mass can sit up/down and in/out
  independently. Confirm with the full view set (front, side, rear, both three-quarters, high rear three-quarter).
  Build a ladder on the axis the user named (where the mass sits), not on size.
- **Shape and volume are confounded.** Keep shape (a fit key) and volume (one uniform scale) as separate controls so
  "same shape, less volume" is one slider later.

### "The geometry doesn't match the texture", "the painted crease is in the wrong place", "looks like it droops"
- **Volume added below a painted fold** (a gluteal fold, an underbust shadow) reads as droop. Confirm by rendering
  with the texture and with clay side by side. Use UV-space landmarks of the painted anatomy to place the edit;
  world-space patches drift as the body changes.

### "It looked fine in the sheet but the shape keys broke", "the face keys moved", "the toggle key does the wrong thing"
- **Keys were not carried through the edit**, or the carry scaled their deltas. Confirm with the preservation gate's
  per-key energy ratio and a render of each affected key at 1.0 on the new body.
- **A body key the outfits rely on was changed in effect.** Every outfit key with the same name must get the identical
  change or it clips when the key is on (see converter: "fits with keys off").

### "Too subtle", "I can't see the difference", "go further"
- **The round was timid.** The user's taste runs bold; make the next ladder clearly bigger and say so. Confirm the
  change is actually in the file (byte-identical output means the change didn't run).

### "The hands clip the hips", "the arms go through the chest at rest"
- **Wider proportions versus the base's rest pose.** Expected with wide hips or a large chest; the user decides
  (tracked hands make it minor). Confirm in an arms-down pose, not only in the rest pose.

### "The head is in the neck", "the calves look weird", "she sinks into the floor / floats"
- **A height or floor change moved the humanoid rest.** Changing the rest, the armature root or a bone length changes
  how the engine's IK poses the legs. Confirm in game, not in the editor. Keep the humanoid rest unchanged; move the
  body through the pose the converter carries, and handle footwear height in the engine.

---

## Converter

### "The hands / wrists / feet are torn off", "the left wrist is wrong on every outfit", "fingers stretched"
- **The displacement field's support ends on an extremity**, or its sampling box is not centred, so values there are
  unclamped. Confirm: measure movement of garment vertices where the body did not change (hands, feet, head); it must
  be zero to noise. Check left against right; the failing side is the field edge.
- **The far-from-body rule is missing**: vertices with no measurable original clearance were given a target. Confirm
  by listing moved vertices against distance to the old body.

### "The skeleton is off", "the outfit sits a few cm off the avatar after export", "it looked right in Blender"
- **A translation applied to a connected bone.** The base's bone ignores it (connected bones follow their parent's
  tail) but the outfit's FBX rig is unconnected, so there it applies. Confirm with the rest-match gate on the FBX
  re-import; the offset appears on that bone and everything under it. Remove the translation at the source (the pose),
  not in the converter.
- **The pose was copied in bone-local space** onto a rig with different bone orientation or roll. Confirm: deviation
  grows down the chain. Drive the outfit bones in armature space to the avatar's posed matrices.
- **Pre-existing offsets**: the shipped outfit's twist/helper bones were never on the base rest. Confirm with the
  original outfit against the original base; those are not your regression.

### "Jewellery looks squashed / scaled", "the bell is a different size", "the buckle is stretched"
- **The rigid fit was computed from the skinned (already scaled) shape** instead of the part's original shape, so it
  inherited the bone's non-uniform scale. Confirm: fit an affine map from original to converted island; a scale far
  from 1 confirms it.
- **The part is not being treated as rigid at all** (threshold decided by size, and it is bigger than the cutoff).
  Confirm by checking which islands were classed rigid in the report.

### "The garter / band / strap stayed stiff and cuts into the skin", "the stocking top didn't widen"
- **A deformable part was classed rigid because it is small.** Rigid must be decided by whether one rigid motion
  actually reproduces the part's target (small residual), not by size. Confirm by measuring the residual.

### "Z-fighting", "skin speckles through the stockings", "the swimsuit shimmers"
- **The clearance threshold is too loose** (a garment allowed to sit 0-1 mm under the skin). Confirm with the fit
  gate at 0.05 mm against the baseline; the original shows none. Target each vertex's original clearance with a
  tight tolerance.
- **Custom normals or shading** were changed. Confirm with the non-destructive gate.

### "The inner-thigh band snapped to the other leg", "the strap sits inside the other thigh", "weighted to the wrong leg"
- **Nearest-surface measured across touching limbs.** Where the thighs meet, the nearest skin is the other leg.
  Confirm by rendering with the other leg swung out; the band is visibly inside. Restrict the clearance (and any
  weight source) to the limb the garment belongs to.

### "It balloons / spikes where the body barely moved", "the glove exploded", "inside on one body, outside on another"
- **The sign of the distance flipped at grazing range** (a different nearest triangle). Confirm: the spike is at a
  place where the garment grazes the body. Cap every correction by how far the body actually moved there.
- **The field overshoots at its boundary** (an attenuation that should be 0..1 exceeding 1). Confirm by sampling the
  field; clamp it.

### "Sleeves / straps / the collar moved where the body didn't change", "the top shifted although the chest edit is below it"
- **The field bleeds** into regions near the edited one (its support is wider than the edit), or near the body the
  field replaces the bone result instead of adding the residual. Confirm: measure garment movement against body
  movement in that region; garment > body is bleed. Mask the field to the edited region; let bones carry the rest.

### "The outfit's own shape key does too much / too little now", "the squeeze key over-shrinks"
- **Key deltas were scaled by the bone matrix** or by the field. Confirm: compare each outfit key's delta magnitude
  before and after (the export gate reports it too). Apply the same offsets to every key so the relative structure
  survives; never scale deltas.

### "Fits with everything off, then clips or floats once a toggle drives a key", "the garter looks broken"
- **The outfit expects a body key to be on** (a squeeze or shrink key under a band). Confirm with the fit gate's
  `expects_body_keys` diagnosis or by re-running with `--keys`. Not a converter defect: report it; the engine's
  blendshape sync drives the key. Never bake the key into the garment or the body.
- **A body key's effect was changed** (boosted, reshaped) without the same change on the outfit's same-name key.
  Confirm by evaluating body and outfit with the key at 1.0.

### "The skirt / tail / chain swings from the wrong place in game", "physics looks detached"
- **Outfit-only bones were not carried** with the cloth the field moved. Confirm: compare each outfit-only bone's head
  with the centroid of the vertices it weights, before and after; a gap of centimetres is the bug. Carry them by the
  same displacement before applying the rest. In-game only: the editor at rest shows nothing.
- **Physics components in the engine still hold the old setup.** Pivots and colliders must be redone after bones
  moved.

### "The tops float off the chest in Unity", "nip slips", "the hair bones reset", "it fit in Blender"
- **Unpacked prefab bones hold stale transforms** that an FBX re-import does not update. Confirm: compare prefab bone
  transforms with the FBX rest; reset them after every re-import.
- **The in-engine renderer isn't refreshed** (edit-mode renders can show a stale skinned mesh). Confirm in play mode
  or in game.

### "Converted twice", "it moved again after I re-imported it"
- **The already-converted guard lives in a custom property, which FBX drops.** Confirm: the re-imported file's shared
  bones already match the custom rest while the guard is absent. The converter needs a second check (compare the
  outfit's rest with the custom rest) that survives export.

### "The gate says better but it looks worse", "the numbers improved"
- **The metric cannot see the defect** (flip counts while garments sink; a 1 mm threshold while stockings z-fight).
  Confirm by rendering the pose the number claims is better. Renders win; fix the metric.

### "Toggles stopped working in game", "the boots turn on the socks", "glasses toggle dead"
- **An upload-time optimiser or mesh merger rewrote the toggles** that passed an editor test build. Confirm by
  disabling it and re-testing. Toggles must target the renderer objects, and a default-on toggle's target must start
  in the opposite state in the scene.

### "Shading artefacts on the chest when the key is on", "faceted highlights"
- **Importer normal settings** (blend-shape normals recalculated vs. legacy). Confirm by switching the import option
  on one mesh. Engine-side, not a converter defect.

### "Nothing changed after your fix", "same output"
- **The fix isn't running** (wrong file, cached data, a stale conversion-data file, the step feeding the previous
  run's output). Confirm by hashing input and output before and after; instrument the code path. Don't argue;
  measure.
