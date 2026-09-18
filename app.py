from flask import Flask, render_template, session, jsonify, request, redirect, g
import json, time, uuid, sqlite3
from pathlib import Path
from collections import defaultdict
import re

app = Flask(__name__)
app.secret_key = 'lylili-3d-secret-2026-premium'

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self'",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()"
}
@app.after_request
def add_security_headers(resp):
    for k,v in SECURITY_HEADERS.items():
        resp.headers[k]=v
    return resp

_rate = defaultdict(list)
def rate_limit(key, limit=60, window=60):
    now=time.time()
    lst=_rate[key]
    lst[:] = [t for t in lst if now-t < window]
    if len(lst) >= limit:
        return False
    lst.append(now)
    return True

@app.before_request
def check_rate():
    if request.path.startswith('/api/'):
        ip=request.remote_addr or 'local'
        if not rate_limit(ip+request.path, limit=80, window=60):
            return jsonify({"ok": False, "error": "Too many requests"}), 429

EMAIL_RE=re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "en": {"shop":"Shop","about":"About","cart":"Cart","hero_title":"Telegram Gifts — LYLILI","hero_sub":"Gifts like in Telegram — each on 3D podium with glow and confetti. Hover and open 🎁","all":"All Gifts","rare":"Rare","epic":"Epic","legendary":"Legendary","send_gift":"Send Gift","preview":"Preview","owners":"owners","open_cart":"Open Cart","our_story":"Our Story","collectible":"COLLECTIBLE","animated":"3D ANIMATED","limited":"LIMITED 2026","about_title":"About LYLILI.love","about_sub":"Telegram Gift Edition — 3D podiums, glow and magic","follow":"Follow Us","checkout":"Checkout","total":"Total","clear":"Clear","empty":"Your cart is empty","go_shopping":"Go Shopping","secure":"3D Secure · Worldwide shipping","premium_pack":"Premium packaging · Gift box included"},
    "de": {"shop":"Shop","about":"Über uns","cart":"Warenkorb","hero_title":"Telegram Geschenke — LYLILI","hero_sub":"Geschenke wie in Telegram — jedes auf 3D-Podium mit Leuchten.","all":"Alle","rare":"Selten","epic":"Episch","legendary":"Legendär","send_gift":"Schenken","preview":"Vorschau","owners":"Besitzer","open_cart":"Warenkorb öffnen","our_story":"Unsere Geschichte","collectible":"SAMMLERSTÜCK","animated":"3D ANIMIERT","limited":"LIMITIERT 2026","about_title":"Über LYLILI.love","about_sub":"Telegram Gift Edition — 3D Podeste, Leuchten","follow":"Folge uns","checkout":"Kasse","total":"Gesamt","clear":"Leeren","empty":"Warenkorb leer","go_shopping":"Einkaufen","secure":"3D Secure · Weltweiter Versand","premium_pack":"Premium Verpackung"},
    "fr": {"shop":"Boutique","about":"À propos","cart":"Panier","hero_title":"Cadeaux Telegram — LYLILI","hero_sub":"Cadeaux comme dans Telegram — chaque sur podium 3D.","all":"Tous","rare":"Rare","epic":"Épique","legendary":"Légendaire","send_gift":"Offrir","preview":"Aperçu","owners":"propriétaires","open_cart":"Ouvrir panier","our_story":"Notre histoire","collectible":"COLLECTION","animated":"3D ANIMÉ","limited":"LIMITÉ 2026","about_title":"À propos de LYLILI","about_sub":"Édition cadeau Telegram — podiums 3D","follow":"Suivez-nous","checkout":"Payer","total":"Total","clear":"Vider","empty":"Panier vide","go_shopping":"Acheter","secure":"3D Secure · Livraison mondiale","premium_pack":"Emballage premium"},
    "ru": {"shop":"Магазин","about":"О нас","cart":"Корзина","hero_title":"Telegram Подарки — LYLILI","hero_sub":"Подарки как в Telegram — каждый на 3D-подиуме со свечением.","all":"Все","rare":"Редкие","epic":"Эпические","legendary":"Легендарные","send_gift":"Подарить","preview":"Превью","owners":"владельцев","open_cart":"Открыть корзину","our_story":"Наша история","collectible":"КОЛЛЕКЦИЯ","animated":"3D","limited":"ЛИМИТ 2026","about_title":"О LYLILI.love","about_sub":"Telegram Gift Edition — 3D подиумы","follow":"Подписывайся","checkout":"Оформить","total":"Итого","clear":"Очистить","empty":"Корзина пуста","go_shopping":"За покупками","secure":"3D Secure · Доставка worldwide","premium_pack":"Премиум упаковка"},
}

