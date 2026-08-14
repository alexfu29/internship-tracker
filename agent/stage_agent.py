#!/usr/bin/env python3
"""
Internship tracker — local staging agent.

WHAT THIS DOES
    The tracker website (github.io or a local clone) POSTs a batch of already
    rendered outreach messages to this agent over loopback. The agent serves a
    review page where you work down the list one card at a time: read the
    message, copy it, open the compose window or the profile, send it yourself,
    tick it off and the next one is dealt.

TWO MODES, NEITHER OF WHICH SENDS
    manual  - the card shows the finished message as text; you copy it and
              open the compose window or profile yourself.

    auto    - one button does the fetching: it opens the real compose window
              (Gmail's link arrives with to/subject/body already filled) and
              puts the note on your real clipboard. Then it stops.

    In both, every action that leaves this machine is one you took. There are
    no screenshots: you pressed the button and you press Send, so a photograph
    of that is a picture of your own work, and evidence of nothing.
    Set "mode" in config.json.

WHAT THIS DOES NOT DO — and cannot, because the code isn't here
    * It does not send email. No mail library is imported and no mail server is
      contacted. (Grep this file for the obvious names - they are deliberately
      not written here, so a clean grep is real proof rather than a promise.)
    * It does not send LinkedIn messages. It opens a profile; you do the rest.
    * It does not click Send, submit a form, or press a key in any window.
      There is no keystroke injection: something that types into whatever
      window has focus cannot coexist with you using the computer, which was
      the entire point of running this in the background.
    * It does not write to your tracker. It has no GitHub token and never PUTs.
      The website reads /status from it and does its own bookkeeping.

    The single outbound request in this whole file is a read-only GET of the
    public data/log.json, used to notice that someone replied since you staged
    their follow-up. Everything else is local.

WHERE THINGS LIVE
    Code:    this file, in the repo.
    Runtime: %LOCALAPPDATA%\\internship-agent\\  — config, staged batches, log.
             Deliberately outside the repo, which is public: nothing here can
             be swept up by `git add -A`.

RUN
    python agent/stage_agent.py            (console, shows the log)
    pythonw agent/stage_agent.py           (silent, for the Scheduled Task)
"""

import base64
import html
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path

APP_NAME = "internship-agent"
VERSION = "1.0"
HOST = "127.0.0.1"
DEFAULT_PORT = 8787

# Not a setting - the absence of send/write code. It exists so the UI can
# state the fact, not so anyone can flip it.
TEST_MODE = True

# Origins allowed to hand us a batch. A JSON content-type forces a CORS
# preflight, so pinning these actually keeps other pages you visit from
# quietly staging things here.
ALLOWED_ORIGINS = {
    "https://alexfu29.github.io",
    "http://localhost:8765",
    "http://127.0.0.1:8765",
}

VALID_KINDS = {"outreach", "followup", "applied", "connect", "liFollowup"}
EMAIL_KINDS = {"outreach", "followup"}

# A rendered draft still carrying one of these means the tracker had no value
# for it. fillTemplate() emits them on purpose so you notice before sending.
PLACEHOLDER_RE = re.compile(
    r"\[(first|name|company|role|date|days|channel|internship|learn)\]"
)

STATE_STAGED = "staged"
STATE_SENT = "sent"
STATE_SKIPPED = "skipped"
STATE_VOIDED = "voided"


# ----------------------------------------------------------------------------
# paths and config
# ----------------------------------------------------------------------------

def data_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME")
    if not base:
        base = str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


ROOT = data_root()
BATCH_DIR = ROOT / "batches"
CONFIG_PATH = ROOT / "config.json"
LOG_PATH = ROOT / "agent.log"

DEFAULT_CONFIG = {
    "_comment": (
        "Sending identity. Nothing here is secret and nothing here sends "
        "anything - it only decides what the preview card claims and which "
        "Gmail account the compose link opens in."
    ),
    "fromName": "",
    "fromAddress": "",
    "gmailAccountIndex": 0,
    "port": DEFAULT_PORT,
    "owner": "alexfu29",
    "repo": "internship-tracker",
    "branch": "main",
    "openBrowserOnStage": True,
    "mode": "manual",
}


def log(msg: str) -> None:
    line = "%s  %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        ROOT.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass
    try:
        print(line, flush=True)
    except (OSError, ValueError):
        pass  # pythonw has no stdout


def load_config() -> dict:
    ROOT.mkdir(parents=True, exist_ok=True)
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            on_disk = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(on_disk, dict):
                cfg.update(on_disk)
        except (OSError, ValueError) as exc:
            log("config.json unreadable (%s) - using defaults" % exc)
    else:
        try:
            CONFIG_PATH.write_text(
                json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8"
            )
            log("wrote a starter config at %s" % CONFIG_PATH)
        except OSError as exc:
            log("could not write config.json: %s" % exc)
    return cfg


CONFIG = load_config()


# ----------------------------------------------------------------------------
# links
# ----------------------------------------------------------------------------

def safe_external_url(raw: str) -> str:
    """
    Nothing in the tracker validates the handle field, and the review page
    carries a session token - so a javascript: value pointed at it would be a
    real hole. Only http(s) survives. A scheme-less linkedin.com/in/x gets
    https:// added, matching the site's own linkHref rule.
    """
    s = (raw or "").strip()
    if not s:
        return ""
    if re.match(r"^https?://", s, re.I):
        pass
    elif re.match(r"^[a-z][a-z0-9+.-]*:", s, re.I):
        return ""  # some other scheme - refuse it outright
    else:
        s = "https://" + s
    parsed = urllib.parse.urlparse(s)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return ""
    return s


def gmail_compose_url(to: str, subject: str, body: str) -> str:
    idx = CONFIG.get("gmailAccountIndex", 0)
    try:
        idx = int(idx)
    except (TypeError, ValueError):
        idx = 0
    q = urllib.parse.quote

    # quote(), not quote_plus(): a literal "+" surviving into a Gmail body is
    # exactly the kind of thing nobody notices.
    return (
        "https://mail.google.com/mail/u/%d/?view=cm&fs=1&to=%s&su=%s&body=%s"
        % (idx, q(to or "", safe=""), q(subject or "", safe=""), q(body or "", safe=""))
    )


