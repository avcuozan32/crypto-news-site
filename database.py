from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from slugify import slugify
import json

db = SQLAlchemy()

class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(500), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    category = db.Column(db.String(100), default='news')
    tags = db.Column(db.Text)  # JSON formatında
    source = db.Column(db.String(200))
    source_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    author = db.Column(db.String(100), default='CryptoNest Team')
    is_auto_generated = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_breaking = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    seo_title = db.Column(db.String(200))
    seo_description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.seo_title:
            self.seo_title = self.title
        if not self.seo_description:
            self.seo_description = self.summary[:160] if self.summary else self.title

    def get_tags(self):
        if self.tags:
            return json.loads(self.tags)
        return []

    def set_tags(self, tag_list):
        self.tags = json.dumps(tag_list)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'summary': self.summary,
            'category': self.category,
            'tags': self.get_tags(),
            'source': self.source,
            'image_url': self.image_url,
            'author': self.author,
            'views': self.views,
            'created_at': self.created_at.isoformat(),
        }


class CoinPrice(db.Model):
    __tablename__ = 'coin_prices'

    id = db.Column(db.Integer, primary_key=True)
    coin_id = db.Column(db.String(100), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    total_volume = db.Column(db.Float)
    price_change_24h = db.Column(db.Float)
    price_change_percentage_24h = db.Column(db.Float)
    price_change_percentage_7d = db.Column(db.Float)
    market_cap_rank = db.Column(db.Integer)
    ath = db.Column(db.Float)  # All Time High
    atl = db.Column(db.Float)  # All Time Low
    circulating_supply = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'coin_id': self.coin_id,
            'symbol': self.symbol,
            'name': self.name,
            'current_price': self.current_price,
            'market_cap': self.market_cap,
            'total_volume': self.total_volume,
            'price_change_24h': self.price_change_24h,
            'price_change_percentage_24h': self.price_change_percentage_24h,
            'price_change_percentage_7d': self.price_change_percentage_7d,
            'market_cap_rank': self.market_cap_rank,
            'image_url': self.image_url,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }


class WhaleTransaction(db.Model):
    __tablename__ = 'whale_transactions'

    id = db.Column(db.Integer, primary_key=True)
    blockchain = db.Column(db.String(50))
    symbol = db.Column(db.String(20))
    amount = db.Column(db.Float)
    amount_usd = db.Column(db.Float)
    from_address = db.Column(db.String(200))
    to_address = db.Column(db.String(200))
    from_owner = db.Column(db.String(100))
    to_owner = db.Column(db.String(100))
    transaction_hash = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    news_generated = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'blockchain': self.blockchain,
            'symbol': self.symbol,
            'amount': self.amount,
            'amount_usd': self.amount_usd,
            'from_owner': self.from_owner or 'Unknown Wallet',
            'to_owner': self.to_owner or 'Unknown Wallet',
            'timestamp': self.timestamp.isoformat(),
        }


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteStats(db.Model):
    __tablename__ = 'site_stats'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True)
    total_views = db.Column(db.Integer, default=0)
    total_articles = db.Column(db.Integer, default=0)
    unique_visitors = db.Column(db.Integer, default=0)


def init_db(app):
    import os
    # data klasörünü oluştur
    os.makedirs('data', exist_ok=True)
    db.init_app(app)
    with app.app_context():
        db.create_all()
