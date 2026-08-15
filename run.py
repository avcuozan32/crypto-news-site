#!/usr/bin/env python3
"""
CryptoNestNews - Ana başlatma scripti
Çalıştır: python run.py
"""

import os
import sys

def check_requirements():
    """Gereksinimleri kontrol et"""
    required = [
        'flask', 'flask_sqlalchemy', 'requests',
        'feedparser', 'apscheduler', 'bs4', 'slugify'
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

def setup_directories():
    """Gerekli klasörleri oluştur"""
    dirs = ['data', 'static/images', 'static/css', 'static/js', 'templates']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def main():
    print("=" * 50)
    print("⚡ CryptoNestNews Starting...")
    print("=" * 50)

    check_requirements()
    setup_directories()

    # Görsel dosyaları üret
    if not os.path.exists('static/images/logo.svg'):
        print("🎨 Generating visual assets...")
        os.system('python static/images/generate_assets.py')

    # Veritabanını başlat
    if not os.path.exists('data/crypto_news.db'):
        print("🗄️  Initializing database...")
        os.system('python init_database.py')

    # Uygulamayı başlat
    from app import app
    from scheduler import setup_scheduler

    scheduler = setup_scheduler(app)

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    print(f"\n✅ Server starting on http://localhost:{port}")
    print(f"📰 Auto news collection: every 15 minutes")
    print(f"💹 Price updates: every 5 minutes")
    print(f"🐋 Whale tracking: every 30 minutes")
    print(f"\nPress CTRL+C to stop\n")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=False  # Scheduler ile çakışmayı önler
    )


if __name__ == '__main__':
    main()