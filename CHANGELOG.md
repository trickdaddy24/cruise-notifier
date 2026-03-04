# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.0.4] - 2026-03-03  *(Latest)*

### Added
- Full interactive menu system with colorama colored output
- Option 1: Check Cruises Now — runs countdown and fires all configured services
- Option 2: Manage Cruises — add/remove cruises at runtime, saved to `cruises.json`
- Option 3: Notification Services — per-service credential setup and test message UI with ✅/❌ status
- Option 4: Schedule — Windows Task Scheduler integration (create/remove daily job from inside the menu)
- `--run` headless flag — skips menu, fires notifications directly (used by Task Scheduler, cron, Docker)
- Dockerfile for containerized headless use
- `cruises.json` data file — cruises no longer hardcoded in the script
- Per-service credential menus for Discord, Telegram, Pushover, and Gmail

### Changed
- Credentials now re-read from `os.getenv()` at send time (picks up changes made during the session)
- `colorama` added to `requirements.txt`

---

## [v0.0.3] - 2026-03-03

### Added
- `requirements.txt` with `requests`, `python-dotenv`, `colorama`
- `_ensure_requirements()` — auto-installs missing packages via pip on first run using only stdlib

### Changed
- Log directory hardcoded to `<script folder>/logs/` — fully portable, no `LOG_DIRECTORY` env var needed
- Removed broken `os.path.join(cwd, absolute_path)` log path logic

---

## [v0.0.2] - 2026-03-03

### Fixed
- Removed duplicate `import requests` (appeared on lines 7 and 76)
- Fixed `SMTP_PORT` type from string `'587'` to `int`
- Fixed broken dual `logging.basicConfig()` — second call was a no-op; replaced with two named loggers using `FileHandler` so `did.not.run.log.cruise.txt` now actually writes
- Fixed log directory path bug — `os.path.join(cwd, absolute_path)` discarded cwd silently on Windows
- Fixed `logging.error()` used on a success message — changed to `logging.info()`
- Fixed Discord webhook hardcoded as empty string inside function — now reads from `.env`
- Removed dead `notification_message` variable (defined but never used)

### Added
- `.env` support via `python-dotenv` — all credentials loaded from `.env` file
- Error handling (`try/except`) on all four senders — network failures no longer crash the script
- Graceful skip with warning message when a service is not configured
- `APP_VERSION = "0.0.2"` constant
- `if __name__ == '__main__':` guard
- `.env.example` template file
- Cruise name as a function parameter — no more hardcoded `"Carnival Celebration"` in message strings
- `CRUISES` list at top of file — easy to add more cruise dates

### Changed
- `SMTP_PORT` cast to `int`

---

## [v0.0.1] - 2026-03-03

### Added
- Initial script — carnival cruise countdown with days remaining, day-of, and past-cruise messages
- Send via Telegram, Pushover, Discord, Gmail
- `MAX_DAYS_FOR_REMINDER` constant to suppress notifications when cruise is far away
- `RUN_REMINDERS` toggle flag
- Basic file logging to `logging.cruise.txt` and `did.not.run.log.cruise.txt`

---

<!-- Generated manually -->
