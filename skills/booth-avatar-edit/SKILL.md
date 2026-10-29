---
name: booth-avatar-edit
description: Use when reshaping a purchased VRChat base avatar (BOOTH bases such as Kumaly, Milltina, Karin, Manuka) into a custom body or original character in Blender, when building or running an outfit converter so clothes, hair or accessories made for the original base fit an edited body, or when resuming such a project across sessions.
---

# BOOTH avatar edit

## Overview

Turn a purchased base avatar into the user's own body **without losing the base's outfit ecosystem**. Two
deliverables: an approved custom body, and an outfit converter that refits anything rigged and skinned for the
original base to that body. The user is the art director and approves every body; you do the maths, scripts,
renders and bookkeeping. **Nothing is done until someone has looked at it:** an independent image-only reviewer,
then the user, then the avatar worn in game. Numbers are supporting evidence only.

## Every session

1. Read `docs/DECISIONS.md` and `docs/HANDOFF.md` in the project. If they don't exist, copy them from this
   skill's `templates/` folder.
2. If you're new to the project, re-run the last recorded command from `HANDOFF.md` and confirm it reproduces the
   current checkpoint before changing anything.
3. Quote the user's decisions from `DECISIONS.md`, not from memory. Write each new decision or tip the moment it's
   given.
4. Before stopping, add a dated `HANDOFF.md` entry: what changed, **exact commands and parameters**, which symptom
   each fix addressed, what's open.

## Phases (each ends at a gate; nothing is *tagged approved or built on* before its gate)

| Phase | Work | Gate |
|---|---|---|
| A. Brief | Interview the user (all template questions at once, each with a recommendation); read `references/choosing-references.md`. Read-only prep is fine meanwhile: extract, hash, inventory the base and outfits, render the unedited base | Every question in the template answered |
| 0. Body | Reshape to the references; follow `references/body-contract.md`. Build the converter scaffold alongside (zero test on the unedited base first) and run provisional conversions of one or two real outfits onto each serious candidate: a body the converter can't carry is not a candidate | Independent image-only review, then **explicit user approval** |
| B. Rig | Make the approved shape the new rest without breaking the shape keys, UVs or weights | Preservation and vertex-ID gates (`gates/`) vs the pristine base pass |
| C. Converter | Build to `references/converter-spec.md`; answer its §7 in `DECISIONS.md` and show the design first | All spec gates on the test corpus, run from the original-base baseline up; an independent code-and-artefact review (fresh agent, strongest model, told to trust nothing, given the code, reports and outputs, not your reasoning); then the image review and user approval |
| D. Engine | Unity assembly, only when the user asks. Any Unity edit, including the converter's in-engine check, needs the user's OK | User wears it in game |

## Hard rules

- **Purchases are read-only.** Extract into `bases/<name>/`; derived files go elsewhere. Record hashes.
- **Script everything** (headless Blender, numpy). One command runs the chain and stops at the first failure; a
  failed step must never hand the previous run's file to the next one.
- **Version every checkpoint by tag. Never overwrite one.** If one was overwritten, regenerate it from the recorded
  commands, tag it, log the slip in `HANDOFF.md`.
- **Keep the base's own skin weights.** Don't smooth, repaint or transfer them by default (`converter-spec.md` §3.8).
- **Baseline first, compare against the original base, never against zero:** the same outfit on the unedited base
  is the baseline for every fit gate, measured *before* the first converter tweak.
- **Claim only what exists:** quote the file and the number.
- **Ask first** before purchases, uploads, editing the Unity project, or changing the base. Shopping: shortlist
  with links and prices; judge items by their images, not titles (page fetches return text; download and look).
- **Early in-game tests are welcome:** if the user asks, make a local build (no upload) labelled *provisional*.
  It's a fit check, not a gate pass.
- **When the user reports a visual problem or a gate fails,** read `references/troubleshooting.md`, match their
  words to a symptom, confirm the cause with a render or measurement, explain it back in plain words, then fix it.
- No uploading avatar files or images to third-party services. If the character is a person, they're an adult.

## Working with the user

Read `references/working-with-the-user.md` before the first body round. In short:
- Show **labelled ladder sheets** (variants A-E of one parameter beside the canon references). The user answers by
  letter. **Every question comes with your recommendation.**
- Read feedback literally. Ask which pose, camera and editor-or-game a screenshot came from, and reproduce that view
  before and after a fix.

## Red flags: stop and re-check

| Thought | Reality |
|---|---|
| "The metric improved, ship it" | Render it. Metrics improve while visuals get worse. |
| "Transfer the body weights onto the garment / smooth the body weights" | That breaks in poses and in Unity. Keep the shipped weights unless a gate proves otherwise. |
| "No visible poke-through at rest" | Test seated, arms down, bend, twist, against the original-base baseline. |
| "I'll overwrite the candidate to save space" | Tag it. Rejected candidates get asked for again. |
| "User wants to test tonight, just upload" | Local test build only. Uploads need explicit approval. |
| "Output identical after my fix" | The fix isn't running. Instrument it. |
| "That's a render artefact" | Look before you say so: re-render with the obstruction removed (the other leg, the hair). "Artefacts" were real clipping twice. |
| "My editor render looks clean, so it's fixed" | Reproduce the user's exact view (pose, camera, play mode or in game). Editor renders can show stale or unsimulated state. |
| "I'll push on, the context is just long" | When mistakes start creeping in, write the handoff and hand over. Long sessions misread numbers and lost tips. |
