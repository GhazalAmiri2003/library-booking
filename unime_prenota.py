import os, time, datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from datetime import timezone, timedelta

load_dotenv()

BOOK_URL   = os.getenv("BOOK_URL")
NAME       = os.getenv("NAME")
EMAIL      = os.getenv("EMAIL")
MATRICOLA  = os.getenv("MATRICOLA")
BOOK_DATE  = os.getenv("BOOK_DATE")       # yyyy-mm-dd
BOOK_SLOT  = os.getenv("BOOK_SLOT")       # فقط برای لاگ/بررسی
TARGET_TIME= os.getenv("TARGET_TIME")     # مثل "08:00:05"
TARGET_TZ  = "Europe/Rome"

# ایتالیا زمستون: UTC+1 (تابستون -> hours=2)
ITALY_TZ = timezone(timedelta(hours=1))

def seconds_until_next_time(time_str, tz_name):
    now = datetime.datetime.now(ITALY_TZ)
    h, m, s = map(int, time_str.split(":"))
    target = datetime.datetime(now.year, now.month, now.day, h, m, s, tzinfo=ITALY_TZ)
    if target < now:
        target += datetime.timedelta(days=1)
    return max(0.0, (target - now).total_seconds())

def click_day_in_calendar(page, date_str):
    day = str(int(date_str.split("-")[2]))
    try:
        page.get_by_role("button", name=day).click(timeout=4000)
        return
    except Exception:
        pass
    page.locator(".ui-datepicker-calendar").locator(f"text='{day}'").first.click(timeout=4000)

def click_slot_by_xpath(page):
    """کلیک روی تایم‌اسلات با XPath تعیین‌شده (در صورت نیاز مسیرتو عوض کن)"""
    xpath = '//*[@id="field_1-1"]/div[1]/div[3]/div/div[2]'

    for _ in range(15):
        try:
            page.locator(f"xpath={xpath}").click(timeout=600)
            print("🕓 Slot clicked successfully.")
            return True
        except Exception:
            time.sleep(0.15)
    raise RuntimeError("❌ Couldn't click time slot via XPath.")

def fill_fields_robust(page, name, email, matricola):
    """پرکردن امن با انتظارِ قابل‌مشاهده و فالبک‌های مختلف"""
    # صبر تا فرم دیده شود (نام یا ایمیل)
    page.locator("#fieldname5_1, #email_1, input[type='email']").first.wait_for(state="visible", timeout=10000)

    # Nominativo
    try:
        page.get_by_label("Nominativo").fill(name, timeout=6000)
    except Exception:
        page.locator("#fieldname5_1").fill(name, timeout=6000)

    # Email
    try:
        page.get_by_label("E-mail").fill(email, timeout=6000)
    except Exception:
        page.locator("#email_1, input[type='email']").first.fill(email, timeout=6000)

    # Matricola (چند فالبک)
    for sel in [
        "#fieldname4_1",
        "input[name='fieldname4_1']",
        "input[id*='fieldname4_']",               # id مشابه
    ]:
        try:
            page.locator(sel).first.fill(matricola, timeout=5000)
            break
        except Exception:
            continue
    else:
        # فالبک با لیبل
        try:
            page.get_by_label("Matricola/n° Documento (se utente esterno)").fill(matricola, timeout=6000)
        except Exception:
            # آخرین فالبک: اولین input متنی بعد از ایمیل
            email_el = page.locator("#email_1, input[type='email']").first
            email_el.scroll_into_view_if_needed()
            # یک input متن بعدی
            page.locator("xpath=(//input[@type='text'])[last()]").fill(matricola, timeout=6000)

    # تیک‌ها
    page.locator("#fieldname3_1").check()
    page.locator("#fieldname6_1").check()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(locale="it-IT")
    page = ctx.new_page()

    # سبک‌سازی لود
    page.route("**/*", lambda r: r.abort()
               if r.request.resource_type in ["image", "font", "media"]
               else r.continue_())

    # صبر تا زمان هدف
    secs = seconds_until_next_time(TARGET_TIME, TARGET_TZ)
    print(f"⏳ Waiting {secs/60:.1f} minutes until {TARGET_TIME} Italy time...")
    time.sleep(max(0, secs - 2))
    while seconds_until_next_time(TARGET_TIME, TARGET_TZ) > 0:
        pass

    try:
        print("→ Opening page…")
        page.goto(BOOK_URL, wait_until="domcontentloaded")

        print("→ Picking date…")
        click_day_in_calendar(page, BOOK_DATE)

        print("→ Clicking slot (XPath)…")
        click_slot_by_xpath(page)

        print("→ Filling form…")
        fill_fields_robust(page, NAME, EMAIL, MATRICOLA)

        print("→ Submitting…")
        try:
            page.locator("div.pbSubmit").click()
        except Exception:
            page.get_by_role("button", name="Prenota posto").click()

        page.wait_for_load_state("networkidle")
        page.screenshot(path=f"unime_{BOOK_DATE}.png")
        print("✅ Reservation attempted — check email for confirmation.")
    except Exception as e:
        print(f"⚠️ Error during booking: {e}")

    ctx.close()
    browser.close()
