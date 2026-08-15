// ========== TICKER BAR ==========
async function loadTicker() {
    try {
        const response = await fetch('/api/ticker');
        const data = await response.json();

        const tickerContent = document.getElementById('tickerContent');
        if (!tickerContent || !data.length) return;

        let html = '';
        // Duplike et (sonsuz scroll efekti)
        for (let i = 0; i < 2; i++) {
            data.forEach(coin => {
                const changeClass = coin.change >= 0 ? 'positive' : 'negative';
                const changeSign = coin.change >= 0 ? '+' : '';
                html += `
                    <span class="ticker-item">
                        <img src="${coin.image}" alt="${coin.symbol}" width="16" height="16">
                        <strong>${coin.symbol}</strong>
                        $${coin.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                        <span class="${changeClass}">${changeSign}${coin.change.toFixed(1)}%</span>
                    </span>
                `;
            });
        }

        tickerContent.innerHTML = html;
    } catch (error) {
        console.error('Ticker error:', error);
    }
}

// ========== MOBILE MENU ==========
document.addEventListener('DOMContentLoaded', function() {
    const menuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');

    if (menuBtn && navLinks) {
        menuBtn.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            const icon = menuBtn.querySelector('i');
            if (navLinks.classList.contains('active')) {
                icon.className = 'fas fa-times';
            } else {
                icon.className = 'fas fa-bars';
            }
        });
    }
});

// ========== AUTO REFRESH TICKER ==========
loadTicker();
setInterval(loadTicker, 60000); // Her 1 dakikada güncelle

// ========== LAZY LOADING IMAGES ==========
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img[loading="lazy"]');
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    observer.unobserve(img);
                }
            });
        });
        images.forEach(img => observer.observe(img));
    }
});

// ========== COOKIE CONSENT ==========
function showCookieConsent() {
    if (localStorage.getItem('cookieConsent')) return;

    const banner = document.createElement('div');
    banner.style.cssText = `
        position: fixed; bottom: 0; left: 0; right: 0; z-index: 9999;
        background: #1e293b; color: white; padding: 15px 20px;
        display: flex; justify-content: space-between; align-items: center;
        font-size: 14px; gap: 15px;
    `;
    banner.innerHTML = `
        <p>We use cookies to improve your experience and serve relevant ads.
        <a href="/privacy" style="color: #818cf8;">Learn more</a></p>
        <button onclick="acceptCookies()" style="
            background: #6366f1; color: white; border: none; padding: 10px 24px;
            border-radius: 8px; cursor: pointer; font-weight: 600; white-space: nowrap;
        ">Accept</button>
    `;
    document.body.appendChild(banner);
}

function acceptCookies() {
    localStorage.setItem('cookieConsent', 'true');
    const banner = document.querySelector('[style*="position: fixed; bottom: 0"]');
    if (banner) banner.remove();
}

document.addEventListener('DOMContentLoaded', showCookieConsent);

// ========== VIEW COUNTER ==========
// Sayfa görüntülenme sayısı article sayfasında otomatik artıyor (backend'de)

// ========== PRICE TABLE SORTING ==========
function sortTable(columnIndex) {
    const table = document.querySelector('.price-table-full');
    if (!table) return;

    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        let aVal = a.cells[columnIndex].textContent.trim();
        let bVal = b.cells[columnIndex].textContent.trim();

        // Sayısal değerleri temizle
        aVal = parseFloat(aVal.replace(/[$,%,T,B,M,K,+]/g, '')) || 0;
        bVal = parseFloat(bVal.replace(/[$,%,T,B,M,K,+]/g, '')) || 0;

        return bVal - aVal;
    });

    rows.forEach(row => tbody.appendChild(row));
}