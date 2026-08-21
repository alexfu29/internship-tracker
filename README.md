# Internship Tracker

A mobile-first, no-build tracker for the Summer 2027 internship hunt: log a cold
contact or an application in one tap, mark replies and meetings from a dropdown,
and get a **red flag when someone you contacted has been silent for 7 days**.

Same shape as [camino-a-madrid](https://github.com/alexfu29/camino-a-madrid): a
single static `index.html` (vanilla HTML/CSS/JS, no frameworks, no build step),
`localStorage` as the real store, and optional two-way sync to this repo's
`data/log.json` through a fine-grained GitHub token. Sync failures show up as a
loud red banner — they never silently swallow your data.

## The shape of it, in one screen

Everything is in **`index.html`** — one file, ~5,400 lines, all JS in one IIFE
with numbered section banners (`4. DERIVED STATE`, `6C. FIND CONTACTS`,
`6D. SEND QUEUE`, `7. SYNC`). Beside it sits **`sw.js`**, the service worker
that keeps a copy of that file on your device so the app opens with no
connection. The only other code is `agent/`, which is **optional and off by
default**.

| Where | What |
|---|---|
| `intern-data` | contacts + companies. The synced one — this is `data/log.json` |
| `intern-settings` | templates, prompts, reader/search config. **Never synced** |
| `intern-outbox` | the staged send queue. Device-local; holds message text |
| `intern-pat`, `intern-ai-key`, `intern-gemini-key` | secrets, per device, never synced |

Four things it does beyond logging, each with its own section below:

1. **The 7-day rule** — who's gone quiet, and the red card that says so.
2. **⚡ Auto-populate** — paste a LinkedIn profile, get a filled-in contact.
3. **🔍 Find contacts** — find BU alumni at a company, plus an engineer doing the
   work you want to do, verified before they land.
4. **✉ Send queue** — stage a batch of personalized messages and work down it.

Three rules the code keeps coming back to, worth knowing before changing any of
it:

- **A gap is shown, not prevented.** Nothing is required and nothing validates its
  format; instead missing things are visible — `(no name)`, an amber `No date`
  chip, a literal `[company]` left in a draft.
- **Never assert what wasn't established.** A bucket is read off the evidence, not
  off the query or a model's say-so; with nothing to go on it's left blank.
- **Never claim a success that didn't happen.** Sync errors get a loud banner,
  a failed clipboard shows the text to copy by hand, and a batch reports what was
  actually accepted.

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
| **Applied yet?** | **Not yet** (default) or **Applied** — tap the row later to flip it |
| **Cold emails sent?** | **Not yet** (default) or **Sent** — did you email anyone there |
| **Connection made?** | **Not yet** (default) or **Connected** — did that outreach actually land |
| **If they came back, what was the answer?** | **No answer yet** (default) · **Accepted** · **Waitlisted** · **Denied** |
| Role | optional |
| Date | defaults to today |
| Careers page or posting link | optional; becomes a tappable link |
| Note | optional |

### The answer, when one comes

Applied / cold email / connection are all about what *you* did. The **answer** is
what came back, and it's the one thing that ends the story: **Accepted**,
**Waitlisted** or **Denied**, defaulting to **No answer yet**.

It **replaces the status chip** on that row. Once a company has said yes, no or
wait, how many days it's been silent stopped being the question — so the answer
outranks "Waiting 12d" and "Not applied" in the same slot, rather than adding a
column.

The colors follow the same rule as everywhere else: **Accepted is green**,
**Waitlisted is amber** because it's still live and may still need chasing, and
**Denied is red**. Red normally means "needs action" here and a denial needs
none — but a no is the one answer you must not misread while scanning, and gray
let it blend into the closed rows it sits near. Being unmissable wins.

The stat row carries an **Accepted** tile with `N waitlisted · N denied`
underneath, so all three are one glance without spending three tiles on it. It
counts every company including closed ones — archiving a row doesn't un-answer it.

An older company row has no answer on file, which reads as **No answer yet**, and
an unrecognised value is read the same way rather than trusted into the UI.

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
- On the **edit form** you get by tapping a company row — the same two controls,
  pre-filled with where that company currently stands.
- In the companies table, as **two small dots** next to the company name.

Both states always render — never just the positive. Showing nothing for "no" would
be ambiguous between *not yet* and *this row predates the flag*, and "who have I not
emailed yet" is the exact question you're scanning the table to answer.

The negatives are **gray, not amber**. They're a fact to read, not an alarm — amber
and red stay reserved for things actually demanding action, so they keep their bite.

In the table the words are compressed to dots to keep the row one line tall, which
is a real accessibility cost, so it's paid back three ways: each dot carries its
full text as a **tooltip**, the same text is there for **screen readers**, and a
**legend** sits under the table. The meaning is compressed, not thrown away — tap
the row and the edit form spells both out in words, so there's always somewhere the
state is unambiguous.

The two dots mean different things **by position**, so the legend names each one
rather than describing the colors:

```
● 1st = cold email sent   ● 2nd = connection made   ○ outline = not yet
```

A filled dot is blue, not green — see "Status colors". The legend used to read
`● done · ○ not yet`, which was worse than nothing: "done" named neither dot and
read like a third state the row could be in.

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

A single column is capped at **640px** — sized to what the row actually needs
(~500px) rather than to the screen. Stretching one column wider only spread dead
space across the card.

### Two columns, one scroll

At **1040px and up** the page widens to 1180px and the two tables sit **side by
side**: contacts on the left, companies on the right. They're separate lists you
read against each other — "have I emailed anyone at this place" spans both — so
side by side beats one buried under the other.

Both columns are in normal page flow, so **one page scroll moves them together**.
Neither column scrolls on its own, and a short list stays short instead of being
stretched to match the tall one.

The **stat row stays full width across the top**, above both columns, since it
counts things from both.

Below 1040px there isn't room for two ~500px rows, so it collapses to the single
640px column and the phone layout is exactly as it was.

On a phone the row still has to fit, so under 620px the company name truncates with
an ellipsis, the gutters tighten, and the link drops to a bare 🔗. That's deliberate:
a shortened name beats having to scroll sideways to find out whether there's a link.
Tap the row to see the full name and role in the dialog.

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

## The layout

Everything is sized to be read, not to fill the window.

**Each column has its own stat row, above it.** A tile over the contacts table
that counted companies was a small lie about what the number belonged to.

| Contacts | Companies |
|---|---|
| **Contacted** — people you actually sent something to; a row with no date is someone you *found*, not someone you wrote to | **Applied** |
| **Waiting** — the same, minus the ones you dropped | **Waiting** — applied and heard nothing at all |
| **Connected** — invitations accepted. A click, not an answer, so it is counted apart from Replied | **Interview** |
| **Replied** — they wrote back | **Waitlisted** |
| **Meetings** | **Accepted**, with denials underneath |

Only applied rows can be **Waiting**: a company you merely bookmarked has
nothing to answer. An outcome of any kind, a reply, or a meeting all mean
something came back, so all three end the wait — and closed rows are out,
because you stopped caring.

Company counts include closed rows: archiving one doesn't un-answer it.

**＋ Cold contact and ＋ Add company live in their own column's heading.** They
used to sit together in a "Log something" card above both tables, which cost a
whole card of vertical space to hold two buttons — and put them nowhere near the
list each one adds to. Now the button is in the heading of the thing it adds to.

Spacing throughout is deliberately tight — card padding, row padding, gutters and
gaps are all pulled in. **Font sizes are untouched**: the point is to fit more
rows on screen, not to make them harder to read.

The biggest single win was the **shortcut strip** under each heading — ✉ Send
queue, ▶ N staged, 📋 Copy AI prompt. Those were full-width 44px buttons, one per
line, each with a 12px gap beneath it: up to **112px of chrome** above the
contacts table before you reached a single row. They're shortcuts, so they're now
sized like shortcuts and share one wrapping row — **28px**.

The rest, all spacing and no type:

| | before → after |
|---|---|
| archive toggle (`▸ View closed…`) | 38 → 28px |
| dot legend gap | 10 → 6px above, 14 → 10px between |
| segmented controls (Applied yet? etc.) | 40 → 32px |
| form field spacing | 10 → 7px, labels 4 → 3px |
| dialog body padding | 14/16/20 → 10/12/14px |
| nudge row | 10 → 7/9px, buttons 40 → 32px |
| ⚙ drawer padding | 16 → 11/12px |
| drawer labels · rules · inputs | 12/16/44 → 8/11/34px |

**One deliberate trade:** several tap targets are now under the 44px normally
recommended for touch. That's the cost of the density, and it was asked for
knowingly — the frequently-tapped things on a phone (table rows, the ＋ buttons,
form inputs) are the ones kept largest.

## Per-entry workspaces

Every contact and every company has **its own workspace** — a bigger, free-form
notes area that belongs to that one entry.

**The workspace opens with the dialog**, beside it — no second tap. That includes
**＋ Cold contact** and **＋ Add company**: there's no row to attach to yet, so it
opens in pending mode (titled `New contact` / `New company`, labelled `Saved when you
save the entry`) and the text is carried onto the row the moment you save it. Draft
the email and log the person in one pass.
It's 340×400, deliberately not a full-height drawer and not a takeover. Opening a
different row repoints it at that entry, and closing the dialog closes it.

Where there's room (**920px and up**) the dialog and the workspace are **centred as
a pair**, side by side with a gap: the dialog shifts left rather than the workspace
landing on top of the thing it's meant to sit beside. Narrower than that — a phone,
or a half-width window — there is no side to sit on, so it still opens with the entry
but sits over the top of the dialog, the same place it has always appeared. **📝
Workspace** in the dialog puts it away and brings it back.

The page underneath never moves either way.

- **Saves as you type**, debounced, straight onto that entry. The label reads
  `Saving…` then `Saved`.
- Pending text is **flushed on the way out** — closing the popup, closing the dialog,
  switching entries, or backgrounding the app all commit what you typed, so a
  mid-sentence debounce can't drop it.
- If the entry has since been deleted (say, on another device), it says
  `⚠ Entry is gone — copy your text out` rather than claiming a save that didn't
  happen.
- The **📝 button shows a dot** when there's already something written in there, so
  you can tell without opening it.
- **📋 Copy** puts the whole thing on the clipboard.
- **♻ Repopulate** wipes it and writes a fresh draft — see below.
- Tapping **📝 Workspace** again puts it away, as does **✕** or **Escape**.

The workspace never re-points at another entry: opening a different one closes it
first, after saving. That's how notes would end up on the wrong person.

### ♻ Repopulate

**🔍 Find contacts** writes the draft into the workspace at the moment it creates
the row. So a company you hadn't finished filling in — no role on it yet, not yet
marked **Applied** — bakes a literal `[internship]`, or the wrong template
entirely, into every workspace it just created. Fixing the company row afterwards did
nothing to them: the only way out was deleting the contact and finding them again,
which throws away the search that found them.

**♻ Repopulate** regenerates the draft from what the tracker holds *now*, in
place. Fill in the company, tap it, and the drafts are right.

It is destructive on purpose — wiping what's in there is the entire point — so it
**asks first** whenever there's anything to lose, and on an empty workspace it just
writes. **✕** and **Escape** are unaffected; this is the one button here that
throws text away.

Afterwards the label **names the template it used and any placeholder still
unfilled**:

```
Repopulated from LinkedIn · first message · still missing [internship]
```

Naming both is the point. Two drafts differing in one clause is not something you
can diff by eye, so a button that silently swapped them would leave you re-reading
the whole thing to find out whether it did anything — and a second `[internship]`
is exactly the gap you tapped it to close. Unfilled placeholders are read with the
same list the send queue blocks on, so the two can't disagree about what counts.

Which of the five drafts you get is **not a choice you make**, same as everywhere
else:

| The contact | What you get |
|---|---|
| no date on it — every row 🔍 Find contacts creates | the **first message**, in their channel |
| already contacted | the **follow-up**, in their channel |

That's the same split **✉ Send queue** groups by, so the two can't hand you
different drafts for the same person.

**Companies don't have the button** — there's no such thing as a draft to a
company. It's hidden rather than greyed out, since a disabled button reads as
broken.

On **＋ Cold contact** it's there before the row exists, drafting from what you've
typed into the form so far; the label says `saved when you save the entry`, because
that's still true of everything in the pending workspace.

One thing it deliberately does **not** read: unsaved edits sitting in the form
next to it. It regenerates from the saved entry, the same source the dialog's
`📋 Copy` buttons use. Change the company on a contact and **Save changes** first,
then repopulate.

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
same button again, the **✕**, or **Escape** closes it. Saving closes it for you.

**Save** and **📋 Copy outreach draft** sit on one line at the end of the form —
they're the two things you do when you're finished with it.

### Tapping outside saves

**Tap any empty space outside the dialog and what you typed is saved**, rather than
thrown away. You don't have to find the Save button to keep an entry, and everything
that's optional stays optional — blank company, blank role, blank note all go in
exactly as they would through Save.

The one exception is a **name** (or a **company**, on the company form). A row with
neither is one you can't find again, so tapping outside with an empty name just
closes the dialog and writes nothing. Explicit **Save** is unchanged and still takes
a completely blank row if you want one — see "No field is enforced".

**✕ and Escape still close without saving**, so there's a deliberate way to back out
of an edit you didn't mean to make.

Tapping a row opens this same dialog pre-filled — see "Opening an entry" below.

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
gets substituted, and `{fieldwords}` is what counts as your field, from Settings —
the same terms 🔍 Find contacts uses, so the two hunts can't describe you
differently. Delete it and the list is **appended at the end** rather than
dropped, so the prompt can't end up with nothing to research — and the first tap of
Done tells you it happened.

The stat row counts **Applied** out of companies tracked, and the reply rate is
measured only against things you actually sent — a bookmarked company can't reply,
so it never drags the percentage down.

## Opening an entry

**Tap any row and it opens in a dialog in the middle of the screen, in edit mode** —
the same dialog and the same form you added it with, pre-filled. Only the title
(`Edit contact` / `Edit company`), the button (`Save changes`) and what happens on
save are different. There's one definition of what a contact or a company looks like,
so the add form and the edit form can't drift apart.

There's no "pick someone from a dropdown" step and nothing unfolds inside the table.
You tap the thing you want to change and it opens.

Below the fields, the dialog carries everything that isn't a field:

| Group | Buttons |
|---|---|
| **Status** | `Replied` · `Reminder sent` *(contacts)* · `Closed` — each shows a ✓ when true |
| **Actions** | `📝 Workspace` · `📋 Copy draft` *(contacts)* · `Delete` |

plus the **meeting date**. Those save the moment you tap them — **Save changes** is
only for the fields, so there's no way to lose a status change by closing without it.
`📝 Workspace` shows a ● when that entry already has something in its workspace. The
workspace is already open by the time you see this button, so it's there to put it
away and bring it back.

Applied / Cold emails / Connection aren't repeated here: they're toggles on the
company form itself, a few lines up.

Editing fields never touches status. Only the keys the form owns are written back:
replies, meetings, reminder history, closed and the workspace all survive a rename.

If an older contact holds a channel that's no longer offered (`In person`, `Phone`),
the form adds it back as a real, selected option instead of silently rewriting the
row — and drops it again on close, so the Add form stays clean.

### Closed entries

Closing something takes it out of the live table and puts it in a collapsed list at
the bottom of that same table: **▸ View closed contacts** / **▸ View closed
companies**, with a count. Tap to expand, tap to collapse; each table remembers
whether you left it open.

The strip **isn't there at all until something is closed**, so an app you've never
closed anything in looks exactly as it did.

It's the same table underneath — same columns, built by the same code, so the two
can't drift apart — with two deliberate differences: no drag handle and no sortable
date header. An archive is for finding one thing, not for keeping in an order, so
it always stays newest-first.

Rows in it stay tappable. Open one and turn **Closed** off and it goes straight back
to the live list, in its old position if you have a custom order.

This replaces the old **Settings → "Show closed entries"** checkbox, which mixed
closed rows in with live ones. Closed things should be out of the way *and* findable,
which a single global toggle can't do.

### Ordering the tables

Both tables open **newest first**, and either can be sorted by any of three
columns — independently of each other, and remembered per device.

| Tap | Sorts by | Opens at |
|---|---|---|
| **Who** / **Company** | name, alphabetically | A → Z |
| **Sent** / **Date** | the date on the row | newest first |
| **Status** | how long it's been sitting | **No date**, then *sent today*, then *waiting 1d*, and so on |

**The arrow is the whole indicator**, and it says two things at once: which column
is sorting, and which way. `↑` ascending, `↓` descending, on exactly one header.

Tapping one column cycles through three states:

```
↑  →  ↓  →  (no arrow)
```

**No arrow means your own order** — the one you get by dragging rows. Reaching it
by a third tap rather than only by dragging means the header is a full cycle
instead of a dead end. The first time you land there it's seeded from whatever
was on screen, so the list never jumps to an arrangement you didn't choose, and
it's saved from then on.

- **Tap a different column** to sort by it, at whatever end is useful to open on.
- **Drag the bars** left of a name to go straight to your own order.
- **Both are remembered**, per table and per device: a dragged order survives a
  sort and vice versa.

Status sorting is one rule rather than a hand-ranked list of every chip: a row's
place is how long it's been sitting, so a **Replied** row sorts among the others
by its date and the chip still says Replied. Sorting by status ascending is the
"who have I just touched" view; reversed, it's the "what have I left longest"
view.

The order is a view preference: it lives in this device's `localStorage`, never on
the entries, so reordering can't alter your data or ride the sync.

Anything the saved order has never seen — added since you last dragged, or synced in
from another device — appears at the **top** in date order rather than silently
sinking to the bottom.

The order is a view preference: it lives in this device's `localStorage`, never on
the entries, so reordering can't alter your data or ride the sync. It also means each
device keeps its own arrangement.

**How the drag works**, because the first attempt didn't: the bars are a 24×34 tap
target drawn in CSS rather than a `⠿` glyph, so they can't land as a tofu box in a
font that lacks it. The drag runs on pointer events with `touch-action: none`, so a
finger drags the row instead of scrolling the page. Crucially the move and release
listeners are bound to `window`, not to the handle — bound to the handle they only
fire while the pointer stays inside that 24px box, which is why nothing moved. And
the click that a press turns into is ignored for 400ms after a drop, by timestamp
rather than a flag, so letting go never also opens the row you just dropped and a
touch drag that produces no click can't leave a flag stuck swallowing your next tap.

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

## Three LinkedIn things that aren't replies

An invitation is not a message, and the two states it can be in were being
squeezed into fields that meant something else.

### ✓ Invite accepted

They clicked accept. **That is not a reply** — they didn't write back — so it's
its own toggle on a LinkedIn contact's dialog, it stamps the day you tapped it,
and it shows as its own chip. It feeds the **Connected** tile, separately from
Replied.

**Four days later you're reminded to send the note**, in a green card that works
like the nudge card: name, how long it's been, and the actions beside it. Sending
a note (**Note sent**) buys another four days rather than leaving them on the
list forever. Connecting and then never writing is the failure this exists to
catch.

While an invitation is accepted, the 7-day nudge steps aside — the four-day clock
has taken over, and two cards naming the same person is how you learn to ignore
both.

### ↩ Worth withdrawing

An invitation that is never accepted just sits there, and LinkedIn caps how many
can be pending. After **three weeks** with no answer, the contact moves to an
amber card suggesting you withdraw it.

Counted from **when the invitation went out**, not from your last reminder:
sending a follow-up note doesn't make a pending request any fresher.

This is a third thing, and the distinction matters:

| | What it means |
|---|---|
| **Ignore** | stop nudging me about this person. They stay live in the table |
| **Drop it** | file them away as over — closes the entry |
| **Withdrawn** | you cancelled the invitation *on LinkedIn*. The person isn't closed, they're just no longer pending |

Past three weeks the advice stops being "send another note" and becomes
"withdraw it", so those rows leave the nudge card for this one.

### The chip order, fixed

A company you'd never applied to but that had **written back** used to show
`Not applied`, because that test ran before the reply test. The chip is meant to
say the most useful true thing about a row, and "they answered" outranks "you
haven't sent anything" every time.

**Interview** is also a company outcome now, alongside Accepted / Waitlisted /
Denied. It's green: green here means something came back to you, and an interview
is the strongest thing short of an offer. It isn't terminal — that's what the
word is for.

## The 7-day rule

A contact goes red when **all** of these hold: no reply, no meeting booked, not
closed, and 7+ days since the last time you touched it. Those rows collect in a
red **"Needs a nudge"** card at the top of the screen.

**Tap the name — or the line under it — and the contact opens**, in the same
dialog you get from tapping their row in the table: their role, their handle,
their note, both copy buttons, the status toggles, and the workspace alongside it.
The nudge card used to be the one place a person appeared that you couldn't open,
so acting on a nudge meant scrolling down and finding them in the table first.
The buttons underneath still do only their own job — tapping **Ignore** doesn't
also open the dialog.

Underneath, the buttons:

- **📋 Copy draft** — puts your follow-up wording on the clipboard, filled in with
  this person's details. Paste into your mail app, tweak, send. Copying is *not*
  sending, so it deliberately leaves the reminder state untouched.
- **Reminder sent** — a **toggle**. On, it logs today and **restarts the 7-day
  clock**, so a contact you're actively chasing goes quiet for another week
  instead of nagging forever. Tap it again to undo (tapped it by mistake, or they
  replied before you actually sent). The reminder count and last-reminder date
  show on the row.
- **They replied** — marks it replied, clears it from the list.
- **Ignore** — stops nudging about this one, and that's all. The row stays live
  and in the table; it just never shows up in the red card again.
- **Drop it** — closes the entry; it stops being chased and moves to the closed
  list at the bottom of the table.

**Ignore is the quiet middle ground**, and it exists because the other three
buttons all say something untrue when you just don't want to chase someone.
*Drop it* files them away as over. *They replied* is a lie about them. *Reminder
sent* is a lie about you, and it only buys a week anyway. Ignoring says the one
thing that's actually true: not this one.

An ignored contact shows a gray **Ignored** chip in the table rather than going
silently quiet — a row that stopped nudging with nothing on it explaining why
would be the same bug as any other silent failure. To undo it, tap the row and
turn **Ignored** off in the Status group; it goes straight back to nudging if
it's still overdue.

Nothing is emailed for you — see **✉ Send queue**, which stages a batch and then
waits for you to send each one.

Applications deliberately **do not** get a red flag — a quiet application at day
7 is normal, and flagging it would train you to ignore red. They show a plain
"Waiting N days" instead.

## ✉ Send queue

Above the contacts table: tick people, hit **Stage N**, and you land in a deck
you work down one card at a time — read it, **📋 Copy**, **✉ Open compose** or
**🔗 Copy note & open profile**, send it yourself, **✓ Sent — next** (or
**Skip**). The card slides away and the next is dealt.

**Nothing here sends anything.** It does the fetching and filling; the judgement
and the click stay yours.

### The buttons that were there but off the edge

For a while the deck looked like it had no way to move on: the card showed
**📋 Copy note** filling its whole width and nothing else. **✓ Sent — next** and
**Skip** were rendered, wired and working the whole time — just painted past the
right-hand edge of the dialog, where no amount of scrolling reached them.

Every button in this app is `width: 100%`, which is right for a phone-first form
layout and fatal in a `nowrap` flex row: `flex: 0 0 auto` takes its basis from
that width, so each button demanded the entire row and refused to shrink. The
reset that should have stopped it, `.dk-acts button`, has the same specificity as
`button.secondary` and loses to it on source order — so it silently did nothing.
The fix is qualifying the selector (`.dk-acts button.secondary`) and letting the
row wrap; four buttons were never going to fit on one phone line, and a second
row beats an unreachable button.

Worth knowing because the failure is invisible to the obvious test. Clicking
`dkSent` from the console advances the deck perfectly whether or not the button
can be seen — so "the handler works" proved nothing. What catches it is measuring
where the buttons actually landed and hit-testing the centre of each one.

**Staging is the only door to the deck**, and the picker used to describe it as
sending your batch off to be "rendered and screenshotted" and left "on the
agent's review page" — none of which had been true since the deck moved into
this dialog. It read as *you need to install something first*, which is a good
reason never to press the button, and without pressing it there is no card, no
**Skip** and no **✓ Sent — next**: just a list of previews and a LinkedIn URL to
copy out by hand. The picker now says what actually happens, and says it
differently if you've switched reviewing to the local agent.

### Copy · both · open

Three buttons on a LinkedIn card, left to right:

```
[📋 Copy note]   [📋🔗 Copy & open]   [🔗 Open profile]
```

The **middle** one is the whole job in one tap and is what you'll use nearly
every time. A Gmail compose window can be pre-filled straight from a URL; **a
LinkedIn connect box can't**, so the note has to travel on the clipboard, and
coming back to the deck for it after opening the profile is the step that makes
a batch feel like work.

The other two stay because the pair comes apart often enough: you reread a note
after opening the profile and want it on the clipboard again without a second
tab, or the profile is already open beside you and a third copy of it is just
clutter. One combined button forces the side effect you didn't ask for.

**Copy & open copies before it opens**, which isn't cosmetic — a clipboard write
needs this document focused and the new tab takes that away. Both happen inside
the one click, so the popup blocker still sees a real gesture.

Email keeps its own set: a compose URL already carries the subject and body, so
there's nothing to copy on the way out and the middle slot is **📋 Copy subject**
instead.

### The card is the message, and you can type in it

The message on a deck card is a **textarea**, not a paragraph. It is the exact
text about to go out, so it's the obvious place to fix a sentence — and what you
type is written straight onto that contact's **Workspace**, which is where the
draft actually lives. So an edit here survives closing the deck, and ♻ Repopulate
in either place overwrites the same thing.

For an email the box holds the whole draft including its `Subject:` line, because
that's how the text is stored; the subject strip above it is a live read-out of
what will be used.

**A staged card is a view of the contact, not a photocopy.** It used to be the
photocopy — the text was frozen when you pressed Stage, so repopulating a
Workspace, or fixing the company row a draft reads from, changed nothing about
the card waiting in the queue and you'd send the old wording having just watched
yourself correct it. The text is now re-derived on every deck render, through the
same `outboxDraft()` the picker uses.

Only `staged` jobs refresh. A **sent** one is a record of what you actually sent,
and rewriting it later would make it a lie.

The picker refuses to stage a draft containing a placeholder, but a card can
acquire one *after* staging — you edit it, or it's re-derived after the company
row changed — so the card warns rather than letting `[internship]` go out:

```
⚠ still unfilled: [internship] — ♻ Repopulate, or type over it.
```

### ♻ Repopulate, per person and for the whole batch

**♻ Repopulate** on the card rebuilds that one message from the template — the
same `draftFor()` the Workspace button uses, so the two can't produce different
wording. It asks first when there's text to lose.

**♻ Repopulate all N** in the footer does the batch, which is what you want after
rewriting a template in Settings; the alternative is walking the deck tapping ♻
once per person. It's destructive across several people rather than one, so it
names the count in the confirm and reports what actually happened — including
anyone whose draft still carries a placeholder afterwards, since regenerating
can't invent a value that isn't on file and quietly leaving those is how one goes
out.

### ♻ Repopulate, on a row that says it has a placeholder

A row carrying `[company]` or any other `[placeholder]` can't be ticked. That
marker exists so you notice before sending — but the fix was somewhere else
entirely: close the queue, find the contact, open the Workspace, repopulate,
come back.

So the blocked row carries the button itself:

```
⚠ the draft still has an unfilled [placeholder] in it   ♻ Repopulate
```

Same regeneration and the same `draftFor()` as the Workspace button, so the two
can't hand you different text. It reports both outcomes because they need
different things from you:

- the draft was stale — usually one 🔍 Find contacts wrote before the company
  row was filled in — so it's rewritten, the row unblocks, and the Stage count
  goes up.
- the value genuinely isn't on file, and no amount of regenerating invents it.
  It names what's still missing and where to put it (`[internship]` lives on the
  **company** row), and **leaves the row blocked** rather than tidying the
  warning away.

