import re, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
pub = Path("public")
bad = []
n = 0
for line in Path("public/_redirects").read_text(encoding="utf-8").splitlines():
    if line.startswith("#") or not line.strip():
        continue
    parts = line.split()
    if len(parts) < 2: continue
    src, dst = parts[0], parts[1]
    n += 1
    if "?" in dst:
        path = dst.split("?")[0]
    else:
        path = dst
    p = path.lstrip("/")
    target = (pub / p / "index.html") if p.endswith("") and (pub/p).is_dir() else (pub / p)
    if not target.exists():
        cand = pub / p / "index.html"
        if not cand.exists():
            bad.append((src, dst))
print(f"redirects: {n}")
print(f"targets with no built page: {len(bad)}")
for s, d in bad[:30]:
    print(f"   {s}  ->  {d}")