# ----------------------------------------------------------------------------
# auto mode — set the message up for real, and stop before Send
#
# What "auto" means here, precisely: open the real compose window or profile
# in your real signed-in browser and put the note on your real clipboard. Then
# it stops. It does not click Send, does not submit a form, and does not press
# a key in anyone else's window. The last action is always yours.
#
# There is no keystroke injection anywhere in here on purpose. Something that
# types into whatever window happens to be focused cannot coexist with you
# using the computer, which was the whole point of running this in the
# background.
# ----------------------------------------------------------------------------

def auto_enabled() -> bool:
    return str(CONFIG.get("mode") or "manual").lower() == "auto"


def _powershell(script: str, timeout: int = 25) -> tuple:
    """Run a PowerShell snippet with no window. Returns (ok, message)."""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    if proc.returncode != 0:
        return False, (proc.stderr.decode("utf-8", "replace").strip()[:200]
                       or "exit %d" % proc.returncode)
    return True, proc.stdout.decode("utf-8", "replace").strip()


def set_clipboard(text: str) -> tuple:
    """
    One card's text, on demand. Deliberately never done for a whole batch:
    copying twenty in a row would leave you holding only the twentieth.

    The text goes over as base64 inside the command rather than through a temp
    file. No file means nothing to mislay between writing and reading it, and
    the note never touches disk. Base64 rather than raw because PowerShell
    reads stdin in the console codepage, which turns the em dash in the
    follow-up template into mojibake.
    """
    if os.name != "nt":
        return False, "clipboard is Windows-only here"
    if not text:
        return False, "nothing to copy"
    b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return _powershell(
        "Set-Clipboard -Value ([Text.Encoding]::UTF8.GetString("
        "[Convert]::FromBase64String('%s')))" % b64)


# ----------------------------------------------------------------------------
# the message, as it appears on a review card
# ----------------------------------------------------------------------------

def mark_placeholders(escaped: str) -> str:
    """Highlight [company] and friends. Runs on already-escaped html."""
    return PLACEHOLDER_RE.sub(lambda m: '<span class="ph">%s</span>' % m.group(0),
                              escaped)


def sender_line() -> str:
    ident = CONFIG.get("fromAddress") or ""
    name = CONFIG.get("fromName") or ""
    if ident and name:
        return "%s <%s>" % (name, ident)
    if ident or name:
        return ident or name
    return "(not configured - set fromName / fromAddress in config.json)"


def message_block(job: dict) -> str:
    """
    The message itself, on the card, as text. This is the thing you are about
    to paste, so it is shown rather than pictured - and it is the same string
    the Copy button hands you, taken from one place, so the two cannot drift.
    """
    e = html.escape
    is_email = job.get("channel") == "Email" or job.get("kind") in EMAIL_KINDS
    target = job.get("to") if is_email else job.get("profileUrl")

    rows = [("From", e(sender_line())),
            ("To", e(target or "(nothing on file)"))]
    row_html = "".join(
        '<div class="mrow"><div class="k">%s</div><div class="v">%s</div></div>'
        % (k, v) for k, v in rows)

    subj = job.get("subject") or ""
    if is_email:
        if subj:
            subj_html = '<div class="msubj">%s</div>' % mark_placeholders(e(subj))
        else:
            subj_html = ('<div class="msubj none">no subject line - check this '
                         'template in Settings</div>')
    else:
        subj_html = ""

    return ('<div class="msg"><div class="mhdr">%s</div>%s'
            '<div class="mbody">%s</div></div>'
            % (row_html, subj_html, mark_placeholders(e(job.get("body") or ""))))


# ----------------------------------------------------------------------------
# batch store
# ----------------------------------------------------------------------------

STORE_LOCK = threading.Lock()


def batch_path(batch_id: str) -> Path:
    return BATCH_DIR / batch_id / "batch.json"


def safe_batch_id(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(raw or ""))[:64]


def save_batch(batch: dict) -> None:
    p = batch_path(batch["batchId"])
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(batch, indent=2), encoding="utf-8")
    tmp.replace(p)


def load_batches() -> list:
    out = []
    if not BATCH_DIR.exists():
        return out
    for folder in BATCH_DIR.iterdir():
        p = folder / "batch.json"
        if not p.exists():
            continue
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            log("skipping unreadable batch %s: %s" % (folder.name, exc))
    out.sort(key=lambda b: b.get("stagedAt", ""), reverse=True)
    return out


# ----------------------------------------------------------------------------
# staleness — the only outbound request in this file, and it is a GET
# ----------------------------------------------------------------------------

_remote_cache = {"at": 0.0, "contacts": None, "error": ""}


def fetch_remote_contacts() -> tuple:
    """
    Read the public data/log.json so a staged card can notice that its contact
    replied since you queued them. Returns (contacts_or_None, error_string).
    No token: the repo is public, and this agent deliberately holds no
    credentials.
    """
    now = time.time()
    if _remote_cache["contacts"] is not None and now - _remote_cache["at"] < 60:
        return _remote_cache["contacts"], _remote_cache["error"]
    if _remote_cache["error"] and now - _remote_cache["at"] < 60:
        return None, _remote_cache["error"]

    url = ("https://raw.githubusercontent.com/%s/%s/%s/data/log.json"
           % (CONFIG.get("owner"), CONFIG.get("repo"), CONFIG.get("branch")))
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "internship-stage-agent/%s" % VERSION}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        contacts = payload.get("contacts") or {}
        _remote_cache.update({"at": now, "contacts": contacts, "error": ""})
        return contacts, ""
    except (urllib.error.URLError, ValueError, OSError, TimeoutError) as exc:
        msg = "could not re-check the tracker (%s)" % exc
        _remote_cache.update({"at": now, "contacts": None, "error": msg})
        return None, msg


def void_reason(contact: dict) -> str:
    """Why this person should no longer be written to. Mirrors needsNudge()."""
    if contact.get("deleted"):
        return "this contact has been deleted"
    if contact.get("responded"):
        return "they replied"
    if contact.get("meetingOn"):
        return "a meeting is booked (%s)" % contact.get("meetingOn")
    if contact.get("closed"):
        return "the entry is closed"
    if contact.get("muted") is True:
        return "you marked this one Ignored"
    return ""


