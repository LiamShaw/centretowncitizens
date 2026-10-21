import json, urllib.request, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe3/1.0)"}
SITE = "https://www.centretowncitizens.ca"

def get(path_and_query):
    url = f"{SITE}{path_and_query}"
    if "?" in path_and_query:
        url += "&format=json-pretty"
    else:
        url += "?format=json-pretty"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))

# 1. events pagination with the correct separator
offset = None
all_ev = {}
pages = 0
for _ in range(15):
    q = "/events" + (f"?offset={offset}" if offset else "")
    d = get(q)
    for key in ("upcoming", "past"):
        for it in (d.get(key) or []):
            all_ev[it.get("urlId")] = {
                "title": it.get("title"),
                "startDate": it.get("startDate"),
                "endDate": it.get("endDate"),
                "bucket": key,
                "bodyLen": len(it.get("body") or ""),
                "assetUrl": it.get("assetUrl"),
                "categories": it.get("categories"),
                "location": it.get("location"),
                "excerpt": it.get("excerpt"),
                "author": (it.get("author") or {}).get("displayName"),
                "publishOn": it.get("publishOn"),
                "updatedOn": it.get("updatedOn"),
            }
    pages += 1
    pag = d.get("pagination") or {}
    if pag.get("nextPage") and pag.get("nextPageOffset"):
        offset = pag["nextPageOffset"]
    else:
        break
print(f"events: {pages} pages, {len(all_ev)} unique urlIds")
buckets = {}
for v in all_ev.values():
    buckets[v["bucket"]] = buckets.get(v["bucket"], 0) + 1
print("  buckets:", buckets)
print("  with body:", sum(1 for v in all_ev.values() if v["bodyLen"] > 0))
print("  with assetUrl:", sum(1 for v in all_ev.values() if v["assetUrl"]))
fut = [k for k, v in all_ev.items() if v["startDate"] and v["startDate"] > 1789000000000]
print("  starting after 2026-09-01:", len(fut), fut[:10])

# 2. static pages: mainContent
for p in ["/about", "/contact", "/get-involved/donate", "/get-involved/membership",
          "/heritage-working-group", "/ccacommittees", "/board-members-1", "/newsletter",
          "/editorial-guidelines", "/get-involved", "/cca-in-the-news-update", "/sepaw"]:
    try:
        d = get(p)
        c = d.get("collection") or {}
        mc = d.get("mainContent")
        items = d.get("items")
        print(f"{p:34} type={c.get('typeName'):18} mainContent_len={len(mc or '') if isinstance(mc,str) else 'n/a'} items={len(items) if isinstance(items,list) else 0}")
        if isinstance(mc, str) and mc:
            print("      snippet:", mc[:150].replace("\n", " "))
    except Exception as e:
        print(f"{p:34} ERR {e}")

# 3. committee pages that have their own blog collection
for p in ["/heritage-working-group", "/sepaw", "/seniors-committee", "/planning-committee"]:
    d = get(p)
    items = d.get("items") or []
    print(f"\n{p}: {len(items)} collection items")
    for it in items[:5]:
        print(f"   {it.get('title')!r} urlId={it.get('urlId')} bodyLen={len(it.get('body') or '')}")
