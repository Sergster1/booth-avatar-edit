# Designing a custom avatar with an agent: how it went

Notes on how the user (Sergster) and an AI agent took a purchased BOOTH avatar to a custom character with its own
outfit converter. They are written generically so someone else can use them as a guide. They describe the
**collaboration**, not the technical method: the spec and the starter prompt cover that.

---

## The shape of the process

1. **Write down who the character is, in one paragraph.** Body, head, details, the overall feel. Then name the one
   proportion that matters most and say which way to lean when in doubt (e.g. "the wider the X the better"). That
   one sentence settled more arguments than any measurement did.
2. **Provide references, then pick the authoritative ones.** Reference art can be commissioned or hand-drawn,
   official art, existing models, or generated images, ideally in one consistent style. The user then said
   *which* image was right about *what*, e.g. "this one's tummy is perfect", "this one's
   thighs are amazing", "aim between them". The references became canon, and everything else was advisory.
3. **A grilling session to lock decisions.** The agent listed every open choice (about two dozen: design details,
   base, outfit, accessories, limits) as numbered questions with a recommendation for each. The user answered them
   in one sitting, often just "rec" or a letter. The answers went into a decisions file the agent re-reads every
   session.
4. **A written design, then a plan, then execution.** Each was approved before the next started.
5. **Body rounds.** Each round: the agent renders labelled candidates beside the canon references, an independent
   image-only reviewer agent critiques them, and the user picks or redirects. Repeat until the user approves. Only
   the user approves a body.
6. **Converter, outfits, then the engine.** Each outfit was converted, gated and rendered. Then in-game testing by the
   user fed back into fixes.
7. **A handoff entry at the end of every session:** what changed, the exact commands, what's open. The next
   session, or a new agent, starts from it.

## Choosing references

Two builds with this workflow used references differently. One used official art plus fan art from several
artists, with the body shape taken from a measured 3D reference mesh. The other used images generated in one
consistent art style, with one canon portrait. That isn't a controlled comparison, but the pattern was clear.

**Several artists, with official art**
- **Artists disagree on the design.** Fan art showed a different top from the official design, and a texture was
  built on the wrong garment before anyone asked which was right.
- **One artist's style can pass for anatomy.** A hard shape break at the stocking tops in one artist's work showed
  up in the reference mesh too, and had to be recognised as clothing compression, not body shape.
- **Plus:** a real canon exists, so a conflict has a right answer to check against.

**One generated style**
- **Plus:**
  - Every round can be judged against one look ("does this read as the canon portrait from every view?").
  - Missing views can be made on demand (rear, side, close-ups), including over the base's own clay renders for
    registration.
  - The reviewer judges proportion without translating between styles.
- **Still has the same problems:**
  - Seeds disagree on details: horns, makeup, accessories, mole position, colours. That needs a design-lock pass.
  - Some generations quietly change proportions.
  - The style adds artefacts that aren't anatomy, such as stylised highlight shapes.
  - Nothing is measurable.
- **In the end the user still had to name canon** (one portrait and one pick), and the reviewer was limited to those.

**What holds either way**
1. **Name the authoritative image for each attribute:** size from one, shape from another, design details from a
   third. This mattered more than where the images came from.
2. **Treat style quirks as style.** Ask "is this the artist or the body?" before modelling a feature.
3. **Measure against something 3D**, such as a reference mesh or the base's own renders. Judge against the drawings,
   never measure against them.
4. **A consistent style helps you iterate; official art settles disputes.** Use whichever you have. When there is
   no canon, the user's picks become the canon. Write them down.

## What went well

- **Pointing at images instead of describing them.** "The tummy in A, the thighs in B, the style of B" beat any
  number of adjectives.
- **Labelled comparison sheets.** Every choice was shown as a sheet with letters, and the user answered with
  letters. It's fast and unambiguous, and the answer is easy to record.
