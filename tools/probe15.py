import json, urllib.request, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA={"User-Agent":"Mozilla/5.0 (compatible; probe15/1.0)"}
SITE="https://www.centretowncitizens.ca"
d=json.loads(urllib.request.urlopen(urllib.request.Request(f"{SITE}/news?format=json-pretty",headers=UA),timeout=45).read().decode("utf-8"))
for it in d["items"]:
    if "robert" in (it.get("urlId") or ""):
        ex=it.get("excerpt")
        print("excerpt repr:", repr(ex[:120]))
        print("codepoints:", [(c,hex(ord(c))) for c in ex[:80] if ord(c)>127])
