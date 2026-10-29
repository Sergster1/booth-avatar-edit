# Working with the user

## The loop for every visual round

1. A **ladder sheet**: 3-5 variants of one parameter, labelled A-E, beside the canon references, in the agreed views.
2. An **independent image-only reviewer**: spawn a separate agent whose prompt contains only the sheet and
   canon-reference image paths, what the user loves, and the scope ("judge proportions only"). No code, numbers or
   your own opinion. Save its review verbatim next to the sheet.
3. Show the user the sheet and the review together, **with your recommendation**.
4. Record the pick. **Lock** approved values by name so later rounds don't move them.

The user's short answers ("rec", "C", "between B and C", "the middle one's shape at the last one's size") only work
if every option is labelled and every question has a recommendation.

## Freedoms to use (and to tell the user you're using)

Agents default to the narrowest safe tool and invent limits nobody set. You may:
- **Move whole regions with a smooth falloff,** like proportional editing. If every variant looks lumpy, your edit
  is too local.
- **Edit the structure under a feature,** not just the feature: pull in the chest wall beneath an overhang, move the
  ribcage, reshape what something rests on. Tedious for a human in Blender; just another displacement for you.
- **Break symmetry and uniformity** (unequal bone scales per axis, rotate or translate paired bones apart) when it
  keeps the shape right.
- **Accept a small, stated trade-off** (some clipping) for a better look, once the user has said which they prefer.
- **Use any mechanism:** bones, shape keys, displacement, shape keys driven above 1.
- **Generate plenty, then filter:** many angles or variants, with the reviewer picking the best.

## Model per task

Strongest model for body shaping, converter maths and the code review; a mid-tier model is fine for routine
image reviews; cheap for renders and plumbing. Reviewers always run as separate agents with their own context.

## Feedback

- Read it **literally**. "Only this contour" means only that.
- Shape words carry meaning: "pumpkin, not torpedo", "too much mass on top". Turn them into ladder axes (where
  the mass sits: up/down, in/out; projection vs width; roundness), and ask only when two readings would give
  different ladders.
- Order matters: fix what a shape rests on before the shape (back before chest, structure before detail).
- If the user hints at a future change ("I may want less volume, same shape"), build it in as its own control.
- **Bold beats timid.** If a round was "too subtle", the next one should be clearly bigger.
- Invite pushback ("you may disagree") and give an honest answer with evidence.
- When something looks off, compare it with a working original (the pristine base, another avatar the user made).
- When the user reports a visual problem, go to `troubleshooting.md`: match their words, confirm with a render or a
  measurement, explain it back in plain words, then fix. Log the symptom with the fix in `HANDOFF.md`.

## What wastes rounds

- Misreading a number or forgetting a tip: quote `DECISIONS.md`.
- Decisions surfacing late: ask everything in phase A.
- Problems only visible in game: ask the user for an in-game check at each milestone.
- A fix that breaks something else: report the regression with the measurement, revert, try another approach.