def revalidate(batches: list) -> str:
    """Flip staged jobs to voided when the tracker has moved on. Returns a
    warning string when the check could not run."""
    contacts, err = fetch_remote_contacts()
    if contacts is None:
        return err
    for b in batches:
        changed = False
        for job in b.get("jobs", []):
            if job.get("state") != STATE_STAGED:
                continue
            c = contacts.get(job.get("contactId"))
            if not c:
                continue  # not synced yet - absence is never evidence
            reason = void_reason(c)
            if reason:
                job["state"] = STATE_VOIDED
                job["voidReason"] = reason
                job["voidedAt"] = stamp()
                changed = True
        if changed:
            save_batch(b)
    return ""


def stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------------------------------------------------------
# review page
# ----------------------------------------------------------------------------

REVIEW_CSS = """
  * { box-sizing: border-box; }
  body { margin: 0; padding: 0 0 60px; background: #eceae5; color: #23211d;
         font: 15px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }
  header { position: sticky; top: 0; z-index: 5; background: #23211d; color: #f4f2ee;
           padding: 14px 22px; display: flex; align-items: center; gap: 16px;
           flex-wrap: wrap; }
  header h1 { font-size: 16px; margin: 0; font-weight: 700; }
  header .count { font-size: 13px; color: #b9b5ac; }
  header .spacer { flex: 1; }
  header .demo { background: #8a5a00; border-radius: 999px; padding: 3px 10px;
                 font-size: 11px; font-weight: 700; letter-spacing: .04em; }
  .test { background: #8a5a00; color: #fff; padding: 10px 22px; font-size: 13px;
          font-weight: 700; }
  .warn { background: #7a2622; color: #fff; padding: 10px 22px; font-size: 13px; }
  main { max-width: 1000px; margin: 22px auto; padding: 0 18px;
         display: flex; flex-direction: column; gap: 20px; }

  /* One at a time. The deck shows the card you're on; finishing it slides
     that card away and deals the next, so a batch of twenty is twenty
     identical gestures in one place instead of a page you scroll and lose
     your position in. */
  .progress { display: flex; align-items: center; gap: 12px; font-size: 13px;
              color: #57544e; font-weight: 600; }
  .bar { flex: 1; height: 6px; background: #d6d3cc; border-radius: 999px;
         overflow: hidden; }
  .bar i { display: block; height: 100%; background: #2f6b47; width: 0;
           transition: width .35s ease; }
  .deck { position: relative; }
  /* Only the top of the deck is on screen. Removing it promotes the next one
     with no JS bookkeeping, so the visible card and the queue can't disagree. */
  #deck > .job ~ .job { display: none; }
  .job { background: #fff; border: 1px solid #d6d3cc; border-radius: 12px;
         overflow: hidden; }

  /* Every card is the same height and the message scrolls inside it, so the
     buttons land in exactly the same place on every card. You press the same
     button twenty times in a row - it must not move because one person's
     draft ran three lines longer than the last. */
  #deck > .job { display: flex; flex-direction: column;
                 height: min(74vh, 660px); }
  #deck > .job .msg { flex: 1 1 auto; overflow-y: auto; min-height: 0; }
  #deck > .job .jh, #deck > .job .voidmsg, #deck > .job .noshot,
  #deck > .job .acts, #deck > .job .url { flex: 0 0 auto; }
  #deck > .job .acts { border-top: 1px solid #e6e3dc; background: #faf9f6; }
  #deck > .job .done-all { margin: auto; }
  .job.leaving { animation: away .28s ease forwards; }
  @keyframes away {
    to { opacity: 0; transform: translateX(-26px) scale(.98); }
  }
  @media (prefers-reduced-motion: reduce) {
    .job.leaving { animation-duration: .01s; }
    .bar i { transition: none; }
  }
  .done-all { text-align: center; padding: 54px 20px; }
  .done-all .big { font-size: 30px; margin-bottom: 10px; }
  .rest { margin-top: 8px; }
  .rest summary { cursor: pointer; font-size: 13px; font-weight: 600;
                  color: #57544e; padding: 8px 2px; }
  .rest .job { margin-top: 12px; }
  .job.done { opacity: .5; }
  .job.void { border-color: #b4514b; }
  .jh { padding: 13px 18px; display: flex; align-items: center; gap: 10px;
        flex-wrap: wrap; border-bottom: 1px solid #e6e3dc; }
  .jh .who { font-weight: 700; }
  .jh .co { color: #6f6c65; }
  .pill { font-size: 11px; font-weight: 700; border-radius: 999px; padding: 3px 9px;
          border: 1px solid #c9c5bc; color: #57544e; text-transform: uppercase;
          letter-spacing: .03em; }
  .pill.li { border-color: #2a5d9f; color: #2a5d9f; }
  .pill.em { border-color: #2f6b47; color: #2f6b47; }
  .pill.state { border-color: #8a5a00; color: #8a5a00; }
  .voidmsg { background: #fbeceb; color: #7a2622; padding: 10px 18px;
             font-size: 13px; font-weight: 600; }
  /* the message itself, shown as text because that's what you're pasting */
  .msg { border-bottom: 1px solid #e6e3dc; }
  .mhdr { padding: 12px 18px; border-bottom: 1px solid #f0eee8; }
  .mrow { display: flex; gap: 10px; padding: 2px 0; font-size: 13.5px; }
  .mrow .k { flex: 0 0 46px; color: #6f6c65; font-weight: 600; }
  .mrow .v { color: #23211d; word-break: break-word; }
  .msubj { padding: 11px 18px; font-size: 16px; font-weight: 700;
           border-bottom: 1px solid #f0eee8; }
  .msubj.none { color: #a33; font-weight: 600; font-size: 13.5px; }
  .mbody { padding: 16px 18px; white-space: pre-wrap; font-size: 14.5px;
           line-height: 1.6; }
  .ph { background: #ffe9b8; border-radius: 3px; padding: 0 3px;
        font-weight: 700; color: #7a4d00; }
  .noshot { padding: 11px 18px; color: #7a4d00; background: #fdf3df;
            font-size: 13px; font-weight: 600;
            border-bottom: 1px solid #e6e3dc; }
  .acts { padding: 13px 18px; display: flex; gap: 9px; align-items: center;
          flex-wrap: nowrap; }
  .acts .right { margin-left: auto; display: flex; gap: 9px; align-items: center;
                 flex: 0 0 auto; }
  .acts > button, .acts > a.btn { flex: 0 0 auto; }
  button, a.btn { font: inherit; font-size: 13.5px; font-weight: 600;
          padding: 8px 13px; border-radius: 8px; border: 1px solid #c9c5bc;
          background: #f7f5f1; color: #23211d; cursor: pointer;
          text-decoration: none; display: inline-block; }
  button:hover, a.btn:hover { background: #ece9e3; }
  button:disabled { opacity: .4; cursor: not-allowed; }
  .primary { background: #23211d; color: #f4f2ee; border-color: #23211d; }
  .primary:hover { background: #3a3630; }
  /* One line, always - it wraps to two for long compose links otherwise, and
     that alone would move the buttons between cards. */
  .url { padding: 9px 18px 0; font-size: 11.5px; color: #8b8780;
         white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .empty { text-align: center; color: #6f6c65; padding: 60px 20px; }
  .ok { color: #2f6b47; font-weight: 700; font-size: 13px; }
"""

