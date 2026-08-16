import requests
from datetime import datetime
from database import db, CoinPrice
from config import Config
import time


class PriceTracker:
    def __init__(self):
        self.api_url = Config.COINGECKO_API_URL

    def fetch_prices(self):
        """CoinGecko API'den fiyatları çek"""
        try:
            coins = ','.join(Config.TOP_COINS)
            url = f"{self.api_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': coins,
                'order': 'market_cap_desc',
                'per_page': 100,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h,7d'
            }
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Fetch error: {e}")
            return []

    def fetch_trending(self):
        """Trend coinleri çek"""
        try:
            url = f"{self.api_url}/search/trending"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json().get('coins', [])
            return []
        except Exception as e:
            print(f"Trending error: {e}")
            return []

    def update_prices(self, app):
        """Veritabanındaki fiyatları güncelle"""
        with app.app_context():
            coins_data = self.fetch_prices()
            alerts = []

            for coin in coins_data:
                existing = CoinPrice.query.filter_by(coin_id=coin['id']).first()

                if existing:
                    old_price = existing.current_price

                    existing.current_price = coin.get('current_price', 0)
                    existing.market_cap = coin.get('market_cap', 0)
                    existing.total_volume = coin.get('total_volume', 0)
                    existing.price_change_24h = coin.get('price_change_24h', 0)
                    existing.price_change_percentage_24h = coin.get('price_change_percentage_24h', 0)
                    existing.price_change_percentage_7d = coin.get('price_change_percentage_7d_in_currency', 0)
                    existing.market_cap_rank = coin.get('market_cap_rank', 0)
                    existing.ath = coin.get('ath', 0)
                    existing.atl = coin.get('atl', 0)
                    existing.circulating_supply = coin.get('circulating_supply', 0)
                    existing.image_url = coin.get('image', '')
                    existing.last_updated = datetime.utcnow()

                    if old_price and old_price > 0:
                        change_pct = abs((existing.current_price - old_price) / old_price * 100)
                        if change_pct >= Config.PRICE_ALERT_THRESHOLD:
                            alerts.append({
                                'coin': coin['name'],
                                'symbol': coin['symbol'].upper(),
                                'old_price': old_price,
                                'new_price': existing.current_price,
                                'change_pct': change_pct,
                                'direction': 'up' if existing.current_price > old_price else 'down'
                            })
                else:
                    new_coin = CoinPrice(
                        coin_id=coin['id'],
                        symbol=coin.get('symbol', '').upper(),
                        name=coin.get('name', ''),
                        current_price=coin.get('current_price', 0),
                        market_cap=coin.get('market_cap', 0),
                        total_volume=coin.get('total_volume', 0),
                        price_change_24h=coin.get('price_change_24h', 0),
                        price_change_percentage_24h=coin.get('price_change_percentage_24h', 0),
                        price_change_percentage_7d=coin.get('price_change_percentage_7d_in_currency', 0),
                        market_cap_rank=coin.get('market_cap_rank', 0),
                        ath=coin.get('ath', 0),
                        atl=coin.get('atl', 0),
                        circulating_supply=coin.get('circulating_supply', 0),
                        image_url=coin.get('image', ''),
                    )
                    db.session.add(new_coin)

            db.session.commit()
            return alerts

    def get_market_summary(self):
        """Piyasa özeti - kendi veritabanımızdan hesaplar (rate limit yemez)"""
        # Bu fonksiyon artık app.py içinde hesaplanıyor
        # Yedek olarak boş değer döndürür
        return {
            'total_market_cap': 0,
            'total_volume': 0,
            'btc_dominance': 0,
            'eth_dominance': 0,
            'active_cryptocurrencies': 0,
            'market_cap_change_24h': 0,
        }
