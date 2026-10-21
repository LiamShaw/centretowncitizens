#!/usr/bin/env python3
"""Export the Centretown CCA Squarespace 7.1 site into Hugo content files.

Squarespace 7.1 offers no XML export. Its public JSON endpoint does return
structured content for blog collections and events: appending ?format=json-pretty
to a collection URL yields every item with its body HTML, categories, publish
dates and authors. Static pages are the exception; their bodies are not in the
JSON, so those are read from the rendered HTML instead.

Usage:
    python tools/export_squarespace.py [--site https://www.centretowncitizens.ca]
                                      [--out .] [--no-images] [--dry-run]

Outputs:
    content/<section>/<slug>.md   Hugo content with YAML front matter
    data/redirects.yaml            old Squarespace path -> new Hugo path
    data-raw/redirects.csv         the same map as CSV, for the check scripts
    data-raw/inventory.csv         every source URL, its destination and status
    static/images/                 downloaded images, renamed by content token
    static/files/                  attachments the old site served, such as PDFs
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

USER_AGENT = "Mozilla/5.0 (compatible; CCA-site-migration/1.0)"

# Squarespace test scaffolding and superseded copies of the home page.
JUNK_PAGES = {
    "/atletico",
    "/blog_test",
    "/homeold",
    "/home-1-1",
    "/test-1",
    "/success",
    "/neighbourwoods",
    "/home",
}

# Blog collections, and the Hugo section each becomes. Committee pages are
# themselves blog collections on Squarespace, and also carry their own
# landing text (chair, remit), which is exported separately.
COLLECTIONS = {
    "/news": "news",
    "/advocacy": "advocacy",
}

# Committee blog collections: (Squarespace path, Hugo section).
COMMITTEE_COLLECTIONS = {
    "/heritage-working-group": "committees/heritage",
    "/housingaffordability": "committees/housing",
    "/planning-committee": "committees/planning",
    "/transportation": "committees/transportation",
    "/treesandgreenspace": "committees/trees",
    "/sepaw": "committees/sepaw",
    "/seniors-committee": "committees/seniors",
}

# The committee page names, as the old site's committees page lists them.
COMMITTEE_TITLES = {
    "committees/heritage": "Heritage Working Group",
    "committees/housing": "Housing Affordability Working Group",
    "committees/planning": "Planning Committee",
    "committees/transportation": "Transportation Committee",
    "committees/trees": "Trees and Greenspace Committee",
    "committees/sepaw": "Safety, Emergency Preparedness and Wellness (SEPAW)",
    "committees/seniors": "Seniors Committee",
}

# Static pages, and the Hugo page each becomes.
STATIC_PAGES = {
    "/about": "about",
    "/board-members-1": "board",
    "/editorial-guidelines": "editorial",
    "/contact": "contact",
    "/newsletter": "newsletter",
    "/cca-in-the-news-update": "media-mentions",
    "/ccacommittees": "committees",
    "/get-involved": "get-involved",
    "/get-involved/donate": "donate",
    "/get-involved/membership": "membership",
    "/get-involved/volunteer": "volunteer",
    "/get-involved/sponsorship": "sponsorship",
    "/climatechange": "climate-change",
    "/climatechange/cafes-climate-resiliency-community-dialogue-report": (
        "climate-change-dialogue-report"
    ),
}

# Squarespace category label -> the label the new site uses.
ADVOCACY_CATEGORIES = {
    "CCA": "CCA",
    "SEPAW": "SEPAW",
    "Planning": "Planning",
    "Transportation": "Transportation",
    "Green": "Greenspace & Sustainability",
    "HAWG": "Housing Affordability",
}

# The event collection page, which is paginated.
EVENTS_PATH = "/events"

# Squarespace allowed the same event to be republished many times, each copy
# getting a random suffix. The base slug is the canonical event.
CLONE_SUFFIX = re.compile(r"(?:-[a-z0-9]{5})+$")

IMAGE_DIR = Path("static/images")

# Maps a Squarespace path to the path it now lives at. Filled in as the
# export discovers the mapping, so that links inside page bodies point at the
# new site rather than at URLs that only exist on Squarespace.
LINK_MAP: dict[str, str] = {}

# Paths that Squarespace served as files rather than pages.
STATIC_FILE_PREFIX = "/s/"

# Files copied across from the old site, keyed by their old path.
STATIC_FILES: dict[str, str] = {}

# Files the old site served directly, and the name they keep in the new one.
STATIC_FILE_DOWNLOADS = {
    "/s/Centretown-Community-Association-Bylaws-current-to-Jan-30-2024.pdf": (
        "Centretown-Community-Association-Bylaws-current-to-Jan-30-2024.pdf"
    ),
}

# Links to pages that Squarespace never published, so they were already
# broken on the old site. Each is pointed at the closest page that does
# exist on the new site.
BROKEN_LINK_FIXES = {
    "/join-the-board": "/membership/",
}


def rewrite_internal_link(href: str) -> str:
    """Point an internal link at the new site's URL for that page."""
    if not href.startswith("/"):
        return href
    path = href.split("?")[0].split("#")[0]
    if not path or path == "/":
        return href
    if path.startswith(STATIC_FILE_PREFIX):
        # A file on Squarespace, such as a letter PDF. These are copied into
        # the new site; the link is rewritten once the copy exists.
        return href
    if path in LINK_MAP:
        return LINK_MAP[path] + href[len(path):]
    return href


