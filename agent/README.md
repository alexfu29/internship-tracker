# The staging agent

Tick people in the tracker and this prepares a personalized message for each
one on your computer, waiting in a list you click through one at a time.
**You send them.** It cannot.

---

## Does it start on its own when I open the website?

**No — and nothing could.** A web page cannot start a program on your computer.
That's a browser security rule, not something the code could be cleverer about:
if `alexfu29.github.io` could launch processes here, so could every other site
you visit. The page can only *talk to* something already running.

**But you only touch PowerShell once, ever.** Run this one line:

```powershell
powershell -ExecutionPolicy Bypass -File agent\install-task.ps1
```

That registers a Windows Scheduled Task. From then on the agent starts itself
**every time you log in**, silently and forever — no console window, no taskbar
entry, nothing on screen. You never run a command again. Open the tracker, tap
**✉ Send queue**, and it's already listening.

Start it right now without logging out:

```powershell
Start-ScheduledTask -TaskName 'Internship staging agent'
```

To undo the whole arrangement: `powershell -ExecutionPolicy Bypass -File agent\install-task.ps1 -Remove`

### If you'd rather not install anything

Run it by hand whenever you want to send a batch, and close it after:

```bash
python agent/stage_agent.py
```

### How do I know it's running?

The tracker tells you. If it isn't running, staging fails immediately with
*"Couldn't reach the staging agent"* and the command to start it — it never
claims success and quietly drops your batch. You can also just ask it:

```bash
curl http://127.0.0.1:8787/ping
```

---

## What it actually does

It's a small web server that only listens on `127.0.0.1` — the loopback
address, reachable from this machine and nowhere else. It is not on your
network and cannot be reached from outside.

The whole thing is one file, `stage_agent.py`, with no installed packages. Six
endpoints, and that is the entire surface:

| Endpoint | What happens |
|---|---|
| `POST /queue` | The tracker hands over a batch of **finished messages** — already personalized, subject already split off. The agent checks each one has a usable address or profile link and stores the batch. |
| `GET /` | The review page. One card at a time: the message as text, Copy buttons, Open compose / Open profile, **✓ Sent — next**. Requires a one-time token it prints at startup. |
| `POST /action` | You ticked Sent / Skip / Undo. Records it in the batch file. Nothing else happens. |
| `POST /setup` | Auto mode only. Opens the real target and loads your clipboard. Stops there. |
| `GET /status` | Tells the website which cards you ticked as sent, so the site can update your tracker. |
| `POST /recorded` | The website confirming it did. Stops the same send being counted twice. |

### The one request it makes to the outside world

Before showing you a card, it re-reads your **public** `data/log.json` from
GitHub — no token, because the file is already public — to check whether that
person replied since you staged them. If they did, the card flips to **"Do not
send"** with the reason and the buttons go dead.

That check exists because of a specific embarrassment: stage a follow-up on
Monday, they reply Monday night, and on Tuesday you send *"I know it's a busy
time of year"* to someone who already answered.

### What it will not do

This matters more than what it does.

| | |
|---|---|
| Send email | No mail library is imported and no mail server is contacted. |
| Send LinkedIn messages | It opens a profile. That is the whole extent of it. |
| Click Send | It never clicks, submits, or presses a key in any window. There is no keystroke injection — something typing into whatever window has focus cannot coexist with you using the computer, which was the point of running it in the background. |
| Take screenshots | None, in either mode. You press the button and you press Send; a photograph of that is a picture of your own work. |
| Write to your tracker | It holds no GitHub token and never PUTs. The website reads `/status` and does its own bookkeeping. |

Check the claims rather than believing them:

```bash
grep -nE "smtplib|sendmail|SMTP|urlopen|https?://" agent/stage_agent.py
```

The only URLs are your own public GitHub file, `mail.google.com` (handed to
your browser as a link, never fetched), and the loopback addresses it listens
on. One `urlopen`, and it's a GET.

---

## Try it before pointing it at anyone real

```bash
python agent/stage_agent.py --demo
```

Five invented people, a full batch, nothing connected to your actual contacts.
Click the whole flow end to end. The header says `DEMO DATA`, and demo cards
are barred from touching your tracker even if you tick them.

