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
| Who | the person's name (not required) |
| Company / their role | optional |
| How you reached out | Email · LinkedIn · Other |
| Their contact handle | label follows the channel — see below; shown on the nudge row so you can copy it |
| Date contacted | prefilled with today |
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
| Company | no longer required — see "No field is enforced" |
| **Applied yet?** | **Not yet** (default) or **Applied** — flip it later from "Update someone" |
| **Cold emails sent?** | **Not yet** (default) or **Sent** — did you email anyone there |
| **Connection made?** | **Not yet** (default) or **Connected** — did that outreach actually land |
| Role | optional |
| Date | defaults to today |
| Careers page or posting link | optional; becomes a tappable link |
| Note | optional |

The point is that a company enters the list the moment you *notice* it, not when
you apply. Add it with **Not yet**, and flip the toggle once you've actually
applied — which re-stamps the date, so "waiting N days" counts from the
application rather than from when you bookmarked it.

### The three company toggles are independent

**Applied**, **Cold emails sent** and **Connection made** are three separate
questions and none of them implies another. You can email a company you never end
up applying to, land a conversation somewhere whose posting isn't open yet, or
apply cold to a place you know nobody at. So each is its own toggle rather than
one "progress" stage, and flipping one never moves the others.

Only **Applied** re-stamps the date and feeds the stat row, the "Copy AI prompt"
list, and the reply rate. The other two are pure flags: they don't touch the date
(the companies table has no 7-day nudge to restart) and they don't change the
status chip.

Where they show up:

- On the **Add company** form, as two segmented controls defaulting to **Not yet**.
- In **Update someone**, as **Cold emails sent** / **Connection made** buttons that
  toggle — tap once to set, tap again to undo a mis-tap, plus a pair of chips with
  the state spelled out in words.
- In the companies table, as **two small dots** next to the company name.

Both states always render — never just the positive. Showing nothing for "no" would
be ambiguous between *not yet* and *this row predates the flag*, and "who have I not
emailed yet" is the exact question you're scanning the table to answer.

The negatives are **gray, not amber**. They're a fact to read, not an alarm — amber
and red stay reserved for things actually demanding action, so they keep their bite.

In the table the words are compressed to dots to keep the row one line tall, which
is a real accessibility cost, so it's paid back three ways: each dot carries its
full text as a **tooltip**, the same text is there for **screen readers**, and a
**legend** sits under the table (`● done · ○ not yet · 1st dot = cold email, 2nd =
connection`). The meaning is compressed, not thrown away. The update panel still
spells both out in words, so there's always somewhere the state is unambiguous.

These are per-*company*. The cold-contact table is still where individual people
and the 7-day nudge live; **Cold emails sent** on a company is the coarse "have I
approached this place at all" answer you want when scanning the list.

A company row created before these toggles existed has neither flag set, which is
read as **not yet** for both — unlike `applied`, no old row ever meant otherwise.

### One line per company

A company row is exactly **one line tall** and reads left to right:

```
Delsys  Wearable EMG Intern  ●○   Aug 9   ● Not applied   🔗 Open ↗
└ name and role ─────────────┘ dots  └ date, status, link — one compact group ┘
```

Nothing stacks. Every real column shrinks to its content and an empty trailing
column soaks up whatever width is left, so the row stays packed together on the
left instead of the link being flung to the right-hand edge with a stretch of dead
space in front of it. Every cell is `nowrap`, so when it doesn't fit the table gets
**wider, never taller**.

The page is capped at **640px** — sized to what the row actually needs (~500px)
rather than to the screen. Stretching it wider only spread dead space across the
card.

On a phone the row still has to fit, so under 620px the company name truncates with
an ellipsis, the gutters tighten, and the link drops to a bare 🔗. That's deliberate:
a shortened name beats having to scroll sideways to find out whether there's a link.
Tap the row to see the full name and role in the update panel.

### The posting link, one tap away

If a company has a **Careers page or posting link**, the row carries a link straight
to it as the last column, so you don't have to select the company just to get at
the URL. It opens in a new tab, and tapping it does *not* also select the row — the
row's tap-to-select is suppressed over the link. The link's tap target is padded to
most of the row height, since it's competing with a row that does something else
when you tap it.

Because nothing is enforced, a link can be saved as a bare `draper.com/careers`
with no `https://`. That's normalised **at render time only** — the scheme is added
to the link you tap, and what you typed is left exactly as you typed it. A value
carrying some other scheme isn't made clickable at all.

## Per-entry workspaces

Every contact and every company has **its own workspace** — a bigger, free-form
notes area that belongs to that one entry. Open the entry and tap the **📝** next to
its name.

It opens as a **small popup on the right**: 340×400, deliberately not a full-height
drawer and not a takeover. The tables stay live and readable behind it — no dimming
— and the page underneath never moves, so nothing reflows while you write.

- **Saves as you type**, debounced, straight onto that entry. The label reads
  `Saving…` then `Saved`.
