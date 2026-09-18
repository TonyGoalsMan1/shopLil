"""
MarketerAgent (Маркетолог) — полный маркетинг: SEO, SMM, email, реклама, аналитика
Анализирует сайт, генерирует контент и воронку
"""
import json, re
from pathlib import Path
from datetime import datetime
from base import Agent

class MarketerAgent(Agent):
    name = "MarketerAgent"
    interval_hours = 12

    def run(self):
        site = self.site_root
        # 1. SEO аудит
        seo = {}
        for tpl in ["shop.html","about.html"]:
            p = site / "templates" / tpl
            if p.exists():
                t = p.read_text(encoding="utf-8")
                seo[tpl] = {
                    "has_title": "<title>" in t,
                    "has_meta_desc": 'meta name="description"' in t,
                    "has_h1": "<h1" in t,
                    "has_og": "og:" in t
                }
        # генерируем sitemap
        sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://lylili.love/</loc><priority>1.0</priority></url>
  <url><loc>https://lylili.love/about/</loc><priority>0.8</priority></url>
  <url><loc>https://lylili.love/cart/</loc><priority>0.5</priority></url>
  <url><loc>https://lylili.love/checkout/</loc><priority>0.6</priority></url>
</urlset>
"""
        (site / "static" / "sitemap.xml").write_text(sitemap, encoding="utf-8")
        # 2. Email кампания
        emails = {
            "welcome": {"subject":"Добро пожаловать в LYLILI 🩷 — твой подарок внутри", "body":"Привет! Твой первый gift — скидка 10% PROMO: LYLILI10. Открой https://lylili.love/ — подарки как в Telegram уже ждут."},
            "abandoned_cart": {"subject":"Твоя корзина скучает 🎁", "body":"Ты оставила подарки в корзине — вернись и получи free доставку! https://lylili.love/cart"},
            "new_drop": {"subject":"Новый дроп: Unicorn Aurora 🦄 — 59€ legendary", "body":"Только 500 штук. 3D подиум, голографик. Успей! https://lylili.love/"},
        }
        (Path(__file__).parent / "memory" / "emails.json").write_text(json.dumps(emails, ensure_ascii=False, indent=2), encoding="utf-8")
        # 3. SMM план
        smm = [
            {"platform":"Instagram Reels","idea":"Распаковка подарка с конфетти — 15 сек","cta":"Link in bio","hashtag":"#lylili #telegramgifts"},
            {"platform":"TikTok","idea":"До/После: в обычных шортах vs LYLILI","cta":"Shop now","hashtag":"#gift #premium"},
            {"platform":"Telegram Channel","idea":"Анонс легендарного Diamond Prism 💎","cta":"Send Gift 89€","hashtag":""},
        ]
        # 4. Реклама
        ads = [
            {"channel":"Meta Ads","audience":"18-28 девушки, интересы: fashion, gifts","creative":"Карусель 3D подарков + UGC","budget":"20€/day","kpi":"CTR 2.5%, CPA 12€"},
            {"channel":"Yandex Direct","audience":"подарки девушке","creative":"Поиск: 'подарок как в телеграм'","budget":"15€/day","kpi":"CR 3%"},
        ]
        # 5. Воронка
        funnel = {
            "awareness": "SMM + Awwwards + Telegram Gifts хайп",
            "interest": "Shop 3D подарки с редкостью",
            "desire": "Cart + чат AI + premium упаковка",
            "action": "Checkout 3D Secure → Success",
            "retention": "Email + повторные дропы"
        }
        # 6. Добавляем OG теги если нет
        for tpl in [site / "templates" / "shop.html", site / "templates" / "about.html"]:
            if tpl.exists():
                t = tpl.read_text(encoding="utf-8")
                if 'property="og:' not in t:
                    og = '  <meta property="og:title" content="LYLILI Telegram Gifts — Premium 4K">\n  <meta property="og:description" content="Коллекционные подарки как в Telegram, 3D подиум, 4K качество, worldwide">\n  <meta property="og:image" content="/static/img/og.jpg">'
                    t = t.replace("</title>", "</title>\n"+og)
                    tpl.write_text(t, encoding="utf-8")

        report = {
            "time": datetime.now().isoformat(),
            "seo": seo,
            "sitemap": "static/sitemap.xml generated",
            "emails": emails,
            "smm": smm,
            "ads": ads,
            "funnel": funnel,
            "kpi_target": {"month_1_orders": 120, "aov": 58, "revenue": 6960, "retention": "22%"}
        }
        out = Path(__file__).parent / "memory" / "marketing.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.log("SUCCESS", f"marketing ready: {len(emails)} emails, {len(smm)} smm, {len(ads)} ads")
        self.save_state(report)
        return report
