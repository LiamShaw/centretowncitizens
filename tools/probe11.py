import urllib.request, re, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe11/1.0)"}
SITE = "https://www.centretowncitizens.ca"


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def inner_of_div(html, marker):
    """Return inner HTML of the div whose attributes contain marker."""
    m = re.search(r'<div[^>]*' + re.escape(marker) + r'[^>]*>', html)
    if not m:
        return None
    start = m.end()
    depth = 1
    pos = start
    tag_re = re.compile(r"<(/?)div\b[^>]*>", re.IGNORECASE)
    while depth > 0:
        tm = tag_re.search(html, pos)
        if not tm:
            break
        depth += -1 if tm.group(1) else 1
        pos = tm.end()
    return html[start:pos]


html = get(SITE + "/about")
for marker in ['id="page-regions"', 'id="page-section-5fa19454f3acb21d88af5873"']:
    seg = inner_of_div(html, marker)
    print(f"{marker}: {'FOUND len=' + str(len(seg)) if seg else 'not found'}")
    if seg:
        print("   sqs-html-content count:", len(re.findall(r'class="sqs-html-content"', seg)))
        from collections import Counter
        print("   blocks:", dict(Counter(re.findall(r'data-sqsp-block="([^"]+)"', seg))))
        chunks = re.findall(r'(?s)<div class="sqs-html-content"[^>]*>(.*?)</div>', seg)
        for c in chunks:
            c2 = re.sub(r"(?s)<style[^>]*>.*?</style>", "", c)
            t = re.sub(r"<[^>]+>", " ", c2)
            t = re.sub(r"\s+", " ", t).strip()
            print("   >", t[:200])
print("\n--- all page-region-ish ids on /about ---")
print(sorted(set(re.findall(r'id="(page[^"]*)"', html))))
print("\n--- region ids ---")
print(re.findall(r'data-region-id="([a-f0-9]+)" data-region-source="([^"]*)"', html))
