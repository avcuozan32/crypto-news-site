// ========== MARKET PAGE JAVASCRIPT ==========

class MarketTracker {
    constructor() {
        this.refreshInterval = 30000; // 30 saniye
        this.sortColumn = 'rank';
        this.sortDirection = 'asc';
        this.searchQuery = '';
        this.init();
    }

    init() {
        this.setupSearch();
        this.setupSorting();
        this.setupAutoRefresh();
        this.setupCurrencyToggle();
        this.loadFearGreedIndex();
        console.log('✅ MarketTracker initialized');
    }

    // ==================== VERİ GÜNCELLEME ====================

    async refreshPrices() {
        try {
            const response = await fetch('/api/prices');
            const coins = await response.json();

            if (!coins || !coins.length) return;

            coins.forEach(coin => {
                this.updateCoinRow(coin);
            });

            this.updateRefreshTime();
        } catch (error) {
            console.error('Price refresh error:', error);
        }
    }

    updateCoinRow(coin) {
        const rows = document.querySelectorAll(
            `.price-table-full tbody tr`
        );

        rows.forEach(row => {
            const nameCell = row.querySelector('.coin-cell strong');
            if (nameCell && nameCell.textContent === coin.name) {
                // Fiyat güncelle
                const priceCell = row.cells[2];
                const oldPrice = parseFloat(
                    priceCell.textContent.replace(/[$,]/g, '')
                );
                const newPrice = coin.current_price;

                if (priceCell) {
                    priceCell.innerHTML = `<strong>$${this.formatPrice(newPrice)}</strong>`;

                    // Renk animasyonu
                    if (newPrice > oldPrice) {
                        this.flashCell(priceCell, 'flash-green');
                    } else if (newPrice < oldPrice) {
                        this.flashCell(priceCell, 'flash-red');
                    }
                }

                // 24h değişim güncelle
                const changeCell = row.cells[3];
                if (changeCell) {
                    const change = coin.price_change_percentage_24h || 0;
                    changeCell.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
                    changeCell.className = change >= 0 ? 'positive' : 'negative';
                }

                // Market cap güncelle
                const mcapCell = row.cells[4];
                if (mcapCell) {
                    mcapCell.textContent = this.formatLargeNumber(coin.market_cap);
                }
            }
        });
    }

    // ==================== ARAMA ====================

    setupSearch() {
        const searchInput = document.getElementById('marketSearch');
        if (!searchInput) return;

        searchInput.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase();
            this.filterTable();
        });
    }

    filterTable() {
        const rows = document.querySelectorAll('.price-table-full tbody tr');

        rows.forEach(row => {
            const nameCell = row.querySelector('.coin-cell strong');
            const symbolCell = row.querySelector('.coin-symbol');

            if (!nameCell) return;

            const name = nameCell.textContent.toLowerCase();
            const symbol = symbolCell ? symbolCell.textContent.toLowerCase() : '';

            if (name.includes(this.searchQuery) || symbol.includes(this.searchQuery)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // ==================== SIRALAMA ====================

    setupSorting() {
        const headers = document.querySelectorAll('.price-table-full th[data-sort]');

        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                const column = header.dataset.sort;

                if (this.sortColumn === column) {
                    this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    this.sortColumn = column;
                    this.sortDirection = 'asc';
                }

                this.sortTable(column, this.sortDirection);
                this.updateSortIndicators(header, this.sortDirection);
            });
        });
    }

    sortTable(column, direction) {
        const table = document.querySelector('.price-table-full');
        if (!table) return;

        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        const columnMap = {
            'rank': 0,
            'price': 2,
            'change24h': 3,
            'marketcap': 4,
            'volume': 5,
        };

        const colIndex = columnMap[column] || 0;

        rows.sort((a, b) => {
            let aVal = a.cells[colIndex]?.textContent.trim() || '0';
            let bVal = b.cells[colIndex]?.textContent.trim() || '0';

            // Sayısal temizlik
            aVal = parseFloat(aVal.replace(/[^0-9.-]/g, '')) || 0;
            bVal = parseFloat(bVal.replace(/[^0-9.-]/g, '')) || 0;

            return direction === 'asc' ? aVal - bVal : bVal - aVal;
        });

        rows.forEach(row => tbody.appendChild(row));
    }

    updateSortIndicators(activeHeader, direction) {
        document.querySelectorAll('.price-table-full th[data-sort]').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        activeHeader.classList.add(`sort-${direction}`);
    }

    // ==================== OTO YENILEME ====================

    setupAutoRefresh() {
        setInterval(() => {
            this.refreshPrices();
        }, this.refreshInterval);

        // Sayaç göster
        this.startRefreshCountdown();
    }

    startRefreshCountdown() {
        const countdownEl = document.getElementById('refreshCountdown');
        if (!countdownEl) return;

        let seconds = this.refreshInterval / 1000;

        const timer = setInterval(() => {
            seconds--;
            countdownEl.textContent = `${seconds}s`;

            if (seconds <= 0) {
                seconds = this.refreshInterval / 1000;
                countdownEl.textContent = 'Updating...';
            }
        }, 1000);
    }

    updateRefreshTime() {
        const lastUpdateEl = document.getElementById('lastUpdate');
        if (lastUpdateEl) {
            const now = new Date();
            lastUpdateEl.textContent = now.toLocaleTimeString() + ' UTC';
        }
    }

    // ==================== DÖVİZ TOGGLE ====================

    setupCurrencyToggle() {
        const toggleBtns = document.querySelectorAll('.currency-toggle');
        let currentCurrency = 'USD';

        toggleBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                currentCurrency = btn.dataset.currency;
                toggleBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                // BTC bazında gösterim için ekstra API çağrısı yapılabilir
            });
        });
    }

    // ==================== FEAR & GREED INDEX ====================

    async loadFearGreedIndex() {
        try {
            const response = await fetch(
                'https://api.alternative.me/fng/?limit=1'
            );
            const data = await response.json();

            if (data && data.data && data.data[0]) {
                const fgi = data.data[0];
                this.displayFearGreedIndex(
                    parseInt(fgi.value),
                    fgi.value_classification
                );
            }
        } catch (error) {
            console.log('Fear & Greed API not available');
        }
    }

    displayFearGreedIndex(value, classification) {
        const container = document.getElementById('fearGreedIndex');
        if (!container) return;

        let color;
        if (value <= 25) color = '#ef4444';
        else if (value <= 45) color = '#f97316';
        else if (value <= 55) color = '#eab308';
        else if (value <= 75) color = '#84cc16';
        else color = '#22c55e';

        container.innerHTML = `
            <div class="fgi-widget">
                <div class="fgi-circle" style="border-color: ${color}">
                    <span class="fgi-number" style="color: ${color}">${value}</span>
                </div>
                <div class="fgi-info">
                    <div class="fgi-label">Fear & Greed Index</div>
                    <div class="fgi-classification" style="color: ${color}">
                        ${classification}
                    </div>
                </div>
            </div>
        `;
    }

    // ==================== YARDIMCI FONKSİYONLAR ====================

    formatPrice(price) {
        if (!price) return '0.00';
        if (price >= 1000) {
            return price.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        } else if (price >= 1) {
            return price.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 4
            });
        } else {
            return price.toFixed(8);
        }
    }

    formatLargeNumber(num) {
        if (!num) return '$0';
        if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
        if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
        if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
        return `$${num.toLocaleString()}`;
    }

    flashCell(cell, className) {
        cell.classList.add(className);
        setTimeout(() => cell.classList.remove(className), 1000);
    }

    formatPercentage(value) {
        if (!value) return '0.00%';
        const sign = value >= 0 ? '+' : '';
        return `${sign}${value.toFixed(2)}%`;
    }
}

