"""
DBArchitectAgent — строит и мигрирует БД, вечно тестирует целостность
"""
import sqlite3
import json
from pathlib import Path
from base import Agent

DB_PATH = Path(__file__).parent.parent / "lylili.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  price INTEGER NOT NULL,
  emoji TEXT,
  color TEXT,
  desc TEXT,
  rarity TEXT,
  owners INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT DEFAULT (datetime('now')),
  total INTEGER,
  items_json TEXT,
  email TEXT
);
CREATE TABLE IF NOT EXISTS subscribers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS design_evolutions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT DEFAULT (datetime('now')),
  variant TEXT,
  trends_json TEXT
);
"""

class DBArchitectAgent(Agent):
    name = "DBArchitectAgent"
    interval_hours = 24

    def run(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH)
        con.executescript(SCHEMA)
        # seed products if empty
        cur = con.cursor()
        cur.execute("SELECT count(*) FROM products")
        cnt = cur.fetchone()[0]
        seeded = 0
        if cnt == 0:
            from pathlib import Path as P
            import sys
            sys.path.insert(0, str(P(__file__).parent.parent))
            # import PRODUCTS from app.py
            try:
                import app as appmod
                products = appmod.PRODUCTS
            except:
                products = [
                    {"id":1,"name":"Flirty Shorts — Pink","price":49,"emoji":"🩷","color":"#ffb3c6","desc":"Mischievous & flirty","rarity":"epic","owners":1200},
                    {"id":2,"name":"Mischievous — Red","price":49,"emoji":"💃","color":"#ff6b8a","desc":"Bold & playful","rarity":"legendary","owners":2500},
                    {"id":3,"name":"Cheerful — Cream","price":45,"emoji":"✨","color":"#fff2cc","desc":"Light & airy","rarity":"rare","owners":800},
                    {"id":4,"name":"Spring — Pastel","price":47,"emoji":"🌸","color":"#ffd6e7","desc":"Soft spring vibes","rarity":"rare","owners":800},
                    {"id":5,"name":"Freedom — Sky","price":49,"emoji":"🦋","color":"#b5e6ff","desc":"Open & free","rarity":"rare","owners":800},
                    {"id":6,"name":"Sweet — Berry","price":52,"emoji":"🍓","color":"#ff8fab","desc":"Sweet adventure","rarity":"legendary","owners":2500},
                    {"id":7,"name":"Unicorn — Aurora","price":59,"emoji":"🦄","color":"#ff8fab","desc":"Holo finish · Ultra rare","rarity":"legendary","owners":2500},
                ]
            for p in products:
                cur.execute("INSERT OR IGNORE INTO products (id,name,price,emoji,color,desc,rarity,owners) VALUES (?,?,?,?,?,?,?,?)",
                            (p["id"], p["name"], p["price"], p["emoji"], p["color"], p["desc"], p.get("rarity","epic"), p.get("owners",1200)))
                seeded +=1
            con.commit()
            self.log("INFO", f"seeded {seeded} products")
        # vacuum + integrity
        cur.execute("PRAGMA integrity_check")
        integrity = cur.fetchone()[0]
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        con.commit()
        con.close()
        # backup
        backup = Path(__file__).parent / "memory" / "backups" / f"lylili.db.bak"
        backup.parent.mkdir(parents=True, exist_ok=True)
        if DB_PATH.exists():
            import shutil
            shutil.copy(DB_PATH, backup)
        self.log("INFO", f"DB ready {DB_PATH} integrity={integrity} products={cnt or seeded}")
        self.save_state({"db": str(DB_PATH), "integrity": integrity, "products": cnt or seeded, "backup": str(backup)})
        return {"db": str(DB_PATH), "integrity": integrity, "seeded": seeded}
