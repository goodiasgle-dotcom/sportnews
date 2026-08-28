#!/usr/bin/env python3
"""
Sportnews - Highlights Fetcher
Sources:
1. Greek TV broadcasters (SKAI.gr, Open TV, Novasports) — European match highlights
2. Greek club channels (PAOK, AEK, Olympiacos, Aris, Panathinaikos, OFI) — league content
3. Score.gr — Greek football news
All sources work in Greece — no geo-restricted channels.
"""

import json
import os
import sys
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone, timedelta
from html import unescape

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_DIR, 'static', 'highlights.json')

# === GREEK TV BROADCASTERS (European match highlights) ===
TV_CHANNELS = {
    'SKAI.gr': {
        'id': 'UCmHgxU394HiIAsN1fMegqzw',
        'type': 'broadcaster',
    },
    'Open TV': {
        'id': 'UCllCEPTcZ_GplDaFsdq_utA',
        'type': 'broadcaster',
    },
    'Novasports': {
        'id': 'UCEIbXco8hU9oDHXGo1kwIlA',
        'type': 'broadcaster',
    },
}

# === GREEK CLUB CHANNELS (league content + behind-the-scenes) ===
CLUB_CHANNELS = {
    'PAOK FC': {
        'id': 'UCInZnZ8JYwmIvs8gtNriwSQ',
    },
    'AEK FC': {
        'id': 'UCX8HprRO1BYnQ6Mu2nB9VsQ',
    },
    'Olympiacos FC': {
        'id': 'UCLf7YXb-0PWEeq59Z_q318A',
    },
    'Aris FC': {
        'id': 'UCy8t8HKIih3JQZygj4XTejA',
    },
    'Panathinaikos FC': {
        'id': 'UCvDGYaeFq9sBdj0cGnZ_Uhg',
    },
    'OFI CRETE FC': {
        'id': 'UCoZ-4i_HbZL5tQOZAEJ6LiA',
    },
}

# === NEWS CHANNELS (Greek football news) ===
NEWS_CHANNELS = {
    'Score.gr': {
        'id': 'UCiaVQyCQACIgkBPYpAjKJGA',
    },
}

# Greek team names (for European competition tagging)
GREEK_TEAMS = [
    'paok', 'παοκ', 'aek', 'αεκ', 'olympiacos', 'ολυμπιακός',
    'aris', 'άρης', 'panathinaikos', 'παναθηναϊκός',
    'atromitos', 'ατρόμητος', 'levadiakos', 'λεβαδειακός',
    'ofi', 'οφη', 'brann', 'μπραν', 'hfc', 'Χράντρετς',
    'sofia', 'σόφια', 'cska', 'leverkusen', 'celtic', 'lask',
]


