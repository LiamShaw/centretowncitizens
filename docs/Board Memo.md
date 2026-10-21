# Board Memo: Website Hosting for the Centretown Community Association

To: Board of Directors, Centretown Community Association
From: Site administrator, prepared for board review
Date: 21 October 2026
Re: Whether to move the website off Squarespace onto free hosting

## Summary

The website is on Squarespace, a paid platform, and the association now uses only a small part of what that platform offers. Moving to free hosting (Cloudflare Pages for the site, GitHub for the files, Sveltia CMS for editing) costs CA$0 in hosting and saves roughly CA$384 a year at the cheapest workable Squarespace plan, more if the association is on a higher plan. The migration itself has already been built and tested, and the old site stays live until the board signs off. The honest counterweight is that the new site is edited through a friendly browser form tied to a GitHub account, so the care of the site concentrates in one volunteer instead of spreading across whoever happens to be available. The recommendation is a staged move: fix the five problems found on the current site first, then migrate if the board still wants to and has named a volunteer who will own it.

Everything in this memo comes from inspecting the live site and the built replacement, not from assumptions about what the site probably contains.

## What the website is today

The site runs on Squarespace 7.1 at centretowncitizens.ca. It has 286 pages listed in its sitemap. The real editorial content is modest:

| Content type | Count |
|---|---|
| News and advocacy posts | 31 |
| Committee pages | about 25 |
| Static pages (about, contact, committees) | 14 |
| Event pages | 194, but only 93 distinct events |
| Images | 131, about 75 MB in total |

Of the 194 event pages, 101 are republished copies of the same events with random name suffixes, and 83 of those are duplicate addresses for the same handful of events.

The platform is being paid for features the association does not use. There is no online store, no members-only area (both login and sign-up are switched off), no products and no customer accounts. Donations run through a PayPal redirect rather than through Squarespace payments, so they carry across to a new platform unchanged. There is no Acuity scheduling, no Mailchimp and no Zapier connection.

The one feature the association does use in full is editing. Six accounts have published news and advocacy posts: jean legault, Mia Jensen, Mindy Sichel, Treasurer CentretownCitizensCA, CCA President - Mary Huang, and a shared "Guest User" account. Squarespace Basic allows only 2 contributors, so Basic is not an option. Core is the floor.

## What it costs to stay

Squarespace Canada pricing, billed annually:

| Plan | Per month | Per year | Works for 6 editors? |
|---|---|---|---|
| Basic | CA$21 | CA$252 | No, capped at 2 contributors |
| Core | CA$32 | CA$384 | Yes |
| Plus | CA$46 | CA$552 | Yes |
| Advanced | CA$109 | CA$1,308 | Yes |

Paying monthly costs roughly 30 percent more across the board (Basic CA$30, Core CA$45, Plus CA$59, Advanced CA$139 per month).

One point needs saying plainly, because the opposite is a common belief. The promotional code NONPROFIT takes 10 percent off the first payment only. There is no standing nonprofit rate and no charity tier. If the association stays on Squarespace, the saving has to come from changing plan. Nonprofit status brings no discount.

## The free hosting option

| Service | What it gives | What this site needs |
|---|---|---|
| Cloudflare Pages (hosting) | Unlimited bandwidth for static files, 500 builds a month, 100 custom domains, 20,000 files per site, 25 MiB maximum file size | 131 images and roughly 300 pages, so the limits are far away |
| Cloudflare DNS | Free | 1 domain zone |
| GitHub (the files) | Free private repository | 1 repository |
| Sveltia CMS (the editor) | MIT licensed, free forever, no user limit, no project limit, no paid tier | 6 editors |

Nothing about hosting becomes a new bill. The domain stays exactly where it is today, registered at the Canadian CIRA registrar (Ethical Web Services, d-zone.ca). Cloudflare does not sell .ca domains and should not, so the domain registration has to remain there. Only where the DNS is hosted changes.

## Cost comparison

| Line | Stay on Squarespace (Core) | Move to free hosting |
|---|---|---|
| Hosting | CA$384 per year | CA$0 |
| Domain renewal | Unchanged | Unchanged |
| Editors | Unlimited, drag-and-drop builder | Unlimited, browser form, one GitHub account per editor |
| Ongoing volunteer effort | Low, any volunteer can be handed the site | Higher, one person has to understand the setup |
| Price risk | Squarespace can raise prices and there is no nonprofit rate to hold them to | Free tier limits are far away for a site this size, and a future change is possible |

The first step is to check the current plan under Settings, Billing. If the association is on Plus or Advanced, the saving is larger than CA$384 a year. If it is on Core, the saving is CA$384, which is real money for a volunteer association and also not a large sum.

## What has already been built and verified

The technical work is done and checked, so the board is deciding on a finished plan, with every step below already verified.