def fetch(url: str, timeout: int = 45) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_json(path: str, site: str, retries: int = 3) -> dict:
    sep = "&" if "?" in path else "?"
    url = f"{site}{path}{sep}format=json-pretty"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            return json.loads(fetch(url))
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def get_sitemap(site: str) -> list[str]:
    xml = fetch(f"{site}/sitemap.xml")
    return re.findall(r"<loc>([^<]+)</loc>", xml)


# --------------------------------------------------------------------------
# HTML handling
# --------------------------------------------------------------------------


def balanced_div(html: str, open_end: int) -> tuple[str, int]:
    """Return the inner HTML of a div, given the index just after its tag."""
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


BLOCK_RE = re.compile(
    r'<div[^>]*class="[^"]*sqs-block\s[^"]*"[^>]*data-sqsp-block="([^"]+)"[^>]*>',
    re.IGNORECASE,
)


def content_blocks(html: str) -> list[tuple[str, str]]:
    """Ordered (block_type, inner_html) for the blocks in a page's body.

    The footer is excluded: it holds the sitewide newsletter block and
    contact details, which the new site renders from its own templates.
    """
    fpos = html.find("<footer")
    body = html[:fpos] if fpos > 0 else html
    out: list[tuple[str, str]] = []
    for m in BLOCK_RE.finditer(body):
        inner, _ = balanced_div(body, m.end())
        out.append((m.group(1), inner))
    return out


def strip_noise(text: str) -> str:
    text = re.sub(r"(?s)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?s)<script[^>]*>.*?</script>", " ", text)
    return text


def decode_entities(text: str) -> str:
    for entity, char in (
        ("&nbsp;", " "),
        ("&amp;", "&"),
        ("&quot;", '"'),
        ("&#39;", "'"),
        ("&rsquo;", "'"),
        ("&lsquo;", "'"),
        ("&ldquo;", '"'),
        ("&rdquo;", '"'),
        ("&hellip;", "..."),
        ("&mdash;", " - "),
        ("&ndash;", " - "),
        ("&middot;", "-"),
        ("&times;", "x"),
    ):
        text = text.replace(entity, char)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    return text


def plain_text(html: str) -> str:
    text = strip_noise(html)
    text = re.sub(r"<[^>]+>", " ", text)
    text = decode_entities(text)
    return re.sub(r"\s+", " ", text).strip()


class ImagePool:
    """Downloads each distinct Squarespace image once and records its new path."""

    def __init__(self, base: str) -> None:
        self.base = base
        self.images: dict[str, str] = {}
        self.failed: dict[str, str] = {}

    def register(self, url: str) -> str | None:
        if not url:
            return None
        base = url.split("?")[0]
        if base in self.images:
            return self.images[base]
        if base in self.failed:
            return None
        name = self.filename_for(base)
        target = self.base / "static" / "images" / name
        try:
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(fetch_bytes(base))
            self.images[base] = f"/images/{name}"
        except Exception as exc:  # noqa: BLE001
            self.failed[base] = str(exc)
            return None
        return self.images[base]

    @staticmethod
    def filename_for(url: str) -> str:
        """Derive a stable local name from the Squarespace asset URL.

        Squarespace image URLs embed a unique per-asset token, which makes a
        better identity than the filename, since filenames repeat across the
        site.
        """
        path = urllib.parse.urlparse(url).path
        parts = [p for p in path.split("/") if p]
        stem = parts[-1] if parts else "image"
        token = ""
        for part in parts:
            if re.search(r"\d{10,}-", part):
                token = part
                break
        suffix = Path(stem).suffix.lower() or ".jpg"
        stem_base = re.sub(r"[^A-Za-z0-9._-]", "-", Path(stem).stem)[:50] or "image"
        if token:
            return f"{stem_base}-{token.split('-')[0]}{suffix}"
        return f"{stem_base}{suffix}"


