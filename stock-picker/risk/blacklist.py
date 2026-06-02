"""黑名单管理."""
import json
import os
from pathlib import Path


class Blacklist:
    """管理不可投资的股票黑名单."""

    def __init__(self, filepath: str = "blacklist.json"):
        self.filepath = Path(filepath)
        self._codes: set[str] = set()
        self._reasons: dict[str, str] = {}
        self.load()

    def load(self):
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._codes = set(data.get("codes", []))
                self._reasons = data.get("reasons", {})
            except Exception:
                pass

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump({"codes": list(self._codes), "reasons": self._reasons}, f, ensure_ascii=False, indent=2)

    def add(self, code: str, reason: str = ""):
        self._codes.add(code)
        if reason:
            self._reasons[code] = reason
        self.save()

    def remove(self, code: str):
        self._codes.discard(code)
        self._reasons.pop(code, None)
        self.save()

    def contains(self, code: str) -> bool:
        return code in self._codes

    def filter(self, codes: list[str]) -> list[str]:
        return [c for c in codes if c not in self._codes]

    @property
    def codes(self) -> set[str]:
        return self._codes

    def list_all(self) -> list[tuple[str, str]]:
        return [(c, self._reasons.get(c, "")) for c in sorted(self._codes)]
