# Cutover Runbook: Squarespace to Cloudflare Pages

Domain: `centretowncitizens.ca`
Registrar (unchanged): Ethical Web Services / d-zone.ca, a CIRA registrar
Prepared: 21 October 2026
Reader: the volunteer holding registrar access and Google Workspace admin access

> ## Read this before you touch anything
>
> The website is the easy part. Email is the part that can hurt the association.
>
> Moving the DNS for this domain moves every record, including the MX records that route mail for every board member. If the MX, SPF or DKIM records are missing or wrong at the moment the nameservers change, mail to the association stops arriving. Board members do not know the site moved, they only know the mail is gone.
>
> Two rules follow from that, and they govern the whole order of operations:
>
> 1. **Write the corrected SPF record before the apex A record changes.** The current SPF contains `+a`, which silently authorises whatever the domain's A record points at. See [Appendix C](#appendix-c-spf-reference-and-the-a-trap).
> 2. **Verify mail before you verify the website.** Run the Phase 8 mail checks first, every time.
>
> The old Squarespace site stays live and untouched until the board signs off. Rollback is a DNS change and takes minutes. See [Phase 9](#phase-9-rollback).

---

## Before you start

### Access you need

| System | What you need it for | Notes |
|---|---|---|
| Ethical Web Services / d-zone.ca | Changing the four nameservers | The registrar login, not the DNS panel. The domain registration stays here. |
| Cloudflare | Hosting DNS, hosting the site, hosting the CMS authenticator | A new account on the Free plan. Add two-factor authentication to the account on day one. |
| GitHub | Holding the content, and sign-in for editors | An account that can create an organisation. See [Phase 2](#phase-2-github-organisation-and-repository). |
| Google Workspace admin console | Reading the authoritative DKIM key, confirming the domain after the move | Admin access for `centretowncitizens.ca`. |
| Squarespace | Keeping the old site alive for rollback | Keep the account paid and open until the board signs off. |
| A second person | Two-person rule on the cutover | Someone reachable by phone for the duration of Phase 6. |

### Tools

- Windows PowerShell. This runbook uses `Resolve-DnsName`. `dig` is not installed on this machine and is not needed.
- A web browser.
- A text editor, for the CMS config and the SPF string.
- Node.js and npm, for deploying the CMS authenticator as a Cloudflare Worker in Phase 7. `node --version` should print a version. If it does not, install Node.js before starting Phase 7.
- Python 3, if you want to run the site's own checking scripts locally before the cutover. The Cloudflare build image already includes it.

### How long it takes

Two to three hours for the cutover itself, plus up to a few hours of DNS propagation afterwards. Do not start after 4pm on a weekday, and do not start in the week before a board meeting.

### What you must not change

- The domain registration. It stays at Ethical Web Services. Cloudflare does not sell `.ca` domains and should not be given the job: CIRA requires Canadian presence for `.ca` registration, and a Canadian registrar already satisfies that.
- The Google Workspace subscription, users, and mailboxes.
- The Squarespace site or subscription until the board signs off.
- Any file in the site repository other than `static/admin/config.yml` (Phase 7), and the GitHub Actions workflow if you take the GitHub Pages option.

### Step zero: export the current DNS zone

Do this before anything else, and keep the export.

1. Log in to the d-zone.ca panel for `centretowncitizens.ca`.
2. Export or copy the complete DNS record list, every record, including anything for subdomains.
3. Save it somewhere outside this repository, as a text file.
4. Diff that list against the record tables in [Phase 4](#phase-4-dns-records-in-cloudflare).

The record tables in this runbook cover the web records and the email records that were verified for this domain. The zone may hold others that were not part of the verification: a Mailchimp CNAME or verification TXT for the newsletter, a Google domain-ownership TXT, a subdomain used by an old campaign, a second site. **Any record in the export that is not in the tables below must be recreated in Cloudflare.** An unrecreated record is an outage that only shows up when someone uses that part of the service.

---

## Phase 1: Choose the host

Two workable options. Both are free, both serve a static Hugo site, both accept the repository without a build server of your own.

| | Cloudflare Pages (recommended) | GitHub Pages (lower DNS risk) |
|---|---|---|
| Nameserver change | Required. Cloudflare cannot serve an apex custom domain unless the domain is a Cloudflare zone. | Not required. The apex is served by A records pointing at GitHub. |
| DNS hosting moves | Yes, to Cloudflare. The mail records are recreated there. | No. The mail records at d-zone are never touched. |
| Speed | Faster. Files are served from Cloudflare's edge network in Canada and elsewhere. | Slower. Files are served from GitHub's edge network. |
| Preview builds | Yes. Every content edit produces a preview URL before it goes live, which is how a second board member checks a page. | Yes, but previews are a GitHub Pages feature, not a first-class part of the publish flow. |
| Redirect map for the 286 old Squarespace addresses | Native. Cloudflare Pages reads the `_redirects` file the build produces and returns a 301 for each old address. | No native support. GitHub Pages serves a 404 page for an unknown address and has no redirect file. The old addresses need a Cloudflare Worker in front of GitHub Pages, or a `404.html` hack that returns a 404 status rather than a 301. See [Appendix B](#appendix-b-full-record-set-github-pages). |
| DNS tooling next to the mail | Yes. The same account that hosts the site hosts the DNS for the domain and can check the mail records. | No. DNS stays at d-zone, in a different login from the site. |
| Repository privacy | Private repositories are supported. | Free private repositories cannot publish GitHub Pages. The repository would have to be public. |
| CMS sign-in | The Sveltia CMS authenticator runs as a Cloudflare Worker in the same account. | The authenticator would still need to live somewhere. Cloudflare Worker remains the simplest route. |
| Risk to email | The records are recreated by hand. Get them right and there is no difference in practice. | Lowest. The mail records are never recreated. |

Recommendation: **Cloudflare Pages.** It is the better host, and the email risk is a matter of care rather than of difficulty, because the record set is written out in full in this runbook and is verified before the nameservers move.

If the board wants the lowest possible risk to email, take GitHub Pages and leave the nameservers at d-zone. The full record set for it is in [Appendix B](#appendix-b-full-record-set-github-pages).

Whichever you choose, the steps after Phase 1 for GitHub Pages skip the Cloudflare zone, Phase 4 and Phase 6, and use [Appendix B](#appendix-b-full-record-set-github-pages) in their place. Phases 2, 5, 7, 8 and 9 still apply, with the Pages settings in Phase 5 replaced by the GitHub Pages settings in [Appendix B](#appendix-b-full-record-set-github-pages).

---

## Phase 2: GitHub organisation and repository

The repository must live in an organisation the association owns, not in a volunteer's personal account. A personal account is a single point of failure: when that volunteer leaves the board, the site goes with them.

### 2.1 Create the organisation

1. On GitHub, click your avatar, then **Organizations**.
2. **New organization**, then **Free** (this is enough; the paid tier is for private repositories on Pages and is not needed).
3. Organisation name: `centretown-cca`.
4. Organisation display name: `Centretown Community Association`.
5. Choose a personal address for the organisation. This address receives GitHub's system mail, so give it a real mailbox that the association controls, not the volunteer's own address.
6. Verify the email address.

### 2.2 Create the repository

1. In the organisation, **New repository**.
2. Name: `website`.
3. Visibility: **Private**. Cloudflare Pages can build a private repository, and the content is the association's business.
4. Initialise the repository with a README, a `.gitignore`, and a licence, or leave it empty and push the existing repository into it.
5. Push the existing site repository into `centretown-cca/website`:
   ```
   git remote add origin https://github.com/centretown-cca/website.git
   git push -u origin main
   ```
   If the site repository already has a remote, change that remote's URL. Keep one remote.

### 2.3 Add the board members

1. Organisation → **Settings** → **People** → **Invite people**.
2. Roles:
   - **Owner**: one or two people. Owners can delete the organisation and manage billing. Do not give this to everyone.
   - **Admin**: the site owner and one backup.
   - **Member**: everybody else who edits content.
3. Then give each editor write access to the content repository, because Sveltia will not let a user sign in without it:
   - Repository `website` → **Settings** → **Collaborators** → **Add people** → add the person with role **Write**.
4. Confirm every editor has signed in to GitHub at least once and enabled two-factor authentication on their own account. Sveltia sign-in goes through GitHub OAuth, so a GitHub account is required for every editor.

---

## Phase 3: Cloudflare account and zone

1. Create a Cloudflare account at dash.cloudflare.com on the Free plan.
2. Enable two-factor authentication on the account.
3. **Add a site** → enter `centretowncitizens.ca` → choose **Free**.
4. Cloudflare scans for existing DNS records and shows a review screen. **Do not accept the scan.** You are entering the records by hand from [Phase 4](#phase-4-dns-records-in-cloudflare) instead, because the scan will not know about the Google Workspace records and the SPF fix.
5. Cloudflare assigns two nameservers, of the form `NAME.ns.cloudflare.com`. Write them down. You need them in Phase 6.
6. Ignore any prompt to change the nameservers yet. That happens in Phase 6, after the records and the Pages project are in place.
7. Create the Cloudflare Pages project now, by following Phase 5.1. You need the project's `<project>.pages.dev` hostname before you can enter the web records in Phase 4.2.

---

## Phase 4: DNS records in Cloudflare

Order inside this phase matters only for your own clarity, but there is one hard dependency that crosses into Phase 6: **every record below must be in the Cloudflare zone before the nameservers change.** At the moment the nameservers change, Cloudflare's zone becomes the live zone. If a record is missing at that moment, it does not exist for the whole internet.

### 4.1 Email records

Go to **DNS** → **Records** → **Add record**. Enter these five MX records first.

| Type | Name | Mail server | Priority | Proxy |
|---|---|---|---|---|
| MX | `@` | `aspmx.l.google.com` | 1 | DNS only |
| MX | `@` | `alt1.aspmx.l.google.com` | 5 | DNS only |
| MX | `@` | `alt2.aspmx.l.google.com` | 5 | DNS only |
| MX | `@` | `alt3.aspmx.l.google.com` | 10 | DNS only |
| MX | `@` | `alt4.aspmx.l.google.com` | 10 | DNS only |

MX records are never proxied. The proxy toggle must be grey.

Now the SPF record. Read [Appendix C](#appendix-c-spf-reference-and-the-a-trap) before you type it.

| Type | Name | Value | Proxy |
|---|---|---|---|
| TXT | `@` | `v=spf1 include:_spf.google.com +mx ip4:50.28.38.88 ~all` | DNS only |

This is the corrected SPF record. It is not the record currently at the domain. The current one is `v=spf1 +a +mx +ip4:50.28.38.88 ~all`, and the `+a` has to go for the reason given in Appendix C.

Do not enter the SPF string until you have confirmed the status of `50.28.38.88`. If that host still sends mail for the domain, keep the `ip4:50.28.38.88` term as shown above. If nothing sends mail from it any more, drop the term, and the final string becomes:

```
v=spf1 include:_spf.google.com +mx ~all
```

Only one SPF record may exist. If the zone has two TXT records starting with `v=spf1`, the result is a permission error and mail fails, so delete the extra one.

Now the DKIM record. **Read the authoritative value out of the Google Admin console. Do not type the copy from this runbook.** A DKIM key that is even slightly wrong means every outbound board email fails signature verification and lands in spam.

1. Google Admin console → **Apps** → **Google Workspace** → **Domains** → **Manage domain** → **View details**.
2. Open the DKIM section. If a key is listed, open it and copy the whole value. If none is listed, generate one and note the selector it is created under.
3. Confirm the selector is `default`. If Google shows a different selector, use that selector as the record name instead of `default`.
4. Compare it against the value in [Appendix C](#appendix-c-spf-reference-and-the-a-trap). If they differ, Google wins. Use the value from the console.
5. If the key in this document has been published anywhere public, rotate it in that same screen before you enter it, and publish only the new value.

Then create the record:

| Type | Name | Value | Proxy |
|---|---|---|---|
| TXT | `default._domainkey` | the value copied from the Google Admin console | DNS only |

If the record name field does not accept `default._domainkey` directly, type `default` in the Name field and leave the zone as `centretowncitizens.ca`. Cloudflare appends the zone automatically.

### 4.2 Web records

Only if you chose Cloudflare Pages. The GitHub Pages equivalent is in [Appendix B](#appendix-b-full-record-set-github-pages).

Let `<project>` be the name of your Cloudflare Pages project. The hostname is `<project>.pages.dev`. The project has to exist before you can fill in this table, so create it now by following Phase 5.1, then come back to this table. Phase 5.1 is also listed in Phase 3 for that reason.

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | `@` | `<project>.pages.dev` | Proxied |
| CNAME | `www` | `<project>.pages.dev` | Proxied |

A CNAME at the apex works because Cloudflare flattens it. Cloudflare Pages often creates these two records itself when you add the custom domain in Phase 5.4. If the record list already shows an A record for the apex pointing at Cloudflare's Pages addresses, keep that record and do not add a second apex record. Two apex records with different targets break the zone.

The old Squarespace records must not be copied into Cloudflare:

| Type | Name | Old target | Action |
|---|---|---|---|
| A | `@` | `198.49.23.145` | Do not enter |
| A | `@` | `198.185.159.145` | Do not enter |
| A | `@` | `198.49.23.144` | Do not enter |
| CNAME | `www` | `ext-cust.squarespace.com` | Do not enter |

### 4.3 CAA

Cloudflare's documentation notes that a CAA record can block certificate issuance for a custom domain, which shows up as a certificate error on the live site.

Check whether one exists today:

```powershell
Resolve-DnsName -Name centretowncitizens.ca -Type CAA
```

"No records found" is the expected result, because there is no CAA record on the domain today. If a CAA record does turn up, it must authorise Let's Encrypt, which is the certificate authority Cloudflare Pages uses for custom domains. Either add the `issue` authorisation to it, or delete it. Adding is safer than deleting.

| Type | Name | Value |
|---|---|---|
| CAA | `@` | `0 issue "letsencrypt.org"` |

In the Cloudflare form this is the flag `0`, the tag `issue`, and the value `"letsencrypt.org"`.

One CAA check covers the whole domain. Certificate authorities look for CAA on the domain being certified and on its parents, so a CAA at the apex governs `www.centretowncitizens.ca` as well.

### 4.4 Cloudflare DNS settings worth checking

| Setting | Where | Value | Why |
|---|---|---|---|
| DNSSEC | Zone → Settings → DNSSEC | Disable if it is currently enabled at d-zone, and re-enable it later from Cloudflare | DNSSEC records are signed against the current registrar's keys. Leaving a stale DS record at the registry after the nameserver change breaks resolution for some resolvers, which looks like an outage. If DNSSEC is on today, capture the DS record from d-zone first. |
| Email addresses | Zone → Settings → Email Addresses | Leave alone | This only affects addresses used on Cloudflare email products, which this domain does not use. |
| Proxy status on MX and TXT | DNS → Records | Grey cloud | Proxied mail records break mail delivery. |

### 4.5 Check the zone before moving on

Every record from the export in "Step zero" must be present. Do not proceed until the list matches.

```powershell
Resolve-DnsName -Name centretowncitizens.ca -Type MX -Server 1.1.1.1
Resolve-DnsName -Name centretowncitizens.ca -Type TXT -Server 1.1.1.1
Resolve-DnsName -Name default._domainkey.centretowncitizens.ca -Type TXT -Server 1.1.1.1
```

These queries do not yet return the Cloudflare records, because the domain still points at d-zone. They return the current records, and they are a way to compare what you typed against what is live. The real check is the Cloudflare dashboard's own DNS record list.

---

## Phase 5: Cloudflare Pages project

Skip to [Appendix B](#appendix-b-full-record-set-github-pages) if you chose GitHub Pages.

### 5.1 Create the project

This is step 7 of Phase 3. Do it there if you have not already.

1. Cloudflare dashboard → **Workers and Pages** → **Create application** → **Pages** → **Connect to Git**.
2. Authorise Cloudflare to reach the organisation. Grant access to `centretown-cca` and to the `website` repository, and to any repository if you want to move the project later.
3. Choose the `centretown-cca` organisation and the `website` repository, then **Begin setup**.

### 5.2 Build settings

| Setting | Value |
|---|---|
| Project name | `website` (gives `website.pages.dev`) |
| Production branch | `main` |
| Framework preset | Hugo |
| Build command | `python tools/build.py` |
| Preview build command | `python tools/build.py` |
| Build output directory | `public` |
| Root directory | leave blank (the repository root) |
| Environment variable `HUGO_VERSION` | `0.148.2` |

Notes on the build settings:

- `HUGO_VERSION` pins the Hugo version. The site was built and verified with Hugo 0.148.2, and pinning it means a future change to the Cloudflare build image cannot change how the site renders without someone noticing.
- The build command runs `tools/build.py`, which runs Hugo and then finalises the redirect map. The map is not optional. The site carries a redirect for every one of the 286 addresses the old Squarespace site published, and Cloudflare Pages clears the output directory before each build and then reads `_redirects` from the root of that directory. A build that skipped the redirect map would publish the site with every old address returning a 404 instead of a 301, and links from council documents, press coverage and social media would break.
- The redirect map is produced by Hugo itself, from `data/redirects.yaml`, which the export writes. The build renders it as `public/_redirects.txt` and `tools/build.py` renames that to `public/_redirects`, which is the name Cloudflare expects. If the map is missing, `tools/build.py` fails the build, so the previous deployment stays live, and the site never goes live without redirects.
- `tools/build_redirects.py` and `tools/check_coverage.py` are the verification side of this. They read the built output and confirm that every redirect points at a page that was actually built. They are not part of the build command and do not need to run on Cloudflare, but running them locally before a cutover is a worthwhile check.
- Cloudflare Pages allows 2,000 static redirects per `_redirects` file. The current map has 286 rules, so there is room, and the export refuses to write a file that would exceed the limit.
- The production canonical URL comes from `baseURL` in `hugo.toml`, which is `https://www.centretowncitizens.ca/`. The script leaves that alone unless `CF_PAGES_URL` is set, so the production site always declares the production domain as its canonical URL.
- Cloudflare sets `CF_PAGES_URL` for every build. The script passes it to Hugo as the base URL, so a preview deployment does not emit canonical tags pointing at the production domain, which would tell search engines that the preview is the real site. In a preview build the canonical therefore points at the preview's own URL, which is correct.
- `public` is the output directory. It is also listed in `.gitignore`, so the build output from a local run is never committed. The build regenerates it either way.

### 5.3 Deploy and check the preview URL

The first build completes in a couple of minutes. When it succeeds, the site is live at `https://website.pages.dev`. Open it and check:

- The homepage renders, with the navigation and the footer.
- The logo and images load.
- Old Squarespace addresses redirect to their new pages. Try `/about`, `/committees`, `/blog_test` and `/homeold`: each should return a 301 to the right page. A 404 on any of them means the redirect map is missing from the build, and the build command is wrong.
- `/admin` loads the Sveltia CMS sign-in page. Signing in does not work yet, because Phase 7 is not done.

### 5.4 Custom domains

Do this before the nameserver change in Phase 6, not after.

1. In the Pages project, open **Custom domains** → **Add a domain**.
2. Add `www.centretowncitizens.ca` **first**. This is the canonical host, matching `baseURL` in `hugo.toml`.
3. Add `centretowncitizens.ca` second.
4. Cloudflare Pages sets up a redirect from the second domain to the first automatically. Confirm that `https://centretowncitizens.ca` lands on `https://www.centretowncitizens.ca` with a 301.
5. If the apex does not redirect to `www` on its own, add the redirect in Cloudflare: **Rules** → **Redirect Rules** → **Single Redirect**, with the incoming host `centretowncitizens.ca`, the target `https://www.centretowncitizens.ca`, and status 301. The free plan allows ten such rules.
6. Cloudflare issues the certificate. It cannot do that until the domain's DNS points at Cloudflare, so the status stays pending until the nameservers change in Phase 6. Watch the status column in the Custom domains table until both domains read **Active**, and expect that to take minutes, occasionally an hour, after the switch.
7. Trigger a new production deployment after the domains are active, so the canonical URL in the built HTML is the production domain.

Adding the domains before the nameserver change is what keeps the cutover clean. If the switch happens first, the domain reaches Cloudflare before Pages knows about it, and visitors get an error page until the custom domains are added.

---

## Phase 6: Change the nameservers at the registrar

This is the point of no return for DNS. Everything before this point is reversible by deleting what you created. This point is reversible only by changing the nameservers back.

### 6.1 Confirm you are ready

- [ ] The Cloudflare zone holds all five MX records with the priorities in the table above.
- [ ] The Cloudflare zone holds the corrected SPF record, with no `+a` in it.
- [ ] The Cloudflare zone holds the DKIM record, with the value copied from the Google Admin console.
- [ ] The Cloudflare zone holds every other record from the d-zone export.
- [ ] The web records point at the new host.
- [ ] Both custom domains are added in the Pages project (Phase 5.4).
- [ ] The second person is on the phone.
- [ ] The current time is inside working hours, with several hours of the working day left.

### 6.2 Replace the nameservers

1. Log in to the d-zone.ca registrar panel for `centretowncitizens.ca`.
2. Find the nameserver or "DNS servers" section for the domain.
3. **Delete** all four current nameservers:
   - `ns1.d-zone.ca`
   - `ns2.d-zone.ca`
   - `ns1.ethicalwebservices.com`
   - `ns2.ethicalwebservices.com`
4. **Add** the two nameservers Cloudflare assigned in Phase 3.
5. Save.

**Do not delete the DNS records at d-zone.** They are the rollback. Leave every A, CNAME, MX and TXT record exactly where it is.

### 6.3 Wait, then watch

Propagation usually starts within minutes and is usually complete within a few hours. Check:

```powershell
Resolve-DnsName -Name centretowncitizens.ca -Type NS -Server 1.1.1.1
```

Expect two records ending in `.ns.cloudflare.com`. Until that happens, the domain is still being served by d-zone and the old site is still live, which is a safe state.

Check every ten minutes. Thirty seconds is too often. When the NS lookup shows Cloudflare, the switch has happened.

### 6.4 Check mail first, before the website

Run the mail checks in [Phase 8](#phase-8-verification-checklist) now, even though the website may not be ready. If mail is broken, this is the moment to roll back, while the cause is still obvious.

---

## Phase 7: Sveltia CMS authentication

Sveltia CMS is the MIT-licensed, free, actively maintained successor to Decap CMS. It is a browser form that commits content to the Git repository, and Cloudflare Pages rebuilds the site from the commit. It has no user limit, no project limit and no paid tier.

### 7.1 Fill in the CMS config

The config file is `static/admin/config.yml` in the site repository. Two values are placeholders and both must be filled in before go-live.

```yaml
backend:
  name: github
  repo: centretown-cca/website
  branch: main
  base_url: https://sveltia-cms-auth.YOUR-SUBDOMAIN.workers.dev
```

- `repo` is currently `centretown-cca/website`. If the organisation and repository names differ from these, change it to the real values, in the form `organisation/repository`.
- `base_url` is currently commented out. Uncomment it and set it to the authenticator URL from whichever route you choose below.

After editing, commit and push. The change rebuilds the site and the CMS picks it up within a minute.

### 7.2 Route 1: the Sveltia CMS Authenticator as a Cloudflare Worker (recommended)

The upstream project is `sveltia/sveltia-cms-auth`, a small stateless OAuth relay. It signs editors in with GitHub and hands the CMS a short-lived token. No editor ever sees or handles a token.

This is the recommended route because every editor gets a one-click GitHub sign-in, and no personal access token has to be created, copied, pasted, stored or revoked.

**Step 1: create the GitHub OAuth app**

1. GitHub → click your avatar → **Settings** → **Developer settings** (bottom of the left column) → **OAuth Apps** → **New OAuth App**.
2. Application name: `Centretown CCA CMS`.
3. Homepage URL: `https://www.centretowncitizens.ca`.
4. Authorization callback URL: `https://sveltia-cms-auth.YOUR-SUBDOMAIN.workers.dev/callback`. The host must be the worker hostname, not the website domain, and the path must be exactly `/callback`. GitHub matches the callback URL exactly, so a trailing slash or a different path is rejected.
5. **Register application**. The client ID is shown. The client secret is shown once, immediately after registration.

**Step 2: deploy the worker**

Install the Cloudflare Wrangler CLI if it is not already on the machine, then:

```
git clone https://github.com/sveltia/sveltia-cms-auth
cd sveltia-cms-auth
npm install
npx wrangler login
npx wrangler deploy
```

Wrangler asks which Cloudflare account to deploy to, and prints the worker hostname when the deploy finishes. That hostname is `sveltia-cms-auth.YOUR-SUBDOMAIN.workers.dev`.

**Step 3: set the secrets**

The client ID and secret go in as encrypted secrets on the worker, never in the repository and never in a document.

```
npx wrangler secret put GITHUB_CLIENT_ID
npx wrangler secret put GITHUB_CLIENT_SECRET
```

Each command prompts for the value and encrypts it before storing it. The equivalent in the dashboard is **Settings** → **Variables and Secrets** → **Add** → type **Secret**.

**Step 4: set the scopes**

In the GitHub OAuth app, open **Permissions and scopes**. Give the app read and write access to repository contents. Add workflow access only if you later want CMS edits to trigger GitHub Actions workflows.

Be clear about what this scope means: an OAuth app with the `repo` scope can reach every private repository the signing-in user can reach, and not only the content repository. That is why the organisation should contain only the site repositories, and why every editor's GitHub account should have write access to `website` and little else.

**Step 5: point the CMS at the worker**

Set `base_url` in `static/admin/config.yml` to the worker hostname, commit, push, and rebuild.

**Step 6: test**

Open `https://www.centretowncitizens.ca/admin`, sign in with GitHub, and confirm you reach the content list. Then create a test news item, publish it, and confirm the site rebuilds and the item appears.

### 7.3 Route 2: Netlify as the OAuth client

Netlify can act as the OAuth client, with no worker of your own to run. This needs no server of the association's own, which is its whole appeal.

The tradeoffs: it needs a Netlify account and a Netlify site for the association, Netlify holds the OAuth client credentials, and Netlify has to stay alive for editors to sign in. You also add a second hosting account to the setup, which is the opposite of the goal of this migration.

To use it, enable Netlify Identity on the Netlify site, register the GitHub OAuth application with Netlify as the client, and point the same `base_url` key in `static/admin/config.yml` at Netlify's identity endpoint.

One value in this runbook must be read from the documentation rather than copied from here: the exact `base_url` value for the Netlify route changes between provider versions. Read it from the Sveltia CMS authentication documentation for the Netlify route, and from the README of the upstream authenticator repository, and use the value they give for your version.

### 7.4 Route 3: personal access tokens (avoid)

The fallback is that each editor creates a GitHub personal access token with write access to the `website` repository and pastes it into the Sveltia sign-in screen.

This is the worst option for non-technical volunteers, and the board should hear that plainly:

- The token is a password. It can be used by anyone who obtains it, to write to every repository the person can write to, until it is revoked.
- Tokens expire, and a token that expires silently stops the editor from publishing, usually discovered by a board member who notices a news post that never appeared.
- Creating a token means navigating a permissions screen that is written for developers, and a volunteer can grant more than they meant to.
- Every volunteer holds a credential for the association's content repository, which defeats the point of keeping the repository in an organisation.

Use this only if the worker deploy fails and there is no time to fix it.

### 7.5 What every editor needs, in all routes

- A GitHub account with two-factor authentication enabled.
- Write access to `centretown-cca/website`. Sveltia will not let a user sign in at all without write access to the content repository, and the sign-in fails with a permissions error in place of a helpful message.

---

## Phase 8: Verification checklist

Run the mail checks first. Run each command in PowerShell on the machine. Use `-Server 1.1.1.1` to query a public resolver directly and skip the local cache; substitute `8.8.8.8` if you want a second opinion. `nslookup` is the alternative if `Resolve-DnsName` is unavailable:

```
nslookup -type=mx centretowncitizens.ca 1.1.1.1
```

If a result looks stale, flush the local cache and try again:

```powershell
ipconfig /flushdns
```

### 8.1 Nameservers

```powershell
Resolve-DnsName -Name centretowncitizens.ca -Type NS -Server 1.1.1.1
```

Expect two records ending in `.ns.cloudflare.com`.

### 8.2 MX records point at Google

```powershell
Resolve-DnsName -Name centretowncitizens.ca -Type MX -Server 1.1.1.1
```

Expect exactly five records:

| Preference | Exchange |
|---|---|
| 1 | `aspmx.l.google.com` |
| 5 | `alt1.aspmx.l.google.com` |
| 5 | `alt2.aspmx.l.google.com` |
| 10 | `alt3.aspmx.l.google.com` |
| 10 | `alt4.aspmx.l.google.com` |

### 8.3 SPF record reads correctly

```powershell
Resolve-DnsName -Name centretowncitizens.ca -Type TXT -Server 1.1.1.1 | Select-String -Pattern "spf1"
```

Expect exactly one line, and expect it to contain `include:_spf.google.com`. It must not contain `+a`. It must not contain `a` as a bare term either.

Confirm the record has not been split or mangled:

```powershell
(Resolve-DnsName -Name centretowncitizens.ca -Type TXT -Server 1.1.1.1).Strings
```

### 8.4 DKIM record resolves

```powershell
Resolve-DnsName -Name default._domainkey.centretowncitizens.ca -Type TXT -Server 1.1.1.1 | Select-String -Pattern "DKIM1"
```

Expect one line containing `v=DKIM1` and `p=`.

### 8.5 The site loads over HTTPS with a valid certificate

```powershell
curl.exe -I https://www.centretowncitizens.ca
curl.exe -I https://centretowncitizens.ca
```

Expect HTTP 200 for the first and HTTP 301 to the canonical host for the second.

Check the certificate itself:

```powershell
curl.exe -v https://www.centretowncitizens.ca 2>&1 | Select-String -Pattern "subject:|issuer:|expire"
```

Expect the subject to name `centretowncitizens.ca` or `www.centretowncitizens.ca`, and the issuer to be Let's Encrypt.

Then open the site in a browser and confirm there is no certificate warning and no browser interstitial.

### 8.6 Both hosts work

- [ ] `https://www.centretowncitizens.ca/` loads the new site.
- [ ] `https://centretowncitizens.ca/` redirects to the `www` host.
- [ ] Old Squarespace addresses redirect to the right new pages, for example `/about`, `/committees`, `/blog_test` and `/homeold`.
- [ ] The admin page at `https://www.centretowncitizens.ca/admin` loads.

### 8.7 Email still arrives

1. From a personal account that is not on this domain, send a message to `ccca@centretowncitizens.ca` and to `president@centretowncitizens.ca`.
2. Confirm both arrive, and are not in the recipient's spam folder.
3. Confirm a reply arrives back at the personal address.

### 8.8 Email still sends, with SPF and DKIM passing

1. From a board member's mailbox, send a message to an address on a different domain, such as a personal Gmail account.
2. Open the received message and show the original headers. In Gmail: **Show details** → **Show original**.
3. In the `Authentication-Results` header, look for:

| Header value | Expected | If it fails |
|---|---|---|
| `spf=` | `pass` | The SPF record is wrong or the sending host is not authorised. See 8.3 and Appendix C. |
| `dkim=` | `pass` | The DKIM record is wrong, or the sending host is signing with a key that is not published. See 8.4. |
| `dmarc=` | `none` or `pass` | There is no DMARC record on this domain, so `none` is expected. A `fail` means a DMARC record exists somewhere that is not in this runbook. |

4. Send a second message from a board mailbox that is configured to send as the association's domain address rather than the Gmail address, and check `spf=pass` on that one too. That is the case where a wrong SPF record actually bites.
5. If anything sends mail directly from `50.28.38.88`, send a test message from that host as well and confirm `spf=pass`.

### 8.9 Check the mail records with Google's own tools

1. Admin console → **Apps** → **Google Workspace** → **Gmail** → **Configure** → open the `Check MX records` tool. Or go straight to `https://toolbox.googleapps.com/apps/dig/`.
2. Run the MX check for `centretowncitizens.ca`. Google confirms it can deliver mail for the domain.
3. Run the DKIM check for selector `default`.
4. In the Admin console, open **Settings** → **Domains** and confirm the domain still shows as verified. A domain that lost its DNS records can show as unverified even though mail is working, and the verification state is what Google uses to decide whether to route mail.

### 8.10 Sign-off checklist

- [ ] Nameservers are Cloudflare.
- [ ] Five MX records with the right preferences.
- [ ] One SPF record, containing `include:_spf.google.com`, no `+a`.
- [ ] One DKIM record at `default._domainkey`, matching the Google Admin console.
- [ ] The site serves over HTTPS with a valid certificate.
- [ ] The apex and `www` both work.
- [ ] Inbound mail to a board address arrives.
- [ ] Outbound mail from a board address shows `spf=pass` and `dkim=pass`.
- [ ] The CMS signs in and a test edit publishes.
- [ ] The board has been told the site moved and the editor training has been scheduled.

---

## Phase 9: Rollback

The old Squarespace site stays live and untouched until the board signs off, so the fallback is a DNS change. No rebuild is needed. Two levels.

### 9.1 When to roll back

Roll back if any of these are true and you cannot fix them within an hour:

- Board mail is bouncing, or is landing in spam, and the mail records look wrong.
- The certificate fails to issue and the site is unreachable.
- The site is serving an error or an empty page for reasons you cannot identify.

Do not roll back for a cosmetic problem, a slow first build, or a broken CMS sign-in. Those do not affect mail.

### 9.2 Level 1: put the old web records back, keep DNS at Cloudflare

Use this when the website is the problem and mail is fine.

1. Cloudflare → **DNS** → **Records**.
2. Edit the apex record so it points at Squarespace again:

| Type | Name | Target | Proxy |
|---|---|---|---|
| A | `@` | `198.49.23.145` | DNS only |
| A | `@` | `198.185.159.145` | DNS only |
| A | `@` | `198.49.23.144` | DNS only |

3. Edit the `www` record:

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | `www` | `ext-cust.squarespace.com` | DNS only |

4. Delete the apex CNAME to `<project>.pages.dev`. Do not leave both an A record and a CNAME at the apex.
5. Wait ten minutes and run the 8.5 and 8.6 checks.

**Do not touch the MX records, the SPF record or the DKIM record during a level 1 rollback.** They live at Cloudflare now and they are what keeps mail working. Touching them is how a web rollback turns into a mail outage.

### 9.3 Level 2: put the whole domain back at d-zone

Use this when mail is broken, or when you want the domain fully back where it was.

1. Log in to the d-zone.ca registrar panel.
2. Delete the two Cloudflare nameservers.
3. Add back all four:

| Nameserver |
|---|
| `ns1.d-zone.ca` |
| `ns2.d-zone.ca` |
| `ns1.ethicalwebservices.com` |
| `ns2.ethicalwebservices.com` |

4. Save.

The Cloudflare zone stops being authoritative the moment the registry accepts the change. The d-zone records were never deleted, so they take over unchanged, including the original MX, SPF and DKIM records.

**Do not delete or edit the Cloudflare email records.** They are harmless while the zone is not authoritative, and they are what you restore from in the next attempt.

5. Wait for propagation, then confirm:

```powershell
Resolve-DnsName -Name centretowncitizens.ca -Type NS -Server 1.1.1.1
Resolve-DnsName -Name centretowncitizens.ca -Type MX -Server 1.1.1.1
```

Expect the four d-zone nameservers and the five Google MX records.

6. Confirm the old site is back and mail is flowing.

### 9.4 After a rollback

- The Cloudflare Pages project keeps deploying. Nothing needs undoing in the repository.
- Leave the GitHub organisation, the repository and the CMS in place. The next attempt is a Phase 4 retry, and no rebuild is needed.
- Write down what went wrong and what the DNS looked like at the time, while you still remember.
- Check whether the Squarespace subscription is still active. A lapsed Squarespace account stops serving the site even with correct DNS.

---

## Appendix A: full record set, Cloudflare Pages

Everything to type into Cloudflare DNS. This is the complete set for the cutover.

| Type | Name | Value | Priority | Proxy | TTL |
|---|---|---|---|---|---|
| MX | `@` | `aspmx.l.google.com` | 1 | DNS only | Auto |
| MX | `@` | `alt1.aspmx.l.google.com` | 5 | DNS only | Auto |
| MX | `@` | `alt2.aspmx.l.google.com` | 5 | DNS only | Auto |
| MX | `@` | `alt3.aspmx.l.google.com` | 10 | DNS only | Auto |
| MX | `@` | `alt4.aspmx.l.google.com` | 10 | DNS only | Auto |
| TXT | `@` | `v=spf1 include:_spf.google.com +mx ip4:50.28.38.88 ~all` | | DNS only | Auto |
| TXT | `default._domainkey` | the DKIM value copied from the Google Admin console | | DNS only | Auto |
| CNAME | `@` | `<project>.pages.dev` | | Proxied | Auto |
| CNAME | `www` | `<project>.pages.dev` | | Proxied | Auto |
| CAA | `@` | `0 issue "letsencrypt.org"` | | DNS only | Auto |

Plus any record from the d-zone export that is not in this table.

Nameservers at the registrar:

| Nameserver |
|---|
| `NAME1.ns.cloudflare.com` |
| `NAME2.ns.cloudflare.com` |

The two CNAME rows only serve the site once the custom domains have been added in the Pages project (Phase 5.4). The five MX rows, the SPF row and the DKIM row carry the mail, and they take effect the moment the nameservers change.

---

## Appendix B: full record set, GitHub Pages

For the lower-DNS-risk option. No nameserver change. The mail records stay at d-zone exactly as they are, and nothing about mail is recreated.

### DNS, entered at d-zone.ca

| Type | Name | Value | TTL |
|---|---|---|---|
| A | `@` | `185.199.108.153` | 300 |
| A | `@` | `185.199.109.153` | 300 |
| A | `@` | `185.199.110.153` | 300 |
| A | `@` | `185.199.111.153` | 300 |
| AAAA | `@` | `2606:50c0:8000::153` | 300 |
| AAAA | `@` | `2606:50c0:8001::153` | 300 |
| AAAA | `@` | `2606:50c0:8002::153` | 300 |
| AAAA | `@` | `2606:50c0:8003::153` | 300 |
| CNAME | `www` | `ORGANIZATION.github.io` | 300 |

Notes:

- `ORGANIZATION.github.io` is the GitHub Pages hostname for the organisation, which is `centretown-cca.github.io`. If the repository is named `website` rather than `<organisation>.github.io`, the site is served from the project path `centretown-cca.github.io/website`, and the `www` CNAME target stays `centretown-cca.github.io`. GitHub routes the request for the custom domain to the project once the custom domain is set in the repository settings. Use the exact hostname shown in the repository's **Settings** → **Pages** panel.
- Set the TTL to 300 on all of these at least a day before the change, so that a rollback is fast.
- The AAAA records are IPv6. GitHub Pages serves over IPv6, so include them.
- The `www` and apex redirect to each other automatically once both are configured and the custom domain is set in the repository settings. Choose which is canonical there and set it.
- Enforce HTTPS from the repository settings, under **Settings** → **Pages**.

### Repository settings for GitHub Pages

| Setting | Value |
|---|---|
| Source | Deploy from a branch |
| Branch | `main` |
| Folder | `/public` |
| Custom domain | `www.centretowncitizens.ca` |
| Enforce HTTPS | On |

### Build for GitHub Pages

GitHub Pages does not run a Hugo build by itself. It serves the static files that are already in the publishing folder. Two ways to fill that folder:

1. **GitHub Actions (recommended).** Add a workflow to the repository that checks out `main`, installs Hugo 0.148.2, runs `python tools/build.py`, and uploads the `public` directory to the `gh-pages` branch. Point **Settings** → **Pages** at the `gh-pages` branch. This is the standard path, it builds on every push, and it gives the editors a preview without any local work.
2. **Commit the built `public` directory.** Set **Settings** → **Pages** to deploy from `main` with the folder `/public`. This works with no workflow at all, but it means someone has to build the site on their own machine and commit the result every time something changes, which is exactly the work the CMS is meant to remove. Use it only as a temporary measure while the workflow is being written.

Whichever you choose, keep `HUGO_VERSION` pinned to `0.148.2` in the build environment. If you keep preview deployments, build them with `python tools/build.py`, which passes Cloudflare's `CF_PAGES_URL` to Hugo so a preview does not claim the production domain as its canonical URL.

Note that `public` is listed in `.gitignore`, so option 2 needs that line removed, or the built output force-added with `git add -f`.

### The redirect map on GitHub Pages

GitHub Pages does not read the `_redirects` file that the build produces. That file format is a Cloudflare Pages and Netlify convention. On GitHub Pages, an unknown address returns the site's `404.html` with an HTTP 404 status, not a 301 to the new page.

Two ways to handle the 286 old Squarespace addresses, in order of preference:

1. **Put a Cloudflare Worker in front of GitHub Pages.** The Worker serves the redirects and forwards everything else to GitHub Pages. The domain's DNS stays at d-zone, so the mail records are untouched, but the DNS now points at Cloudflare's addresses rather than GitHub's, and the Worker does the work. This is the version that preserves the 301 status codes, which is what search engines need. It means running a Cloudflare account alongside GitHub Pages.
2. **Accept a `404.html` that redirects in the browser.** A page at the root of the output directory can redirect the visitor with JavaScript or a meta refresh. This keeps visitors on the right page but returns a 404 status to crawlers, and it costs a fraction of a second per redirect. It is a worse experience for search engines and should be a last resort.

Pick one of these deliberately, before the cutover, and test it. A domain that answers 404 for all 286 old addresses is a real loss of the link equity the old site built up over years.

### Constraints specific to this option

- GitHub Pages does not serve private repositories on the free plan. The repository must be public. If the association wants the content repository private, this option does not work as written.
- The `.ca` domain's DNS and the site's DNS stay at d-zone, in a login separate from the site. The board has to remember that a future DNS change happens in the d-zone panel.
- The Sveltia CMS authenticator still needs a home. The Cloudflare Worker in Phase 7 is still the simplest route, which means a Cloudflare account is needed anyway.

---

## Appendix C: SPF reference and the `+a` trap

### The current record

```
v=spf1 +a +mx +ip4:50.28.38.88 ~all
```

### The recommended final record

```
v=spf1 include:_spf.google.com +mx ip4:50.28.38.88 ~all
```

If, and only if, nothing sends mail directly from `50.28.38.88` any more:

```
v=spf1 include:_spf.google.com +mx ~all
```

### Why the change is required

The `+a` term authorises the A record of the domain itself, so today it authorises Squarespace's addresses, which is harmless because nothing sends mail from them. The moment the apex A record is repointed at Cloudflare Pages, `+a` authorises Cloudflare's addresses instead, and Cloudflare is not authorised to send mail for this domain, so mail sent from the association's own host at `50.28.38.88` would fail the SPF check at the receiving server and be rejected or junked. Replacing `+a` with `include:_spf.google.com` states the Google Workspace authorisation explicitly, so the mail path no longer depends on what the web A record points at, and the web half of the domain can move without touching the mail half.

Two properties of the new string to know:

- It stays well inside the limit of ten DNS lookups per SPF evaluation. `include:_spf.google.com` expands to Google's mail hosts, `+mx` adds one lookup for the MX hosts, and `ip4:` adds none.
- `~all` stays as it is. Do not change it to `-all` in the same edit. `-all` tells receiving servers to reject any mail from a host not listed, and if one legitimate sender is missing from the list, its mail is refused outright. A host that is merely missing from the list ends up in the spam folder, which is recoverable. A refusal is not.

### The `50.28.38.88` decision

`50.28.38.88` reverse-resolves to `green.ethicalhost.ca`, which is a Liquid Web host. It appears to be the association's own outbound mail server, and it is the only non-Google host the current SPF authorises.

Before you remove it, confirm whether anything still sends mail from that address as `centretowncitizens.ca`:

1. Ask whoever administers the ethicalhost or Liquid Web account whether the server sends mail for the domain: a website contact form, a mailing list, a CRM, a WordPress site, a ticketing system, a print or notification service.
2. Look for outgoing mail logs or a non-empty mail queue on that server.
3. Check the Google Workspace Admin console for Google Groups that send announcements to the domain, and for a third-party email sending entry that routes outbound mail to another server.
4. Note what does not depend on this record. The newsletter is sent through Mailchimp, and the links in the site point at `mailchi.mp`, so Mailchimp sends from its own infrastructure and is not covered by this SPF record. Squarespace's own form mail was relayed from Squarespace infrastructure, also not covered by it. The current site's newsletter signup form is disabled in `hugo.toml` (`newsletter_enabled = false`), so the new site sends no mail from its own host.

If anything still sends from `50.28.38.88`, keep the `ip4:50.28.38.88` term and check with the host administrator that the reverse DNS for the address still resolves to a hostname that forward-resolves back to it, since some receiving systems weight that alignment in their scoring.

If nothing sends from it, remove the term. Removing it is the right cleanup, but only after the check above, because removing it while something is still sending means that sender's mail starts failing SPF.

### Never

- Never leave `+a` in the SPF record at the same time as a Cloudflare apex A record.
- Never change the apex A record first and fix the SPF afterwards. Write the corrected SPF record, verify it resolves, then change the A record.
- Never publish two SPF records. One record only, because two cause a permission error.

### The DKIM value

The authoritative DKIM value for this domain, as copied for reference:

```
v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv1du+Eu9KYUFL6jAOx9/DV1qsnXOMi6L1moZvjLqXCx15Fllh1bxN3xthPKMkaRNF9cpK2BGUMxRRKDWyLAHyzilAom4udXHfA0NDngzeNK5h7CW/IEEKIf0BiyALgzoBRfEghJCbBpcDY3CDCZzrDYYj5CHtBDh0O8tVFlzJH8P/c65NdwCTyYGpHHZKMyhce3h7kbhAjg9ddQyzccjnBKWLu1GwqkEi+zcw1kzJXj7xjAMSC7fwkEGoPjdXuVFoGHfHFIjymOio3l1rz6fnWUYZ1wR6DvVpbfvkg8qbssqOcSsAtTRjNzLm8Xvh2BeCD++eO2FP0YYLcBxpIkMCwIDAQAB
```

Do not type this from the document. Read the value from the Google Admin console, in the path given in [Phase 4.1](#41-email-records), and use that. If the two differ, the console is right.

### Optional: DMARC

There is no DMARC record on the domain today. Adding one is optional and can wait until after the cutover. If you do add one, start in monitoring mode only:

| Type | Name | Value |
|---|---|---|
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:dmarc@centretowncitizens.ca` |

`p=none` reports without rejecting anything. Do not use `p=quarantine` or `p=reject` until the reports show that every legitimate sender passes both SPF and DKIM, because those policies start discarding mail from senders you have not found yet.

---

## Appendix D: Cloudflare Pages free tier limits

Every limit the association has to live inside, and how far the site is from it.

| Limit | Free tier | This site |
|---|---|---|
| Builds per month | 500 | A handful. One per content edit, plus one per commit. |
| Files per site | 20,000 | 432 files in the built site, of which 275 are pages. |
| Maximum size of one file | 25 MiB | The largest file is 3.8 MiB. |
| Custom domains per project | 100 | 2. |
| Bandwidth for static assets | Unlimited | No limit to reach. |
| Requests for static assets | Unlimited | No limit to reach. |
| Concurrent builds | 1 | One branch builds at a time. A second push waits for the first. |
| Build timeout | 20 minutes | The Hugo build finishes in seconds. |

Pages Functions, if any are ever added, count against the Cloudflare Workers free tier rather than the Pages tier: 100,000 requests per day and 10 ms of CPU time per request. The site is a static Hugo build with no Pages Functions, so it uses none of that. The CMS authenticator in Phase 7 is a separate Worker with its own allowance, and it handles a handful of sign-ins a week.