Who shows up: **First message** (no contact date yet) and **Follow-up** (the
`dueNudges()` set). Rows that can't be sent are shown greyed **with the reason**
rather than hidden — the handle field is one unvalidated box, so a LinkedIn URL
sitting on an `Email` contact is caught and named, because `firstContactKind()`
keys off the channel alone and would otherwise paste a full email, `Subject:`
line and all, into a connection request.

A draft still carrying `[company]` or any other `[placeholder]` **can't be
ticked**. That marker exists so you notice before sending; a Gmail subject field
is where it would go unnoticed.

**Hand-edited Workspace text wins** over the regenerated draft, and the row says
`using your Workspace text` so you can see which source it used.

**Line wrapping is undone before staging.** The templates are hard-wrapped at ~80
characters so they read well in the Settings textarea; Gmail and LinkedIn wrap
themselves, at their own width, so those breaks land mid-sentence. Paragraphs are
rejoined and only the blank lines between them survive — a sign-off (`Best,` /
`Thanks,`) keeps its break so the name stays on its own line.

### ↩ Back, for a tap you didn't mean

**✓ Sent — next** writes into the tracker, so taking it back has to put those
writes back too — not just re-deal the card. Everything the tick can touch is
photographed first: the contact's date and reminder history, and the company's
cold-email dot. **↩ Back** restores from that snapshot and says what it actually
reversed:

