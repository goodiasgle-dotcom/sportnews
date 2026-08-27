#!/bin/bash
# Auto-update script - fetches news and pushes to GitHub
# Run by cron every hour

PROJECT_DIR="/home/ch/Desktop/sport news/sportnews"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
LOG_FILE="/home/ch/.local/share/sport-news-update.log"

export PATH="/home/ch/.local/bin:$PATH"

echo "$(date): Starting news update" >> "$LOG_FILE"

# Go to project directory
cd "$PROJECT_DIR" || exit 1

# Fetch news
python3 "$SCRIPTS_DIR/fetch_news.py" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "$(date): RSS fetch failed" >> "$LOG_FILE"
    exit 1
fi

# Build site
hugo --minify --baseURL "https://goodiasgle-dotcom.github.io/sportnews/" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "$(date): Hugo build failed" >> "$LOG_FILE"
    exit 1
fi

# Check if news.json changed
if git diff --quiet static/news.json; then
    echo "$(date): No new news to commit" >> "$LOG_FILE"
    exit 0
fi

# Commit and push
git add static/news.json
git commit -m "Auto-update: $(date +%Y-%m-%d_%H:%M)" >> "$LOG_FILE" 2>&1

# Push with token (stored in a file for cron)
TOKEN_FILE="/home/ch/.github-token"
if [ -f "$TOKEN_FILE" ]; then
    TOKEN=$(cat "$TOKEN_FILE")
    git remote set-url origin "https://goodiasgle-dotcom:${TOKEN}@github.com/goodiasgle-dotcom/sportnews.git"
    git push origin main >> "$LOG_FILE" 2>&1
    git remote set-url origin "https://github.com/goodiasgle-dotcom/sportnews.git"
    if [ $? -eq 0 ]; then
        echo "$(date): Push succeeded" >> "$LOG_FILE"
    else
        echo "$(date): Push failed" >> "$LOG_FILE"
    fi
else
    echo "$(date): No token file found - cannot push" >> "$LOG_FILE"
fi

echo "$(date): Update complete" >> "$LOG_FILE"
