"""
FullPipeline — полномасштабный процесс реализации сайта от идеи до роста
Запуск: python agents/full_pipeline.py
Шаги: Discovery -> Design -> Dev -> Test (UserAgents) -> Marketing -> Lead -> Turbo
"""
import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from trend_scout import TrendScoutAgent
from db_architect import DBArchitectAgent
from security_agent import SecurityAgent
from quality_4k_agent import Quality4KAgent
from design_evolver import DesignEvolverAgent
from ux_optimizer import UXOptimizerAgent
from content_curator import ContentCuratorAgent
from user_agents import UserAgents
from marketer import MarketerAgent
from lead import LeadAgent
from test_agent import TestAgent

ROOT = Path(__file__).parent.parent
STEPS = [
    ("Discovery: TrendScout", lambda: TrendScoutAgent(ROOT).safe_run()),
    ("DB Architect", lambda: DBArchitectAgent(ROOT).safe_run()),
    ("Security Premium", lambda: SecurityAgent(ROOT).safe_run()),
    ("4K Quality", lambda: Quality4KAgent(ROOT).safe_run()),
    ("Design Evolver", lambda: DesignEvolverAgent(ROOT).safe_run()),
    ("UX Optimizer", lambda: UXOptimizerAgent(ROOT).safe_run()),
    ("Content Curator", lambda: ContentCuratorAgent(ROOT).safe_run()),
    ("USER TESTS: 5 персон", lambda: UserAgents(ROOT).safe_run()),
    ("MARKETING: SEO/SMM/Ads", lambda: MarketerAgent(ROOT).safe_run()),
    ("TEST: perf/security", lambda: TestAgent(ROOT).safe_run()),
    ("LEAD: full check + roadmap", lambda: LeadAgent(ROOT).safe_run()),
]

if __name__ == "__main__":
    print("=== FULL PIPELINE: полномасштабная реализация LYLILI ===")
    results={}
    for name, fn in STEPS:
        print(f"\n[{name}]...")
        r=fn()
        results[name]=r
        time.sleep(0.6)
    # сводка
    lead = Path(__file__).parent / "memory" / "lead_report.json"
    users = Path(__file__).parent / "memory" / "user_tests.json"
    mark = Path(__file__).parent / "memory" / "marketing.json"
    print("\n=== PIPELINE DONE ===")
    if lead.exists():
        import json as J
        d=J.loads(lead.read_text(encoding="utf-8"))
        print(f"Lead: {d.get('passed')} -> {d.get('decision')}")
        print(f"Roadmap done: {sum(1 for p in d.get('roadmap',[]) if p.get('done'))}/{len(d.get('roadmap',[]))}")
    if users.exists():
        u=json.loads(users.read_text(encoding="utf-8"))
        print(f"UserAgents: {u.get('passed')}/{u.get('tested')} passed")
        print(f"Insights: {u.get('insights')}")
    if mark.exists():
        m=json.loads(mark.read_text(encoding="utf-8"))
        print(f"Marketing: {list(m.get('emails',{}).keys())} + {len(m.get('smm',[]))} SMM")
    print("\nСайт: http://127.0.0.1:5000/ | http://127.0.0.1:5000/cart | http://127.0.0.1:5000/checkout")
    print("Чат: клик 💬 | Корзина: работает | Оплата: 4242 4242 4242 4242")
