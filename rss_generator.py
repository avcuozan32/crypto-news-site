from datetime import datetime

from database import Article
from config import Config


class RSSGenerator:
    """RSS beslemeleri üretir (ana, kategori, breaking, Google News)"""

    @staticmethod
    def _esc(text):
        if not text:
            return ""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))

    @staticmethod
    def _build_rss(articles, title, description, link, self_url):
        now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

        rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
        rss += '<rss version="2.0" '
        rss += 'xmlns:atom="http://www.w3.org/2005/Atom" '
        rss += 'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        rss += 'xmlns:media="http://search.yahoo.com/mrss/" '
        rss += 'xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
        rss += '<channel>\n'
        rss += '  <title>' + RSSGenerator._esc(title) + '</title>\n'
        rss += '  <link>' + link + '</link>\n'
        rss += '  <description>' + RSSGenerator._esc(description) + '</description>\n'
        rss += '  <language>en-us</language>\n'
        rss += '  <lastBuildDate>' + now + '</lastBuildDate>\n'
        rss += '  <ttl>15</ttl>\n'
        rss += '  <atom:link href="' + self_url + '" rel="self" type="application/rss+xml"/>\n'

        for a in articles:
            url = Config.SITE_URL + '/article/' + a.slug
            pub = a.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")

            rss += '  <item>\n'
            rss += '    <title><![CDATA[' + (a.title or '') + ']]></title>\n'
            rss += '    <link>' + url + '</link>\n'
            rss += '    <guid isPermaLink="true">' + url + '</guid>\n'
            rss += '    <pubDate>' + pub + '</pubDate>\n'
            rss += '    <dc:creator>' + RSSGenerator._esc(a.author) + '</dc:creator>\n'
            rss += '    <description><![CDATA[' + (a.summary or a.title or '') + ']]></description>\n'
            rss += '    <category>' + RSSGenerator._esc(a.category) + '</category>\n'

            if a.image_url:
                rss += '    <media:content url="' + RSSGenerator._esc(a.image_url) + '" medium="image"/>\n'
                rss += '    <media:thumbnail url="' + RSSGenerator._esc(a.image_url) + '"/>\n'

            rss += '  </item>\n'

        rss += '</channel>\n</rss>'
        return rss

    @staticmethod
    def generate_main_feed(app, limit=50):
        with app.app_context():
            articles = (Article.query
                        .filter_by(is_published=True)
                        .order_by(Article.created_at.desc())
                        .limit(limit).all())
            return RSSGenerator._build_rss(
                articles,
                Config.SITE_NAME,
                Config.SITE_DESCRIPTION,
                Config.SITE_URL,
                Config.SITE_URL + '/rss')

    @staticmethod
    def generate_category_feed(category, app, limit=30):
        names = {
            'bitcoin': 'Bitcoin News',
            'ethereum': 'Ethereum News',
            'defi': 'DeFi News',
            'nft': 'NFT News',
            'market': 'Market Analysis',
            'web3': 'Web3 News',
            'regulation': 'Crypto Regulation',
            'altcoins': 'Altcoin News',
            'security': 'Security News',
            'exchange': 'Exchange News',
            'news': 'Latest News',
        }
        with app.app_context():
            articles = (Article.query
                        .filter_by(is_published=True, category=category)
                        .order_by(Article.created_at.desc())
                        .limit(limit).all())
            cat_name = names.get(category, category.title())
            return RSSGenerator._build_rss(
                articles,
                cat_name + ' | ' + Config.SITE_NAME,
                'Latest ' + cat_name + ' from ' + Config.SITE_NAME,
                Config.SITE_URL + '/category/' + category,
                Config.SITE_URL + '/rss/' + category)

    @staticmethod
    def generate_breaking_feed(app, limit=20):
        with app.app_context():
            articles = (Article.query
                        .filter_by(is_published=True, is_breaking=True)
                        .order_by(Article.created_at.desc())
                        .limit(limit).all())
            return RSSGenerator._build_rss(
                articles,
                'Breaking News | ' + Config.SITE_NAME,
                'Breaking cryptocurrency news from ' + Config.SITE_NAME,
                Config.SITE_URL,
                Config.SITE_URL + '/rss/breaking')

    @staticmethod
    def generate_google_news_feed(app, limit=100):
        with app.app_context():
            articles = (Article.query
                        .filter_by(is_published=True)
                        .order_by(Article.created_at.desc())
                        .limit(limit).all())
            now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

            rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
            rss += '<rss version="2.0" '
            rss += 'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            rss += 'xmlns:media="http://search.yahoo.com/mrss/" '
            rss += 'xmlns:atom="http://www.w3.org/2005/Atom" '
            rss += 'xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
            rss += '<channel>\n'
            rss += '  <title>' + RSSGenerator._esc(Config.SITE_NAME) + '</title>\n'
            rss += '  <link>' + Config.SITE_URL + '</link>\n'
            rss += '  <description>' + RSSGenerator._esc(Config.SITE_DESCRIPTION) + '</description>\n'
            rss += '  <language>en-us</language>\n'
            rss += '  <lastBuildDate>' + now + '</lastBuildDate>\n'
            rss += '  <ttl>15</ttl>\n'
            rss += '  <atom:link href="' + Config.SITE_URL + '/rss/google-news" rel="self" type="application/rss+xml"/>\n'

            for a in articles:
                url = Config.SITE_URL + '/article/' + a.slug
                pub = a.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")

                rss += '  <item>\n'
                rss += '    <title><![CDATA[' + (a.title or '') + ']]></title>\n'
                rss += '    <link>' + url + '</link>\n'
                rss += '    <guid isPermaLink="true">' + url + '</guid>\n'
                rss += '    <pubDate>' + pub + '</pubDate>\n'
                rss += '    <dc:creator>' + RSSGenerator._esc(a.author) + '</dc:creator>\n'
                rss += '    <description><![CDATA[' + (a.summary or '') + ']]></description>\n'
                rss += '    <content:encoded><![CDATA[' + (a.content or '') + ']]></content:encoded>\n'
                rss += '    <category>' + RSSGenerator._esc(a.category) + '</category>\n'

                try:
                    for tag in a.get_tags()[:5]:
                        rss += '    <category>' + RSSGenerator._esc(tag) + '</category>\n'
                except Exception:
                    pass

                if a.image_url:
                    rss += '    <media:content url="' + RSSGenerator._esc(a.image_url) + '" medium="image"/>\n'
                    rss += '    <media:thumbnail url="' + RSSGenerator._esc(a.image_url) + '"/>\n'

                rss += '  </item>\n'

            rss += '</channel>\n</rss>'
            return rss
