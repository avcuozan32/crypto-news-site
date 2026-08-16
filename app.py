from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
from flask_caching import Cache
from database import db, init_db, Article, CoinPrice, NewsletterSubscriber
from config import Config
from scheduler import setup_scheduler
from price_tracker import PriceTracker
import os

app = Flask(__name__)
app.config.from_object(Config)

init_db(app)
cache = Cache(app)
tracker = PriceTracker()
scheduler = setup_scheduler(app)


# ==================== ANA SAYFALAR ====================

@app.route('/')
@cache.cached(timeout=120)
def index():
    page = request.args.get('page', 1, type=int)

    featured = Article.query.filter_by(
        is_published=True, is_featured=True
    ).order_by(Article.created_at.desc()).limit(3).all()

    breaking = Article.query.filter_by(
        is_published=True, is_breaking=True
    ).order_by(Article.created_at.desc()).limit(5).all()

    articles = Article.query.filter_by(
        is_published=True
    ).order_by(Article.created_at.desc()).paginate(
        page=page, per_page=Config.POSTS_PER_PAGE, error_out=False
    )

    coins = CoinPrice.query.order_by(CoinPrice.market_cap_rank).limit(20).all()

    return render_template('index.html',
        featured=featured,
        breaking=breaking,
        articles=articles,
        coins=coins,
        page=page,
    )


@app.route('/article/<slug>')
def article(slug):
    article = Article.query.filter_by(slug=slug, is_published=True).first_or_404()
    article.views += 1
    db.session.commit()

    related = Article.query.filter(
        Article.category == article.category,
        Article.id != article.id,
        Article.is_published == True
    ).order_by(Article.created_at.desc()).limit(4).all()

    return render_template('article.html', article=article, related=related)


@app.route('/category/<category>')
@cache.cached(timeout=120)
def category(category):
    page = request.args.get('page', 1, type=int)
    articles = Article.query.filter_by(
        category=category, is_published=True
    ).order_by(Article.created_at.desc()).paginate(
        page=page, per_page=Config.POSTS_PER_PAGE, error_out=False
    )

    category_names = {
        'news': 'Latest News',
        'market': 'Market Analysis',
        'bitcoin': 'Bitcoin',
        'ethereum': 'Ethereum',
        'altcoins': 'Altcoins',
        'defi': 'DeFi',
        'nft': 'NFT',
        'web3': 'Web3 & GameFi',
        'regulation': 'Regulation',
        'security': 'Security',
        'technology': 'Blockchain Tech',
        'exchange': 'Exchanges',
    }

    return render_template('category.html',
        articles=articles,
        category=category,
        category_name=category_names.get(category, category.title()),
        page=page,
    )


@app.route('/market')
@cache.cached(timeout=60)
def market():
    coins = CoinPrice.query.order_by(CoinPrice.market_cap_rank).all()

    total_market_cap = sum((c.market_cap or 0) for c in coins)
    total_volume = sum((c.total_volume or 0) for c in coins)

    btc = next((c for c in coins if c.symbol == 'BTC'), None)
    eth = next((c for c in coins if c.symbol == 'ETH'), None)

    btc_dominance = 0
    eth_dominance = 0
    if total_market_cap > 0:
        if btc:
            btc_dominance = (btc.market_cap or 0) / total_market_cap * 100
        if eth:
            eth_dominance = (eth.market_cap or 0) / total_market_cap * 100

    changes = [c.price_change_percentage_24h for c in coins if c.price_change_percentage_24h is not None]
    avg_change = sum(changes) / len(changes) if changes else 0

    summary = {
        'total_market_cap': total_market_cap,
        'total_volume': total_volume,
        'btc_dominance': btc_dominance,
        'eth_dominance': eth_dominance,
        'active_cryptocurrencies': len(coins),
        'market_cap_change_24h': avg_change,
    }

    return render_template('market.html', coins=coins, summary=summary, trending=[])


@app.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    if query:
        articles = Article.query.filter(
            Article.is_published == True,
            (Article.title.contains(query) | Article.content.contains(query))
        ).order_by(Article.created_at.desc()).paginate(
            page=page, per_page=Config.POSTS_PER_PAGE, error_out=False
        )
    else:
        articles = None

    return render_template('category.html',
        articles=articles,
        category='search',
        category_name=f'Search Results: "{query}"',
        page=page,
    )


