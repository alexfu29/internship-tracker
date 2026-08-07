# Internship Tracker

A mobile-first, no-build tracker for the Summer 2027 internship hunt: log a cold
contact or an application in one tap, mark replies and meetings from a dropdown,
and get a **red flag when someone you contacted has been silent for 7 days**.

Same shape as [camino-a-madrid](https://github.com/alexfu29/camino-a-madrid): a
single static `index.html` (vanilla HTML/CSS/JS, no frameworks, no build step),
`localStorage` as the real store, and optional two-way sync to this repo's
`data/log.json` through a fine-grained GitHub token. Sync failures show up as a
loud red banner — they never silently swallow your data.

## THE ONE URL

```
https://alexfu29.github.io/internship-tracker/
```

Pin it to your phone's home screen (Share → Add to Home Screen); it launches
full-screen like a native app.

## What it tracks

Two logs, two tables.

**Cold contacts** — who you reached out to, and how:

| Field | Notes |
|---|---|
| Who | required — the person's name |
| Company / their role | optional |
| How you reached out | Email · LinkedIn · Other |
| Their contact handle | label follows the channel — see below |
| Their email | optional; shown on the nudge row so you can copy it |
| Date contacted | defaults to today |
| Note | optional |

The contact-handle field **relabels itself from the channel** you pick, live, in both
the logging form and the edit form:

| Channel | Label |
|---|---|
| Email | Their email |
| LinkedIn | LinkedIn profile |
| Other | Email or profile link |
| Phone *(legacy rows only)* | Phone number |

It's a plain text field with **no format validation**, so a LinkedIn URL, a phone
number or a bare handle all go in without the browser rejecting it for not looking
like an email address. Under the hood it's still one stored field, so switching the
channel relabels it without moving or clearing what you already typed.

**Companies** — every company you've looked at, applied or not:

| Field | Notes |
|---|---|
| Company | required |
| **Applied yet?** | **Not yet** (default) or **Applied** — flip it later from "Update someone" |
| Role | optional |
| Date | defaults to today |
| Careers page or posting link | optional; becomes a tappable link |
| Note | optional |

The point is that a company enters the list the moment you *notice* it, not when
you apply. Add it with **Not yet**, and flip the toggle once you've actually
applied — which re-stamps the date, so "waiting N days" counts from the
application rather than from when you bookmarked it.

## Copy AI prompt

Above the Companies table, whenever anything is still unapplied, there's a
**📋 Copy AI prompt (N not applied)** button. It builds a prompt listing exactly
those companies — with the role, link and note you saved as hints — and asks an AI
to check each company's careers page for mechanical/biomedical engineering
internships. Paste it into Claude (or anything with web access).

The prompt is written against the two ways this task actually fails: the model
answering from memory instead of opening the page, and the model inventing a
plausible-looking job URL. So it pins the company's own careers site as the source
of truth, forbids constructing links, and makes **"NONE FOUND" an explicitly
correct answer** so there's no pressure to pad the list. It also carries your real
search parameters (paid, Summer 2027, Boston/NYC, sophomore/junior-eligible) and
asks it to flag citizenship requirements, since some of these are
defense-adjacent.

The whole prompt is editable in **Settings → AI research prompt**, with the same
Done / Reset pattern as the email drafts. `{companies}` is where your numbered list
gets substituted. Delete it and the list is **appended at the end** rather than
dropped, so the prompt can't end up with nothing to research — and the first tap of
Done tells you it happened.

The stat row counts **Applied** out of companies tracked, and the reply rate is
measured only against things you actually sent — a bookmarked company can't reply,
so it never drags the percentage down.

Both kinds carry the same two follow-up states: **replied** (yes/no) and
**meeting** (a date). Set either from the "Update someone" dropdown, which lists
every person and company you've logged, grouped. Tapping any table row jumps
straight to that entry in the dropdown, and **Done** closes the panel when you've
finished with that person.

Every status control in that panel saves the moment you tap it, so **Done is an
exit, not a save** — there is no way to lose an edit by closing without it.

**✎ Edit contact details / ✎ Edit company details** opens every field for editing —
name, company, role, how you reached out, email, date, link, note. Field labels are
word-for-word the ones on the logging form, so a field never means one thing when
you add it and something else when you fix it. The company date label follows the
Applied toggle: **Date applied** when applied, **Date added** when not.

Editing is a distinct mode with **Save changes** and **Cancel** — Cancel discards,
and a missing name or company or an invalid date blocks the save with a message
rather than writing a broken row. Editing fields never touches status: the Applied
flag, replies, meetings and reminder history all survive a rename.

If an older contact holds a channel that's no longer offered (`In person`, `Phone`),
the edit form keeps it as a selected option instead of silently rewriting it.

## The 7-day rule

A contact goes red when **all** of these hold: no reply, no meeting booked, not
closed, and 7+ days since the last time you touched it. Those rows collect in a
red **"Needs a nudge"** card at the top of the screen with three buttons:

- **📋 Copy draft** — puts your follow-up wording on the clipboard, filled in with
  this person's details. Paste into your mail app, tweak, send. Copying is *not*
  sending, so it deliberately leaves the reminder state untouched.
- **Reminder sent** — a **toggle**. On, it logs today and **restarts the 7-day
  clock**, so a contact you're actively chasing goes quiet for another week
  instead of nagging forever. Tap it again to undo (tapped it by mistake, or they
  replied before you actually sent). The reminder count and last-reminder date
  show on the row.
- **They replied** — marks it replied, clears it from the list.
- **Drop it** — closes the entry; it stops being chased and dims in the table.

Nothing is emailed for you. The app flags who needs a follow-up; you send it.

Applications deliberately **do not** get a red flag — a quiet application at day
7 is normal, and flagging it would train you to ignore red. They show a plain
"Waiting N days" instead.

## Email drafts

Both draft templates live in **Settings → Email drafts**, so the wording is in the
same app as the reminder — you never navigate somewhere else to find it. Two
templates: **first-contact** and **follow-up**. Both ship with real, sendable
wording (BU mech-e, biosensors/HMI, Summer 2027); edit them to taste, then hit
**Done editing drafts** — that saves and closes the drawer in one tap. **Reset to
defaults** puts the built-in wording back.

Where the copy buttons are:

| Button | Where | Uses |
|---|---|---|
| 📋 Copy outreach draft | on the Cold contact form | the name/company you've *just typed* — copy, send, then Save |
| 📋 Copy draft | on each red nudge row | that person's follow-up |
| 📋 Copy follow-up draft | in "Update someone" | the selected contact's follow-up |

Placeholders substituted automatically:

| | |
|---|---|
| `{first}` | first name only — for "Hi Sam," |
| `{name}` | full name |
| `{company}` `{role}` `{channel}` | as logged |
| `{date}` | date you first contacted them (e.g. Jul 25) |
| `{days}` | days since your last contact or reminder |

A placeholder with **no value on file** comes through as a visible `[company]`
rather than an empty gap — you notice `at [company]` before sending; you don't
notice `at .`.

A typo like `{Company}` can't quietly ship as literal text either: the first tap
of **Done** names the unrecognised placeholder and keeps the drawer open so you
can fix it; a second tap accepts it as-is. Either way your text is already saved,
so nothing you typed is at risk while it warns you.

Templates are stored per-device in `localStorage`, **not** in the synced log — so
rewriting your drafts never touches contact data, and it also means you re-enter
them on each device.

If the browser blocks clipboard access, the app doesn't pretend it worked: it
shows the draft in a red panel with the text selected so you can copy it by hand.

## Status colors

Statuses come from a fixed, contrast-validated status palette and always ship as
a **colored dot plus words** — never color alone, so they survive colorblindness,
grayscale, and a glance in bright sun:

| Dot | Means |
|---|---|
| red | needs a nudge (7+ days silent) |
| amber | company tracked but **not applied yet** — a to-do, not a waiting game |
| green | replied, or a meeting is set |
| gray filled | waiting, under 7 days |
| gray outline | closed |

Light and dark mode both follow the OS setting.

## Setup: the GitHub sync token

Sync is optional — the tracker works fully offline via `localStorage` with zero
setup. To sync between your phone and laptop through `data/log.json`:

1. Go to **github.com/settings/personal-access-tokens → New token**.
2. **Scope it to only this repository** (`internship-tracker`), not all repos.
3. Under **Repository permissions → Contents**, set **Read and write**. Leave
   everything else "No access."
4. Copy the token (`github_pat_…`).
5. Open the tracker → gear icon → paste it into **Settings** → Save.

Do this on every device. The token lives only in that device's `localStorage`
(key `intern-pat`) and is never sent anywhere except `api.github.com`. Owner and
repo are autodetected from the `github.io` URL.

## How sync resolves conflicts

Every contact and application carries its own `updated` timestamp, and merges are
**per-entry last-write-wins**: edit different entries on two devices and both
edits survive. Deletes write a `deleted: true` tombstone rather than removing the
key, so deleting on your phone isn't undone by the next sync from your laptop.

Pushes are debounced 10 seconds (each push is a real commit) and flushed when you
background the app.

## Recovery playbook

- **Red sync banner?** The app is still working entirely locally — nothing you
  logged is lost. Fix the token in Settings, then hit **Test sync**.
- **Lost the token?** Generate a new one (steps above), paste it on each device,
  revoke the old one on GitHub.
- **New device?** Open the URL, gear icon, paste the token — it pulls and merges.
- **No token, ever?** Use **Export JSON** / **Import JSON** in Settings as a
  manual backup path. Import *merges*, it doesn't overwrite.
- **Accidentally deleted something?** Restore from an exported JSON, or edit
  `data/log.json` in the repo and flip that entry's `deleted` back to `false`
  (bump its `updated` so it wins the merge).
- **Want closed entries back in the tables?** Settings → "Show closed entries."

## A note on `data/log.json` being public

GitHub Pages on the free tier wants a public repo, so `data/log.json` is publicly
readable — and unlike the Spanish tracker, **this file holds real names, email
addresses, companies, and your notes**. That's the tradeoff for zero-backend,
zero-cost sync.

Two ways out if that's not acceptable:

1. **Don't use the token.** Skip sync entirely; data stays in `localStorage` on
   each device, and `data/log.json` in the repo stays empty. Use Export/Import to
   move it around.
2. **Make the repo private.** GitHub Pages on private repos needs a paid plan,
   but you can also just open `index.html` from a local clone — everything except
   sync works from `file://`.

If you sync to a public repo, keep notes free of anything you wouldn't post
publicly.

## Debugging

`?d=YYYY-MM-DD` renders the app as if it were that date — the fastest way to see
the 7-day nudge fire without waiting a week:

```
https://alexfu29.github.io/internship-tracker/?d=2026-08-20
```
