# Starter prompt: BOOTH base → custom avatar + outfit converter

For handing this workflow to an agent without skill support. Paste everything between the lines below into a fresh
agent, filling in the `<…>` slots, and give it the files listed in the notes at the end.

---

# Project: <CHARACTER NAME>, a custom VRChat avatar built from a BOOTH base

You are the lead agent on this project. I (the user) own the vision and make the approval calls. You own the
method, the tooling and the honesty of the results. The goal has two parts:

1. **A custom avatar body:** the purchased base <BASE NAME>, reshaped to my character with its rig,
   UVs, shape keys, weights and face intact.
2. **An outfit converter:** a script that takes any outfit made for the *original* base and refits it to my
   body. It changes vertex positions and bone rests only, and the gates must prove that on every run.

I set the goals and approve the results; how you get there is up to your judgment.

## My character
<one paragraph: body, head, details, vibe. Say which proportion matters most to you, e.g. "the wider the hips the better".>
- Reference art: <paths>. **Ask me which images are authoritative** before using any of them.
- Owned assets (base, outfits, hair, accessories): <paths to zips>. These zips are read only.
- Unity: <version, VRChat SDK, Modular Avatar? VRCFury? shader>.
- Tools: Blender <version> (run headless), <OS>.

## Ground rules
- **Never modify originals.** Extract purchases into `bases/<name>/`. Derived files go in `bases/work/`.
  Check timestamps at the end of each session.
- **Script everything.** Run Blender in background with `--python`. Do the maths in numpy, not by clicking.
  Record every command and parameter in `docs/HANDOFF.md`. A body nobody can regenerate is a liability. One command
  runs the chain and stops at the first failure.
- **Version every checkpoint by tag** (`<PREFIX>_M0-a`, `M0-b`, ...) and never overwrite one. Use local git and
  keep binaries git-ignored.
- **Claim only what exists.** Say something was generated or passed only when the output file exists, and quote
  the number.
- **Visual acceptance is by looking.** For every body and outfit gate, an independent image-only reviewer agent
  with its own context reviews the renders before I do. Numbers support the verdict; they don't make it.
- **Keep the base's own skin weights.** Don't smooth, repaint or transfer them by default.
- Keep Python dependencies in a venv inside the workspace. Do not upload avatar files to third-party services.
- When I mark up screenshots, read them **literally**, and ask which pose and camera they came from. When I report
  a visual problem, match my words to a symptom in `troubleshooting.md`, confirm the cause with a render or a
  measurement, explain it back to me in plain words, then fix it.

## Phases (each ends at a gate; nothing is tagged approved or built on before its gate)

**A. Brief.** Ask the questions that otherwise surface late (they are the table in `DECISIONS.md`): which
references are authoritative, which assets I already own, the Unity toolchain (Modular Avatar means no armature
merging in Blender, one FBX per outfit), who makes textures, and which body keys the outfits expect. Also settle how
we get the target shape: a reference mesh to wrap the base onto, sculpting, or bone and shape-key edits. Write the
answers to `docs/DECISIONS.md`. Every question comes with your recommendation.
*Gate: I've answered.*

**0. Body.** Reshape the base mesh to the target, following `body-contract.md`.
- Vertex count and order stay unchanged; added shape keys are fine, removed or reordered ones are damage.
- Each edited region fades out smoothly (continuous in slope and curvature). Smooth displacement, never positions.
- No new flipped or degenerate triangles; triangle area ratio p99 < ~2.
- Geometry must agree with the painted anatomy on the body texture. Use UV-space landmarks.
- Iterate from labelled ladder sheets: orthographic front, side and rear, both three-quarters, high
  rear-three-quarter, close-ups, a seated and an arms-down pose, beside the canon references.
- Build the converter scaffold alongside (zero test on the unedited base first) and run provisional conversions of
  one or two real outfits onto each serious candidate: a body the converter can't carry is not a candidate.
*Gate: the independent reviewer, then my explicit approval. Nothing downstream starts before that.*

