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
`6D. SEND QUEUE`, `7. SYNC`). The only other code is `agent/`, which is
**optional and off by default**.

| Where | What |
|---|---|
| `intern-data` | contacts + companies. The synced one — this is `data/log.json` |
| `intern-settings` | templates, prompts, reader/search config. **Never synced** |
| `intern-outbox` | the staged send queue. Device-local; holds message text |
| `intern-pat`, `intern-ai-key`, `intern-gemini-key` | secrets, per device, never synced |

Four things it does beyond logging, each with its own section below:

1. **The 7-day rule** — who's gone quiet, and the red card that says so.
2. **⚡ Auto-populate** — paste a LinkedIn profile, get a filled-in contact.
3. **🔍 Find contacts** — find six people at a company, verified before they land.
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
entirely, into six workspaces at once. Fixing the company row afterwards did
nothing to them: the only way out was deleting the contact and finding them again,
which throws away the search that found them.

**♻ Repopulate** regenerates the draft from what the tracker holds *now*, in
place. Fill in the company, tap it, and the six drafts are right.

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
gets substituted. Delete it and the list is **appended at the end** rather than
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

Both tables start **newest first**, and the **↓** next to `DATE` (or `SENT`) is the
whole indicator: present means date order, absent means your own order.

- **Drag the bars** left of a name to move a row. Dragging *is* the switch to your
  own order — the ↓ disappears the moment you drop.
- **Tap the date header** to go back to newest-first. Tap it again and you're back in
  your own order. It's a straight toggle between the two.
- **Both orders are remembered.** Rearranging doesn't destroy the date sort, and
  sorting by date doesn't destroy your arrangement.

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

**Staging is the only door to the deck**, and the picker used to describe it as
sending your batch off to be "rendered and screenshotted" and left "on the
agent's review page" — none of which had been true since the deck moved into
this dialog. It read as *you need to install something first*, which is a good
reason never to press the button, and without pressing it there is no card, no
**Skip** and no **✓ Sent — next**: just a list of previews and a LinkedIn URL to
copy out by hand. The picker now says what actually happens, and says it
differently if you've switched reviewing to the local agent.

### 🔗 Copy note & open profile

One button, because on LinkedIn it's one action. A Gmail compose window can be
pre-filled straight from a URL; **a LinkedIn connect box can't**, so the note has
to travel on the clipboard, and having to come back to the deck for it after
opening the profile is the step that makes a batch feel like work.

It copies **before** it opens, which is not cosmetic: a clipboard write needs
this document focused and the new tab takes that away. Both happen inside the one
click, so the popup blocker still sees a real gesture.

Email is unchanged — **✉ Open compose** already carries the subject and body into
the compose window, so there is nothing to copy.

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

### Five drafts, and you never pick one

There are **five** templates on two axes — the channel you're writing in, and
whether this is the first message or a chase:

| | First message | Follow-up |
|---|---|---|
| **Email** | Email · first message | Email · follow-up |
| **LinkedIn** | LinkedIn · first message *(applied / not applied)* | LinkedIn · follow-up |

A LinkedIn note and a cold email are not the same piece of writing — one goes in
a connection request and has to be short — so they're separate templates rather
than one draft you reword every time.

**The app picks from the contact's channel**, so there's no dropdown and no
choosing. The LinkedIn first message has two versions and the **Companies** table
decides between them: marked **Applied** gets the "I recently applied…" wording,
anything else gets the one that makes no such claim.

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
| `{learn}` | "you" for a recruiter, "your work" for an engineer |

`{role}` and `{internship}` are easy to confuse and are not the same thing.
`{role}` is the **person's** bucket — `Hiring`, `VP Eng`, `BU Eng`.
`{internship}` is the job **you** applied to, which lives on the company row
because it's the same for everyone you know there. A draft saying "I applied to
the Marotta VP Eng" is what using the wrong one looks like.

There are **four** templates. `applied` and `connect` are the short LinkedIn
connect notes used by ⚡ Auto-populate; `outreach` and `followup` are the emails.

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

### Their role is a bucket, not a job title

The `role` field on an auto-populated contact holds one of exactly three values,
because when you're scanning a list of people to approach, their literal title
isn't the thing you need:

| Bucket | Who, and why it matters |
|---|---|
| `Hiring` | the **recruiting function** — talent acquisition, recruiters, sourcers, HR, People. Not anyone whose headline happens to say "hiring": LinkedIn is full of *"We're hiring!"*, and that was landing VPs of Engineering here |
| `VP Eng` | engineering leadership — more power, harder to reach. EVP/SVP count |
| `BU Eng` | **Boston University** engineers there — least gatekeeping, by far the easiest yes, because you already share something |

