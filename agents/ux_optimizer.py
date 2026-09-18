"""
UXOptimizerAgent — анализирует доступность, скорость, SEO и фиксит
"""
import re
import json
from pathlib import Path
from base import Agent

class UXOptimizerAgent(Agent):
    name = "UXOptimizerAgent"
    interval_hours = 24

    def run(self):
        fixes = []
        # 1. Проверка доступности: alt, aria, контраст
        for tpl in (self.site_root / "templates").glob("*.html"):
            html = tpl.read_text(encoding="utf-8")
            orig = html
            # добавляем aria-label для кнопок без текста
            if 'aria-label' not in html and '<button' in html:
                html = html.replace('<button', '<button aria-label="action"')
                fixes.append(f"{tpl.name}: added aria-label")
            # lazy loading для будущих img
            if '<img' in html and 'loading="lazy"' not in html:
                html = html.replace('<img', '<img loading="lazy"')
                fixes.append(f"{tpl.name}: lazy loading")
            if html != orig:
                tpl.write_text(html, encoding="utf-8")

        # 2. Performance: минифицируем CSS (удаляем комменты и лишние пробелы) — делаем копию .min.css
        css = self.site_root / "static" / "css" / "style.css"
        if css.exists():
            text = css.read_text(encoding="utf-8")
            minified = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
            minified = re.sub(r"\s+", " ", minified)
            minified = re.sub(r"\s*([{}:;,])\s*", r"\1", minified)
            out = self.site_root / "static" / "css" / "style.min.css"
            out.write_text(minified, encoding="utf-8")
            fixes.append(f"minified CSS {len(text)} -> {len(minified)} bytes ({len(minified)/len(text):.0%})")

        # 3. SEO: проверяем title/description
        shop = self.site_root / "templates" / "shop.html"
        if shop.exists():
            html = shop.read_text(encoding="utf-8")
            if '<meta name="description"' not in html:
                inject = '<meta name="description" content="LYLILI Telegram Gifts — collectible 3D animated gifts, limited 2026">'
                html = html.replace("</title>", "</title>\n  " + inject)
                shop.write_text(html, encoding="utf-8")
                fixes.append("added meta description")

        self.log("INFO", f"UX fixes: {fixes}")
        self.save_state({"fixes": fixes})
        return {"fixes": fixes}
