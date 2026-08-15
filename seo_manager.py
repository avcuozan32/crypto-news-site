from datetime import datetime
from database import Article
from config import Config


class SEOManager:
    @staticmethod
    def generate_sitemap(app):
        with app.app_context():
            articles = Article.query.filter_by(is_published=True).order_by(Article.created_at.desc()).all()

            xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            xml += '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'

            # Ana sayfa
            xml += f"""
            <url>
                <loc>{Config.SITE_URL}/</loc>
                <changefreq>hourly</changefreq>
                <priority>1.0</priority>
            </url>\n"""

            # Market sayfası
            xml += f"""
            <url>
                <loc>{Config.SITE_URL}/market</loc>
                <changefreq>always</changefreq>
                <priority>0.9</priority>
            </url>\n"""

            # Makaleler
            for article in articles:
                xml += f"""
            <url>
                <loc>{Config.SITE_URL}/article/{article.slug}</loc>
                <lastmod>{article.updated_at.strftime('%Y-%m-%dT%H:%M:%S+00:00')}</lastmod>
                <changefreq>daily</changefreq>
                <priority>0.8</priority>
                <news:news>
                    <news:publication>
                        <news:name>{Config.SITE_NAME}</news:name>
                        <news:language>{Config.SITE_LANGUAGE}</news:language>
                    </news:publication>
                    <news:publication_date>{article.created_at.strftime('%Y-%m-%dT%H:%M:%S+00:00')}</news:publication_date>
                    <news:title>{article.title}</news:title>
                </news:news>
            </url>\n"""

            xml += '</urlset>'
            return xml

    @staticmethod
    def generate_rss(app):
        with app.app_context():
            articles = Article.query.filter_by(is_published=True).order_by(Article.created_at.desc()).limit(50).all()

            rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
            rss += '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
            rss += '<channel>\n'
            rss += f'  <title>{Config.SITE_NAME}</title>\n'
            rss += f'  <link>{Config.SITE_URL}</link>\n'
            rss += f'  <description>{Config.SITE_DESCRIPTION}</description>\n'
            rss += f'  <language>{Config.SITE_LANGUAGE}</language>\n'
            rss += f'  <atom:link href="{Config.SITE_URL}/rss" rel="self" type="application/rss+xml"/>\n'

            for article in articles:
                rss += '  <item>\n'
                rss += f'    <title><![CDATA[{article.title}]]></title>\n'
                rss += f'    <link>{Config.SITE_URL}/article/{article.slug}</link>\n'
                rss += f'    <description><![CDATA[{article.summary or article.title}]]></description>\n'
                rss += f'    <pubDate>{article.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>\n'
                rss += f'    <guid>{Config.SITE_URL}/article/{article.slug}</guid>\n'
                rss += f'    <category>{article.category}</category>\n'
                rss += '  </item>\n'

            rss += '</channel>\n</rss>'
            return rss

    @staticmethod
    def generate_robots_txt():
        return f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/

Sitemap: {Config.SITE_URL}/sitemap.xml
"""