import time
import json
import traceback
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).parent / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

class Agent:
    name = "BaseAgent"
    interval_hours = 6  # how often to run autonomously
    def __init__(self, site_root: Path):
        self.site_root = Path(site_root)
        self.log_file = MEMORY_DIR / f"{self.name}.jsonl"
        self.state_file = MEMORY_DIR / f"{self.name}.state.json"

    def log(self, level, msg, data=None):
        entry = {"time": datetime.now().isoformat(), "agent": self.name, "level": level, "msg": msg, "data": data}
        print(f"[{self.name}] {level}: {msg}")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def save_state(self, state: dict):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def load_state(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        return {}

    def run(self):
        """Override in subclass — one autonomous improvement cycle"""
        raise NotImplementedError

    def safe_run(self):
        try:
            self.log("INFO", "cycle start")
            result = self.run()
            self.log("SUCCESS", "cycle done", result)
            return result
        except Exception as e:
            self.log("ERROR", f"{e}\n{traceback.format_exc()}")
            return {"error": str(e)}
