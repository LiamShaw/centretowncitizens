import sys, io
sys.path.insert(0,"tools")
from export_squarespace import content_blocks, plain_text, fetch
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
html = fetch("https://www.centretowncitizens.ca/")
for btype, inner in content_blocks(html):
    t = plain_text(inner)
    print(f"[{btype}] {t[:150]!r}")
