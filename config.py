import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# data klasörünü otomatik oluştur
os.makedirs(DATA_DIR, exist_ok=True)


class Config:
    # Site Ayarları
    SITE_NAME = "CryptoNestNews"
    SITE_URL = "https://cryptonestnews.onrender.com"
    SITE_DESCRIPTION = "Your trusted source for crypto news, market analysis, and blockchain technology updates."
    SITE_LANGUAGE = "en"

    # Veritabanı (tam yol)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(DATA_DIR, 'crypto_news.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'crypto-news-secret-key-2024')

    # API
    COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
    COINMARKETCAP_API_KEY = os.environ.get('CMC_API_KEY', '')
    COINMARKETCAP_API_URL = "https://pro-api.coinmarketcap.com/v1"

    # RSS Haber Kaynakları
    NEWS_RSS_FEEDS = [
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed",
        "https://beincrypto.com/feed/",
        "https://cryptonews.com/news/feed/",
        "https://bitcoinmagazine.com/feed",
    ]

    # Takip Edilecek Coinler
    TOP_COINS = [
        'bitcoin', 'ethereum', 'binancecoin', 'solana', 'ripple',
        'cardano', 'dogecoin', 'polkadot', 'avalanche-2', 'chainlink',
        'polygon', 'tron', 'uniswap', 'litecoin', 'near',
        'aptos', 'arbitrum', 'optimism', 'sui', 'sei-network'
    ]

    # Otomatik Haber Ayarları
    PRICE_ALERT_THRESHOLD = 5
    WHALE_ALERT_MINIMUM = 1000000
    AUTO_NEWS_INTERVAL_MINUTES = 15

    # SEO
    GOOGLE_ANALYTICS_ID = os.environ.get('GA_ID', '')
    GOOGLE_ADSENSE_ID = os.environ.get('ADSENSE_ID', '')

    # Cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

    # Sayfalama
    POSTS_PER_PAGE = 12
