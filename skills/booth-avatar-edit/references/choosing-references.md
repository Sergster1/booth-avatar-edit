# Choosing references (phase A)

References can be official art, commissioned or hand-drawn art, fan art, existing 3D models, or generated images.
The source matters less than naming **which image is authoritative for which attribute**.

## Ask the user

- Which image is right about *what*? Size from one, shape from another, design details from a third.
- If two images disagree (a garment, horns, makeup, a mole), which wins? Write it in `DECISIONS.md`.
- Is there official art? If there is, it settles design disputes.
- Which single image best captures the overall look? The reviewer is told that.

## Know the failure modes

| Source | Watch for |
|---|---|
| Several artists | Conflicting designs (a texture built on the wrong garment); one artist's stylisation mistaken for anatomy (e.g. a hard ledge at stocking tops is clothing compression, not body shape). |
| One generated style | Seeds disagree on details, so it needs a design-lock pass. Some generations quietly change proportions. Style artefacts (stylised highlights) aren't anatomy. Easy to fill gaps: rear, side, close-ups on demand. Labels lie: a "back" view may face the camera; check each image before it goes to the reviewer. |
| 3D reference mesh | Missing or fused surfaces (under clothing, the head under hair). Measure only what's really there. |

## Rules

1. **Measure against something 3D** (a reference mesh, the base's own renders). Judge against drawings; never
   measure them.
2. **Treat style quirks as style.** Ask "is this the artist or the body?" before modelling a feature.
3. **With no official canon, the user's picks are the canon.** Give the reviewer only the canon unless you're stuck.
4. If you generate extra references, run that in a separate session or job queue, not from the main build.
