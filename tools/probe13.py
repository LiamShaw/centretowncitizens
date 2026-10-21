import urllib.request, json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA={"User-Agent":"Mozilla/5.0 (compatible; probe13/1.0)"}
SITE="https://www.centretowncitizens.ca"
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=45).read().decode("utf-8","replace")

for p in ["/events/yoga-in-the-park","/events/9z7f9ipcyz90dbyg8wpf0bub8oy894","/events/committee-meeting-planning","/events/b3cxdm8hgqw0rigx9201hwfuwb85ts","/events/mayoraldebate2026"]:
    try:
        d=json.loads(get(f"{SITE}{p}?format=json-pretty"))
        it=d.get("item")
        print(f"{p}")
        print(f"   has item: {it is not None}")
        if it:
            print(f"   title={it.get('title')!r} urlId={it.get('urlId')!r}")
            print(f"   startDate={it.get('startDate')} workflowState={it.get('workflowState')}")
            print(f"   bodyLen={len(it.get('body') or '')} assetUrl={'yes' if it.get('assetUrl') else 'no'}")
            print(f"   fullUrl={it.get('fullUrl')}")
    except Exception as e:
        print(f"{p}  ERR {e}")
