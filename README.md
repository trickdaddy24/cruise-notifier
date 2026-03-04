# 🚢 Cruise Notifier

**Current version: v0.0.4**

A portable Python CLI tool that sends countdown reminders for upcoming cruises via Discord, Telegram, Pushover, and/or Email. Includes an interactive menu for managing cruises, configuring credentials, and scheduling automatic daily notifications via Windows Task Scheduler (or cron on Linux/Mac).

---

## Features

- 🚢 **Cruise countdown** — shows days remaining, fires on cruise day, and acknowledges past cruises
- 📬 **Multi-channel notifications** — Discord, Telegram, Pushover, Gmail (enable any or all)
- 📋 **Manage multiple cruises** — add/remove cruises at runtime, saved to `cruises.json`
- 🔑 **Interactive credential setup** — set API tokens directly from the menu, saved to `.env`
- 🗓️ **Windows Task Scheduler** — schedule daily automatic runs from inside the menu
- 🐧 **Linux/Mac cron** — schedule via crontab (see instructions below)
- 🐳 **Docker support** — headless/automated mode for containerized environments
- 📦 **Auto-installs dependencies** — checks for `requests`, `python-dotenv`, `colorama` on startup
- 📁 **Fully portable** — all files (logs, config, data) live next to the script
- 📝 **Dual log files** — separate logs for sent notifications and skipped reminders

---

## Project Structure

```
cruise-notifier/
├── cruise.notify.py       # Main application (entry point)
├── requirements.txt       # Python dependencies
├── .env.example           # Credential template — copy to .env and fill in
├── .env                   # Your credentials (git-ignored)
├── cruises.json           # Cruise list (auto-created, git-ignored)
├── Dockerfile             # Docker support
├── README.md
├── CHANGELOG.md
├── LICENSE
└── logs/                  # Auto-created on first run (git-ignored)
    ├── logging.cruise.txt          # Sent notification log
    └── did.not.run.log.cruise.txt  # Skipped reminder log
```

---

## Requirements

- Python 3.9 or newer
- pip (included with Python)

**Python packages** (auto-installed on first run):

| Package | Version | Purpose |
|---|---|---|
| `requests` | latest | HTTP calls to notification APIs |
| `python-dotenv` | latest | Load credentials from `.env` |
| `colorama` | latest | Colored terminal output on Windows |

---

## Installation

### Windows 11

