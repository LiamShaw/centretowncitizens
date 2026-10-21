# Editing the CCA website

This guide is for CCA board volunteers and committee members who want to add or change something on the association's website.

You do not need to know how websites are built. Everything in this guide happens in your browser, through a form.

If you would rather not read the whole thing, the section you need is almost certainly one of these:

- Posting a news item: [Posting a news item](#posting-a-news-item)
- Posting a letter or statement: [Posting an advocacy letter or statement](#posting-an-advocacy-letter-or-statement)
- Posting an event: [Posting an event](#posting-an-event)
- Changing a standing page: [Editing a standing page](#editing-a-standing-page)
- Fixing a mistake: [Fixing a mistake on something already published](#fixing-a-mistake-on-something-already-published)

## Before you start

You need two things.

1. A GitHub account. It is free. If you do not have one, create one at <https://github.com>.
2. Write access to the CCA website repository. The repository belongs to the association's GitHub organisation. Email the website maintainer and ask them to add your GitHub username. They will do this for you, it takes a couple of minutes, and there is nothing for you to install.

That is the whole setup. There is no password to create for the website and no access token to paste into a form.

## Where the editor is

Once the new site is live, the editor is at:

```
https://www.centretowncitizens.ca/admin/
```

It is called Sveltia CMS. You may also hear it called "the CMS" or "the admin page". It is a form that sits in front of the website's content, so you never see raw text unless you want to.

The editor is free, open source software. It is maintained by the same people who now maintain Decap CMS, which many associations used before.

## Signing in

1. Open <https://www.centretowncitizens.ca/admin/>.
2. Click the GitHub button, which will read something like `Login with GitHub` or `Authenticate with GitHub`.
3. GitHub will ask whether you agree to let Sveltia CMS access your account. Click the green `Authorize` button.
4. GitHub will send you back to the editor. You are now signed in.

Sign-in is handled by a small program called the Sveltia CMS Authenticator, which runs on Cloudflare. That is why there is no personal access token for you to manage. If you are ever asked to paste a long string of letters and numbers into the editor, stop and ask the maintainer. The association does not need you to do that.

## Your first five minutes

Do this once, before you post anything.

1. Sign in as described above.
2. Look at the list down the left side of the editor. You should see four entries: `News`, `Advocacy`, `Events` and `Pages`.
3. Click `News`. You should see a list of news items that already exist on the site.
4. Click the title of any one of them. A form opens with the item's `Title`, `Date`, `Author`, `Summary` and `Body`.
5. Click `Cancel` or `Close` without changing anything.
6. Tell the website maintainer that you can sign in and see the list. That is your first task done.

If any of those steps does not work, stop there and email the maintainer. Do not try to work around it.

## How publishing works

Every time you press `Publish`, three things happen:

1. The editor writes your changes into a Markdown file in the website's source files. One item is one file.
2. Cloudflare rebuilds the website from those files.
3. The rebuilt site goes live.

Step 2 and 3 take about a minute. The editor confirms your change is saved almost immediately, but the live site catches up a moment later.

This means the content of the website is just text files. If the form ever turns out to be too limited, someone can open the file and edit it directly. That is a fallback, not something you need to worry about now.

## Posting a news item

News items are short announcements: a meeting, a poster, a milestone, an obituary, a notice that something is open.

1. In the editor, click `News` in the list on the left.
2. Click the `Add News` button, or the `+` button. Sveltia asks you to confirm the folder to save into. Choose the `News` folder and click `Add`.
3. Fill in `Title`. This is the headline that visitors see in the list and at the top of the page. Keep it to one line.
4. Fill in `Date`. The date picker handles the format for you. Today is usually right. This is the date the item is filed under, not the date of an event described in it.
5. Fill in `Author`, if you want to be credited. This is optional. Leave it blank and it will be left off the page.
6. Fill in `Summary`. One or two sentences. This is optional, but it is worth doing, because the summary is what shows in the listing pages and in link previews.
7. Fill in `Body`. This is the item itself. Write it in the large text box at the bottom.
8. If you want a picture, use the image button on the `Body` toolbar. It opens the media library, where you can choose `Upload file` and pick a picture from your computer. The picture is copied into the site's own uploads folder and inserted into your text at the cursor. Keep pictures under about 1 MB, otherwise the page loads slowly on phones.
9. Click `Publish`.
10. Wait about a minute, then look at the site to confirm your item appears.

### On formatting

The editor's toolbar does bold, italic, headings and links for you. Type ordinary text in between. Do not paste text from Word, Google Docs or an email. Those programs carry hidden formatting that breaks pages. If you do paste something, paste it as ordinary text first, and then use the toolbar to add bold or headings.

## Posting an advocacy letter or statement

Advocacy items are letters, statements and public positions. They work like news items, with one extra field.

1. Click `Advocacy` in the list on the left.
2. Click the `Add Advocacy` button, or the `+` button. Choose the `Advocacy` folder and click `Add`.
3. Fill in `Title`. For a letter, this is usually the subject line of the letter.
4. Fill in `Date`. Use the date the letter was sent or published.
5. Fill in `Author`, if you want to be credited. Optional.
6. Fill in `Summary`. One or two sentences on what the letter is about. Optional but worth doing.
7. Choose a committee from the `Committee` dropdown. The options are:
   - CCA
   - SEPAW
   - Planning
   - Transportation
   - Greenspace & Sustainability
   - Housing Affordability
8. Fill in `Body`. The full text of the letter, or a summary of it with a link to the PDF.
9. Click `Publish`.

### Choosing the committee

The committee you pick decides how the item is labelled and filtered. Visitors on the advocacy page can filter the list by committee using the buttons across the top of that page. An item with the wrong committee will not show up under the right filter.

Always pick from the dropdown. Do not type your own wording into the box. The filter matches the exact words in the dropdown, so "Housing" will not match "Housing Affordability", and "Greenspace" will not match "Greenspace & Sustainability".

### More than one committee

The dropdown lets you pick several committees, so a letter that concerns more than one can be labelled with all of them. Hold the control key while you pick the second one, or use the same key your keyboard uses for multiple selections.

The site itself has always been able to carry more than one committee on an item, and the form now matches that.

## Posting an event

Events are meetings, workshops, festivals and public conversations.

1. Click `Events` in the list on the left.
2. Click the `Add Events` button, or the `+` button. Choose the `Events` folder and click `Add`.
3. Fill in `Title`. The name of the event, as you would say it out loud.
4. Fill in `Starts`. This is the date and time the event begins. The date picker handles the format.
5. Fill in `Ends`, if the event has an end time. Optional. It is shown as the finishing time next to the start time.
6. Fill in `Location`. Where the event is happening, for example "Dundonald Park, Ottawa". Optional.
7. Fill in `Image`, if you have a poster. Optional. The image appears at the top of the event page. Keep it under about 1 MB.
8. Fill in `Summary`. One or two sentences on what the event is. Optional but worth doing.
9. Fill in `Description`. The full details: what happens, who it is for, whether to bring anything, whether it is accessible. This is the text that appears on the page.
10. Click `Publish`.

### Dates decide where an event appears

This is the part that catches people out, so read it twice.

- An event with a `Starts` date in the future appears under `Upcoming Events` on the home page and at the top of the events page.
- An event with a `Starts` date in the past appears further down the events page, under `Past Events`. It drops off the home page on its own.
- An event with no `Starts` date will not appear in either list. The start date is what the site sorts on, so an event without one is invisible.

Always check the date before you publish. If an event you expected to see is missing, the start date is the first thing to look at. Also check that you have not set a start time of 12:00 AM by accident, which will sort it into the past.

## Posting a committee's own news

Each committee has its own section of the site with its own list of posts: Heritage, Housing Affordability, Planning, Transportation, Trees and Greenspace, Safety and Emergency Preparedness (SEPAW), and Seniors.

To add a post to one of these:

1. Click `Committees` in the list on the left.
2. Click the `Add Committees` button, or the `+` button.
3. Choose the committee's folder, for example `heritage`, and click `Add`.
4. Fill in `Title`. The name of the report, letter or announcement.
5. Fill in `Date`. The date it was written or published.
6. Fill in `Author`, if you want to be credited. Optional.
7. Fill in `Summary`. One or two sentences. Optional.
8. Fill in `Body`. The full text, or a summary with a link to a PDF.
9. Click `Publish`.

The post appears on that committee's page, under its own heading. Committee pages also carry a short description of what the committee does, which the maintainer sets. If the description is out of date, mention it to the maintainer.

## Editing a standing page

Standing pages are the pages that stay on the site and get updated regularly: About, Board of Directors, CCA in the News, Climate Change, Contact, Donate, Editorial Guidelines, Get Involved, Become a Member, Newsletter, Sponsorship, Volunteer and the Climate Change report.

They all live in one list called `Pages`.

To change the board list, for example:

1. Click `Pages` in the list on the left.
2. Find `Board of Directors` in the list and click it.
3. The form opens with a `Title` field and a `Body` field.
4. Edit the `Body`. This is the list of names and roles, written in Markdown.
5. Click `Publish`.

Editing a standing page works exactly like creating one, with one difference: you are changing a file that already exists. The address of the page does not change when you edit it.

The Markdown used for these pages is plain. A board list looks like this in the file:

```
## Board of Directors

**Mia Jensen**, President

**Sam Okonkwo**, Vice-President
```

If you are not comfortable with that, keep the existing format and change only the names, or leave the page to someone who is. The format is not checked automatically, so it is better to make a small, careful change than to rewrite the whole page.

## Fixing a mistake on something already published

There is no special process for this. You edit the item the same way you edited it the first time, and press `Publish` again.

1. Find the item. News items are under `News`, letters under `Advocacy`, events under `Events`, standing pages under `Pages`.
2. Click it.
3. Fix the text.
4. Click `Publish`.
5. Wait about a minute and check.

The site keeps the history of every change, so nothing is lost. The change you see on screen replaces the old one, and the old version is still in the repository's history if it needs to be recovered.

Two things to be careful about:

- If you change the `Title` of something already published, its address on the website may change too. Old links from council documents, press coverage and social media would then break. If a title needs rewording, ask the maintainer first.
- Do not delete an item that someone else created, even if it looks wrong or out of date. Ask the maintainer or the committee chair first. A deleted item cannot be unlinked, and a deleted letter may be one the association is still relying on.

## Checking a change before it goes live

Cloudflare Pages builds a preview for every change that is pushed to the repository, not just for the ones that go straight onto the live site. A maintainer can open that preview and check your change before it is relied on.

If you would like your change checked before the board sees it, say so in your email to the maintainer. They can open the preview build and reply.

To check your own work, the simplest method is:

1. Publish.
2. Wait about a minute.
3. Open the page on the live site.
4. If what you see is not what you expected, use Ctrl and F5 together (or Cmd and F5 on a Mac) to force a fresh copy, in case your browser is showing a cached version.

## If your change does not appear

Work through this list in order.

1. Wait a minute or two. The rebuild is not instant.
2. Check that you published. Closing the editor without publishing leaves the website unchanged. A published item shows a confirmation message in the editor.
3. Check the build. The website's source files are correct, but if the build itself fails, nothing goes live. The website maintainer can see this in the Cloudflare Pages dashboard.
4. Check the committee field. If you published an advocacy item with a committee chosen, this is the most likely cause of a failed build. See the note in the advocacy section above.
5. Check the start date on an event. An event whose start date is in the past will not show under `Upcoming Events`, and an event with no start date will not show at all.
6. Check the address. Look at the address bar and make sure you are looking at the page you edited and not a different one.
7. Email the website maintainer. Say what you published, roughly when, and what you expected to see. That is enough for them to find it.

If something is wrong on the live site and it is not urgent, leave it and let the maintainer deal with it. If it is urgent, for example a wrong date on an event that people may turn up to, email the maintainer and the committee chair.

## Things to be careful about

- Use the `Committee` dropdown, and leave the wording to it. The filter matches the dropdown words exactly.
- Check the `Starts` date on every event before you publish. It decides whether the event shows as upcoming or in the past archive.
- Do not delete a post you did not create without asking first.
- Do not paste formatting from a word processor. Paste as ordinary text and use the Markdown toolbar instead.
- Keep images under about 1 MB, so the site loads quickly on phones.
- Write summaries that make sense on their own. People often see the summary before the full text, in a link preview or in a search result.
- Be careful with the `Title` of something already published, because it can change the address of the page.
- If you are unsure, publish nothing and ask. A question costs nobody anything.

## Who to contact

The website maintainer is the person the board has put in charge of the site. They handle sign-in problems, failed builds, deleted content and anything the editor cannot do.

If you do not know who the current maintainer is, ask the board chair.

For general site questions, use the association's own contact address, <ccca@centretowncitizens.ca>.

## A note on the old site

The old Squarespace site stays online until the board has signed off on the new one. Both sites are reachable during the handover.

Every address on the old site redirects to the right place on the new one, so links in council documents, press coverage and social media keep working.
