import urllib.request, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe7/1.0)"}
SITE = "https://www.centretowncitizens.ca"


def get_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def extract_page_section(html):
    """Return the inner HTML of the page content region."""
    # Find the opening div for the page section and walk to its match.
    m = re.search(r'<div[^>]*id="page-section-[a-f0-9]+"[^>]*>', html)
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
    return html[start:pos - len(tm.group(0))] if depth == 0 else html[start:pos]


for path in ["/about", "/contact", "/get-involved/donate", "/editorial-guidelines", "/newsletter"]:
    html = get_text(SITE + path)
    seg = extract_page_section(html)
    if seg is None:
        print(f"{path}: NO SECTION")
        continue
    from collections import Counter
    types = Counter(re.findall(r'data-sqsp-block="([^"]+)"', seg))
    text = re.sub(r"(?s)<(script|style).*?</\1>", " ", seg)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    print(f"{path}")
    print(f"   section len={len(seg)} blocks={dict(types)}")
    print(f"   text: {text[:260]}")
    print()
