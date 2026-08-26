#!/usr/bin/env python3
"""
Sport News GR - RSS Feed Fetcher and Processor
Fetches RSS feeds from Greek and European sports sites,
translates foreign headlines to Greek, and generates news.json
"""

import json
import hashlib
import os
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape
import re

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
OUTPUT_FILE = os.path.join(PROJECT_DIR, 'static', 'news.json')
FEEDS_FILE = os.path.join(DATA_DIR, 'feeds.json')
TRANSLATION_CACHE_FILE = os.path.join(DATA_DIR, 'translation_cache.json')

# Football keywords for filtering (Greek and English)
FOOTBALL_KEYWORDS_GR = [
    'ποδόσφαιρο', 'ποδοσφαίρου', 'ποδοσφαιρικός', 'ποδοσφαιρική',
    'ομάδα', 'ομάδας', 'παίκτης', 'παίκτη', 'προπονητής',
    'γκολ', 'νίκη', 'ήττα', 'ισοπαλία', 'πρωτάθλημα',
    'κύπελλο', 'λίγκα', 'champions', 'europa', 'conference',
    'σούπερ λίγκα', 'super league', 'premier league', 'serie a',
    'la liga', 'bundesliga', 'ligue 1', 'liga', 'erected',
    'μεταγραφή', 'μεταγραφές', 'συμβόλαιο', 'συμβόλαια',
    'Ολυμπιακός', 'Παναθηναϊκός', 'ΑΕΚ', 'ΠΑΟΚ', 'Άρης',
    'Ολυμπιακού', 'Παναθηναϊκού', 'ΑΕΚ', 'ΠΑΟΚ', 'Άρη',
    'real madrid', 'barcelona', 'manchester', 'liverpool', 'chelsea',
    'arsenal', 'bayern', 'juventus', 'milan', 'inter', 'napoli',
    'psg', 'paris saint', 'atletico', 'dortmund', 'leverkusen'
]

FOOTBALL_KEYWORDS_EN = [
    'football', 'soccer', 'goal', 'match', 'team', 'player',
    'manager', 'coach', 'transfer', 'league', 'cup', 'champion',
    'premier', 'serie a', 'la liga', 'bundesliga', 'ligue 1',
    'olympiacos', 'panathinaikos', 'aek', 'paok', 'aris',
    'real madrid', 'barcelona', 'manchester', 'liverpool', 'chelsea',
    'arsenal', 'bayern', 'juventus', 'milan', 'inter', 'napoli',
    'psg', 'paris saint', 'atletico', 'dortmund', 'leverkusen'
]

# Source to CSS class mapping
SOURCE_CLASSES = {
    'Sport24': 'sport24',
    'Gazzetta.gr': 'gazzetta',
    'Sportime': 'sportime',
    'Novasports': 'novasports',
    'BBC Sport': 'bbc',
    'Sky Sports': 'sky',
    'ESPN': 'espn',
    'The Guardian': 'guardian',
    'Football Italia': 'football-italia',
    'Gazzetta dello Sport': 'gazzetta-it',
    'Sky Sport Italia': 'sky-it',
    "L'Equipe": 'lequipe',
    'Kicker': 'kicker',
    'Marca': 'marca',
    'ESPN Deportes': 'espn'
}


def load_json(filepath, default=None):
    """Load JSON file with fallback."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(filepath, data):
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_url(url, timeout=15):
    """Fetch content from URL."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'SportNewsGR/1.0 (RSS Reader)'
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def parse_rss(xml_content):
    """Parse RSS/Atom feed and extract items."""
    items = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # Handle different feed formats
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'content': 'http://purl.org/rss/1.0/modules/content/'
        }
        
        # Try RSS 2.0 format
        for item in root.findall('.//item'):
            title = item.findtext('title', '').strip()
            link = item.findtext('link', '').strip()
            description = item.findtext('description', '').strip()
            pub_date = item.findtext('pubDate', '').strip()
            content = item.findtext('content:encoded', '', namespaces).strip()
            
            if title and link:
                items.append({
                    'title': clean_html(title),
                    'link': link,
                    'description': clean_html(description),
                    'content': clean_html(content) if content else clean_html(description),
                    'pubDate': pub_date
                })
        
        # Try Atom format if no RSS items found
        if not items:
            for entry in root.findall('.//atom:entry', namespaces):
                title = entry.findtext('atom:title', '', namespaces).strip()
                link_elem = entry.find('atom:link', namespaces)
                link = link_elem.get('href', '') if link_elem is not None else ''
                summary = entry.findtext('atom:summary', '', namespaces).strip()
                content = entry.findtext('atom:content', '', namespaces).strip()
                updated = entry.findtext('atom:updated', '', namespaces).strip()
                
                if title and link:
                    items.append({
                        'title': clean_html(title),
                        'link': link,
                        'description': clean_html(summary),
                        'content': clean_html(content) if content else clean_html(summary),
                        'pubDate': updated
                    })
        
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
    
    return items


