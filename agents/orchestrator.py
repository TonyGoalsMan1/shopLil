"""
Orchestrator — запускает всех агентов автономно по расписанию и по команде
Запуск: python agents/orchestrator.py  (один прогон) 
       python agents/orchestrator.py --loop (вечный loop)
       python agents/orchestrator.py --schedule (APSheduler)
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# добавляем путь
sys.path.insert(0, str(Path(__file__).parent))

from base import Agent
from trend_scout import TrendScoutAgent
from design_evolver import DesignEvolverAgent
from ux_optimizer import UXOptimizerAgent
from content_curator import ContentCuratorAgent
from db_architect import DBArchitectAgent
from security_agent import SecurityAgent
from quality_4k_agent import Quality4KAgent
from test_agent import TestAgent

SITE_ROOT = Path(__file__).parent.parent

AGENTS = [
    TrendScoutAgent(SITE_ROOT),
    DBArchitectAgent(SITE_ROOT),
    SecurityAgent(SITE_ROOT),
    Quality4KAgent(SITE_ROOT),
    DesignEvolverAgent(SITE_ROOT),
    UXOptimizerAgent(SITE_ROOT),
    ContentCuratorAgent(SITE_ROOT),
    TestAgent(SITE_ROOT),
]

def run_once():
    print(f"\n=== LYLILI AUTONOMOUS AGENTS - run {datetime.now().isoformat()} ===\n")
    results = {}
    for agent in AGENTS:
        print(f"-> {agent.name} ...")
        res = agent.safe_run()
        results[agent.name] = res
        time.sleep(0.5)
    # сводный отчет
    report_path = Path(__file__).parent / "memory" / "last_run.json"
    report_path.write_text(json.dumps({"time": datetime.now().isoformat(), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] All agents done. Report -> {report_path}")
    # перезапускаем Flask если меняли CSS/app.py
    try:
        import requests
        # touch для автоперезагрузки (если debug)
        print("-> Trigger Flask reload (touch app.py)")
        app_py = SITE_ROOT / "app.py"
        if app_py.exists():
            app_py.touch()
    except: pass
    return results

def loop_forever(interval_minutes=60):
    print(f"LOOP mode: every {interval_minutes} min")
    while True:
        run_once()
        print(f"\nSleep {interval_minutes} min ...")
        time.sleep(interval_minutes*60)

def schedule_mode():
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except ImportError:
        print("APScheduler not installed, falling back to loop")
        return loop_forever(180)
    sched = BlockingScheduler()
    sched.add_job(lambda: TrendScoutAgent(SITE_ROOT).safe_run(), 'interval', hours=2, id='scout')
    sched.add_job(lambda: DBArchitectAgent(SITE_ROOT).safe_run(), 'interval', hours=24, id='db')
    sched.add_job(lambda: SecurityAgent(SITE_ROOT).safe_run(), 'interval', hours=6, id='sec')
    sched.add_job(lambda: Quality4KAgent(SITE_ROOT).safe_run(), 'interval', hours=12, id='4k')
    sched.add_job(lambda: DesignEvolverAgent(SITE_ROOT).safe_run(), 'interval', hours=8, id='evolver')
    sched.add_job(lambda: UXOptimizerAgent(SITE_ROOT).safe_run(), 'interval', hours=12, id='ux')
    sched.add_job(lambda: ContentCuratorAgent(SITE_ROOT).safe_run(), 'interval', hours=12, id='content')
    sched.add_job(lambda: TestAgent(SITE_ROOT).safe_run(), 'interval', minutes=30, id='test')
    print("Scheduler started: Scout 2h, DB 24h, Sec 6h, 4K 12h, Evolver 8h, UX 12h, Content 12h, Test 30m — 4K quality + security + DB")
    print("Press Ctrl+C to stop")
    sched.start()

if __name__ == "__main__":
    if "--schedule" in sys.argv:
        schedule_mode()
    elif "--loop" in sys.argv:
        mins = int(sys.argv[sys.argv.index("--loop")+1]) if len(sys.argv) > sys.argv.index("--loop")+1 and sys.argv[sys.argv.index("--loop")+1].isdigit() else 60
        loop_forever(mins)
    else:
        run_once()
