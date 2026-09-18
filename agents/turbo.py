"""
TURBO — безостановочно изменяет сайт каждые N секунд
Изучает крутые сайты, мутирует дизайн, БД, безопасность, 4K
"""
import sys, time, random, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from trend_scout import TrendScoutAgent
from design_evolver import DesignEvolverAgent
from ux_optimizer import UXOptimizerAgent
from content_curator import ContentCuratorAgent
from db_architect import DBArchitectAgent
from security_agent import SecurityAgent
from quality_4k_agent import Quality4KAgent
from test_agent import TestAgent

SITE_ROOT = Path(__file__).parent.parent
INTERVAL = 20  # секунд — безостановочно

# для 4K динамики — рандомные палитры как у топ сайтов 2026
PALETTES = [
    ("#ff6b9d","#7b61ff","aurora"),
    ("#0f0f0f","#2a2a2a","midnight"),
    ("#ffb3c6","#ffe4ec","candy"),
    ("#00d4ff","#7b61ff","ocean"),
    ("#ff8c00","#ffd700","sunset"),
    ("#00ffa3","#00d4ff","neon"),
]

def turbo_once(n):
    print(f"\n===== TURBO #{n} {time.strftime('%H:%M:%S')} =====")
    # 1. Scout быстро (каждый раз)
    TrendScoutAgent(SITE_ROOT).safe_run()
    # 2. DB check
    DBArchitectAgent(SITE_ROOT).safe_run()
    # 3. Security
    SecurityAgent(SITE_ROOT).safe_run()
    # 4. 4K —
    Quality4KAgent(SITE_ROOT).safe_run()
    # 5. Дизайн — форсируем случайную палитру каждый раз
    ev = DesignEvolverAgent(SITE_ROOT)
    # патчим выбор варианта на рандом для безостановочности
    import random as R
    pal = R.choice(PALETTES)
    css = SITE_ROOT / "static/css/style.css"
    txt = css.read_text(encoding="utf-8")
    evo = f"\n/* TURBO {n} {pal[2]} {time.time():.0f} */\n.gift-card {{ --gift-bg1:{pal[0]}; --gift-bg2:{pal[1]}; }}\n.gift-stage {{ filter: hue-rotate({R.randint(-15,15)}deg) brightness(1.05); }}\n"
    css.write_text(txt + evo, encoding="utf-8")
    print(f"[Turbo] design -> {pal[2]} {pal[0]}->{pal[1]}")
    # 6. UX
    UXOptimizerAgent(SITE_ROOT).safe_run()
    # 7. Content — шанс добавить подарок
    if n % 3 == 0:
        ContentCuratorAgent(SITE_ROOT).safe_run()
    # 8. Test
    TestAgent(SITE_ROOT).safe_run()
    # touch Flask
    (SITE_ROOT / "app.py").touch()
    print(f"[Turbo] done #{n} -> http://127.0.0.1:5000/")

if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv)>1 and sys.argv[1].isdigit() else INTERVAL
    print(f"TURBO MODE — безостановочно каждые {interval} сек. Ctrl+C чтобы остановить.")
    n=1
    while True:
        try:
            turbo_once(n)
        except Exception as e:
            print("turbo error", e)
        n+=1
        time.sleep(interval)
