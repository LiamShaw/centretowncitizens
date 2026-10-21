# Centretown CCA website

The website of the Centretown Community Association (CCA), Ottawa.

The public site is at <https://www.centretowncitizens.ca>.

This is a static site. It is built with [Hugo](https://gohugo.io/), hosted on [Cloudflare Pages](https://pages.cloudflare.com/), and edited through [Sveltia CMS](https://github.com/sveltia/sveltia-cms) by volunteers working in a browser. The content is Markdown files in this repository.

The site was migrated from Squarespace. Every URL the old site published redirects to its new location, so old links in council documents, press coverage and social media keep working.

## Who this README is for

Someone picking this repository up in a few years, with no prior knowledge of it. It explains what the pieces are, how to build and check the site, and how to add things to it.

If you are a volunteer who wants to add news, a letter or an event, you want [docs/Editing Guide.md](<docs/Editing Guide.md>) instead.

## Stack

| Piece | What it is | Where it lives |
| --- | --- | --- |
| Hugo | The static site generator that turns the content into HTML | `hugo.toml`, `layouts/` |
| Sveltia CMS | The browser-based editor that volunteers use | `static/admin/` |
| Cloudflare Pages | Builds the site and hosts it | project settings in the Cloudflare dashboard |
| GitHub | Holds the source files and the history | the `centretown-cca/website` repository |
| CSS | One stylesheet for the whole site | `static/css/style.css` |
| JavaScript | Two small files: the mobile menu and the advocacy filter | `static/js/nav.js`, `static/js/filter.js` |

There is no framework and no build step beyond Hugo. There is no database. The content in the repository is the content of the site.

## Repository layout

```
centretown-cca-site/
├── archetypes/            Hugo templates for new Markdown files
├── content/               all site content, as Markdown with YAML frontmatter
│   ├── *.md               the standing pages: about, board, contact, editorial,
│   │                      get-involved, membership, newsletter, sponsorship,
│   │                      volunteer, media-mentions, climate-change, donate
│   ├── news/              news items
│   ├── advocacy/          letters and statements, tagged by committee
│   ├── events/            events
│   └── committees/        one folder per committee: heritage, housing, planning,
│                          seniors, sepaw, transportation, trees
├── data/
│   ├── redirects.csv      each old Squarespace path and where it went
│   └── inventory.csv      every old URL, its destination, and its status
├── docs/
│   ├── Editing Guide.md   the guide for volunteers
│   ├── Board Memo.md      the memo that went to the board
│   └── Cutover Runbook.md the handover runbook, covering DNS, mail and rollback
├── layouts/               Hugo templates
│   ├── index.html         the home page: upcoming events and latest advocacy
│   ├── _default/          the generic page, list and post templates
│   ├── events/            the events list and the single event page
│   └── baseof.html        the shared shell: header, navigation, footer
├── public/                the built output. Not committed, regenerated on every build
├── resources/             Hugo's generated assets. Not committed
├── scripts/               deployment helper scripts
├── static/
│   ├── admin/             the CMS: index.html and config.yml
│   ├── css/style.css      the stylesheet
│   ├── js/nav.js          mobile navigation toggle
│   ├── js/filter.js       committee filter on the advocacy list
│   ├── files/             files served as they are, such as the by-laws PDF
│   └── images/            images from the old site, and images/uploads/ for
│                          pictures added through the editor
├── tools/                 the Python scripts described below
└── hugo.toml              site settings, navigation menus and taxonomies
```

## Content model

Five kinds of content, each in its own place.

| Kind | Folder | Notes |
| --- | --- | --- |
| News items | `content/news/` | Title, Date, Author, Summary, Body |
| Advocacy letters and statements | `content/advocacy/` | The same fields, plus a Committee |
| Events | `content/events/` | Title, Starts, Ends, Location, Image, Summary, Description |
| Standing pages | `content/` | One file per page, for example `board.md` |
| Committee pages and posts | `content/committees/<name>/` | One folder per committee |

Every file starts with YAML frontmatter and then the body in Markdown.

```markdown
---
title: "CCA expresses concerns about loss of trees on James Street"
date: "2024-11-13"
author: "Mia Jensen"
description: "One or two sentences. These show in listings and link previews."
categories:
  - "Greenspace & Sustainability"
---

The body of the item goes here, in Markdown.
```

An event carries its own fields instead:

```markdown
---
title: "Fall Festival at Dundonald Park"
date: "2026-09-24"
start: "2026-09-24T14:00:00Z"
end: "2026-09-24T18:00:00Z"
location: "Dundonald Park, Ottawa"
image: "/images/uploads/fall-festival.jpg"
description: "Short summary for listings."
---
```

Two details matter more than they look.

### The committee list must be a list

A file written by the CMS with the `Committee` field filled in holds a single value:

```yaml
categories: "Planning"
```

The templates expect a list, and the site build fails on the single-value form with `range can't iterate over Planning`. Write it as a list of one, which is what the exported files use:

```yaml
categories:
  - "Planning"
```

### The start date decides whether an event is upcoming or past

The home page and the events list both sort on `start`. An event with no `start` appears in neither list.

The `categories` key is also a Hugo taxonomy, which is what produces the `/categories/<name>/` pages and the committee filter buttons on the advocacy list. `static/js/filter.js` reads the `?category=` query string and hides the cards that do not match.

## The tooling

All the scripts are Python 3 and live in `tools/`. Run them from the repository root.

| Script | What it does |
| --- | --- |
| `export_squarespace.py` | Pulls the content out of the old Squarespace site |
| `build_redirects.py` | Turns the built site into the Cloudflare Pages `_redirects` file |
| `check_coverage.py` | Verifies the redirect map covers the old site completely |
| `check_site.py` | Crawls the built site for broken internal links and missing images |
| `audit_images.py` | Checks that every image referenced in content exists on disk |

There are also `tools/check_redirects.py`, a narrower version of the coverage check, and a set of `tools/probe*.py` scripts left over from working out how the old site's JSON endpoint behaves. They are kept because they are useful if the export ever needs to be repeated.

### export_squarespace.py

This is the one-time migration, and the tool to reach for if the export ever has to be redone.

Squarespace 7.1 has no XML export. Instead, the script reads the public JSON endpoint, which returns structured content for blog collections and events when you append `?format=json-pretty` to a collection URL. Static pages are the exception, because their bodies are not in the JSON, so those are read from the rendered HTML instead.

```powershell
python tools\export_squarespace.py
```

Useful flags:

```
--site https://www.centretowncitizens.ca   the site to read from
--out .                                    where to write the output
--no-images                                skip downloading images
--dry-run                                  report what it would do, write nothing
```

It writes:

- `content/<section>/<slug>.md`, the Hugo content with YAML frontmatter
- `data/redirects.csv`, the old path mapped to the new one
- `data/inventory.csv`, every source URL with its destination and status
- `static/images/`, the downloaded images, renamed by content token
- `static/files/`, the by-laws PDF and other files the old site served directly
- `static/images/favicon.ico`, the site icon

### build_redirects.py

This is how the redirect map is made, and it is the reason the map is correct rather than merely plausible.

Rather than predicting what URL Hugo will produce, the script reads the built HTML in `public/` and finds the `legacy-url` meta tag that each page carries. That tag holds the old Squarespace address. The script pairs it with the path the page was actually built at, so the map is right by construction even when a slug contains characters Hugo rewrites.

```powershell
python tools\build_redirects.py
```

Defaults are `--public public`, `--inventory data/inventory.csv` and `--out public/_redirects`. It refuses to write a file with more than 2,000 redirects, which is the Cloudflare Pages limit.

### check_coverage.py

Checks that every URL the old site published has a redirect, that every redirect target was actually built, and that no redirect points at itself.

```powershell
python tools\check_coverage.py
```

This one needs network access, because it fetches the old site's `sitemap.xml` to find out what the old site published. Run it while the old site is still up.

### check_site.py

Crawls the running site over HTTP and reports broken internal links and missing images.

```powershell
python tools\check_site.py
```

It expects a server on `http://127.0.0.1:8811`, so start one first:

```powershell
C:\Users\shawl\bin\hugo.exe server --port 8811 --disableFastRender
```

It exits non-zero if it finds anything wrong, which makes it usable as a gate.

### audit_images.py

Reads every Markdown file in `content/`, collects the `/images/...` references, and compares them with what is on disk in `static/images/`. It reports images that are referenced but missing, and files that are on disk but never referenced.

```powershell
python tools\audit_images.py
```

It takes no arguments and reads the current directory, so run it from the repository root. It also queries the live site to explain where unreferenced images came from, so it needs network access.

## Build and deploy

Hugo is at `C:\Users\shawl\bin\hugo.exe` on the machine this was built on. Everywhere else, install Hugo and make sure `hugo` is on the path.

### The full sequence

```powershell
cd C:\Users\shawl\source\repos\centretown-cca-site

# 1. Build the site into public/
C:\Users\shawl\bin\hugo.exe --minify

# 2. Rebuild the redirect map from what was just built
python tools\build_redirects.py

# 3. Confirm the map covers the old site and every target exists
python tools\check_coverage.py

# 4. Confirm every image referenced in content is on disk
python tools\audit_images.py
```

Then, in a second terminal, start a server and crawl it:

```powershell
cd C:\Users\shawl\source\repos\centretown-cca-site
C:\Users\shawl\bin\hugo.exe server --port 8811 --disableFastRender
```

```powershell
cd C:\Users\shawl\source\repos\centretown-cca-site
python tools\check_site.py
```

Then publish:

```powershell
cd C:\Users\shawl\source\repos\centretown-cca-site
git add -A
git commit -m "Update the site"
git push origin main
```

Cloudflare Pages builds on the push and publishes the result, which takes about a minute.

`public/` and `resources/` are build output. They should not be committed. Add them to `.gitignore` if that file is missing.

### Cloudflare Pages settings

The Pages project should build with Hugo and publish the `public` directory. The build command has to include the redirect step, because the redirect file is generated from the built HTML and the built HTML is not committed:

```
hugo --minify && python tools/build_redirects.py
```

If the build image provides Python as `python3` rather than `python`, use that name instead. Check the build log if the redirect file is missing from a deployment.

The production branch is `main`. Cloudflare Pages creates a preview build for each change, which is what a maintainer reviews before a change goes live.

## Adding a new page or section

### A new standing page

1. Create a Markdown file in `content/`. The file name becomes the address, so `content/annual-report.md` gives you `/annual-report/`.
2. Give it frontmatter with a `title`, and write the body in Markdown.
3. Add it to the navigation in `hugo.toml`:

```toml
[[menus.main]]
name = "Annual Report"
pageRef = "/annual-report"
weight = 115
```

`weight` decides the order in the menu. Existing weights run from 10 to 110.

4. Build and check that the page appears.
5. Nothing else is needed for the editor. The Pages collection covers every top-level file in `content/`, so volunteers will be able to edit the new page through the form straight away.

### A new section, such as another kind of post

1. Create `content/<name>/_index.md` with a `title` and any introductory text.
2. Add the section to the permalinks table in `hugo.toml`, so its posts get a consistent address:

```toml
[permalinks]
reports = "/reports/:slug/"
```

3. Add a menu entry, as above.
4. Add a collection to `static/admin/config.yml` so the section appears in the editor, and give it the fields it needs.
5. Build and check.

## Adding a committee

1. Create the folder `content/committees/<name>/` and a file `_index.md` inside it, holding the committee's title and its remit.
2. Add it to the committees menu in `hugo.toml`:

```toml
[[menus.committees]]
name = "Seniors"
pageRef = "/committees/seniors"
weight = 70
```

3. Add the committee's posts as Markdown files in that folder.
4. If the committee's posts should also be labelled in the advocacy listing, add the committee's name to the `options` list of the `Committee` field in `static/admin/config.yml`, and to the `categories` list in `content/advocacy/_index.md`. The filter buttons on the advocacy page come from that second list, and they have to match the dropdown exactly.
5. Build and check that the committee page appears in the footer and in the navigation.

## The redirect map

The map lives in `public/_redirects`, which Cloudflare Pages reads when it serves the site.

It is generated by `tools/build_redirects.py` from the built site, and it is never edited by hand. The file starts with a comment saying so. If you need to change it, change the content that produces it and rebuild.

Each published page carries its old Squarespace address in a `legacy-url` meta tag, which is what the generator reads. Pages that were deliberately dropped are taken from `data/inventory.csv` and pointed at their nearest replacement.

Two things to know:

- Cloudflare Pages allows 2,000 static redirects in a `_redirects` file. The generator refuses to write more than that, so it fails loudly rather than producing a silently truncated map. The map currently holds 286 entries, so there is room, but the count is worth watching if the old site ever grows.
- The old site's advocacy pages were split by committee, for example `/advocacy/category/SEPAW`. The new site filters one page instead, so those old addresses redirect to `/advocacy/?category=SEPAW`.

## The old site, email and domain

The old Squarespace site stays online until the board signs off on the new one. Both are reachable during the handover.

The association's email address and its domain registration are not affected by this repository. They live with the provider that manages them, not with the website code. The handover of those, and the order the two must be done in, is written up in [docs/Cutover Runbook.md](<docs/Cutover Runbook.md>), which is worth reading before any change to the domain's nameservers.
