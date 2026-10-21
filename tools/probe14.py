import urllib.request, json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA={"User-Agent":"Mozilla/5.0 (compatible; probe14/1.0)"}
SITE="https://www.centretowncitizens.ca"
def j(u):
    return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=45).read().decode("utf-8","replace"))

# The clone family that clearly exists in the sitemap
family = ["elgin-street-market-s4tms",
          "elgin-street-market-s4tms-65grg",
          "elgin-street-market-s4tms-65grg-nwry5-hse5s-cw5n7-sdn8m",
          "yoga-in-the-park-gcl7l",
          "yoga-in-the-park-gcl7l-hjxzp"]
for f in family:
    d=j(f"{SITE}/events/{f}?format=json-pretty")
    it=d.get("item") or {}
    print(f"{f[:50]:52}")
    print(f"   title={it.get('title')!r}")
    print(f"   startDate={it.get('startDate')}  publishOn={it.get('publishOn')}")
    print(f"   bodyLen={len(it.get('body') or '')}  assetUrl={ (it.get('assetUrl') or '')[-40:] }")
