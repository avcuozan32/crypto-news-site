from datetime import datetime, timedelta
from database import db, Article, CoinPrice
from config import Config
from slugify import slugify
import random


class NewsGenerator:
    """
    Piyasa verilerinden otomatik haber içeriği üretir.
    Hiç API gerektirmez - kural tabanlı içerik üretimi.
    """

    # Haber şablonları
    BULLISH_TEMPLATES = [
        "{coin} Surges {change:.1f}% – Bulls Take Control as Price Hits ${price:,.2f}",
        "{coin} Price Rallies {change:.1f}% – Is a New All-Time High Coming?",
        "{coin} Jumps {change:.1f}% in 24 Hours – Here's What's Driving the Move",
        "{coin} ({symbol}) Breaks Key Resistance at ${price:,.2f} – Up {change:.1f}%",
        "Bullish Momentum: {coin} Gains {change:.1f}% as Market Sentiment Improves",
    ]

    BEARISH_TEMPLATES = [
        "{coin} Drops {change:.1f}% – Bears Push Price to ${price:,.2f}",
        "{coin} Price Falls {change:.1f}% – Is This a Buying Opportunity?",
        "{coin} Loses {change:.1f}% – Market Analysts Weigh In on Next Support Level",
        "{coin} ({symbol}) Slides {change:.1f}% – What's Causing the Selloff?",
        "Correction Alert: {coin} Down {change:.1f}% – Key Support Levels to Watch",
    ]

    MILESTONE_TEMPLATES = [
        "{coin} Reaches New Monthly High of ${price:,.2f} – What's Next?",
        "{coin} Breaks ${price_round} Barrier – Traders Eye Next Target",
        "{coin} Market Cap Surpasses ${mcap} – Milestone Achievement",
        "Technical Analysis: {coin} Forms {pattern} – Price Target ${target:,.2f}",
    ]

    WEEKLY_ANALYSIS_TEMPLATES = [
        "{coin} Weekly Analysis: Price Up {change:.1f}% – Key Levels for Next Week",
        "{coin} 7-Day Review: From ${old_price:,.2f} to ${price:,.2f} – What to Expect",
        "Weekly Crypto Recap: {coin} Outperforms Market with {change:.1f}% Gains",
    ]

    CHART_PATTERNS = [
        "Bullish Flag", "Cup and Handle", "Double Bottom",
        "Ascending Triangle", "Golden Cross", "Bull Flag",
        "Head and Shoulders (Inverted)", "Falling Wedge",
    ]

    BEARISH_PATTERNS = [
        "Bearish Flag", "Double Top", "Descending Triangle",
        "Death Cross", "Head and Shoulders", "Rising Wedge",
    ]

    def generate_price_news(self, coin_data, app):
        """Fiyat verilerinden haber üret"""
        with app.app_context():
            generated = []
            change = coin_data.get('price_change_percentage_24h', 0) or 0
            price = coin_data.get('current_price', 0) or 0
            name = coin_data.get('name', 'Unknown')
            symbol = coin_data.get('symbol', '').upper()

            if abs(change) < Config.PRICE_ALERT_THRESHOLD:
                return []

            is_bullish = change > 0

            # Şablon seç
            templates = self.BULLISH_TEMPLATES if is_bullish else self.BEARISH_TEMPLATES
            title_template = random.choice(templates)

            title = title_template.format(
                coin=name,
                symbol=symbol,
                price=price,
                change=abs(change),
            )

            content = self._build_price_article(
                coin_data, is_bullish, change, price, name, symbol
            )

            summary = (
                f"{name} ({symbol}) has {'surged' if is_bullish else 'dropped'} "
                f"{abs(change):.1f}% in the last 24 hours, trading at "
                f"${price:,.2f}. Market analysts are closely watching key "
                f"{'resistance' if is_bullish else 'support'} levels."
            )

            return self._save_article(
                title=title,
                content=content,
                summary=summary,
                category=self._get_category(symbol),
                tags=[symbol.lower(), 'price-analysis', 'market',
                      'bullish' if is_bullish else 'bearish'],
                app=app,
                is_breaking=abs(change) >= 10,
            )

    def _build_price_article(self, coin, is_bullish, change, price, name, symbol):
        """Detaylı fiyat analiz makalesi oluştur"""
        direction = "surged" if is_bullish else "declined"
        direction_adj = "bullish" if is_bullish else "bearish"
        signal_color = "bullish" if is_bullish else "bearish"
        emoji = "📈" if is_bullish else "📉"

        market_cap = coin.get('market_cap', 0) or 0
        volume = coin.get('total_volume', 0) or 0
        change_7d = coin.get('price_change_percentage_7d', 0) or 0
        ath = coin.get('ath', 0) or 0
        atl = coin.get('atl', 0) or 0
        rank = coin.get('market_cap_rank', 'N/A')

        # Fiyat tahmini (basit teknik analiz)
        if is_bullish:
            target_1 = price * 1.05
            target_2 = price * 1.10
            support = price * 0.95
        else:
            target_1 = price * 0.95
            target_2 = price * 0.90
            support = price * 1.05

        pattern = random.choice(
            self.CHART_PATTERNS if is_bullish else self.BEARISH_PATTERNS
        )

        # Hacim formatı
        if volume >= 1e9:
            volume_str = f"${volume/1e9:.2f}B"
        elif volume >= 1e6:
            volume_str = f"${volume/1e6:.2f}M"
        else:
            volume_str = f"${volume:,.0f}"

        if market_cap >= 1e12:
            mcap_str = f"${market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            mcap_str = f"${market_cap/1e9:.2f}B"
        else:
            mcap_str = f"${market_cap/1e6:.2f}M"

        content = f"""
        <div class="article-content">

            <div class="price-summary-banner {signal_color}">
                <div class="price-banner-main">
                    <span class="price-emoji">{emoji}</span>
                    <div>
                        <strong>{name} ({symbol})</strong>
                        <span class="current-price">${price:,.4f}</span>
                    </div>
                </div>
                <div class="price-change-badge {signal_color}">
                    {'▲' if is_bullish else '▼'} {abs(change):.2f}%
                </div>
            </div>

            <p class="lead">
                <strong>{name} ({symbol})</strong> has {direction} by 
                <strong>{abs(change):.2f}%</strong> over the past 24 hours, 
                currently trading at <strong>${price:,.4f}</strong>. 
                The move has sparked significant interest among traders, 
                with trading volume reaching <strong>{volume_str}</strong>.
            </p>

            <h2>📊 Key Statistics</h2>
            <table class="stats-table">
                <tr>
                    <td>Current Price</td>
                    <td><strong>${price:,.4f}</strong></td>
                </tr>
                <tr>
                    <td>24h Change</td>
                    <td class="{'positive' if is_bullish else 'negative'}">
                        {'▲' if is_bullish else '▼'} {abs(change):.2f}%
                    </td>
                </tr>
                <tr>
                    <td>7d Change</td>
                    <td class="{'positive' if change_7d >= 0 else 'negative'}">
                        {'+' if change_7d >= 0 else ''}{change_7d:.2f}%
                    </td>
                </tr>
                <tr>
                    <td>24h Volume</td>
                    <td>{volume_str}</td>
                </tr>
                <tr>
                    <td>Market Cap</td>
                    <td>{mcap_str}</td>
                </tr>
                <tr>
                    <td>Market Cap Rank</td>
                    <td>#{rank}</td>
                </tr>
                <tr>
                    <td>All-Time High</td>
                    <td>${ath:,.4f}</td>
                </tr>
                <tr>
                    <td>All-Time Low</td>
                    <td>${atl:,.4f}</td>
                </tr>
            </table>

            <h2>🔍 Technical Analysis</h2>
            <p>
                The daily chart for {name} shows a <strong>{pattern}</strong> formation, 
                which is typically considered a <strong>{direction_adj}</strong> signal 
                by technical analysts. The Relative Strength Index (RSI) suggests the 
                asset is {'approaching overbought territory' if is_bullish and change > 15 else
                          'entering oversold territory' if not is_bullish and abs(change) > 15 else
                          'in neutral territory'}.
            </p>

            <h3>Key Price Levels</h3>
            <table class="stats-table">
                <tr>
                    <td>{'Resistance Level 1' if is_bullish else 'Support Level 1'}</td>
                    <td>${target_1:,.4f}</td>
                </tr>
                <tr>
                    <td>{'Resistance Level 2' if is_bullish else 'Support Level 2'}</td>
                    <td>${target_2:,.4f}</td>
                </tr>
                <tr>
                    <td>{'Key Support' if is_bullish else 'Key Resistance'}</td>
                    <td>${support:,.4f}</td>
                </tr>
            </table>

            <h2>💡 Market Sentiment</h2>
            <p>
                The cryptocurrency market has been showing <strong>{direction_adj}</strong> 
                sentiment over the past 24 hours. {name}'s price action is consistent with 
                {'increased buying pressure and positive market momentum' if is_bullish else
                 'selling pressure and cautious market sentiment'}. 
                Institutional interest in {symbol} {'remains strong' if is_bullish else 'has cooled'}, 
                and on-chain metrics indicate {'accumulation' if is_bullish else 'distribution'} 
                patterns from large wallet holders.
            </p>

            <h2>🔮 Price Prediction</h2>
            <p>
                Based on current technical indicators and market conditions, analysts 
                project that {name} could {'target ${:,.4f} in the short term if bullish momentum continues'.format(target_1) 
                if is_bullish else 
                'find support around ${:,.4f} if selling pressure eases'.format(target_1)}.
                However, the crypto market remains highly volatile, and unexpected news 
                events can quickly change price direction.
            </p>

            <h2>📰 What's Driving the Move?</h2>
            <ul>
                <li>{'Increased retail and institutional buying activity' if is_bullish else 'Profit-taking by early investors'}</li>
                <li>{'Positive developments in the broader crypto ecosystem' if is_bullish else 'Broader market uncertainty and risk-off sentiment'}</li>
                <li>{'Growing adoption and real-world use cases' if is_bullish else 'Regulatory concerns weighing on investor sentiment'}</li>
                <li>{'Technical breakout above key resistance levels' if is_bullish else 'Technical breakdown below key support levels'}</li>
            </ul>

            <div class="disclaimer-box">
                <p><strong>⚠️ Disclaimer:</strong> This article is for informational 
                purposes only and does not constitute financial advice. 
                Cryptocurrency investments carry significant risk. 
                Always do your own research (DYOR) before investing.</p>
            </div>
        </div>
        """

        return content.strip()

    def generate_new_listing_news(self, coin_name, coin_symbol,
                                   exchange_name, listing_price, app):
        """Yeni listeleme haberi üret"""
        title = (
            f"{exchange_name} Lists {coin_name} ({coin_symbol}) – "
            f"Token Launches at ${listing_price:,.4f}"
        )

        content = f"""
        <div class="article-content">
            <div class="listing-banner">
                <span class="listing-icon">🆕</span>
                <strong>NEW LISTING: {coin_symbol} on {exchange_name}</strong>
            </div>

            <p class="lead">
                <strong>{exchange_name}</strong> has officially listed 
                <strong>{coin_name} ({coin_symbol})</strong>, making the token 
                available for trading to millions of users worldwide. 
                The token launched at an initial price of 
                <strong>${listing_price:,.4f}</strong>.
            </p>

            <h2>Listing Details</h2>
            <table class="stats-table">
                <tr><td>Token Name</td><td>{coin_name} ({coin_symbol})</td></tr>
                <tr><td>Exchange</td><td>{exchange_name}</td></tr>
                <tr><td>Initial Price</td><td>${listing_price:,.4f}</td></tr>
                <tr><td>Trading Pairs</td><td>{coin_symbol}/USDT, {coin_symbol}/BTC</td></tr>
                <tr><td>Listing Date</td><td>{datetime.utcnow().strftime('%B %d, %Y')}</td></tr>
            </table>

            <h2>About {coin_name}</h2>
            <p>
                {coin_name} is a cryptocurrency project that has gained significant 
                attention in the crypto community. The listing on {exchange_name} 
                represents a major milestone for the project and could increase 
                its visibility and trading volume significantly.
            </p>

            <h2>Why This Listing Matters</h2>
            <ul>
                <li>Increased liquidity and trading volume</li>
                <li>Greater market accessibility for retail investors</li>
                <li>Enhanced credibility through major exchange listing</li>
                <li>Potential price discovery with broader market participation</li>
            </ul>

            <h2>How to Buy {coin_name}</h2>
            <ol>
                <li>Create or log in to your {exchange_name} account</li>
                <li>Complete KYC verification if required</li>
                <li>Deposit funds (USDT or BTC)</li>
                <li>Navigate to {coin_symbol}/USDT trading pair</li>
                <li>Place your buy order</li>
            </ol>

            <div class="disclaimer-box">
                <p><strong>⚠️ Disclaimer:</strong> New token listings can be extremely 
                volatile. This is not financial advice. Always research thoroughly 
                before investing in newly listed tokens.</p>
            </div>
        </div>
        """

        summary = (
            f"{exchange_name} has listed {coin_name} ({coin_symbol}) at an initial "
            f"price of ${listing_price:,.4f}. The token is now available for trading."
        )

        return self._save_article(
            title=title,
            content=content,
            summary=summary,
            category='exchange',
            tags=[coin_symbol.lower(), exchange_name.lower(),
                  'new-listing', 'token'],
            app=app,
            is_breaking=True,
        )

    def generate_weekly_market_report(self, top_coins, app):
        """Haftalık piyasa raporu üret"""
        with app.app_context():
            today = datetime.utcnow()
            week_ago = today - timedelta(days=7)

            gainers = sorted(
                top_coins,
                key=lambda x: x.price_change_percentage_7d or 0,
                reverse=True
            )[:5]

            losers = sorted(
                top_coins,
                key=lambda x: x.price_change_percentage_7d or 0
            )[:5]

            title = (
                f"Weekly Crypto Market Report – "
                f"Week of {week_ago.strftime('%B %d')} to "
                f"{today.strftime('%B %d, %Y')}"
            )

            gainers_html = ""
            for coin in gainers:
                change = coin.price_change_percentage_7d or 0
                gainers_html += f"""
                <tr>
                    <td><img src="{coin.image_url}" width="20" style="vertical-align:middle"> 
                        {coin.name} ({coin.symbol})</td>
                    <td>${coin.current_price:,.4f}</td>
                    <td style="color: #10b981">+{change:.2f}%</td>
                </tr>"""

            losers_html = ""
            for coin in losers:
                change = coin.price_change_percentage_7d or 0
                losers_html += f"""
                <tr>
                    <td><img src="{coin.image_url}" width="20" style="vertical-align:middle"> 
                        {coin.name} ({coin.symbol})</td>
                    <td>${coin.current_price:,.4f}</td>
                    <td style="color: #ef4444">{change:.2f}%</td>
                </tr>"""

            content = f"""
            <div class="article-content">
                <p class="lead">
                    Here is your comprehensive weekly cryptocurrency market report 
                    covering the period from <strong>{week_ago.strftime('%B %d')}</strong> 
                    to <strong>{today.strftime('%B %d, %Y')}</strong>. 
                    We analyze the biggest movers, market trends, and what to 
                    expect in the coming week.
                </p>

                <h2>🟢 Top Weekly Gainers</h2>
                <table class="stats-table">
                    <thead>
                        <tr><th>Coin</th><th>Price</th><th>7d Change</th></tr>
                    </thead>
                    <tbody>{gainers_html}</tbody>
                </table>

                <h2>🔴 Top Weekly Losers</h2>
                <table class="stats-table">
                    <thead>
                        <tr><th>Coin</th><th>Price</th><th>7d Change</th></tr>
                    </thead>
                    <tbody>{losers_html}</tbody>
                </table>

                <h2>📊 Market Overview</h2>
                <p>
                    The cryptocurrency market has experienced significant volatility 
                    this week. Bitcoin and Ethereum continue to dominate market 
                    sentiment, while altcoins show mixed performance.
                </p>

                <h2>🔮 Week Ahead Outlook</h2>
                <p>
                    Looking ahead, traders will be monitoring macroeconomic data 
                    releases, regulatory developments, and on-chain metrics to 
                    gauge market direction. Key events to watch include Federal 
                    Reserve meetings, major protocol upgrades, and institutional 
                    investment announcements.
                </p>

                <div class="disclaimer-box">
                    <p><strong>⚠️ Disclaimer:</strong> This weekly report is for 
                    informational purposes only and does not constitute financial 
                    advice.</p>
                </div>
            </div>
            """

            summary = (
                f"Weekly crypto market report: Top gainer is "
                f"{gainers[0].name if gainers else 'N/A'} and "
                f"biggest loser is {losers[0].name if losers else 'N/A'}."
            )

            return self._save_article(
                title=title,
                content=content,
                summary=summary,
                category='market',
                tags=['weekly-report', 'market-analysis', 'crypto'],
                app=app,
                is_featured=True,
            )

    def generate_fear_greed_news(self, index_value, app):
        """Fear & Greed Index haberi üret"""
        if index_value <= 25:
            sentiment = "Extreme Fear"
            emoji = "😱"
            analysis = (
                "Historically, extreme fear in the crypto market has often "
                "presented buying opportunities for long-term investors. "
                "Warren Buffett's principle of 'be greedy when others are fearful' "
                "is frequently cited in these conditions."
            )
        elif index_value <= 45:
            sentiment = "Fear"
            emoji = "😨"
            analysis = (
                "The market is showing fearful sentiment, indicating that many "
                "investors are cautious about the near-term outlook. This could "
                "present accumulation opportunities for patient investors."
            )
        elif index_value <= 55:
            sentiment = "Neutral"
            emoji = "😐"
            analysis = (
                "The market is in a neutral state, with neither significant "
                "greed nor fear dominating sentiment. This balanced state "
                "often precedes a directional move in either direction."
            )
        elif index_value <= 75:
            sentiment = "Greed"
            emoji = "🤑"
            analysis = (
                "Greedy sentiment suggests the market may be becoming overheated. "
                "Investors should exercise caution and consider taking some profits "
                "as the market could be approaching a local top."
            )
        else:
            sentiment = "Extreme Greed"
            emoji = "🚀"
            analysis = (
                "Extreme greed historically precedes market corrections. "
                "While momentum can continue, investors should be aware of "
                "the increased risk of a pullback when sentiment reaches "
                "such extreme levels."
            )

        title = (
            f"Crypto Fear & Greed Index Hits {index_value} – "
            f"Market Shows '{sentiment}' {emoji}"
        )

        content = f"""
        <div class="article-content">
            <div class="fear-greed-display">
                <div class="fgi-gauge">
                    <div class="fgi-value" style="color: {'#10b981' if index_value > 50 else '#ef4444'}">
                        {index_value}
                    </div>
                    <div class="fgi-label">{sentiment} {emoji}</div>
                </div>
            </div>

            <p class="lead">
                The <strong>Crypto Fear & Greed Index</strong> currently stands at 
                <strong>{index_value}/100</strong>, indicating 
                <strong>{sentiment}</strong> in the cryptocurrency market. 
                This metric aggregates multiple factors including market volatility, 
                trading volume, social media sentiment, and market dominance.
            </p>

            <h2>What Does This Mean?</h2>
            <p>{analysis}</p>

            <h2>How is the Index Calculated?</h2>
            <ul>
                <li><strong>Volatility (25%):</strong> Current volatility vs 30/90-day averages</li>
                <li><strong>Market Momentum (25%):</strong> Volume and market momentum</li>
                <li><strong>Social Media (15%):</strong> Twitter and Reddit sentiment</li>
                <li><strong>Surveys (15%):</strong> Weekly crypto polls</li>
                <li><strong>Bitcoin Dominance (10%):</strong> BTC market share</li>
                <li><strong>Google Trends (10%):</strong> Search interest data</li>
            </ul>

            <h2>Historical Context</h2>
            <p>
                The Fear & Greed Index has been a useful contrarian indicator 
                throughout crypto market history. Major market bottoms in 2018, 
                2020, and 2022 all coincided with extreme fear readings, while 
                market peaks often saw extreme greed levels.
            </p>

            <div class="disclaimer-box">
                <p><strong>⚠️ Disclaimer:</strong> The Fear & Greed Index is one 
                tool among many and should not be used as the sole basis for 
                investment decisions.</p>
            </div>
        </div>
        """

        summary = (
            f"The Crypto Fear & Greed Index is at {index_value}/100, "
            f"showing '{sentiment}'. {analysis[:100]}..."
        )

        return self._save_article(
            title=title,
            content=content,
            summary=summary,
            category='market',
            tags=['fear-greed-index', 'market-sentiment', 'analysis'],
            app=app,
        )

    def _get_category(self, symbol):
        """Sembolden kategori belirle"""
        categories = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'altcoins',
            'SOL': 'altcoins',
            'ADA': 'altcoins',
            'DOT': 'altcoins',
            'MATIC': 'altcoins',
            'LINK': 'altcoins',
            'UNI': 'defi',
            'AAVE': 'defi',
        }
        return categories.get(symbol.upper(), 'altcoins')

    def _save_article(self, title, content, summary, category,
                       tags, app, is_breaking=False, is_featured=False):
        """Makaleyi veritabanına kaydet"""
        with app.app_context():
            slug = slugify(title[:200])
            existing = Article.query.filter_by(slug=slug).first()

            if existing:
                return []

            article = Article(
                title=title,
                slug=slug,
                content=content,
                summary=summary,
                category=category,
                author='CryptoNest AI',
                is_auto_generated=True,
                is_published=True,
                is_breaking=is_breaking,
                is_featured=is_featured,
                seo_title=f"{title[:150]} | CryptoNestNews",
                seo_description=summary[:160],
            )
            article.set_tags(tags)

            db.session.add(article)
            db.session.commit()

            print(f"✅ Article generated: {title[:60]}...")
            return [title]