// ========== CRYPTO CHARTS SISTEMI ==========
// Lightweight Charts (TradingView açık kaynak) kullanır
// CDN: https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js

class CryptoCharts {
    constructor() {
        this.charts = {};
        this.apiBase = 'https://api.coingecko.com/api/v3';
        this.defaultColor = '#6366f1';
        this.init();
    }

    init() {
        // Otomatik chart container'larını bul ve yükle
        document.querySelectorAll('[data-chart]').forEach(container => {
            const coinId = container.dataset.chart;
            const days = parseInt(container.dataset.days) || 7;
            this.loadChart(container, coinId, days);
        });

        // Mini sparkline grafikleri
        document.querySelectorAll('[data-sparkline]').forEach(container => {
            const coinId = container.dataset.sparkline;
            this.loadSparkline(container, coinId);
        });
    }

    // ==================== ANA GRAFİK ====================

    async loadChart(container, coinId, days = 7) {
        try {
            const data = await this.fetchPriceHistory(coinId, days);
            if (!data || !data.prices) return;

            this.renderLineChart(container, data.prices, coinId);
        } catch (error) {
            console.error(`Chart error for ${coinId}:`, error);
            container.innerHTML = '<p style="color:#64748b;text-align:center;padding:20px">Chart unavailable</p>';
        }
    }

    async fetchPriceHistory(coinId, days) {
        const cacheKey = `chart_${coinId}_${days}`;
        const cached = this.getFromCache(cacheKey);
        if (cached) return cached;

        const url = `${this.apiBase}/coins/${coinId}/market_chart`;
        const params = new URLSearchParams({
            vs_currency: 'usd',
            days: days,
            interval: days <= 1 ? 'minute' : days <= 7 ? 'hourly' : 'daily'
        });

        const response = await fetch(`${url}?${params}`);
        const data = await response.json();

        this.setToCache(cacheKey, data, 300); // 5 dakika cache
        return data;
    }

    renderLineChart(container, prices, coinId) {
        // Canvas oluştur
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        const width = container.offsetWidth;
        const height = container.offsetHeight || 300;

        canvas.width = width;
        canvas.height = height;

        if (!prices || prices.length === 0) return;

        const values = prices.map(p => p[1]);
        const timestamps = prices.map(p => new Date(p[0]));
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);
        const range = maxVal - minVal;

        const isPositive = values[values.length - 1] >= values[0];
        const lineColor = isPositive ? '#10b981' : '#ef4444';
        const fillColor = isPositive ?
            'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';

        const padding = 40;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;

