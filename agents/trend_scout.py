"""
TrendScoutAgent — автономно сканирует интернет на предмет крутого дизайна
Источники: Awwwards, Dribbble, Linear, Stripe, Telegram Gifts, Glassmorphism 2026
Пишет отчет в memory/trends.json
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
from base import Agent

TREND_SOURCES = [
    ("Awwwards 2026", "https://www.awwwards.com/websites/"),
    ("Linear App", "https://linear.app/features"),
    ("Stripe Design", "https://stripe.com/"),
    ("Telegram Blog Gifts", "https://telegram.org/blog/gifts-and-stars"),
    ("Vercel Design", "https://vercel.com/geist/introduction"),
    ("Apple 4K", "https://www.apple.com/iphone/"),
    ("Dribbble Popular", "https://dribbble.com/shots/popular"),
    ("Awwwards 4K Sites", "https://www.awwwards.com/collections/4k/"),
    ("Figma Community", "https://www.figma.com/community"),
    ("Notion Design", "https://www.notion.so/"),
]

HEADERS = {"User-Agent": "LYLILI-Scout/1.0 (+https://lylili.love)"}

class TrendScoutAgent(Agent):
    name = "TrendScoutAgent"
    interval_hours = 3

    def fetch(self, url):
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            r.raise_for_status()
            return r.text
        except Exception as e:
            self.log("WARN", f"fetch failed {url}: {e}")
            return ""

    def extract_signals(self, html: str):
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)[:8000]
        # эвристики: ищем модные ключевые слова 2026 + 4K
        keywords = ["glass", "3D", "neomorphism", "aurora", "gradient", "bento", "glassmorphism", "neumorphism", "micro-interaction", "parallax", "gift", "collectible", "glow", "blur", "mesh gradient", "dark mode", "motion", "4K", "retina", "crisp", "8K", "ultra", "hdr", "depth", "spatial"]
        found = [k for k in keywords if k.lower() in text.lower()]
        # вытаскиваем цвета из style
        colors = re.findall(r"#[0-9a-fA-F]{3,6}|rgba?\([^)]+\)", html)[:12]
        title = soup.title.string.strip() if soup.title else ""
        return {"found_keywords": found, "colors": colors, "title": title, "text_snippet": text[:500]}

    def run(self):
        trends = []
        for name, url in TREND_SOURCES:
            html = self.fetch(url)
            if not html:
                continue
            sig = self.extract_signals(html)
            trends.append({"source": name, "url": url, **sig})
            self.log("INFO", f"scouted {name}: {sig['found_keywords'][:5]}")

        # локальные эвристики 2026 — добавляем если источники недоступны
        if not trends:
            trends = [{"source": "fallback 2026", "found_keywords": ["glass", "glow", "3D", "bento", "aurora"], "colors": ["#e85a7a", "#7b61ff", "#4facfe"]}]

        # агрегируем топ-тренды
        all_kw = {}
        for t in trends:
            for k in t.get("found_keywords", []):
                all_kw[k] = all_kw.get(k, 0) + 1
        top = sorted(all_kw.items(), key=lambda x: -x[1])[:6]

        report = {
            "top_keywords": top,
            "sources": trends,
            "recommendations": self.make_recommendations(top)
        }
        out = Path(__file__).parent / "memory" / "trends.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.save_state(report)
        return report

    def make_recommendations(self, top):
        recs = []
        kw = [k for k,_ in top]
        if any(x in kw for x in ["glass", "glassmorphism", "blur"]):
            recs.append("Усилить glassmorphism: backdrop-filter 20px, полупрозрачные бордеры, inner glow")
        if any(x in kw for x in ["3D", "parallax", "glow"]):
            recs.append("Добавить 3D подиумы + параллакс + свечение как у Telegram Gifts — уже есть, усилить tilt до 8deg")
        if "bento" in kw:
            recs.append("Bento-grid для каталога: 2 большие карточки + 4 малые, как у Linear/Stripe")
        if "aurora" in kw or "mesh gradient" in kw:
            recs.append("Aurora mesh градиенты на фоне: radial gradients с анимацией hue-rotate")
        if "gift" in kw or "collectible" in kw:
            recs.append("Коллекционность: добавить rarity, номер #xxxx, owners, анимацию распаковки")
        recs.append("Micro-interactions: hapticulse, shine, confetti, spring анимации")
        return recs

if __name__ == "__main__":
    from pathlib import Path
    a = TrendScoutAgent(Path(__file__).parent.parent)
    print(json.dumps(a.safe_run(), ensure_ascii=False, indent=2))