def clean_html(text):
    """Remove HTML tags and clean text."""
    if not text:
        return ''
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode HTML entities
    text = unescape(text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_football_related(title, description=''):
    """Check if article is about football."""
    text = (title + ' ' + description).lower()
    
    # Check Greek keywords
    for keyword in FOOTBALL_KEYWORDS_GR:
        if keyword.lower() in text:
            return True
    
    # Check English keywords
    for keyword in FOOTBALL_KEYWORDS_EN:
        if keyword in text:
            return True
    
    return False


def needs_translation(language):
    """Check if text needs translation (not Greek)."""
    return language != 'el'


def translate_text(text, source_lang='en', target_lang='el'):
    """Translate text using MyMemory API (free tier)."""
    if not text or source_lang == target_lang:
        return text
    
    # Check cache first
    cache = load_json(TRANSLATION_CACHE_FILE, {})
    cache_key = hashlib.md5(f"{source_lang}:{target_lang}:{text}".encode()).hexdigest()
    
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        # MyMemory API - free, no key needed
        encoded_text = urllib.parse.quote(text[:500])  # Limit to 500 chars
        url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair={source_lang}|{target_lang}"
        
        response = fetch_url(url, timeout=10)
        if response:
            data = json.loads(response)
            if data.get('responseStatus') == 200:
                translated = data['responseData']['translatedText']
                if translated and translated != text:
                    # Cache the translation
                    cache[cache_key] = translated
                    save_json(TRANSLATION_CACHE_FILE, cache)
                    return translated
        
        # Rate limiting - wait between requests
        time.sleep(1)
        
    except Exception as e:
        print(f"  Translation error: {e}")
    
    return text  # Return original if translation fails


def parse_date(date_str):
    """Parse various date formats to ISO format."""
    if not date_str:
        return datetime.now(timezone.utc).isoformat()
    
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
        '%d %b %Y %H:%M:%S',
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


def time_ago(iso_date):
    """Convert ISO date to Greek time ago string."""
    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        seconds = int(diff.total_seconds())
        
        if seconds < 60:
            return 'Μόλις τώρα'
        elif seconds < 3600:
            minutes = seconds // 60
            return f'{minutes} λεπτό' if minutes == 1 else f'{minutes} λεπτά'
        elif seconds < 86400:
            hours = seconds // 3600
            return f'{hours} ώρα' if hours == 1 else f'{hours} ώρες'
        else:
            days = seconds // 86400
            return f'{days} μέρα' if days == 1 else f'{days} μέρες'
    except:
        return 'Πρόσφατα'


def generate_id(title, source):
    """Generate unique ID for news item."""
    text = f"{source}:{title}"
    return hashlib.md5(text.encode()).hexdigest()[:12]


def deduplicate_news(news_list):
    """Remove duplicate news items."""
    seen = {}
    unique = []
    
    for item in news_list:
        # Normalize title for comparison
        normalized = re.sub(r'[^\w\s]', '', item['title'].lower()).strip()
        words = set(normalized.split())
        
        is_duplicate = False
        
        # Check against already seen items
        for key, existing in seen.items():
            existing_words = set(re.sub(r'[^\w\s]', '', existing['title'].lower()).strip().split())
            
            # Calculate similarity
            if words and existing_words:
                common = words & existing_words
                similarity = len(common) / max(len(words), len(existing_words))
                
                # If more than 70% similar, it's a duplicate
                if similarity > 0.7:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            seen[item['id']] = item
            unique.append(item)
    
    return unique


def main():
    print("Sport News GR - Fetching RSS feeds...")
    print("=" * 50)
    
    # Load feeds configuration
    feeds_data = load_json(FEEDS_FILE, {'feeds': []})
    feeds = feeds_data.get('feeds', [])
    
    if not feeds:
        print("No feeds configured!")
        sys.exit(1)
    
    all_news = []
    stats = {'total': 0, 'football': 0, 'translated': 0}
    
    for feed in feeds:
        print(f"\nFetching: {feed['name']}...")
        
        xml_content = fetch_url(feed['url'])
        if not xml_content:
            continue
        
        items = parse_rss(xml_content)
        print(f"  Found {len(items)} items")
        
        for item in items[:20]:  # Limit to 20 items per feed
            stats['total'] += 1
            
            # Check if football related
            if not is_football_related(item['title'], item.get('description', '')):
                continue
            
            stats['football'] += 1
            
            title = item['title']
            description = item.get('description', '') or item.get('content', '')
            
            # Translate if needed
            if needs_translation(feed['language']):
                original_title = title
                title = translate_text(title, feed['language'], 'el')
                if title != original_title:
                    stats['translated'] += 1
                # Translate description too (shorter)
                if description:
                    description = translate_text(description[:200], feed['language'], 'el')
                time.sleep(0.5)  # Rate limiting
            
            # Create news item
            news_item = {
                'id': generate_id(title, feed['name']),
                'title': title,
                'highlights': description[:300] + '...' if len(description) > 300 else description,
                'source': feed['name'],
                'source_class': SOURCE_CLASSES.get(feed['name'], 'default'),
                'link': item['link'],
                'pubDate': parse_date(item.get('pubDate', '')),
                'time_display': time_ago(parse_date(item.get('pubDate', ''))),
                'country': feed['country']
            }
            
            all_news.append(news_item)
    
    # Deduplicate
    print(f"\nBefore dedup: {len(all_news)} items")
    all_news = deduplicate_news(all_news)
    print(f"After dedup: {len(all_news)} items")
    
    # Sort by date (newest first)
    all_news.sort(key=lambda x: x['pubDate'], reverse=True)
    
    # Save to JSON
    save_json(OUTPUT_FILE, all_news)
    
    print("\n" + "=" * 50)
    print(f"Stats:")
    print(f"  Total items fetched: {stats['total']}")
    print(f"  Football items: {stats['football']}")
    print(f"  Translated items: {stats['translated']}")
    print(f"  Final unique items: {len(all_news)}")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
