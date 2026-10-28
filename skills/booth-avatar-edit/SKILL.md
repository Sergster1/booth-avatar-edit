---
name: booth-avatar-edit
description: Use when reshaping a purchased VRChat base avatar (BOOTH bases such as Kumaly, Milltina, Karin, Manuka) into a custom body or original character, or when outfits, hair or accessories made for the original base must be refitted to an edited body. Also use when resuming such a project across sessions.
---

# BOOTH avatar edit

## Overview

Turn a purchased base avatar into the user's own body **without losing the base's outfit ecosystem**. There are two
deliverables: an approved custom body, and an outfit converter that refits anything rigged and skinned for the
original base to that body. The user is the art director and approves every body. You do the maths, the scripts,
the renders and the bookkeeping.

**Core principle:** nothing is done until someone has *looked* at it. Renders judged by an independent image-only
reviewer, then the user, and finally the avatar worn in game. Numbers are supporting evidence only.

## Every session

1. Read `docs/DECISIONS.md` and `docs/HANDOFF.md` in the project. If they don't exist, copy them from this
   skill's `templates/` folder.
2. Quote the user's decisions from `DECISIONS.md`, not from memory. Write each new decision or tip the moment it's
   given.
3. Before stopping, add a dated `HANDOFF.md` entry: what changed, **exact commands and parameters**, what's open.

## Phases (each ends at a gate; never start the next one early)

| Phase | Work | Gate |
|---|---|---|
| A. Brief | Interview the user (all template questions at once, each with a recommendation); read `references/choosing-references.md`. Read-only prep is fine meanwhile: extract, hash, inventory the base and outfits, render the unedited base | Every question in the template answered |
| 0. Body | Reshape to the references; follow `references/body-contract.md` | Independent image-only review, then **explicit user approval** |
| B. Rig | Make the approved shape the new rest without breaking the shape keys, UVs or weights | Preservation report vs the pristine base passes |
| C. Converter | Build to `references/converter-spec.md`; answer its §7 in `DECISIONS.md` and show the design first | All spec gates on the test corpus + review + user approval |
| D. Engine | Unity assembly, only when the user asks. Any Unity edit, including the converter's in-engine check, needs the user's OK | User wears it in game |

## Hard rules

- **Purchases are read-only.** Extract into `bases/<name>/`; derived files go elsewhere. Record hashes.
- **Script everything** (headless Blender, numpy). A body nobody can regenerate is a liability.
- **Version every checkpoint by tag. Never overwrite one.**
- **Keep the base's own skin weights.** Don't smooth, repaint or transfer them by default; see `converter-spec.md` §3, item 8.
- **Compare against the original base,** never against zero: the same outfit on the unedited base is the baseline
  for every fit gate.
- **Claim only what exists:** quote the file and the number.
- **Baseline first:** run every test outfit on the unedited base *before* the first converter tweak.
- **Ask first** before purchases, uploads, editing the Unity project, or changing the base.
- **Early in-game tests are welcome:** if the user asks, make a local build (no upload) labelled
  *provisional*, with the current candidate. It's a fit check, not a gate pass.
- **If a checkpoint was overwritten,** regenerate it from the recorded commands, tag it, and log the slip in
  `HANDOFF.md`.
- No uploading avatar files or images to third-party services. If the character is a person, they're an adult.

## Working with the user

Read `references/working-with-the-user.md` before the first body round. In short:
- Show **labelled ladder sheets** (variants A-E of one parameter beside the canon references). The user answers by
  letter.
- **Every question comes with your recommendation.**
- Read feedback literally. Ask which pose, camera and editor-or-game a screenshot came from.
- You have freedoms the user may not think to grant: say so, and use them.

## Red flags: stop and re-check

| Thought | Reality |
|---|---|
| "The metric improved, ship it" | Render it. Metrics improve while visuals get worse. |
| "Transfer the body weights onto the garment / smooth the body weights" | That breaks in poses and in Unity. Keep the shipped weights unless a gate proves otherwise. |
| "No visible poke-through at rest" | Test seated, arms down, bend, twist, against the original-base baseline. |
| "I'll overwrite the candidate to save space" | Tag it. Rejected candidates get asked for again. |
| "User wants to test tonight, just upload" | Local test build only. Uploads need explicit approval. |
| "Output identical after my fix" | The fix isn't running. Instrument it. |