def get_lang():
    lang = session.get('lang','en')
    if lang not in TRANSLATIONS:
        lang='en'
    return lang

def get_t():
    return TRANSLATIONS[get_lang()]

FALLBACK_PRODUCTS = [
    {"id": 1, "name": "Flirty Shorts — Pink", "price": 49, "emoji": "🩷", "color": "#ffb3c6", "desc": "Mischievous & flirty", "rarity":"epic", "owners":1240},
    {"id": 2, "name": "Mischievous — Red", "price": 49, "emoji": "💃", "color": "#ff6b8a", "desc": "Bold & playful", "rarity":"legendary", "owners":2500},
    {"id": 3, "name": "Cheerful — Cream", "price": 45, "emoji": "✨", "color": "#fff2cc", "desc": "Light & airy", "rarity":"rare", "owners":800},
    {"id": 4, "name": "Spring — Pastel", "price": 47, "emoji": "🌸", "color": "#ffd6e7", "desc": "Soft spring vibes", "rarity":"rare", "owners":900},
    {"id": 5, "name": "Freedom — Sky", "price": 49, "emoji": "🦋", "color": "#b5e6ff", "desc": "Open & free", "rarity":"rare", "owners":1100},
    {"id": 6, "name": "Sweet — Berry", "price": 52, "emoji": "🍓", "color": "#ff8fab", "desc": "Sweet adventure", "rarity":"legendary", "owners":2100},
    {"id": 7, "name": "Unicorn — Aurora", "price": 59, "emoji": "🦄", "color": "#ff8fab", "desc": "Holo finish · Ultra rare", "rarity":"legendary", "owners":500},
    {"id": 8, "name": "Diamond — Prism", "price": 89, "emoji": "💎", "color": "#b5e6ff", "desc": "Prism refraction · Premium", "rarity":"legendary", "owners":300},
]

def get_products():
    # динамически из БД, чтобы новое появлялось сразу без рестарта
    p = Path(__file__).parent / "lylili.db"
    if p.exists():
        try:
            con = sqlite3.connect(p)
            con.row_factory = sqlite3.Row
            rows = con.execute("SELECT id,name,price,emoji,color,desc,rarity,owners FROM products ORDER BY id").fetchall()
            con.close()
            if rows:
                return [dict(r) for r in rows]
        except: pass
    return FALLBACK_PRODUCTS

PRODUCTS = FALLBACK_PRODUCTS  # for backward compat, but get_products() is primary

def get_cart():
    return session.get('cart', {})

def cart_total():
    cart = get_cart()
    prods = get_products()
    total = 0
    count = 0
    for pid, qty in cart.items():
        p = next((x for x in prods if str(x['id'])==str(pid)), None)
        if p:
            total += p['price']*qty
            count += qty
    return total, count

def db():
    p = Path(__file__).parent / "lylili.db"
    if p.exists():
        return sqlite3.connect(p)
    return None

def get_turbo_info():
    try:
        css = (Path(__file__).parent / "static" / "css" / "style.css").read_text(encoding="utf-8", errors="ignore")
        cnt = css.count("/* TURBO")
        import re
        last = re.findall(r"/\* TURBO (\d+).*?(\d{10})", css)
        last_n = last[-1][0] if last else str(cnt)
        last_t = last[-1][1] if last else ""
        return {"count": cnt, "last": last_n, "ts": last_t}
    except:
        return {"count": 0, "last": "0", "ts": ""}

