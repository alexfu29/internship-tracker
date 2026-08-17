#!/usr/bin/env python3
"""
profile_probe.py - a one-off experiment, not the finished fetcher.

THE QUESTION
------------
The tracker's reader only ever sees the signed-out view of LinkedIn, where the
Education section is usually missing. That is why rows land on `check this`
instead of `verified`. The premise of the whole education feature is that
reading the page *as you* fixes it.

This script tests that premise on three real profiles before a single line of
index.html changes. Each profile is read twice - once in a window carrying your
LinkedIn session, once in a clean window with no session - and the two texts are
run through the same three-outcome BU logic the app uses. If the signed-in read
doesn't produce an Education section, there is nothing here worth building.

WHAT IT DOES, EXACTLY
---------------------
  * six page loads total (three profiles, two passes), nothing else
  * a randomised 20-45 second gap between every load
  * stops the moment LinkedIn serves a wall rather than pushing through
  * reads document.body.innerText - no clicking, no scrolling, no retries

HEADLESS vs VISIBLE
-------------------
Headless Chrome puts "HeadlessChrome" in its own user agent, so LinkedIn can see
it plainly and is likely to answer with a wall. The signed-in pass therefore uses
a normal visible window by default - a real Chrome, reporting itself honestly.
Nothing here masks a user agent or otherwise dresses the browser up as something
it isn't; the point is to stay well under the threshold, not to get past it.

A window will open and load three pages. It does not take over your machine -
your mouse and keyboard are untouched, and you can minimise it. Pass --headless
to try the invisible route instead, at the cost of a likely wall.

It sends nothing anywhere. Only your browser and linkedin.com are involved.

WHERE THE CAPTURES GO
---------------------
%LOCALAPPDATA%\\internship-agent\\probe\\ - deliberately OUTSIDE this repo,
because data/log.json is public and these captures are other people's profiles.

USAGE
-----
  pip install playwright
  python agent/profile_probe.py

It drives the Chrome already installed on this machine, so there is no browser
to download.

First run opens a visible window so you can sign into LinkedIn by hand, once.
The session persists in its own profile directory afterwards.
"""

import os
import random
import re
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright is not installed.\n  pip install playwright")


# --------------------------------------------------------------------------
# The three test subjects - one per bucket, pulled from data/log.json.
# Two share a company on purpose: it separates what changes between buckets
# from what changes between companies.
# --------------------------------------------------------------------------
SUBJECTS = [
    ("Hiring", "Ashley Bulloch", "Kraft Heinz",
     "https://www.linkedin.com/in/ashleybulloch/"),
    ("VP Eng", "Steve Fox", "Marotta Controls",
     "https://www.linkedin.com/in/steve-fox-71018711/"),
    ("BU Eng", "William Dimas", "Marotta Controls",
     "https://www.linkedin.com/in/william-dimas-92022051/"),
]

MIN_GAP, MAX_GAP = 20, 45          # seconds between page loads
NAV_TIMEOUT = 45000                # ms

# Drive the Chrome you already have, not Playwright's bundled Chromium. Real
# Chrome is what LinkedIn expects to see; bundled Chromium reports itself
# differently and is the easier thing for them to flag. It also means nothing
# has to be downloaded.
CHANNEL = "chrome"


def app_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.local/share")
    return Path(base) / "internship-agent"


PROFILE_DIR = app_dir() / "probe-chrome"     # the browser session, kept apart
OUT_DIR = app_dir() / "probe"                # the captures


# ==========================================================================
# The app's BU logic, ported verbatim from index.html so the probe's verdict
# is the app's verdict. If these drift, the comparison means nothing.
#   sectionText()  index.html:3529
#   quoteLine()    index.html:3548
#   buEvidence()   index.html:3557
# ==========================================================================
RE_BU_ANY = re.compile(r"boston univ(?:ersity)?\b|questrom", re.I)
RE_BU_EDU = re.compile(r"boston univ(?:ersity)?\b|questrom|\bBU\b", re.I)

RE_SECTION = re.compile(
    r"^\s*(experience|education|experience &(amp;)? education|about|skills|"
    r"top skills|activity|licenses|certifications?|projects|honou?rs|languages|"
    r"recommendations|interests|volunteering|publications)\s*$", re.I)

# A wall parses perfectly happily - the heading is just "Join LinkedIn" - so
# without this check a challenge page becomes a confidently wrong contact.
RE_WALL = re.compile(
    r"^(join linkedin|sign ?up|sign ?in|log ?in|security verification|linkedin|"
    r"page not found|something went wrong)\b", re.I)


