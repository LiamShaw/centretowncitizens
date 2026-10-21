#!/usr/bin/env python3
"""Verify the redirect map covers every URL the old site published.

Checks three things:
  1. every URL in the live sitemap has a redirect,
  2. every redirect target is a page that was actually built,
  3. no redirect points at itself.

Usage:
    python tools/check_coverage.py [--site https://www.centretowncitizens.ca]
                                   [--public public]
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote, unquote

UA = {"User-Agent": "Mozilla/5.0 (compatible; coverage-check/1.0)"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", default="https://www.centretowncitizens.ca")
    parser.add_argument("--public", default="public")
    parser.add_argument("--redirects", default="public/_redirects")
    args = parser.parse_args()

    site = args.site.rstrip("/")
    public = Path(args.public)

    xml = urllib.request.urlopen(
        urllib.request.Request(f"{site}/sitemap.xml", headers=UA), timeout=45
    ).read().decode("utf-8", "replace")
    live = {quote(u.replace(site, ""), safe="/") for u in re.findall(r"<loc>([^<]+)</loc>", xml)}

    redirects: dict[str, str] = {}
    for line in Path(args.redirects).read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split(None, 2)
        if len(parts) >= 2:
            redirects[parts[0]] = parts[1]

    problems = 0

    missing = sorted(live - set(redirects))
    print(f"live sitemap URLs: {len(live)}")
    print(f"redirect sources:  {len(redirects)}")
    if missing:
        problems += len(missing)
        print(f"URLs with no redirect: {len(missing)}")
        for m in missing:
            print(f"   MISSING: {m}")
    else:
        print("every live URL has a redirect")

    bad_targets = []
    for source, target in redirects.items():
        path = unquote(target.split("?")[0]).lstrip("/")
        if not (public / path / "index.html").exists():
            bad_targets.append((source, target))
    if bad_targets:
        problems += len(bad_targets)
        print(f"redirects with no built page: {len(bad_targets)}")
        for s, t in bad_targets[:20]:
            print(f"   {s}  ->  {t}")
    else:
        print("every redirect target exists")

    self_redirects = [s for s, t in redirects.items() if unquote(s) == unquote(t)]
    if self_redirects:
        problems += len(self_redirects)
        print(f"self redirects: {len(self_redirects)}")
        for s in self_redirects:
            print(f"   {s}")

    if problems:
        print(f"\nFAILED with {problems} problems")
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