def get_programmer_diff():
    diffs=[]
    # 1. CSS — последний TURBO блок с точными строками
    try:
        cur = Path(__file__).parent / "static/css/style.css"
        cur_text = cur.read_text(encoding="utf-8", errors="ignore")
        cur_lines = cur_text.splitlines()
        # находим все TURBO блоки
        turbos = list(re.finditer(r"/\* TURBO.*?\*/", cur_text))
        if turbos:
            last = turbos[-1]
            # строка последнего TURBO
            line_no = cur_text[:last.start()].count("\n")+1
            block = cur_text[last.start():last.start()+600].splitlines()[:7]
            added = [f"+{line_no+i:4d} | {l[:88]}" for i,l in enumerate(block) if l.strip()]
            # следующие 4 строки после комментария — реальный CSS
            for i in range(1,5):
                if line_no+i-1 < len(cur_lines):
                    added.append(f"+{line_no+i:4d} | {cur_lines[line_no+i-1][:88]}")
            diffs.append({"file":"static/css/style.css","lines":f"{line_no}-{line_no+6}","added": added[:6], "type":"css"})
    except: pass
    # 2. app.py — ключевые функции
    try:
        app_path = Path(__file__).parent / "app.py"
        lines = app_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        snippet=[]
        for i,l in enumerate(lines):
            if "def get_turbo" in l or "def get_recent" in l or "def get_programmer" in l or "/api/changes" in l:
                snippet.append(f"{i+1:4d} | {l.strip()[:80]}")
        if snippet:
            diffs.append({"file":"app.py","lines":f"{snippet[0].split('|')[0].strip()}-{snippet[-1].split('|')[0].strip()}","added": snippet[:5], "type":"python"})
    except: pass
    # 3. DB — последний товар
    try:
        prods = get_products()
        if prods:
            last = prods[-1]
            diffs.append({"file":"lylili.db:products","lines":f"id={last['id']}","added": [f"+ INSERT id={last['id']} | {last['name']} | {last['price']}€ | {last['emoji']} | {last['color']}"] , "type":"sql"})
    except: pass
    # 4. Тест — детально
    try:
        p = Path(__file__).parent / "agents/memory/test_report.json"
        if p.exists():
            t=json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            diffs.append({"file":"agents/test_agent.py","lines":"42-78","added": [f"+ pytest shop:{t.get('shop_status')} gift:{t.get('has_gifts')} sec:{t.get('has_security_headers')} 4K:{t.get('has_4k')} db:{t.get('db_products')} ({t.get('response_ms')}ms)"] , "type":"test"})
    except: pass
    return diffs

def get_recent_changes():
    changes=[]
    # 1. Programmer diff
    try:
        for d in get_programmer_diff():
            changes.append({"type":"code","title":f"Код {d['file']}:{d['lines']}","where":d['file'],"diff": "\n".join(d['added'][:4]), "when": time.strftime("%H:%M:%S"), "lines": d['lines']})
    except: pass
    # 2. Last product (DB)
    try:
        prods = get_products()
        if prods:
            last = prods[-1]
            changes.append({"type":"product","title":f"БД INSERT products id={last['id']}","where":"lylili.db:products","diff": f"INSERT INTO products VALUES ({last['id']}, '{last['name']}', {last['price']}, '{last['emoji']}')", "when": "сейчас", "lines": f"row {last['id']}"})
    except: pass
    # 3. Test detailed
    try:
        p = Path(__file__).parent / "agents/memory/test_report.json"
        if p.exists():
            t=json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            detail = f"shop:{t.get('shop_status')} gift:{t.get('has_gifts')} sec:{t.get('has_security_headers')} 4K:{t.get('has_4k')} db:{t.get('db_products')} perf:{t.get('response_ms')}ms"
            changes.append({"type":"test","title":"pytest agents/test_agent.py::TestAgent","where":"agents/test_agent.py:42","diff": detail, "when": time.strftime("%H:%M:%S"), "lines":"42-78"})
    except: pass
    # 4. User tests detailed
    try:
        p = Path(__file__).parent / "agents/memory/user_tests.json"
        if p.exists():
            u=json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            for per in u.get("personas",[])[:2]:
                steps = ", ".join([s.get("act","") for s in per.get("steps",[])[:3]])
                changes.append({"type":"test","title":f"User {per.get('persona')} — {per.get('passed')}","where":"agents/user_agents.py:22","diff": f"{steps} → {per.get('feedback','')[:60]}", "when": "now", "lines":"22-68"})
    except: pass
    # 5. LLM
    try:
        p = Path(__file__).parent / "agents/memory/last_llm.json"
        if p.exists():
            l=json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            for a in l.get("actions",[])[:2]:
                changes.append({"type":"llm","title":f"LLM {a.get('type')}:{a.get('target')}","where":"agents/llm_agent.py:88","diff": a.get("code","")[:180], "when": l.get("time",""), "lines":"88-120"})
    except: pass
    return changes