`BU Eng` is deliberately **not** "any engineer". The BU connection is the entire
point of the bucket, so it's set from Boston University actually appearing in
their **Education** — never guessed from a job title, and never from the rest of
the page. Their real title isn't thrown away: the
preview shows it (`filed as VP Eng · LinkedIn says "Chairman and CEO"`) so you can
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
is used there and it only decides which pair to *try* someone in. The profile read
is what settles it.

### The draft, and the claim it won't make

The Note is drafted from your **companies table**, not from the person:

- that company is in your list and marked **Applied** → the `applied` draft,
  *"I recently applied to the {company} {internship} for 2027…"*
- anything else → the `connect` draft, which says the same thing minus any claim
  that you applied.

The app will not put an application you didn't make into your own outbox, so the
companies table decides. The status line always says which draft it used and why.
If the Note already has text, the draft is **appended** after a blank line.

### Company names get matched to your list

The profile says "Marotta Controls, Inc."; you track "Marotta". Left alone that's
two companies, a split list, and a silently broken Applied lookup. So names are
compared with the decoration stripped (`Inc`, `LLC`, punctuation) and on a
whole-word prefix, and **the spelling already in your tracker wins**. The preview
tells you when it substituted. `Boston Scientific` and `Boston Dynamics` don't
match each other — neither is a prefix of the other.

## 🔍 Find contacts

On a company's edit dialog: up to six people at that company, in three pairs —
two `Hiring`, two `VP Eng`, two `BU Eng`. A pair comes back **empty with a note**
rather than padded. Four stages, and **nothing reaches your log until the last
one**:

```
find    → pool every query, bucket by job title, score, take two per pair
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
| `check this` | read, but something disagrees — different employer, a `BU Eng` row whose **Education** doesn't confirm BU (or that has no Education section to confirm it against), or a title that doesn't read like leadership on a `VP Eng` row |
| `unverified` | couldn't be read at all, or there was no profile link |

`verified` means **the profile page agreed** — not that this is the right person
to write to. Read the six before you send anything.

A **sign-in wall counts as a failure, not a profile.** LinkedIn answers a reader
it doesn't like with a signup or "Security verification" page, and those parse
perfectly happily — the heading is just "Join LinkedIn". Without that check a
challenge page becomes a confidently wrong contact, which is worse than a failed
read, so any page that looks like a wall is forced to `unverified`.

Each created contact also gets **the draft already written into its workspace**,
ready to send. Six people with six empty workspaces is six more things to do by
hand, which was the thing this was meant to save.

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

#### Which pair someone lands in

**The query that found you doesn't decide your bucket — your job title does.**
A search for `recruiter` happily returns a VP, and filing them under Hiring
makes the app assert something it never established. It also feeds `{learn}`, so
a mis-filed engineer gets a draft offering to "learn more about *you*".

Every query runs, results are pooled, then each person is bucketed from their own
title. Three details worth knowing:

- **Hiring means the recruiting function** — talent acquisition, recruiter,
  sourcer, HR, People — not anyone whose headline says "hiring". LinkedIn
  headlines are full of *"We're hiring!"*, and that alone was putting VPs of
  Engineering in the Hiring pair.
- **EVP/SVP count as leadership.** `\bvp\b` cannot match inside "EVP", so an EVP
  of Technology used to land in no bucket at all.
- **A BU pick requires Boston University in the evidence.** Everyone the BU query
  returns works at the company, so without the school there's nothing left
  distinguishing them. The pair comes back **empty with a note** rather than
  naming two strangers — the same rule as `⚡ Auto-populate`: never guessed.
  At the verify stage that tightens to their **Education** specifically — see
  "Where the BU evidence comes from".

#### Picking two out of dozens

With a pool that deep, *which* two matters more than how many were found, so hits
are scored:

| Signal | Why |
|---|---|
| their headline names the employer | strongest evidence it's the right person |
| **extra organisation words dock heavily** | `Lexington Medical Center` is an unrelated hospital, and `sameCompany()` matches it *on purpose* — that prefix rule is what makes "Marotta" find "Marotta Controls, Inc." |
| the company appears **only in their name** earns nothing | a search for Draper returns Kristen Draper, who recruits for someone else |
| exec needs engineering **and** leadership, docked separately | a Senior Mechanical Engineer is the right field but not leadership; a Guest Services Manager is the reverse |

Checked across Draper, Whoop, Marotta Controls, Boston Scientific and Medtronic:
hiring and engineering leadership land the right people in all five.

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
the three searches to run, and that a Director of Talent Acquisition counts as a
hiring contact even though the title doesn't say "engineering" — the same run missed
exactly that person.

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
