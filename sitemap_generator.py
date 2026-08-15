from database import Article
from config import Config
from datetime import datetime


class SitemapGenerator:
    """
    Google News uyumlu XML Sitemap üretir.
    Ana sitemap, haber sitemap'i ve kategori sitemap'i içerir.
    """

    STATIC_PAGES = [
        {'url': '/', 'priority': '1.0', 'changefreq': 'always'},
        {'url': '/market', 'priority': '0.9', 'changefreq': 'always'},
        {'url': '/category/bitcoin', 'priority': '0.8', 'changefreq': 'hourly'},
        {'url': '/category/ethereum', 'priority': '0.8', 'changefreq': 'hourly'},
        {'url': '/category/altcoins', 'priority': '0.8', 'changefreq': 'hourly'},
        {'url': '/category/defi', 'priority': '0.7', 'changefreq': 'daily'},
        {'url': '/category/nft', 'priority': '0.7', 'changefreq': 'daily'},
        {'url': '/category/web3', 'priority': '0.7', 'changefreq': 'daily'},
        {'url': '/category/regulation', 'priority': '0.7', 'changefreq': 'daily'},
        {'url': '/category/market', 'priority': '0.8', 'changefreq': 'hourly'},
        {'url': '/category/security', 'priority': '0.7', 'changefreq': 'daily'},
        {'url': '/category/exchange', 'priority': '0.7', 'changefreq': 'daily'},
        {'url': '/about', 'priority': '0.5', 'changefreq': 'monthly'},
        {'url': '/privacy', 'priority': '0.4', 'changefreq': 'monthly'},
        {'url': '/disclaimer', 'priority': '0.4', 'changefreq': 'monthly'},
        {'url': '/contact', 'priority': '0.4', 'changefreq': 'monthly'},
    ]

    @staticmethod
    def generate_main_sitemap(app):
        """Ana sitemap (sitemap index)"""
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')

        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<?xml-stylesheet type="text/xsl" href="/static/sitemap.xsl"?>\n'
        xml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        sitemaps = [
            f'{Config.SITE_URL}/sitemap-pages.xml',
            f'{Config.SITE_URL}/sitemap-news.xml',
            f'{Config.SITE_URL}/sitemap-articles.xml',
        ]

        for sitemap_url in sitemaps:
            xml += '  <sitemap>\n'
            xml += f'    <loc>{sitemap_url}</loc>\n'
            xml += f'    <lastmod>{now}</lastmod>\n'
            xml += '  </sitemap>\n'

        xml += '</sitemapindex>'
        return xml

    @staticmethod
    def generate_pages_sitemap():
        """Statik sayfalar sitemap'i"""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        for page in SitemapGenerator.STATIC_PAGES:
            xml += '  <url>\n'
            xml += f'    <loc>{Config.SITE_URL}{page["url"]}</loc>\n'
            xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
            xml += f'    <priority>{page["priority"]}</priority>\n'
            xml += '  </url>\n'

        xml += '</urlset>'
        return xml

    @staticmethod
    def generate_news_sitemap(app):
        """
        Google News Sitemap'i.
        Son 2 gün içindeki haberleri içerir.
        Google News'e başvurmak için gereklidir.
        """
        with app.app_context():
            from datetime import timedelta
            two_days_ago = datetime.utcnow() - timedelta(days=2)

            articles = (
                Article.query
                .filter(
                    Article.is_published == True,
                    Article.created_at >= two_days_ago
                )
                .order_by(Article.created_at.desc())
                .all()
            )

            xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml += '<urlset\n'
            xml += '  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            xml += '  xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"\n'
            xml += '  xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'

            for article in articles:
                url = f"{Config.SITE_URL}/article/{article.slug}"
                pub_date = article.created_at.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                title_safe = article.title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                xml += '  <url>\n'
                xml += f'    <loc>{url}</loc>\n'
                xml += '    <news:news>\n'
                xml += '      <news:publication>\n'
                xml += f'        <news:name>{Config.SITE_NAME}</news:name>\n'
                xml += f'        <news:language>{Config.SITE_LANGUAGE}</news:language>\n'
                xml += '      </news:publication>\n'
                xml += f'      <news:publication_date>{pub_date}</news:publication_date>\n'
                xml += f'      <news:title>{title_safe}</news:title>\n'

                # Etiketler
                tags = article.get_tags()
                if tags:
                    keywords = ', '.join(tags[:10])
                    xml += f'      <news:keywords>{keywords}</news:keywords>\n'

                xml += '    </news:news>\n'

                # Görsel varsa ekle
                if article.image_url:
                    xml += '    <image:image>\n'
                    xml += f'      <image:loc>{article.image_url}</image:loc>\n'
                    xml += f'      <image:title>{title_safe}</image:title>\n'
                    xml += '    </image:image>\n'

                xml += '  </url>\n'

            xml += '</urlset>'
            return xml

    @staticmethod
    def generate_articles_sitemap(app):
        """Tüm makaleler sitemap'i"""
        with app.app_context():
            articles = (
                Article.query
                .filter_by(is_published=True)
                .order_by(Article.created_at.desc())
                .all()
            )

            xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

            for article in articles:
                url = f"{Config.SITE_URL}/article/{article.slug}"
                lastmod = article.updated_at.strftime('%Y-%m-%dT%H:%M:%S+00:00')

                # Eski makaleler için düşük öncelik
                days_old = (datetime.utcnow() - article.created_at).days
                if days_old <= 1:
                    priority = '1.0'
                    changefreq = 'hourly'
                elif days_old <= 7:
                    priority = '0.9'
                    changefreq = 'daily'
                elif days_old <= 30:
                    priority = '0.7'
                    changefreq = 'weekly'
                else:
                    priority = '0.5'
                    changefreq = 'monthly'

                xml += '  <url>\n'
                xml += f'    <loc>{url}</loc>\n'
                xml += f'    <lastmod>{lastmod}</lastmod>\n'
                xml += f'    <changefreq>{changefreq}</changefreq>\n'
                xml += f'    <priority>{priority}</priority>\n'
                xml += '  </url>\n'

            xml += '</urlset>'
            return xml
