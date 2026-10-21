import json, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe/1.0)"}
SITE = "https://www.centretowncitizens.ca"

def get(path):
    url = f"{SITE}{path}?format=json-pretty"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def shape(obj, depth=0, maxdepth=2):
    if depth > maxdepth:
        return "..."
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                if isinstance(v, list):
                    out[k] = f"[list:{len(v)}]"
                else:
                    out[k] = shape(v, depth + 1, maxdepth)
            elif isinstance(v, str):
                out[k] = f"str:{len(v)}"
            else:
                out[k] = v
        return out
    if isinstance(obj, list):
        return f"[list:{len(obj)}]"
    return type(obj).__name__

for path in ["/news", "/advocacy", "/events", "/events/mayoraldebate2026", "/about", "/contact", "/get-involved/donate"]:
    print("=" * 70)
    print(path)
    try:
        d = get(path)
    except Exception as e:
        print("  ERR", e)
        continue
    print("TOP:", list(d.keys()))
    if "collection" in d:
        c = d["collection"]
        print("  collection keys:", list(c.keys()))
        print("  collection.title:", c.get("title"))
        print("  collection.type:", c.get("type"), c.get("typeName"))
        print("  collection.itemCount:", c.get("itemCount"))
        print("  collection.body len:", len(c.get("body") or ""))
        print("  collection.items:", type(c.get("items")).__name__, len(c.get("items") or []) if isinstance(c.get("items"), list) else "")
    if "item" in d:
        it = d["item"]
        print("  item keys:", list(it.keys())[:25])
        print("  item.title:", it.get("title"), "urlId:", it.get("urlId"))
        print("  item.body len:", len(it.get("body") or ""))
        print("  item.categories:", it.get("categories"))
        print("  item.startDate:", it.get("startDate"))
    if "items" in d:
        print("  items:", type(d["items"]).__name__, len(d["items"]) if isinstance(d["items"], list) else "")
        if isinstance(d["items"], list) and d["items"]:
            print("   item0 keys:", list(d["items"][0].keys())[:25])
            print("   item0.title:", d["items"][0].get("title"))
            print("   item0.body len:", len(d["items"][0].get("body") or ""))
            print("   item0.categories:", d["items"][0].get("categories"))
    if "pagination" in d:
        print("  pagination:", d["pagination"])
