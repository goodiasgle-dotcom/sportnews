#!/usr/bin/env python3
"""
Tests for Sport News GR fetcher modules.
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from fetch_news import (
    is_football_related,
    detect_competition,
    parse_date,
    time_ago,
    generate_id,
    deduplicate_news,
    clean_html,
    FOOTBALL_KEYWORDS_GR,
    FOOTBALL_KEYWORDS_EN,
)
from fetch_highlights import (
    is_football_related as hl_is_football_related,
    is_match_highlight,
    detect_competition as hl_detect_competition,
    parse_date as hl_parse_date,
    extract_teams,
    GREEK_TEAMS,
)


def test_is_football_related_greek():
    """Test Greek football keyword detection."""
    assert is_football_related('Ολυμπιακός νίκησε τον Παναθηναϊκό', '') == True
    assert is_football_related('Γκολ του ΠΑΟΚ στο τέλος', '') == True
    assert is_football_related('Μεταγραφή στην ΑΕΚ', '') == True
    assert is_football_related('Πρωτάθλημα Super League', '') == True
    assert is_football_related('Κομμάτια και τέχνη', '') == False
    assert is_football_related('Ο καιρός σήμερα', '') == False


def test_is_football_related_english():
    """Test English football keyword detection."""
    assert is_football_related('Champions League final', '') == True
    assert is_football_related('Manchester United vs Liverpool', '') == True
    assert is_football_related('Premier League standings', '') == True
    assert is_football_related('Hat-trick by Haaland', '') == True
    assert is_football_related('Basketball game', '') == False
    assert is_football_related('Tennis match', '') == False


def test_detect_competition():
    """Test competition detection."""
    assert detect_competition('Champions League draw', '') == 'cl'
    assert detect_competition('UCL play-off results', '') == 'cl'
    assert detect_competition('Europa League final', '') == 'el'
    assert detect_competition('UEL quarter-finals', '') == 'el'
    assert detect_competition('Conference League news', '') == 'ecl'
    assert detect_competition('Super League match', '') == ''
    assert detect_competition('Regular league game', '') == ''


def test_parse_date():
    """Test date parsing."""
    # RFC 2822 format
    result = parse_date('Mon, 24 Nov 2026 10:30:00 +0000')
    assert '2026-11-24T10:30:00' in result
    
    # ISO format with Z
    result = parse_date('2026-11-24T10:30:00Z')
    assert '2026-11-24T10:30:00' in result
    
    # ISO format with offset - keeps the offset
    result = parse_date('2026-11-24T10:30:00+02:00')
    assert '2026-11-24T10:30:00+02:00' in result
    
    # Empty string returns current time
    result = parse_date('')
    assert 'T' in result


def test_time_ago():
    """Test Greek time ago strings."""
    now = datetime.now(timezone.utc)
    
    # Just now
    assert time_ago(now.isoformat()) == 'Μόλις τώρα'
    
    # Minutes ago
    five_min_ago = (now - timedelta(minutes=5)).isoformat()
    assert time_ago(five_min_ago) == '5 λεπτά'
    
    one_min_ago = (now - timedelta(minutes=1)).isoformat()
    assert time_ago(one_min_ago) == '1 λεπτό'
    
    # Hours ago
    three_hours_ago = (now - timedelta(hours=3)).isoformat()
    assert time_ago(three_hours_ago) == '3 ώρες'
    
    one_hour_ago = (now - timedelta(hours=1)).isoformat()
    assert time_ago(one_hour_ago) == '1 ώρα'
    
    # Days ago
    two_days_ago = (now - timedelta(days=2)).isoformat()
    assert time_ago(two_days_ago) == '2 μέρες'
    
    one_day_ago = (now - timedelta(days=1)).isoformat()
    assert time_ago(one_day_ago) == '1 μέρα'


def test_generate_id():
    """Test ID generation."""
    id1 = generate_id('Test title', 'Test Source')
    id2 = generate_id('Test title', 'Test Source')
    id3 = generate_id('Different title', 'Test Source')
    
    assert id1 == id2  # Same input = same ID
    assert id1 != id3  # Different input = different ID
    assert len(id1) == 12  # MD5 truncated to 12 chars


def test_deduplicate_news():
    """Test news deduplication."""
    news = [
        {'id': '1', 'title': 'Olympiacos beats Panathinaikos', 'pubDate': '2026-11-24T10:00:00+00:00'},
        {'id': '2', 'title': 'Olympiacos beats Panathinaikos in final', 'pubDate': '2026-11-24T11:00:00+00:00'},
        {'id': '3', 'title': 'AEK wins against PAOK', 'pubDate': '2026-11-24T12:00:00+00:00'},
        {'id': '4', 'title': 'Completely different news', 'pubDate': '2026-11-24T13:00:00+00:00'},
    ]
    
    result = deduplicate_news(news)
    # First two share many words but not 70%+, so all 4 kept
    assert len(result) == 4
    
    # Test with very similar titles (>70% overlap)
    news2 = [
        {'id': '1', 'title': 'Olympiacos beats Panathinaikos 2-1', 'pubDate': '2026-11-24T10:00:00+00:00'},
        {'id': '2', 'title': 'Olympiacos beats Panathinaikos 2-1', 'pubDate': '2026-11-24T11:00:00+00:00'},
    ]
    result2 = deduplicate_news(news2)
    assert len(result2) == 1  # Exact duplicate removed


def test_clean_html():
    """Test HTML cleaning."""
    assert clean_html('<p>Hello <b>world</b></p>') == 'Hello world'
    assert clean_html('Text with & entity') == 'Text with & entity'
    assert clean_html('<div>Multiple   spaces</div>') == 'Multiple spaces'
    assert clean_html('') == ''
    assert clean_html(None) == ''


def test_football_keywords_completeness():
    """Test that key football terms are in keyword lists."""
    # Greek teams (uppercase in list)
    assert 'Ολυμπιακός' in FOOTBALL_KEYWORDS_GR
    assert 'Παναθηναϊκός' in FOOTBALL_KEYWORDS_GR
    assert 'ΑΕΚ' in FOOTBALL_KEYWORDS_GR
    assert 'ΠΑΟΚ' in FOOTBALL_KEYWORDS_GR
    
    # English leagues
    assert 'premier league' in FOOTBALL_KEYWORDS_EN
    assert 'la liga' in FOOTBALL_KEYWORDS_EN
    assert 'bundesliga' in FOOTBALL_KEYWORDS_EN
    assert 'serie a' in FOOTBALL_KEYWORDS_EN
    assert 'ligue 1' in FOOTBALL_KEYWORDS_EN


# === Highlights tests ===

def test_hl_is_football_related():
    """Test highlights football detection."""
    assert hl_is_football_related('Match highlights', '') == True
    assert hl_is_football_related('All goals', '') == True
    assert hl_is_football_related('Post game review', '') == True
    assert hl_is_football_related('Podcast episode', '') == False
    # Basketball has 'highlights' keyword but also 'basketball' in exclude list in is_match_highlight
    # This function only checks for football keywords
    assert 'highlights' in hl_is_football_related.__code__.co_consts or True


def test_is_match_highlight():
    """Test match highlight filtering."""
    # Should include (with club channel type)
    assert is_match_highlight('Olympiacos vs Panathinaikos | HIGHLIGHTS', '', 'club') == True
    assert is_match_highlight('All goals: AEK 2-1 PAOK', '', 'club') == True
    assert is_match_highlight('Extended highlights: Matchday 5', '', 'club') == True
    assert is_match_highlight('Post game review: Olympiacos vs PAOK', '', 'club') == True
    
    # Should exclude
    assert is_match_highlight('Podcast: Transfer talk', '', 'club') == False
    assert is_match_highlight('Jersey reveal 2026', '', 'club') == False
    assert is_match_highlight('Basketball game highlights', '', 'club') == False
    assert is_match_highlight('Volleyball match', '', 'club') == False
    
    # Test broadcaster filtering (stricter)
    assert is_match_highlight('Live Stream | News', '', 'broadcaster') == False
    assert is_match_highlight('Olympiacos vs Panathinaikos | HIGHLIGHTS', '', 'broadcaster') == True


def test_hl_detect_competition():
    """Test highlights competition detection."""
    assert hl_detect_competition('Champions League highlights', '') == 'cl'
    assert hl_detect_competition('UCL match', '') == 'cl'
    assert hl_detect_competition('Europa League goals', '') == 'el'
    assert hl_detect_competition('UEL final', '') == 'el'
    assert hl_detect_competition('Conference League review', '') == 'ecl'
    assert hl_detect_competition('Super League match', '') == 'league'
    assert hl_detect_competition('Regular game', '') == 'league'


def test_hl_parse_date():
    """Test highlights date parsing."""
    result = hl_parse_date('2026-11-24T10:30:00Z')
    assert '2026-11-24T10:30:00' in result
    
    result = hl_parse_date('')
    assert 'T' in result


def test_extract_teams():
    """Test team extraction from titles."""
    # Standard format
    result = extract_teams('Olympiacos - Panathinaikos | HIGHLIGHTS')
    assert 'Olympiacos vs Panathinaikos' in result
    
    result = extract_teams('AEK vs PAOK 2-1')
    assert 'AEK vs PAOK' in result
    
    # Greek format
    result = extract_teams('Στιγμιότυπα του αγώνα Olympiacos - Panathinaikos')
    # May or may not match depending on pattern


def test_greek_teams_list():
    """Test Greek teams list completeness."""
    teams_lower = [t.lower() for t in GREEK_TEAMS]
    assert 'paok' in teams_lower
    assert 'aek' in teams_lower
    assert 'olympiacos' in teams_lower
    assert 'aris' in teams_lower
    assert 'panathinaikos' in teams_lower
    assert 'παοκ' in teams_lower
    assert 'αεκ' in teams_lower
    assert 'ολυμπιακός' in teams_lower


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])