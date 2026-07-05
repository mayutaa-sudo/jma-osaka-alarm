import json
from datetime import datetime
from pathlib import Path

result = {
    "warning": False,
    "checked_at": datetime.now().isoformat()
}

Path("docs").mkdir(exist_ok=True)

with open("docs/warning.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("warning.json を更新しました")
