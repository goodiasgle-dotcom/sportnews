// Sportnews - Main JavaScript

let allNews = [];
let displayedCount = 0;
const ITEMS_PER_PAGE = 10;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadNewsData();
    initTheme();
    initBackToTop();
    initFilters();
});

// Load news from JSON data file
async function loadNewsData() {
    showLoading(true);

    try {
        const response = await fetch('news.json');
        if (!response.ok) throw new Error('Failed to load news');

        allNews = await response.json();
        displayedCount = 0;

        updateLastTime();
        loadMoreNews();
    } catch (error) {
        console.error('Error loading news:', error);
        showEmptyState();
    } finally {
        showLoading(false);
    }
}

// Load more news items
function loadMoreNews() {
    const container = document.getElementById('news-container');
    const loadMoreBtn = document.getElementById('load-more');

    const filtered = currentFilter === 'all'
        ? allNews
        : allNews.filter(n => n.country === currentFilter);

    const start = displayedCount;
    const end = Math.min(start + ITEMS_PER_PAGE, filtered.length);

    for (let i = start; i < end; i++) {
        const news = filtered[i];
        const card = createNewsCard(news);
        container.appendChild(card);
    }

    displayedCount = end;

    if (displayedCount < filtered.length) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }

    if (filtered.length === 0) {
        showEmptyState();
    }
}

// Create a news card element
function createNewsCard(news) {
    const article = document.createElement('article');
    article.className = 'news-card';
    article.dataset.id = news.id;
    article.dataset.country = news.country || 'all';

    const sourceClass = getSourceClass(news.source);
    const isNew = isRecentlyPublished(news.pubDate);

    article.innerHTML = `
        <div class="card-header">
            <div class="card-header-left">
                <span class="source-badge source-${sourceClass}">${escapeHtml(news.source)}</span>
                ${isNew ? '<span class="new-badge">ΝΕΟ</span>' : ''}
            </div>
            <span class="post-time">${escapeHtml(news.time_display)}</span>
        </div>
        <div class="card-body">
            <h2 class="card-title">${escapeHtml(news.title)}</h2>
            <div class="card-content">
                <p>${escapeHtml(news.highlights || '')}</p>
                <a href="${escapeHtml(news.link)}" target="_blank" rel="noopener noreferrer" class="read-original">
                    Διαβάστε το πλήρες άρθρο →
                </a>
            </div>
        </div>
        <div class="card-footer">
            <button class="expand-btn" onclick="toggleCard(this)">
                <span class="expand-text">Διαβάστε περισσότερα</span>
                <span class="expand-icon">▼</span>
            </button>
        </div>
    `;

    return article;
}

// Toggle card expansion with smooth animation
function toggleCard(button) {
    const card = button.closest('.news-card');
    const content = card.querySelector('.card-content');
    const icon = button.querySelector('.expand-icon');
    const text = button.querySelector('.expand-text');

    if (content.classList.contains('expanded')) {
        content.classList.remove('expanded');
        button.classList.remove('active');
        text.textContent = 'Διαβάστε περισσότερα';
    } else {
        content.classList.add('expanded');
        button.classList.add('active');
        text.textContent = 'Κλείστε';
    }
}

// Check if article was published in the last hour
function isRecentlyPublished(pubDate) {
    if (!pubDate) return false;
    try {
        const published = new Date(pubDate);
        const now = new Date();
        return (now - published) < 60 * 60 * 1000;
    } catch {
        return false;
    }
}

// Get source CSS class
function getSourceClass(source) {
    const sourceMap = {
        'BBC Sport': 'bbc',
        'Sky Sports': 'sky',
        'ESPN': 'espn',
        'The Guardian': 'guardian',
        'Gazzetta.gr': 'gazzetta',
        'Gazzetta Football': 'gazzetta',
        'Novasports': 'novasports',
        'Redaroume': 'redaroume',
        'OPA.gr': 'opa',
        'Football Italia': 'football-italia',
        'Get German Football News': 'german-fn',
        'Get French Football News': 'french-fn',
        'Get Spanish Football News': 'spanish-fn',
        'Get Italian Football News': 'italian-fn',
        '101 Great Goals': 'great-goals'
    };

    for (const [key, value] of Object.entries(sourceMap)) {
        if (source.includes(key)) return value;
    }
    return 'default';
}

// Update last update time
function updateLastTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    document.getElementById('last-update').textContent = `${hours}:${minutes}`;
}

// Show/hide loading
function showLoading(show) {
    const loader = document.getElementById('loading');
    loader.style.display = show ? 'flex' : 'none';
}

// Show empty state
function showEmptyState() {
    const container = document.getElementById('news-container');
    container.innerHTML = `
        <div class="empty-state">
            <div class="icon">📰</div>
            <h3>Δεν βρέθηκαν νέα</h3>
            <p>Δοκιμάστε ξανά αργότερα</p>
        </div>
    `;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// === DARK MODE ===
function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeIcon(next);
}

function updateThemeIcon(theme) {
    const btn = document.querySelector('.theme-toggle');
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// === BACK TO TOP ===
function initBackToTop() {
    window.addEventListener('scroll', function() {
        const btn = document.getElementById('back-to-top');
        if (btn) btn.classList.toggle('visible', window.scrollY > 300);
    });
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// === COUNTRY FILTER ===
let currentFilter = 'all';

function initFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            currentFilter = this.dataset.country;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            resetAndFilter();
        });
    });
}

function resetAndFilter() {
    const container = document.getElementById('news-container');
    container.innerHTML = '';
    displayedCount = 0;
    loadMoreNews();
}

function applyCurrentFilter() {
    document.querySelectorAll('.news-card').forEach(card => {
        if (currentFilter === 'all') {
            card.style.display = '';
        } else {
            card.style.display = card.dataset.country === currentFilter ? '' : 'none';
        }
    });
}
