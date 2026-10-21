import json, urllib.request, sys, io, re
from pathlib import Path
sys.path.insert(0,"tools")
from export_squarespace import ImagePool
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA={"User-Agent":"Mozilla/5.0 (compatible; probe17/1.0)"}
SITE="https://www.centretowncitizens.ca"
sm=urllib.request.urlopen(urllib.request.Request(SITE+"/sitemap.xml",headers=UA),timeout=45).read().decode()
paths=[u.replace(SITE,"") for u in re.findall(r"<loc>([^<]+)</loc>",sm) if "/events/" in u]
byname={}
for p in paths:
    try:
        d=json.loads(urllib.request.urlopen(urllib.request.Request(SITE+p+"?format=json-pretty",headers=UA),timeout=45).read().decode("utf-8"))
    except Exception: continue
    it=d.get("item") or {}
    au=it.get("assetUrl")
    if not au: continue
    b=au.split("?")[0]
    byname.setdefault(ImagePool.filename_for(b),[]).append(b)
for n,v in byname.items():
    if len(set(v))>1:
        print("COLLISION:",n)
        for x in set(v): print("   ",x)
print("done")
