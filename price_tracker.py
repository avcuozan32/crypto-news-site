import requests
import time
from datetime import datetime
from database import db, CoinPrice
from config import Config


class PriceTracker:
    """CoinGecko API üzerinden fiyat takibi ve piyasa özeti"""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    }

    def __init__(self):
        self.api_url = Config.COINGECKO_API_URL

    # ==================== API ÇAĞRILARI ====================

    def fetch_prices(self):
        """Coin fiyatlarını çek (3 deneme)"""
        coins = ','.join(Config.TOP_COINS)
        url = f"{self.api_url}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'ids': coins,
            'order': 'market_cap_desc',
            'per_page': 100,
            'page': 1,
            'sparkline': 'false',
            'price_change_percentage': '24h,7d',
        }

        for attempt in range(3):
            try:
                r = requests.get(url, params=params,
                                 headers=self.HEADERS, timeout=25)
                if r.status_code == 200:
                    return r.json()
                if r.status_code == 429:
                    print(f"[prices] rate limited, retry {attempt + 1}/3")
                    time.sleep(6)
                else:
                    print(f"[prices] API error: {r.status_code}")
                    time.sleep(2)
            except Exception as e:
                print(f"[prices] error (try {attempt + 1}): {e}")
                time.sleep(2)
        return []

    def fetch_global_data(self):
        """Global piyasa verisi çek (3 deneme)"""
        url = f"{self.api_url}/global"

        for attempt in range(3):
            try:
                r = requests.get(url, headers=self.HEADERS, timeout=20)
                if r.status_code == 200:
                    return r.json().get('data', {}) or {}
                if r.status_code == 429:
                    print(f"[global] rate limited, retry {attempt + 1}/3")
                    time.sleep(6)
                else:
                    print(f"[global] API error: {r.status_code}")
                    time.sleep(2)
            except Exception as e:
                print(f"[global] error (try {attempt + 1}): {e}")
                time.sleep(2)
        return {}

    def fetch_trending(self):
        """Trend coinleri çek"""
        try:
            r = requests.get(f"{self.api_url}/search/trending",
                             headers=self.HEADERS, timeout=15)
            if r.status_code == 200:
                return r.json().get('coins', [])
        except Exception as e:
            print(f"[trending] error: {e}")
        return []

    # ==================== VERİTABANI GÜNCELLEME ====================

    def update_prices(self, app):
        """Fiyatları veritabanına yaz, büyük değişimleri döndür"""
        with app.app_context():
            coins_data = self.fetch_prices()
            if not coins_data:
                print("[prices] no data received")
                return []

            alerts = []

            for coin in coins_data:
                try:
                    existing = CoinPrice.query.filter_by(
                        coin_id=coin['id']).first()

                    price = coin.get('current_price') or 0
                    change_24h = coin.get('price_change_percentage_24h') or 0
                    change_7d = coin.get(
                        'price_change_percentage_7d_in_currency') or 0

                    if existing:
                        old_price = existing.current_price or 0

                        existing.current_price = price
                        existing.market_cap = coin.get('market_cap') or 0
                        existing.total_volume = coin.get('total_volume') or 0
                        existing.price_change_24h = coin.get('price_change_24h') or 0
                        existing.price_change_percentage_24h = change_24h
                        existing.price_change_percentage_7d = change_7d
                        existing.market_cap_rank = coin.get('market_cap_rank') or 999
                        existing.ath = coin.get('ath') or 0
                        existing.atl = coin.get('atl') or 0
                        existing.circulating_supply = coin.get('circulating_supply') or 0
                        existing.image_url = coin.get('image') or ''
                        existing.last_updated = datetime.utcnow()

                        if old_price > 0 and price > 0:
                            pct = abs((price - old_price) / old_price * 100)
                            if pct >= Config.PRICE_ALERT_THRESHOLD:
                                alerts.append({
                                    'coin': coin.get('name', ''),
                                    'symbol': (coin.get('symbol') or '').upper(),
                                    'old_price': old_price,
                                    'new_price': price,
                                    'change_pct': pct,
                                    'direction': 'up' if price > old_price else 'down',
                                })
                    else:
                        db.session.add(CoinPrice(
                            coin_id=coin['id'],
                            symbol=(coin.get('symbol') or '').upper(),
                            name=coin.get('name', ''),
                            current_price=price,
                            market_cap=coin.get('market_cap') or 0,
                            total_volume=coin.get('total_volume') or 0,
                            price_change_24h=coin.get('price_change_24h') or 0,
                            price_change_percentage_24h=change_24h,
                            price_change_percentage_7d=change_7d,
                            market_cap_rank=coin.get('market_cap_rank') or 999,
                            ath=coin.get('ath') or 0,
                            atl=coin.get('atl') or 0,
                            circulating_supply=coin.get('circulating_supply') or 0,
                            image_url=coin.get('image') or '',
                        ))
                except Exception as e:
                    print(f"[prices] coin error: {e}")
                    continue

            try:
                db.session.commit()
                print(f"[prices] {len(coins_data)} coins updated")
            except Exception as e:
                db.session.rollback()
                print(f"[prices] commit error: {e}")

            return alerts

    # ==================== PİYASA ÖZETİ ====================

    def get_market_summary(self, app=None):
        """
        Piyasa özeti döndür.
        1) CoinGecko /global dener
        2) Başarısızsa veritabanındaki coinlerden hesaplar
        """
        g = self.fetch_global_data()
        total_mcap = 0
        try:
            total_mcap = (g.get('total_market_cap') or {}).get('usd', 0) or 0
        except Exception:
            total_mcap = 0

        if total_mcap and total_mcap > 0:
            return {
                'total_market_cap': total_mcap,
                'total_volume': (g.get('total_volume') or {}).get('usd', 0) or 0,
                'btc_dominance': (g.get('market_cap_percentage') or {}).get('btc', 0) or 0,
                'eth_dominance': (g.get('market_cap_percentage') or {}).get('eth', 0) or 0,
                'active_cryptocurrencies': g.get('active_cryptocurrencies', 0) or 0,
                'market_cap_change_24h': g.get('market_cap_change_percentage_24h_usd', 0) or 0,
                'source': 'api',
            }

        print("[global] API failed -> calculating from database")
        if app is not None:
            with app.app_context():
                return self._calculate_from_db()
        return self._calculate_from_db()

    def _calculate_from_db(self):
        """Veritabanındaki coinlerden piyasa özeti hesapla"""
        try:
            coins = CoinPrice.query.all()
            if not coins:
                return self._empty_summary()

            total_mcap = sum((c.market_cap or 0) for c in coins)
            total_vol = sum((c.total_volume or 0) for c in coins)

            btc = next((c for c in coins if (c.symbol or '').upper() == 'BTC'), None)
            eth = next((c for c in coins if (c.symbol or '').upper() == 'ETH'), None)

            btc_dom = ((btc.market_cap or 0) / total_mcap * 100) if btc and total_mcap else 0
            eth_dom = ((eth.market_cap or 0) / total_mcap * 100) if eth and total_mcap else 0

            weighted = 0.0
            if total_mcap > 0:
                for c in coins:
                    if c.market_cap and c.price_change_percentage_24h:
                        weighted += c.price_change_percentage_24h * (c.market_cap / total_mcap)

            return {
                'total_market_cap': total_mcap,
                'total_volume': total_vol,
                'btc_dominance': btc_dom,
                'eth_dominance': eth_dom,
                'active_cryptocurrencies': len(coins),
                'market_cap_change_24h': weighted,
                'source': 'database',
            }
        except Exception as e:
            print(f"[global] db calc error: {e}")
            return self._empty_summary()

    @staticmethod
    def _empty_summary():
        return {
            'total_market_cap': 0,
            'total_volume': 0,
            'btc_dominance': 0,
            'eth_dominance': 0,
            'active_cryptocurrencies': 0,
            'market_cap_change_24h': 0,
            'source': 'empty',
        }