- Pending text is **flushed on the way out** — closing the popup, switching entries,
  or backgrounding the app all commit what you typed, so a mid-sentence debounce
  can't drop it.
- If the entry has since been deleted (say, on another device), it says
  `⚠ Entry is gone — copy your text out` rather than claiming a save that didn't
  happen.
- The **📝 button shows a dot** when there's already something written in there, so
  you can tell without opening it.
- **📋 Copy** puts the whole thing on the clipboard.
- Tapping the same 📝 again puts it away, as does **✕** or **Escape**.

The workspace **does not follow the dropdown**. Selecting a different entry closes
it (after saving) instead of re-pointing at someone else — that's how you'd end up
typing notes onto the wrong person.

This is separate from the form's short **Note** field, which stays where it is. The
note is the one-line "how did this go"; the workspace is where you draft the actual
email or keep a running log.

**It lives on the entry, so it syncs** like every other field, and it's deleted when
the entry is. That also means it lands in `data/log.json` — see the note about that
file being public if you sync to a public repo.

## The logging form

**＋ Cold contact** and **＋ Add company** open a **centred dialog**.

The form used to expand inline underneath the two buttons, which shoved the tables
down the page every time you opened it. Now it opens over the middle of the screen,
where you're already looking, and the page behind it never reflows.

- The header stays put while the body scrolls, so **Save** is never stranded
  off-screen in a long form.
- The **Note** field keeps its place at the bottom of the form.

Both buttons drive the same dialog and it only ever shows one form: tapping the
other button swaps the contents and retitles the header. Close it by tapping the
same button again, the **✕**, **Escape**, or by tapping outside it. Saving closes it
for you.

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

## Opening an entry

**Tap any row and it opens in place — right underneath itself.** The page does not
scroll, the row does not move, and you keep your place in the table. Editing fields,
flipping a toggle and saving all happen there too; none of them throw you back to
the top.

Under the hood it's one panel that gets physically moved into a detail row beneath
its own entry, so the inline version is identical to what you'd get anywhere else —
same fields, same buttons, same behaviour.

The **Update someone** dropdown still lists everything you've logged, grouped, for
reaching an entry that isn't on screen. Picking from it does scroll — but only when
the row isn't already in front of you.

If the selected entry has no visible row (a closed entry with "show closed" off),
the panel falls back to sitting in the dropdown's card rather than disappearing.

### The buttons

They're split into two groups, because they answer two different questions:

| Group | Shape | Examples |
|---|---|---|
| **Status** | a fact, with a ✓ when it's true | `Applied` · `Cold emails` · `Connection` · `Replied` · `Reminder sent` |
| **Actions** | a verb | `✎ Edit` · `📋 Copy draft` · `Close` · `Delete` · `Done` |

Every label is short enough to sit on one line at its natural width, and the buttons
wrap like text instead of being stretched into a fixed two-column grid — that grid
was what forced long labels to wrap *inside* the button and turned the panel into a
wall of half-legible text. Each label now says what it does on its own.

Both kinds of entry carry the same two follow-up states: **replied** (yes/no) and
**meeting** (a date). **Done** closes the panel when you've finished with that entry.

Every status control in that panel saves the moment you tap it, so **Done is an
exit, not a save** — there is no way to lose an edit by closing without it.

**✎ Edit contact details / ✎ Edit company details** opens every field for editing —
name, company, role, how you reached out, email, date, link, note. Field labels are
word-for-word the ones on the logging form, so a field never means one thing when
you add it and something else when you fix it. The company date label follows the
Applied toggle: **Date applied** when applied, **Date added** when not.

Editing is a distinct mode with **Save changes** and **Cancel** — Cancel discards.
Editing fields never touches status: the Applied / Cold emails sent / Connection
made flags, replies, meetings and reminder history all survive a rename.

If an older contact holds a channel that's no longer offered (`In person`, `Phone`),
the edit form keeps it as a selected option instead of silently rewriting it.

## No field is enforced

**Nothing is required and no field validates its format.** No red "this is
required" message, no browser rejecting a value for not looking like an email or a
URL. Paste a LinkedIn URL into the handle field, a bare `draper.com/careers` with no
`https://` into the link, or save a completely empty row — it all goes in.

The tradeoff is that gaps have to be *visible* instead of prevented, so:

- A row with no name or no company lists as **(no name)** / **(no company)** rather
  than a blank line you can't select or delete.
- A row with no date shows an amber **No date** chip. It doesn't pretend the date is
  today, and it never fires the 7-day reminder — there's nothing to count from. Fill
  the date in and it starts behaving normally.

Dates are still a date picker rather than free text, since the 7-day rule is
computed from them.

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
| amber | **no date** on the row, so the 7-day clock can't run |
| green | replied, or a meeting is set |
| gray filled | waiting, under 7 days |
| gray outline | closed; or a company flag still at **no** (no cold email, no connection) |

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