- **The agent always recommending.** Short answers ("rec", "C", "go with your recs") only work if every question
  comes with a recommendation and a reason.
- **An independent reviewer before the user.** A separate agent that sees only the renders (no code, no numbers, no
  earlier conversation) found real problems the numbers missed: seams, ledges, shapes that read wrong from one angle.
  The user's time went to taste, not to catching bugs. A cheaper model at medium effort was fine for routine
  reviews. The reviewer was told what the user loves, and shown only the canon references unless the work was stuck.
- **Blunt, specific feedback.** "Those look awful, they lose the shape entirely", "the change being subtle is
  unacceptable", "I'd rather some clipping than them being flat against each other". Hearing what's wrong *and*
  which trade-off the user prefers lets the agent move in one step.
- **Tips from experience.** The user sometimes knew the order that works ("fix the upper back first, then the
  chest") or a constraint ("these don't need to be equal; whatever keeps them rounded"). Each tip saved a round or
  two.
- **Hard rules stated early and written into the project instructions:** never modify purchases, local-only git,
  naming, no uploads, ask before purchases and engine edits. Nothing had to be re-argued.
- **"Reference X, do it like that."** Pointing the agent at an existing, working avatar or setup ("set it up like my
  other avatar does it") produced correct results quickly.

## Nudges from the user that changed the result

Some of the biggest jumps came from short remarks about *how* to approach a problem, rather than from feedback on
a render. The agent tended to pick the narrowest, safest tool and to work within limits nobody had set. These
remarks removed those limits. Paraphrased from the sessions:

- **"Did you try proportional editing?"** A whole round of local fixes all looked bad: shapes pushed in one spot,
  with hard edges where they stopped. The fix was to move a whole region with a smooth falloff, the way an artist
  would with proportional editing. *Lesson: if every variant looks lumpy, the edit is too local.*
- **"You have it easier than me: you're working with maths, not tools."** The user pointed out that the agent could
  move the structure *under* a feature (pull in the chest wall beneath an overhanging shape to make room) instead
  of pushing only the feature itself. A human in Blender would avoid that because it's tedious; for an agent it's
  just another displacement. *Lesson: tell the agent it can edit anything, including the parts nobody would hand-edit.*
- **"They don't need equal scales; use whatever keeps them rounded and fits the reference."** The agent had kept a
  pair of bones uniform and symmetric by default. *Lesson: say which constraints are real and which the agent
  made up.*
- **"If there's clipping, translate the bones apart or rotate them. I'd rather have some clipping than a flat
  look."** It named the fix and the trade-off at once, so the agent stopped optimising the wrong thing (zero
  contact) at the cost of the look.
- **"It should sag a bit, but control that however you like, with bones or editing."** It gave the goal and left
  the method open.
- **"Pumpkins, not torpedoes." "Too much mass on top instead of the bottom."** Analogies and *where the mass sits*
  carried shape better than measurements.
- **"Work on the upper back first, then the chest."** Fix what something rests on before the thing itself. The
  user's sense of order saved rounds.
- **"Take the size from the canon portrait, the shape and transitions from that other model."** References were
  split by attribute: one source for how big, another for how it's shaped.
- **"Look at the pristine base in Unity" / "use my other avatar as the reference for how I do emissions."** When a
  result looked off, comparing it with a working original found the cause faster than reasoning about it.
- **"Before the lock, maybe widen the chest bone. You may disagree if you think it's unnecessary."** Asking for
  pushback got an honest answer: the reviewer showed the change barely mattered, and why.
- **"Longer ears: drive the shape key above 1."** Engine and tool tricks the user knew, which the agent didn't think
  to try.
- **"Keep in mind I may later want less volume but the same shape."** Saying future changes early let the agent
  build them in as a separate control.
- **"Get as many angles as you need, then let the reviewer pick the best ones."** Generating plenty and filtering
  beat carefully making a few.
- **"The reviewer should focus only on the body proportions."** Scoping the reviewer kept its notes useful.
- **"Tell me how you'd do it before you go outside the usual toolchain."** It made the agent propose before
  building in the uncommon cases.
- **"I gave you that tip earlier."** A tip was lost between sessions. Write every tip into the decisions file the
  moment it's given.

## What sped things up

- **Answering many decisions in one sitting**, instead of drip-feeding them while work was underway.
- **Ladders instead of single tries.** Three to five variants of one parameter on one sheet, so the user could say
  "between B and C" or "the middle one's shape at the last one's size".
- **One region at a time**, in an order that made sense (structure before detail, back before front where they
  interact). Then lock what's approved so later rounds don't move it.
- **Locking approved values by name** ("width ×1.20 LOCKED") so nobody revisited them.
- **Parallel streams** while waiting on the user: tooling, asset renders and shopping lists ran beside the body
  rounds.
- **Shortlists with links and prices**, so the user only had to buy.
- **Keeping reference-making separate.** If you generate extra reference images, run that in its own session
  with its own job files, not from the main agent.
- **"No further checks needed" / "one render is enough"** when the user was satisfied, so the agent stopped
  polishing.

## What slowed things down

- **Misread instructions.** A number was read an order of magnitude off, a tip was forgotten, a height was misplaced.
  Each cost a round. The fix that stuck: the agent quotes the user's words from the decisions file, not from memory,
  and reads feedback literally.
- **Decisions surfacing late.** Which images were authoritative, which assets were already owned, which engine tools
  were in use, which outfits relied on body features. Every late answer meant rework. Ask them all up front.
- **Numbers that looked fine on a broken result.** A metric improved while the visual got worse. Only renders, and
  in-game tests, caught it.
- **The engine behaving differently from the editor.** Toggles, bone positions, weights and optimiser tools that looked
  right in the editor broke in game. Problems only the user could see in VRChat took a round trip each.
- **Fixes that broke something else.** For example, a tool that merged meshes broke toggles, and a height fix bent
  the calves. Each needed a revert and a second approach.
- **Subtle changes when the user wanted obvious ones.** Being conservative wasted a round when the user's taste was
  "go further".
- **Long sessions and agent handoffs.** Context ran out and new agents had to catch up. A good handoff entry made
  this cheap, and a vague one made it expensive.

## What could have gone better

- **Collect every decision before building**, including engine and toolchain questions, owned assets, and what each
  outfit expects from the body. A checklist up front beats discovering them one by one.
- **Agree on the review views and poses at the start**, including the ones that expose problems (seated, arms down,
  high angles), so early rounds aren't judged from flattering angles only.
- **Test in game earlier and more often.** The editor was not a reliable stand-in for VRChat. A small "wear it and
  move" check after each milestone would have caught several issues sooner.
- **Record how every input was made from the first day.** Anything made ad hoc can't be regenerated later.
- **Tell the agent its freedoms on day one.** Most of the nudges above could have been a paragraph at the start:
  you may move whole regions with falloff, edit structure under a feature, break symmetry, use bones or shape
  keys, accept small clipping for a better look. Agents default to the narrowest safe option.
- **Say "bigger steps" sooner.** When the user's taste runs bold, tell the agent at the start so its first try isn't
  timid.
- **Screenshots with context.** "Which pose, which camera, editor or in game?" saved time once it became a habit.
  Put that with the screenshot.
- **Keep one source of truth for decisions.** When decisions were spread across chat, handoff notes and config, they
  got misread. One table, kept current, is better.

## A template for your own run

1. One paragraph + one "when in doubt, lean this way" rule.
2. Canon references, each with what it's authoritative *for*.
3. A grilling session: numbered questions, a recommendation for each, all answered before building.
4. A design, a plan and the hard rules, written into the project instructions.
5. Rounds: labelled ladder sheet → independent image-only review → the user's pick → lock.
6. In-game check at every milestone.
7. A handoff entry every session, with exact commands.
