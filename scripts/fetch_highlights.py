#!/usr/bin/env python3
"""
Sportnews - Highlights Fetcher
Sources (in priority order):
1. Greek club channels (always work in Greece)
2. Dailymotion (fewer geo-restrictions)
No geo-restricted YouTube channels.
"""

import json
import os
import sys
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from html import unescape

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_DIR, 'static', 'highlights.json')

# === GREEK CLUB CHANNELS (primary - always work in Greece) ===
GREEK_CLUBS = {
    'PAOK FC': {
        'id': 'UCInZnZ8JYwmIvs8gtNriwSQ',
        'keywords_gr': ['στιγμιότυπα', 'highlights', 'γκολ', 'αγώνας', 'παρακάμερα'],
        'keywords_en': ['highlights', 'goals', 'match'],
    },
    'AEK FC': {
        'id': 'UCX8HprRO1BYnQ6Mu2nB9VsQ',
        'keywords_gr': ['στιγμιότυπα', 'highlights', 'γκολ', 'αγώνας'],
        'keywords_en': ['highlights', 'goals', 'match'],
    },
    'Olympiacos FC': {
        'id': 'UCLf7YXb-0PWEeq59Z_q318A',
        'keywords_gr': ['στιγμιότυπα', 'highlights', 'γκολ', 'αγώνας', 'παρακάμερα'],
        'keywords_en': ['highlights', 'goals', 'match', 'behind the scenes'],
    },
    'Aris FC': {
        'id': 'UCy8t8HKIih3JQZygj4XTejA',
        'keywords_gr': ['στιγμιότυπα', 'highlights', 'γκολ', 'αγώνας', 'παρακάμερα'],
        'keywords_en': ['highlights', 'goals', 'match'],
    },
}

# === DAILYMOTION CHANNELS (secondary - fewer geo-restrictions) ===
DAILYMOTION_CHANNELS = {
    'footballhighlights': {
        'competitions': {
            'cl': ['champions league', 'ucl'],
            'el': ['europa league', 'uel'],
            'ecl': ['conference league', 'uecl'],
            'league': ['premier league', 'la liga', 'serie a', 'bundesliga', 'ligue 1'],
        }
    },
    'footballhighlightstv': {
        'competitions': {
            'cl': ['champions league', 'ucl'],
            'el': ['europa league', 'uel'],
            'ecl': ['conference league', 'uecl'],
            'league': ['premier league', 'la liga', 'serie a', 'bundesliga', 'ligue 1'],
        }
    },
}

# Competition detection keywords
COMP_KEYWORDS = {
    'cl': ['champions league', 'ucl', 'Champions League'],
    'el': ['europa league', 'uel', 'Europa League'],
    'ecl': ['conference league', 'uecl', 'Conference League'],
}


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


def parse_dailymotion_feed(xml_content):
    """Parse Dailymotion RSS feed."""
    videos = []
    ns = '{http://search.yahoo.com/mrss/}'
    try:
        root = ET.fromstring(xml_content)
        for item in root.findall('.//item'):
            title_el = item.find('title')
            title = title_el.text.strip() if title_el is not None and title_el.text else ''

            guid_el = item.find('guid')
            video_id = guid_el.text.strip() if guid_el is not None and guid_el.text else ''

            pub_el = item.find('pubDate')
            pub_date = pub_el.text.strip() if pub_el is not None and pub_el.text else ''

            thumb_el = item.find(f'{ns}thumbnail')
            thumbnail_url = thumb_el.get('url', '') if thumb_el is not None else ''

            desc_el = item.find('description')
            description = desc_el.text.strip() if desc_el is not None and desc_el.text else ''

            if title and video_id:
                videos.append({
                    'title': unescape(title),
                    'videoId': video_id,
                    'thumbnail': thumbnail_url,
                    'published': pub_date,
                    'description': unescape(description)[:200],
                })
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
    return videos