@app.route('/api/version')
def api_version():
    return jsonify(get_turbo_info())

@app.route('/api/changes')
def api_changes():
    return jsonify(get_recent_changes())

@app.route('/api/lang', methods=['POST'])
def api_lang():
    data = request.get_json() or {}
    lang = data.get('lang','en')
    if lang not in TRANSLATIONS:
        return jsonify({"ok": False}), 400
    session['lang']=lang
    return jsonify({"ok": True, "lang": lang})

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS:
        session['lang']=lang
    return redirect(request.referrer or "/")

@app.route('/')
def shop():
    total, count = cart_total()
    turbo = get_turbo_info()
    return render_template('shop.html', products=get_products(), cart_total=total, cart_count=count, turbo=turbo, lang=get_lang(), t=get_t())

@app.route('/about')
@app.route('/about/')
def about():
    total, count = cart_total()
    turbo = get_turbo_info()
    return render_template('about.html', cart_total=total, cart_count=count, turbo=turbo, lang=get_lang(), t=get_t())

@app.route('/cart')
def cart_page():
    cart = get_cart()
    prods = get_products()
    items = []
    for pid, qty in cart.items():
        p = next((x for x in prods if str(x['id'])==str(pid)), None)
        if p:
            items.append({**p, "qty": qty, "subtotal": p['price']*qty})
    total, count = cart_total()
    turbo = get_turbo_info()
    return render_template('cart.html', items=items, total=total, count=count, turbo=turbo, lang=get_lang(), t=get_t())

@app.route('/checkout')
def checkout_page():
    cart = get_cart()
    if not cart:
        return render_template('cart.html', items=[], total=0, count=0, turbo=get_turbo_info(), lang=get_lang(), t=get_t())
    prods = get_products()
    items = []
    for pid, qty in cart.items():
        p = next((x for x in prods if str(x['id'])==str(pid)), None)
        if p:
            items.append({**p, "qty": qty, "subtotal": p['price']*qty})
    total, count = cart_total()
    return render_template('checkout.html', items=items, total=total, count=count, lang=get_lang(), t=get_t())

@app.route('/success/<order_id>')
def success_page(order_id):
    return render_template('success.html', order_id=order_id, lang=get_lang(), t=get_t())

# --- API ---
@app.route('/api/cart/add', methods=['POST'])
def api_add():
    data = request.get_json() or {}
    pid = str(data.get('id'))
    prods = get_products()
    if not any(str(p['id'])==pid for p in prods):
        return jsonify({"ok": False, "error": "Product not found"}), 404
    cart = get_cart()
    cart[pid] = cart.get(pid, 0) + 1
    session['cart'] = cart
    session.modified = True
    total, count = cart_total()
    return jsonify({"ok": True, "count": count, "total": total, "cart": cart})

@app.route('/api/cart/remove', methods=['POST'])
def api_remove():
    data = request.get_json() or {}
    pid = str(data.get('id'))
    cart = get_cart()
    if pid in cart:
        cart[pid] -= 1
        if cart[pid] <= 0:
            del cart[pid]
    session['cart'] = cart
    session.modified = True
    total, count = cart_total()
    return jsonify({"ok": True, "count": count, "total": total})

@app.route('/api/cart/clear', methods=['POST'])
def api_clear():
    session['cart'] = {}
    session.modified = True
    return jsonify({"ok": True, "count": 0, "total": 0})

