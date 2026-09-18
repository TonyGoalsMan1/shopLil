"""
LLMAgent — подключает LLM API для конкретных действий по улучшению
Если есть OPENAI_API_KEY — зовет реальный LLM, иначе — умный мок на основе трендов и состояния сайта
Логирует подробно: prompt, reasoning, actions, diff, результат
"""
import os, json, re, time
from pathlib import Path
from base import Agent
import requests

MOCK_SYSTEM = """Ты — Senior Product Designer + Frontend Lead для LYLILI Telegram Gifts.
Сайт: 3D подарки с подиумом, glassmorphism, 4K, премиум gold.
Отвечай JSON: {"reasoning": "...", "actions": [{"type":"css|product|copy|ux", "target":"...", "change":"...", "code":"...", "why":"..."}]} 
Делай конкретно, с кодом."""

def build_context(site_root: Path):
    ctx = {}
    try:
        # products
        import sqlite3
        p = site_root / "lylili.db"
        if p.exists():
            con = sqlite3.connect(p)
            rows = con.execute("SELECT count(*) FROM products").fetchone()
            ctx["products_count"] = rows[0] if rows else 0
            con.close()
        # css
        css = (site_root / "static/css/style.css").read_text(encoding="utf-8", errors="ignore")
        ctx["css_size"] = len(css)
        ctx["turbo_count"] = css.count("/* TURBO")
        # trends
        tr = Path(site_root) / "agents/memory/trends.json"
        if tr.exists():
            t = json.loads(tr.read_text(encoding="utf-8", errors="ignore"))
            ctx["top_trends"] = t.get("top_keywords", [])[:4]
            ctx["recommendations"] = t.get("recommendations", [])[:3]
        # user tests
        ut = Path(site_root) / "agents/memory/user_tests.json"
        if ut.exists():
            u = json.loads(ut.read_text(encoding="utf-8", errors="ignore"))
            ctx["user_passed"] = f"{u.get('passed')}/{u.get('tested')}"
            ctx["insights"] = u.get("insights", [])[:2]
    except Exception as e:
        ctx["error"] = str(e)
    return ctx

def mock_llm(prompt: str, context: dict):
    # умный мок — генерирует конкретные действия без внешнего API
    prompt_l = prompt.lower()
    actions=[]
    if any(x in prompt_l for x in ["премиум","люкс","gold","premium"]):
        actions.append({"type":"css","target":".gift-card","change":"Добавить золотую рамку и inner glow для legendary","code":".gift-card[data-cat='legendary']{ border:1px solid #d4af37; box-shadow:0 0 0 1px #d4af37 inset, 0 12px 32px rgba(212,175,55,0.18); }","why":"Премиум как у Telegram gifts"})
    if any(x in prompt_l for x in ["4k","четк","резк","crisp"]):
        actions.append({"type":"css","target":"html","change":"Усилить crisp-edges и 4K медиа","code":"@media(min-width:2560px){ .gift-emoji-wrap{ font-size:124px } } html{ image-rendering: crisp-edges; }","why":"4K мониторы"})
    if any(x in prompt_l for x in ["товар","продукт","подар","gift","ассортимент"]):
        actions.append({"type":"product","target":"DB","change":"Добавить лимитированный подарок","code":"{'id':11,'name':'Aurora Borealis — Limited','price':109,'emoji':'🌌','color':'#7b61ff','desc':'Северное сияние'}","why":"Расширение коллекции"})
    if any(x in prompt_l for x in ["корзин","оплата","checkout","payment"]):
        actions.append({"type":"ux","target":"/cart","change":"Добавить Apple Pay кнопку и бесплатную доставку бейдж","code":"<div class='pill gold'>Бесплатная доставка от €100</div>","why":"CR +12% по тестам"})
    if any(x in prompt_l for x in ["дизайн","css","градиент","glass","aurora"]):
        actions.append({"type":"css","target":".gift-stage","change":"Aurora mesh градиент с анимацией","code":".gift-stage.aurora{ background: radial-gradient(800px 400px at 30% 0%, #ffb3c6 0%, #7b61ff 60%, transparent 100%); animation: aurora 8s infinite alternate; } @keyframes aurora{ to{ filter: hue-rotate(20deg)}}","why":"Тренд 2026"})
    if not actions:
        # дефолт на основе контекста
        if context.get("products_count",0) < 12:
            actions.append({"type":"product","target":"DB","change":"Дроп нового подарка","code":"{'id':12,'name':'Starlight — Holo','price':95,'emoji':'⭐','color':'#ffd700'}","why":"Мало товаров"})
        else:
            actions.append({"type":"css","target":".gift-card","change":"Усилить hover 3D tilt до 9deg","code":".gift-card:hover{ transform: translateY(-12px) rotateX(3deg) rotateY(-3deg) scale(1.03) }","why":"Премиум интеракция"})
    return {
        "reasoning": f"Контекст: {context.get('top_trends')} | {context.get('products_count')} товаров | Запрос: {prompt[:80]}. Выбрал {len(actions)} конкретных действий.",
        "actions": actions
    }

