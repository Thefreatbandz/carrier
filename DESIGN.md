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

## Phase 3 (shipped 2026-09-29) - DUNGEON DEPTHS
- Seeded multi-room dungeons replace the single open floor: entrance /
  combat / treasure / extraction room types, door gaps between connected
  rooms, tiled wall blocks, extraction pad in the farthest room (BFS)
- Chests: touch to open, 3-pickup loot shower, gold marker on minimap
- Weapons as loot: WORN SHIV -> RUSTY BLADE -> HUNTER'S EDGE -> PLAGUEBANE
  (tier by depth), each +1 damage with a toast; drop from brutes (12%),
  chests, and the boss (guaranteed)
- Boss every 3rd depth: THE WARDEN (brute, 6x HP, 1.5x damage, 1.5x size),
  red boss HP bar under the DEPTH label, guards the extraction pad,
  drops weapon + medkit + suppressant + 3 scrap, 150 XP
- Minimap draws the actual room layout (rects), chest + boss markers
- Touch fixes: screen->canvas coordinate conversion (fixed button taps
  double-firing attacks + joystick misplacement), left-half joystick zone,
  tactile styled buttons (normal/pressed/disabled states), joystick drawn
  under buttons, v0.3 build label on title
- QA: 27/27 phase-3 integration tests (connectivity, chest, weapon, boss,
  drops, minimap, depth-2 rebuild), 22/22 phase-2 regression green
- Deploy fix: root URL was serving the stale phase-1 index.* while the new
  build sat at carrier.html - now exports as index.* (root) and mirrors to
  carrier.* so both URLs serve the current build

## Phase 4 (shipped 2026-09-29) - GATE / ART / ANIMATION / PHYSICS / UI POLISH
- First-room exit fixed and rebuilt as a real GATE: DOOR_GAP widened
  180 -> 280, player collision shrunk to 52x64, doorway center has NO
  collision - two stone gatepost sprites flank the opening with a soft
  infection glow. Physics walk-through test proves traversal.
- New character art (48 generated frames): hooded outbreak carrier
  (glowing infection eyes, blade), SHAMBLER / RUNNER / BRUTE redesigns.
- Full animation contract: player idle/walk (3 directions, 4-frame walk),
  attack (3 frames), hurt, death; infected walk (4) / attack (2) / death (2).
  Attack + hurt anim locks; death pose reads 0.5s then fades.
- Combat physics: accel/decel movement, knockback with decay, enemy
  steering smoothing, distance-weighted separation (anti-stack), attack
  telegraph (0.35s windup) + lunge + cooldown, hit-stop on slash/kill,
  screen shake (trauma-based) on player hit/kill. Engine.time_scale always
  reset on death/draft/scene load.
- UI cleanup: bordered bars, HP number + green/yellow/red states with
  low-HP pulse, styled draft/death buttons, infection emphasis kept.
- Graphics: 4 floor tile variants (base/crack/grime/infection moss) in
  seeded 6x6 per-room mix, gate glows, pulsing extraction pad glow.
- Run-state persistence across depths still unproven (known issue).
- QA: walk-through PASS, 22/22 phase-2, 27/27 phase-3, zero script errors.

## Phase 5 (shipped 2026-09-29) - HD SPRITE PASS
- All 48 character frames redrawn at 2x (192x256) with gradient shading,
  rim light, glowing eyes/cracks, detailed cloth/armor/blade work.
- HD environment: 4 floor tiles (240px, fine grain + bevels), wall blocks
  (stone courses, mortar, moss), gate posts (carved stones, glowing runes),
  HD sword pickup + chests (open chest glows).
- Sprite scales halved to keep on-screen sizes; collisions unchanged.
- QA: walk-through PASS, 22/22 phase-2, 27/27 phase-3, zero script errors.

## RPG roadmap (Tbandz's blueprint, staged)
Loop: Explore -> Fight -> Loot -> Upgrade -> Discover -> Boss -> New
Dungeon -> Repeat. Infection meter stays the signature mechanic.
- Phase 4: inventory UI + equippable weapons/armor, loot rarity tiers,
  gold economy, elite infected, miniboss on depth 2 of each cycle
- Phase 5: combat depth - combos, dodge roll, block, crits, status effects
  (bleed/burn), elemental damage types, active skills beyond the 3 powers
- Phase 6: town/hub between cycles - NPCs, merchants, quests, crafting,
  multiple dungeon biomes, save data, achievements
- Phase 7: endgame - New Game+, endless dungeon, boss rush, challenge
  modifiers, daily seeded dungeon
Rules: classes optional (identity via equipment); hand-designed room
archetypes with randomized order; no duplicate systems; $0-first;
iPhone 12 smooth; every build gets a bug-check pass; Tbandz is final QA.
