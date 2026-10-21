import re, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
t = Path("public/index.html").read_text(encoding="utf-8", errors="replace")
for m in re.finditer(r'<img[^>]*>', t):
    print("IMG:", m.group(0)[:200])
print()
print("hero region:")
i = t.find("hero")
print(t[i-100:i+700])