REVIEW_JS = """
function copy(id, btn) {
  var t = document.getElementById(id).textContent;
  var done = function () {
    var old = btn.textContent;
    btn.textContent = "\\u2713 Copied";
    setTimeout(function () { btn.textContent = old; }, 1500);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(t).then(done, function () { fallback(t, done); });
  } else { fallback(t, done); }
}
function fallback(t, done) {
  var ta = document.createElement("textarea");
  ta.value = t; ta.style.position = "fixed"; ta.style.opacity = "0";
  document.body.appendChild(ta); ta.select();
  try { document.execCommand("copy"); done(); } catch (e) { alert(t); }
  document.body.removeChild(ta);
}
/* Auto mode: open the real target and load the clipboard. It stops there —
   the send is still your click. */
function setup(batch, job, btn) {
  var old = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Setting up\\u2026";
  fetch("/setup", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ batchId: batch, jobId: job })
  }).then(function (r) { return r.json(); })
    .then(function (j) {
      if (!j.ok) { alert("Couldn't set that up: " + j.error); btn.disabled = false;
                   btn.textContent = old; return; }
      location.reload();
    })
    .catch(function (e) {
      alert("Couldn't set that up: " + e);
      btn.disabled = false; btn.textContent = old;
    });
}

function act(batch, job, state, el) {
  fetch("/action", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ batchId: batch, jobId: job, state: state })
  }).then(function (r) {
    if (!r.ok) throw new Error("agent said no");
    return r.json();
  }).then(function () { advance(el); })
    .catch(function (e) { alert("Could not record that: " + e); });
}

/* Slide the finished card away and deal the next one, rather than reloading
   into a long list you have to find your place in again. */
function advance(el) {
  var card = el ? el.closest(".job") : null;
  // Undo from the "already handled" block puts a card back into the deck,
  // which is a reshuffle rather than an advance - reload and re-deal.
  if (!card || !card.closest("#deck")) { location.reload(); return; }
  card.classList.add("leaving");
  setTimeout(function () {
    card.remove();
    // "left" counts real job cards; the end-of-batch panel is not one, so it
    // can't be mistaken for something still owed.
    var left = document.querySelectorAll("#deck .job .acts").length;
    var total = +document.body.dataset.total || 0;
    var doneN = Math.max(0, total - left);
    var bar = document.getElementById("bar");
    var lbl = document.getElementById("plabel");
    if (bar) bar.style.width = (total ? (doneN / total) * 100 : 100) + "%";
    if (lbl) lbl.textContent = left
      ? doneN + " of " + total + " done \\u00b7 " + left + " to go"
      : "all " + total + " done";
    if (!left) {
      var deck = document.getElementById("deck");
      if (deck) deck.innerHTML =
        '<div class="job"><div class="done-all"><div class="big">\\u2713</div>' +
        "<strong>That's the batch.</strong><br>" +
        "<span style='color:#6f6c65;font-size:13.5px'>Nothing was sent by this " +
        "agent \\u2014 you sent them. Your tracker has not been changed.</span>" +
        "</div></div>";
    }
  }, 260);
}
"""


def render_review(batches: list, warning: str) -> str:
    """
    The deck holds only what still needs you, one card at a time. Everything
    already dealt with collapses into a details block, so finishing the batch
    is the same gesture repeated rather than a scroll you lose your place in.
    """
    e = html.escape
    live, handled, demo = [], [], False

    for b in batches:
        if b.get("demo"):
            demo = True
        for job in b.get("jobs", []):
            (live if job.get("state", STATE_STAGED) == STATE_STAGED
             else handled).append((b, job))

    # Progress describes the work in front of you *now*, not every batch ever
    # staged. Counting old handled jobs made the total climb forever and the
    # fraction stop meaning anything ("3 of 47 done"). So the page opens with
    # however many are still waiting, and counts up as you clear them; the
    # older ones live in their own collapsed section with their own count.
    total = len(live)
    done_n = 0

    if live:
        deck = "".join(render_card(b, j) for b, j in live)
    elif total:
        deck = ("<div class='job'><div class='done-all'><div class='big'>"
                "&#10003;</div><strong>That's the batch.</strong><br>"
                "<span style='color:#6f6c65;font-size:13.5px'>Nothing was sent "
                "by this agent &mdash; you sent them. Your tracker has not been "
                "changed.</span></div></div>")
    else:
        deck = ('<div class="empty">Nothing staged yet.<br><br>'
                'Open the tracker, tap <strong>&#9993; Send queue</strong>, '
                'tick some people and stage them.</div>')

    progress = ""
    if total:
        progress = ("<div class='progress'><span id='plabel'>"
                    "0 of %d done &middot; %d to go</span>"
                    "<span class='bar'><i id='bar' style='width:0%%'></i></span>"
                    "</div>" % (total, total))

    rest = ""
    if handled:
        rest = ("<details class='rest'><summary>%d already handled</summary>%s"
                "</details>"
                % (len(handled), "".join(render_card(b, j) for b, j in handled)))

    warn_html = '<div class="warn">%s</div>' % e(warning) if warning else ""
    demo_html = ("<span class='demo'>DEMO DATA</span>" if demo else "")

    # The banner has to say which mode is actually running. Hardcoding
    # "MANUAL MODE" while auto was on made the page state something untrue
    # about what had just happened to the screen.
    if auto_enabled():
        mode_html = ("AUTO MODE &mdash; &#9654; Set it up opens the real window "
                     "already filled and loads your clipboard, then stops. It "
                     "cannot send, and it is not modifying your tracker. You "
                     "press Send.")
    else:
        mode_html = ("MANUAL MODE &mdash; these are staged for you to send. This "
                     "agent cannot send anything and is not modifying your "
                     "tracker. Ticking &#10003; Sent is your checklist.")

    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta name='referrer' content='no-referrer'>"
        "<title>Staged outreach</title><style>%s</style></head>"
        "<body data-total='%d'>"
        "<header><h1>Staged outreach</h1>"
        "<span class='count'>%d waiting on you%s</span>"
        "<span class='spacer'></span>%s</header>"
        "<div class='test'>%s</div>%s"
        "<main>%s<div class='deck' id='deck'>%s</div>%s</main>"
        "<script>%s</script></body></html>"
        % (REVIEW_CSS, total, len(live),
           (" &middot; %d handled earlier" % len(handled)) if handled else "",
           demo_html, mode_html, warn_html, progress, deck, rest, REVIEW_JS)
    )


