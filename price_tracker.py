import requests
from datetime import datetime
from database import db, CoinPrice
from config import Config
import time


class PriceTracker:
    def __init__(self):
        self.api_url = Config.COINGECKO_API_URL
        self.previous_prices = {}

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

        def fetch_global_data(self):
        """Genel piyasa verilerini çek - 3 deneme"""
        for attempt in range(3):
            try:
                url = f"{self.api_url}/global"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json',
                }
                response = requests.get(url, headers=headers, timeout=20)
                if response.status_code == 200:
                    return response.json().get('data', {})
                elif response.status_code == 429:
                    print(f"Rate limited, attempt {attempt+1}/3")
                    time.sleep(5)
                else:
                    print(f"Global API error: {response.status_code}")
            except Exception as e:
                print(f"Global data error (attempt {attempt+1}): {e}")
                time.sleep(2)
        return {}

    def update_prices(self, app):
        """Veritabanındaki fiyatları güncelle"""
        with app.app_context():
            coins_data = self.fetch_prices()
            alerts = []

            for coin in coins_data:
                existing = CoinPrice.query.filter_by(coin_id=coin['id']).first()

                if existing:
                    # Önceki fiyatı sakla (alarm için)
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

                    # Büyük fiyat değişimi kontrolü
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
                        market_cap_rank=coin.get('market_cap_rank', 0),
                        ath=coin.get('ath', 0),
                        atl=coin.get('atl', 0),
                        circulating_supply=coin.get('circulating_supply', 0),
                        image_url=coin.get('image', ''),
                    )
                    db.session.add(new_coin)

            db.session.commit()
            return alerts

        def get_market_summary(self, app=None):
        """Piyasa özeti - API başarısız olursa DB'den hesapla"""
        global_data = self.fetch_global_data()

        total_mcap = global_data.get('total_market_cap', {}).get('usd', 0)

        # API çalıştıysa direkt döndür
        if total_mcap and total_mcap > 0:
            return {
                'total_market_cap': total_mcap,
                'total_volume': global_data.get('total_volume', {}).get('usd', 0),
                'btc_dominance': global_data.get('market_cap_percentage', {}).get('btc', 0),
                'eth_dominance': global_data.get('market_cap_percentage', {}).get('eth', 0),
                'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                'market_cap_change_24h': global_data.get('market_cap_change_percentage_24h_usd', 0),
            }

        # API başarısız → Veritabanından hesapla
        return self._calculate_from_db(app)

    def _calculate_from_db(self, app=None):
        """Veritabanındaki coinlerden piyasa özeti hesapla"""
        from database import CoinPrice

        try:
            coins = CoinPrice.query.all()
            if not coins:
                return self._empty_summary()

            total_mcap = sum(c.market_cap or 0 for c in coins)
            total_vol = sum(c.total_volume or 0 for c in coins)

            btc = next((c for c in coins if c.symbol.upper() == 'BTC'), None)
            eth = next((c for c in coins if c.symbol.upper() == 'ETH'), None)

            btc_dom = ((btc.market_cap / total_mcap) * 100) if btc and total_mcap else 0
            eth_dom = ((eth.market_cap / total_mcap) * 100) if eth and total_mcap else 0

            # Ortalama 24s değişim (market cap ağırlıklı)
            weighted_change = 0
            if total_mcap > 0:
                for c in coins:
                    if c.market_cap and c.price_change_percentage_24h:
                        weight = c.market_cap / total_mcap
                        weighted_change += c.price_change_percentage_24h * weight

            return {
                'total_market_cap': total_mcap,
                'total_volume': total_vol,
                'btc_dominance': btc_dom,
                'eth_dominance': eth_dom,
                'active_cryptocurrencies': len(coins),
                'market_cap_change_24h': weighted_change,
            }
        except Exception as e:
            print(f"DB calculation error: {e}")
            return self._empty_summary()

    def _empty_summary(self):
        return {
            'total_market_cap': 0,
            'total_volume': 0,
            'btc_dominance': 0,
            'eth_dominance': 0,
            'active_cryptocurrencies': 0,
            'market_cap_change_24h': 0,
        }
