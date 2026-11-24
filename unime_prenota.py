"""Playwright library form assistant with explicit user review."""
import argparse
import datetime as dt
import os
import time
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
TARGET_TZ = "Europe/Rome"


def next_target(time_str, tz_name=TARGET_TZ, now=None):
    """Return one absolute target; handle DST gaps and repeated local times."""
    zone = ZoneInfo(tz_name)
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    local = now.astimezone(zone)
    clock = dt.time.fromisoformat(time_str)
    if clock.tzinfo is not None:
        raise ValueError("TARGET_TIME must be a local clock time")
    for offset in range(3):
        date = local.date() + dt.timedelta(days=offset)
        naive = dt.datetime.combine(date, clock)
        candidates = set()
        for fold in (0, 1):
            candidate = naive.replace(tzinfo=zone, fold=fold)
            utc = candidate.astimezone(dt.timezone.utc)
            if utc.astimezone(zone).replace(tzinfo=None) == naive:
                candidates.add(utc)
        future = [target for target in candidates if target >= now]
        if future:
            return min(future)
    raise ValueError("No valid target time found")


def wait_until(target):
    while True:
        remaining = (target - dt.datetime.now(dt.timezone.utc)).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 30.0))


def require_config():
    load_dotenv(ROOT / ".env")
    keys = ("BOOK_URL", "NAME", "EMAIL", "MATRICOLA", "BOOK_DATE", "BOOK_SLOT")
    values = {key: (os.getenv(key) or "").strip() for key in keys}
    missing = [key for key in keys if not values[key]]
    if missing:
        raise ValueError("Missing configuration: " + ", ".join(missing))
    url = urlparse(values["BOOK_URL"])
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError("BOOK_URL must be a valid HTTPS address")
    date = dt.date.fromisoformat(values["BOOK_DATE"])
    if date < dt.datetime.now(ZoneInfo(TARGET_TZ)).date():
        raise ValueError("BOOK_DATE cannot be in the past")
    return values


def fill_fields(page, name, email, matricola):
    """Use unambiguous labels or known field IDs; never guess an input."""
    for label, selector, value in (
        ("Nominativo", "#fieldname5_1", name),
        ("E-mail", "#email_1", email),
        ("Matricola/n° Documento (se utente esterno)", "#fieldname4_1", matricola),
    ):
        field = page.get_by_label(label, exact=True)
        if field.count() != 1:
            field = page.locator(selector)
        if field.count() != 1:
            raise RuntimeError("Cannot uniquely identify field: " + label)
        field.fill(value, timeout=6000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Use a local mock form and synthetic data")
    args = parser.parse_args()
    try:
        if args.demo:
            values = {"NAME": "Demo Student", "EMAIL": "student@example.com", "MATRICOLA": "000000"}
        else:
            values = require_config()
            clock = (os.getenv("TARGET_TIME") or "").strip()
            if clock:
                target = next_target(clock)
                print("Waiting for the selected local time. No repeated booking attempts.")
                wait_until(target)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            try:
                context = browser.new_context(locale="it-IT")
                page = context.new_page()
                if args.demo:
                    page.goto((ROOT / "demo_form.html").as_uri())
                else:
                    page.goto(values["BOOK_URL"], wait_until="domcontentloaded")
                    print("Select and verify the date and slot in the browser:")
                    print("Requested date:", values["BOOK_DATE"], "| slot:", values["BOOK_SLOT"])
                    input("After you select the correct available date and slot, press Enter (Ctrl+C to cancel): ")
                fill_fields(page, values["NAME"], values["EMAIL"], values["MATRICOLA"])
                print("Review the form in the browser. Read and accept any applicable terms yourself.")
                print("Submit manually only if appropriate. Check the service's confirmation.")
                input("Press Enter here when finished to close the browser: ")
            finally:
                browser.close()
    except (ValueError, RuntimeError) as exc:
        print("Configuration or form error:", exc)
        return 1
    except KeyboardInterrupt:
        print("Cancelled.")
        return 130
    except Exception:
        # Avoid logging exception details that might include form values or URLs.
        print("Browser operation failed. Check the page and configuration.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