def section_text(text, heading):
    lines = (text or "").split("\n")
    head = re.compile(r"^\s*(?:#{1,6}\s+)?" + heading + r"\s*$", re.I)
    start = -1
    for i, line in enumerate(lines):
        if head.match(line):
            start = i + 1
            break
    if start == -1:
        return ""
    out = []
    for line in lines[start:]:
        if re.match(r"^\s*#{1,6}\s+\S", line) or RE_SECTION.match(line):
            break
        out.append(line)
    return "\n".join(out)


def quote_line(block, rx):
    hit = next((l for l in block.split("\n") if rx.search(l)), "")
    hit = re.sub(r"^[\s#*\->|]+", "", hit)
    hit = re.sub(r"\s+", " ", hit).strip()
    return hit[:87] + "…" if len(hit) > 90 else hit


def bu_evidence(text):
    """None, or {ok, strong, quote, why} - the app's three outcomes."""
    edu = section_text(text, "Education")
    if edu:
        if RE_BU_EDU.search(edu):
            return {"ok": True, "strong": True, "quote": quote_line(edu, RE_BU_EDU),
                    "why": "Boston University under Education"}
        if RE_BU_ANY.search(text):
            return {"ok": False, "strong": False, "quote": quote_line(text, RE_BU_ANY),
                    "why": "Boston University is on the page but not in their "
                           "Education - usually a sidebar or a repost, not a degree"}
        return None
    if RE_BU_ANY.search(text):
        return {"ok": True, "strong": False, "quote": quote_line(text, RE_BU_ANY),
                "why": "Boston University on the page, but this view has no "
                       "Education section to confirm it against"}
    return None


def verdict_for(text, is_bu_row):
    """What the finder would decide. Mirrors applyVerification(), BU branches."""
    bu = bu_evidence(text)
    if not is_bu_row:
        return "n/a (not a BU row)", bu
    if not (bu and bu["ok"]):
        return "check this", bu
    if not bu["strong"]:
        return "check this", bu
    return "verified", bu


# ==========================================================================
# Reading pages
# ==========================================================================
def looks_walled(url, text):
    if re.search(r"/authwall|/checkpoint|/uas/login|linkedin\.com/login", url or "", re.I):
        return True
    head = (text or "").strip().split("\n")[0] if text else ""
    return bool(RE_WALL.match(head.strip()))


def pace(label):
    gap = random.uniform(MIN_GAP, MAX_GAP)
    print("    ... waiting %.0fs before %s" % (gap, label))
    time.sleep(gap)