def is_match_highlight(title, description='', keywords_gr=None, keywords_en=None):
    """Check if video is a match highlight (not just news/interview)."""
    text = (title + ' ' + description).lower()

    # EXCLUDE first — catch non-highlight content before anything else
    exclude = ['podcast', 'transfer', 'press conference', 'interview',
               'analysis', 'preview', 'debate', 'show', 'fpl', 'fantasy',
               'jersey reveal', 'commercial', 'sponsor', 'announcement',
               'ready for', 'propovisi', 'προπόνηση', 'training',
               'jumbo pack', 'random pack', 'ultimate team', 'season',
               'jersey', 'fanis', 'hellenic', 'τσακ κοτζαμπαση',
               'matchday', 'md-', 'md 1', 'md 2', 'md 3', 'md 4',
               'friendly', 'φιλικό', 'behind the scenes', 'παρακάμερα',
               'δηλώσεις', 'statements', 'presser', 'rondo',
               'atmosphere', 'θέαμα', 'κόσμος', 'fans', 'ultras',
               'choreography', 'tifo']
    if any(kw in text for kw in exclude):
        return False

    # For Greek clubs: look for match-related keywords
    if keywords_gr:
        if any(kw.lower() in text for kw in keywords_gr):
            return True
    if keywords_en:
        if any(kw.lower() in text for kw in keywords_en):
            return True

    # Include if has highlight keywords
    include = ['highlights', 'highlight', 'all goals', 'goals',
               'extended highlights', 'key moments', 'every goal',
               'στιγμιότυπα', 'γκολ', 'γκολαρες']
    return any(kw in text for kw in include)


def detect_competition(title, description=''):
    """Detect European competition from title."""
    text = (title + ' ' + description).lower()
    # More specific patterns first
    if any(kw in text for kw in ['champions league', 'ucl', 'Champions League']):
        return 'cl'
    if any(kw in text for kw in ['europa league', 'uel', 'Europa League']):
        return 'el'
    if any(kw in text for kw in ['conference league', 'uecl', 'Conference League',
                                   'europa conference', 'conference']):
        return 'ecl'
    return 'league'


def is_greek_team_playing(title, description=''):
    """Check if a Greek team is playing (to tag European competition)."""
    text = (title + ' ' + description).lower()
    greek_teams = ['paok', 'παοκ', 'aek', 'αεκ', 'olympiacos', 'ολυμπιακός',
                   'aris', 'άρης', 'panathinaikos', 'παναθηναϊκός',
                   'ατρόμητος', 'atromitos', 'λεβαδειακός', 'levadiakos',
                   'μπραν', 'brann', 'παο']
    return any(team in text for team in greek_teams)