def render_card(batch: dict, job: dict) -> str:
    e = html.escape
    state = job.get("state", STATE_STAGED)
    bid, jid = batch["batchId"], job["jobId"]
    is_email = job.get("channel") == "Email" or job.get("kind") in EMAIL_KINDS

    cls = "job"
    if state in (STATE_SENT, STATE_SKIPPED):
        cls += " done"
    if state == STATE_VOIDED:
        cls += " void"

    chan_cls = "em" if is_email else "li"
    head = (
        "<div class='jh'><span class='who'>%s</span>"
        "<span class='co'>%s</span>"
        "<span class='pill %s'>%s</span>"
        "<span class='pill'>%s</span>"
        % (e(job.get("name") or "(no name)"), e(job.get("company") or ""),
           chan_cls, e(job.get("channel") or "?"), e(job.get("kind") or "?"))
    )
    if state != STATE_STAGED:
        head += "<span class='pill state'>%s</span>" % e(state)
    head += "</div>"

    void_html = ""
    if state == STATE_VOIDED:
        void_html = ("<div class='voidmsg'>Do not send &mdash; %s. "
                     "This was staged before that changed.</div>"
                     % e(job.get("voidReason") or "the tracker has moved on"))

    shot = message_block(job)
    notes = job.get("notes") or []
    if notes:
        shot += "<div class='noshot'>&#9888; %s</div>" % e("; ".join(notes))

    if job.get("setupSteps"):
        shot += ("<div class='noshot'>Set up: %s</div>"
                 % e("; ".join(job["setupSteps"])))

    # Hidden nodes are the single source for the copy buttons, and hold the
    # same strings the block above renders - so what you read and what you
    # paste cannot drift apart.
    hidden = (
        "<div id='body-%s' style='display:none'>%s</div>"
        "<div id='subj-%s' style='display:none'>%s</div>"
        % (e(jid), e(job.get("body") or ""), e(jid), e(job.get("subject") or ""))
    )

    live = state == STATE_STAGED
    dis = "" if live else " disabled"
    acts = ["<div class='acts'>"]

    if auto_enabled() and live:
        acts.append("<button class='primary' onclick=\"setup('%s','%s',this)\">"
                    "&#9654; Set it up</button>" % (e(bid), e(jid)))

    if is_email:
        acts.append("<button onclick=\"copy('body-%s',this)\"%s>&#128203; Copy body</button>"
                    % (e(jid), dis))
        if job.get("subject"):
            acts.append("<button onclick=\"copy('subj-%s',this)\"%s>&#128203; Copy subject</button>"
                        % (e(jid), dis))
        url = job.get("composeUrl") or ""
        if url and live:
            acts.append("<a class='btn' href='%s' target='_blank' "
                        "rel='noopener noreferrer'>&#9993; Open compose</a>" % e(url))
        else:
            acts.append("<button disabled>&#9993; Open compose</button>")
    else:
        acts.append("<button onclick=\"copy('body-%s',this)\"%s>&#128203; Copy note</button>"
                    % (e(jid), dis))
        url = job.get("profileHref") or ""
        if url and live:
            acts.append("<a class='btn' href='%s' target='_blank' "
                        "rel='noopener noreferrer'>&#128279; Open profile</a>" % e(url))
        else:
            acts.append("<button disabled>&#128279; Open profile</button>")

    # Everything above is per-channel and so varies in width. The commit
    # buttons go in their own right-anchored group, so "Sent" is in the same
    # spot whether the card had two buttons before it or three - you press it
    # twenty times in a row without re-aiming.
    acts.append("<span class='right'>")
    if live:
        acts.append("<button class='primary' onclick=\"act('%s','%s','sent',this)\">"
                    "&#10003; Sent &mdash; next</button>" % (e(bid), e(jid)))
        acts.append("<button onclick=\"act('%s','%s','skipped',this)\">Skip</button>"
                    % (e(bid), e(jid)))
    else:
        acts.append("<span class='ok'>%s</span>" % e(
            {"sent": "✓ you marked this sent",
             "skipped": "skipped",
             "voided": "not sendable"}.get(state, state)))
        acts.append("<button onclick=\"act('%s','%s','staged',this)\">Undo</button>"
                    % (e(bid), e(jid)))
    acts.append("</span></div>")

    url_line = ""
    shown = job.get("composeUrl") if is_email else job.get("profileHref")
    if shown:
        url_line = "<div class='url'>%s</div>" % e(shown)

    # Order matters: the action row is last, so it is always flush with the
    # bottom edge and lands in the same place on every card.
    return ("<section class='%s'>%s%s%s%s%s%s</section>"
            % (cls, head, void_html, shot, hidden, url_line, "".join(acts)))


