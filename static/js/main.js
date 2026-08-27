// Sport News GR - Main JavaScript

let allNews = [];
let displayedCount = 0;
const ITEMS_PER_PAGE = 10;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadNewsData();
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
    
    const end = Math.min(displayedCount + ITEMS_PER_PAGE, allNews.length);
    
    for (let i = displayedCount; i < end; i++) {
        const news = allNews[i];
        const card = createNewsCard(news);
        container.appendChild(card);
    }
    
    displayedCount = end;
    
    // Show/hide load more button
    if (displayedCount < allNews.length) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }
}

// Create a news card element
function createNewsCard(news) {
    const article = document.createElement('article');
    article.className = 'news-card';
    article.dataset.id = news.id;
    
    const sourceClass = getSourceClass(news.source);
    
    article.innerHTML = `
        <div class="card-header">
            <span class="source-badge source-${sourceClass}">${escapeHtml(news.source)}</span>
            <span class="post-time">${escapeHtml(news.time_display)}</span>
        </div>
        <div class="card-body">
            <h2 class="card-title">${escapeHtml(news.title)}</h2>
            <div class="card-content" style="display: none;">
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

// Toggle card expansion
function toggleCard(button) {
    const card = button.closest('.news-card');
    const content = card.querySelector('.card-content');
    const icon = button.querySelector('.expand-icon');
    const text = button.querySelector('.expand-text');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        button.classList.add('active');
        text.textContent = 'Κλείστε';
    } else {
        content.style.display = 'none';
        button.classList.remove('active');
        text.textContent = 'Διαβάστε περισσότερα';
    }
}

// Get source CSS class
function getSourceClass(source) {
    const sourceMap = {
        'BBC Sport': 'bbc',
        'Sky Sports': 'sky',
        'ESPN': 'espn',
        'The Guardian': 'guardian',
        'Sport24': 'sport24',
        'Gazzetta.gr': 'gazzetta',
        'Sportime': 'sportime',
        'Novasports': 'novasports',
        'Football Italia': 'football-italia',
        'Gazzetta dello Sport': 'gazzetta-it',
        'Sky Sport Italia': 'sky-it',
        "L'Equipe": 'lequipe',
        'Kicker': 'kicker',
        'Marca': 'marca',
        'ESPN Deportes': 'espn'
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

// Show/hide loading spinner
function showLoading(show) {
    const loader = document.getElementById('loading');
    loader.style.display = show ? 'block' : 'none';
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
