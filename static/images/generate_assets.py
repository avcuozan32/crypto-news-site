"""
Bu script logo.png ve favicon.ico dosyalarını üretir.
Çalıştırmak için: python static/images/generate_assets.py
Gereksinim: pip install Pillow
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not installed. Run: pip install Pillow")

import os
import base64


def create_logo_svg():
    """SVG logo üret"""
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="100" viewBox="0 0 400 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
        </linearGradient>
    </defs>

    <!-- Arka plan (transparent) -->

    <!-- Yıldırım ikonu -->
    <circle cx="45" cy="50" r="38" fill="url(#grad1)"/>
    <polygon points="52,15 30,55 45,55 38,85 62,45 47,45" fill="white"/>

    <!-- Site adı -->
    <text x="95" y="42" font-family="Arial, sans-serif" font-size="28"
          font-weight="800" fill="#0f172a">CryptoNest</text>
    <text x="95" y="72" font-family="Arial, sans-serif" font-size="28"
          font-weight="800" fill="#6366f1">News</text>

    <!-- Küçük slogan -->
    <text x="95" y="90" font-family="Arial, sans-serif" font-size="11"
          fill="#64748b">Your Trusted Crypto Source</text>
</svg>'''

    with open('static/images/logo.svg', 'w') as f:
        f.write(svg_content)
    print("✅ logo.svg created")
    return svg_content


def create_favicon_svg():
    """SVG favicon üret"""
    favicon_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#6366f1"/>
            <stop offset="100%" style="stop-color:#8b5cf6"/>
        </linearGradient>
    </defs>
    <rect width="32" height="32" rx="6" fill="url(#bg)"/>
    <polygon points="18,4 10,18 15,18 14,28 22,14 17,14" fill="white"/>
</svg>'''

    with open('static/images/favicon.svg', 'w') as f:
        f.write(favicon_svg)
    print("✅ favicon.svg created")
    return favicon_svg


def create_logo_png():
    """PNG logo üret (Pillow ile)"""
    if not PIL_AVAILABLE:
        print("❌ Pillow not available. Using SVG instead.")
        return

    # Ana logo (400x100)
    img = Image.new('RGBA', (400, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gradient daire (yıldırım ikonu arka planı)
    for i in range(76):
        r = int(99 + (139 - 99) * i / 76)
        g = int(102 + (92 - 102) * i / 76)
        b = int(241 + (246 - 241) * i / 76)
        draw.ellipse([5 + i//2, 5 + i//2, 85 - i//2, 95 - i//2],
                     fill=(r, g, b, 255))

    # Yıldırım
    lightning = [(45, 8), (25, 52), (42, 52), (35, 92), (62, 48), (45, 48)]
    draw.polygon(lightning, fill=(255, 255, 255, 255))

    # Metin (font olmadan basit çizgi)
    # Not: Gerçek font için system font path gerekir
    try:
        font_large = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 30)
        font_small = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 12)
    except:
        try:
            font_large = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30
            )
            font_small = ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12
            )
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

    draw.text((95, 10), "CryptoNest", font=font_large, fill=(15, 23, 42, 255))
    draw.text((95, 45), "News", font=font_large, fill=(99, 102, 241, 255))
    draw.text((95, 80), "Your Trusted Crypto Source",
              font=font_small, fill=(100, 116, 139, 255))

    img.save('static/images/logo.png', 'PNG')
    print("✅ logo.png created (400x100)")

    # OG Image (1200x630)
    og_img = Image.new('RGB', (1200, 630), (15, 23, 42))
    og_draw = ImageDraw.Draw(og_img)

    # Gradient arka plan efekti
    for y in range(630):
        r = int(15 + (30 - 15) * y / 630)
        g = int(23 + (41 - 23) * y / 630)
        b = int(42 + (65 - 42) * y / 630)
        og_draw.line([(0, y), (1200, y)], fill=(r, g, b))

    # Büyük metin
    try:
        font_title = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 80)
        font_sub = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 30)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    og_draw.text((100, 200), "⚡ CryptoNestNews",
                  font=font_title, fill=(255, 255, 255))
    og_draw.text((100, 350), "Your trusted source for crypto news,",
                  font=font_sub, fill=(148, 163, 184))
    og_draw.text((100, 400), "market analysis & blockchain updates",
                  font=font_sub, fill=(148, 163, 184))

    og_img.save('static/images/og-default.jpg', 'JPEG', quality=90)
    print("✅ og-default.jpg created (1200x630)")


def create_favicon_ico():
    """ICO favicon üret"""
    if not PIL_AVAILABLE:
        print("❌ Pillow not available for ICO. Using SVG instead.")
        return

    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    images = []

    for size in sizes:
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Mor daire arka plan
        draw.ellipse([0, 0, size[0] - 1, size[1] - 1], fill=(99, 102, 241, 255))

        # Yıldırım (ölçeklenmiş)
        s = size[0]
        lightning = [
            (s * 0.56, s * 0.12),
            (s * 0.31, s * 0.56),
            (s * 0.47, s * 0.56),
            (s * 0.44, s * 0.88),
            (s * 0.69, s * 0.44),
            (s * 0.53, s * 0.44),
        ]
        lightning = [(int(x), int(y)) for x, y in lightning]
        draw.polygon(lightning, fill=(255, 255, 255, 255))

        images.append(img)

    images[1].save(
        'static/images/favicon.ico',
        format='ICO',
        sizes=sizes
    )
    print("✅ favicon.ico created")


def create_placeholder_image():
    """Varsayılan makale görseli üret"""
    if not PIL_AVAILABLE:
        return

    img = Image.new('RGB', (800, 450), (30, 41, 59))
    draw = ImageDraw.Draw(img)

    # Gradient efekt
    for y in range(450):
        shade = int(30 + (50 - 30) * y / 450)
        draw.line([(0, y), (800, y)], fill=(shade, shade + 11, shade + 29))

    # Logo metni ortada
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 48)
    except:
        font = ImageFont.load_default()

    draw.text((400, 200), "⚡ CryptoNestNews",
              font=font, fill=(99, 102, 241), anchor='mm')
    draw.text((400, 270), "Crypto News & Analysis",
              font=font, fill=(100, 116, 139), anchor='mm')

    img.save('static/images/placeholder.jpg', 'JPEG', quality=85)
    print("✅ placeholder.jpg created")


def create_all_assets():
    """Tüm görsel dosyaları oluştur"""
    os.makedirs('static/images', exist_ok=True)

    print("🎨 Creating visual assets...")

    # SVG dosyaları (her zaman oluştur)
    create_logo_svg()
    create_favicon_svg()

    # PNG/ICO dosyaları (Pillow varsa)
    if PIL_AVAILABLE:
        create_logo_png()
        create_favicon_ico()
        create_placeholder_image()
    else:
        print("ℹ️  Install Pillow for PNG/ICO: pip install Pillow")
        print("ℹ️  SVG files can be used as alternatives")
        # Pillow olmadan basit PNG'ler oluştur (base64)
        create_minimal_assets()

    print("✅ All assets created!")


def create_minimal_assets():
    """Pillow olmadan minimal PNG/ICO üret (base64 encoded)"""
    # 1x1 şeffaf PNG
    minimal_png = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
    )

    # Placeholder olarak kaydet
    for filename in ['logo.png', 'favicon.ico', 'placeholder.jpg', 'og-default.jpg']:
        if not os.path.exists(f'static/images/{filename}'):
            with open(f'static/images/{filename}', 'wb') as f:
                f.write(minimal_png)
            print(f"📄 Created minimal {filename}")


if __name__ == '__main__':
    create_all_assets()