def fetch_url(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'SportNewsGR/1.0 (RSS Reader)'
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  Error: {e}")
        return None


def parse_youtube_feed(xml_content):
    """Parse YouTube Atom feed."""
    videos = []
    ns = {
        'media': 'http://search.yahoo.com/mrss/',
        'yt': 'http://www.youtube.com/xml/schemas/2015',
        'atom': 'http://www.w3.org/2005/Atom',
    }
    try:
        root = ET.fromstring(xml_content)
        for entry in root.findall('atom:entry', ns):
            title_el = entry.find('atom:title', ns)
            title = title_el.text.strip() if title_el is not None and title_el.text else ''

            vid_el = entry.find('yt:videoId', ns)
            video_id = vid_el.text.strip() if vid_el is not None and vid_el.text else ''

            pub_el = entry.find('atom:published', ns)
            published = pub_el.text.strip() if pub_el is not None and pub_el.text else ''

            thumbnail_url = ''
            media_group = entry.find('media:group', ns)
            description = ''
            if media_group is not None:
                thumb_el = media_group.find('media:thumbnail', ns)
                if thumb_el is not None:
                    thumbnail_url = thumb_el.get('url', '')
                desc_el = media_group.find('media:description', ns)
                description = desc_el.text.strip() if desc_el is not None and desc_el.text else ''

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


def is_football_related(title, description=''):
    """Check if video is football-related."""
    text = (title + ' ' + description).lower()
    # Must have at least one football keyword
    football_kw = ['football', 'ποδόσφαιρο', 'goal', 'γκολ', 'highlight', 'match',
                   'αγώνας', 'vs', 'versus', 'league', 'cup', 'κύπελλο',
                   'conference', 'europa', 'champion', 'super league', 'πρωτάθλημα',
                   'προκριση', 'πρόκριση', 'qualify', 'qualif', 'highlights',
                   'στιγμιότυπα', 'γκολαρες', 'live', 'post game', 'review',
                   'δηλώσεις', 'statements', 'παρακάμερα', 'behind the scenes',
                   'aftermovie', 'build', 'show', 'review', 'γύρος', 'round',
                   'md ', 'matchday']
    return any(kw in text for kw in football_kw)


def is_match_highlight(title, description=''):
    """Check if video is a match highlight or related content."""
    text = (title + ' ' + description).lower()

    # EXCLUDE non-football content
    exclude = ['podcast', 'transfer', 'jersey reveal', 'commercial', 'sponsor',
               'jumbo pack', 'random pack', 'ultimate team', 'fpl', 'fantasy',
               'hellenic', 'τσακ κοτζαμπαση', 'rondo', 'atmosphere', 'θέαμα',
               'κόσμος', 'fans', 'ultras', 'choreography', 'tifo',
               'diamond league', 'στίβος', 'athletics', 'volleyball', 'βόλεϊ',
               'basketball', 'μπάσκετ', 'handball', 'χάντμπολ', 'tennis',
               'swimming', 'κολύμβηση', 'cycling', 'ποδηλασία']
    if any(kw in text for kw in exclude):
        return False

    # Must be football-related
    if not is_football_related(title, description):
        return False

    # INCLUDE if has match-related keywords
    include = ['highlight', 'highlights', 'all goals', 'goals', 'every goal',
               'extended highlights', 'key moments', 'γκολ', 'γκολαρες',
               'στιγμιότυπα', 'vs', 'live', 'post game', 'review',
               'παρακάμερα', 'behind the scenes', 'aftermovie', 'build',
               'δηλώσεις', 'statements', 'show', 'γύρος', 'round',
               'md ', 'matchday', 'προπόνηση', 'training', 'press conference',
               'συνέντευξη']
    return any(kw in text for kw in include)


def detect_competition(title, description=''):
    """Detect European competition from title — explicit mentions only."""
    text = (title + ' ' + description).lower()
    if any(kw in text for kw in ['champions league', 'ucl']):
        return 'cl'
    if any(kw in text for kw in ['europa league', 'uel']):
        return 'el'
    if any(kw in text for kw in ['conference league', 'uecl']):
        return 'ecl'
    return 'league'


def is_greek_team_playing(title, description=''):
    """Check if a Greek team is playing."""
    text = (title + ' ' + description).lower()
    return any(team in text for team in GREEK_TEAMS)


def extract_teams(title):
    """Extract team names from title."""
    patterns = [
        # "T1 - T2 | HIGHLIGHTS" or "T1 - T2 4-0" (at start)
        r'^([A-Za-zΑ-Ωα-ωΆ-Ώά-ώ0-9\s\.]+)\s*[-–]\s*([A-Za-zΑ-Ωα-ωΆ-Ώά-ώ0-9\s\.]+?)(?:\s*\||\s+\d+-\d+|$)',
        # "T1 vs T2" (at start)
        r'^([A-Za-zΑ-Ωα-ωΆ-Ώά-ώ0-9\s\.]+)\s+vs\.?\s+([A-Za-zΑ-Ωα-ωΆ-Ώά-ώ0-9\s\.]+?)(?:\s*[\|\-]|$)',
        # Greek: "στιγμιότυπα/παρακάμερα του/των T1-T2"
        r'(?:στιγμιότυπα|παρακάμερα)\s+(?:του|των)\s+(?:αγώνα\s+)?(.+?)[\s]*[-–]\s*(.+?)(?:\s*[-–]|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            t1 = match.group(1).strip()
            t2 = match.group(2).strip()
            # Clean up common suffixes
            for cleanup in ['HIGHLIGHTS', 'Highlights', 'Extended Highlights',
                           'All Goals', 'Goals', 'Super League', 'Champions League',
                           'Europa League', 'Conference League', 'PAOK TV', 'AEK FC',
                           'FC', 'F.C.', 'FC TV', 'αγώνα', 'match', 'LIVE',
                           'Post Game', 'Post game', 'Press Conference',
                           'Pre-game', 'Pre game', 'OFI Crete', 'ΠΑΕ', 'ΠΑΕ ΟΦΗ']:
                t1 = t1.replace(cleanup, '').strip()
                t2 = t2.replace(cleanup, '').strip()
            # Remove dates like MD1, MD 1, 27/08/2026
            t1 = re.sub(r'\bMD\s*\d+\b', '', t1).strip()
            t1 = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '', t1).strip()
            t2 = re.sub(r'\bMD\s*\d+\b', '', t2).strip()
            t2 = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '', t2).strip()
            # Remove trailing scores
            t1 = re.sub(r'\s+\d+$', '', t1).strip()
            t2 = re.sub(r'\s+\d+$', '', t2).strip()
            # Skip if either team is too short or too long
            if t1 and t2 and 2 < len(t1) < 40 and 2 < len(t2) < 40:
                return f"{t1} vs {t2}"
    return ''