- A scripted export pulled all content from Squarespace's public JSON endpoint, because Squarespace 7.1 has no XML export at all, and rendered it into Hugo content files.
- All 286 old addresses are mapped to permanent redirects at their new location. Every one of the 286 was checked: every live address has a redirect, and every redirect points to a page that was actually built.
- All 131 images were downloaded and re-hosted inside the new site, because Squarespace's image addresses stop working if the account is closed.
- A link checker crawled the finished site and found zero broken internal links and zero missing images.
- The new site runs on Hugo, with the Sveltia CMS editor at /admin for the people who write the news posts.
- The old Squarespace site stays live and untouched until the board signs off, so the fallback if anything goes wrong is "wait an hour", not "rebuild from scratch".

Page load speed is expected to improve on the new site, since it serves static files with no page-building layer. We have not measured the difference, so please treat that as an expectation.

## Recommendation

A staged move, in three parts.

1. Fix the five problems listed below on the current site. They are worth fixing whichever platform the board chooses, and doing them first means the site is correct in the meantime if the move is delayed or dropped.
2. Check the current Squarespace plan under Settings, Billing and record the number, so the board knows the real saving.
3. If the board still wants to move after step 1, approve the cutover and name a site owner. The cutover itself is small: freeze the content, run the final export, change the DNS, publish the announcement to members.

The case for moving is not only the CA$384. It also removes a dependency on one vendor's pricing, it removes limits the association does not need, and it puts the content and images in the association's own repository, which the association owns outright. The case against is that editors have to learn a different way of working, and the care of the site ends up in fewer hands. The board should decide with both halves in view.

## The main risk: volunteer attention and a single point of failure

The cost of the migration is not money. It is volunteer attention, and it concentrates responsibility.

Squarespace's editor is forgiving. A volunteer can be handed the site and be publishing within an hour. Sveltia presents a friendly form, so nobody has to touch the underlying version control system, but every editor does need a GitHub account, and if the person who set the site up leaves the board, somebody else has to learn the setup from scratch.

Today the risk of the site going unmaintained is low, because many people can edit it. After the move that risk is higher, unless the board deliberately assigns it. This is the single most important thing to decide before approving the move.

Three measures reduce it:

- The repository lives in a GitHub organisation owned by the association, not in a personal account, so it survives any individual leaving the board.
- Sveltia gives editors a friendly web form, so no volunteer ever needs to work with the version control system directly.
- Cloudflare Pages creates a preview of any change before it goes live, so an editor can ask a second person to check the page first.

## Decisions requested

1. Approve fixing the five defects on the current site now, whatever the platform decision turns out to be.
2. Decide whether to approve the migration, conditional on naming a site owner and running one training session for the editors.
3. If the migration is approved, approve the DNS change and a cutover date. The domain registration itself does not change and costs the same as it does today.
4. Decide where newsletter signups should be collected, so the broken form can be retired or repaired. A Google Group is the leading candidate.
5. Report the current Squarespace plan, since the size of the saving depends on it.

## Problems on the current site worth fixing regardless

1. The newsletter signup form is broken. Every page carries a Squarespace newsletter block, and the block's own status reads "This newsletter signup form needs a storage option." That status is hidden from visitors, but the Sign Up button is live. The form has nowhere to put the addresses it collects. It is an inference, not a confirmed fact, that signups are being silently lost. If they are, the board may believe it has a subscriber list when it has none. The new site hides the form until a real destination is chosen, and a Google Group is the leading candidate because the board already runs Google Groups for its board and chairs lists and already pays for Google Workspace. To keep the form on Squarespace instead would require a paid storage add-on, which changes the cost comparison.
2. A broken link on the September 2025 obituary for Patricia Marsden Dole. The link target contains a stray space, so it reads as `https:// https://www.hpmcgarry.ca/...` and does not work.
3. The Events page still shows a past event as "Upcoming". The Mayoral Debate took place on 15 October 2026 and is still the headline event. There are no future events on the site, confirmed by scanning all 194 event addresses.
4. Junk pages are live and can be found by search engines: /blog_test, /atletico, /homeold, /test-1, /success, plus 83 duplicate event addresses for the same handful of events. On the new site only real pages are built and everything else redirects.
5. Empty blocks are showing. The homepage "Summary Block" for Coming Events is empty, and one advocacy post still contains an empty embed placeholder.

## Who has to do the work

| Task | Who | Rough time |
|---|---|---|
| Fix the five defects on the current site | Site administrator, plus one volunteer to check the links afterwards | 2 to 4 hours |
| Record the current Squarespace plan | Any board member with account access | 15 minutes |
| Decide where newsletter signups go, then wire it up | Board decision, then the site administrator | 1 hour, plus the decision |
| Train the editors on the new form | Site administrator runs one session, then each editor publishes one test page | 1 hour per editor |
| Cutover | Site administrator, with one other person reachable by phone | 2 to 3 hours |
| Ongoing editing | One named site owner, plus any number of trained editors | Small, ongoing |

These durations are estimates. They have not been measured.

The board's decision is the second and third items in the decision list: whether to approve the migration, and who will own the site afterwards. The saving is worth having, but the owner is worth more.
