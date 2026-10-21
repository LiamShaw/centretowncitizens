import urllib.request, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe9/1.0)"}
SITE = "https://www.centretowncitizens.ca"


def get_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


for path in ["/about", "/contact", "/get-involved/donate", "/get-involved/membership",
             "/editorial-guidelines", "/newsletter", "/ccacommittees", "/board-members-1",
             "/get-involved", "/cca-in-the-news-update", "/heritage-working-group"]:
    html = get_text(SITE + path)
    fpos = html.find("<footer")
    body = html[:fpos] if fpos > 0 else html
    chunks = re.findall(r'(?s)<div class="sqs-html-content"[^>]*>(.*?)</div>\s*(?=<div|<footer|$)', body)
    from collections import Counter
    types = Counter(re.findall(r'data-sqsp-block="([^"]+)"', body))
    print(f"{path:32} footer@{fpos:7} sqs-html-content={len(chunks):2} blocks={dict(types)}")
    for c in chunks:
        t = re.sub(r"<[^>]+>", " ", c)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            print(f"      > {t[:150]}")
    print()