def parse_date(date_str):
    """Parse date string to ISO format."""
    if not date_str:
        return datetime.now(timezone.utc).isoformat()
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()


def process_channel(channel_name, channel_info, source_type):
    """Process a single YouTube channel and return highlights."""
    print(f"\nFetching: {channel_name}...")
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_info['id']}"

    xml_content = fetch_url(url)
    if not xml_content:
        print(f"  Failed to fetch feed")
        return []

    videos = parse_youtube_feed(xml_content)
    print(f"  Found {len(videos)} videos")

    highlights = []
    for video in videos:
        if not is_match_highlight(video['title'], video.get('description', '')):
            continue

        # Detect competition
        competition = detect_competition(video['title'], video.get('description', ''))

        teams = extract_teams(video['title'])

        highlights.append({
            'id': video['videoId'][:12],
            'videoId': video['videoId'],
            'title': video['title'],
            'thumbnail': video['thumbnail'],
            'teams': teams,
            'competition': competition,
            'channel': channel_name,
            'source': source_type,
            'platform': 'youtube',
            'pubDate': parse_date(video.get('published', '')),
        })

    print(f"  Added: {len(highlights)} highlights")
    return highlights


def main():
    print("Sportnews - Fetching highlights...")
    print("=" * 50)

    all_highlights = []
    seen_ids = set()

    # === GREEK TV BROADCASTERS (European match highlights) ===
    print("\n--- Greek TV Broadcasters ---")
    for channel_name, channel_info in TV_CHANNELS.items():
        highlights = process_channel(channel_name, channel_info, 'broadcaster')
        for h in highlights:
            if h['videoId'] not in seen_ids:
                seen_ids.add(h['videoId'])
                all_highlights.append(h)

    # === GREEK CLUB CHANNELS (league content + behind-the-scenes) ===
    print("\n--- Greek Club Channels ---")
    for channel_name, channel_info in CLUB_CHANNELS.items():
        highlights = process_channel(channel_name, channel_info, 'club')
        for h in highlights:
            if h['videoId'] not in seen_ids:
                seen_ids.add(h['videoId'])
                all_highlights.append(h)

    # === NEWS CHANNELS (Greek football news) ===
    print("\n--- News Channels ---")
    for channel_name, channel_info in NEWS_CHANNELS.items():
        highlights = process_channel(channel_name, channel_info, 'news')
        for h in highlights:
            if h['videoId'] not in seen_ids:
                seen_ids.add(h['videoId'])
                all_highlights.append(h)

    # Sort by date (newest first)
    all_highlights.sort(key=lambda x: x['pubDate'], reverse=True)

    # Keep 30 days
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)
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
    comp_counts = Counter(h['competition'] for h in filtered)
    source_counts = Counter(h['source'] for h in filtered)
    for comp, count in comp_counts.most_common():
        label = {'cl': 'Champions League', 'el': 'Europa League',
                 'ecl': 'Conference League', 'league': 'League'}[comp]
        print(f"  {label}: {count}")
    print(f"\nBy source:")
    for source, count in source_counts.most_common():
        print(f"  {source}: {count}")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
