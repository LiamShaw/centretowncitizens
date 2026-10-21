#!/usr/bin/env python3
"""Build the site and finalise the Cloudflare Pages redirect map.

Hugo renders the redirect map as public/_redirects.txt, because a Hugo
output format always appends its suffix to the file name. Cloudflare Pages
expects a file called _redirects with no extension, at the root of the
published site, so this script renames it after the build.

The build command for Cloudflare Pages is:

    python tools/build.py

Doing both steps here means the redirect map cannot be left out of a
deployment by accident. A site published without it would return a 404 for
every URL the old Squarespace site served.

Usage:
    python tools/build.py [--hugo <path to hugo>] [--base-url <url>]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--hugo",
        default=os.environ.get("HUGO", "hugo"),
        help="path to the hugo executable",
    )
    parser.add_argument("--base-url", default=os.environ.get("CF_PAGES_URL", ""))
    parser.add_argument("--source", default=".")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    public = source / "public"

    command = [args.hugo, "--gc", "--minify"]
    if args.base_url:
        # Cloudflare sets CF_PAGES_URL for each build. Passing it as the
        # base URL keeps preview deployments from emitting canonical tags
        # that point at the production domain.
        command += ["-b", args.base_url]

    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=source)
    if result.returncode != 0:
        print("error: the Hugo build failed", file=sys.stderr)
        return result.returncode

    rendered = public / "_redirects.txt"
    final = public / "_redirects"
    if rendered.exists():
        shutil.move(str(rendered), str(final))
        count = sum(1 for line in final.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#"))
        print(f"Published redirect map: {final.name} ({count} redirects)")
    elif not final.exists():
        print(
            "error: no redirect map was produced. The build must not be published without it, "
            "because every old URL would return a 404.",
            file=sys.stderr,
        )
        return 1
    else:
        print(f"Redirect map already in place: {final.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
