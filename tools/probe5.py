import json, urllib.request, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe5/1.0)"}
SITE = "https://www.centretowncitizens.ca"

def get_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")

html = get_text(SITE + "/about")

# Locate the page content container. Squarespace 7.1 marks it with
# data-content-entity-id or a page-specific section id.
print("=== candidate content containers in rendered /about ===")
for pat in [r'<div[^>]*id="page-[a-f0-9]+"[^>]*>', r'<section[^>]*data-content-entity-id[^>]*>',
            r'<div[^>]*class="[^"]*sqs-block-container[^"]*"[^>]*>', r'<div[^>]*class="[^"]*page-content[^"]*"[^>]*>']:
    ms = re.findall(pat, html)
    print(f"{pat[:52]:54} {len(ms)}")
    for m in ms[:3]:
        print("      ", m[:160])

# Which blocks sit inside the page div?
m = re.search(r'<div[^>]*id="page-[a-f0-9]+"[^>]*>', html)
if m:
    start = m.end()
    seg = html[start:start+6000]
    print("\n=== first 6000 chars inside the page div (tags collapsed) ===")
    t = re.sub(r"(?s)<(script|style).*?</\1>", " ", seg)
    t = re.sub(r"<[^>]+>", " ", t)
    print(re.sub(r"\s+", " ", t)[:800])

# Count sqs-block types inside that page div
if m:
    seg = html[m.end():m.end()+20000]
    types = re.findall(r'data-sqsp-block="([^"]+)"', seg)
    print("\n=== block types inside page div ===")
    from collections import Counter
    print(Counter(types))
    print("\n=== sqs-html-content chunks ===")
    chunks = re.findall(r'(?s)<div class="sqs-html-content"[^>]*>(.*?)</div>\s*(?=<)', seg)
    print("count:", len(chunks))
    for c in chunks[:4]:
        t = re.sub(r"<[^>]+>", " ", c)
        print("   ", re.sub(r"\s+", " ", t)[:300])