def html_to_markdown(html: str, pool: ImagePool, site: str) -> str:
    """Convert a Squarespace block's HTML into Markdown."""
    if not html:
        return ""
    html = strip_noise(html)

    # Images become local references.
    def img_sub(match: re.Match) -> str:
        src = match.group(1)
        alt = match.group(2) or ""
        local = pool.register(src)
        return f"![{alt}]({local})" if local else ""

    html = re.sub(
        r'<img[^>]*src="([^"]+)"[^>]*?(?:alt="([^"]*)")?[^>]*/?>',
        img_sub,
        html,
        flags=re.IGNORECASE,
    )

    # Headings.
    for level in range(1, 7):
        html = re.sub(
            rf"(?is)<h{level}[^>]*>(.*?)</h{level}>",
            lambda m, lvl=level: "\n\n" + "#" * lvl + " " + plain_text(m.group(1)) + "\n\n",
            html,
        )

    # Lists.
    html = re.sub(r"(?is)<li[^>]*>(.*?)</li>", lambda m: "\n- " + plain_text(m.group(1)), html)
    html = re.sub(r"(?is)</?(ul|ol)[^>]*>", "\n", html)

    # Links.
    def link_sub(match: re.Match) -> str:
        href = match.group(1)
        label = plain_text(match.group(2))
        if not label:
            return ""
        if href.startswith(site):
            href = href[len(site):] or "/"
        href = rewrite_internal_link(href)
        return f"[{label}]({href})"

    html = re.sub(r'(?is)<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', link_sub, html)

    # Paragraphs and line breaks.
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</p>", "\n\n", html)
    html = re.sub(r"(?is)<p[^>]*>", "", html)
    html = re.sub(r"(?is)<[^>]+>", "", html)
    html = decode_entities(html)

    html = re.sub(r"[ \t]+\n", "\n", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


# --------------------------------------------------------------------------
# Front matter helpers
# --------------------------------------------------------------------------


def yaml_escape(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def yaml_scalar(value: str) -> str:
    """Quote a YAML scalar, escaping the characters that would break it."""
    return yaml_escape(value)


def quote_path(path: str) -> str:
    """Percent-encode a path so it is safe in a redirect rule.

    A few old Squarespace URLs contain a space. Cloudflare's redirect file
    expects the percent-encoded form, which is what a browser sends.
    """
    return quote(path, safe="/:?=&#%~!$'()*+,;@")


def frontmatter(fields: list[tuple[str, object]]) -> str:
    lines = ["---"]
    for key, value in fields:
        if value is None or value == "" or value == []:
            continue
        if isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {yaml_escape(item)}")
        elif isinstance(value, int):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {yaml_escape(value)}")
    lines.append("---")
    return "\n".join(lines)


def iso_date(millis: int | None) -> str:
    if not millis:
        return ""
    return datetime.fromtimestamp(millis / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def iso_datetime(millis: int | None) -> str:
    if not millis:
        return ""
    return (
        datetime.fromtimestamp(millis / 1000, tz=timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def strip_leading_heading(body: str, title: str) -> str:
    """Remove a heading at the top of a page that repeats the page title.

    Squarespace pages usually begin with a heading block holding the page
    name. The new site renders the title itself, so leaving it in would show
    the same words twice.
    """
    lines = body.lstrip().split("\n")
    if not lines:
        return body
    first = lines[0].strip()
    if not first.startswith("#"):
        return body
    heading = first.lstrip("#").strip().rstrip(":").strip()
    if heading.lower() == title.strip().lower():
        return "\n".join(lines[1:]).lstrip()
    return body


def write_content(path: Path, fields: list[tuple[str, object]], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter(fields) + "\n\n" + body.strip() + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# Exporters
# --------------------------------------------------------------------------


def copy_static_files(site: str, out_dir: Path) -> None:
    """Copy across the files the old site served directly.

    Squarespace hosts attachments such as letter PDFs under /s/. Every such
    link found in the exported content is downloaded and the link rewritten
    to the local copy, so that nothing depends on the old account staying
    alive.
    """
    target_dir = out_dir / "static" / "files"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Collect every attachment link that appears in the exported content.
    wanted: set[str] = set()
    for md in (out_dir / "content").rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\]\((/s/[^)]+)\)", text):
            wanted.add(m.group(1))

    if not wanted:
        print("  no attachments referenced")
        return

    for path in sorted(wanted):
        name = path[len(STATIC_FILE_PREFIX):].split("?")[0]
        if not name:
            continue
        try:
            data = fetch_bytes(f"{site}{path}")
        except Exception as exc:  # noqa: BLE001
            print(f"  warning: could not fetch {path} ({exc})")
            continue
        (target_dir / name).write_bytes(data)
        STATIC_FILES[path] = f"/files/{name}"
        print(f"  {path} -> /files/{name} ({len(data):,} bytes)")

    # Rewrite the links in the content that point at them.
    rewritten = 0
    for md in (out_dir / "content").rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        original = text
        for old, new in STATIC_FILES.items():
            text = text.replace(f"]({old})", f"]({new})")
        if text != original:
            md.write_text(text, encoding="utf-8")
            rewritten += 1
    print(f"  rewrote attachment links in {rewritten} files")


def copy_favicon(site: str, out_dir: Path) -> None:
    """Copy the site icon across, so the new site is not icon-less."""
    try:
        data = fetch_bytes(f"{site}/favicon.ico")
    except Exception as exc:  # noqa: BLE001
        print(f"  warning: could not fetch favicon ({exc})")
        return
    target = out_dir / "static" / "images" / "favicon.ico"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(f"  favicon.ico ({len(data):,} bytes)")


def build_link_map(site: str, sitemap: list[str]) -> None:
    """Work out where each old Squarespace URL now lives.

    The mapping has to be complete before any page body is converted, so
    that a link to a committee page is rewritten to the new committee URL
    rather than left pointing at a path that no longer exists.
    """
    # Static pages.
    for path, slug in STATIC_PAGES.items():
        LINK_MAP[path] = f"/{slug}/"

    # Collection index pages.
    for collection_path, section in COLLECTIONS.items():
        LINK_MAP[collection_path] = f"/{section}/"
    for collection_path, section in COMMITTEE_COLLECTIONS.items():
        LINK_MAP[collection_path] = f"/{section}/"
    LINK_MAP[EVENTS_PATH] = "/events/"

    # Blog and committee posts, keyed by their Squarespace path.
    for collection_path, section in COLLECTIONS.items():
        try:
            payload = fetch_json(collection_path, site)
        except Exception:  # noqa: BLE001
            continue
        for item in payload.get("items") or []:
            slug = item.get("urlId") or ""
            if not slug or re.search(r"blog[- ]post[- ]title", slug, re.IGNORECASE):
                continue
            LINK_MAP[f"{collection_path}/{slug}"] = f"/{section}/{slug}/"

    for collection_path, section in COMMITTEE_COLLECTIONS.items():
        try:
            payload = fetch_json(collection_path, site)
        except Exception:  # noqa: BLE001
            continue
        for item in payload.get("items") or []:
            slug = item.get("urlId") or ""
            if not slug or re.search(r"blog[- ]post[- ]title", slug, re.IGNORECASE):
                continue
            LINK_MAP[f"{collection_path}/{slug}"] = f"/{section}/{slug}/"

    # Events, keyed by their Squarespace path.
    for url in sitemap:
        path = urllib.parse.urlparse(url).path
        if not path.startswith(f"{EVENTS_PATH}/"):
            continue
        url_id = path[len(EVENTS_PATH) + 1:]
        LINK_MAP[path] = f"/events/{url_id}/"

    # The advocacy category views become a filtered list on one page.
    for category in (
        "All",
        "CCA",
        "SEPAW",
        "Planning",
        "Transportation",
        "Green",
        "HAWG",
    ):
        LINK_MAP[f"/advocacy/category/{category}"] = f"/advocacy/?category={category}"

    # Links to pages that Squarespace never published, so they were already
    # broken on the old site. They are pointed at the closest page that does
    # exist rather than left as a dead link.
    LINK_MAP.update(BROKEN_LINK_FIXES)

    print(f"  {len(LINK_MAP)} paths mapped")


def export_collection(
    site: str,
    collection_path: str,
    section: str,
    out_dir: Path,
    pool: ImagePool,
    redirects: list[tuple[str, str]],
    inventory: list[dict],
) -> None:
    payload = fetch_json(collection_path, site)
    items = payload.get("items") or []
    print(f"  {collection_path}: {len(items)} items")
    for item in items:
        slug = item.get("urlId") or ""
        if not slug:
            continue
        # Squarespace left placeholder posts in the live collections, with
        # generated titles such as "Blog Post Title One". They carry no
        # content and are not worth migrating.
        if re.search(r"blog[- ]post[- ]title", slug, re.IGNORECASE):
            inventory.append(
                {
                    "source_url": f"{collection_path}/{slug}",
                    "new_url": "",
                    "kind": "placeholder",
                    "status": "dropped (placeholder post)",
                }
            )
            continue
        body = html_to_markdown(item.get("body") or "", pool, site)
        cats = [c for c in (item.get("categories") or []) if c]
        if collection_path == "/advocacy":
            labels = [
                ADVOCACY_CATEGORIES.get(c, c)
                for c in cats
                if c in ADVOCACY_CATEGORIES
            ]
        else:
            labels = [c for c in cats if c not in ADVOCACY_CATEGORIES]
        fields = [
            ("title", item.get("title") or slug),
            ("slug", slug),
            # The published path is set explicitly, so it matches the redirect
            # map exactly. Hugo would otherwise sanitise the slug, which
            # would move a page without the redirect following it.
            ("url", f"/{section}/{slug}/"),
            ("date", iso_date(item.get("publishOn"))),
            ("lastmod", iso_datetime(item.get("updatedOn"))),
            ("author", (item.get("author") or {}).get("displayName") or ""),
            ("description", plain_text(item.get("excerpt") or "")[:200]),
            ("categories", labels),
            ("legacy_url", f"{collection_path}/{slug}"),
        ]
        write_content(out_dir / "content" / section / f"{slug}.md", fields, body)
        new_path = f"/{section}/{slug}/"
        redirects.append((f"{collection_path}/{slug}", new_path))
        inventory.append(
            {
                "source_url": f"{collection_path}/{slug}",
                "new_url": new_path,
                "kind": "collection-item",
                "status": "migrated",
            }
        )


def export_events(
    site: str,
    event_paths: list[str],
    out_dir: Path,
    pool: ImagePool,
    redirects: list[tuple[str, str]],
    inventory: list[dict],
) -> dict[str, dict]:
    """Export every event, fetching each one from the sitemap.

    The paginated collection endpoint omits some events, so the sitemap is
    treated as the authoritative list and each event URL is read directly.

    Squarespace let the same event be published repeatedly, each copy getting
    a random suffix. Copies are grouped by title and start date, and the
    shortest URL in each group is kept as the canonical event; the rest
    redirect to it.
    """
    fetched: dict[str, dict] = {}
    for path in event_paths:
        url_id = path[len(EVENTS_PATH) + 1:]
        if url_id in fetched:
            continue
        try:
            payload = fetch_json(path, site)
        except Exception as exc:  # noqa: BLE001
            inventory.append(
                {"source_url": path, "new_url": "", "kind": "event", "status": f"failed: {exc}"}
            )
            continue
        item = payload.get("item")
        if not item:
            inventory.append(
                {"source_url": path, "new_url": "", "kind": "event", "status": "no item returned"}
            )
            continue
        fetched[url_id] = item

    # Group copies of the same event together.
    groups: dict[tuple, list[str]] = {}
    for url_id, item in fetched.items():
        key = (item.get("title") or "", item.get("startDate") or 0)
        groups.setdefault(key, []).append(url_id)

    canonical_paths: dict[str, str] = {}
    for (title, start), url_ids in groups.items():
        # The original publication has the shortest URL; the copies carry
        # extra random suffixes.
        keep = sorted(url_ids, key=len)[0]
        canonical_paths[keep] = f"{EVENTS_PATH}/{keep}/"
        for url_id in url_ids:
            if url_id != keep:
                canonical_paths[url_id] = f"{EVENTS_PATH}/{keep}/"

    for url_id, item in sorted(fetched.items()):
        target = canonical_paths[url_id]
        is_canonical = target == f"{EVENTS_PATH}/{url_id}/"
        body = html_to_markdown(item.get("body") or "", pool, site)
        start = iso_datetime(item.get("startDate"))
        end = iso_datetime(item.get("endDate"))
        fields = [
            ("title", item.get("title") or url_id),
            ("slug", url_id),
            ("url", f"/events/{url_id}/"),
            # The date carries the start time, so that the site can tell an
            # upcoming event from a past one.
            ("date", start or iso_date(item.get("publishOn"))),
            ("start", start),
            ("end", end),
            ("lastmod", iso_datetime(item.get("updatedOn"))),
            ("author", (item.get("author") or {}).get("displayName") or ""),
            ("description", plain_text(item.get("excerpt") or "")[:200]),
            ("location", (item.get("location") or {}).get("addressLine1") or ""),
            ("legacy_url", f"{EVENTS_PATH}/{url_id}"),
        ]
        if item.get("assetUrl"):
            local = pool.register(item["assetUrl"])
            if local:
                fields.append(("image", local))
        if is_canonical:
            write_content(out_dir / "content" / "events" / f"{url_id}.md", fields, body)
        redirects.append((f"{EVENTS_PATH}/{url_id}", target))
        inventory.append(
            {
                "source_url": f"{EVENTS_PATH}/{url_id}",
                "new_url": target,
                "kind": "event" if is_canonical else "event-clone",
                "status": "migrated" if is_canonical else "redirected to canonical",
            }
        )

    unique = sum(1 for u in canonical_paths if canonical_paths[u] == f"{EVENTS_PATH}/{u}/")
    print(f"  {EVENTS_PATH}: {len(fetched)} published, {unique} distinct events")
    return canonical_paths


def export_committee_pages(
    site: str,
    pool: ImagePool,
    redirects: list[tuple[str, str]],
    inventory: list[dict],
    out_dir: Path,
) -> None:
    """Export the committee pages.

    Each committee on Squarespace is a blog collection with its own landing
    text (chair, remit) sitting alongside the posts. The posts come from the
    JSON endpoint; the landing text comes from the rendered page.
    """
    for path, section in sorted(COMMITTEE_COLLECTIONS.items()):
        # The posts.
        try:
            payload = fetch_json(path, site)
        except Exception as exc:  # noqa: BLE001
            inventory.append(
                {
                    "source_url": path,
                    "new_url": "",
                    "kind": "committee",
                    "status": f"failed: {exc}",
                }
            )
            continue

        for item in payload.get("items") or []:
            slug = item.get("urlId") or ""
            if not slug:
                continue
            body = html_to_markdown(item.get("body") or "", pool, site)
            fields = [
                ("title", item.get("title") or slug),
                ("slug", slug),
                ("url", f"/{section}/{slug}/"),
                ("date", iso_date(item.get("publishOn"))),
                ("lastmod", iso_datetime(item.get("updatedOn"))),
                ("author", (item.get("author") or {}).get("displayName") or ""),
                ("description", plain_text(item.get("excerpt") or "")[:200]),
                ("legacy_url", f"{path}/{slug}"),
            ]
            write_content(out_dir / "content" / section / f"{slug}.md", fields, body)
            new_path = f"/{section}/{slug}/"
            redirects.append((f"{path}/{slug}", new_path))
            inventory.append(
                {
                    "source_url": f"{path}/{slug}",
                    "new_url": new_path,
                    "kind": "committee-post",
                    "status": "migrated",
                }
            )

        # The landing text, which lives in the rendered page.
        try:
            html = fetch(f"{site}{path}")
        except Exception as exc:  # noqa: BLE001
            inventory.append(
                {
                    "source_url": path,
                    "new_url": "",
                    "kind": "committee-index",
                    "status": f"failed: {exc}",
                }
            )
            continue

        pieces: list[str] = []
        for btype, inner in content_blocks(html):
            if btype in ("newsletter", "summary"):
                continue
            md = html_to_markdown(inner, pool, site)
            if md.strip():
                pieces.append(md)
        body = "\n\n".join(pieces)

        collection = payload.get("collection") or {}
        title = COMMITTEE_TITLES.get(section) or collection.get("title") or path.strip("/").split("/")[-1]
        body = strip_leading_heading(body, title)
        fields = [
            ("title", title),
            ("legacy_url", path),
            ("sitemap", "true"),
        ]
        write_content(out_dir / "content" / section / "_index.md", fields, body)
        new_path = f"/{section}/"
        redirects.append((path, new_path))
        inventory.append(
            {
                "source_url": path,
                "new_url": new_path,
                "kind": "committee-index",
                "status": "migrated",
            }
        )


def export_static_pages(
    site: str,
    pool: ImagePool,
    redirects: list[tuple[str, str]],
    inventory: list[dict],
    out_dir: Path,
) -> None:
    """Export the plain pages, reading their bodies from the rendered HTML."""
    for path, slug in sorted(STATIC_PAGES.items()):
        try:
            html = fetch(f"{site}{path}")
        except Exception as exc:  # noqa: BLE001
            inventory.append(
                {"source_url": path, "new_url": "", "kind": "page", "status": f"failed: {exc}"}
            )
            continue

        pieces: list[str] = []
        for btype, inner in content_blocks(html):
            if btype == "newsletter":
                continue
            md = html_to_markdown(inner, pool, site)
            if md.strip():
                pieces.append(md)
        body = "\n\n".join(pieces)

        title = slug.replace("-", " ").title()
        for special, label in (
            ("board", "Board of Directors"),
            ("media-mentions", "CCA in the News"),
            ("committees", "Committees"),
            ("get-involved", "Get Involved"),
            ("editorial", "Editorial Guidelines"),
            ("newsletter", "Newsletter"),
            ("donate", "Donate"),
            ("membership", "Become a Member"),
            ("volunteer", "Volunteer"),
            ("sponsorship", "Sponsorship"),
            ("climate-change", "Climate Change"),
            ("climate-change-dialogue-report", "CAFES Climate Resiliency Community Dialogue Report"),
        ):
            if slug == special:
                title = label

        body = strip_leading_heading(body, title)

        fields = [
            ("title", title),
            ("url", f"/{slug}/"),
            ("legacy_url", path),
            ("sitemap", "true"),
        ]
        if slug == "committees":
            # The committees overview is the section index for /committees/.
            fields[1] = ("url", "/committees/")
            target = out_dir / "content" / "committees" / "_index.md"
        else:
            target = out_dir / "content" / f"{slug}.md"
        write_content(target, fields, body)
        new_path = f"/{slug}/"
        redirects.append((path, new_path))
        inventory.append(
            {"source_url": path, "new_url": new_path, "kind": "page", "status": "migrated"}
        )


def canonical_event_path(url_id: str) -> str:
    return CLONE_SUFFIX.sub("", url_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", default="https://www.centretowncitizens.ca")
    parser.add_argument("--out", default=".")
    parser.add_argument("--no-images", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    site = args.site.rstrip("/")
    out_dir = Path(args.out).resolve()
    pool = ImagePool(out_dir)

    if not args.dry_run:
        # Clear previously exported content so that removed pages do not
        # linger and get published.
        for stale in ("content", "data"):
            target = out_dir / stale
            if target.exists():
                shutil.rmtree(target)

    print(f"Reading sitemap from {site}")
    sitemap = get_sitemap(site)
    print(f"  {len(sitemap)} urls")

    redirects: list[tuple[str, str]] = []
    inventory: list[dict] = []

    # Build the map of old paths to new paths before any page is converted,
    # so that links inside page bodies can be rewritten.
    print("Building the path map")
    build_link_map(site, sitemap)

    print("Exporting blog collections")
    for collection_path, section in COLLECTIONS.items():
        export_collection(site, collection_path, section, out_dir, pool, redirects, inventory)

    print("Exporting committee pages")
    export_committee_pages(site, pool, redirects, inventory, out_dir)

    print("Exporting events")
    event_paths = [
        urllib.parse.urlparse(u).path
        for u in sitemap
        if urllib.parse.urlparse(u).path.startswith(f"{EVENTS_PATH}/")
    ]
    export_events(site, event_paths, out_dir, pool, redirects, inventory)

    print("Exporting static pages")
    export_static_pages(site, pool, redirects, inventory, out_dir)

    # The attachments are copied once the content exists, because the links
    # to them are discovered in the exported content.
    print("Copying site files")
    copy_static_files(site, out_dir)
    copy_favicon(site, out_dir)

    # 3. Section landing pages for the blog collections and events.
    section_pages = {
        "news": ("News", "Updates and announcements from the Centretown Community Association."),
        "advocacy": (
            "Recent Advocacy",
            "Positions, letters and statements from the CCA and its committees.",
        ),
        "events": ("Events", "Meetings, workshops and neighbourhood events."),
    }
    for section, (title, description) in section_pages.items():
        fields = [
            ("title", title),
            ("description", description),
            ("sitemap", "true"),
        ]
        if section == "advocacy":
            fields.append(("categories", sorted(set(ADVOCACY_CATEGORIES.values()))))
        write_content(out_dir / "content" / section / "_index.md", fields, "")
        inventory.append(
            {
                "source_url": "",
                "new_url": f"/{section}/",
                "kind": "section-index",
                "status": "created",
            }
        )

    # 4. The home page. The hero is rendered by the template, so only the
    # blocks that the template does not already provide are kept.
    home_body = ""
    try:
        home_html = fetch(f"{site}/")
        pieces = []
        for btype, inner in content_blocks(home_html):
            # The template supplies the heading, the tagline, the call to
            # action and the events list.
            if btype in ("newsletter", "summary", "code", "image", "button", "line"):
                continue
            text = plain_text(inner)
            if not text.strip():
                continue
            # The template supplies the heading, the tagline, the call to
            # action and the events list.
            if text.strip() in (
                "Centretown Community Association",
                "Working for and with everyone who lives, works and plays in Centretown. Join the Community",
                "Working for and with everyone who lives, works and plays in Centretown.",
                "Join the Community",
                "Coming Events",
            ):
                continue
            md = html_to_markdown(inner, pool, site)
            if md.strip():
                pieces.append(md)
        home_body = "\n\n".join(pieces)
    except Exception as exc:  # noqa: BLE001
        print(f"  warning: could not read home page ({exc})")
    home_fields = [
        ("title", "Centretown Community Association"),
        ("description", "Working for and with everyone who lives, works and plays in Centretown."),
        ("legacy_url", "/"),
        ("sitemap", "true"),
    ]
    write_content(out_dir / "content" / "_index.md", home_fields, home_body)
    inventory.append(
        {"source_url": "/", "new_url": "/", "kind": "home", "status": "migrated"}
    )

    # 5. Collection landing pages and their category views.
    for collection_path, section in COLLECTIONS.items():
        redirects.append((collection_path, f"/{section}/"))
        inventory.append(
            {
                "source_url": collection_path,
                "new_url": f"/{section}/",
                "kind": "collection-index",
                "status": "migrated",
            }
        )
    redirects.append((EVENTS_PATH, "/events/"))
    inventory.append(
        {"source_url": EVENTS_PATH, "new_url": "/events/", "kind": "collection-index", "status": "migrated"}
    )

    # 4. Account for every sitemap URL that is not a direct migration.
    handled = {r[0] for r in redirects}
    for url in sitemap:
        path = urllib.parse.urlparse(url).path
        if path in handled:
            continue
        if path in JUNK_PAGES:
            inventory.append(
                {"source_url": path, "new_url": "/", "kind": "junk", "status": "dropped (test page)"}
            )
            continue
        if path.startswith(f"{EVENTS_PATH}/"):
            inventory.append(
                {"source_url": path, "new_url": "", "kind": "event", "status": "unmapped"}
            )
            continue
        if re.match(r"^/advocacy/category/", path):
            # The new site filters advocacy by category on one page.
            category = path.rsplit("/", 1)[-1]
            redirects.append((path, f"/advocacy/?category={category}"))
            inventory.append(
                {
                    "source_url": path,
                    "new_url": f"/advocacy/?category={category}",
                    "kind": "category-view",
                    "status": "migrated",
                }
            )
            continue
        if path.startswith("/blog_test/") or re.search(
            r"blog[- ]post[- ]title", path, re.IGNORECASE
        ):
            inventory.append(
                {
                    "source_url": path,
                    "new_url": "",
                    "kind": "placeholder",
                    "status": "dropped (test post)",
                }
            )
            continue
        if re.match(r"^/(news|advocacy)/\d{4}$", path):
            inventory.append(
                {"source_url": path, "new_url": "", "kind": "year-archive", "status": "dropped"}
            )
            continue
        inventory.append(
            {"source_url": path, "new_url": "", "kind": "other", "status": "unmapped"}
        )

    # 5. Junk pages redirect home rather than 404, in case anything links them.
    # The test posts under /blog_test/ go the same way.
    for path in sorted(JUNK_PAGES):
        redirects.append((path, "/"))
    for url in sitemap:
        path = urllib.parse.urlparse(url).path
        if path.startswith("/blog_test/"):
            redirects.append((path, "/"))
        elif re.search(r"blog[- ]post[- ]title", path, re.IGNORECASE):
            # A placeholder post. The page is not published, so the old
            # address points home.
            redirects.append((path, "/"))

    if args.dry_run:
        print("\nDry run. Nothing written.")
        unmapped = [i for i in inventory if i["status"] == "unmapped"]
        print(f"  redirects: {len(redirects)}")
        print(f"  images: {len(pool.images)}")
        print(f"  unmapped: {len(unmapped)}")
        for item in unmapped[:40]:
            print(f"    {item['source_url']}")
        return 0

    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    # Hugo reads everything under data/ as site data and tries to parse it,
    # so the CSV working files live outside that directory.
    raw_dir = out_dir / "data-raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with (raw_dir / "redirects.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["source_path", "target_path"])
        for source, target in sorted(set(redirects)):
            writer.writerow([source, target])

    # The same map in YAML, which the Hugo build reads to render the
    # Cloudflare Pages _redirects file.
    with (data_dir / "redirects.yaml").open("w", encoding="utf-8") as fh:
        fh.write("# Generated by tools/export_squarespace.py. Do not edit by hand.\n")
        fh.write("# Every URL the old Squarespace site published, and where it lives now.\n")
        for source, target in sorted(set(redirects)):
            fh.write(
                f"- source: {yaml_scalar(quote_path(source))}\n"
                f"  target: {yaml_scalar(quote_path(target))}\n"
            )

    with (raw_dir / "inventory.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source_url", "new_url", "kind", "status"])
        writer.writeheader()
        for row in inventory:
            writer.writerow(row)

    print(f"\nWrote {len(set(redirects))} redirects and {len(inventory)} inventory rows")
    print(f"Images downloaded: {len(pool.images)}")
    if pool.failed:
        print(f"Images failed: {len(pool.failed)}")
        for url, err in list(pool.failed.items())[:10]:
            print(f"  {url}: {err}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
