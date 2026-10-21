import urllib.request, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = {"User-Agent": "Mozilla/5.0 (compatible; probe8/1.0)"}
SITE = "https://www.centretowncitizens.ca"


def get_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


html = get_text(SITE + "/about")
i = html.find("founded in")
print("=== 2500 chars of markup around 'founded in' ===")
print(html[max(0, i - 2200):i + 300])
