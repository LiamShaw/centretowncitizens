import json, urllib.request, sys, io, re, os
from pathlib import Path
sys.path.insert(0, "tools")
from export_squarespace import ImagePool
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA={"User-Agent":"Mozilla/5.0 (compatible; probe16/1.0)"}
SITE="https://www.centretowncitizens.ca"

# Recompute the filename mapping over every image URL the exporter saw
pool = ImagePool(Path("."))
mapping = {}
def register(url):
    base = url.split("?")[0]
    if base in mapping: return mapping[base]
    name = ImagePool.filename_for(base)
    mapping[base] = name
    return name

for p in ["/","/news","/advocacy","/events","/about","/contact","/get-involved","/newsletter","/cca-in-the-news-update"]:
    html = urllib.request.urlopen(urllib.request.Request(SITE+p,headers=UA),timeout=45).read().decode("utf-8","replace")
    for m in re.finditer(r'<img[^>]*src="([^"]+)"', html):
        register(m.group(1))

by_name = {}
for base, name in mapping.items():
    by_name.setdefault(name, []).append(base)
collisions = {n:v for n,v in by_name.items() if len(v)>1}
print(f"distinct source urls: {len(mapping)}  distinct names: {len(by_name)}")
print(f"collisions: {len(collisions)}")
for n, v in collisions.items():
    print(f"  {n}")
    for b in v: print(f"      {b}")

print("\n--- verify a description reads correctly ---")
p = Path("content/news/robert-smythe-the-passing-of-a-centretown-giant.md")
for line in p.read_text(encoding="utf-8").split("\n")[:8]:
    if line.startswith("description"):
        print(repr(line[:130]))
