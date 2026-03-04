# cruise.notify.py  v0.0.4
#
# Carnival Cruise countdown notifier — interactive menu edition.
# Sends reminders via Discord, Telegram, Pushover, and/or Email.
#
# Run normally  : python cruise.notify.py          (opens menu)
# Run headless  : python cruise.notify.py --run    (used by Task Scheduler)

APP_VERSION = "0.0.4"

# ── stdlib only (safe before any pip install) ──────────────────────────────────
import subprocess
import sys
from pathlib import Path

# ── Auto-install requirements ──────────────────────────────────────────────────

def _ensure_requirements():
    checks = [('requests', 'requests'), ('python-dotenv', 'dotenv'), ('colorama', 'colorama')]
    missing = [pkg for pkg, mod in checks if not _can_import(mod)]
    if not missing:
        return
    req_file = Path(__file__).parent / 'requirements.txt'
    if req_file.exists():
        print(f"📦 Installing missing packages from requirements.txt...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(req_file)])
    else:
        print(f"📦 Installing: {', '.join(missing)}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
    print()

def _can_import(mod):
    try:
        __import__(mod)
        return True
    except ImportError:
        return False

_ensure_requirements()

# ── Third-party imports ────────────────────────────────────────────────────────
from datetime import datetime
from email.message import EmailMessage
import json
import logging
import os
import smtplib

import requests
from colorama import init, Fore, Style
from dotenv import load_dotenv, set_key

init(autoreset=False)

# ── Paths (all relative to script — fully portable) ───────────────────────────

_BASE        = Path(__file__).parent
_LOG_DIR     = _BASE / 'logs'
_CRUISES_FILE = _BASE / 'cruises.json'
ENV_PATH     = _BASE / '.env'

_LOG_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(ENV_PATH)

# ── Logging ────────────────────────────────────────────────────────────────────

_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

cruise_logger = logging.getLogger('cruise.sent')
cruise_logger.setLevel(logging.INFO)
_sh = logging.FileHandler(_LOG_DIR / 'logging.cruise.txt')
_sh.setFormatter(_fmt)
cruise_logger.addHandler(_sh)

not_run_logger = logging.getLogger('cruise.not_run')
not_run_logger.setLevel(logging.INFO)
_nrh = logging.FileHandler(_LOG_DIR / 'did.not.run.log.cruise.txt')
_nrh.setFormatter(_fmt)
not_run_logger.addHandler(_nrh)

# ── UI helpers ─────────────────────────────────────────────────────────────────

def _box(title):
    c = Fore.CYAN + Style.BRIGHT
    print(f"\n{c}╔═══════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{c}║  {title:<37}║{Style.RESET_ALL}")
    print(f"{c}╚═══════════════════════════════════════╝{Style.RESET_ALL}")

def _div():
    print(f"  {Fore.WHITE}{Style.DIM}{'─'*39}{Style.RESET_ALL}")

def _opt(num, color, emoji, label):
    print(f"  {Fore.YELLOW}{Style.BRIGHT}{num}{Style.RESET_ALL}  {color}{emoji}  {label}{Style.RESET_ALL}")

def _prompt(text):
    return input(f"\n  {Fore.YELLOW}▶  {text}{Style.RESET_ALL}").strip()

def _ok(msg):   print(f"  {Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
def _warn(msg): print(f"  {Fore.YELLOW}⚠️  {msg}{Style.RESET_ALL}")
def _err(msg):  print(f"  {Fore.RED}❌ {msg}{Style.RESET_ALL}")
def _tick(ok):  return f"{Fore.GREEN}✅{Style.RESET_ALL}" if ok else f"{Fore.RED}❌{Style.RESET_ALL}"

# ── Cruise data (cruises.json) ─────────────────────────────────────────────────

_DEFAULT_CRUISES = [
    {"date": "6/30/25", "name": "Carnival Celebration"},
]

def load_cruises():
    if _CRUISES_FILE.exists():
        try:
            with open(_CRUISES_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return _DEFAULT_CRUISES.copy()

def save_cruises(cruises):
    with open(_CRUISES_FILE, 'w') as f:
        json.dump(cruises, f, indent=2)

# ── Service status checks ──────────────────────────────────────────────────────

def discord_status():  return bool(os.getenv('DISCORD_WEBHOOK_URL', ''))
def telegram_status(): return bool(os.getenv('TELEGRAM_BOT_TOKEN')) and bool(os.getenv('TELEGRAM_CHAT_ID'))
def pushover_status(): return bool(os.getenv('PUSHOVER_API_TOKEN')) and bool(os.getenv('PUSHOVER_USER_KEY'))
def email_status():    return all([os.getenv('EMAIL_SENDER'), os.getenv('EMAIL_PASSWORD'), os.getenv('EMAIL_RECIPIENT')])

# ── Credential helper ──────────────────────────────────────────────────────────

def _set_cred(key, label, secret=False):
    if secret:
        import getpass
        val = getpass.getpass(f"\n  {Fore.YELLOW}▶  {label} (hidden): {Style.RESET_ALL}").strip()
    else:
        val = input(f"\n  {Fore.YELLOW}▶  {label}: {Style.RESET_ALL}").strip()
    if not val:
        _warn("Skipped — value unchanged.")
        return
    set_key(str(ENV_PATH), key, val)
    os.environ[key] = val
    load_dotenv(str(ENV_PATH), override=True)
    _ok(f"{key} saved.")

# ── Senders ────────────────────────────────────────────────────────────────────

def send_discord_notification(message):
    webhook = os.getenv('DISCORD_WEBHOOK_URL', '')
    if not webhook:
        _warn("Discord not configured — skipping.")
        return
    try:
        r = requests.post(webhook, json={"content": message}, timeout=10)
        if r.status_code in (200, 204):
            _ok("Discord sent.")
        else:
            _err(f"Discord error: {r.status_code}")
            cruise_logger.error(f"Discord error: {r.status_code}")
    except requests.exceptions.RequestException as e:
        _err(f"Discord failed: {e}")
        cruise_logger.error(f"Discord failed: {e}")

def send_telegram_message(message):
    token   = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
    if not token or not chat_id:
        _warn("Telegram not configured — skipping.")
        return
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={'chat_id': chat_id, 'text': message}, timeout=10)
        if r.status_code == 200:
            _ok("Telegram sent.")
        else:
            _err(f"Telegram error: {r.status_code}")
            cruise_logger.error(f"Telegram error: {r.status_code}")
    except requests.exceptions.RequestException as e:
        _err(f"Telegram failed: {e}")
        cruise_logger.error(f"Telegram failed: {e}")

def send_pushover_message(message):
    token    = os.getenv('PUSHOVER_API_TOKEN', '')
    user_key = os.getenv('PUSHOVER_USER_KEY', '')
    if not token or not user_key:
        _warn("Pushover not configured — skipping.")
        return
    try:
        r = requests.post("https://api.pushover.net/1/messages.json",
                          data={"token": token, "user": user_key, "message": message}, timeout=10)
        if r.status_code == 200:
            _ok("Pushover sent.")
        else:
            _err(f"Pushover error: {r.status_code}")
            cruise_logger.error(f"Pushover error: {r.status_code}")
    except requests.exceptions.RequestException as e:
        _err(f"Pushover failed: {e}")
        cruise_logger.error(f"Pushover failed: {e}")

def send_email_message(message):
    smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    smtp_port   = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    username    = os.getenv('EMAIL_SENDER', '')
    password    = os.getenv('EMAIL_PASSWORD', '')
    email_from  = os.getenv('EMAIL_SENDER', '')
    email_to    = os.getenv('EMAIL_RECIPIENT', '')
    if not all([username, password, email_from, email_to]):
        _warn("Email not configured — skipping.")
        return
    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = 'Carnival Cruise Reminder'
        msg['From'] = email_from
        msg['To'] = email_to
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(msg)
        _ok("Email sent.")
    except Exception as e:
        _err(f"Email failed: {e}")
        cruise_logger.error(f"Email failed: {e}")

# ── Core check logic ───────────────────────────────────────────────────────────

def run_check(cruises=None):
    if cruises is None:
        cruises = load_cruises()
    if not cruises:
        _warn("No cruises configured. Use 'Manage Cruises' to add one.")
        return

    max_days      = int(os.getenv('MAX_DAYS_FOR_REMINDER', '65'))
    run_reminders = os.getenv('RUN_REMINDERS', 'true').lower() == 'true'
    today         = datetime.today().date()

    for c in cruises:
        target_date = c['date']
        cruise_name = c['name']
        try:
            cruise_date = datetime.strptime(target_date, '%m/%d/%y').date()
        except ValueError:
            _err(f"Invalid date '{target_date}' — use m/d/yy (e.g. 6/30/26). Skipping.")
            continue

        days_left = (cruise_date - today).days

        if run_reminders and days_left <= max_days:
            if days_left > 0:
                message = (f"There are {days_left} days left until your Carnival Cruise "
                           f"on {target_date} for the {cruise_name}. Enjoy your trip!")
            elif days_left == 0:
                message = (f"Today is the day of your Carnival Cruise on {target_date} "
                           f"for the {cruise_name}. Have a fantastic trip!")
            else:
                message = (f"Your Carnival Cruise on {target_date} for the {cruise_name} "
                           f"has already passed. We hope you had a wonderful trip!")

            print(f"\n  {Fore.CYAN}{Style.BRIGHT}🚢 {message}{Style.RESET_ALL}")
            send_discord_notification(message)
            send_telegram_message(message)
            send_pushover_message(message)
            # send_email_message(message)  # Uncomment to enable email
            cruise_logger.info(message)
        else:
            log_msg = (f"Reminder skipped for '{cruise_name}' on {target_date} "
                       f"— more than {max_days} days away.")
            print(f"  {Fore.WHITE}{Style.DIM}⏭️  {log_msg}{Style.RESET_ALL}")
            not_run_logger.info(log_msg)

# ── Notification services menus ────────────────────────────────────────────────

def discord_menu():
    while True:
        _box("💬 DISCORD SETTINGS")
        print(f"  Status: {_tick(discord_status())}\n")
        _opt("1", Fore.GREEN, "🔑", "Set Webhook URL")
        _opt("2", Fore.CYAN,  "📤", "Send Test Message")
        _div()
        _opt("0", Fore.RED + Style.DIM, "⬅️ ", "Back")
        c = _prompt("Choose: ")
        if c == "1":   _set_cred('DISCORD_WEBHOOK_URL', 'Webhook URL')
        elif c == "2": send_discord_notification("🧪 Test from Cruise Notifier!")
        elif c == "0": break

def telegram_menu():
    while True:
        _box("📱 TELEGRAM SETTINGS")
        print(f"  Status: {_tick(telegram_status())}\n")
        _opt("1", Fore.GREEN, "🔑", "Set Credentials")
        _opt("2", Fore.CYAN,  "📤", "Send Test Message")
        _div()
        _opt("0", Fore.RED + Style.DIM, "⬅️ ", "Back")
        c = _prompt("Choose: ")
        if c == "1":
            _set_cred('TELEGRAM_BOT_TOKEN', 'Bot Token')
            _set_cred('TELEGRAM_CHAT_ID',   'Chat ID')
        elif c == "2": send_telegram_message("🧪 Test from Cruise Notifier!")
        elif c == "0": break

def pushover_menu():
    while True:
        _box("📲 PUSHOVER SETTINGS")
        print(f"  Status: {_tick(pushover_status())}\n")
        _opt("1", Fore.GREEN, "🔑", "Set Credentials")
        _opt("2", Fore.CYAN,  "📤", "Send Test Message")
        _div()
        _opt("0", Fore.RED + Style.DIM, "⬅️ ", "Back")
        c = _prompt("Choose: ")
        if c == "1":
            _set_cred('PUSHOVER_API_TOKEN', 'API Token')
            _set_cred('PUSHOVER_USER_KEY',  'User Key')
        elif c == "2": send_pushover_message("🧪 Test from Cruise Notifier!")
        elif c == "0": break

def email_menu():
    while True:
        _box("📧 EMAIL SETTINGS")
        print(f"  Status: {_tick(email_status())}\n")
        _opt("1", Fore.GREEN, "🔑", "Set Credentials")
        _opt("2", Fore.CYAN,  "📤", "Send Test Email")
        _div()
        _opt("0", Fore.RED + Style.DIM, "⬅️ ", "Back")
        c = _prompt("Choose: ")
        if c == "1":
            _set_cred('EMAIL_SENDER',    'Sender Email')
            _set_cred('EMAIL_PASSWORD',  'App Password', secret=True)
            _set_cred('EMAIL_RECIPIENT', 'Recipient Email')
        elif c == "2": send_email_message("🧪 Test from Cruise Notifier!")
        elif c == "0": break

def services_menu():
    while True:
        _box("📬 NOTIFICATION SERVICES")
        _opt("1", Fore.WHITE, f"💬", f"Discord   {_tick(discord_status())}")
        _opt("2", Fore.WHITE, f"📱", f"Telegram  {_tick(telegram_status())}")
        _opt("3", Fore.WHITE, f"📲", f"Pushover  {_tick(pushover_status())}")
        _opt("4", Fore.WHITE, f"📧", f"Email     {_tick(email_status())}")
        _div()
        _opt("0", Fore.RED + Style.DIM, "⬅️ ", "Back")
        c = _prompt("Choose: ")
        if c == "1":   discord_menu()
        elif c == "2": telegram_menu()
        elif c == "3": pushover_menu()
        elif c == "4": email_menu()
        elif c == "0": break

# ── Cruise management menu ─────────────────────────────────────────────────────

def cruises_menu():
    while True:
        cruises = load_cruises()
        _box("🚢 MANAGE CRUISES")
        today = datetime.today().date()
        if cruises:
            for i, c in enumerate(cruises, 1):
                try:
                    d = datetime.strptime(c['date'], '%m/%d/%y').date()
                    days_left = (d - today).days
                    days_str = f"{days_left} days" if days_left > 0 else ("today!" if days_left == 0 else "passed")
                except ValueError:
                    days_str = "bad date"
                print(f"  {Fore.YELLOW}{Style.BRIGHT}{i}{Style.RESET_ALL}  "
                      f"{Fore.CYAN}{c['name']}{Style.RESET_ALL}  "
                      f"{Fore.WHITE}{Style.DIM}{c['date']}  [{days_str}]{Style.RESET_ALL}")
        else:
            _warn("No cruises configured.")
        _div()
        _opt("A", Fore.GREEN + Style.BRIGHT, "➕", "Add Cruise")
        _opt("R", Fore.RED,                  "🗑️ ", "Remove Cruise")
        _opt("0", Fore.RED + Style.DIM,      "⬅️ ", "Back")
        c = _prompt("Choose: ").upper()

        if c == "A":
            name = input(f"\n  {Fore.YELLOW}▶  Cruise name (e.g. Carnival Celebration): {Style.RESET_ALL}").strip()
            if not name:
                _warn("Name cannot be empty.")
                continue
            date_str = input(f"  {Fore.YELLOW}▶  Date (m/d/yy, e.g. 6/30/26): {Style.RESET_ALL}").strip()
            try:
                datetime.strptime(date_str, '%m/%d/%y')
            except ValueError:
                _err("Invalid date. Use m/d/yy (e.g. 6/30/26)")
                continue
            cruises.append({"date": date_str, "name": name})
            save_cruises(cruises)
            _ok(f"Added '{name}' on {date_str}.")

        elif c == "R":
            if not cruises:
                _warn("Nothing to remove.")
                continue
            idx = _prompt("Enter number to remove: ")
            if idx.isdigit() and 1 <= int(idx) <= len(cruises):
                removed = cruises.pop(int(idx) - 1)
                save_cruises(cruises)
                _ok(f"Removed '{removed['name']}'.")
            else:
                _err("Invalid number.")
        elif c == "0":
            break

# ── Schedule menu (Windows Task Scheduler) ────────────────────────────────────

def schedule_menu():
    _box("🗓️  SCHEDULE — WINDOWS TASK SCHEDULER")
    script     = str(Path(__file__).resolve())
    python     = sys.executable
    task_name  = "CruiseNotifier"

    result = subprocess.run(['schtasks', '/Query', '/TN', task_name],
                            capture_output=True, text=True)
    task_exists = result.returncode == 0
    status_str  = f"{Fore.GREEN}✅ Scheduled{Style.RESET_ALL}" if task_exists else f"{Fore.RED}❌ Not scheduled{Style.RESET_ALL}"
    print(f"\n  Task '{task_name}': {status_str}\n")

    _opt("1", Fore.GREEN + Style.BRIGHT, "🗓️ ", "Schedule daily (pick a time)")
    if task_exists:
        _opt("2", Fore.RED, "🗑️ ", "Remove scheduled task")
    _div()
    _opt("0", Fore.RED + Style.DIM, "⬅️ ", "Back")

    c = _prompt("Choose: ")
    if c == "1":
        time_str = _prompt("Run daily at what time? (HH:MM, 24h — e.g. 08:00): ")
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            _err("Invalid time. Use HH:MM e.g. 08:00")
            input(f"\n  {Fore.YELLOW}Press Enter...{Style.RESET_ALL}")
            return
        cmd = (f'schtasks /Create /F /SC DAILY /TN "{task_name}" '
               f'/TR "\\"{python}\\" \\"{script}\\" --run" /ST {time_str}')
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if r.returncode == 0:
            _ok(f"Scheduled '{task_name}' daily at {time_str}.")
        else:
            _err(f"schtasks failed: {r.stderr.strip()}")
    elif c == "2" and task_exists:
        r = subprocess.run(['schtasks', '/Delete', '/TN', task_name, '/F'],
                           capture_output=True, text=True)
        if r.returncode == 0:
            _ok("Scheduled task removed.")
        else:
            _err(f"Failed: {r.stderr.strip()}")

    input(f"\n  {Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

# ── Main menu ──────────────────────────────────────────────────────────────────

def main():
    # --run flag: headless mode for Task Scheduler (no menu)
    if '--run' in sys.argv:
        run_check()
        return

    while True:
        cruises = load_cruises()
        _box(f"🚢 CRUISE NOTIFIER  v{APP_VERSION}")
        _opt("1", Fore.CYAN + Style.BRIGHT,    "🚢", f"Check Cruises Now  {Fore.WHITE}{Style.DIM}[{len(cruises)} configured]")
        _opt("2", Fore.GREEN + Style.BRIGHT,   "📋", "Manage Cruises")
        _opt("3", Fore.MAGENTA + Style.BRIGHT, "📬", "Notification Services")
        _opt("4", Fore.BLUE + Style.BRIGHT,    "🗓️ ", "Schedule (Windows Task Scheduler)")
        _div()
        _opt("0", Fore.RED + Style.DIM,        "🚪", "Exit")

        c = _prompt("Choose an option: ")

        if c == "1":
            print()
            run_check(cruises)
            input(f"\n  {Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        elif c == "2":
            cruises_menu()
        elif c == "3":
            services_menu()
        elif c == "4":
            schedule_menu()
        elif c == "0":
            print(f"\n  {Fore.GREEN}{Style.BRIGHT}👋  Goodbye!{Style.RESET_ALL}\n")
            break
        else:
            _err("Invalid choice.")

if __name__ == '__main__':
    main()
