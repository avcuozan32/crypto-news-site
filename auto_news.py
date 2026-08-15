import feedparser
import requests
from datetime import datetime, timedelta
from database import db, Article
from config import Config
from slugify import slugify
from bs4 import BeautifulSoup
import re
import hashlib


class AutoNewsCollector:
    def __init__(self):
        self.feeds = Config.NEWS_RSS_FEEDS
        self.collected_hashes = set()

    def _clean_html(self, html_content):
        """HTML'den temiz metin çıkar"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _generate_hash(self, title):
        """Başlık hash'i oluştur (tekrar kontrolü için)"""
        return hashlib.md5(title.lower().encode()).hexdigest()

    def _extract_image(self, entry):
        """RSS entry'den görsel URL'si çıkar"""
        # media:content
        if hasattr(entry, 'media_content') and entry.media_content:
            url = entry.media_content[0].get('url', '')
            if url:
                return url

        # media:thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            url = entry.media_thumbnail[0].get('url', '')
            if url:
                return url

        # enclosure
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if 'image' in enc.get('type', ''):
                    return enc.get('href', '')

        # İçerikten img çıkar
        content = entry.get('summary', '') or entry.get('description', '')
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            img = soup.find('img')
            if img and img.get('src'):
                return img['src']

        # content:encoded içinden dene
        if hasattr(entry, 'content') and entry.content:
            for c in entry.content:
                soup = BeautifulSoup(c.get('value', ''), 'html.parser')
                img = soup.find('img')
                if img and img.get('src'):
                    return img['src']

        return ''

    def _get_fallback_image(self, category, title):
        """Resim yoksa kategori bazlı varsayılan resim"""
        import random
        fallback_images = {
            'bitcoin': [
                'https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=800',
                'https://images.unsplash.com/photo-1543699565-003b8adda5fc?w=800',
                'https://images.unsplash.com/photo-1621761191319-c6fb62004040?w=800',
            ],
            'ethereum': [
                'https://images.unsplash.com/photo-1622790698141-94e30457ef12?w=800',
                'https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800',
            ],
            'defi': [
                'https://images.unsplash.com/photo-1620321023374-d1a68fbc720d?w=800',
                'https://images.unsplash.com/photo-1642104704074-907c0698cbd9?w=800',
            ],
            'nft': [
                'https://images.unsplash.com/photo-1646153742982-7b80f4b4a3d0?w=800',
                'https://images.unsplash.com/photo-1637858868799-7f26a0640eb6?w=800',
            ],
            'market': [
                'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800',
                'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800',
            ],
            'web3': [
                'https://images.unsplash.com/photo-1639322537228-f710d846310a?w=800',
                'https://images.unsplash.com/photo-1644143379190-08a5f055de1d?w=800',
            ],
            'regulation': [
                'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800',
                'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800',
            ],
            'security': [
                'https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800',
                'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800',
            ],
            'altcoins': [
                'https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=800',
                'https://images.unsplash.com/photo-1629339942248-45d4b10c8c2f?w=800',
            ],
            'exchange': [
                'https://images.unsplash.com/photo-1560221328-12fe60f83ab8?w=800',
                'https://images.unsplash.com/photo-1601597111158-2fceff292cdc?w=800',
            ],
            'news': [
                'https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800',
                'https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=800',
            ],
        }

        category_images = fallback_images.get(category, fallback_images['news'])
        return random.choice(category_images)

    def _categorize(self, title, content):
        """Haberi otomatik kategorize et"""
        text = (title + ' ' + content).lower()

        categories = {
            'defi': ['defi', 'decentralized finance', 'yield', 'liquidity', 'dex', 'swap', 'lending'],
            'nft': ['nft', 'non-fungible', 'opensea', 'digital art', 'collectible'],
            'regulation': ['sec', 'regulation', 'regulatory', 'law', 'legal', 'ban', 'compliance', 'court'],
            'bitcoin': ['bitcoin', 'btc', 'satoshi', 'halving', 'mining'],
            'ethereum': ['ethereum', 'eth', 'vitalik', 'layer 2', 'l2'],
            'altcoins': ['altcoin', 'solana', 'cardano', 'polkadot', 'avalanche', 'polygon'],
            'exchange': ['binance', 'coinbase', 'kraken', 'exchange', 'listing', 'delist'],
            'web3': ['web3', 'metaverse', 'gamefi', 'play-to-earn', 'dao'],
            'security': ['hack', 'exploit', 'vulnerability', 'scam', 'fraud', 'phishing'],
            'market': ['price', 'market', 'bull', 'bear', 'rally', 'crash', 'surge', 'dump'],
            'technology': ['blockchain', 'protocol', 'upgrade', 'fork', 'consensus'],
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category

        return 'news'

    def _extract_tags(self, title, content):
        """Otomatik etiket çıkar"""
        text = (title + ' ' + content).lower()
        possible_tags = [
            'bitcoin', 'ethereum', 'solana', 'cardano', 'ripple', 'xrp',
            'binance', 'coinbase', 'defi', 'nft', 'web3', 'metaverse',
            'sec', 'regulation', 'mining', 'staking', 'layer2', 'dao',
            'polygon', 'avalanche', 'polkadot', 'chainlink', 'dogecoin',
            'ai', 'artificial intelligence', 'etf', 'halving', 'whale',
            'hack', 'security', 'gamefi', 'airdrop', 'token', 'ico'
        ]
        tags = [tag for tag in possible_tags if tag in text]
        return tags[:10]

    def _rewrite_content(self, title, summary, source):
        """İçeriği yeniden yaz (özgünleştir)"""
        clean_summary = self._clean_html(summary)

        if len(clean_summary) < 50:
            clean_summary = title

        # Basit özgünleştirme (kendi yorumunu ekle)
        intro_templates = [
            f"In a significant development for the cryptocurrency market, {clean_summary}",
            f"The crypto community is buzzing after {clean_summary}",
            f"Breaking crypto news: {clean_summary}",
            f"In the latest development from the digital asset space, {clean_summary}",
            f"Crypto markets are reacting to the news that {clean_summary}",
        ]

        import random
        intro = random.choice(intro_templates)

        content = f"""
        <div class="article-content">
            <p class="lead">{intro}</p>

            <h2>Key Details</h2>
            <p>{clean_summary}</p>

            <h2>Market Impact</h2>
            <p>This development could have significant implications for the broader 
            cryptocurrency market. Traders and investors are closely monitoring the 
            situation for potential price movements.</p>

            <h2>What This Means for Investors</h2>
            <p>As always, investors should conduct their own research (DYOR) before 
            making any investment decisions. The cryptocurrency market remains highly 
            volatile and unpredictable.</p>

            <div class="disclaimer-box">
                <p><strong>Disclaimer:</strong> This article is for informational purposes 
                only and should not be considered as financial advice. Always do your own 
                research before making investment decisions.</p>
            </div>

            <p class="source-credit"><em>Source: {source}</em></p>
        </div>
        """

        return content.strip()

    def collect_from_rss(self, app):
        """RSS beslemelerinden haber topla"""
        with app.app_context():
            new_articles = []

            for feed_url in self.feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    source_name = feed.feed.get('title', 'Unknown Source')

                    for entry in feed.entries[:5]:  # Her kaynaktan son 5 haber
                        title = entry.get('title', '').strip()
                        if not title:
                            continue

                        # Tekrar kontrolü
                        title_hash = self._generate_hash(title)
                        if title_hash in self.collected_hashes:
                            continue

                        # Veritabanında var mı kontrol
                        slug = slugify(title)[:200]
                        existing = Article.query.filter_by(slug=slug).first()
                        if existing:
                            continue

                        # İçerik hazırla
                        summary = self._clean_html(
                            entry.get('summary', '') or entry.get('description', '')
                        )[:500]

                        content = self._rewrite_content(title, summary, source_name)
                        image_url = self._extract_image(entry)
                        if not image_url:
                            image_url = self._get_fallback_image(category, title)
                        category = self._categorize(title, summary)
                        tags = self._extract_tags(title, summary)

                        # Yayın tarihi
                        published = entry.get('published_parsed')
                        if published:
                            pub_date = datetime(*published[:6])
                        else:
                            pub_date = datetime.utcnow()

                        # SEO
                        seo_title = f"{title} | {Config.SITE_NAME}"[:200]
                        seo_desc = summary[:160] if summary else title[:160]

                        article = Article(
                            title=title,
                            slug=slug,
                            content=content,
                            summary=summary,
                            category=category,
                            source=source_name,
                            source_url=entry.get('link', ''),
                            image_url=image_url,
                            author='CryptoNest AI',
                            is_auto_generated=True,
                            is_published=True,
                            seo_title=seo_title,
                            seo_description=seo_desc,
                            created_at=pub_date,
                        )
                        article.set_tags(tags)

                        db.session.add(article)
                        self.collected_hashes.add(title_hash)
                        new_articles.append(title)

                except Exception as e:
                    print(f"RSS Error ({feed_url}): {e}")
                    continue

            db.session.commit()
            print(f"✅ {len(new_articles)} new articles collected")
            return new_articles


class PriceAlertNewsGenerator:
    """Fiyat değişimlerinden otomatik haber üret"""

    def generate_price_alert_news(self, alerts, app):
        """Büyük fiyat hareketlerinden haber üret"""
        with app.app_context():
            for alert in alerts:
                direction_word = "Surges" if alert['direction'] == 'up' else "Drops"
                direction_emoji = "🚀" if alert['direction'] == 'up' else "📉"

                title = f"{alert['coin']} ({alert['symbol']}) {direction_word} {alert['change_pct']:.1f}% – What's Behind the Move?"

                content = f"""
                <div class="article-content">
                    <div class="price-alert-banner {'bullish' if alert['direction'] == 'up' else 'bearish'}">
                        <span class="alert-emoji">{direction_emoji}</span>
                        <span class="alert-text">PRICE ALERT</span>
                    </div>

                    <p class="lead"><strong>{alert['coin']} ({alert['symbol']})</strong> has 
                    {'surged' if alert['direction'] == 'up' else 'dropped'} by 
                    <strong>{alert['change_pct']:.1f}%</strong>, moving from 
                    <strong>${alert['old_price']:,.2f}</strong> to 
                    <strong>${alert['new_price']:,.2f}</strong>.</p>

                    <h2>Price Movement Details</h2>
                    <div class="price-details">
                        <table class="price-table">
                            <tr><td>Previous Price</td><td>${alert['old_price']:,.2f}</td></tr>
                            <tr><td>Current Price</td><td>${alert['new_price']:,.2f}</td></tr>
                            <tr><td>Change</td><td>{alert['change_pct']:.1f}%</td></tr>
                            <tr><td>Direction</td><td>{'📈 Bullish' if alert['direction'] == 'up' else '📉 Bearish'}</td></tr>
                        </table>
                    </div>

                    <h2>Market Analysis</h2>
                    <p>The {'upward' if alert['direction'] == 'up' else 'downward'} movement in 
                    {alert['coin']} price could be attributed to several factors including market 
                    sentiment, trading volume changes, and broader cryptocurrency market trends.</p>

                    <h2>What Traders Should Watch</h2>
                    <ul>
                        <li>Key support and resistance levels</li>
                        <li>Trading volume trends</li>
                        <li>Overall market sentiment</li>
                        <li>Upcoming events or announcements</li>
                    </ul>

                    <div class="disclaimer-box">
                        <p><strong>Disclaimer:</strong> This is not financial advice. 
                        Always DYOR before making investment decisions.</p>
                    </div>
                </div>
                """

                summary = f"{alert['coin']} ({alert['symbol']}) {'surges' if alert['direction'] == 'up' else 'drops'} {alert['change_pct']:.1f}% from ${alert['old_price']:,.2f} to ${alert['new_price']:,.2f}."

                article = Article(
                    title=title,
                    slug=slugify(title)[:200],
                    content=content,
                    summary=summary,
                    category='market',
                    author='CryptoNest Price Bot',
                    is_auto_generated=True,
                    is_published=True,
                    is_breaking=True,
                )
                article.set_tags([alert['symbol'].lower(), 'price-alert', 'market'])

                db.session.add(article)

            db.session.commit()


class MarketSummaryGenerator:
    """Günlük piyasa özeti üret"""

    def generate_daily_summary(self, coins_data, global_data, app):
        """Günlük piyasa özet haberi üret"""
        with app.app_context():
            today = datetime.utcnow().strftime('%B %d, %Y')

            # En çok yükselen ve düşen
            sorted_coins = sorted(coins_data, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)
            top_gainers = sorted_coins[:3]
            top_losers = sorted_coins[-3:]

            title = f"Crypto Market Daily Recap – {today}"

            gainers_html = ""
            for coin in top_gainers:
                change = coin.get('price_change_percentage_24h', 0)
                gainers_html += f"<li><strong>{coin['name']} ({coin['symbol'].upper()})</strong>: ${coin['current_price']:,.2f} ({'+' if change > 0 else ''}{change:.1f}%)</li>"

            losers_html = ""
            for coin in top_losers:
                change = coin.get('price_change_percentage_24h', 0)
                losers_html += f"<li><strong>{coin['name']} ({coin['symbol'].upper()})</strong>: ${coin['current_price']:,.2f} ({change:.1f}%)</li>"

            total_mcap = global_data.get('total_market_cap', 0)
            btc_dom = global_data.get('btc_dominance', 0)

            content = f"""
            <div class="article-content">
                <p class="lead">Here's your daily cryptocurrency market recap for {today}. 
                The total crypto market cap stands at approximately 
                <strong>${total_mcap/1e12:.2f} trillion</strong> with Bitcoin dominance at 
                <strong>{btc_dom:.1f}%</strong>.</p>

                <h2>🟢 Top Gainers (24h)</h2>
                <ul>{gainers_html}</ul>

                <h2>🔴 Top Losers (24h)</h2>
                <ul>{losers_html}</ul>

                <h2>📊 Market Overview</h2>
                <p>The cryptocurrency market has shown {'bullish' if global_data.get('market_cap_change_24h', 0) > 0 else 'bearish'} 
                sentiment over the last 24 hours.</p>

                <h2>🔍 Key Metrics</h2>
                <table class="market-table">
                    <tr><td>Total Market Cap</td><td>${total_mcap/1e12:.2f}T</td></tr>
                    <tr><td>BTC Dominance</td><td>{btc_dom:.1f}%</td></tr>
                    <tr><td>24h Market Change</td><td>{global_data.get('market_cap_change_24h', 0):.2f}%</td></tr>
                </table>

                <div class="disclaimer-box">
                    <p><strong>Disclaimer:</strong> This market recap is for informational 
                    purposes only and does not constitute financial advice.</p>
                </div>
            </div>
            """

            slug = slugify(title)[:200]
            existing = Article.query.filter_by(slug=slug).first()
            if not existing:
                article = Article(
                    title=title,
                    slug=slug,
                    content=content,
                    summary=f"Daily crypto market recap for {today}. Total market cap: ${total_mcap/1e12:.2f}T. BTC dominance: {btc_dom:.1f}%.",
                    category='market',
                    author='CryptoNest Market Bot',
                    is_auto_generated=True,
                    is_published=True,
                    is_featured=True,
                )
                article.set_tags(['market-recap', 'daily-summary', 'bitcoin', 'ethereum'])
                db.session.add(article)
                db.session.commit()
                return True
            return False
