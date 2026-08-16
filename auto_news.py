import feedparser
import hashlib
import random
import re
from datetime import datetime
from bs4 import BeautifulSoup
from slugify import slugify

from database import db, Article
from config import Config
from image_helper import ImageHelper


class AutoNewsCollector:
    """RSS beslemelerinden otomatik haber toplayıcı"""

    def __init__(self):
        self.feeds = Config.NEWS_RSS_FEEDS
        self.collected_hashes = set()

    # ==================== YARDIMCILAR ====================

    @staticmethod
    def _clean_html(html_content):
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def _generate_hash(title):
        return hashlib.md5(title.lower().encode()).hexdigest()

    @staticmethod
    def _is_valid_image(url):
        """Logo/ikon/placeholder görselleri ele"""
        if not url or not url.startswith('http'):
            return False
        bad = ['logo', 'icon', 'avatar', 'sprite', 'placeholder',
               'blank', 'pixel', '1x1', 'spacer', 'default-']
        low = url.lower()
        if any(b in low for b in bad):
            return False
        if low.endswith('.svg'):
            return False
        return True

    def _extract_image(self, entry):
        """RSS entry'den görsel URL'si çıkar"""
        # media:content
        try:
            if hasattr(entry, 'media_content') and entry.media_content:
                for m in entry.media_content:
                    u = m.get('url', '')
                    if self._is_valid_image(u):
                        return u
        except Exception:
            pass

        # media:thumbnail
        try:
            if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                for m in entry.media_thumbnail:
                    u = m.get('url', '')
                    if self._is_valid_image(u):
                        return u
        except Exception:
            pass

        # enclosure
        try:
            if hasattr(entry, 'enclosures') and entry.enclosures:
                for enc in entry.enclosures:
                    if 'image' in (enc.get('type') or ''):
                        u = enc.get('href', '')
                        if self._is_valid_image(u):
                            return u
        except Exception:
            pass

        # content:encoded veya summary içindeki <img>
        for field in ('content', 'summary', 'description'):
            try:
                raw = getattr(entry, field, None)
                if isinstance(raw, list) and raw:
                    raw = raw[0].get('value', '')
                if not raw:
                    continue
                soup = BeautifulSoup(raw, 'html.parser')
                for img in soup.find_all('img'):
                    u = img.get('src') or img.get('data-src') or ''
                    if self._is_valid_image(u):
                        return u
            except Exception:
                continue

        return ''

    @staticmethod
    def _categorize(title, content):
        text = (title + ' ' + content).lower()
        categories = {
            'security':   ['hack', 'exploit', 'vulnerabil', 'scam', 'fraud', 'phishing', 'stolen', 'breach'],
            'regulation': ['sec ', 'regulat', 'lawsuit', 'court', 'ban ', 'compliance', 'legislation', 'senate'],
            'defi':       ['defi', 'decentralized finance', 'yield', 'liquidity', 'dex', 'lending', 'tvl'],
            'nft':        ['nft', 'non-fungible', 'opensea', 'collectible', 'digital art'],
            'web3':       ['web3', 'metaverse', 'gamefi', 'play-to-earn', 'dao ', 'airdrop'],
            'exchange':   ['binance', 'coinbase', 'kraken', 'listing', 'delist', 'exchange'],
            'bitcoin':    ['bitcoin', 'btc', 'satoshi', 'halving', 'mining', 'miner'],
            'ethereum':   ['ethereum', ' eth ', 'vitalik', 'layer 2', 'l2 ', 'staking'],
            'altcoins':   ['altcoin', 'solana', 'cardano', 'polkadot', 'avalanche', 'polygon', 'xrp', 'dogecoin'],
            'market':     ['price', 'market', 'bull', 'bear', 'rally', 'crash', 'surge', 'dump', 'etf'],
            'technology': ['blockchain', 'protocol', 'upgrade', 'fork', 'consensus', 'zk-'],
        }
        for cat, keys in categories.items():
            if any(k in text for k in keys):
                return cat
        return 'news'

    @staticmethod
    def _extract_tags(title, content):
        text = (title + ' ' + content).lower()
        possible = [
            'bitcoin', 'ethereum', 'solana', 'cardano', 'ripple', 'xrp',
            'binance', 'coinbase', 'defi', 'nft', 'web3', 'metaverse',
            'sec', 'regulation', 'mining', 'staking', 'layer2', 'dao',
            'polygon', 'avalanche', 'polkadot', 'chainlink', 'dogecoin',
            'etf', 'halving', 'whale', 'hack', 'security', 'airdrop', 'token',
        ]
        return [t for t in possible if t in text][:10]

    @staticmethod
    def _rewrite_content(title, summary, source, source_url):
        clean = AutoNewsCollector._clean_html(summary)
        if len(clean) < 40:
            clean = title

        intros = [
            f"In a significant development for the cryptocurrency market, {clean}",
            f"The crypto community is closely watching as {clean}",
            f"Breaking crypto news: {clean}",
            f"In the latest development from the digital asset space, {clean}",
            f"Crypto markets are reacting to reports that {clean}",
        ]
        intro = random.choice(intros)

        return f"""
<div class="article-content">
    <p class="lead">{intro}</p>

    <h2>Key Details</h2>
    <p>{clean}</p>

    <h2>Market Impact</h2>
    <p>This development could carry implications for the broader cryptocurrency
    market. Traders and investors are monitoring the situation for potential
    volatility and price movements across major digital assets.</p>

    <h2>What This Means for Investors</h2>
    <p>As always, market participants should conduct their own research (DYOR)
    before making any investment decisions. The cryptocurrency market remains
    highly volatile and sensitive to news events, regulatory shifts, and
    macroeconomic conditions.</p>

    <div class="disclaimer-box">
        <p><strong>Disclaimer:</strong> This article is for informational purposes
        only and should not be considered financial advice. Always do your own
        research before making investment decisions.</p>
    </div>

    <p class="source-credit"><em>Source: <a href="{source_url}" target="_blank"
    rel="noopener nofollow">{source}</a></em></p>
</div>
""".strip()

    # ==================== ANA TOPLAYICI ====================

    def collect_from_rss(self, app):
        with app.app_context():
            new_titles = []

            for feed_url in self.feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    source_name = feed.feed.get('title', 'Crypto Source')

                    for entry in feed.entries[:6]:
                        title = (entry.get('title') or '').strip()
                        if not title or len(title) < 15:
                            continue

                        h = self._generate_hash(title)
                        if h in self.collected_hashes:
                            continue

                        slug = slugify(title)[:200]
                        if Article.query.filter_by(slug=slug).first():
                            self.collected_hashes.add(h)
                            continue

                        raw_summary = entry.get('summary', '') or entry.get('description', '')
                        summary = self._clean_html(raw_summary)[:500]
                        source_url = entry.get('link', '')

                        category = self._categorize(title, summary)
                        tags = self._extract_tags(title, summary)
                        content = self._rewrite_content(
                            title, raw_summary, source_name, source_url)

                        # --- GÖRSEL ÇÖZÜMLEME (3 katmanlı) ---
                        image_url = self._extract_image(entry)
                        if not self._is_valid_image(image_url):
                            image_url = ImageHelper.resolve_image(
                                rss_image=None,
                                source_url=source_url,
                                category=category,
                                article_id=abs(hash(slug)) % 1000,
                            )
                        # -------------------------------------

                        published = entry.get('published_parsed') or entry.get('updated_parsed')
                        pub_date = datetime(*published[:6]) if published else datetime.utcnow()

                        article = Article(
                            title=title,
                            slug=slug,
                            content=content,
                            summary=summary or title,
                            category=category,
                            source=source_name,
                            source_url=source_url,
                            image_url=image_url,
                            author='CryptoNest AI',
                            is_auto_generated=True,
                            is_published=True,
                            seo_title=f"{title[:150]} | {Config.SITE_NAME}",
                            seo_description=(summary or title)[:160],
                            created_at=pub_date,
                        )
                        article.set_tags(tags)

                        db.session.add(article)
                        self.collected_hashes.add(h)
                        new_titles.append(title)

                except Exception as e:
                    print(f"[rss] error ({feed_url}): {e}")
                    continue

            try:
                db.session.commit()
                print(f"[rss] {len(new_titles)} new articles collected")
            except Exception as e:
                db.session.rollback()
                print(f"[rss] commit error: {e}")

            return new_titles


