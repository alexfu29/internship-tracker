# The staging agent

Tick people in the tracker, and this stages a personalized message for each one
on your computer: rendered, screenshotted, and waiting in a list you click
through. **You send them.** It cannot.

## What it will not do

This matters more than what it does, so it's first.

| | |
|---|---|
| Send email | No mail library is imported and no mail server is contacted. |
| Send LinkedIn messages | It opens a profile in your browser. That's the whole extent of it. |
| Click Send | It never clicks, submits, or presses a key in any window. There is no keystroke injection — something typing into whatever window has focus can't coexist with you using the computer. |
| Write to your tracker | It holds no GitHub token and never PUTs. The website reads `/status` from it and does its own bookkeeping. |
| Look at the screenshots | Captured and displayed. Nothing reads them, nothing is uploaded. |
| Touch the network, mostly | One request exists: a read-only GET of your **public** `data/log.json`, so a staged card can notice someone replied since you queued them. |

You can check the first and last of those yourself rather than taking my word:

```bash
grep -nE "smtplib|sendmail|SMTP|urlopen|https?://" agent/stage_agent.py
```

The only URLs are your own GitHub raw file, `mail.google.com` (handed to your
browser as a link, never fetched), and the loopback addresses it listens on.

## Try it before pointing it at anyone real

```bash
python agent/stage_agent.py --demo
```

Five invented people, a full batch, nothing connected to your actual contacts.
It opens the review page and you can click the whole flow end to end. The header
says `DEMO DATA` so a demo run can never be mistaken for a real one.

## Setup

Needs Python 3 and Chrome. No `pip install`, no packages, nothing to build.

```bash
python agent/stage_agent.py
```

It prints a review-page link and creates `%LOCALAPPDATA%\internship-agent\config.json`:

```json
{
  "fromName": "",
  "fromAddress": "",
  "gmailAccountIndex": 0,
  "port": 8787,
  "owner": "alexfu29",
  "repo": "internship-tracker",
  "branch": "main",
  "openBrowserOnStage": true,
  "mode": "manual",
  "autoSettleSeconds": 3
}
```

Fill in `fromName` and `fromAddress` with **whichever account you're actually
sending from** — the preview card shows it so you can catch a wrong one before
you click. Nothing here is a secret and nothing here sends: these only decide
what the card claims and which Gmail tab the compose link opens in.

`gmailAccountIndex` is the `/u/<n>` slot. If you're signed into several Google
accounts, `0` is whichever Google decides is primary — which is exactly how a
cold email goes out from the wrong address. Open Gmail on the account you want
and read the number out of the URL.

### Run it in the background

```powershell
powershell -ExecutionPolicy Bypass -File agent\install-task.ps1
```

Registers a logon task running `pythonw.exe`, which has no console window at
all. Nothing appears on screen and nothing steals focus — the screenshots are
rendered offscreen. `-Remove` unregisters it.

## The two modes

Set `"mode"` in `config.json` and restart. Neither one sends anything.

### `"manual"` (default)

1. In the tracker, tap **✉ Send queue**, tick people, tap **Stage N**.
2. The review page opens. One card at a time: the message as text, a **Copy**
   button, and **Open compose** / **Open profile**.
3. Paste, send it yourself, hit **✓ Sent — next**. The card slides away and the
   next is dealt.

There's no screenshot here on purpose — a picture of text sitting next to that
same text isn't evidence of anything.

### `"auto"`

Adds a **▶ Set it up** button to each card. Pressing it:

1. opens the real target in your real signed-in browser — for email that's a
   Gmail compose window that arrives with **To, Subject and body already
   filled**;
2. puts the note on your real clipboard (for LinkedIn, ready to paste);
3. waits `autoSettleSeconds` for the window to paint, then **photographs your
   actual screen** and shows that on the card.

Then it stops. It does not click Send. *Here* the screenshot means something:
it's a state you didn't assemble by hand, captured at the moment before you
commit.

**Setting up the accounts** is just being signed in normally — there are no
credentials to give this thing:

- **Gmail** — be signed in, in your default browser. Set `gmailAccountIndex`
  to the right `/u/<n>` slot (open Gmail on the account you want and read the
  number out of the URL). With several accounts signed in, `0` is whichever
  Google decides is primary, which is exactly how a message goes out from the
  wrong address.
- **LinkedIn** — be signed in. It opens the person's profile; you click Message
  and paste. LinkedIn is not automated any further, deliberately: doing so
  breaks their terms and risks your account.

One caveat: the screen capture photographs **the whole screen**, including
whatever else is on it. The images stay in `%LOCALAPPDATA%`, never in the repo.

## Copying is always a button press

Nothing lands on your clipboard on its own. Staging twenty and auto-copying
would leave you holding only the twentieth.

## Ticking "Sent" updates your tracker

The agent can't write to your tracker — no token, by design. Instead the
website asks it what you ticked, and does the bookkeeping itself the next time
you open or return to the tracker tab:

- **the 7-day clock restarts** for that contact (or, if they had no contact
  date at all, today becomes it);
- **the company's cold-email dot turns on**, so you don't have to go back into
  the company and say you approached them. A LinkedIn note counts: per the
  tracker's own README that flag is the coarse "have I approached this place at
  all" answer, not a claim about the channel.

It never touches **replied**, **meeting booked** or **closed** — those mean
something came *back*, and nothing here knows whether it did.

Double-counting takes two independent failures: the agent won't re-report a
job it has marked recorded, and each write is separately idempotent (today
isn't added to the nudge list twice, and a dot already on is left alone).

## Where things live

```
%LOCALAPPDATA%\internship-agent\
  config.json                     settings above
  agent.log                       what it did, including the review link
  batches\<batchId>\
    batch.json                    the batch and its state
    <jobId>.html / <jobId>.png    the preview and its screenshot
```

Deliberately **not** in this repo, which is public. `.gitignore` also covers
these names in case anything is ever pointed at the working tree.

## When something's wrong

**"Couldn't reach the staging agent"** — it isn't running. Start it, or
`Start-ScheduledTask -TaskName 'Internship staging agent'`.

**A card says "Do not send"** — that contact replied, booked a meeting, was
closed or ignored *after* you staged them. The agent re-reads your published
log and voids the card rather than letting you send "I know it's a busy time of
year" to someone who answered. If the re-read fails, it says so and disables
sending instead of showing you stale state confidently.

**"could not re-check the tracker"** — no network, or your log isn't published
yet. Staging and screenshots still work; only the staleness check is off, and
the page tells you.

**"▶ Set it up" isn't there** — you're in manual mode. Set `"mode": "auto"` and
restart the agent.

**Screen capture failed** — it uses PowerShell and .NET, so it's Windows-only.
Everything else in auto mode still works; you just lose the picture, and the
card says so rather than pretending.

**The dots didn't update** — the website does that, not the agent, and only
when the tracker is open. Open or refocus the tracker tab; a note appears above
the table saying what it recorded.

**Port 8787 in use** — change `port` in the config. `AGENT_BASE` near the top of
the send-queue section in `index.html` has to match.

## A caveat worth knowing

The tracker page has to be open **on this computer** for the queue to reach the
agent — it's a direct loopback connection, not something that travels through
your GitHub sync. Queuing from your phone would need a different design and
isn't built.
