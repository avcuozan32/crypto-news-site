import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def initialize_database():
    from app import app
    from database import db, Article, CoinPrice, SiteStats
    from datetime import datetime, date

    os.makedirs('data', exist_ok=True)

    with app.app_context():
        db.create_all()
        print("✅ Database tables created")

        if Article.query.count() == 0:
            from slugify import slugify

            starter_articles = [
                {
                    'title': 'Welcome to CryptoNestNews – Your Ultimate Crypto Source',
                    'slug': 'welcome-to-cryptonestnews',
                    'content': '''<div class="article-content">
                        <p class="lead">Welcome to CryptoNestNews, your trusted source for
                        the latest cryptocurrency news, market analysis, and blockchain
                        technology updates.</p>
                        <h2>What We Cover</h2>
                        <ul>
                            <li>Breaking cryptocurrency news 24/7</li>
                            <li>Real-time market analysis and price updates</li>
                            <li>DeFi, NFT, and Web3 developments</li>
                            <li>Regulatory news from around the world</li>
                        </ul>
                        <div class="disclaimer-box">
                            <p><strong>Disclaimer:</strong> All content on CryptoNestNews
                            is for informational purposes only. Not financial advice.</p>
                        </div>
                    </div>''',
                    'summary': 'Welcome to CryptoNestNews. We provide 24/7 cryptocurrency news, market analysis, whale alerts, and blockchain updates.',
                    'category': 'news',
                    'author': 'CryptoNest Team',
                    'is_featured': True,
                    'is_published': True,
                    'tags': ['welcome', 'about', 'crypto-news'],
                },
                {
                    'title': 'Bitcoin 2024: Everything You Need to Know About the Halving',
                    'slug': 'bitcoin-2024-halving-guide',
                    'content': '''<div class="article-content">
                        <p class="lead">The Bitcoin halving is one of the most significant
                        events in the cryptocurrency calendar.</p>
                        <h2>What is the Bitcoin Halving?</h2>
                        <p>The Bitcoin halving is a pre-programmed event that occurs every
                        210,000 blocks (approximately every 4 years).</p>
                        <h2>Historical Halvings</h2>
                        <table class="stats-table">
                            <tr><th>Date</th><th>Before</th><th>After</th></tr>
                            <tr><td>2012</td><td>50 BTC</td><td>25 BTC</td></tr>
                            <tr><td>2016</td><td>25 BTC</td><td>12.5 BTC</td></tr>
                            <tr><td>2020</td><td>12.5 BTC</td><td>6.25 BTC</td></tr>
                            <tr><td>2024</td><td>6.25 BTC</td><td>3.125 BTC</td></tr>
                        </table>
                        <div class="disclaimer-box">
                            <p><strong>Disclaimer:</strong> Not financial advice.</p>
                        </div>
                    </div>''',
                    'summary': 'The Bitcoin halving reduces miner rewards by 50%. Learn what this means for BTC price.',
                    'category': 'bitcoin',
                    'author': 'CryptoNest Research',
                    'is_featured': True,
                    'is_published': True,
                    'tags': ['bitcoin', 'halving', 'btc', 'mining'],
                },
                {
                    'title': 'What is DeFi? A Complete Beginners Guide',
                    'slug': 'what-is-defi-beginners-guide',
                    'content': '''<div class="article-content">
                        <p class="lead">Decentralized Finance (DeFi) is revolutionizing
                        the traditional financial system.</p>
                        <h2>What is DeFi?</h2>
                        <p>DeFi refers to financial services built on blockchain networks
                        that operate without central intermediaries like banks.</p>
                        <h2>Key DeFi Concepts</h2>
                        <ul>
                            <li><strong>Smart Contracts:</strong> Self-executing code</li>
                            <li><strong>Liquidity Pools:</strong> Funds in smart contracts</li>
                            <li><strong>Yield Farming:</strong> Earning rewards</li>
                            <li><strong>DEX:</strong> Decentralized exchanges</li>
                        </ul>
                        <div class="disclaimer-box">
                            <p><strong>Disclaimer:</strong> Not financial advice.</p>
                        </div>
                    </div>''',
                    'summary': 'DeFi is transforming financial services through blockchain. Learn what it is and how it works.',
                    'category': 'defi',
                    'author': 'CryptoNest Education',
                    'is_featured': False,
                    'is_published': True,
                    'tags': ['defi', 'ethereum', 'beginners'],
                },
            ]

            for article_data in starter_articles:
                import json
                tags = article_data.pop('tags', [])
                article = Article(**article_data)
                article.set_tags(tags)
                db.session.add(article)

            db.session.commit()
            print(f"✅ 3 starter articles added")

        if SiteStats.query.count() == 0:
            stats = SiteStats(
                date=date.today(),
                total_views=0,
                total_articles=Article.query.count(),
                unique_visitors=0,
            )
            db.session.add(stats)
            db.session.commit()
            print("✅ Site stats initialized")

        print(f"\n📊 Database Summary:")
        print(f"   Articles: {Article.query.count()}")
        print(f"   Coins: {CoinPrice.query.count()}")
        print(f"   Location: data/crypto_news.db")
        print(f"\n🚀 Ready to start!")


if __name__ == '__main__':
    initialize_database()