1. **Install Python 3.9+** from [python.org](https://www.python.org/downloads/) — check *"Add Python to PATH"* during install.

2. **Clone the repo:**
   ```cmd
   git clone https://github.com/trickdaddy24/cruise-notifier.git
   cd cruise-notifier
   ```

3. **Copy the env template:**
   ```cmd
   copy .env.example .env
   ```

4. **Run:**
   ```cmd
   python cruise.notify.py
   ```
   Dependencies install automatically on first run. The interactive menu opens.

5. **Set credentials** — choose option `3` (Notification Services) from the menu and enter your tokens.

6. **Schedule daily notifications** — choose option `4` (Schedule) from the menu and pick a time. This creates a Windows Task Scheduler job that runs automatically every day.

---

### Linux / macOS

1. **Install Python 3.9+:**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install python3 python3-pip git -y

   # macOS (Homebrew)
   brew install python
   ```

2. **Clone the repo:**
   ```bash
   git clone https://github.com/trickdaddy24/cruise-notifier.git
   cd cruise-notifier
   ```

3. **Copy the env template:**
   ```bash
   cp .env.example .env
   ```

4. **Run:**
   ```bash
   python3 cruise.notify.py
   ```

5. **Set credentials** — use option `3` in the menu.

6. **Schedule with cron** (Linux/macOS):
   ```bash
   crontab -e
   ```
   Add a line to run daily at 8:00 AM (adjust path and time as needed):
   ```
   0 8 * * * /usr/bin/python3 /path/to/cruise-notifier/cruise.notify.py --run >> /path/to/cruise-notifier/logs/cron.log 2>&1
   ```

---

### Docker

Docker runs in **headless mode** (`--run` flag) — no interactive menu. Configure your `.env` file and `cruises.json` before building.

1. **Copy and fill in `.env`:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Add your cruises to `cruises.json`:**
   ```json
   [
     {"date": "6/30/25", "name": "Carnival Celebration"}
   ]
   ```

3. **Build the image:**
   ```bash
   docker build -t cruise-notifier .
   ```

4. **Run once:**
   ```bash
   docker run --rm \
     -v "$(pwd)/.env:/app/.env" \
     -v "$(pwd)/cruises.json:/app/cruises.json" \
     -v "$(pwd)/logs:/app/logs" \
     cruise-notifier
   ```

5. **Schedule with cron on the Docker host** (run daily at 8:00 AM):
   ```bash
   0 8 * * * docker run --rm \
     -v /path/to/cruise-notifier/.env:/app/.env \
     -v /path/to/cruise-notifier/cruises.json:/app/cruises.json \
     -v /path/to/cruise-notifier/logs:/app/logs \
     cruise-notifier
   ```

---

## Configuration

Copy `.env.example` to `.env` and fill in the services you want to use. You only need to configure the services you plan to use — unconfigured services are silently skipped.

```env
# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_CHAT_ID=987654321

# Pushover
PUSHOVER_API_TOKEN=your_api_token
PUSHOVER_USER_KEY=your_user_key

# Gmail (optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=you@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient@email.com

# Reminder behaviour
MAX_DAYS_FOR_REMINDER=65
RUN_REMINDERS=true
```

> **Gmail note:** Use an [App Password](https://support.google.com/accounts/answer/185833), not your regular Gmail password.

---

## Menu Overview

```
╔═══════════════════════════════════════╗
║  🚢 CRUISE NOTIFIER  v0.0.4          ║
╚═══════════════════════════════════════╝
  1  🚢  Check Cruises Now
  2  📋  Manage Cruises
  3  📬  Notification Services
  4  🗓️   Schedule (Windows Task Scheduler)
  ───────────────────────────────────────
  0  🚪  Exit
```

| Option | Description |
|---|---|
| `1` Check Cruises Now | Runs the countdown and sends notifications to all configured services |
| `2` Manage Cruises | Add or remove cruises. Changes saved to `cruises.json` |
| `3` Notification Services | Configure and test Discord, Telegram, Pushover, Email |
| `4` Schedule | Create or remove a Windows Task Scheduler job for daily automation |
| `0` Exit | Quit |

### Notification Services Sub-menu

Each service shows a ✅/❌ status indicator:

```
╔═══════════════════════════════════════╗
║  📬 NOTIFICATION SERVICES            ║
╚═══════════════════════════════════════╝
  1  💬  Discord   ✅
  2  📱  Telegram  ❌
  3  📲  Pushover  ❌
  4  📧  Email     ❌
```

Each service sub-menu has:
- **Set Credentials** — saves tokens to `.env` immediately
- **Send Test Message** — fires a live test to confirm it works

---

## Headless / Automated Mode

Pass `--run` to skip the menu and fire notifications directly. Used by Task Scheduler, cron, and Docker:

```bash
python cruise.notify.py --run
```

---

## Version History

| Version | Date | Summary |
|---|---|---|
| v0.0.1 | 2026-03-03 | Initial script — basic countdown, hardcoded credentials |
| v0.0.2 | 2026-03-03 | Bug fixes: dual logging, error handling, `.env` support, portable logs |
| v0.0.3 | 2026-03-03 | Auto-install requirements, fully portable log path, `requirements.txt` |
| v0.0.4 | 2026-03-03 | Full interactive menu, credential setup UI, cruise management, Windows Task Scheduler integration, Docker support |

---

## License

MIT — see [LICENSE](LICENSE)
