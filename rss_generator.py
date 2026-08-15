from flask import Response
from database import Article
from config import Config
from datetime import datetime
import xml.etree.ElementTree as ET


class RSSGenerator:
    """
    Farklı kategoriler için RSS beslemeleri üretir.
    Google News, Feedly ve diğer RSS okuyucularla uyumludur.
    """

    @staticmethod
    def generate_main_feed(app, limit=50):
    """Ana RSS beslemesi"""
    with app.app_context():
        articles = (
            Article.query
            .filter_by(is_published=True)
            .order_by(Article.created_at.desc())
            .limit(limit)
            .all()
        )

        rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
        rss += '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:media="http://search.yahoo.com/mrss/">\n'
        rss += '<channel>\n'
        rss += f'  <title>{Config.SITE_NAME}</title>\n'
        rss += f'  <link>{Config.SITE_URL}</link>\n'
        rss += f'  <description>{Config.SITE_DESCRIPTION}</description>\n'
        rss += f'  <language>en-us</language>\n'
        rss += f'  <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>\n'
        rss += f'  <ttl>15</ttl>\n'
        rss += f'  <atom:link href="{Config.SITE_URL}/rss" rel="self" type="application/rss+xml"/>\n'
        rss += f'  <image>\n'
        rss += f'    <url>{Config.SITE_URL}/static/images/logo.png</url>\n'
        rss += f'    <title>{Config.SITE_NAME}</title>\n'
        rss += f'    <link>{Config.SITE_URL}</link>\n'
        rss += f'  </image>\n'

        for article in articles:
            url = f"{Config.SITE_URL}/article/{article.slug}"
            pub_date = article.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")
            title_safe = article.title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            summary_safe = (article.summary or "").replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            rss += '  <item>\n'
            rss += f'    <title><![CDATA[{title_safe}]]></title>\n'
            rss += f'    <link>{url}</link>\n'
            rss += f'    <guid isPermaLink="true">{url}</guid>\n'
            rss += f'    <pubDate>{pub_date}</pubDate>\n'
            rss += f'    <description><![CDATA[{summary_safe}]]></description>\n'
            rss += f'    <content:encoded><![CDATA[{article.content}]]></content:encoded>\n'
            rss += f'    <category>{article.category}</category>\n'

            if article.image_url:
                rss += f'    <media:content url="{article.image_url}" medium="image"/>\n'
                rss += f'    <media:thumbnail url="{article.image_url}"/>\n'

            rss += '  </item>\n'

        rss += '</channel>\n</rss>'
        return rss

    @staticmethod
    def generate_category_feed(category, app, limit=30):
        """Kategori bazlı RSS beslemesi"""
        category_names = {
            'bitcoin': 'Bitcoin News',
            'ethereum': 'Ethereum News',
            'defi': 'DeFi News',
            'nft': 'NFT News',
            'market': 'Market Analysis',
            'web3': 'Web3 News',
            'regulation': 'Crypto Regulation',
            'altcoins': 'Altcoin News',
        }

        with app.app_context():
            articles = (
                Article.query
                .filter_by(is_published=True, category=category)
                .order_by(Article.created_at.desc())
                .limit(limit)
                .all()
            )

            cat_name = category_names.get(category, category.title())
            return RSSGenerator._build_rss(
                articles=articles,
                title=f"{cat_name} | {Config.SITE_NAME}",
                description=f"Latest {cat_name} from {Config.SITE_NAME}",
                link=f"{Config.SITE_URL}/category/{category}",
            )

    @staticmethod
    def generate_google_news_feed(app, limit=100):
        """Google News uyumlu özel RSS beslemesi"""
        with app.app_context():
            articles = (
                Article.query
                .filter_by(is_published=True)
                .order_by(Article.created_at.desc())
                .limit(limit)
                .all()
            )

            rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
            rss += '<rss version="2.0"\n'
            rss += '  xmlns:dc="http://purl.org/dc/elements/1.1/"\n'
            rss += '  xmlns:media="http://search.yahoo.com/mrss/"\n'
            rss += '  xmlns:atom="http://www.w3.org/2005/Atom"\n'
            rss += '  xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
            rss += '<channel>\n'
            rss += f'  <title>{Config.SITE_NAME}</title>\n'
            rss += f'  <link>{Config.SITE_URL}</link>\n'
            rss += f'  <description>{Config.SITE_DESCRIPTION}</description>\n'
            rss += f'  <language>en-us</language>\n'
            rss += f'  <managingEditor>editor@cryptonestnews.com ({Config.SITE_NAME})</managingEditor>\n'
            rss += f'  <webMaster>tech@cryptonestnews.com ({Config.SITE_NAME})</webMaster>\n'
            rss += f'  <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>\n'
            rss += f'  <ttl>15</ttl>\n'
            rss += f'  <atom:link href="{Config.SITE_URL}/rss/google-news" rel="self" type="application/rss+xml"/>\n'

            for article in articles:
                url = f"{Config.SITE_URL}/article/{article.slug}"
                pub_date = article.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")
                tags = article.get_tags()

                rss += '  <item>\n'
                rss += f'    <title><![CDATA[{article.title}]]></title>\n'
                rss += f'    <link>{url}</link>\n'
                rss += f'    <guid isPermaLink="true">{url}</guid>\n'
                rss += f'    <pubDate>{pub_date}</pubDate>\n'
                rss += f'    <dc:creator>{article.author}</dc:creator>\n'
                rss += f'    <description><![CDATA[{article.summary or ""}]]></description>\n'
                rss += f'    <content:encoded><![CDATA[{article.content}]]></content:encoded>\n'
                rss += f'    <category>{article.category}</category>\n'

                for tag in tags[:5]:
                    rss += f'    <category>{tag}</category>\n'

                if article.image_url:
                    rss += f'    <media:content url="{article.image_url}" medium="image"/>\n'
                    rss += f'    <media:thumbnail url="{article.image_url}"/>\n'

                rss += '  </item>\n'

            rss += '</channel>\n</rss>'
            return rss

    @staticmethod
    def generate_breaking_feed(app, limit=20):
        """Sadece son dakika haberlerinin RSS'i"""
        with app.app_context():
            articles = (
                Article.query
                .filter_by(is_published=True, is_breaking=True)
                .order_by(Article.created_at.desc())
                .limit(limit)
                .all()
            )
            return RSSGenerator._build_rss(
                articles=articles,
                title=f"Breaking News | {Config.SITE_NAME}",
                description=f"Breaking cryptocurrency news from {Config.SITE_NAME}",
                link=f"{Config.SITE_URL}/breaking",
            )

    @staticmethod
    def _build_rss(articles, title, description, link):
        """Temel RSS XML oluştur"""
        rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
        rss += '<rss version="2.0" '
        rss += 'xmlns:atom="http://www.w3.org/2005/Atom" '
        rss += 'xmlns:media="http://search.yahoo.com/mrss/">\n'
        rss += '<channel>\n'
        rss += f'  <title>{title}</title>\n'
        rss += f'  <link>{link}</link>\n'
        rss += f'  <description>{description}</description>\n'
        rss += f'  <language>en-us</language>\n'
        rss += f'  <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>\n'
        rss += f'  <ttl>15</ttl>\n'
        rss += f'  <atom:link href="{link}/feed" rel="self" type="application/rss+xml"/>\n'

        for article in articles:
            url = f"{Config.SITE_URL}/article/{article.slug}"
            pub_date = article.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")

            rss += '  <item>\n'
            rss += f'    <title><![CDATA[{article.title}]]></title>\n'
            rss += f'    <link>{url}</link>\n'
            rss += f'    <guid isPermaLink="true">{url}</guid>\n'
            rss += f'    <pubDate>{pub_date}</pubDate>\n'
            rss += f'    <description><![CDATA[{article.summary or ""}]]></description>\n'
            rss += f'    <category>{article.category}</category>\n'
            if article.image_url:
                rss += f'    <media:thumbnail url="{article.image_url}"/>\n'
            rss += '  </item>\n'

        rss += '</channel>\n</rss>'
        return rss