---

## Setup

Needs Python 3. No `pip install`, no packages, nothing to build.

First run creates `%LOCALAPPDATA%\internship-agent\config.json`:

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
  "mode": "manual"
}
```

Fill in `fromName` and `fromAddress` with **whichever account you actually send
from** — the card shows it so you can catch a wrong one before you click.
Nothing here is a secret and nothing here sends.

`gmailAccountIndex` is the `/u/<n>` slot. With several Google accounts signed
in, `0` is whichever Google decides is primary — which is exactly how a cold
email goes out from the wrong address. Open Gmail on the account you want and
read the number out of the URL.

---

## The two modes

Set `"mode"` in `config.json` and restart. Neither one sends anything.

### `"manual"` (default)

1. In the tracker, tap **✉ Send queue**, tick people, tap **Stage N**.
2. The review page opens. One card: the message as text, **Copy**, and
   **Open compose** / **Open profile**.
3. Paste, send it yourself, hit **✓ Sent — next**. That card slides away and
   the next is dealt.

### `"auto"`

Adds **▶ Set it up** to each card. Pressing it opens the real target in your
signed-in browser — for email, a Gmail compose window that arrives with **To,
Subject and body already filled** — and puts the note on your clipboard. Then
it stops. It's the fetching and filling done for you; the judgement and the
commit stay yours.

**Setting up the accounts** is just being signed in normally. There are no
credentials to give this thing:

- **Gmail** — be signed in, in your default browser, and set
  `gmailAccountIndex`.
- **LinkedIn** — be signed in. It opens the profile; you click Message and
  paste. LinkedIn is not automated further, deliberately: doing so breaks their
  terms and risks your account.

### Copying is always a button press

Nothing lands on your clipboard on its own. Staging twenty and auto-copying
would leave you holding only the twentieth.

---

## Ticking "Sent" updates your tracker

The agent can't write to your tracker — no token, by design. The website asks
it what you ticked and does the bookkeeping itself, next time you open or
return to the tracker tab:

- **the 7-day clock restarts** for that contact (or, if they had no contact
  date at all, today becomes it);
- **the company's cold-email dot turns on**, so you never go back into the
  company to say you approached them. A LinkedIn note counts: per the tracker's
  own README that flag is the coarse "have I approached this place at all"
  answer, not a claim about the channel.

It never touches **replied**, **meeting booked** or **closed** — those mean
something came *back*, and nothing here knows whether it did.

Double-counting takes two independent failures: the agent won't re-report a job
it has marked recorded, and each write is separately idempotent.

---

## Where things live

```
%LOCALAPPDATA%\internship-agent\
  config.json                 the settings above
  agent.log                   what it did, including the review link
  batches\<batchId>\
    batch.json                the batch, its messages and their state
```

Deliberately **not** in this repo, which is public. `.gitignore` also covers
these names in case anything is ever pointed at the working tree.

---

## When something's wrong

**"Couldn't reach the staging agent"** — it isn't running. `Start-ScheduledTask
-TaskName 'Internship staging agent'`, or run it by hand.

**A card says "Do not send"** — that contact replied, booked a meeting, was
closed or ignored *after* you staged them. If the re-check itself fails, the
page says so and disables sending rather than showing you stale state
confidently.

**"could not re-check the tracker"** — no network, or your log isn't published
yet. Staging still works; only the staleness check is off.

**"▶ Set it up" isn't there** — you're in manual mode. Set `"mode": "auto"` and
restart.

**Clipboard didn't load** — it uses PowerShell, so it's Windows-only. The
compose window still opens filled, and the card says what worked rather than
pretending.

**The dots didn't update** — the website does that, not the agent, and only
while the tracker is open. Open or refocus the tracker tab; a note appears
above the table saying what it recorded.

**Port 8787 in use** — change `port` in the config. `AGENT_BASE` near the top
of the send-queue section in `index.html` has to match.

---

## The one real limitation

The tracker page has to be open **on this computer**. The queue goes straight
from the page to the agent over loopback — it does not travel through your
GitHub sync — so staging from your phone would need a different design and
isn't built.
