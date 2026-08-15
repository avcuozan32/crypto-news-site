import requests
import feedparser
from datetime import datetime
from database import db, Article, WhaleTransaction
from config import Config
from slugify import slugify
import random


class WhaleTracker:
    def __init__(self):
        # Whale Alert RSS (ücretsiz)
        self.whale_rss_url = "https://whale-alert.io/rss"
        # Alternatif: Blockchair API (ücretsiz)
        self.blockchair_url = "https://api.blockchair.com"
        self.min_usd = Config.WHALE_ALERT_MINIMUM

    def fetch_from_rss(self):
        """Whale Alert RSS beslemesinden büyük transferleri çek"""
        try:
            feed = feedparser.parse(self.whale_rss_url)
            transactions = []

            for entry in feed.entries[:20]:
                title = entry.get('title', '')
                summary = entry.get('summary', '')

                parsed = self._parse_whale_entry(title, summary)
                if parsed:
                    transactions.append(parsed)

            return transactions
        except Exception as e:
            print(f"Whale RSS Error: {e}")
            return []

    def fetch_from_blockchair(self, blockchain='bitcoin'):
        """Blockchair API'den büyük transferleri çek (ücretsiz)"""
        try:
            url = f"{self.blockchair_url}/{blockchain}/transactions"
            params = {
                'q': f'output_total_usd({self.min_usd}..)',
                'limit': 10,
                'offset': 0,
                's': 'time(desc)',
            }
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            return []
        except Exception as e:
            print(f"Blockchair Error: {e}")
            return []

    def fetch_large_eth_transfers(self):
        """Etherscan API'den büyük ETH transferleri (ücretsiz plan)"""
        try:
            # Ücretsiz Etherscan API
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': '0x0000000000000000000000000000000000000000',
                'startblock': 0,
                'endblock': 99999999,
                'sort': 'desc',
                'apikey': 'YourApiKeyToken'  # Ücretsiz Etherscan key
            }
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return response.json().get('result', [])[:10]
            return []
        except Exception as e:
            print(f"Etherscan Error: {e}")
            return []

    def _parse_whale_entry(self, title, summary):
        """RSS entry'i parse et"""
        try:
            # Örnek: "1,000 BTC (45,000,000 USD) transferred from Binance to Unknown"
            import re

            # Miktar ve sembol
            amount_match = re.search(r'([\d,]+(?:\.\d+)?)\s+([A-Z]+)', title)
            usd_match = re.search(r'\(?([\d,]+(?:\.\d+)?)\s+USD\)?', title)

            if not amount_match:
                return None

            amount = float(amount_match.group(1).replace(',', ''))
            symbol = amount_match.group(2)
            usd_value = float(usd_match.group(1).replace(',', '')) if usd_match else 0

            if usd_value < self.min_usd:
                return None

            # Kaynak ve hedef
            from_match = re.search(r'from\s+([A-Za-z\s]+?)(?:\s+to|\s*$)', title, re.I)
            to_match = re.search(r'to\s+([A-Za-z\s]+?)(?:\s*$)', title, re.I)

            from_owner = from_match.group(1).strip() if from_match else 'Unknown Wallet'
            to_owner = to_match.group(1).strip() if to_match else 'Unknown Wallet'

            return {
                'symbol': symbol,
                'amount': amount,
                'amount_usd': usd_value,
                'from_owner': from_owner,
                'to_owner': to_owner,
                'blockchain': self._get_blockchain(symbol),
                'timestamp': datetime.utcnow(),
            }
        except Exception as e:
            print(f"Parse error: {e}")
            return None

    def _get_blockchain(self, symbol):
        """Sembolden blockchain belirle"""
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binance-smart-chain',
            'SOL': 'solana',
            'USDT': 'ethereum',
            'USDC': 'ethereum',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'MATIC': 'polygon',
        }
        return mapping.get(symbol, 'unknown')

    def save_transactions(self, transactions, app):
        """Transferleri veritabanına kaydet"""
        with app.app_context():
            saved = []
            for tx in transactions:
                # Tekrar kontrolü
                existing = WhaleTransaction.query.filter_by(
                    symbol=tx['symbol'],
                    amount=tx['amount'],
                    amount_usd=tx['amount_usd']
                ).first()

                if not existing:
                    whale_tx = WhaleTransaction(
                        blockchain=tx.get('blockchain', 'unknown'),
                        symbol=tx['symbol'],
                        amount=tx['amount'],
                        amount_usd=tx['amount_usd'],
                        from_owner=tx.get('from_owner', 'Unknown'),
                        to_owner=tx.get('to_owner', 'Unknown'),
                        timestamp=tx.get('timestamp', datetime.utcnow()),
                    )
                    db.session.add(whale_tx)
                    saved.append(whale_tx)

            db.session.commit()
            return saved

    def generate_whale_news(self, transactions, app):
        """Balina hareketi haberlerini üret"""
        with app.app_context():
            generated = []

            for tx in transactions:
                if tx.amount_usd < self.min_usd:
                    continue

                # Büyüklük ifadesi
                if tx.amount_usd >= 1_000_000_000:
                    usd_str = f"${tx.amount_usd/1_000_000_000:.2f} Billion"
                elif tx.amount_usd >= 1_000_000:
                    usd_str = f"${tx.amount_usd/1_000_000:.2f} Million"
                else:
                    usd_str = f"${tx.amount_usd:,.0f}"

                # Yön analizi
                is_exchange_to_wallet = (
                    any(ex in tx.from_owner.lower() for ex in
                        ['binance', 'coinbase', 'kraken', 'okx', 'bybit', 'huobi'])
                    and 'unknown' in tx.to_owner.lower()
                )
                is_wallet_to_exchange = (
                    'unknown' in tx.from_owner.lower()
                    and any(ex in tx.to_owner.lower() for ex in
                            ['binance', 'coinbase', 'kraken', 'okx', 'bybit', 'huobi'])
                )

                if is_exchange_to_wallet:
                    signal = "Bullish"
                    signal_emoji = "🟢"
                    analysis = (
                        f"This movement from exchange to private wallet suggests "
                        f"accumulation. When large amounts of {tx.symbol} leave exchanges, "
                        f"it typically indicates holders are moving funds to cold storage "
                        f"for long-term holding, reducing selling pressure."
                    )
                elif is_wallet_to_exchange:
                    signal = "Bearish"
                    signal_emoji = "🔴"
                    analysis = (
                        f"This transfer to an exchange could indicate potential selling "
                        f"pressure. Large amounts of {tx.symbol} moving to exchanges often "
                        f"precede sell orders, which could put downward pressure on price."
                    )
                else:
                    signal = "Neutral"
                    signal_emoji = "⚪"
                    analysis = (
                        f"This large {tx.symbol} transfer between wallets is being closely "
                        f"monitored by market analysts. Such movements by major holders "
                        f"(whales) can significantly impact market sentiment."
                    )

                title = (
                    f"🐋 Whale Alert: {tx.amount:,.0f} {tx.symbol} "
                    f"({usd_str}) Moved from {tx.from_owner} to {tx.to_owner}"
                )

                content = f"""
                <div class="article-content">
                    <div class="whale-alert-banner {signal.lower()}">
                        <span class="whale-emoji">🐋</span>
                        <strong>WHALE ALERT</strong>
                        <span class="signal-badge {signal.lower()}">{signal_emoji} {signal} Signal</span>
                    </div>

                    <p class="lead">
                        A massive cryptocurrency transfer has been detected on the 
                        <strong>{tx.blockchain.title()}</strong> blockchain. 
                        <strong>{tx.amount:,.2f} {tx.symbol}</strong> worth approximately 
                        <strong>{usd_str}</strong> has been moved from 
                        <strong>{tx.from_owner}</strong> to <strong>{tx.to_owner}</strong>.
                    </p>

                    <h2>Transaction Details</h2>
                    <div class="tx-details">
                        <table class="detail-table">
                            <tr>
                                <td><strong>Amount</strong></td>
                                <td>{tx.amount:,.2f} {tx.symbol}</td>
                            </tr>
                            <tr>
                                <td><strong>USD Value</strong></td>
                                <td>{usd_str}</td>
                            </tr>
                            <tr>
                                <td><strong>From</strong></td>
                                <td>{tx.from_owner}</td>
                            </tr>
                            <tr>
                                <td><strong>To</strong></td>
                                <td>{tx.to_owner}</td>
                            </tr>
                            <tr>
                                <td><strong>Blockchain</strong></td>
                                <td>{tx.blockchain.title()}</td>
                            </tr>
                            <tr>
                                <td><strong>Time</strong></td>
                                <td>{tx.timestamp.strftime('%Y-%m-%d %H:%M UTC')}</td>
                            </tr>
                        </table>
                    </div>

                    <h2>Market Analysis {signal_emoji}</h2>
                    <p>{analysis}</p>

                    <h2>What Are Whale Movements?</h2>
                    <p>
                        Cryptocurrency "whales" are individuals or entities that hold 
                        large amounts of digital assets. Their transactions can move 
                        markets significantly due to the sheer volume of assets involved. 
                        Tracking whale movements has become a popular strategy for 
                        retail investors looking for market signals.
                    </p>

                    <h2>Historical Context</h2>
                    <p>
                        Large {tx.symbol} movements have historically preceded significant 
                        price action. While correlation doesn't equal causation, traders 
                        often use whale tracking tools to gain insights into potential 
                        market direction.
                    </p>

                    <div class="disclaimer-box">
                        <p><strong>⚠️ Disclaimer:</strong> This whale alert is for 
                        informational purposes only. Whale movements do not guarantee 
                        any specific price action. Always conduct your own research 
                        before making investment decisions.</p>
                    </div>
                </div>
                """

                summary_text = (
                    f"Whale alert: {tx.amount:,.0f} {tx.symbol} worth {usd_str} "
                    f"transferred from {tx.from_owner} to {tx.to_owner}. "
                    f"Signal: {signal}."
                )

                slug = slugify(title[:150])
                existing_article = Article.query.filter_by(slug=slug).first()

                if not existing_article:
                    article = Article(
                        title=title,
                        slug=slug,
                        content=content,
                        summary=summary_text,
                        category='market',
                        author='CryptoNest Whale Bot',
                        is_auto_generated=True,
                        is_published=True,
                        is_breaking=True,
                        seo_title=f"Whale Alert: {usd_str} in {tx.symbol} Transferred | CryptoNestNews",
                        seo_description=summary_text[:160],
                    )
                    article.set_tags([
                        tx.symbol.lower(),
                        'whale-alert',
                        'large-transaction',
                        tx.blockchain,
                        signal.lower()
                    ])
                    db.session.add(article)
                    tx.news_generated = True
                    generated.append(title)

            db.session.commit()
            print(f"🐋 {len(generated)} whale news generated")
            return generated

    def run(self, app):
        """Tüm whale takip sürecini çalıştır"""
        print("🐋 Running whale tracker...")

        # RSS'den çek
        rss_transactions = self.fetch_from_rss()
        saved = self.save_transactions(rss_transactions, app)

        # Haberleri üret
        if saved:
            self.generate_whale_news(saved, app)

        print(f"✅ Whale tracker completed: {len(saved)} transactions processed")