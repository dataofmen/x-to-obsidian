"""
처리된 북마크 ID를 추적해 중복 생성을 방지합니다.
"""

import json
from datetime import datetime
from pathlib import Path


class State:
    def __init__(self, state_file: Path):
        self.path = state_file
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except Exception:
                pass
        return {"processed_ids": [], "last_run": None, "total_notes": 0}

    def is_processed(self, tweet_id: str) -> bool:
        return tweet_id in self._data["processed_ids"]

    def mark_processed(self, tweet_id: str):
        ids = self._data["processed_ids"]
        if tweet_id not in ids:
            ids.append(tweet_id)
            # 최근 2000개만 유지
            self._data["processed_ids"] = ids[-2000:]
            self._data["total_notes"] = self._data.get("total_notes", 0) + 1
        self._save()

    def update_last_run(self):
        self._data["last_run"] = datetime.now().isoformat(timespec="seconds")
        self._save()

    def _save(self):
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2))

    @property
    def total_notes(self) -> int:
        return self._data.get("total_notes", 0)