// ==================== PORTFOLIO TRACKER (BASIT) ====================

class PortfolioTracker {
    constructor() {
        this.portfolio = JSON.parse(
            localStorage.getItem('cryptoPortfolio') || '{}'
        );
    }

    addCoin(symbol, amount, buyPrice) {
        this.portfolio[symbol] = {
            amount: parseFloat(amount),
            buyPrice: parseFloat(buyPrice),
            addedAt: new Date().toISOString()
        };
        this.save();
    }

    removeCoin(symbol) {
        delete this.portfolio[symbol];
        this.save();
    }

    calculatePnL(symbol, currentPrice) {
        const holding = this.portfolio[symbol];
        if (!holding) return null;

        const totalCost = holding.amount * holding.buyPrice;
        const currentValue = holding.amount * currentPrice;
        const pnl = currentValue - totalCost;
        const pnlPercent = ((currentValue - totalCost) / totalCost) * 100;

        return { totalCost, currentValue, pnl, pnlPercent };
    }

    save() {
        localStorage.setItem('cryptoPortfolio', JSON.stringify(this.portfolio));
    }
}

// ==================== INIT ====================

document.addEventListener('DOMContentLoaded', () => {
    window.marketTracker = new MarketTracker();
    window.portfolioTracker = new PortfolioTracker();
});

// ========== MARKET PAGE CSS (market.js'ye eklenen stiller) ==========
const marketStyles = `
    .flash-green {
        animation: flash-green 1s ease;
    }
    .flash-red {
        animation: flash-red 1s ease;
    }
    @keyframes flash-green {
        0% { background-color: transparent; }
        50% { background-color: rgba(16, 185, 129, 0.3); }
        100% { background-color: transparent; }
    }
    @keyframes flash-red {
        0% { background-color: transparent; }
        50% { background-color: rgba(239, 68, 68, 0.3); }
        100% { background-color: transparent; }
    }
    .sort-asc::after { content: ' ▲'; font-size: 10px; }
    .sort-desc::after { content: ' ▼'; font-size: 10px; }
    .fgi-widget {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 15px;
    }
    .fgi-circle {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        border: 4px solid;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .fgi-number {
        font-size: 22px;
        font-weight: 800;
    }
    .fgi-label {
        font-size: 12px;
        color: #64748b;
    }
    .fgi-classification {
        font-size: 16px;
        font-weight: 700;
    }
    .market-search-bar {
        margin-bottom: 20px;
    }
    .market-search-input {
        width: 100%;
        padding: 12px 20px;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        font-size: 15px;
        outline: none;
    }
    .market-search-input:focus {
        border-color: #6366f1;
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = marketStyles;
document.head.appendChild(styleSheet);