class PriceAlertNewsGenerator:
    """Büyük fiyat hareketlerinden otomatik haber üretir"""

    def generate_price_alert_news(self, alerts, app):
        with app.app_context():
            created = 0

            for a in alerts:
                try:
                    up = a['direction'] == 'up'
                    word = "Surges" if up else "Drops"
                    emoji = "🚀" if up else "📉"
                    cls = "bullish" if up else "bearish"

                    title = (f"{a['coin']} ({a['symbol']}) {word} "
                             f"{a['change_pct']:.1f}% – What's Behind the Move?")
                    slug = slugify(title)[:200]

                    if Article.query.filter_by(slug=slug).first():
                        continue

                    category = 'bitcoin' if a['symbol'] == 'BTC' else \
                               'ethereum' if a['symbol'] == 'ETH' else 'market'

                    image_url = ImageHelper.get_fallback_image(category)

                    content = f"""
<div class="article-content">
    <div class="price-alert-banner {cls}">
        <span class="alert-emoji">{emoji}</span>
        <span class="alert-text">PRICE ALERT</span>
    </div>

    <p class="lead"><strong>{a['coin']} ({a['symbol']})</strong> has
    {'surged' if up else 'dropped'} by <strong>{a['change_pct']:.1f}%</strong>,
    moving from <strong>${a['old_price']:,.2f}</strong> to
    <strong>${a['new_price']:,.2f}</strong>.</p>

    <h2>Price Movement Details</h2>
    <table class="price-table">
        <tr><td>Previous Price</td><td>${a['old_price']:,.2f}</td></tr>
        <tr><td>Current Price</td><td>${a['new_price']:,.2f}</td></tr>
        <tr><td>Change</td><td>{a['change_pct']:.2f}%</td></tr>
        <tr><td>Direction</td><td>{'📈 Bullish' if up else '📉 Bearish'}</td></tr>
    </table>

    <h2>Market Analysis</h2>
    <p>The {'upward' if up else 'downward'} movement in {a['coin']} may be
    attributed to shifting market sentiment, changes in trading volume, and
    broader trends across the cryptocurrency sector.</p>

    <h2>What Traders Should Watch</h2>
    <ul>
        <li>Key support and resistance levels</li>
        <li>24-hour trading volume trends</li>
        <li>Overall market sentiment and Bitcoin dominance</li>
        <li>Upcoming events, listings or protocol announcements</li>
    </ul>

    <div class="disclaimer-box">
        <p><strong>Disclaimer:</strong> This is not financial advice.
        Always DYOR before making investment decisions.</p>
    </div>
</div>
""".strip()

                    summary = (f"{a['coin']} ({a['symbol']}) "
                               f"{'surges' if up else 'drops'} {a['change_pct']:.1f}% "
                               f"from ${a['old_price']:,.2f} to ${a['new_price']:,.2f}.")

                    article = Article(
                        title=title,
                        slug=slug,
                        content=content,
                        summary=summary,
                        category=category,
                        image_url=image_url,
                        author='CryptoNest Price Bot',
                        is_auto_generated=True,
                        is_published=True,
                        is_breaking=a['change_pct'] >= 10,
                        seo_title=f"{title[:150]} | {Config.SITE_NAME}",
                        seo_description=summary[:160],
                    )
                    article.set_tags([a['symbol'].lower(), 'price-alert', 'market',
                                      'bullish' if up else 'bearish'])
                    db.session.add(article)
                    created += 1
                except Exception as e:
                    print(f"[alert] error: {e}")
                    continue

            try:
                db.session.commit()
                if created:
                    print(f"[alert] {created} price alert articles created")
            except Exception as e:
                db.session.rollback()
                print(f"[alert] commit error: {e}")


