"""Mirror live script files into build_godot.py sections. Usage: python3 mirror_builder.py [path ...]"""
import sys

NL = chr(10)

def new_block(p):
    with open(p) as f:
        content = f.read()
    assert '"""' not in content, p
    return 'W("' + p + '", """' + content + '""")'

def replace_section(src, p):
    wpos = src.find('W("' + p + '", """')
    assert wpos != -1, p
    h = src.rfind('# =', 0, wpos)
    assert h != -1, p
    lstart = src.rfind(NL, 0, h) + 1
    cstart = wpos + len('W("' + p + '", """')
    cend = src.find(NL + '""")', cstart)
    assert cend != -1, p
    cend = cend + len(NL + '""")')
    header = src[lstart:src.find(NL, h)]
    return src[:lstart] + header + NL + new_block(p) + src[cend:]

paths = sys.argv[1:] or ["project.godot", "scripts/player.gd", "scripts/main.gd",
    "scripts/infected.gd", "scripts/slash.gd", "scripts/pickup.gd",
    "scripts/hud.gd", "scripts/title.gd", "scripts/sfx.gd"]

with open("build_godot.py") as f:
    src = f.read()
for p in paths:
    src = replace_section(src, p)
    print("mirrored", p)
with open("build_godot.py", "w") as f:
    f.write(src)
print("done")
