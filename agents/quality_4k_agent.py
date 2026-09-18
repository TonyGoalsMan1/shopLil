"""
Quality4KAgent — доводит дизайн до 4K: retina, crisp, 4K медиа-запросы, вектор, sharpness
"""
import json
from pathlib import Path
from base import Agent

FOUR_K_CSS = """
/* === 4K ULTRA by Quality4KAgent === */
html { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; text-rendering: optimizeLegibility; }
img, canvas, svg { image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges; }
/* 4K containers */
@media (min-width: 2560px) {
  .container { max-width: 1600px; }
  .hero h1 { font-size: 64px; }
  .about-card { max-width: 1100px; padding: 56px; }
  .grid { grid-template-columns: repeat(4, 1fr); gap: 28px; }
  .gift-stage { height: 340px; }
  .gift-emoji-wrap { font-size: 110px; width: 200px; height: 200px; }
}
/* Retina 2x */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  .gift-card { border-width: 0.5px; }
  .gift-stage::before { background-size: 18px 18px; }
}
/* 8K future */
@media (min-width: 3840px) {
  .container { max-width: 1800px; }
  .grid { grid-template-columns: repeat(4, 1fr); }
}
/* crisp glass for 4K */
.gift-card { will-change: transform; backface-visibility: hidden; transform: translateZ(0); }
.gift-stage { transform: translateZ(0); }
"""

class Quality4KAgent(Agent):
    name = "Quality4KAgent"
    interval_hours = 12

    def run(self):
        css = self.site_root / "static" / "css" / "style.css"
        text = css.read_text(encoding="utf-8")
        fixes = []
        if "4K ULTRA" not in text:
            text += "\n" + FOUR_K_CSS
            fixes.append("added 4K ultra CSS (2560/3840, retina, crisp-edges)")
        # добавляем viewport + preconnect для 4K шрифтов
        for tpl in (self.site_root / "templates").glob("*.html"):
            html = tpl.read_text(encoding="utf-8")
            if 'rel="preconnect"' not in html:
                html = html.replace('</title>', '</title>\n  <link rel="preconnect" href="https://fonts.googleapis.com">\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
                tpl.write_text(html, encoding="utf-8")
                fixes.append(f"{tpl.name}: preconnect for 4K fonts")
            if 'image-rendering' not in html:
                pass
        css.write_text(text, encoding="utf-8")
        # создаём 4K чеклист
        report = {
            "checks": [
                "2560px container 1600px",
                "3840px container 1800px",
                "retina 2x border 0.5px",
                "crisp-edges + antialiased",
                "gift-stage 340px on 4K",
                "will-change transform for GPU"
            ],
            "fixes": fixes
        }
        (Path(__file__).parent / "memory" / "4k_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.log("INFO", f"4K fixes: {fixes}")
        self.save_state(report)
        return report