def call_real_llm(prompt: str, context: dict):
    key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if not key:
        return None
    try:
        # пробуем OpenAI-compatible
        url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        payload = {
            "model": model,
            "messages": [
                {"role":"system","content": MOCK_SYSTEM},
                {"role":"user","content": f"Контекст: {json.dumps(context, ensure_ascii=False)[:1000]}\nЗапрос: {prompt}"}
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }
        r = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"}, json=payload, timeout=20)
        r.raise_for_status()
        txt = r.json()["choices"][0]["message"]["content"]
        # вытаскиваем JSON
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            return json.loads(m.group(0))
        return {"reasoning": txt[:300], "actions": [{"type":"copy","target":"site","change":txt[:200],"code":"","why":"LLM"}]}
    except Exception as e:
        return {"error": str(e), "fallback": True}

class LLMAgent(Agent):
    name = "LLMAgent"
    interval_hours = 24

    def ask(self, prompt: str, apply: bool = False):
        ctx = build_context(self.site_root)
        self.log("INFO", f"LLM ask: {prompt[:60]}", {"context": ctx})
        # пробуем реальный LLM
        llm_res = call_real_llm(prompt, ctx)
        used_real = llm_res is not None and "error" not in llm_res
        if not used_real:
            if llm_res and "error" in llm_res:
                self.log("WARN", f"LLM API failed {llm_res['error']}, fallback to mock")
            llm_res = mock_llm(prompt, ctx)
            llm_res["mode"] = "mock"
        else:
            llm_res["mode"] = "real"
        llm_res["prompt"] = prompt
        llm_res["context"] = ctx
        llm_res["time"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # информативный лог
        for a in llm_res.get("actions", []):
            self.log("INFO", f"LLM action {a['type']}:{a['target']} — {a['change']}", a)

        if apply:
            applied = self.apply_actions(llm_res.get("actions", []))
            llm_res["applied"] = applied
            self.log("SUCCESS", f"Applied {len(applied)} actions", applied)

        # сохраняем
        out = Path(__file__).parent / "memory" / "last_llm.json"
        out.write_text(json.dumps(llm_res, ensure_ascii=False, indent=2), encoding="utf-8")
        self.save_state(llm_res)
        return llm_res

    def apply_actions(self, actions):
        applied=[]
        for a in actions:
            try:
                if a["type"]=="css" and a.get("code"):
                    css = self.site_root / "static/css/style.css"
                    txt = css.read_text(encoding="utf-8", errors="ignore")
                    # добавляем с комментарием LLM
                    add = f"\n/* LLM {time.strftime('%H:%M:%S')} {a['target']} — {a['change']} */\n{a['code']}\n"
                    css.write_text(txt + add, encoding="utf-8")
                    applied.append({"type":"css","target":a["target"],"ok":True})
                elif a["type"]=="product" and a.get("code"):
                    # парсим id из code
                    import re, sqlite3
                    m = re.search(r"'id':\s*(\d+)", a["code"])
                    pid = int(m.group(1)) if m else int(time.time())%1000
                    # пробуем вставить в БД
                    import pathlib
                    p = pathlib.Path(self.site_root) / "lylili.db"
                    if p.exists():
                        con = sqlite3.connect(p)
                        # извлекаем поля
                        name = re.search(r"'name':\s*'([^']+)'", a["code"])
                        price = re.search(r"'price':\s*(\d+)", a["code"])
                        emoji = re.search(r"'emoji':\s*'([^']+)'", a["code"])
                        color = re.search(r"'color':\s*'([^']+)'", a["code"])
                        desc = re.search(r"'desc':\s*'([^']+)'", a["code"])
                        try:
                            con.execute("INSERT OR REPLACE INTO products (id,name,price,emoji,color,desc,rarity,owners) VALUES (?,?,?,?,?,?,?,?)",
                                        (pid, name.group(1) if name else f"LLM Gift {pid}", int(price.group(1)) if price else 79, emoji.group(1) if emoji else "🎁", color.group(1) if color else "#7b61ff", desc.group(1) if desc else "LLM generated", "legendary", 100))
                            con.commit()
                            applied.append({"type":"product","id":pid,"ok":True})
                        except Exception as e:
                            applied.append({"type":"product","error":str(e)})
                        con.close()
                    else:
                        applied.append({"type":"product","skipped":"no db"})
                elif a["type"] in ["ux","copy"]:
                    applied.append({"type":a["type"],"target":a["target"],"ok":True, "note":"logged"})
                else:
                    applied.append({"type":a["type"],"ok":False,"error":"unknown type"})
            except Exception as e:
                applied.append({"type":a.get("type"),"error":str(e)})
        return applied

    def run(self):
        # автономный прогон — спрашивает LLM "что улучшить?"
        return self.ask("Что улучшить на сайте LYLILI чтобы стать премиум 4K и увеличить конверсию?", apply=False)