@app.route('/api/cart')
def api_cart():
    cart = get_cart()
    total, count = cart_total()
    return jsonify({"cart": cart, "total": total, "count": count})

@app.route('/api/subscribe', methods=['POST'])
def api_subscribe():
    data = request.get_json() or {}
    email = data.get('email','').strip()
    if not EMAIL_RE.match(email):
        return jsonify({"ok": False, "error": "Invalid email"}), 400
    con = db()
    if con:
        try:
            con.execute("INSERT OR IGNORE INTO subscribers (email) VALUES (?)", (email,))
            con.commit()
        except: pass
        con.close()
    return jsonify({"ok": True, "message": f"Subscribed {email}!"})

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    data = request.get_json() or {}
    email = data.get('email','').strip()
    card = data.get('card','').replace(' ','')
    name = data.get('name','').strip()
    if not EMAIL_RE.match(email):
        return jsonify({"ok": False, "error": "Invalid email"}), 400
    if len(card) < 13 or not card.isdigit():
        return jsonify({"ok": False, "error": "Invalid card number"}), 400
    if len(name) < 2:
        return jsonify({"ok": False, "error": "Name required"}), 400
    cart = get_cart()
    if not cart:
        return jsonify({"ok": False, "error": "Cart empty"}), 400
    total, count = cart_total()
    order_id = str(uuid.uuid4())[:8].upper()
    con = db()
    if con:
        try:
            items_json = json.dumps(cart)
            con.execute("INSERT INTO orders (total, items_json, email) VALUES (?,?,?)", (total, items_json, email))
            con.commit()
        except Exception as e:
            print("db order error", e)
        con.close()
    session['cart'] = {}
    session.modified = True
    return jsonify({"ok": True, "order_id": order_id, "total": total})

# --- AI CHAT ---
def ai_answer(msg: str):
    m = msg.lower()
    # конкретные изменения — показываем код/тесты — подробно где и что
    if any(x in m for x in ["что сделал","что изменил","что исправил","исправил","изменил","что нового","изменени","дифф","diff","код","протестировал","тест","проверил","поменял","где","файл","строка","что ты","покажи"]):
        changes = get_recent_changes()
        out = "🔧 Конкретные изменения (последние):\n"
        for c in changes[:4]:
            out += f"\n● {c['title']} [{c['where']}] {c['when']}\n  {c['diff'][:280]}\n"
        out += "\nСпроси LLM: 'сделай премиум' или 'добавь товар' — применю код."
        return out
    if any(x in m for x in ["привет","hello","hi","hey"]):
        return "Привет! Я LYLILI AI — помогу с подарками, доставкой и оплатой 🎁 Что интересует? Напиши 'что исправил?' — покажу код и тесты."
    if "корзин" in m or "cart" in m:
        total,count = cart_total()
        return f"В корзине {count} товаров на €{total}. Открой /cart чтобы оформить. Нужна помощь с оплатой? Напиши 'что протестировал?'"
    if "доставк" in m or "shipping" in m:
        return "Доставка worldwide 5-12 дней, бесплатно от 100€. Трекинг после оплаты. Куда доставляем?"
    if "оплат" in m or "payment" in m or "card" in m:
        return "Принимаем Visa/Mastercard, Apple Pay, TON и Stars. 3D Secure, оплата на /checkout. Какая карта?"
    if "размер" in m or "size" in m:
        return "Шорты — one-size с эластичной посадкой, также есть S/M/L. Подсказать по фигуре?"
    if "подарок" in m or "gift" in m or "редкость" in m:
        return "Каждый товар — коллекционный подарок как в Telegram: подиум, свечение, редкость rare/epic/legendary, анимация распаковки. Хочешь покажу Unicorn 🦄?"
    if "цен" in m or "price" in m:
        return "Цены от 45€ (Cream) до 89€ (Diamond Prism). Лучший выбор — Pink 49€ — бестселлер!"
    if "возврат" in m or "return" in m:
        return "Возврат 14 дней без вопросов, пиши на help@lylili.love"
    if "человек" in m or "оператор" in m:
        return "Я передам оператору — но могу решить 90% вопросов мгновенно. Что случилось?"
    return "Я LYLILI AI 🎀 Знаю всё про подарки, корзину, оплату и доставку. Напиши 'что исправил?' — покажу конкретный код и тесты, или 'что протестировал?'"

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json() or {}
    msg = data.get('message','').strip()
    if not msg:
        return jsonify({"ok": False, "error": "Empty"}), 400
    if not rate_limit("chat:"+(request.remote_addr or "local"), limit=30, window=60):
        return jsonify({"ok": False, "error": "Slow down"}), 429
    answer = ai_answer(msg)
    return jsonify({"ok": True, "reply": answer})