class MarketSummaryGenerator:
    """Günlük piyasa özeti üretir"""

    def generate_daily_summary(self, coins_data, global_data, app):
        with app.app_context():
            if not coins_data:
                print("[summary] no coin data")
                return False

            today = datetime.utcnow().strftime('%B %d, %Y')
            title = f"Crypto Market Daily Recap – {today}"
            slug = slugify(title)[:200]

            if Article.query.filter_by(slug=slug).first():
                return False

            def pct(c):
                return c.get('price_change_percentage_24h') or 0

            ordered = sorted(coins_data, key=pct, reverse=True)
            gainers = ordered[:5]
            losers = ordered[-5:]

            def row_list(items):
                html = ""
                for c in items:
                    ch = pct(c)
                    color = '#10b981' if ch >= 0 else '#ef4444'
                    html += (f"<li><strong>{c.get('name')} "
                             f"({(c.get('symbol') or '').upper()})</strong>: "
                             f"${(c.get('current_price') or 0):,.2f} "
                             f"<span style='color:{color}'>"
                             f"{'+' if ch >= 0 else ''}{ch:.2f}%</span></li>")
                return html

            total_mcap = global_data.get('total_market_cap', 0) or 0
            btc_dom = global_data.get('btc_dominance', 0) or 0
            change_24h = global_data.get('market_cap_change_24h', 0) or 0
            total_vol = global_data.get('total_volume', 0) or 0

            mcap_str = f"${total_mcap / 1e12:.2f}T" if total_mcap >= 1e12 \
                else f"${total_mcap / 1e9:.2f}B"
            vol_str = f"${total_vol / 1e9:.2f}B" if total_vol >= 1e9 \
                else f"${total_vol / 1e6:.2f}M"

            content = f"""
<div class="article-content">
    <p class="lead">Here is your daily cryptocurrency market recap for
    <strong>{today}</strong>. The total tracked crypto market cap stands at
    approximately <strong>{mcap_str}</strong>, with Bitcoin dominance at
    <strong>{btc_dom:.1f}%</strong>.</p>

    <h2>🟢 Top Gainers (24h)</h2>
    <ul>{row_list(gainers)}</ul>

    <h2>🔴 Top Losers (24h)</h2>
    <ul>{row_list(losers)}</ul>

    <h2>📊 Market Overview</h2>
    <p>The cryptocurrency market has shown
    <strong>{'bullish' if change_24h >= 0 else 'bearish'}</strong> sentiment
    over the last 24 hours, with an aggregate change of
    <strong>{change_24h:+.2f}%</strong>.</p>

    <h2>🔍 Key Metrics</h2>
    <table class="market-table">
        <tr><td>Total Market Cap</td><td>{mcap_str}</td></tr>
        <tr><td>24h Volume</td><td>{vol_str}</td></tr>
        <tr><td>BTC Dominance</td><td>{btc_dom:.1f}%</td></tr>
        <tr><td>24h Market Change</td><td>{change_24h:+.2f}%</td></tr>
    </table>

    <div class="disclaimer-box">
        <p><strong>Disclaimer:</strong> This market recap is for informational
        purposes only and does not constitute financial advice.</p>
    </div>
</div>
""".strip()

            summary = (f"Daily crypto market recap for {today}. "
                       f"Total market cap: {mcap_str}. BTC dominance: {btc_dom:.1f}%.")

            article = Article(
                title=title,
                slug=slug,
                content=content,
                summary=summary,
                category='market',
                image_url=ImageHelper.get_fallback_image('market'),
                author='CryptoNest Market Bot',
                is_auto_generated=True,
                is_published=True,
                is_featured=True,
                seo_title=f"{title} | {Config.SITE_NAME}",
                seo_description=summary[:160],
            )
            article.set_tags(['market-recap', 'daily-summary', 'bitcoin', 'ethereum'])

            db.session.add(article)
            try:
                db.session.commit()
                print("[summary] daily market recap created")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"[summary] commit error: {e}")
                return False
