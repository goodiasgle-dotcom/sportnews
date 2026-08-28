#!/usr/bin/env python3
"""
Sportnews - YouTube Highlights Fetcher
Fetches goal highlights from official YouTube channels via RSS feeds.
No API key needed — uses public YouTube RSS feeds.
"""

import json
import os
import sys
import re
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from html import unescape

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_DIR, 'static', 'highlights.json')

# Official YouTube channels that post football highlights
CHANNELS = {
    'Premier League': {
        'id': 'UCG5qGWdu8nIRZqJ_GgDwQ-w',
        'competitions': {
            'league': ['premier league'],
        }
    },
    'La Liga': {
        'id': 'UCTv-XvfzLX3i4IGWAm4sbmA',
        'competitions': {
            'league': ['la liga', 'laliga'],
        }
    },
    'Bundesliga': {
        'id': 'UC6UL29enLNe4mqwTfAyeNuw',
        'competitions': {
            'league': ['bundesliga'],
        }
    },
    'Serie A': {
        'id': 'UCBJeMCIeLQos7wacox4hmLQ',
        'competitions': {
            'league': ['serie a'],
        }
    },
    'Ligue 1': {
        'id': 'UCQsH5XtIc9hONE1BQjucM0g',
        'competitions': {
            'league': ['ligue 1'],
        }
    },
    'Sky Sports Football': {
        'id': 'UCZ7wY7MRDSygp63HIEfdQZA',
        'competitions': {
            'cl': ['champions league', 'ucl'],
            'el': ['europa league', 'uel'],
            'ecl': ['conference league', 'uecl'],
            'league': ['premier league', 'carabao cup', 'fa cup'],
        }
    },
    'ESPN FC': {
        'id': 'UC6c1z7bA__85CIWZ_jpCK-Q',
        'competitions': {
            'cl': ['champions league', 'ucl'],
            'el': ['europa league', 'uel'],
            'ecl': ['conference league', 'uecl'],
            'league': ['premier league', 'la liga', 'serie a', 'bundesliga', 'ligue 1'],
        }
    },
}

HIGHLIGHT_KEYWORDS = [
    'highlights', 'highlight', 'all goals', 'goals',
    'extended highlights', 'recap', 'key moments',
    'best moments', 'every angle', 'every goal',
    'classic highlights', 'full highlights',
]

# Words that indicate it's NOT a match highlight
NOT_HIGHLIGHT_KEYWORDS = [
    'podcast', 'transfer news', 'gossip', 'reaction',
    'press conference', 'interview', 'analysis',
    'preview', 'debate', 'discuss', 'show',
    'podcast', 'fpl', 'fantasy',
]

NAMESPACES = {
    'media': 'http://search.yahoo.com/mrss/',
    'yt': 'http://www.youtube.com/xml/schemas/2015',
    'atom': 'http://www.w3.org/2005/Atom',
}


