"""
ContentCuratorAgent — подтягивает свежие тексты/идеи из интернета и предлагает новые подарки
"""
import json
import random
from pathlib import Path
from base import Agent

# пул крутых идей 2026 (если интернет недоступен — fallback, иначе парсит тренды)
GIFT_IDEAS = [
    {"emoji": "🦄", "name": "Unicorn — Aurora", "desc": "Holo finish · Ultra rare", "rarity": "legendary", "colors": ["#ff8fab", "#7b61ff"]},
    {"emoji": "👑", "name": "Crown — Royal", "desc": "Gold plated · 1 of 500", "colors": ["#ffd700", "#ff8c00"]},
    {"emoji": "💎", "name": "Diamond — Prism", "desc": "Refraction glow", "colors": ["#b5e6ff", "#7fb8ff"]},
    {"emoji": "🔮", "name": "Crystal Ball — Mystic", "desc": "Predicts your vibe", "colors": ["#c084fc", "#7b61ff"]},
    {"emoji": "🍒", "name": "Cherry — Sweet", "desc": "Candy coated", "colors": ["#ff4d6d", "#ff8fab"]},
    {"emoji": "⚡", "name": "Bolt — Energy", "desc": "Electric pulse", "colors": ["#ffe600", "#ff8c00"]},
]

class ContentCuratorAgent(Agent):
    name = "ContentCuratorAgent"
    interval_hours = 24

    def run(self):
        # читаем тренды чтобы адаптировать идеи
        trends_path = Path(__file__).parent / "memory" / "trends.json"
        trends = {}
        if trends_path.exists():
            trends = json.loads(trends_path.read_text(encoding="utf-8"))
        top_kw = [k for k,_ in trends.get("top_keywords", [])]

        # генерируем 2 новые идеи на основе трендов
        picks = random.sample(GIFT_IDEAS, 2)
        # если в трендах bento — предлагаем набор
        if "bento" in top_kw:
            picks[0]["name"] += " · Bento Set"

        out = Path(__file__).parent / "memory" / "content_ideas.json"
        ideas = {"generated_from": top_kw, "ideas": picks, "action": "Можно добавить в PRODUCTS в app.py как новые gift-карточки"}
        out.write_text(json.dumps(ideas, ensure_ascii=False, indent=2), encoding="utf-8")
        self.log("INFO", f"new gift ideas: {[p['name'] for p in picks]}")

        # автономно добавляем один подарок в БД lylili.db (безопасно, без порчи кода)
        try:
            import sqlite3
            db_path = self.site_root / "lylili.db"
            if db_path.exists():
                con = sqlite3.connect(db_path)
                # найти свободный id
                cur = con.cursor()
                cur.execute("SELECT MAX(id) FROM products")
                max_id = cur.fetchone()[0] or 10
                new_id = max_id + 1
                # проверяем нет ли уже такого имени
                cur.execute("SELECT id FROM products WHERE name=?", (picks[0]["name"],))
                if not cur.fetchone():
                    cur.execute("INSERT INTO products (id,name,price,emoji,color,desc,rarity,owners) VALUES (?,?,?,?,?,?,?,?)",
                                (new_id, picks[0]["name"], 59, picks[0]["emoji"], picks[0]["colors"][0], picks[0]["desc"], "epic", 500))
                    con.commit()
                    self.log("SUCCESS", f"auto-added gift {picks[0]['name']} id={new_id} to DB")
                    ideas["auto_added"] = {**picks[0], "id": new_id}
                con.close()
            else:
                self.log("WARN", "no DB, skip auto-add")
        except Exception as e:
            self.log("WARN", f"DB auto-add failed: {e}")

        self.save_state(ideas)
        return ideas
