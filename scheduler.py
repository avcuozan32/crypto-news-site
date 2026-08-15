from apscheduler.schedulers.background import BackgroundScheduler
from price_tracker import PriceTracker
from auto_news import AutoNewsCollector, PriceAlertNewsGenerator, MarketSummaryGenerator
from whale_tracker import WhaleTracker

price_tracker = PriceTracker()
news_collector = AutoNewsCollector()
price_news_gen = PriceAlertNewsGenerator()
market_summary_gen = MarketSummaryGenerator()
whale_tracker = WhaleTracker()


def setup_scheduler(app):
    scheduler = BackgroundScheduler()

    def update_prices_job():
        try:
            alerts = price_tracker.update_prices(app)
            if alerts:
                price_news_gen.generate_price_alert_news(alerts, app)
                print(f"⚠️ {len(alerts)} price alerts generated")
        except Exception as e:
            print(f"Price update error: {e}")

    def collect_news_job():
        try:
            news_collector.collect_from_rss(app)
        except Exception as e:
            print(f"News collect error: {e}")

    def daily_summary_job():
        try:
            coins_data = price_tracker.fetch_prices()
            global_data = price_tracker.get_market_summary()
            market_summary_gen.generate_daily_summary(coins_data, global_data, app)
            print("📊 Daily market summary generated")
        except Exception as e:
            print(f"Daily summary error: {e}")

    def whale_tracking_job():
        try:
            whale_tracker.run(app)
            print("🐋 Whale tracking completed")
        except Exception as e:
            print(f"Whale tracking error: {e}")

    scheduler.add_job(
        update_prices_job,
        'interval',
        minutes=5,
        id='price_update'
    )

    scheduler.add_job(
        collect_news_job,
        'interval',
        minutes=15,
        id='news_collect'
    )

    scheduler.add_job(
        daily_summary_job,
        'cron',
        hour=0,
        minute=5,
        id='daily_summary'
    )

    scheduler.add_job(
        whale_tracking_job,
        'interval',
        minutes=30,
        id='whale_tracking'
    )

    scheduler.start()
    print("✅ Scheduler started successfully")
    return scheduler
