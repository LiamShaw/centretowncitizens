import urllib.request, re, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe12/1.0)"}
SITE = "https://www.centretowncitizens.ca"


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def balanced_div(html, open_end):
    """Given html and the index just after an opening <div ...>, return inner html and end index."""
    depth = 1
    pos = open_end
    tag_re = re.compile(r"<(/?)div\b[^>]*>", re.IGNORECASE)
    while depth > 0:
        tm = tag_re.search(html, pos)
        if not tm:
            return html[open_end:], len(html)
        depth += -1 if tm.group(1) else 1
        pos = tm.end()
        if depth == 0:
            return html[open_end:tm.start()], tm.start()
    return html[open_end:], pos


def extract_blocks(html):
    """Return ordered list of (block_type, inner_html) for content blocks."""
    fpos = html.find("<footer")
    body = html[:fpos] if fpos > 0 else html
    out = []
    pat = re.compile(r'<div[^>]*class="[^"]*sqs-block\s[^"]*"[^>]*data-sqsp-block="([^"]+)"[^>]*>', re.I)
    for m in pat.finditer(body):
        btype = m.group(1)
        inner, _ = balanced_div(body, m.end())
        out.append((btype, inner))
    return out


def text_of(inner):
    c = re.sub(r"(?s)<style[^>]*>.*?</style>", "", inner)
    c = re.sub(r"(?s)<script[^>]*>.*?</script>", "", c)
    t = re.sub(r"<[^>]+>", " ", c)
    return re.sub(r"\s+", " ", t).strip()


for path in ["/about", "/contact", "/get-involved/donate", "/editorial-guidelines", "/newsletter", "/heritage-working-group"]:
    html = get(SITE + path)
    blocks = extract_blocks(html)
    print(f"=== {path}: {len(blocks)} blocks ===")
    for btype, inner in blocks:
        t = text_of(inner)
        if not t and btype != "image":
            continue
        imgs = re.findall(r'<img[^>]*src="([^"]+)"', inner)
        print(f"  [{btype:14}] {t[:130]!r} imgs={len(imgs)}")
    print()