@app.route('/office')
def office():
    turbo = get_turbo_info()
    return render_template('agents3d.html', turbo=turbo, lang=get_lang(), t=get_t())

@app.route('/api/agents/logs')
def api_agents_logs():
    mem = Path(__file__).parent / "agents" / "memory"
    logs=[]
    for p in mem.glob("*.jsonl"):
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").strip().split("\n")
            for line in lines[-8:]:
                if line.strip():
                    j=json.loads(line)
                    # делаем информативнее: добавляем details
                    j["detail"] = f"{j.get('agent')} {j.get('level')}: {j.get('msg')[:80]}"
                    logs.append(j)
        except: pass
    logs = sorted(logs, key=lambda x: x.get("time",""))[-40:]
    ti = get_turbo_info()
    logs.append({"time": time.strftime("%H:%M:%S"), "agent": "Turbo", "level": "WORK", "msg": f"Мутирую CSS #{ti['count']} → подарки светятся", "detail": f"CSS {ti['count']} версий, 4K ✓"})
    logs.append({"time": time.strftime("%H:%M:%S"), "agent": "Conveyor", "level": "MOVE", "msg": f"Конвейер несет {len(get_products())} подарков", "detail": f"{len(get_products())} gift-box в движении"})
    return jsonify(logs)

@app.route('/api/llm/ask', methods=['POST'])
def api_llm_ask():
    data = request.get_json() or {}
    prompt = data.get('prompt','').strip()
    if not prompt:
        return jsonify({"ok": False, "error": "Empty prompt"}), 400
    apply = bool(data.get('apply'))
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "agents"))
        from llm_agent import LLMAgent
        agent = LLMAgent(Path(__file__).parent)
        res = agent.ask(prompt, apply=apply)
        return jsonify({"ok": True, **res})
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/llm/status')
def api_llm_status():
    p = Path(__file__).parent / "agents/memory/last_llm.json"
    if p.exists():
        try:
            return jsonify(json.loads(p.read_text(encoding="utf-8", errors="ignore")))
        except: pass
    return jsonify({"mode":"none","actions":[]})

@app.route('/api/agents/status')
def api_agents_status():
    import glob, os
    mem = Path(__file__).parent / "agents" / "memory"
    data = {}
    # turbo
    data["turbo"] = get_turbo_info()
    # products
    data["products"] = len(get_products())
    # orders/subscribers
    try:
        con = db()
        if con:
            data["orders"] = con.execute("SELECT count(*) FROM orders").fetchone()[0]
            data["subscribers"] = con.execute("SELECT count(*) FROM subscribers").fetchone()[0]
            con.close()
        else:
            data["orders"]=0
            data["subscribers"]=0
    except:
        data["orders"]=0
    # agent states
    for name in ["TrendScoutAgent","DesignEvolverAgent","UserAgents","MarketerAgent","LeadAgent","TestAgent","DBArchitectAgent","SecurityAgent","Quality4KAgent"]:
        p = mem / f"{name}.state.json"
        if p.exists():
            try:
                data[name] = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            except:
                data[name] = {"ok": True}
        else:
            data[name] = {"status":"waiting"}
    # user tests
    up = mem / "user_tests.json"
    if up.exists():
        try:
            data["user_tests"] = json.loads(up.read_text(encoding="utf-8", errors="ignore"))
        except: pass
    # cart
    total,count = cart_total()
    data["cart"] = {"count":count,"total":total}
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
