# Library Booking Form Assistant

A Python browser-automation project using Playwright to demonstrate form preparation, environment-based configuration, time-zone-aware scheduling and user-reviewed interactions.

## Features

- Local offline demonstration with synthetic student data.
- Environment variables keep personal configuration out of source control.
- Europe/Rome scheduling with daylight-saving time handling and a fixed absolute target.
- Browser form filling with explicit labels and known ID fallbacks; ambiguous fields fail closed.
- Manual date and slot selection, review of consent and final submission. No automated reservation submission or repeated booking attempts.
- Unit tests for scheduling, including daylight-saving transitions.

## Setup

Requires Python 3.10+.

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
python unime_prenota.py --demo
```

The demo is local and does not access the university website or send a reservation. Use it to explore the browser form-filling workflow.

## Real form assistance (optional)

Only use this with authorization and where the service permits browser automation. Copy `.env.example` to `.env` locally and supply your own values. Never commit `.env` or screenshots containing personal information.

- `BOOK_URL`: authorized HTTPS booking page.
- `NAME`, `EMAIL`, `MATRICOLA`: personal form fields.
- `BOOK_DATE`, `BOOK_SLOT`: requested date and slot, verified manually.
- `TARGET_TIME`: optional local clock time (HH:MM:SS).

Run `python unime_prenota.py`. Select the date and slot yourself, then allow the script to fill the identified form fields. Review the terms and submit yourself if appropriate. The script does not confirm that a reservation succeeded.

## Tests

```bash
python -m unittest discover -v
```

The current live university form and browser workflow have not been independently verified. This is a portfolio demonstration, not an official university service.

**Stack:** Python · Playwright · python-dotenv · zoneinfo · unittest