```
↩ Zoe Adams is back — un-dated the contact, turned Zeta Corp's cold-email dot back off.
```

Restoring beats inverting each change one by one, which would have to know that a
dot already on before you got here should stay on.

The button only appears once there's a tap to take back, and you can walk back
several. It is **not** persisted: an undo stack surviving a reload would let you
reverse something from yesterday, long after the tracker has moved on.

A **Skip** can be taken back the same way, and correctly reports that nothing in
the tracker changed — because nothing did.

### Ticking Sent updates the tracker

- **The 7-day clock restarts** for that contact — or, if they had no contact date
  at all, today becomes it. ("Set the date only if it's empty" would record
  nothing for anyone already contacted, so they'd re-qualify tomorrow forever.)
- **The company's cold-email dot turns on**, so you never go back into the
  company to say you approached them. A LinkedIn note counts: that flag is the
  coarse "have I approached this place at all" answer, not a claim about channel.
- **Never** touched: replied, meeting booked, closed. Those mean something came
  *back*, and nothing here knows whether it did.

The batch lives in this device's `localStorage` under `intern-outbox`, **not** in
`DATA` — it carries full message text and `data/log.json` is public. It's working
state anyway; once something is sent the fact lives on the contact.

Staleness is re-checked against `DATA` on every render, so a contact who replied
thirty seconds ago voids their own card before you can write to them.

### The local agent — optional, and off by default

`agent/stage_agent.py` does the same job in its own window, which outlives the
tab. **Nothing needs it**: a browser can open a compose window, write the
clipboard and keep a batch, so the review deck moved into the site and the agent
became a choice rather than a requirement.

Switch to it under **Settings → Send queue → Where to work through them**, which
also shows its start and stop commands with a copy button each. It is **not**
installed as a startup task and does not run unless you start it; the stop
command finds it by the port it holds, so it can't kill an unrelated python.

It holds no credentials and never writes to your tracker — the website reads
`/status` from it and does its own bookkeeping. Its `auto` mode opens the real
pre-filled compose window and loads your clipboard, then stops. Its runtime data
lives in `%LOCALAPPDATA%\internship-agent\`, deliberately outside this public
repo. See `agent/README.md`.

There are no screenshots anywhere in this. You press the button and you press
Send, so a picture of that is a picture of your own work.

## Email drafts

Both draft templates live in **Settings → Email drafts**, so the wording is in the
same app as the reminder — you never navigate somewhere else to find it. Two
templates: **first-contact** and **follow-up**. Both ship with real, sendable
wording (BU mech-e, biosensors/HMI, Summer 2027); edit them to taste, then hit
**Done editing drafts** — that saves and closes the drawer in one tap. **Reset to
defaults** puts the built-in wording back.

### Eight drafts, and you never pick one

Two axes — the channel, and first message versus chase — plus **a first message
per role**:

| | First message | Follow-up |
|---|---|---|
| **Email** | `outreach` · `outreachBU` · `outreachField` | `followup` |
| **LinkedIn** | `connect` · `connectBU` · `connectField` | `liFollowup` |

A LinkedIn note and a cold email are not the same piece of writing — one goes in
a connection request and has to be short — so they're separate templates rather
than one draft you reword every time.

**The app picks from the contact's channel and role**, so there's no dropdown and
no choosing.

#### One opener per bucket

The two buckets are two different conversations, and sending both of them the
same paragraph wastes the only thing that distinguishes them:

| Role | What its opener does |
|---|---|
| `BU Eng` | leads with the shared school, which is the whole reason that bucket exists |
| `Field Eng` | asks about the work — they're doing what you want to do, and it's the one thing they can actually answer |
| anything else | the plain opener. Includes older `Hiring` / `VP Eng` rows, which keep their role text and are never rewritten |

A role that is blank, or something you typed by hand, gets the **plain** version
rather than being pushed into a bucket it never established — the same rule the
rest of this app follows. `BU Eng` in particular is only ever set from Boston
University appearing in someone's **Education**, so "I saw you went to BU as
well" is a claim the app established before writing it. Change a role by hand and
the draft follows; ♻ Repopulate rewrites an existing one to match.

**Follow-ups are one each**, unchanged — by the time you're chasing, the opener
already did the work of saying who you are.

#### The applied / not-applied fork is gone

The LinkedIn opener used to have two versions and the **Companies** table chose
between them: marked **Applied** got "I recently applied to the {company}
{internship}…", anything else got wording that made no such claim. That's now one
template. Both versions said the same thing to the reader — you'd like to talk —
while doubling the wording to keep in sync, and the difference mattered to the
app's conscience rather than to the person receiving it. If you want to mention
an application, it's one line in the template.

Your old `applied` wording is **left in `localStorage` rather than deleted**, so
nothing you wrote is gone; it's simply no longer used. (Tapping **Reset to
defaults** does clear it, along with everything else.)

Every copy button **names what it will actually hand you**, and relabels itself
live as you change the channel — `📋 Copy draft` told you nothing about whether
you were about to paste an email into a connection request:

| Button | Where | Gives you |
|---|---|---|
| 📋 Copy first email / 📋 Copy LinkedIn note | on the Cold contact form | the first message, from what you've *just typed* — copy, send, then Save |
| 📋 Copy email follow-up / 📋 Copy LinkedIn follow-up | on each red nudge row | that person's chase, in their channel |
| 📋 Copy LinkedIn note · 📋 Copy LinkedIn follow-up | in a contact's edit dialog | both, for that contact |

Placeholders substituted automatically:

| | |
|---|---|
| `{first}` | first name only — for "Hi Sam," |
| `{name}` | full name |
| `{company}` `{role}` `{channel}` | as logged |
| `{date}` | date you first contacted them (e.g. Jul 25) |
| `{days}` | days since your last contact or reminder |
| `{internship}` | the role **you** applied to, read off that company's row |
| `{learn}` | "your work" for an engineer — everyone the search files — and "you" only on an older `Hiring` row |

`{role}` and `{internship}` are easy to confuse and are not the same thing.
`{role}` is the **person's** bucket — `BU Eng` or `Field Eng`.
`{internship}` is the job **you** applied to, which lives on the company row
because it's the same for everyone you know there. A draft saying "I applied to
the Marotta BU Eng" is what using the wrong one looks like.

The eight keys, as stored: `outreach` / `outreachBU` / `outreachField` are the
emails, `connect` / `connectBU` / `connectField` the short LinkedIn connect
notes, and `followup` / `liFollowup` the two chases.

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
| red | **Denied** |
| amber | company tracked but **not applied yet** — a to-do, not a waiting game |
| amber | **no date** on the row, so the 7-day clock can't run |
| amber | **Waitlisted** — still live, may still need chasing |
| green | replied, or a meeting is set |
| green | **Accepted** |
| gray filled | waiting, under 7 days |
| gray outline | closed; or a company flag still at **no** (no cold email, no connection) |
| blue | a company flag at **yes** — cold email sent, or connection made |

**Green never means "I did something."** It means something came back to you —
they replied, you have a meeting, you got in. The two company flag dots are
things *you* did, so they're **blue**: sharing green made a company you'd emailed
look at a glance like a company that had answered.

Light and dark mode both follow the OS setting.

## ⚡ Auto-populate from a LinkedIn profile

On the **Cold contact** form there's one button: **⚡ Auto-populate from LinkedIn**.
Tap it and the paste box opens as a popup beside the form; paste a profile, and the
name, company and their role land in the fields with an outreach draft in the Note.

It's a **popup, not a permanent block**. Most saves don't involve it, and a paste
box plus a preview sitting above the name field pushed the actual form down every
single time. It opens on ⚡, closes on ⚡ again, **✕** or **Escape**, and closes
itself whenever the form opens — a parse belongs to the entry it was run for.

**A browser cannot read linkedin.com.** LinkedIn sends no CORS headers, so the
request is refused before it leaves — this was tested, not assumed. A bookmarklet
is out too: LinkedIn's CSP blocks any bookmarklet. So there is no scraper here.
There are two ways in:

| You paste | What happens |
|---|---|
| the **whole copied page** (Ctrl+A, Ctrl+C on the profile) | parsed on this device, **no request made at all** |
| just the **URL** | a reader service fetches the public logged-out view, and that gets parsed |

The paste route is the guarantee; the URL route is the convenience. That's why
the reader is a setting you can blank out — see below.

**Nothing is written straight into the form.** It parses, shows you exactly what
it found, and waits for **Use these**. Then it fills only the fields that are
still empty, so auto-populate can never eat something you typed. A bad read costs
one tap.

If the profile can't be read, it doesn't fail silently or invent anything — the
URL slug still carries a name (`/in/nathalie-dubois-8a4b21` → `Nathalie Dubois`),
so it fills that, says why the rest is missing, and tells you to paste the page.

### It leaves the date empty

The Add form prefills today's date, because logging usually follows sending.
Auto-populate **clears it**: pasting somebody's profile URL is research, not
contact, and a date there is the app asserting you wrote to them. It would also
start the 7-day clock, so a person you have never messaged would turn up in the
red nudge card a week later.

Same choice 🔍 Find contacts already makes. Type a date in yourself, or let
✉ Send queue stamp it when you actually send.

### Their role is a bucket, not a job title

The `role` field on an auto-populated contact holds one of exactly two values,
because when you're scanning a list of people to approach, their literal title
isn't the thing you need:

| Bucket | Who, and why it matters |
|---|---|
| `BU Eng` | **Boston University** people there — least gatekeeping, by far the easiest yes, because you already share something |
| `Field Eng` | somebody doing the work you want to do, from the terms in **Settings** — the one person who can say what that work is actually like |

Recruiters and engineering leadership had buckets of their own once. They don't
now: the BU connection is the one that actually gets answered, so the slots go
there. Rows written back then keep their `Hiring` / `VP Eng` text and are never
rewritten underneath you.

`BU Eng` is deliberately **not** "any engineer". The BU connection is the entire
point of the bucket, so it's set from Boston University actually appearing in
their **Education** — never guessed from a job title, and never from the rest of
the page. Their real title isn't thrown away: the
preview shows it (`filed as BU Eng · LinkedIn says "Chairman and CEO"`) so you can
see what was decided and overrule it before saving. With nothing to go on the role
is left **blank** rather than guessed.

### Where the BU evidence comes from

`BU Eng` is the one bucket resting entirely on a fact about the person rather
than on their title, so it's the one where a loose match does real damage. It
used to test the whole page for "boston university", which fires on things that
aren't a degree — a **People also viewed** sidebar, a reposted BU article, a lab
manager who *works at* Boston University — and misses the ways people actually
write it: `BU`, `Boston Univ.`, `Questrom`.

So the page is sliced at its **Education** heading and only that block is read.
Three outcomes, and the difference between them is the whole point:

| What's on the page | Verdict |
|---|---|
| Education section, BU in it | **BU Eng.** The strongest answer available |
| Education section, BU only *outside* it | **not BU.** A hit elsewhere is reported and then rejected — the section not naming BU is a stronger "no" than a sidebar is a "yes" |
| no Education section (the logged-out view often omits it) | **evidence, marked weak.** 🔍 Find contacts turns that into `check this`, not `verified` |

Inside the Education block `BU` on its own is unambiguous, so the abbreviation
counts there and only there; everywhere else it takes the full name.

Nothing here calls a model, and nothing extra leaves your machine — it reads the
same text the profile reader already fetched, or the page you pasted. **Pasting
the page while signed in always produces an Education section**, which is what
turns a weak read into a settled one, and every unverified row already offers
📋 paste the page to check it.

The evidence is **quoted rather than asserted**, in the ⚡ preview, in the 🔍
review, and in the note written onto the created contact — because `BU Eng` on
its own is a claim you can't check once the finder is closed:

```
BU Eng · LinkedIn says "Senior Mechanical Engineer" ·
  Boston University under Education ("Boston University — BS, Mechanical Engineering")
```

A search **snippet** has no Education section to scope to, so the strict spelling
is used there and it only decides which bucket to *try* someone in. The profile read
is what settles it.

### The draft it writes into the Workspace

The **Workspace** gets the LinkedIn first message, picked the same way every
other copy button picks — `connectBU` when the profile put Boston University in their
education, `connect` otherwise. The status line always says which it used:

```
Filled in. Used the LinkedIn · first message (BU engineer) draft — Boston
University is on their profile, so it opens on the school you share.
```

This used to fork on whether the company was marked **Applied**, and kept its own
copy of that rule. It now calls `firstContactKind()` like everything else, so the
⚡ preview can't drift from what 📋 Copy or the send queue would hand you.

If the Workspace already has text, the draft is **appended** after a blank line —
what you wrote is yours.

It used to land in the **Note**, which was a dead end. The Note is the short
one-line "how did this go" field; **✉ Send queue reads the Workspace**. So an
auto-populated draft was never the message that got staged — the queue quietly
regenerated one from the template and everything the parse had filled in went
nowhere. 🔍 Find contacts has always written to the Workspace; this is now the
same path, and the picker confirms it with `using your Workspace text`.

On the **Add** form the Workspace is open in pending mode and its text is lifted
onto the row when you save. If you've put the Workspace away with **📝**, it is
re-opened against the right entry first — writing into a textarea nothing is
pointing at would drop the draft on the floor.

### Company names get matched to your list

The profile says "Marotta Controls, Inc."; you track "Marotta". Left alone that's
two companies, a split list, and a silently broken Applied lookup. So names are
compared with the decoration stripped (`Inc`, `LLC`, punctuation) and on a
whole-word prefix, and **the spelling already in your tracker wins**. The preview
tells you when it substituted. `Boston Scientific` and `Boston Dynamics` don't
match each other — neither is a prefix of the other.

## 🔍 Find contacts

On a company's edit dialog: **4 Boston University alumni and 1 engineer doing
the work you want to do**. Recruiters and engineering leadership are gone — the
BU connection is the one that actually gets answered, so the slots go there.

Both counts, and what counts as your field, are in **Settings**. A bucket comes
back **empty with a note** rather than padded. Four stages, and **nothing reaches your log until the last
one**:

```
find    → pool every query, bucket by job title, score, take as many
          of each as Settings asks for
verify  → each profile URL read back and parsed — missing links looked up first
review  → what was claimed vs what the profile actually says, with tickboxes
write   → ordinary cold-contact rows, only for what you left ticked
```

Stage 1 alone is not trustworthy: a search can return a stale title, the wrong
person, or a profile URL that was pattern-matched rather than opened. **Stage 2 is
the reason this is worth doing** and stage 3 is where you get to disagree with it.

Each row comes back as one of:

| Verdict | Means |
|---|---|
| `verified` | the profile was read and its employer matches this company |
| `check this` | read, but something disagrees — different employer, a `BU Eng` row whose **Education** doesn't confirm BU (or that has no Education section to confirm it against), or a title that doesn't read like leadership on an older `VP Eng` row |
| `unverified` | couldn't be read at all, or there was no profile link |

`verified` means **the profile page agreed** — not that this is the right person
to write to. Read them before you send anything.

A **sign-in wall counts as a failure, not a profile.** LinkedIn answers a reader
it doesn't like with a signup or "Security verification" page, and those parse
perfectly happily — the heading is just "Join LinkedIn". Without that check a
challenge page becomes a confidently wrong contact, which is worse than a failed
read, so any page that looks like a wall is forced to `unverified`.

Each created contact also gets **the draft already written into its workspace**,
ready to send. Five people with five empty workspaces is five more things to do
by hand, which was the thing this was meant to save.

### Searching, with no key and nothing to install

**🔎 Search** is built in and needs no account, no key and no quota. It's the
default route, and it works on your phone.

Getting there took some ruling out. **Every hosted search API refuses a
browser** — Brave and five public SearXNG instances send no CORS header, Google's
Custom Search JSON API is closed to new signups, and DuckDuckGo's free API returns
instant answers rather than web results. All tested, not assumed.

What works is the reader you already have. DuckDuckGo's **lite** endpoint won't
answer a browser directly, but it goes through the same reader the profiles do,
and its results page is plainly structured:

```
1.[Cici C. - Software Engineer at Microsoft | LinkedIn](https://duckduckgo.com/l/?uddg=…)
Software Engineer at Microsoft · Experience: Microsoft · Education: Boston University · …
www.linkedin.com/in/cici-c-30179ba7
```

Eight `site:linkedin.com/in` searches run and the bare URL on the third line is
read rather than DuckDuckGo's tracking redirect above it. The snippet is kept
because it often **names the school outright**, which is the BU evidence, before
any profile is opened.

This beats asking a model for this job: the links come out of a search index, so
they **can't be invented** — the exact failure the verify stage exists to catch.

#### How the queries are built, and why it once found nobody

Two rules, both learned by measuring the live endpoint rather than reasoning
about it. Getting either wrong returns *literally* "No results found":

- **The company name is stripped of legal decoration.** `Lexington Medical, Inc.`
  searched verbatim matches nothing, because almost no profile writes it that
  way. `normCompany()` already knew how to strip that; the search didn't use it.
- **Exactly one quoted phrase per query — the company.** Two quoted phrases
  return nothing here. `"Lexington Medical" "engineering manager"` → no results;
  `"Lexington Medical" engineering manager` → eight profiles including the VP of
  Technology. So role words go in loose.

Together those take a search from nothing to 47–74 profiles per company.

#### Which bucket someone lands in

**The query that found you doesn't decide your bucket — your job title does.**
A search for `recruiter` happily returns a VP, and filing them under Hiring
makes the app assert something it never established. It also feeds `{learn}`, so
a mis-filed engineer gets a draft offering to "learn more about *you*".

That rule had a back door until it was caught on a real search. The code read
`searchCategory(p) || p.category` — bucket them by their title, **and if the
title says nothing, keep the bucket of the query that found them**. So a run
against a mechanical contractor filed an *Assistant Billing Engineer* and a
*Project Engineer* under **Hiring**, purely because DuckDuckGo returned them for
`"…" recruiter`. Scoring can't save this: `hitScore()` docks a non-hiring title,
but docking only reorders, and when every candidate is wrong the top two are
still wrong.

**Every bucket needs positive evidence from the person themselves**, which is
the rule `BU Eng` always had. Nothing established, no bucket, and the bucket
comes back empty. Naming four strangers as your BU connection is worse than
naming none — and the bucket picks the opener, so a mis-filed row leads with a
school they never went to.

That makes empty buckets more common, so an empty one now says **which kind of
empty it is**, because only one of them means your query was wrong:

```
No Field Eng — the 4 profiles those searches found don't say
mechanical / biomedical / biosensor in their title, so none were filed here.
No BU Eng — those searches found nobody.
```

A small company often has no BU alum on LinkedIn at all, and that is a real
answer rather than a failed search. Those counts are taken **before** the pool
de-duplicates: someone the BU query found who an earlier query already returned
still means the BU query found somebody, and counting off the pool reported it
as having found nobody.

Every query runs, results are pooled, then each person is bucketed from their own
title. Three details worth knowing:

- **BU is checked first.** Someone who went there *and* works in your field is
  filed as the BU contact: the bucket decides how you open, and the shared
  school is the stronger opening of the two.
- **A field pick is somebody doing the work, not running it.** `hitScore()`
  docks leadership, because a director of engineering is exactly who this
  bucket replaced.
- **A BU pick requires Boston University in the evidence.** Everyone the BU query
  returns works at the company, so without the school there's nothing left
  distinguishing them. The bucket comes back **empty with a note** rather than
  naming strangers — the same rule as `⚡ Auto-populate`: never guessed.
  At the verify stage that tightens to their **Education** specifically — see
  "Where the BU evidence comes from".

#### Picking five out of dozens

With a pool that deep, *which* five matters more than how many were found, so
hits are scored:

| Signal | Why |
|---|---|
| their headline names the employer | strongest evidence it's the right person |
| **extra organisation words dock heavily** | `Lexington Medical Center` is an unrelated hospital, and `sameCompany()` matches it *on purpose* — that prefix rule is what makes "Marotta" find "Marotta Controls, Inc." |
| the company appears **only in their name** earns nothing | a search for Draper returns Kristen Draper, who recruits for someone else |
| a field pick scores on your terms and docks on leadership | a Senior Mechanical Engineer is what this bucket is for; a Director of Engineering is what it replaced |
| a BU pick with no Boston University in the result docks hard | everyone the BU query returns works there, so the school is the only thing that makes them a BU pick |

Checked across Draper, Whoop, Marotta Controls, Boston Scientific and Medtronic:
the right people land in all five.

#### Getting past the sign-in wall

The reader only ever sees the logged-out view, and LinkedIn answers a throttled
reader with a wall. Any row that isn't verified offers **📋 paste the page to
check it** — you're signed in, so your copy of the page always works. It runs
through the same check as a fetched page, so the two can't reach different
verdicts. It's offered even with no profile link, since the page you paste is
itself the evidence.

A **free reader API key** in Settings clears the throttling that causes most of
these. Giving the reader your LinkedIn session is not an option here and won't
be: it means handing your logged-in account to a third party, and authenticated
scraping is what LinkedIn actually restricts accounts for.

#### The two routes fill each other's gaps

Search returns URLs but only finds what the index surfaces. A model names people
it knows about and routinely leaves `linkedin` blank, treating reporting a URL as
vouching for one — and those people were skipped by verify and stuck at
`unverified` forever. **Missing links are now looked up by name** and handed to
the same verification as everyone else. The slug must contain their surname
first: attaching a plausible-but-wrong profile is exactly the confidently-wrong
failure verify exists to catch, and it would sail through it. The review says
when a link was found by search rather than claimed.

Two parsing details worth knowing, both of which bit during testing. LinkedIn
sometimes titles a page with the headline alone (`Principal Engineering Manager at
Microsoft - LinkedIn`), and splitting that naively files a job title as somebody's
name — so if the first segment reads like a role, the name comes off the URL slug
instead. And a profile whose public view is laid out differently puts
`Experience & Education` exactly where the job title usually sits, so section
headings are rejected as titles.

**Optional: your own SearXNG.** If you'd rather nothing left your machine at all:

```bash
docker run -d -p 8888:8080 searxng/searxng
```

Add `json` to `search.formats` in its `settings.yml`, allow this page's origin, and
put `http://localhost:8888` into **Settings → My own search engine**. It then takes
over from the built-in route and the button reads **🔎 Search with my own engine**.
It only works on the machine running it, which is why it isn't the default.

### Claude or Gemini

Either can do the searching. Paste a key for whichever you have into **Settings →
Find contacts**; if you fill in only one, that's the one it uses regardless of the
**Which model searches** toggle, since a preference for a provider you have no key
for would just look broken.

| | Where the key comes from | Endpoint |
|---|---|---|
| **Gemini** *(cheaper way in)* | `aistudio.google.com/apikey` | `generativelanguage.googleapis.com`, with Google Search grounding |
| **Claude** | `console.anthropic.com` | `api.anthropic.com`, with server-side web search |

The Gemini model is a settings field defaulting to `gemini-flash-latest`, so you
can point it at a newer one without touching the code. A wrong model name comes
back as "no such model as …", not a silent failure.

**The prompt is tuned for how these models actually fail.** An early Gemini Flash
run returned six people with *every* LinkedIn URL blank, and then explained that it
had left them out to comply with "never construct a URL" — reading a rule against
*fabricating* links as a rule against *reporting* them. So the prompt now says the
opposite explicitly: if a search result shows a profile URL, include it, you are not
vouching for it, it gets checked automatically afterwards, and blanking every URL to
be safe is the wrong answer because it makes the list useless. It also spells out
the searches to run, and that recruiters and engineering leadership are not wanted
however good a match they look — the BU alumni are the point of it.

**📋 Copy the research prompt is always there**, next to whichever search buttons
you have. It puts the full prompt on your clipboard to run in Gemini, Claude or
anything else with web access, and **Paste a reply instead** takes the JSON back.
Every route — built-in search, your own SearXNG, a hosted model, or copy-and-paste —
goes through the same parser and the same review step, so none of them can drift
from the others. The prompt is editable in Settings and carries the same anti-invention rules
as **Copy AI prompt** — a blank URL is explicitly a correct answer, because every
row gets checked anyway.

What gets written: `company` is your company row's name verbatim, `channel` is
LinkedIn, the handle is the profile URL, `role` is the bucket, and the note carries
their real job title plus the verdict and date. **No date** is set — nothing has
been sent, so the 7-day nudge clock stays off until you actually send something.
The company row itself is untouched: **Cold emails sent** stays at *no*, because
it still is. Running it twice on one company skips names already on your list and
tells you how many.

## It opens with no connection

The data was always local — `localStorage`, no backend. The *app* wasn't: losing
signal meant a blank page, which is a strange way for something with no server
to fail. `sw.js` keeps a copy of `index.html` on the device and serves it when
the network can't.

So GitHub is only ever used for **moving data between your devices**. Opening the
app, logging a contact, reading the tables, drafting, the 7-day rule — none of it
needs a network. An amber **Offline** banner says so while you're out, and says
the thing you actually want to know: everything still saves here, and syncing
resumes when you're back.

### Why it's network-first, and not the usual PWA recipe

The standard recipe is cache-first: instant offline, and then it serves you the
old app for a session — or forever, when the update dance goes wrong. **That
failure has already cost this project three rounds of "I don't see any
changes"**, so it's the one outcome the file is written to prevent.

```
online   → fetch it, use it, keep a copy
offline  → serve the copy from the last time you were online
```

Fresh whenever the network can answer, working whenever it can't. The cost is
that a load waits on the network rather than painting from cache — one file from
a CDN, which is a fair price for never wondering which version you're looking at.
This was tested by editing the file and doing a **plain reload** with the worker
active: the change came through.

**Nothing cross-origin is touched.** `api.github.com`, the profile reader, the
model endpoints and the local agent all go straight past. Caching a sync response
is how you'd resurrect deleted contacts; caching a LinkedIn read is how a stale
profile would verify as current.

One honest limit: GitHub Pages sets `Cache-Control: max-age=600` on the file
itself, so for up to **ten minutes** after a push the CDN may still hand back the
previous copy. That's above this layer and can't be configured on Pages. Adding
`?fresh=2` to the URL bypasses it.

### Which build am I looking at?

**Settings → This build** shows the version, whether the offline copy is in
place, and whether you're online right now:

```
Version 2026-08-16a · Offline ready (cache 2026-08-16a) · Online.
```

It exists because "the change didn't work" and "you're looking at last week's
file" are indistinguishable from the outside, and that ambiguity has burned real
time three times now. The version string lives *in the file being executed*, so
it can't lie about which file that is. `Offline ready` only appears once a worker
is genuinely controlling the page — not merely because registration was
attempted.

Opening `index.html` straight off disk (`file://`) has no secure context, so
service workers are unavailable there; Settings says that rather than failing
quietly, and everything except offline mode works as before.

## Every interval is a setting

"How long is too long" was my guess baked into the file. It's yours now, under
**Settings**:

| Setting | Default | Drives |
|---|---|---|
| Nudge after N days of silence | 7 | the red **Needs a nudge** card |
| Note N days after an invite is accepted | 4 | the green **Accepted your invite** card |
| Suggest withdrawing after N days pending | 21 | the amber **Worth withdrawing** card |
| BU alumni to find | 4 | 🔍 Find contacts |
| Engineers in my field to find | 1 | 🔍 Find contacts |
| What counts as my field | mechanical, biomedical, biosensor, wearable, human-machine interaction, human factors | see below |

Every one is read through a helper that falls back to the default on a blank or
nonsense entry, rather than producing a `NaN` day count that quietly never fires.

**The field terms are used four ways, so they can't drift**: the searches 🔎
Search runs (the first four terms, one query each), the check that a field
pick's title actually bears the claim out, the `{fieldwords}` in the contact
research prompt, and the `{fieldwords}` in **Copy AI prompt** — the line that
tells a model what work I'm interested in. Change what you work on and all four
follow, rather than the company hunt and the contact hunt describing you
differently.

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

## The two optional outside services

Everything above works with no network but the GitHub sync. The two LinkedIn
features can each reach one outside service, both **off by default in the sense
that blanking the field disables them**, both visible in Settings:

| Service | Used for | Sees | Turn it off by |
|---|---|---|---|
| the **profile reader** (`https://r.jina.ai/` by default) | reading a public profile from a URL, **and the built-in search** | the profile URL you paste, or the search query | clearing the field — then only pasted page text is parsed, with no request, and 🔎 Search is unavailable |
| `api.anthropic.com` **or** `generativelanguage.googleapis.com` | the search behind 🔍 Find contacts | the company name and role | clearing that API key — Find contacts switches to copy-and-paste |
| **your own SearXNG** | the same search, locally | nothing leaves your machine | clearing the URL |

Both keys are stored **only on that device** (`intern-ai-key`, `intern-gemini-key`, and `readerKey` in
`intern-settings`), never ride the sync, and are only ever sent to their own
service. Neither feature reads anything but the public logged-out view, and
neither touches or automates your LinkedIn account.

Honest limitation: the reader's free anonymous tier **gets throttled for
linkedin.com**, and when it does, LinkedIn serves a sign-in wall instead of the
profile. You'll see this as rows coming back `unverified` with a message saying
so. A free reader API key clears it; pasting the page always works regardless.

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
- **Looking for something you closed?** It's under **View closed contacts** /
  **View closed companies** at the bottom of that table. Tap the row and turn
  **Closed** off to put it back in the live list.

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
