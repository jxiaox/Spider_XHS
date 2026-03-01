#!/bin/bash

cd "$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="./venv/bin/python3"
ENV_FILE=".env"
LOG_FILE="scraper.log"

ensure_venv() {
  if [ ! -x "$VENV_PYTHON" ]; then
    if command -v python3 >/dev/null 2>&1; then
      python3 -m venv ./venv || /usr/bin/python3 -m venv ./venv
    elif command -v python >/dev/null 2>&1; then
      python -m venv ./venv
    fi
  fi
  if [ -x "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" -m pip install --upgrade pip >/dev/null 2>&1
    if [ -f "requirements.txt" ]; then
      "$VENV_PYTHON" -m pip install -r requirements.txt
    fi
  else
    echo "Python environment not available"
    exit 1
  fi
}

case "$1" in
  status)
    echo "=== Scraper Process Status ==="
    ps aux | grep -E "scrape_from|ocr_subprocess" | grep -v grep || echo "No scraper running"
    echo ""
    echo "=== Last 5 Log Lines ==="
    tail -5 "$LOG_FILE" 2>/dev/null || echo "No log file found"
    ;;

  logs)
    echo "=== Last 60 Log Lines ==="
    tail -60 "$LOG_FILE"
    ;;

  progress)
    echo "=== Progress Summary ==="
    grep "Progress:" "$LOG_FILE" | tail -5
    echo ""
    echo "=== Errors (last 10) ==="
    grep -E "ERROR|Login expired" "$LOG_FILE" | tail -10
    ;;

  stop)
    echo "Stopping scraper..."
    pkill -f "scrape_from_local.py" 2>/dev/null
    pkill -f "ocr_subprocess.py" 2>/dev/null
    sleep 2
    # Verify
    if pgrep -f "scrape_from_local.py" > /dev/null; then
      echo "Force killing..."
      pkill -9 -f "scrape_from_local.py"
      pkill -9 -f "ocr_subprocess.py"
    fi
    echo "Scraper stopped."
    ;;

  restart)
    echo "Restarting scraper..."
    pkill -f "scrape_from_local.py" 2>/dev/null
    pkill -f "ocr_subprocess.py" 2>/dev/null
    sleep 2
    pkill -9 -f "scrape_from_local.py" 2>/dev/null
    pkill -9 -f "ocr_subprocess.py" 2>/dev/null
    sleep 1
    ensure_venv
    nohup caffeinate -i $VENV_PYTHON scrape_from_local.py >> "$LOG_FILE" 2>&1 &
    echo "Scraper restarted (PID: $!)"
    sleep 3
    tail -5 "$LOG_FILE"
    ;;

  update_cookie)
    if [ -z "$2" ]; then
      echo "Usage: ./manage_scraper.sh update_cookie 'YOUR_COOKIE_STRING'"
      echo ""
      echo "Current cookie (first 80 chars):"
      head -1 "$ENV_FILE" | cut -c1-80
      exit 1
    fi
    echo "Updating cookie..."
    # Backup old .env
    cp "$ENV_FILE" "${ENV_FILE}.bak"
    # Write new cookie (preserve other lines if any)
    COOKIE="$2"
    # Replace first line (COOKIES=...)
    echo "COOKIES='${COOKIE}'" > "${ENV_FILE}.tmp"
    tail -n +2 "$ENV_FILE" >> "${ENV_FILE}.tmp"
    mv "${ENV_FILE}.tmp" "$ENV_FILE"
    echo "Cookie updated."
    echo ""
    echo "Restarting scraper with new cookie..."
    pkill -f "scrape_from_local.py" 2>/dev/null
    pkill -f "ocr_subprocess.py" 2>/dev/null
    sleep 2
    pkill -9 -f "scrape_from_local.py" 2>/dev/null
    pkill -9 -f "ocr_subprocess.py" 2>/dev/null
    sleep 1
    ensure_venv
    nohup caffeinate -i $VENV_PYTHON scrape_from_local.py >> "$LOG_FILE" 2>&1 &
    echo "Scraper restarted (PID: $!)"
    sleep 3
    tail -5 "$LOG_FILE"
    ;;

  *)
    echo "Scraper Manager"
    echo "==============="
    echo "Usage: ./manage_scraper.sh <command>"
    echo ""
    echo "Commands:"
    echo "  status         - Check scraper status and recent logs"
    echo "  logs           - Show last 60 lines of log"
    echo "  progress       - Show progress summary"
    echo "  stop           - Stop scraper"
    echo "  restart        - Restart scraper"
    echo "  update_cookie  - Update cookie and restart"
    echo ""
    echo "Examples:"
    echo "  ./manage_scraper.sh status"
    echo "  ./manage_scraper.sh update_cookie 'gid=xxx; web_session=yyy; ...'"
    ;;
esac
