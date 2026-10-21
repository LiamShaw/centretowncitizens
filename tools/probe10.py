import urllib.request, re, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe10/1.0)"}
SITE = "https://www.centretowncitizens.ca"


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def page_section_chunks(html, page_id):
    """Extract sqs-html-content chunks from the page's own section."""
    marker = f'id="page-section-{page_id}"'
    m = re.search(r'<div[^>]*' + re.escape(marker) + r'[^>]*>', html)
    if not m:
        return None
    start = m.end()
    depth = 1
    pos = start
    tag_re = re.compile(r"<(/?)div\b[^>]*>", re.IGNORECASE)
    end = len(html)
    while depth > 0:
        tm = tag_re.search(html, pos)
        if not tm:
            break
        depth += -1 if tm.group(1) else 1
        pos = tm.end()
        if depth == 0:
            end = tm.start()
    seg = html[start:end]
    chunks = re.findall(r'(?s)<div class="sqs-html-content"[^>]*>(.*?)</div>(?=\s*(?:</div>|<div|</section|$))', seg)
    return chunks, len(seg)


def clean(chunk):
    c = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", "", chunk)
    c = re.sub(r"(?s)<style[^>]*>.*?</style>", "", c)
    return c


for path in ["/about", "/contact", "/get-involved/donate", "/get-involved/membership",
             "/editorial-guidelines", "/newsletter", "/ccacommittees", "/board-members-1",
             "/get-involved", "/cca-in-the-news-update", "/heritage-working-group",
             "/sepaw", "/seniors-committee", "/planning-committee", "/treesandgreenspace",
             "/housingaffordability", "/transportation", "/climatechange"]:
    try:
        j = json.loads(get(f"{SITE}{path}?format=json-pretty"))
    except Exception as e:
        print(f"{path}: JSON ERR {e}")
        continue
    mc = j.get("mainContent") or ""
    pid = re.search(r'id="page-([a-f0-9]+)"', mc)
    pid = pid.group(1) if pid else None
    html = get(SITE + path)
    res = page_section_chunks(html, pid) if pid else None
    if res is None:
        print(f"{path:32} page_id={pid} NO SECTION MATCH")
        continue
    chunks, seglen = res
    texts = []
    for c in chunks:
        t = re.sub(r"<[^>]+>", " ", clean(c))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            texts.append(t)
    print(f"{path:32} page_id={pid} seg={seglen:6} chunks={len(chunks):2} withtext={len(texts)}")
    for t in texts[:2]:
        print(f"      > {t[:120]}")
