import json, urllib.request, re

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe2/1.0)"}
SITE = "https://www.centretowncitizens.ca"

def raw(path):
    url = f"{SITE}{path}?format=json-pretty"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.headers.get("Content-Type"), r.read()

# 1. mainContent shape for a static page
ct, data = raw("/about")
print("Content-Type:", ct)
d = json.loads(data.decode("utf-8"))
mc = d.get("mainContent")
print("mainContent type:", type(mc).__name__)
if isinstance(mc, dict):
    print("mainContent keys:", list(mc.keys()))
    for k, v in mc.items():
        print(f"  {k}: {type(v).__name__} len={len(v) if isinstance(v,(str,list)) else v}")
elif isinstance(mc, list):
    print("mainContent list len:", len(mc))
    print("first:", json.dumps(mc[0])[:600])

# 2. encoding: find the raw bytes of the advocacy title
ct2, data2 = raw("/advocacy")
i = data2.find(b"return to office")
print("\nraw bytes around title:", data2[i-60:i+30])
# does the response declare utf-8 and do we decode fine?
txt = data2.decode("utf-8")
j = txt.find("return to office")
print("decoded utf-8:", txt[j-60:j+30])
print("codepoints:", [hex(ord(c)) for c in txt[j-30:j+10]])

# 3. events collection pagination structure
ct3, data3 = raw("/events")
d3 = json.loads(data3.decode("utf-8"))
print("\nevents upcoming type:", type(d3.get("upcoming")).__name__, len(d3.get("upcoming") or []))
print("events past type:", type(d3.get("past")).__name__, len(d3.get("past") or []))
up = d3.get("upcoming") or []
if up:
    print("upcoming[0] keys:", list(up[0].keys())[:20])
    print("upcoming[0] title:", up[0].get("title"), "startDate:", up[0].get("startDate"))
print("pagination:", d3.get("pagination"))

# 4. paginate to get all events
offset = None
count = 0
all_ev = []
for _ in range(12):
    path = "/events" + (f"?offset={offset}" if offset else "")
    _, dd = raw(path)
    j = json.loads(dd.decode("utf-8"))
    for key in ("upcoming", "past"):
        for it in (j.get(key) or []):
            all_ev.append((it.get("urlId"), it.get("title"), it.get("startDate"), key))
    pag = j.get("pagination") or {}
    count += 1
    if pag.get("nextPage") and pag.get("nextPageOffset"):
        offset = pag["nextPageOffset"]
    else:
        break
print(f"\npaginated through {count} pages, collected {len(all_ev)} event entries")
seen = {}
for u, t, s, k in all_ev:
    seen.setdefault(u, (t, s, k))
print("unique urlIds:", len(seen))
future = [v for v in seen.values() if v[1] and v[1] > 1780000000000]
print("with startDate in 2026+:", len(future))
