// Sportnews - Main JavaScript

let allNews = [];
let allHighlights = [];
let displayedCount = 0;
const ITEMS_PER_PAGE = 5;
const HIGHLIGHTS_PER_PAGE = 6;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadNewsData();
    loadHighlightsData();
    initTheme();
    initBackToTop();
    initFilters();
    initHighlightFilters();
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

// Load highlights from JSON data file
async function loadHighlightsData() {
    const hlLoading = document.getElementById('highlights-loading');
    const hlEmpty = document.getElementById('highlights-empty');
    const hlContainer = document.getElementById('highlights-container');

    try {
        const response = await fetch('highlights.json');
        if (!response.ok) throw new Error('No highlights yet');

        allHighlights = await response.json();
        if (allHighlights.length === 0) {
            hlLoading.style.display = 'none';
            hlEmpty.style.display = 'block';
            return;
        }
        hlLoading.style.display = 'none';
        renderHighlights('all');
    } catch (error) {
        hlLoading.style.display = 'none';
        hlEmpty.style.display = 'block';
    }
}

// Render highlights for current filter
let hlDisplayedCount = 0;
let currentHlFilter = 'all';

function renderHighlights(filter) {
    const container = document.getElementById('highlights-container');
    container.innerHTML = '';
    currentHlFilter = filter;
    hlDisplayedCount = 0;

    const filtered = filter === 'all'
        ? allHighlights
        : allHighlights.filter(h => h.competition === filter);

    loadMoreHighlights(filtered, container);
}

function loadMoreHighlights(filtered, container) {
    const start = hlDisplayedCount;
    const end = Math.min(start + HIGHLIGHTS_PER_PAGE, filtered.length);

    for (let i = start; i < end; i++) {
        const hl = filtered[i];
        const card = createHighlightCard(hl);
        container.appendChild(card);
    }
    hlDisplayedCount = end;
}

function createHighlightCard(hl) {
    const card = document.createElement('div');
    card.className = 'highlight-card';
    card.onclick = function() { openHighlightModal(hl.videoId); };

    const compLabel = {
        'cl': 'UCL',
        'el': 'UEL',
        'ecl': 'UECL',
        'league': 'Πρωτάθλημα'
    }[hl.competition] || '';

    card.innerHTML = `
        <div class="highlight-thumb">
            <img src="${escapeHtml(hl.thumbnail)}" alt="${escapeHtml(hl.title)}" loading="lazy">
            <div class="highlight-play"></div>
            ${compLabel ? `<span class="highlight-comp-badge">${compLabel}</span>` : ''}
        </div>
        <div class="highlight-info">
            <div class="highlight-title">${escapeHtml(hl.title)}</div>
            <div class="highlight-meta">${escapeHtml(hl.teams || '')}</div>
        </div>
    `;

    return card;
}

function openHighlightModal(videoId) {
    let modal = document.getElementById('highlight-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'highlight-modal';
        modal.className = 'highlight-video-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <button class="modal-close" onclick="closeHighlightModal()">&times;</button>
                <iframe src="" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>
        `;
        modal.onclick = function(e) {
            if (e.target === modal) closeHighlightModal();
        };
        document.body.appendChild(modal);
    }

    const iframe = modal.querySelector('iframe');
    iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeHighlightModal() {
    const modal = document.getElementById('highlight-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.querySelector('iframe').src = '';
        document.body.style.overflow = '';
    }
}

// Load more news items
function loadMoreNews() {
    const container = document.getElementById('news-container');
    const loadMoreBtn = document.getElementById('load-more');

    const filtered = getFilteredNews();

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
    } else {
        hideEmptyState();
    }
}

function getFilteredNews() {
    if (currentFilter === 'all') return allNews;

    // Competition filters (cl, el, ecl)
    if (['cl', 'el', 'ecl'].includes(currentFilter)) {
        return allNews.filter(n => n.competition === currentFilter);
    }

    // Country filters
    return allNews.filter(n => n.country === currentFilter);
}

// Create a news card element
function createNewsCard(news) {
    const article = document.createElement('article');
    article.className = 'news-card';
    article.dataset.id = news.id;
    article.dataset.country = news.country || 'all';
    article.dataset.competition = news.competition || '';

    const sourceClass = getSourceClass(news.source);
    const isNew = isRecentlyPublished(news.pubDate);

    article.innerHTML = `
        <div class="card-header">
            <div class="card-header-left">
                <span class="source-badge source-${sourceClass}">${escapeHtml(news.source)}</span>
                ${news.competition ? `<span class="comp-badge comp-${news.competition}">${getCompLabel(news.competition)}</span>` : ''}
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

function getCompLabel(comp) {
    return { 'cl': 'UCL', 'el': 'UEL', 'ecl': 'UECL' }[comp] || '';
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

function hideEmptyState() {
    const container = document.getElementById('news-container');
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();
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

// === NEWS COUNTRY FILTER ===
let currentFilter = 'all';

function initFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.disabled) return;
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

// === HIGHLIGHTS FILTER ===
function initHighlightFilters() {
    document.querySelectorAll('.hl-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.hl-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            renderHighlights(this.dataset.comp);
        });
    });
}

// Close modal on Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeHighlightModal();
});
