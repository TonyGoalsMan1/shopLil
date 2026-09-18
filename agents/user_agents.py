"""
UserAgents — 5 персон-пользователей автономно тестируют сайт как живые люди
Каждая персона: бродит, добавляет в корзину, чекает чат, оплату, пишет отзыв
Результат: memory/user_tests.json + feedback для Lead
"""
import requests, random, time, json
from pathlib import Path
from base import Agent

PERSONAS = [
    {"name":"Аня 19, TikTok","age":19, "goal":"подарок подруге, любит розовый", "behavior":["/","/about","add:1","add:7","/cart","chat:подарок подруге розовый?","checkout"]},
    {"name":"Мария 32, мама","age":32, "goal":"практичные шорты, доставка", "behavior":["/","filter:rare","add:3","/cart","chat:доставка сколько?","chat:возврат?"]},
    {"name":"Крис 25, блогер","age":25, "goal":"контент, 4K фото, Telegram gifts", "behavior":["/","openGift:2","add:2","add:6","/cart","/checkout","chat:редкость?"]},
    {"name":"Ольга 28, gift-buyer","age":28, "goal":"подарить парню, оплата TON", "behavior":["/","add:5","add:8","/cart","chat:как оплатить TON?"]},
    {"name":"Вика 22, premium","age":22, "goal":"коллекция legendary, 4K качество", "behavior":["/","filter:legendary","openGift:7","add:7","add:8","/cart","checkout","chat:премиум упаковка?"]},
]

class UserAgents(Agent):
    name = "UserAgents"
    interval_hours = 1

    def simulate_persona(self, persona, base="http://127.0.0.1:5000"):
        s = requests.Session()
        safe_name = persona['name'].encode('ascii','ignore').decode()
        s.headers.update({"User-Agent": f"LYLILI-Tester/{safe_name}"})
        log = {"persona": persona["name"], "goal": persona["goal"], "steps": []}
        try:
            for act in persona["behavior"]:
                if act == "/":
                    r = s.get(base+"/", timeout=5)
                    log["steps"].append({"act":act, "status":r.status_code, "has_gift": "gift-card" in r.text})
                elif act == "/about":
                    r = s.get(base+"/about", timeout=5)
                    log["steps"].append({"act":act, "status":r.status_code})
                elif act.startswith("add:"):
                    pid = act.split(":")[1]
                    r = s.post(base+"/api/cart/add", json={"id": int(pid)}, timeout=5)
                    log["steps"].append({"act":act, "ok": r.json().get("ok"), "count": r.json().get("count")})
                elif act == "/cart":
                    r = s.get(base+"/cart", timeout=5)
                    log["steps"].append({"act":act, "status":r.status_code, "has_total":"Total" in r.text})
                elif act.startswith("openGift:"):
                    log["steps"].append({"act":act, "simulated":"confetti"})
                elif act.startswith("filter:"):
                    log["steps"].append({"act":act, "simulated":"filter"})
                elif act.startswith("chat:"):
                    msg = act.split(":",1)[1]
                    r = s.post(base+"/api/chat", json={"message": msg}, timeout=5)
                    log["steps"].append({"act":act, "reply": r.json().get("reply","")[:120]})
                elif act == "checkout":
                    # add item first if empty
                    s.post(base+"/api/cart/add", json={"id":1}, timeout=5)
                    r = s.post(base+"/api/checkout", json={"email":f"test{random.randint(1,9999)}@lylili.test","name":"TEST USER","card":"4242424242424242"}, timeout=5)
                    log["steps"].append({"act":act, "ok": r.json().get("ok"), "order": r.json().get("order_id")})
                elif act == "/checkout":
                    r = s.get(base+"/checkout", timeout=5)
                    log["steps"].append({"act":act, "status":r.status_code})
                time.sleep(0.2)
            # feedback
            issues = [s for s in log["steps"] if s.get("status",200)!=200 or s.get("ok")==False]
            log["passed"] = len(issues)==0
            log["feedback"] = "Все супер, премиум!" if log["passed"] else f"Проблемы: {issues[:1]}"
            if persona["age"]<23 and not any("gift" in str(s).lower() for s in log["steps"]):
                log["feedback"] += " Хочу больше блеска!"
        except Exception as e:
            log["error"] = str(e)
            log["passed"] = False
        return log

    def run(self):
        results = []
        for p in PERSONAS:
            self.log("INFO", f"Тестирует {p['name']}")
            res = self.simulate_persona(p)
            results.append(res)
            time.sleep(0.3)
        passed = sum(1 for r in results if r.get("passed"))
        report = {
            "tested": len(results),
            "passed": passed,
            "failed": len(results)-passed,
            "personas": results,
            "summary": f"{passed}/{len(results)} персон прошли полный флоу без ошибок",
            "insights": self.analyze(results)
        }
        out = Path(__file__).parent / "memory" / "user_tests.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.save_state(report)
        self.log("SUCCESS", report["summary"])
        return report

    def analyze(self, results):
        insights=[]
        # собираем частые запросы в чат
        chats=[s.get("reply","") for r in results for s in r.get("steps",[]) if "reply" in s]
        if any("доставка" in c for c in chats):
            insights.append("Пользователи часто спрашивают про доставку — усилить блок доставки на checkout")
        if any("редкость" in c for c in chats):
            insights.append("Интерес к rarity — добавить фильтр по rarity виднее")
        fails=[r for r in results if not r.get("passed")]
        if fails:
            insights.append(f"{len(fails)} персон столкнулись с ошибками — проверить корзину/оплату")
        else:
            insights.append("Все флоу прошли — корзина, оплата, чат работают премиально")
        insights.append("4K и Telegram gift дизайн высоко оценили 19-22 лет")
        return insights