def fetch_url(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'SportNewsGR/1.0 (RSS Reader)'
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def parse_youtube_feed(xml_content):
    """Parse YouTube Atom feed and extract video entries."""
    videos = []
    try:
        root = ET.fromstring(xml_content)
        for entry in root.findall('atom:entry', NAMESPACES):
            title_el = entry.find('atom:title', NAMESPACES)
            title = title_el.text.strip() if title_el is not None and title_el.text else ''

            video_id_el = entry.find('yt:videoId', NAMESPACES)
            video_id = video_id_el.text.strip() if video_id_el is not None and video_id_el.text else ''

            published_el = entry.find('atom:published', NAMESPACES)
            published = published_el.text.strip() if published_el is not None and published_el.text else ''

            # Get thumbnail
            thumbnail_url = ''
            media_group = entry.find('media:group', NAMESPACES)
            if media_group is not None:
                thumbnail_el = media_group.find('media:thumbnail', NAMESPACES)
                if thumbnail_el is not None:
                    thumbnail_url = thumbnail_el.get('url', '')
                # Get description from media:description
                desc_el = media_group.find('media:description', NAMESPACES)
                description = desc_el.text.strip() if desc_el is not None and desc_el.text else ''
            else:
                description = ''

            if title and video_id:
                videos.append({
                    'title': unescape(title),
                    'videoId': video_id,
                    'thumbnail': thumbnail_url,
                    'published': published,
                    'description': unescape(description)[:200],
                })
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
    return videos


def is_highlight_video(title, description=''):
    """Check if a video is a highlight/goals video."""
    text = (title + ' ' + description).lower()
    # Exclude non-highlight content
    if any(kw in text for kw in NOT_HIGHLIGHT_KEYWORDS):
        return False
    return any(kw in text for kw in HIGHLIGHT_KEYWORDS)


def detect_competition(title, description='', channel_competitions=None):
    """Detect competition from video title."""
    text = (title + ' ' + description).lower()

    if channel_competitions:
        for comp, keywords in channel_competitions.items():
            if any(kw in text for kw in keywords):
                return comp

    # Fallback global detection
    if any(kw in text for kw in ['champions league', 'ucl']):
        return 'cl'
    if any(kw in text for kw in ['europa league', 'uel']):
        return 'el'
    if any(kw in text for kw in ['conference league', 'uecl']):
        return 'ecl'
    return 'league'


def extract_teams(title):
    """Try to extract team names from highlight title."""
    # Common patterns: "Team A 2-1 Team B", "Team A vs Team B"
    patterns = [
        r'(.+?)\s+\d+\s*[-–]\s*\d+\s+(.+?)(?:\s*\||$)',
        r'(.+?)\s+vs\.?\s+(.+?)(?:\s*\||$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return f"{match.group(1).strip()} vs {match.group(2).strip()}"
    return ''


def parse_date(date_str):
    """Parse ISO date string."""
    if not date_str:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def generate_id(video_id):
    return video_id[:12]


def main():
    print("Sportnews - Fetching YouTube highlights...")
    print("=" * 50)

    all_highlights = []
    seen_ids = set()

    for channel_name, channel_info in CHANNELS.items():
        print(f"\nFetching: {channel_name}...")
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_info['id']}"

        xml_content = fetch_url(url)
        if not xml_content:
            print(f"  Failed to fetch feed")
            continue

        videos = parse_youtube_feed(xml_content)
        print(f"  Found {len(videos)} videos")

        channel_comps = channel_info.get('competitions', {})

        for video in videos:
            # Skip duplicates
            if video['videoId'] in seen_ids:
                continue

            # Check if it's a highlight video
            if not is_highlight_video(video['title'], video.get('description', '')):
                continue

            competition = detect_competition(
                video['title'],
                video.get('description', ''),
                channel_comps
            )

            teams = extract_teams(video['title'])

            highlight = {
                'id': generate_id(video['videoId']),
                'videoId': video['videoId'],
                'title': video['title'],
                'thumbnail': video['thumbnail'],
                'teams': teams,
                'competition': competition,
                'channel': channel_name,
                'pubDate': parse_date(video.get('published', '')),
            }

            all_highlights.append(highlight)
            seen_ids.add(video['videoId'])

    # Sort by date (newest first)
    all_highlights.sort(key=lambda x: x['pubDate'], reverse=True)

    # Keep only last 7 days of highlights
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    filtered = []
    for h in all_highlights:
        try:
            dt = datetime.fromisoformat(h['pubDate'].replace('Z', '+00:00'))
            if dt > cutoff:
                filtered.append(h)
        except Exception:
            filtered.append(h)

    # Save
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print(f"Total highlights: {len(filtered)}")
    from collections import Counter
    comp_counts = Counter(h['competition'] for h in filtered)
    for comp, count in comp_counts.most_common():
        label = {'cl': 'Champions League', 'el': 'Europa League', 'ecl': 'Conference League', 'league': 'League'}[comp]
        print(f"  {label}: {count}")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
