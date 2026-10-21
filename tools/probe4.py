import json, urllib.request, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe4/1.0)"}
SITE = "https://www.centretowncitizens.ca"

def get_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")

# What does the rendered About page actually contain?
html = get_text(SITE + "/about")
text = re.sub(r"(?s)<(script|style).*?</\1>", " ", html)
text = re.sub(r"<[^>]+>", " ", text)
text = re.sub(r"\s+", " ", text)
i = text.find("About CCA")
print("RENDERED /about (around 'About CCA'):")
print(" ", text[i:i+400] if i >= 0 else text[:400])

# Search the JSON for that same text
j = get_text(SITE + "/about?format=json-pretty")
print("\nJSON length:", len(j))
for needle in ["About CCA", "Centretown Community Association", "ccca@centretowncitizens.ca"]:
    print(f"  contains {needle!r}: {needle in j}")

# Find the longest string values in the JSON, which is where content must be
d = json.loads(j)
strings = []

def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, f"{path}.{k}")
    elif isinstance(o, list):
        for idx, v in enumerate(o[:50]):
            walk(v, f"{path}[{idx}]")
    elif isinstance(o, str) and len(o) > 120:
        strings.append((len(o), path, o[:160]))

walk(d)
strings.sort(reverse=True)
print("\nLongest string values in /about JSON:")
for ln, path, snip in strings[:12]:
    print(f"  {ln:7} {path}")
    print(f"          {snip!r}")

# Try the collection-style URL: /about is a page; try the 7.1 blocks endpoint
for variant in ["/about?format=json", "/about?format=json-pretty&_escaped_fragment_="]:
    try:
        t = get_text(SITE + variant)
        print(f"\n{variant}: len={len(t)} hasAboutCCA={'About CCA' in t}")
    except Exception as e:
        print(f"\n{variant}: ERR {e}")