# ==================== API ENDPOINTS ====================

@app.route('/api/prices')
@cache.cached(timeout=60)
def api_prices():
    coins = CoinPrice.query.order_by(CoinPrice.market_cap_rank).limit(50).all()
    return jsonify([coin.to_dict() for coin in coins])


@app.route('/api/ticker')
@cache.cached(timeout=30)
def api_ticker():
    coins = CoinPrice.query.order_by(CoinPrice.market_cap_rank).limit(10).all()
    ticker_data = []
    for coin in coins:
        ticker_data.append({
            'symbol': coin.symbol,
            'price': coin.current_price,
            'change': coin.price_change_percentage_24h,
            'image': coin.image_url,
        })
    return jsonify(ticker_data)


# ==================== NEWSLETTER ====================

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email', '').strip()
    if email:
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if not existing:
            sub = NewsletterSubscriber(email=email)
            db.session.add(sub)
            db.session.commit()
    return redirect(url_for('index'))


# ==================== SEO SAYFALAR ====================

from sitemap_generator import SitemapGenerator
from rss_generator import RSSGenerator

@app.route('/sitemap.xml')
def sitemap_xml():
    xml = SitemapGenerator.generate_main_sitemap(app)
    return Response(xml, mimetype='application/xml')

@app.route('/sitemap-pages.xml')
def sitemap_pages():
    xml = SitemapGenerator.generate_pages_sitemap()
    return Response(xml, mimetype='application/xml')

@app.route('/sitemap-news.xml')
def sitemap_news():
    xml = SitemapGenerator.generate_news_sitemap(app)
    return Response(xml, mimetype='application/xml')

@app.route('/sitemap-articles.xml')
def sitemap_articles():
    xml = SitemapGenerator.generate_articles_sitemap(app)
    return Response(xml, mimetype='application/xml')

@app.route('/rss')
@app.route('/feed')
def rss_main():
    xml = RSSGenerator.generate_main_feed(app)
    return Response(xml, mimetype='application/rss+xml')

@app.route('/rss/google-news')
def rss_google_news():
    xml = RSSGenerator.generate_google_news_feed(app)
    return Response(xml, mimetype='application/rss+xml')

@app.route('/rss/breaking')
def rss_breaking():
    xml = RSSGenerator.generate_breaking_feed(app)
    return Response(xml, mimetype='application/rss+xml')

@app.route('/rss/<category>')
def rss_category(category):
    xml = RSSGenerator.generate_category_feed(category, app)
    return Response(xml, mimetype='application/rss+xml')

@app.route('/robots.txt')
def robots():
    content = f"""User-agent: *
Allow: /
Disallow: /api/

Sitemap: {Config.SITE_URL}/sitemap.xml
"""
    return Response(content, mimetype='text/plain')


# ==================== GOOGLE VERIFICATION ====================

@app.route('/google04f0ed8bce0d36b0.html')
def google_verify():
    return 'google-site-verification: google04f0ed8bce0d36b0.html'


# ==================== YASAL SAYFALAR ====================

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')


# ==================== HATA SAYFALARI ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Server error"), 500


# ==================== TEMPLATE FİLTRELERİ ====================

@app.template_filter('format_number')
def format_number(value):
    if value is None:
        return '$0'
    if value >= 1e12:
        return f'${value/1e12:.2f}T'
    elif value >= 1e9:
        return f'${value/1e9:.2f}B'
    elif value >= 1e6:
        return f'${value/1e6:.2f}M'
    elif value >= 1e3:
        return f'${value/1e3:.2f}K'
    else:
        return f'${value:,.2f}'

@app.template_filter('time_ago')
def time_ago(dt):
    from datetime import datetime
    if not dt:
        return ''
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        return f'{int(seconds / 60)}m ago'
    elif seconds < 86400:
        return f'{int(seconds / 3600)}h ago'
    elif seconds < 604800:
        return f'{int(seconds / 86400)}d ago'
    else:
        return dt.strftime('%b %d, %Y')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