        // Arka plan
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);

        // Grid çizgileri
        ctx.strokeStyle = '#f1f5f9';
        ctx.lineWidth = 1;

        for (let i = 0; i <= 5; i++) {
            const y = padding + (chartHeight / 5) * i;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();

            // Y ekseni etiketleri
            const value = maxVal - (range / 5) * i;
            ctx.fillStyle = '#94a3b8';
            ctx.font = '10px Inter, sans-serif';
            ctx.textAlign = 'right';
            ctx.fillText(
                this.formatPrice(value),
                padding - 5,
                y + 4
            );
        }

        // Çizgi ve fill
        ctx.beginPath();
        prices.forEach((point, index) => {
            const x = padding + (index / (prices.length - 1)) * chartWidth;
            const y = padding + ((maxVal - point[1]) / range) * chartHeight;

            if (index === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });

        // Fill area
        ctx.lineTo(width - padding, padding + chartHeight);
        ctx.lineTo(padding, padding + chartHeight);
        ctx.closePath();
        ctx.fillStyle = fillColor;
        ctx.fill();

        // Ana çizgi
        ctx.beginPath();
        prices.forEach((point, index) => {
            const x = padding + (index / (prices.length - 1)) * chartWidth;
            const y = padding + ((maxVal - point[1]) / range) * chartHeight;

            if (index === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });

        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.stroke();

        // Son nokta
        const lastX = width - padding;
        const lastY = padding + ((maxVal - values[values.length - 1]) / range) * chartHeight;

        ctx.beginPath();
        ctx.arc(lastX, lastY, 5, 0, Math.PI * 2);
        ctx.fillStyle = lineColor;
        ctx.fill();

        // Hover etkileşimi
        this.addHoverEffect(canvas, prices, padding, chartWidth, chartHeight, maxVal, range, lineColor);
    }

    addHoverEffect(canvas, prices, padding, chartWidth, chartHeight, maxVal, range) {
        const tooltip = document.createElement('div');
        tooltip.style.cssText = `
            position: absolute;
            background: #1e293b;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 100;
        `;
        canvas.parentElement.style.position = 'relative';
        canvas.parentElement.appendChild(tooltip);

        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;

            const index = Math.round(
                ((mouseX - padding) / chartWidth) * (prices.length - 1)
            );

            if (index >= 0 && index < prices.length) {
                const price = prices[index];
                const date = new Date(price[0]);
                const value = price[1];

                tooltip.style.opacity = '1';
                tooltip.style.left = `${mouseX + 10}px`;
                tooltip.style.top = `${e.clientY - rect.top - 40}px`;
                tooltip.innerHTML = `
                    <div>${date.toLocaleDateString()}</div>
                    <div><strong>$${this.formatPrice(value)}</strong></div>
                `;
            }
        });

        canvas.addEventListener('mouseleave', () => {
            tooltip.style.opacity = '0';
        });
    }

    // ==================== SPARKLİNE GRAFİK ====================

    async loadSparkline(container, coinId) {
        try {
            const data = await this.fetchPriceHistory(coinId, 7);
            if (!data || !data.prices) return;

            this.renderSparkline(container, data.prices);
        } catch (error) {
            console.error(`Sparkline error:`, error);
        }
    }

    renderSparkline(container, prices) {
        const canvas = document.createElement('canvas');
        const width = 100;
        const height = 40;

        canvas.width = width;
        canvas.height = height;
        canvas.style.display = 'block';

        const ctx = canvas.getContext('2d');
        const values = prices.map(p => p[1]);
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);
        const range = maxVal - minVal || 1;

        const isPositive = values[values.length - 1] >= values[0];
        const color = isPositive ? '#10b981' : '#ef4444';

        ctx.beginPath();
        prices.forEach((point, index) => {
            const x = (index / (prices.length - 1)) * width;
            const y = height - ((point[1] - minVal) / range) * height;

            if (index === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });

        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.lineJoin = 'round';
        ctx.stroke();

        container.innerHTML = '';
        container.appendChild(canvas);
    }

    // ==================== VOLUME CHART ====================

    renderVolumeChart(container, volumes) {
        const canvas = document.createElement('canvas');
        const width = container.offsetWidth;
        const height = 80;

        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        const maxVol = Math.max(...volumes.map(v => v[1]));
        const barWidth = width / volumes.length;

        volumes.forEach((vol, index) => {
            const barHeight = (vol[1] / maxVol) * height;
            const x = index * barWidth;
            const y = height - barHeight;

            ctx.fillStyle = 'rgba(99, 102, 241, 0.6)';
            ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        });

        container.appendChild(canvas);
    }

    // ==================== MARKET CAP DOUGHNUT ====================

    renderDominanceChart(container, dominanceData) {
        const canvas = document.createElement('canvas');
        const size = 200;
        canvas.width = size;
        canvas.height = size;

        const ctx = canvas.getContext('2d');
        const centerX = size / 2;
        const centerY = size / 2;
        const radius = 80;

        const colors = [
            '#f7931a', // BTC
            '#627eea', // ETH
            '#00d395', // BNB
            '#9945ff', // SOL
            '#6366f1', // Others
        ];

        let startAngle = -Math.PI / 2;
        const total = Object.values(dominanceData).reduce((a, b) => a + b, 0);

        Object.entries(dominanceData).forEach(([coin, percentage], index) => {
            const sliceAngle = (percentage / total) * 2 * Math.PI;

            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
            ctx.closePath();
            ctx.fillStyle = colors[index % colors.length];
            ctx.fill();

            // Beyaz çizgi (ayırıcı)
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.stroke();

            startAngle += sliceAngle;
        });

        // Ortada beyaz daire (doughnut efekti)
        ctx.beginPath();
        ctx.arc(centerX, centerY, 50, 0, 2 * Math.PI);
        ctx.fillStyle = '#ffffff';
        ctx.fill();

        // Ortada metin
        ctx.fillStyle = '#0f172a';
        ctx.font = 'bold 14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('Market', centerX, centerY - 5);
        ctx.fillText('Share', centerX, centerY + 15);

        container.appendChild(canvas);
    }

    // ==================== CACHE SİSTEMİ ====================

    getFromCache(key) {
        try {
            const item = sessionStorage.getItem(key);
            if (!item) return null;

            const parsed = JSON.parse(item);
            if (Date.now() > parsed.expiry) {
                sessionStorage.removeItem(key);
                return null;
            }
            return parsed.data;
        } catch {
            return null;
        }
    }

    setToCache(key, data, seconds) {
        try {
            sessionStorage.setItem(key, JSON.stringify({
                data,
                expiry: Date.now() + seconds * 1000
            }));
        } catch {
            // Session storage dolu olabilir
        }
    }

    // ==================== YARDIMCI ====================

    formatPrice(price) {
        if (price >= 1000) return '$' + price.toLocaleString('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
        if (price >= 1) return '$' + price.toFixed(2);
        if (price >= 0.01) return '$' + price.toFixed(4);
        return '$' + price.toFixed(8);
    }

    // ==================== YARDIMCI: PERIOD SEÇİCİ ====================

    static addPeriodSelector(container, coinId, chartInstance) {
        const periods = [
            { label: '1D', days: 1 },
            { label: '7D', days: 7 },
            { label: '30D', days: 30 },
            { label: '90D', days: 90 },
            { label: '1Y', days: 365 },
        ];

        const selector = document.createElement('div');
        selector.className = 'chart-period-selector';
        selector.style.cssText = `
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        `;

        periods.forEach(period => {
            const btn = document.createElement('button');
            btn.textContent = period.label;
            btn.style.cssText = `
                padding: 5px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background: transparent;
                cursor: pointer;
                font-size: 12px;
                font-weight: 600;
                transition: all 0.2s;
            `;

            if (period.days === 7) {
                btn.style.background = '#6366f1';
                btn.style.color = 'white';
                btn.style.borderColor = '#6366f1';
            }

            btn.addEventListener('click', () => {
                selector.querySelectorAll('button').forEach(b => {
                    b.style.background = 'transparent';
                    b.style.color = '#0f172a';
                    b.style.borderColor = '#e2e8f0';
                });
                btn.style.background = '#6366f1';
                btn.style.color = 'white';

                container.innerHTML = '';
                container.appendChild(selector);
                chartInstance.loadChart(container, coinId, period.days);
            });

            selector.appendChild(btn);
        });

        container.insertBefore(selector, container.firstChild);
    }
}

// ==================== INIT ====================

document.addEventListener('DOMContentLoaded', () => {
    window.cryptoCharts = new CryptoCharts();
});