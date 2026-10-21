import urllib.request, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA={"User-Agent":"Mozilla/5.0 (compatible; probe6/1.0)"}
SITE="https://www.centretowncitizens.ca"
req=urllib.request.Request(SITE+"/about",headers=UA)
html=urllib.request.urlopen(req,timeout=45).read().decode("utf-8","replace")
print("len:",len(html))
print("\n--- ids containing 'page' ---")
print(sorted(set(re.findall(r'id="(page[^"]*)"',html)))[:20])
print("\n--- all sqs-block types on page ---")
from collections import Counter
print(Counter(re.findall(r'data-sqsp-block="([^"]+)"',html)))
print("\n--- sqs-html-content blocks ---")
chunks=re.findall(r'(?s)<div class="sqs-html-content"[^>]*>(.*?)</div>',html)
print("count:",len(chunks))
for c in chunks[:8]:
    t=re.sub(r"<[^>]+>"," ",c); t=re.sub(r"\s+"," ",t).strip()
    if t: print("   >",t[:220])
print("\n--- looking for the actual About body text ---")
for needle in ["Centretown Community Association is","Welcome to the CCA","founded in","1963"]:
    i=html.find(needle); print(f"  {needle!r}: {'at '+str(i) if i>0 else 'NOT FOUND'}")
print("\n--- section tags ---")
print(re.findall(r"<section[^>]{0,200}>",html)[:12])
