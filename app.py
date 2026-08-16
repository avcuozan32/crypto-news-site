import os
from datetime import datetime

from flask import (Flask, render_template, request, jsonify,
                   Response, redirect, url_for)
from flask_caching import Cache

from config import Config
from database import db, init_db, Article, CoinPrice, NewsletterSubscriber
from price_tracker import PriceTracker
from rss_generator import RSSGenerator
from sitemap_generator import SitemapGenerator

app = Flask(__name__)
app.config.from_object(Config)

init_db(app)
cache = Cache(app)
tracker = PriceTracker()

CATEGORY_NAMES = {
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


# ==================== ANA SAYFALAR ====================

@app.route('/')
@cache.cached(timeout=120)
def index():
    page = request.args.get('page', 1, type=int)

    featured = (Article.query
                .filter_by(is_published=True, is_featured=True)
                .order_by(Article.created_at.desc()).limit(3).all())

    if len(featured) < 3:
        extra = (Article.query
                 .filter(Article.is_published == True,
                         Article.image_url != None,
                         Article.image_url != '')
                 .order_by(Article.created_at.desc())
                 .limit(6).all())
        ids = {a.id for a in featured}
        for a in extra:
            if a.id not in ids and len(featured) < 3:
                featured.append(a)
                ids.add(a.id)

    breaking = (Article.query
                .filter_by(is_published=True, is_breaking=True)
                .order_by(Article.created_at.desc()).limit(5).all())

    articles = (Article.query
                .filter_by(is_published=True)
                .order_by(Article.created_at.desc())
                .paginate(page=page, per_page=Config.POSTS_PER_PAGE,
                          error_out=False))

    coins = (CoinPrice.query
             .order_by(CoinPrice.market_cap_rank).limit(20).all())

    return render_template('index.html',
                           featured=featured,
                           breaking=breaking,
                           articles=articles,
                           coins=coins,
                           page=page)


@app.route('/article/<slug>')
def article_detail(slug):
    art = Article.query.filter_by(slug=slug, is_published=True).first_or_404()
    art.views = (art.views or 0) + 1
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    related = (Article.query
               .filter(Article.category == art.category,
                       Article.id != art.id,
                       Article.is_published == True)
               .order_by(Article.created_at.desc()).limit(4).all())

    return render_template('article.html', article=art, related=related)


@app.route('/category/<category>')
@cache.cached(timeout=120)
def category_page(category):
    page = request.args.get('page', 1, type=int)
    articles = (Article.query
                .filter_by(category=category, is_published=True)
                .order_by(Article.created_at.desc())
                .paginate(page=page, per_page=Config.POSTS_PER_PAGE,
                          error_out=False))

    return render_template('category.html',
                           articles=articles,
                           category=category,
                           category_name=CATEGORY_NAMES.get(category, category.title()),
                           page=page)


@app.route('/market')
@cache.cached(timeout=120)
def market_page():
    coins = CoinPrice.query.order_by(CoinPrice.market_cap_rank).all()
    summary = tracker.get_market_summary(app)
    try:
        trending = tracker.fetch_trending()
    except Exception:
        trending = []
    return render_template('market.html', coins=coins,
                           summary=summary, trending=trending)


@app.route('/search')
def search_page():
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    articles = None
    if query:
        articles = (Article.query
                    .filter(Article.is_published == True,
                            (Article.title.contains(query) |
                             Article.summary.contains(query) |
                             Article.content.contains(query)))
                    .order_by(Article.created_at.desc())
                    .paginate(page=page, per_page=Config.POSTS_PER_PAGE,
                              error_out=False))

    return render_template('category.html',
                           articles=articles,
                           category='search',
                           category_name=f'Search Results: "{query}"',
                           page=page)


# ==================== API ====================

@app.route('/api/prices')
@cache.cached(timeout=60)
def api_prices():
    coins = CoinPrice.query.order_by(CoinPrice.market_cap_rank).limit(50).all()
    return jsonify([c.to_dict() for c in coins])


@app.route('/api/ticker')
@cache.cached(timeout=45)
def api_ticker():
    coins = CoinPrice.query.order_by(CoinPrice.market_cap_rank).limit(12).all()
    return jsonify([{
        'symbol': c.symbol,
        'price': c.current_price or 0,
        'change': c.price_change_percentage_24h or 0,
        'image': c.image_url or '',
    } for c in coins])


@app.route('/api/articles')
@cache.cached(timeout=120)
def api_articles():
    limit = request.args.get('limit', 10, type=int)
    category = request.args.get('category')
    q = Article.query.filter_by(is_published=True)
    if category:
        q = q.filter_by(category=category)
    items = q.order_by(Article.created_at.desc()).limit(limit).all()
    return jsonify([a.to_dict() for a in items])


@app.route('/api/market-summary')
@cache.cached(timeout=120)
def api_market_summary():
    return jsonify(tracker.get_market_summary(app))


# ==================== NEWSLETTER ====================

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = (request.form.get('email') or '').strip()
    if email and '@' in email:
        try:
            if not NewsletterSubscriber.query.filter_by(email=email).first():
                db.session.add(NewsletterSubscriber(email=email))
                db.session.commit()
        except Exception:
            db.session.rollback()
    return redirect(url_for('index'))


# ==================== SEO / FEED ====================

@app.route('/sitemap.xml')
def sitemap_root():
    return Response(SitemapGenerator.generate_main_sitemap(app),
                    mimetype='application/xml')


@app.route('/sitemap-pages.xml')
def sitemap_pages_file():
    return Response(SitemapGenerator.generate_pages_sitemap(),
                    mimetype='application/xml')


@app.route('/sitemap-news.xml')
def sitemap_news_file():
    return Response(SitemapGenerator.generate_news_sitemap(app),
                    mimetype='application/xml')


@app.route('/sitemap-articles.xml')
def sitemap_articles_file():
    return Response(SitemapGenerator.generate_articles_sitemap(app),
                    mimetype='application/xml')


@app.route('/rss')
@app.route('/feed')
def rss_main_feed():
    return Response(RSSGenerator.generate_main_feed(app),
                    mimetype='application/rss+xml')


@app.route('/rss/google-news')
def rss_google_feed():
    return Response(RSSGenerator.generate_google_news_feed(app),
                    mimetype='application/rss+xml')


@app.route('/rss/breaking')
def rss_breaking_feed():
    return Response(RSSGenerator.generate_breaking_feed(app),
                    mimetype='application/rss+xml')


@app.route('/rss/<category>')
def rss_category_feed(category):
    return Response(RSSGenerator.generate_category_feed(category, app),
                    mimetype='application/rss+xml')


@app.route('/robots.txt')
def robots_txt():
    txt = (f"User-agent: *\n"
           f"Allow: /\n"
           f"Disallow: /api/\n\n"
           f"Sitemap: {Config.SITE_URL}/sitemap.xml\n")
    return Response(txt, mimetype='text/plain')


@app.route('/google04f0ed8bce0d36b0.html')
def google_site_verification():
    return Response("google-site-verification: google04f0ed8bce0d36b0.html",
                    mimetype='text/html')


# ==================== STATİK SAYFALAR ====================

@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/privacy')
def privacy_page():
    return render_template('privacy.html')


@app.route('/disclaimer')
def disclaimer_page():
    return render_template('disclaimer.html')


# ==================== HATA SAYFALARI ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', error="Page not found (404)"), 404


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('base.html', error="Server error (500)"), 500


# ==================== TEMPLATE FİLTRELERİ ====================

@app.template_filter('format_number')
def format_number(value):
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        return '$0'
    if value >= 1e12:
        return f'${value / 1e12:.2f}T'
    if value >= 1e9:
        return f'${value / 1e9:.2f}B'
    if value >= 1e6:
        return f'${value / 1e6:.2f}M'
    if value >= 1e3:
        return f'${value / 1e3:.2f}K'
    return f'${value:,.2f}'


@app.template_filter('time_ago')
def time_ago(dt):
    if not dt:
        return ''
    diff = datetime.utcnow() - dt
    s = diff.total_seconds()
    if s < 60:
        return 'just now'
    if s < 3600:
        return f'{int(s / 60)}m ago'
    if s < 86400:
        return f'{int(s / 3600)}h ago'
    if s < 604800:
        return f'{int(s / 86400)}d ago'
    return dt.strftime('%b %d, %Y')


@app.context_processor
def inject_globals():
    return {'current_year': datetime.utcnow().year}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
