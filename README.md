# booth-avatar-edit

Design docs, a Claude Code skill and a set of acceptance gates for handing a **BOOTH avatar edit** to an AI agent.
Start from a purchased VRChat base avatar, reshape it into your own character with the agent, and end up with:

- **your custom avatar body**, approved by you render by render, and
- **an outfit converter** that refits anything rigged and skinned for the original base (clothes, hair,
  accessories) to your edited body. When you change the body later, the agent re-runs the pipeline and your
  outfits follow.

There is **no converter** here, on purpose: your agent builds its own to the spec, toward the same result. What *is*
included is the set of acceptance **gates** (`gates/`), because measuring wrong was the most expensive mistake in
both builds this comes from. You direct the art; the agent does the 3D maths.

Based on what I learned building two avatars this way.

## What's inside

| Path | For | What it is |
|---|---|---|
| `skills/booth-avatar-edit/` | the agent | The skill: phases, gates, hard rules, and references (body contract, converter spec, choosing references, working with the user, troubleshooting) plus `DECISIONS.md` / `HANDOFF.md` templates |
| `gates/` | the agent | Headless-Blender scripts that measure the gates (vertex IDs, preservation, non-destructive, fit under motion vs the original base, rest match, FBX round trip), a config for your base's names, pose and accepted-regression templates, example reports. MIT |
| `docs/DESIGN_PROCESS_NOTES.md` | you | How the design process went: what worked, what sped it up, what slowed it down, and the nudges that changed the result |
| `docs/BOOTH_AVATAR_STARTER_PROMPT.md` | agents without skills | The same workflow as a paste-in prompt with fill-in slots |

## Install (Claude Code)

Copy `skills/booth-avatar-edit/` into `~/.claude/skills/` (all projects) or `<your project>/.claude/skills/` (one
project). Copy `gates/` into your project (e.g. `<your project>/gates/`). Then open your project and describe what you
want, e.g. *"I bought the Kumaly base and some outfits; help me turn her into my own character."* The skill loads
when the task matches.

Other agents: paste `docs/BOOTH_AVATAR_STARTER_PROMPT.md` and give them
`skills/booth-avatar-edit/references/converter-spec.md`, `body-contract.md`, the two templates and `gates/`.

## What you need

- Blender (the gates were tested with 5.1; run headless from the command line), Python 3 with numpy
- Unity with the VRChat SDK and whatever your avatars use (Modular Avatar, VRCFury, your shaders)
- The base avatar and the outfits you own, as the purchased zips, and their licence terms for edits

## What you'll still do

- Provide references and say which image is right about what
- Approve every body round (pick by letter)
- Test in VRChat at each milestone
- Buy assets and approve uploads
- Expect Unity-side work (prefab setup, toggles, physics bones, importer settings) that the converter does not
  regenerate: after a re-conversion the FBX follows, the Unity setup on top of it is yours or the agent's to redo

Read `docs/DESIGN_PROCESS_NOTES.md` before you start. It'll save you rounds.

## Respect the licences

BOOTH assets come with their own terms. The workflow never modifies or redistributes the purchased files. Check
each asset's terms before editing it or sharing anything derived from it. The kit itself is MIT (`LICENSE`).
