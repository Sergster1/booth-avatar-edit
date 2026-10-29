# Decisions

One source of truth. Quote from here, not from memory. Date every entry and use the user's own words.

## Phase A brief

| # | Question | Answer (user's words) | Date |
|---|---|---|---|
| 1 | The character in one paragraph | | |
| 2 | The one proportion that matters most, and which way to lean when in doubt | | |
| 3 | Canon references: which image is authoritative for what (size, shape, design details, style) | | |
| 4 | Official art? Which source wins a conflict? | | |
| 5 | Base avatar (zip path) and outfits/hair/accessories already owned (zip paths); any part of the base or owned assets that already matches the character (ears, horns, tails, chokers) | | |
| 6 | Outfits that must keep working; any that rely on body shape keys | | |
| 7 | Unity version and toolchain (VRChat SDK, Modular Avatar, VRCFury, shaders, optimisers) | | |
| 8 | PC only or Quest too; performance targets | | |
| 9 | Who makes textures | | |
| 10 | How the target shape is made (reference mesh wrap, sculpt, bones and keys, mix) | | |
| 11 | Review views and poses (incl. seated and arms down) | | |
| 12 | Height, size ceilings and anything off limits | | |
| 13 | How bold the first round should be | | |
| 14 | Git: local only, or a remote? | | |

## Locked values

| Name | Value | Approved by user on |
|---|---|---|

## Tips from the user

- (date) "..." → how it's applied

## Destructive edits (user-approved, each one listed)

- (date) what changed beyond positions, why, what was asserted unchanged

## Converter design (spec §7)

Answer each question in the spec's §7 before writing code, and show the user. One or two sentences each:
**the choice, why, and how you'll prove it works** (which gate or render). Example of the expected depth:

- *In-engine check?* "The user wears a local build at each milestone; I compare prefab bone transforms with the FBX
  rest after every re-import, because a stale prefab hides a correct conversion."

Your answers:

- 
