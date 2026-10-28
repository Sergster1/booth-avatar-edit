# booth-avatar-edit

Design docs and a Claude Code skill for handing a **BOOTH avatar edit** to an AI agent. Start from a purchased
VRChat base avatar, reshape it into your own character with the agent, and end up with:

- **your custom avatar body**, approved by you render by render, and
- **an outfit converter** that refits anything rigged and skinned for the original base (clothes, hair,
  accessories) to your edited body. When you change the body later, the agent re-runs the pipeline and your
  outfits follow.

There is **no code** here, on purpose. Your agent builds its own tools to the specs, toward the same result. You
direct the art; the agent does the 3D maths.

Based on what Sergster learned building two avatars this way. Please credit Sergster in derivatives.

## What's inside

| Path | For | What it is |
|---|---|---|
| `skills/booth-avatar-edit/` | the agent | The skill: phases, gates, hard rules, and references (body contract, converter spec, choosing references, working with the user) plus `DECISIONS.md` / `HANDOFF.md` templates |
| `docs/DESIGN_PROCESS_NOTES.md` | you | How the design process went: what worked, what sped it up, what slowed it down, and the nudges that changed the result |
| `docs/BOOTH_AVATAR_STARTER_PROMPT.md` | agents without skills | The same workflow as a paste-in prompt with fill-in slots |

## Install (Claude Code)

Copy `skills/booth-avatar-edit/` into `~/.claude/skills/` (all projects) or `<your project>/.claude/skills/` (one
project). Then open your project and describe what you want, e.g. *"I bought the Kumaly base and some outfits; help
me turn her into my own character."* The skill loads when the task matches.

Other agents: paste `docs/BOOTH_AVATAR_STARTER_PROMPT.md` and give them
`skills/booth-avatar-edit/references/converter-spec.md`.

## What you'll still do

- Provide references and say which image is right about what
- Approve every body round (pick by letter)
- Test in VRChat at each milestone
- Buy assets and approve uploads

Read `docs/DESIGN_PROCESS_NOTES.md` before you start. It'll save you rounds.

## Respect the licences

BOOTH assets come with their own terms. The workflow never modifies or redistributes the purchased files. Check
each asset's terms before editing it or sharing anything derived from it.
