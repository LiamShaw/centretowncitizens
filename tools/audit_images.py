import re, sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

root = Path(".")
md_files = list((root / "content").rglob("*.md"))
print(f"markdown files: {len(md_files)}")

refs = set()
for p in md_files:
    text = p.read_text(encoding="utf-8")
    for m in re.finditer(r"/images/([A-Za-z0-9._-]+)", text):
        refs.add(m.group(1))

on_disk = {p.name for p in (root / "static" / "images").iterdir() if p.is_file()}

# The favicon is referenced from the page head rather than from content, so
# it is never referenced by a Markdown file.
on_disk.discard("favicon.ico")

print(f"referenced images: {len(refs)}")
print(f"files on disk:     {len(on_disk)}")

missing = sorted(refs - on_disk)
orphans = sorted(on_disk - refs)
print(f"\nreferenced but MISSING on disk: {len(missing)}")
for m in missing[:20]:
    print("   ", m)
print(f"\non disk but never referenced:  {len(orphans)}")
for o in orphans[:40]:
    print("   ", o)

# Where do orphans come from? Check the live site for each orphan's filename.
print("\n=== check orphans against live site references ===")
import urllib.request
UA = {"User-Agent": "Mozilla/5.0 (compatible; audit/1.0)"}
SITE = "https://www.centretowncitizens.ca"
sm = urllib.request.urlopen(urllib.request.Request(SITE + "/sitemap.xml", headers=UA), timeout=45).read().decode()
paths = [u.replace(SITE, "") for u in re.findall(r"<loc>([^<]+)</loc>", sm)]
live = {}
for path in paths[:60]:
    try:
        html = urllib.request.urlopen(urllib.request.Request(SITE + path, headers=UA), timeout=30).read().decode("utf-8", "replace")
    except Exception:
        continue
    for m in re.finditer(r"https://images\.squarespace-cdn\.com/[^/]+/[^/]+/([^/?\"']+)", html):
        live.setdefault(m.group(1), []).append(path)
print(f"live image filenames seen on first 60 pages: {len(live)}")
for o in orphans:
    stem = o.rsplit(".", 1)[0]
    # match by the original stem before the token suffix we appended
    orig = re.sub(r"-\d{10,}$", "", stem)
    if orig in live:
        print(f"   {o}  <- live at {live[orig][:3]}")
    else:
        print(f"   {o}  <- NOT found on sampled live pages")
