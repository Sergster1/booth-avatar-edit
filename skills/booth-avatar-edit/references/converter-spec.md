# Outfit converter: general spec

A requirements spec for the outfit converter, part of the `booth-avatar-edit` skill. It says **what** the converter
must do and how to prove it, not how to build it. The method and its design choices are yours to work out. Credit
for the original workflow: Sergster.

---

## 1. Purpose

Outfits on BOOTH are made for a specific base avatar. After you reshape that base into a custom body, those outfits
no longer fit. The converter takes an outfit made for the **original base** and produces the same outfit fitted to
the **custom body**, ready for Unity. No hand-editing per outfit.

**Done means:** you can buy a new outfit for the base, run one command, pass the gates below, and wear it in VRChat.

## 2. Terms

| Term | Meaning |
|---|---|
| Original base | The purchased avatar as shipped. Never modified. |
| Custom body | Your approved reshaped body: same topology and rig, new shape and possibly new bone rests. |
| Outfit | Any mesh(es) + armature made for the original base (clothes, hair, accessories). |
| Conversion data | Whatever you precompute from the original base and custom body so the converter can map one to the other. |

## 3. Contract (must hold for every conversion)

1. **Only geometry moves.** Vertex positions (in every shape key) and bone rest positions/orientations may change.
   Everything else is identical to the input: topology, vertex order, UVs, materials, vertex groups and weights,
   custom normals, shape-key names, order and relations, modifiers, bone names and hierarchy.
2. **The outfit's skeleton lands on the custom avatar's skeleton.** Every bone the outfit shares with the avatar
   ends up at the avatar's new rest, within a tolerance you set.
3. **Deterministic and recorded.** Same inputs give the same output. Each run writes a machine-readable report:
   inputs, settings, what moved, warnings, gate results.
4. **Refuse rather than guess.** It stops with a clear message when the input is not an outfit for this base, is
   already converted (and that check must survive an FBX export/re-import), or is in a state it can't handle.
   Warnings are for things it can handle but you should know about.
5. **No per-outfit tuning required.** Optional flags are fine; needing them for ordinary outfits is a bug.
6. **The originals are never written.** Input files are read; output goes to a new file.
7. **Re-runnable after body edits.** One command rebuilds from the current approved body: it regenerates the
   conversion data, re-converts every outfit on the project's outfit list, re-runs the gates and writes one summary.
   A body change must never mean hand-refitting outfits.
8. **Weights stay as the outfit shipped them.** The converter doesn't smooth, repaint or transfer weights by
   default. Engines cap influences per vertex (Unity: 4), and "improved" weights can make garments sink into the body
   in poses even when static metrics improve. Any weight change is opt-in, per mesh, and has to pass the
   fit-under-motion gate.

## 4. Behaviour (what a good result looks like)

Each item is a requirement. Deciding how to meet it is part of the work.

1. **Follows the body.** Where the body changed, the garment changes with it. Where the body didn't change, the
   garment doesn't move.
2. **Keeps its relationship to the skin.** Tight stays tight, loose stays loose, and nothing that was outside the
   skin ends up inside it. Layers stay in order (a coat over a shirt over a bra).
3. **Keeps working when the avatar moves.** It must hold up in poses (sitting, crouching, arms down and crossed,
   torso bend and twist), not just at rest. The weights the outfit shipped with will move it in Unity.
4. **Shape keys still work.** The outfit's own keys do the same thing after conversion. Outfits that expect a body
   shape key to be on (e.g. a "squeeze" key under a sock band) are detected and reported, so the Unity setup can
   drive that key.
5. **Rigid things stay rigid.** Jewellery, buckles, bells and charms move and rotate but don't stretch or squash.
   Pieces that must stretch (bands, straps, stockings) still stretch. Telling the two apart is your call.
6. **Physics bones go with their cloth.** Skirt, hair, tail and chain bones that exist only on the outfit end up
   where their geometry now is.
7. **Parts far from the body behave sensibly.** Decide what should happen to hair, tails, wings, hats and props, and
   test it.
8. **Symmetric in, symmetric out.** A left-right symmetric body change gives a left-right symmetric result. Check
   both sides.
9. **Survives awkward inputs:** object transforms not applied, shared mesh data, meshes parented but not bound to
   the armature, extra or missing bones, slightly different rest poses, non-uniform scale, multiple armatures.

## 5. Gates (acceptance)

**Set every threshold before you look at results**, and write it down. Each gate is a script that writes a report
file and returns pass/fail.

| Gate | What it proves |
|---|---|
| **Non-destructive** | Item-by-item comparison of input and output: everything in §3.1 identical, only coordinates differ. |
| **Fit under motion** | For a set of poses, garment vertices inside the body, per mesh and per pose, compared against the **same outfit on the original base**. The baseline matters: some outfits clip on the original too. Any regression is either fixed or written down with evidence and accepted by the user. |
| **Rest match** | Shared bones match the avatar's new rest within your tolerance. |
| **Export round trip** | Export to FBX, re-import: meshes, bones and blend shapes all survive. |
| **In-engine check** | In Unity, the outfit follows the body in a few poses, with the influence limits Unity actually uses. |
| **Visual review** | Renders from fixed views (front, side, back, three-quarters, close-ups, a seated pose) reviewed by an independent image-only agent, then by the user. Numbers support this; they don't replace it. |

**Starting points** (tune them, but write yours down first): fit-under-motion no more than a few extra verts inside
per mesh per pose versus the baseline, and no new penetration deeper than ~3 mm; rest match ≤ 1 mm; non-destructive
bit-identical; zero test ≤ 1e-5 m. Count tight garments (bras, swimsuits, stockings) at a strict threshold
(~0.05 mm), not 1 mm: a loose threshold hides garments sitting just under the skin.

A metric can improve while the result gets worse. If the numbers say better and the renders say worse, the renders
win and the metric needs fixing.

## 6. Test corpus

At least five real outfits from different creators, covering:
- a tight garment (stockings, bodysuit, swimsuit)
- a loose garment with physics bones (skirt, coat)
- a top that covers the chest, if the chest changed
- something with rigid accessories (jewellery, buckles)
- something that expects body shape keys
- hair or another item that sits away from the body

Keep a synthetic set too (transforms not applied, shared mesh, missing bones, unbound mesh) for §4.9.
Keep the original-base baseline for each. If the user owns fewer outfits, use free BOOTH outfits for the same base
first; anything paid goes on a shortlist with links and prices, and the user decides.

## 7. Questions to answer yourselves (write the answers down)

- How is the body change represented: bone changes, a displacement field, or both? Where does each part go?
- How far from the body does the deformation reach, and how does it fade out?
- How do you measure "inside the body" and "distance to skin", and where does that measure go wrong (e.g. where two
  body parts touch)?
- What is rigid, and how do you decide?
- Which outfit bones get moved, and how?
- How do you detect an already-converted outfit after an FBX round trip?
- What does the in-engine check look like, and who runs it?

## 8. Tests worth having from day one

These are the kinds of failure that are easy to miss:
- a **zero test**: custom body = original base, so the converter must change nothing (to floating-point noise)
- left and right compared on every conversion
- the outfit's skeleton compared to the avatar's **after export and re-import**, not only in Blender
- small rigid parts measured for scale change
- garment fit in a seated pose
- a check that a code change actually changed the output (identical bytes after a fix means the fix isn't running)
