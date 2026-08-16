import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class ImageHelper:
    # Kategori bazlı yüksek çözünürlüklü ve telifsiz Unsplash kripto/finans görselleri
    FALLBACK_IMAGES = {
        'bitcoin': 'https://images.unsplash.com/photo-1516245834210-c4c142787335?auto=format&fit=crop&w=800&q=80',
        'ethereum': 'https://images.unsplash.com/photo-1621761191319-c6fb62004040?auto=format&fit=crop&w=800&q=80',
        'altcoins': 'https://images.unsplash.com/photo-1622630998477-20aa696ecb05?auto=format&fit=crop&w=800&q=80',
        'market': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80',
        'defi': 'https://images.unsplash.com/photo-1639762681485-074b7f938ba0?auto=format&fit=crop&w=800&q=80',
        'nft': 'https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?auto=format&fit=crop&w=800&q=80',
        'web3': 'https://images.unsplash.com/photo-1639762681057-408e52192e55?auto=format&fit=crop&w=800&q=80',
        'security': 'https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=800&q=80',
        'regulation': 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80',
        'exchange': 'https://images.unsplash.com/photo-1642104704074-907c0698cbd9?auto=format&fit=crop&w=800&q=80',
        'technology': 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80',
        'news': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80'
    }

    @classmethod
    def get_fallback_image(cls, category):
        """Kategoriye uygun yedek görsel URL'i döner"""
        category = (category or '').lower()
        return cls.FALLBACK_IMAGES.get(category, cls.FALLBACK_IMAGES['news'])

    @classmethod
    def resolve_image(cls, rss_image=None, source_url=None, category=None, article_id=None):
        """
        Görsel çözümleme mantığı:
        1. Eğer geçerli bir RSS görseli varsa onu kullan.
        2. RSS görseli yoksa haber kaynağı URL'ine gidip 'og:image' meta etiketini çekmeyi dene.
        3. O da başarısız olursa kategorisine göre harika bir stok görsel ata.
        """
        # 1. RSS'ten gelen resmi kontrol et
        if rss_image and rss_image.startswith('http'):
            return rss_image

        # 2. Kaynak siteden og:image çekmeyi dene
        if source_url and source_url.startswith('http'):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                # Sitenin çökmesini engellemek için max 3 saniye bekle
                response = requests.get(source_url, headers=headers, timeout=3)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # og:image (Facebook/OpenGraph) etiketini ara
                    meta_og = soup.find('meta', property='og:image') or soup.find('meta', attrs={"name": "og:image"})
                    if meta_og and meta_og.get('content'):
                        img_url = meta_og['content']
                        # Eğer relative path ise absolute url'e çevir
                        return urljoin(source_url, img_url)

                    # twitter:image etiketini ara
                    meta_tw = soup.find('meta', attrs={"name": "twitter:image"}) or soup.find('meta', property='twitter:image')
                    if meta_tw and meta_tw.get('content'):
                        img_url = meta_tw['content']
                        return urljoin(source_url, img_url)
            except Exception as e:
                # Herhangi bir bağlantı veya parsing hatasında programın çökmemesini sağla
                print(f"[ImageHelper] Meta image extraction failed for {source_url}: {e}")

        # 3. Hiçbiri olmazsa kategoriye göre yedek görsel döndür
        return cls.get_fallback_image(category)