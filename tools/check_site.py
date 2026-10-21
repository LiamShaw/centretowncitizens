#!/usr/bin/env python3
"""Crawl the built site and report broken internal links and missing images.

Usage:
    python tools/check_site.py [--base http://127.0.0.1:8811] [--public public]
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (compatible; site-check/1.0)"}

# The built HTML is minified, so attribute quotes may be absent.
HREF_RE = re.compile(r'href=(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))', re.IGNORECASE)
SRC_RE = re.compile(r'src=(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))', re.IGNORECASE)


def attrs(pattern: re.Pattern, body: str) -> list[str]:
    out = []
    for m in pattern.finditer(body):
        value = m.group(1) or m.group(2) or m.group(3) or ""
        if value:
            out.append(value)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8811")
    parser.add_argument("--public", default="public")
    parser.add_argument("--max-pages", type=int, default=400)
    args = parser.parse_args()

    base = args.base.rstrip("/")
    public = Path(args.public)

    seen: set[str] = set()
    queue = deque(["/"])
    broken_links: dict[str, set[str]] = {}
    broken_images: dict[str, set[str]] = {}
    checked = 0

    while queue and checked < args.max_pages:
        path = queue.popleft()
        if path in seen:
            continue
        seen.add(path)
        url = base + urllib.parse.quote(path)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                body = r.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            broken_links.setdefault(path, set()).add(f"<page failed: {exc}>")
            continue
        checked += 1

        for href in attrs(HREF_RE, body):
            if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "#")):
                continue
            target = urllib.parse.urlparse(href)
            clean = target.path or "/"
            if not clean.startswith("/"):
                continue
            # Check the target file exists in the built output.
            base_path = urllib.parse.urlparse(clean).path
            candidate = public / base_path.lstrip("/")
            if base_path.endswith("/"):
                candidate = candidate / "index.html"
            if not candidate.exists():
                broken_links.setdefault(path, set()).add(href)
                continue
            # Follow the link, ignoring the query string so that category
            # filters do not create separate crawl targets.
            if base_path.endswith("/"):
                queue.append(base_path)

        for src in attrs(SRC_RE, body):
            if src.startswith(("http://", "https://", "data:", "//")):
                continue
            clean = urllib.parse.urlparse(src).path
            if not clean.startswith("/"):
                continue
            candidate = public / clean.lstrip("/")
            if not candidate.exists():
                broken_images.setdefault(path, set()).add(src)

    print(f"pages crawled: {checked}")
    print(f"broken internal links: {len(broken_links)}")
    for page, links in list(broken_links.items())[:25]:
        print(f"   {page}")
        for l in sorted(links)[:8]:
            print(f"       {l}")
    print(f"\npages with missing images: {len(broken_images)}")
    for page, imgs in list(broken_images.items())[:25]:
        print(f"   {page}")
        for i in sorted(imgs)[:8]:
            print(f"       {i}")

    if broken_links or broken_images:
        return 1
    print("\nOK: no broken internal links or missing images")
    return 0


if __name__ == "__main__":
    sys.exit(main())
