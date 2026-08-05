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
| How you reached out | Email · LinkedIn · In person · Phone · Other |
| Their email | optional; shown on the nudge row so you can copy it |
| Date contacted | defaults to today |
| Note | optional |

**Applications** — where you applied:

| Field | Notes |
|---|---|
| Company | required |
| Role | optional |
| Date applied | defaults to today |
| Posting link | optional; becomes a tappable link |
| Note | optional |

Both kinds carry the same two follow-up states: **replied** (yes/no) and
**meeting** (a date). Set either from the "Update someone" dropdown, which lists
every person and company you've logged, grouped. Tapping any table row jumps
straight to that entry in the dropdown.

## The 7-day rule

A contact goes red when **all** of these hold: no reply, no meeting booked, not
closed, and 7+ days since the last time you touched it. Those rows collect in a
red **"Needs a nudge"** card at the top of the screen with three buttons:

- **Reminder sent** — logs today and **restarts the 7-day clock**, so a contact
  you're actively chasing goes quiet for another week instead of nagging forever.
  The reminder count and last-reminder date show on the row.
- **They replied** — marks it replied, clears it from the list.
- **Drop it** — closes the entry; it stops being chased and dims in the table.

Nothing is emailed for you. The app flags who needs a follow-up; you write and
send it yourself.

Applications deliberately **do not** get a red flag — a quiet application at day
7 is normal, and flagging it would train you to ignore red. They show a plain
"Waiting N days" instead.

## Status colors

Statuses come from a fixed, contrast-validated status palette and always ship as
a **colored dot plus words** — never color alone, so they survive colorblindness,
grayscale, and a glance in bright sun:

| Dot | Means |
|---|---|
| red | needs a nudge (7+ days silent) |
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
