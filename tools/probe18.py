import re, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = Path("public/advocacy/Blog Post Title One-x584z-3sp2r/index.html")
print("exists:", p.exists())
if p.exists():
    t = p.read_text(encoding="utf-8", errors="replace")
    i = t.find("legacy-url")
    print("context:", t[max(0,i-60):i+120] if i>0 else "NOT FOUND")
# list dirs with spaces
for d in Path("public/advocacy").iterdir():
    if " " in d.name: print("dir with space:", repr(d.name))
