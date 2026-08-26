#!/bin/bash
# Sport News GR - Build Script
# Fetches RSS feeds, translates, and builds the Hugo site

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Sport News GR - Building site..."
echo "================================"

# Step 1: Fetch RSS feeds and generate news.json
echo ""
echo "Step 1: Fetching RSS feeds..."
python3 "$SCRIPT_DIR/fetch_news.py"

# Step 2: Build Hugo site
echo ""
echo "Step 2: Building Hugo site..."
cd "$PROJECT_DIR"
hugo --minify

echo ""
echo "Build complete!"
echo "Output directory: $PROJECT_DIR/public/"