# ----------------------------------------------------------------------------
# http
# ----------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "internship-stage-agent/%s" % VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quieter than the default
        pass

    # -- helpers ------------------------------------------------------------

    def _cors(self, origin: str) -> None:
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            # Chrome's Local Network Access preflight
            self.send_header("Access-Control-Allow-Private-Network", "true")

    def _send(self, code: int, body: bytes, ctype: str, origin: str = "") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        if origin:
            self._cors(origin)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, code: int, payload: dict, origin: str = "") -> None:
        self._send(code, json.dumps(payload).encode("utf-8"),
                   "application/json; charset=utf-8", origin)

    def _html(self, code: int, text: str) -> None:
        self._send(code, text.encode("utf-8"), "text/html; charset=utf-8")

    def _read_json(self) -> dict:
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}
        if n <= 0 or n > 8 * 1024 * 1024:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, OSError):
            return {}

    # -- routes -------------------------------------------------------------

    def do_OPTIONS(self):
        origin = self.headers.get("Origin") or ""
        if origin not in ALLOWED_ORIGINS:
            self._send(403, b"", "text/plain")
            return
        self.send_response(204)
        self._cors(origin)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/ping":
            origin = self.headers.get("Origin") or ""
            self._json(200, {"ok": True, "agent": "internship-stage-agent",
                             "version": VERSION, "testMode": TEST_MODE}, origin)
            return

        if path == "/status":
            # What the website needs to do its own bookkeeping: which jobs you
            # ticked as sent and haven't been written into the tracker yet.
            # The agent reports; the site decides and writes.
            origin = self.headers.get("Origin") or ""
            if origin and origin not in ALLOWED_ORIGINS:
                self._json(403, {"ok": False, "error": "origin not allowed"})
                return
            out = []
            with STORE_LOCK:
                for b in load_batches():
                    for j in b.get("jobs", []):
                        if j.get("state") == STATE_SENT and not j.get("recorded"):
                            out.append({
                                "batchId": b["batchId"], "jobId": j["jobId"],
                                "contactId": j.get("contactId", ""),
                                "kind": j.get("kind", ""),
                                "channel": j.get("channel", ""),
                                "company": j.get("company", ""),
                                "name": j.get("name", ""),
                                "demo": bool(b.get("demo")),
                                "markedAt": j.get("markedAt", ""),
                            })
            self._json(200, {"ok": True, "sent": out}, origin)
            return

        if path in ("/", "/index.html"):
            if not self._token_ok(qs):
                return
            with STORE_LOCK:
                batches = load_batches()
                warning = revalidate(batches)
            self._html(200, render_review(batches, warning))
            return

        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/queue":
            self._queue()
        elif parsed.path == "/action":
            self._action()
        elif parsed.path == "/setup":
            self._setup()
        elif parsed.path == "/recorded":
            self._recorded()
        else:
            self._send(404, b"not found", "text/plain")

    # -- route bodies -------------------------------------------------------

    def _token_ok(self, qs: dict) -> bool:
        """
        The review page is gated on a per-run token. It arrives in the URL
        once, then lives in a host-scoped cookie so it stops travelling in
        addresses you might click away from.
        """
        supplied = (qs.get("t") or [""])[0]
        cookie = ""
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == "agent_token":
                cookie = v
        if supplied == TOKEN or cookie == TOKEN:
            if supplied == TOKEN and cookie != TOKEN:
                self.send_response(303)
                self.send_header("Location", "/")
                self.send_header(
                    "Set-Cookie",
                    "agent_token=%s; Path=/; SameSite=Lax; Max-Age=86400" % TOKEN)
                self.send_header("Content-Length", "0")
                self.send_header("Referrer-Policy", "no-referrer")
                self.end_headers()
                return False
            return True
        self._html(403, "<h1>403</h1><p>Open this page from the link the agent "
                        "printed, or restart the agent.</p>")
        return False

    def _recorded(self) -> None:
        """
        The website confirming it has written these into the tracker. Marking
        them here is what stops the same send being counted twice - the site
        also guards on its own side, so it takes both failing to double-count.
        """
        origin = self.headers.get("Origin") or ""
        if origin and origin not in ALLOWED_ORIGINS:
            self._json(403, {"ok": False, "error": "origin not allowed"}, )
            return
        payload = self._read_json()
        ids = payload.get("jobIds")
        if not isinstance(ids, list):
            self._json(400, {"ok": False, "error": "jobIds must be a list"}, origin)
            return
        wanted = {str(i) for i in ids}
        n = 0
        with STORE_LOCK:
            for b in load_batches():
                changed = False
                for j in b.get("jobs", []):
                    if j.get("jobId") in wanted and not j.get("recorded"):
                        j["recorded"] = True
                        j["recordedAt"] = stamp()
                        changed = True
                        n += 1
                if changed:
                    save_batch(b)
        if n:
            log("website recorded %d send(s) into the tracker" % n)
        self._json(200, {"ok": True, "recorded": n}, origin)

    def _setup(self) -> None:
        """
        Auto mode's one action: open the real target and load the clipboard.
        It stops there - the send is still your click.
        """
        if not auto_enabled():
            self._json(409, {"ok": False,
                             "error": "auto mode is off - set \"mode\": \"auto\" "
                                      "in config.json and restart"})
            return
        payload = self._read_json()
        bid = safe_batch_id(payload.get("batchId"))
        jid = safe_batch_id(payload.get("jobId"))
        with STORE_LOCK:
            try:
                batch = json.loads(batch_path(bid).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._json(404, {"ok": False, "error": "no such batch"})
                return
            job = next((j for j in batch.get("jobs", []) if j.get("jobId") == jid),
                       None)
            if job is None:
                self._json(404, {"ok": False, "error": "no such job"})
                return
            if job.get("state") == STATE_VOIDED:
                self._json(409, {"ok": False,
                                 "error": "voided: %s" % job.get("voidReason", "")})
                return

        is_email = (job.get("channel") == "Email"
                    or job.get("kind") in EMAIL_KINDS)
        url = job.get("composeUrl") if is_email else job.get("profileHref")
        if not url:
            self._json(400, {"ok": False, "error": "nothing to open for this one"})
            return

        steps = []
        # Gmail's compose link arrives with to/subject/body already filled, so
        # for email this genuinely is "everything set up, waiting on Send".
        try:
            webbrowser.open(url)
            steps.append("opened the " + ("compose window" if is_email
                                          else "profile"))
        except OSError as exc:
            self._json(500, {"ok": False, "error": "could not open it: %s" % exc})
            return

        ok, msg = set_clipboard(job.get("body") or "")
        steps.append("note on your clipboard" if ok else "clipboard failed: " + msg)

        with STORE_LOCK:
            batch = json.loads(batch_path(bid).read_text(encoding="utf-8"))
            job = next(j for j in batch["jobs"] if j["jobId"] == jid)
            job["setUpAt"] = stamp()
            job["setupSteps"] = steps
            save_batch(batch)

        log("set up %s (%s) - nothing was sent" % (jid, "; ".join(steps)))
        self._json(200, {"ok": True, "steps": steps})

    def _queue(self) -> None:
        origin = self.headers.get("Origin") or ""
        if origin and origin not in ALLOWED_ORIGINS:
            self._json(403, {"ok": False, "error": "origin not allowed"})
            return
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ctype != "application/json":
            self._json(415, {"ok": False, "error": "send application/json"}, origin)
            return

        payload = self._read_json()
        raw_jobs = payload.get("jobs")
        if not isinstance(raw_jobs, list) or not raw_jobs:
            self._json(400, {"ok": False, "error": "no jobs in the batch"}, origin)
            return

        batch_id = safe_batch_id(payload.get("batchId")) or datetime.now().strftime(
            "%Y%m%d-%H%M%S")
        now = stamp()
        jobs, rejected = [], []

        for i, raw in enumerate(raw_jobs[:200]):
            if not isinstance(raw, dict):
                rejected.append("job %d was not an object" % i)
                continue
            body = str(raw.get("body") or "")
            if not body.strip():
                rejected.append("%s: empty message" % (raw.get("name") or "job %d" % i))
                continue
            kind = str(raw.get("kind") or "")
            if kind not in VALID_KINDS:
                rejected.append("%s: unknown template %r"
                                % (raw.get("name") or "job %d" % i, kind))
                continue

            channel = str(raw.get("channel") or "")
            is_email = channel == "Email" or kind in EMAIL_KINDS
            to = str(raw.get("to") or "").strip()
            profile = safe_external_url(str(raw.get("profileUrl") or ""))

            if is_email and "@" not in to:
                rejected.append("%s: no email address"
                                % (raw.get("name") or "job %d" % i))
                continue
            if not is_email and not profile:
                rejected.append("%s: no usable profile link"
                                % (raw.get("name") or "job %d" % i))
                continue

            job = {
                "jobId": "%s-%02d" % (batch_id, i),
                "contactId": str(raw.get("contactId") or ""),
                "name": str(raw.get("name") or ""),
                "company": str(raw.get("company") or ""),
                "channel": channel,
                "kind": kind,
                "to": to,
                "profileUrl": str(raw.get("profileUrl") or ""),
                "profileHref": profile,
                "subject": str(raw.get("subject") or ""),
                "body": body,
                "source": str(raw.get("source") or "template"),
                "state": STATE_STAGED,
                "stagedAt": now,
                "notes": [],
            }
            if is_email:
                job["composeUrl"] = gmail_compose_url(to, job["subject"], body)
            if PLACEHOLDER_RE.search(body) or PLACEHOLDER_RE.search(job["subject"]):
                job["notes"].append("contains an unfilled [placeholder]")
            jobs.append(job)

        if not jobs:
            self._json(400, {"ok": False, "error": "nothing usable in that batch",
                             "rejected": rejected}, origin)
            return

        batch = {"batchId": batch_id, "stagedAt": now, "testMode": TEST_MODE,
                 "jobs": jobs}
        with STORE_LOCK:
            save_batch(batch)

        log("staged %d job(s) as batch %s%s"
            % (len(jobs), batch_id,
               (" (%d rejected)" % len(rejected)) if rejected else ""))
        self._json(200, {"ok": True, "batchId": batch_id, "accepted": len(jobs),
                         "rejected": rejected, "testMode": TEST_MODE,
                         "reviewUrl": review_url()}, origin)

    def _action(self) -> None:
        payload = self._read_json()
        bid = safe_batch_id(payload.get("batchId"))
        jid = safe_batch_id(payload.get("jobId"))
        state = str(payload.get("state") or "")
        if state not in (STATE_STAGED, STATE_SENT, STATE_SKIPPED):
            self._json(400, {"ok": False, "error": "unknown state"})
            return
        with STORE_LOCK:
            try:
                batch = json.loads(batch_path(bid).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._json(404, {"ok": False, "error": "no such batch"})
                return
            hit = None
            for job in batch.get("jobs", []):
                if job.get("jobId") == jid:
                    hit = job
                    break
            if hit is None:
                self._json(404, {"ok": False, "error": "no such job"})
                return
            if hit.get("state") == STATE_VOIDED and state == STATE_SENT:
                self._json(409, {"ok": False, "error": "this one was voided"})
                return
            hit["state"] = state
            hit["markedAt"] = stamp()
            save_batch(batch)
        log("%s -> %s (your checklist only; nothing was transmitted)" % (jid, state))
        self._json(200, {"ok": True})


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


TOKEN = base64.urlsafe_b64encode(os.urandom(18)).decode("ascii").rstrip("=")
PORT = DEFAULT_PORT


def review_url() -> str:
    return "http://%s:%d/?t=%s" % (HOST, PORT, TOKEN)


# ----------------------------------------------------------------------------
# demo batch - invented people, so you can click the whole flow before
# pointing it at anyone real
# ----------------------------------------------------------------------------

DEMO_PEOPLE = [
    ("Priya Raghunathan", "Aerodyne Medical", "Email", "outreach",
     "p.raghunathan@example.com", "",
     "Subject: BU mechanical engineering student - Summer 2027 internship at "
     "Aerodyne Medical\n\nHi Priya,\n\nI'm a mechanical engineering student at "
     "Boston University working on biosensors,\nwearables and human-machine "
     "interaction. I've been following what Aerodyne\nMedical is doing and it "
     "lines up closely with the work I want to be doing.\n\nI'm looking for a "
     "Summer 2027 internship and wanted to ask whether your team\ntakes interns "
     "- or if there's someone better placed for me to talk to.\n\nHappy to send "
     "my resume. Thanks for your time.\n\nBest,\nAlex", "template"),
    ("Marcus Ilunga", "Northwind Robotics", "LinkedIn", "connect",
     "", "linkedin.com/in/marcus-ilunga-demo",
     "Hi Marcus,\n\nI'm a mechanical engineering student at Boston University "
     "and I've been\nfollowing what Northwind Robotics is doing. I'd love to "
     "connect with you to\nlearn more about your work and the company "
     "culture.\n\nWould you be down for a quick zoom meeting to connect?\n\nI'm "
     "available daily after 6:30pm and Sundays after 2pm.", "template"),
    ("Dr. Elena Vasquez", "Kestrel Instruments", "Email", "followup",
     "e.vasquez@example.com", "",
     "Subject: Following up - Summer 2027 internship at Kestrel Instruments\n\n"
     "Hi Elena,\n\nI reached out on Jul 28 about internship opportunities at "
     "Kestrel Instruments\nand wanted to follow up in case my note landed at a "
     "busy moment.\n\nI'm still very interested - I'm a mechanical engineering "
     "student at Boston\nUniversity focused on biosensors and human-machine "
     "interaction.\n\nThanks,\nAlex", "template"),
    ("Tomás Beckett", "Halden Dynamics", "LinkedIn", "applied",
     "", "linkedin.com/in/tomas-beckett-demo",
     "Hi Tomás,\n\nI recently applied to the Halden Dynamics Test Engineering "
     "Intern for 2027.\nI'd love to connect with you to learn more about your "
     "work and the company\nculture.\n\nWould you be down for a quick zoom "
     "meeting to connect?\n\nI'm available daily after 6:30pm and Sundays "
     "after 2pm.", "workspace"),
    ("Sam Okonkwo", "Brightline Surgical", "Email", "outreach",
     "s.okonkwo@example.com", "",
     "Subject: BU mechanical engineering student - Summer 2027 internship at "
     "[company]\n\nHi Sam,\n\nI've been following what [company] is doing and "
     "it lines up closely with the\nwork I want to be doing.\n\nBest,\nAlex",
     "template"),
]


_SIGNOFF_RE = re.compile(
    r"^(best|thanks|thank you|regards|best regards|cheers|sincerely)[,!.]?$", re.I)


def unwrap_paragraphs(text: str) -> str:
    """
    Mirror of the site's unwrapParagraphs(). Only used for the demo bodies,
    which are hard-wrapped in this file so the source stays readable - real
    batches arrive already unwrapped, because the site does it before staging
    so that what you approve is what you paste.
    """
    out = []
    for para in re.split(r"\n{2,}", text or ""):
        lines = [ln for ln in para.split("\n")]
        if not lines:
            continue
        acc = lines[0].rstrip()
        for i in range(1, len(lines)):
            ln = lines[i].strip()
            if not ln:
                continue
            if _SIGNOFF_RE.match(lines[i - 1].strip()):
                acc += "\n" + ln
            else:
                acc += (" " if acc and not acc.endswith(" ") else "") + ln
        out.append(acc)
    return "\n\n".join(out).rstrip()


def seed_demo() -> str:
    """Stage a batch of invented people. Nothing here touches your tracker."""
    batch_id = "demo-" + datetime.now().strftime("%H%M%S")
    now = stamp()
    jobs = []
    for i, (name, company, channel, kind, to, profile, body, source) in enumerate(
            DEMO_PEOPLE):
        split = body.split("\n", 1)
        if split[0].lower().startswith("subject:"):
            subject = split[0].split(":", 1)[1].strip()
            body_only = split[1].lstrip("\n")
        else:
            subject, body_only = "", body
        body_only = unwrap_paragraphs(body_only)
        job = {
            "jobId": "%s-%02d" % (batch_id, i),
            # A contact id that matches nothing real, so the staleness check
            # can never resolve a demo card against an actual person.
            "contactId": "demo-not-a-real-contact-%d" % i,
            "name": name, "company": company, "channel": channel, "kind": kind,
            "to": to, "profileUrl": profile,
            "profileHref": safe_external_url(profile),
            "subject": subject, "body": body_only, "source": source,
            "state": STATE_STAGED, "stagedAt": now, "notes": [],
        }
        if to:
            job["composeUrl"] = gmail_compose_url(to, subject, body_only)
        if PLACEHOLDER_RE.search(body_only) or PLACEHOLDER_RE.search(subject):
            job["notes"].append("contains an unfilled [placeholder]")
        jobs.append(job)

    batch = {"batchId": batch_id, "stagedAt": now, "testMode": TEST_MODE,
             "demo": True, "jobs": jobs}
    save_batch(batch)
    return batch_id


def main() -> int:
    global PORT
    try:
        PORT = int(CONFIG.get("port") or DEFAULT_PORT)
    except (TypeError, ValueError):
        PORT = DEFAULT_PORT

    BATCH_DIR.mkdir(parents=True, exist_ok=True)

    try:
        server = Server((HOST, PORT), Handler)
    except OSError as exc:
        log("could not bind %s:%d - %s" % (HOST, PORT, exc))
        log("something else is probably using that port. Change \"port\" in %s"
            % CONFIG_PATH)
        return 1

    mode = str(CONFIG.get("mode") or "manual").lower()
    if mode not in ("manual", "auto"):
        log("config asks for mode=%r, which does not exist - running manual." % mode)

    log("=" * 66)
    log("internship staging agent %s" % VERSION)
    if auto_enabled():
        log("AUTO MODE: it opens the real compose window already filled and")
        log("loads your clipboard - then stops. You press Send.")
    else:
        log("MANUAL MODE: it stages messages; you copy and send them.")
    log("It cannot send anything and cannot write to your tracker.")
    log("listening on http://%s:%d  (loopback only)" % (HOST, PORT))
    log("review page: %s" % review_url())
    log("runtime data: %s" % ROOT)
    ident = CONFIG.get("fromAddress") or ""
    log("sending identity: %s" % (ident or "not configured yet (config.json)"))
    log("=" * 66)

    if "--demo" in sys.argv:
        bid = seed_demo()
        log("seeded demo batch %s with %d invented people" % (bid, len(DEMO_PEOPLE)))
        log("nothing in it corresponds to a real contact")
        try:
            webbrowser.open(review_url())
        except OSError:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
