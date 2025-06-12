# CrashTracker.py — Tracks fatal events for learning

import os
import json
import time
from colorama import Fore, Style

_CACHE_FILE = os.path.expanduser("~/.embryo_crash_log.json")

class CrashTracker:
    def __init__(self):
        self.crashes = []
        self._load()

    def _load(self):
        if not os.path.exists(_CACHE_FILE):
            self.crashes = []
            return

        try:
            with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
                self.crashes = json.load(f)
        except json.JSONDecodeError as e:
            # Corrupted JSON: back it up and start fresh
            backup = _CACHE_FILE + ".bak"
            os.replace(_CACHE_FILE, backup)
            print(f"{Fore.YELLOW}[CRASH TRACKER] Corrupted log; backed up to {backup}{Style.RESET_ALL}")
            self.crashes = []
            # write a new empty log
            try:
                with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f)
            except Exception:
                pass
        except Exception as e:
            print(f"{Fore.RED}[CRASH TRACKER] Failed to load crash log: {e}{Style.RESET_ALL}")
            self.crashes = []

    def _save(self):
        try:
            with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.crashes, f, indent=2)
        except Exception as e:
            print(f"{Fore.RED}[CRASH TRACKER] Failed to save crash log: {e}{Style.RESET_ALL}")

    def record_crash(self, goal: str, phase: str, context: dict = None):
        event = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "goal": goal,
            "phase": phase,
            "context": context or {}
        }
        self.crashes.append(event)
        self._save()
        print(f"{Fore.RED}[CRASH] Logged fatal event: {goal} during {phase} — {event['context']}{Style.RESET_ALL}")

    def log_crash(self, context: dict):
        goal  = context.get("goal",  "unknown")
        phase = context.get("phase", "unknown")
        self.record_crash(goal, phase, context)

    def recent_crashes(self, limit: int = 5):
        return self.crashes[-limit:]

    def recent_crashes_for_goal(self, goal: str, phase: str = None, limit: int = 10):
        return [
            c for c in reversed(self.crashes)
            if c.get("goal") == goal and (phase is None or c.get("phase") == phase)
        ][:limit]

    def crash_count(self):
        return len(self.crashes)

    def clear(self):
        self.crashes = []
        self._save()
        print(f"{Fore.YELLOW}[CRASH TRACKER] Cleared crash history{Style.RESET_ALL}")

    # ─── NEW: Export to JSON ────────────────────────────────────────────
    def to_json(self) -> str:
        """
        Convert the entire crash list to a JSON string.
        """
        return json.dumps(self.crashes)

    # ─── NEW: Reconstruct from JSON ─────────────────────────────────────
    @classmethod
    def from_json(cls, json_str: str) -> "CrashTracker":
        """
        Given the JSON we stored, re-create a CrashTracker instance.
        """
        instance = cls.__new__(cls)
        # Skip calling __init__ so we don't reload from disk immediately
        instance.crashes = json.loads(json_str)
        return instance