**B. Rig.** Make the approved shape the new rest of the base's own rig without breaking anything the base ships:
vertex count and order, UVs, materials, vertex groups and weights, and every base shape key (prove key-by-key that
each still does the same thing). If proportions are carried by bones, apply them as the new rest exactly once;
connected bones never receive translations, and any bone setting changed while posing is restored afterwards. Keep
what you do here simple and recorded: the converter has to reproduce it on every outfit.
*Gate: the preservation and vertex-ID gates (`gates/`) against the pristine purchased file pass.*

**C. Converter.** Build to `converter-spec.md`. It sets out the contract, the behaviour, the gates and the test
corpus, not the method. Before writing code, answer its §7 questions in `docs/DECISIONS.md` and show me the design.
Run every test outfit on the unedited base first (the baseline), then the gates in `gates/` from that baseline up.
*Gate: every spec gate passes on the test corpus; a fresh agent that has not seen your reasoning reviews the code,
the reports and the outputs and tries to break the contract; the image reviewer has checked the renders; I approve.*

**D. Assemble in Unity** (only when I say so). One FBX per outfit, Modular Avatar, Blendshape Sync for
outfit-expected body keys, then the SDK avatar audit. After every FBX re-import, check prefab bone transforms
against the FBX rest. I test every toggle, each outfit in motion, seated, and footwear on the floor in game.

## Techniques to consider

Not a recipe; families of technique that have done this job before. Pick, mix and record your choices.

*Body:* bone scale, rotation and unconnected-only translation in one pose applied as rest once (proportions; the
converter carries it most easily); whole-region moves with a smooth falloff (anything bones can't shape; if every
variant looks lumpy the falloff is too small); new shape keys or base keys driven past 1 (local shape and softness;
keep shape and volume as separate controls); a wrap toward a measured reference mesh (align by landmark heights,
bound the region, repair flips). Avoid Shrinkwrap, Surface Deform or remesh on the body.

*Converter:* carry the body's pose onto the outfit rig; a smooth displacement field for what bones can't express;
rigid-part fitting for jewellery and bells; a clearance pass that restores each vertex's original distance to the
skin; carry outfit-only bones with their cloth; sync body-key values by name. Avoid Data Transfer, Surface Deform,
weight transfer or smoothing as the method. The spec's §4b lists what each one looks like when it goes wrong.

## Lessons that cost the previous projects the most
1. The independent reviewer found what the passing numbers hid. Budget a full review before calling anything done.
2. Choose metrics that can see the defect. "0 inside at 1 mm" hid 72 verts inside and thousands within 0.8 mm.
3. Byte-identical output after a change means the change isn't running. Instrument it; don't argue.
4. Revert fixes that make things worse, and tell me with the measurement.
5. Look at assets; don't trust product titles. Wrong shopping picks came from names.
6. Use the strongest model for body shaping, converter maths and review, and a cheap model for renders and
   plumbing.
7. Compare against the original base, never against zero: the same outfit on the unedited base is the baseline.

## How we work
- Start each session by reading `docs/HANDOFF.md`. End it with a dated entry: what changed, exact commands,
  which symptom each fix addressed, open decisions.
- I answer numbered questions tersely, so always give your recommendation.
- Label every comparison sheet with letters, and refer to options by those letters.
- Before anything hard to undo (Unity edits, uploads, purchases, changing the base), ask me.
- Shopping: you shortlist with links and prices, judged from the item's images; I buy.

Begin with Phase A. Read what's in the workspace, then ask me your questions.

---

## Notes for whoever hands this over

- **For agents without skill support.** Claude Code users should install `skills/booth-avatar-edit/` instead. Give
  the agent this prompt plus `references/converter-spec.md`, `references/body-contract.md`,
  `references/troubleshooting.md`, the two `templates/`, and the `skills/booth-avatar-edit/gates/` folder (as `gates/` in your project); `DESIGN_PROCESS_NOTES.md` is for
  the person. On purpose, there is no converter and no record of our implementation, so they build their own toward
  the same result; the gates measure whether they got there.
