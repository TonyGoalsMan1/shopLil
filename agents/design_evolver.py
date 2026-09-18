"""
DesignEvolverAgent — читает trends.json и автономно улучшает CSS
Генерирует 3 варианта темы и применяет лучший, делает бэкап
"""
import json
import random
import shutil
from pathlib import Path
from datetime import datetime
from base import Agent

VARIANTS = {
    "aurora": {"--gift-bg1": "#ff6b9d", "--gift-bg2": "#7b61ff", "accent": "aurora mesh + hue-rotate"},
    "midnight": {"--gift-bg1": "#0f0f0f", "--gift-bg2": "#2a2a2a", "accent": "dark premium как Telegram"},
    "candy": {"--gift-bg1": "#ffb3c6", "--gift-bg2": "#ffe4ec", "accent": "candy pastel"},
}

class DesignEvolverAgent(Agent):
    name = "DesignEvolverAgent"
    interval_hours = 12

    def run(self):
        trends_path = Path(__file__).parent / "memory" / "trends.json"
        trends = json.loads(trends_path.read_text(encoding="utf-8")) if trends_path.exists() else {"top_keywords": []}
        self.log("INFO", f"trends: {trends.get('top_keywords')}")

        css_path = self.site_root / "static" / "css" / "style.css"
        if not css_path.exists():
            return {"error": "style.css not found"}

        original = css_path.read_text(encoding="utf-8")
        # бэкап
        backup_dir = self.site_root / "agents" / "memory" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"style.{datetime.now().strftime('%Y%m%d_%H%M%S')}.css"
        shutil.copy(css_path, backup_path)
        self.log("INFO", f"backup -> {backup_path.name}")

        # выбираем вариант на основе трендов
        keywords = [k for k,_ in trends.get("top_keywords", [])]
        if "aurora" in keywords or "mesh" in str(keywords):
            variant_name = "aurora"
        elif "dark" in keywords:
            variant_name = "midnight"
        else:
            variant_name = random.choice(list(VARIANTS.keys()))

        variant = VARIANTS[variant_name]
        self.log("INFO", f"chosen variant: {variant_name} {variant}")

        # применяем эволюцию: добавляем CSS-переменные и анимации в конец файла
        evolution = f"""
/* === AUTO-EVOLVED by DesignEvolverAgent {datetime.now().isoformat()} variant:{variant_name} === */
:root {{ --evolved-accent: {variant['--gift-bg1']}; }}
.gift-card {{ --gift-bg1: {variant['--gift-bg1']}; --gift-bg2: {variant['--gift-bg2']}; }}
/* aurora animation if selected */
.gift-stage.aurora {{ animation: auroraShift 8s ease-in-out infinite alternate; }}
@keyframes auroraShift {{ 0%{{ filter: hue-rotate(0deg) brightness(1); }} 100%{{ filter: hue-rotate(18deg) brightness(1.08); }} }}
/* micro-interaction boost */
.gift-card {{ transition: transform 0.5s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.5s; }}
.gift-card:active {{ transform: scale(0.98) !important; }}
"""

        # в безостановочном режиме всегда эволюционируем — добавляем таймстамп чтобы не скипать
        # удаляем старый маркер для ротации
        if "AUTO-EVOLVED" in original and variant_name in original[-2000:] and "--turbo" not in str(Path(__file__).parent):
            # в турбо — не скипаем
            pass

        css_path.write_text(original + "\n" + evolution, encoding="utf-8")
        self.log("SUCCESS", f"evolved CSS with {variant_name}")

        # также обновляем shop: добавляем класс aurora к первому подарку
        shop_path = self.site_root / "templates" / "shop.html"
        if shop_path.exists() and variant_name == "aurora":
            html = shop_path.read_text(encoding="utf-8")
            if 'gift-stage aurora' not in html:
                html = html.replace('class="gift-stage"', 'class="gift-stage aurora"', 1)
                shop_path.write_text(html, encoding="utf-8")

        self.save_state({"last_variant": variant_name, "backup": str(backup_path), "trends": keywords})
        return {"variant": variant_name, "backup": str(backup_path), "evolution": evolution[:200]}