def extract_teams(title):
    """Extract team names from title."""
    # Handle Greek format: "Τα στιγμιότυπα του ΠΑΟΚ-Λεβαδειακός - PAOK TV"
    # Handle Greek format: "Η παρακάμερα του αγώνα ΑΕΚ-Athens Kallithea 4-0"
    # Handle English format: "AEK - Ηρακλής 4-0"
    # Handle: "ΑΕΚ-ATHENS KALLITHEA 4-0"
    patterns = [
        # Greek: "στιγμιότυπα/παρακάμερα του/των αγώνα T1-T2"
        r'(?:στιγμιότυπα|παρακάμερα)\s+(?:του|των)\s+(?:αγώνα\s+)?(.+?)[\s]*[-–]\s*(.+?)(?:\s*[-–]|$)',
        # "T1-T2 4-0" (with hyphen)
        r'(.+?)[-–]\s*(.+?)(?:\s+\d+-\d+|$)',
        # "T1 - T2 4-0" style
        r'(.+?)\s*[-–]\s*(.+?)(?:\s+\d+-\d+|$)',
        # "T1 vs T2"
        r'(.+?)\s+vs\.?\s+(.+?)(?:\s*[\|\-]|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            t1 = match.group(1).strip()
            t2 = match.group(2).strip()
            # Clean up
            for cleanup in ['Highlights', 'Extended Highlights', 'All Goals',
                           'Goals', 'Super League', 'Champions League', 'Europa League',
                           'PAOK TV', 'AEK FC', 'FC', 'F.C.', 'FC TV',
                           'Highligh', 'αγώνα', 'match']:
                t1 = t1.replace(cleanup, '').strip()
                t2 = t2.replace(cleanup, '').strip()
            # Remove trailing scores
            t1 = re.sub(r'\s+\d+$', '', t1).strip()
            t2 = re.sub(r'\s+\d+$', '', t2).strip()
            if t1 and t2 and len(t1) < 50 and len(t2) < 50:
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


def main():
    print("Sportnews - Fetching highlights...")
    print("=" * 50)

    all_highlights = []
    seen_ids = set()
    seen_team_comp = set()

    # === GREEK CLUBS (primary - always work in Greece) ===
    print("\n--- Greek Club Channels ---")
    for club_name, club_info in GREEK_CLUBS.items():
        print(f"\nFetching: {club_name}...")
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={club_info['id']}"

        xml_content = fetch_url(url)
        if not xml_content:
            print(f"  Failed to fetch feed")
            continue

        videos = parse_youtube_feed(xml_content)
        print(f"  Found {len(videos)} videos")

        added = 0
        for video in videos:
            if not is_match_highlight(
                video['title'], video.get('description', ''),
                club_info.get('keywords_gr'), club_info.get('keywords_en')
            ):
                continue

            if video['videoId'] in seen_ids:
                continue

            competition = detect_competition(video['title'], video.get('description', ''))
            # If no explicit competition keyword but it's a Greek team in European context, tag as UCL/UEL/UECL
            if competition == 'league' and is_greek_team_playing(video['title'], video.get('description', '')):
                # Check if it mentions European opponents or competition context
                text = (video['title'] + ' ' + video.get('description', '')).lower()
                if any(kw in text for kw in ['conference', 'europa', 'champions', 'qualify', 'qualif',
                                              'προκριση', 'πρόκριση', 'brann', 'μπραν',
                                              'norway', 'norwegian', 'UECL']):
                    competition = 'ecl'
                elif any(kw in text for kw in ['european', 'ευρωπη']):
                    competition = 'el'

            teams = extract_teams(video['title'])
            team_key = f"{competition}:{teams.lower()}" if teams else ''

            if team_key and team_key in seen_team_comp:
                continue
            if team_key:
                seen_team_comp.add(team_key)
            seen_ids.add(video['videoId'])

            all_highlights.append({
                'id': video['videoId'][:12],
                'videoId': video['videoId'],
                'title': video['title'],
                'thumbnail': video['thumbnail'],
                'teams': teams,
                'competition': competition,
                'channel': club_name,
                'platform': 'youtube',
                'pubDate': parse_date(video.get('published', '')),
            })
            added += 1

        print(f"  Added: {added} highlights")

    # === DAILYMOTION (secondary - fewer geo-restrictions) ===
    print("\n--- Dailymotion ---")
    for channel_name, channel_info in DAILYMOTION_CHANNELS.items():
        print(f"\nFetching: {channel_name}...")
        url = f"https://www.dailymotion.com/rss/user/{channel_name}"

        xml_content = fetch_url(url)
        if not xml_content:
            print(f"  Failed to fetch feed")
            continue

        videos = parse_dailymotion_feed(xml_content)
        print(f"  Found {len(videos)} videos")

        channel_comps = channel_info.get('competitions', {})
        added = 0

        for video in videos:
            if not is_match_highlight(video['title'], video.get('description', '')):
                continue

            if video['videoId'] in seen_ids:
                continue

            competition = detect_competition(video['title'], video.get('description', ''))
            # Override with channel-specific detection
            text = (video['title'] + ' ' + video.get('description', '')).lower()
            for comp, keywords in channel_comps.items():
                if any(kw in text for kw in keywords):
                    competition = comp
                    break

            teams = extract_teams(video['title'])
            team_key = f"{competition}:{teams.lower()}" if teams else ''

            if team_key and team_key in seen_team_comp:
                continue
            if team_key:
                seen_team_comp.add(team_key)
            seen_ids.add(video['videoId'])

            all_highlights.append({
                'id': video['videoId'][:12],
                'videoId': video['videoId'],
                'title': video['title'],
                'thumbnail': video['thumbnail'],
                'teams': teams,
                'competition': competition,
                'channel': channel_name,
                'platform': 'dailymotion',
                'pubDate': parse_date(video.get('published', '')),
            })
            added += 1

        print(f"  Added: {added} highlights")

    # Sort by date (newest first)
    all_highlights.sort(key=lambda x: x['pubDate'], reverse=True)

    # Keep: Greek clubs 30 days, Dailymotion 30 days
    now = datetime.now(timezone.utc)
    filtered = []
    for h in all_highlights:
        try:
            dt = datetime.fromisoformat(h['pubDate'].replace('Z', '+00:00'))
            cutoff = now - timedelta(days=30)
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
    plat_counts = Counter(h['platform'] for h in filtered)
    for comp, count in comp_counts.most_common():
        label = {'cl': 'Champions League', 'el': 'Europa League',
                 'ecl': 'Conference League', 'league': 'League'}[comp]
        print(f"  {label}: {count}")
    print(f"\nBy platform:")
    for plat, count in plat_counts.most_common():
        print(f"  {plat}: {count}")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
