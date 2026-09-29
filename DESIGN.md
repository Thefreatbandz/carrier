# CARRIER - design doc (working title, not final)

Original tower-extraction RPG. LAST SHIFT outbreak universe.
Core mechanic (Tbandz picked 2026-09-29): the INFECTION METER.

## The loop
1. Drop onto a tower floor (top-down 2D pixel art).
2. Fight infected, grab loot (scrap / suppressant / medkit).
3. Reach the glowing extraction pad, channel 3s to descend.
4. Draft 1 of 3 upgrades between floors.
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
- More infected types, boss floors, Sense power (loot radar)
- Proper infected art (replace slime stand-in)
- Sound, more tower biomes, daily seeded tower
