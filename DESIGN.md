# CARRIER - design doc (working title, not final)

Original dungeon-descent extraction RPG. LAST SHIFT outbreak universe.
Core mechanic (Tbandz picked 2026-09-29): the INFECTION METER.
Direction call 2026-09-29: it's a DUNGEON game - descend the depths, fight
dungeon creatures (the infected), extract down. "FLOOR" renamed "DEPTH",
darker dungeon mood (vignette, dim tiles).

## The loop
1. Drop into a dungeon depth (top-down 2D pixel art).
2. Fight infected (shamblers, runners, brutes), grab loot (scrap / suppressant / medkit).
3. Reach the glowing extraction pad, channel 3s to descend.
4. Draft 1 of 3 upgrades between depths.
5. Die (HP 0) or TURN (infection 100%) = run over. Run it back.

## The infection meter (0-100%)
- Rises: +0.35/s passive, +6 per hit taken, powers cost chunks.
- Spend it: SURGE (3s +80% speed, 15%), FRENZY (5s 2x damage, 20%).
- Lowers: suppressant pickup -30%, extraction pad -5%/s while channeling.
- 100% = you turn. Run over.

## Risk/reward (the longevity engine)
Push deeper for better loot or extract and bank it. Harder floors scale
infected HP/speed/damage + spawn rate. Upgrade draft compounds builds.

## Phase 1 (shipped scope)
- Procedural floors (seeded), border + interior walls, rubble/door decor
- 1 infected type (crawler), spawner, touch damage
- Melee swing, 2 powers, suppressant/medkit/scrap
- Extraction pad + channel + floor progression
- 4-upgrade draft pool, death/turn screens, retry
- Touch: floating joystick (left), tap right = attack, power buttons
- Desktop: WASD/arrows, Space, Q/E

## Later phases
- Meta progression: XP, skill tree, base upgrades (persist across runs)
- More infected types, boss floors
- More dungeon biomes, daily seeded dungeon

## Phase 2 (shipped 2026-09-29)
- 3 infected types with real art: SHAMBLER (slow, tanky, floor 1), RUNNER
  (fast, fragile, floor 2+), BRUTE (big, heavy hitter, floor 3+)
- 13 synthesized sound effects (swing/hit/die/pickup/powers/level/death/extract ticks)
- SENSE power (10% infection, 4s loot+pad markers, 10s cd, key F)
- XP/levels: kills grant XP, level-ups heal 30%, +12 max HP, +1 dmg every 2nd level
- Big ATTACK button (kept tap-right attack); SENSE joins SURGE/FRENZY buttons
- Minimap: player/pad/pickups/infected dots, pulsing extraction marker
- Animation: attack lunge, walk bob, hit knockback + flash, shrink-out death
- Dungeon reframe: DEPTH label, darker tiles, vignette
- QA: 22/22 integration tests green (1 real bug found + fixed: kill rewards
  skipped when main wasn't current_scene - group fallback added)
