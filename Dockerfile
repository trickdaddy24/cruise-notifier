# Dockerfile — Cruise Notifier (headless mode)
# Runs: python cruise.notify.py --run
# Mount .env and cruises.json as volumes before running.
#
# Build:  docker build -t cruise-notifier .
# Run:    docker run --rm \
#           -v "$(pwd)/.env:/app/.env" \
#           -v "$(pwd)/cruises.json:/app/cruises.json" \
#           -v "$(pwd)/logs:/app/logs" \
#           cruise-notifier

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY cruise.notify.py .

# Logs directory
RUN mkdir -p logs

# Run headless (--run skips the interactive menu)
CMD ["python", "cruise.notify.py", "--run"]
