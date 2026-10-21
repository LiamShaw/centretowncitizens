import re, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
for name in ["advocacy/returntooffice", "advocacy/cca-expresses", "news/robert-smythe-the-passing-of-a-centretown-giant"]:
    p = Path("public") / name / "index.html"
    t = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'<meta name=legacy-url content=([^ >]+)', t)
    print(f"{name}\n   -> {m.group(1) if m else 'NOT FOUND'}")