def safe_goto(page, url):
    """LinkedIn redirects mid-navigation - to a login, or to a checkpoint. That
    makes goto() raise "interrupted by another navigation", which is not an
    error so much as the answer to a different question. Swallow it and report
    wherever we actually landed."""
    try:
        page.goto(url, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
    except Exception as exc:
        if "interrupted by another navigation" not in str(exc):
            raise
        page.wait_for_timeout(3000)
    page.wait_for_timeout(2500)          # let the body settle
    try:
        return page.url, (page.evaluate("() => document.body.innerText") or "")
    except Exception:
        return page.url, ""


def read_profile(page, url):
    return safe_goto(page, url)


def show_page(url, text, lines=14):
    """Print what a page actually says. A checkpoint that asks for an emailed
    code is ordinary new-device verification; one that talks about unusual
    activity or proving you're not a robot is detection, and the two need
    opposite responses."""
    print("\n  landed on: %s" % url)
    print("  ---- what the page says " + "-" * 40)
    for line in [l for l in (text or "").split("\n") if l.strip()][:lines]:
        print("  | " + line.strip()[:76])
    print("  " + "-" * 64)


def ensure_login(pw):
    """First run: a visible window, you sign in by hand, once."""
    ctx = pw.chromium.launch_persistent_context(
        str(PROFILE_DIR), headless=False, channel=CHANNEL)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try:
        url, text = safe_goto(page, "https://www.linkedin.com/feed/")
        if not looks_walled(url, text):
            print("  already signed in.")
            return True

        show_page(url, text)
        if "/checkpoint/" in url:
            print("\n  LinkedIn sent a CHECKPOINT before any profile was read.")
            print("  Read the window. Which is it?")
            print("    (a) a code emailed/texted to you  -> ordinary new-device")
            print("        verification. Complete it in the window.")
            print("    (b) unusual activity / prove you are not a robot -> this")
            print("        is detection. Close the window and stop; automating")
            print("        past it is what gets accounts restricted.")

        print("\n  Sign in / finish up in the window, then press Enter here.")
        print("  Press Enter without doing anything to stop.")
        input("  > ")

        url, text = safe_goto(page, "https://www.linkedin.com/feed/")
        ok = not looks_walled(url, text)
        if ok:
            print("  signed in.")
        else:
            print("  still not through - stopping rather than retrying.")
            show_page(url, text)
        return ok
    finally:
        ctx.close()


def pass_signed_in(pw, headless):
    """Three profiles, carrying your session."""
    out = {}
    ctx = pw.chromium.launch_persistent_context(
        str(PROFILE_DIR), headless=headless, channel=CHANNEL)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    try:
        for i, (bucket, name, _co, url) in enumerate(SUBJECTS):
            if i:
                pace("%s (signed in)" % name)
            final_url, text = read_profile(page, url)
            walled = looks_walled(final_url, text)
            print("    %-8s %-16s %5d chars%s"
                  % (bucket, name, len(text), "  <-- WALLED" if walled else ""))
            out[name] = {"text": text, "url": final_url, "walled": walled}
            if walled:
                print("    stopping this pass - a wall means stop, not retry.")
                break
    finally:
        ctx.close()
    return out


def pass_signed_out(pw, headless):
    """The same three, in a clean window with no session. No third party.

    Same browser mode as the signed-in pass on purpose: if one ran headless and
    the other didn't, a difference between them could be the missing session or
    could just be the user agent, and the comparison would prove nothing."""
    out = {}
    browser = pw.chromium.launch(headless=headless, channel=CHANNEL)
    ctx = browser.new_context()
    page = ctx.new_page()
    try:
        for bucket, name, _co, url in SUBJECTS:
            pace("%s (signed out)" % name)
            final_url, text = read_profile(page, url)
            walled = looks_walled(final_url, text)
            print("    %-8s %-16s %5d chars%s"
                  % (bucket, name, len(text), "  <-- WALLED" if walled else ""))
            out[name] = {"text": text, "url": final_url, "walled": walled}
    finally:
        browser.close()
    return out


# ==========================================================================
# The comparison
# ==========================================================================
def describe(cap, is_bu_row):
    if cap is None:
        return "not read"
    if cap["walled"]:
        return "WALLED - no profile"
    text = cap["text"]
    edu = section_text(text, "Education")
    exp = section_text(text, "Experience")
    verdict, bu = verdict_for(text, is_bu_row)
    bits = [
        "%d chars" % len(text),
        "Education section: %s" % ("YES (%d chars)" % len(edu) if edu else "NO"),
        "Experience section: %s" % ("YES (%d chars)" % len(exp) if exp else "NO"),
        "BU verdict: %s" % verdict,
    ]
    if bu:
        bits.append("evidence: %s" % bu["why"])
        if bu["quote"]:
            bits.append('quote: "%s"' % bu["quote"])
    return "\n      ".join(bits)


def report(signed_in, signed_out):
    lines = ["", "=" * 72, "COMPARISON", "=" * 72]
    for bucket, name, company, url in SUBJECTS:
        is_bu = (bucket == "BU Eng")
        lines.append("")
        lines.append("%s  -  %s (%s)" % (name, bucket, company))
        lines.append("  signed OUT (what the tracker sees today):")
        lines.append("      " + describe(signed_out.get(name), is_bu))
        lines.append("  signed IN (what this would give it):")
        lines.append("      " + describe(signed_in.get(name), is_bu))
    lines.append("")
    lines.append("=" * 72)
    return "\n".join(lines)


def save(captures, suffix):
    for name, cap in captures.items():
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        (OUT_DIR / ("%s.%s.txt" % (slug, suffix))).write_text(
            cap["text"], encoding="utf-8")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print("captures -> %s" % OUT_DIR)
    print("session  -> %s" % PROFILE_DIR)

    with sync_playwright() as pw:
        print("\n[1/3] checking your LinkedIn session")
        if not ensure_login(pw):
            return 1

        headless = "--headless" in sys.argv
        print("\n[2/3] reading three profiles signed in (%s)"
              % ("headless" if headless else "visible window"))
        signed_in = pass_signed_in(pw, headless=headless)

        print("\n[3/3] reading the same three signed out (clean window)")
        signed_out = pass_signed_out(pw, headless)

        save(signed_in, "signed-in")
        save(signed_out, "signed-out")

    text = report(signed_in, signed_out)
    print(text)
    (OUT_DIR / "comparison.txt").write_text(text, encoding="utf-8")
    print("\nwritten to %s" % (OUT_DIR / "comparison.txt"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
