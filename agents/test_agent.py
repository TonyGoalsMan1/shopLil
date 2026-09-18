"""
TestAgent — автономно тестирует сайт (функционал, визуал, производительность)
"""
import json
import time
import sqlite3
from pathlib import Path
from base import Agent

class TestAgent(Agent):
    name = "TestAgent"
    interval_hours = 2

    def run(self):
        base = "http://127.0.0.1:5000"
        results = {}
        try:
            import requests
            # 1. Функционал
            r = requests.get(base + "/", timeout=6)
            results["shop_status"] = r.status_code
            results["has_gifts"] = "gift-card" in r.text
            results["has_unicorn"] = "Unicorn" in r.text
            r2 = requests.get(base + "/about", timeout=6)
            results["about_status"] = r2.status_code
            # api
            r3 = requests.get(base + "/api/cart", timeout=6)
            results["api_cart"] = r3.json()
            # add to cart
            r4 = requests.post(base + "/api/cart/add", json={"id": 1}, timeout=6)
            results["add_cart"] = r4.json().get("ok") is True
            # security headers
            r5 = requests.get(base + "/", timeout=6)
            results["security_headers"] = {k: r5.headers.get(k) for k in ["Content-Security-Policy","X-Frame-Options","X-Content-Type-Options"] if r5.headers.get(k)}
            results["has_security_headers"] = len(results["security_headers"]) >= 2
            # performance
            start = time.time()
            requests.get(base + "/", timeout=6)
            results["response_ms"] = int((time.time()-start)*1000)
            results["perf_ok"] = results["response_ms"] < 800
            # 4K check
            css = (self.site_root / "static" / "css" / "style.css").read_text(encoding="utf-8")
            results["has_4k"] = "4K ULTRA" in css
            results["has_min"] = (self.site_root / "static" / "css" / "style.min.css").exists()
            # DB check
            db = self.site_root / "lylili.db"
            results["db_exists"] = db.exists()
            if db.exists():
                con = sqlite3.connect(db)
                cur = con.cursor()
                cur.execute("SELECT count(*) FROM products")
                results["db_products"] = cur.fetchone()[0]
                cur.execute("PRAGMA integrity_check")
                results["db_integrity"] = cur.fetchone()[0]
                con.close()
            # overall
            results["passed"] = all([results["shop_status"]==200, results["has_gifts"], results["api_cart"] is not None, results["response_ms"]<2000])
        except Exception as e:
            results["error"] = str(e)
            self.log("ERROR", str(e))

        out = Path(__file__).parent / "memory" / "test_report.json"
        out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        self.log("INFO", f"tests: {results}")
        self.save_state(results)
        # если провален — триггерим фикс
        if not results.get("passed"):
            self.log("WARN", "tests failed, will retry next cycle")
        return results
