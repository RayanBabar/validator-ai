"""
Fix History Tracker for consistency fixing.
Tracks fixes across cycles to prevent regressions and infinite loops.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class FixRecord:
    """Record of a single fix applied."""

    issue_hash: str
    modules: List[str]
    target_module: str
    target_state_key: str
    field_path: str
    fix_type: str
    cycle: int
    timestamp: datetime = field(default_factory=datetime.now)


class FixHistory:
    """
    Tracks fix history to prevent regressions and infinite loops.

    In-memory only - resets each compilation session.
    """

    def __init__(self, max_history: int = 50, max_module_fixes: int = 3):
        self.fixes: List[FixRecord] = []
        self.max_history = max_history
        self.max_module_fixes = max_module_fixes
        self._issue_hash_counts: Dict[str, int] = {}

    def generate_issue_hash(self, issue: Dict) -> str:
        """Generate deterministic hash for issue identification."""
        modules = sorted(issue.get("modules", []))
        issue_text = issue.get("issue", "")
        content = json.dumps({"modules": modules, "issue": issue_text}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_issue_repeated(self, issue: Dict) -> bool:
        """Check if we've seen this exact issue before."""
        issue_hash = self.generate_issue_hash(issue)
        return self._issue_hash_counts.get(issue_hash, 0) >= 2

    def record_fix(
        self,
        issue: Dict,
        target_module: str,
        target_state_key: str,
        field_path: str,
        fix_type: str,
        cycle: int,
    ):
        """Record a fix that was applied."""
        issue_hash = self.generate_issue_hash(issue)

        record = FixRecord(
            issue_hash=issue_hash,
            modules=issue.get("modules", []),
            target_module=target_module,
            target_state_key=target_state_key,
            field_path=field_path,
            fix_type=fix_type,
            cycle=cycle,
        )

        self.fixes.append(record)
        self._issue_hash_counts[issue_hash] = (
            self._issue_hash_counts.get(issue_hash, 0) + 1
        )

        # Trim history if needed
        if len(self.fixes) > self.max_history:
            self.fixes = self.fixes[-self.max_history :]

        logger.debug(
            f"Recorded fix: {target_module} (cycle {cycle}), total fixes: {len(self.fixes)}"
        )

    def get_module_fix_count(self, module: str) -> int:
        """Get how many times a module was fixed."""
        return sum(1 for f in self.fixes if f.target_module == module)

    def is_module_over_fixed(self, module: str) -> bool:
        """Check if a module has been fixed too many times."""
        return self.get_module_fix_count(module) >= self.max_module_fixes

    def should_skip_issue(
        self,
        issue: Dict,
        target_module: str,
    ) -> tuple[bool, str]:
        """
        Determine if we should skip fixing this issue.

        Returns:
            (should_skip, reason)
        """
        # Skip if we've fixed this module too many times
        if self.is_module_over_fixed(target_module):
            fix_count = self.get_module_fix_count(target_module)
            return (
                True,
                f"Module {target_module} already fixed {fix_count} times (max {self.max_module_fixes})",
            )

        # Skip if we've seen this exact issue too many times
        if self.is_issue_repeated(issue):
            issue_hash = self.generate_issue_hash(issue)
            count = self._issue_hash_counts.get(issue_hash, 0)
            return True, f"Issue repeated {count} times - skipping to avoid loop"

        return False, ""

    def was_module_just_fixed(self, module: str, current_cycle: int) -> bool:
        """Check if a module was fixed in the immediately previous cycle."""
        if not self.fixes:
            return False

        last_fix = self.fixes[-1]
        return last_fix.target_module == module and last_fix.cycle == current_cycle - 1

    def get_fix_summary(self) -> Dict:
        """Get summary of all fixes."""
        if not self.fixes:
            return {
                "total_fixes": 0,
                "modules_affected": [],
                "fixes_by_module": {},
                "cycles_used": 0,
            }

        modules_affected = list(set(f.target_module for f in self.fixes))

        return {
            "total_fixes": len(self.fixes),
            "modules_affected": modules_affected,
            "fixes_by_module": {
                m: self.get_module_fix_count(m) for m in modules_affected
            },
            "cycles_used": max((f.cycle for f in self.fixes), default=0) + 1,
        }

    def get_recent_fixes(self, limit: int = 5) -> List[Dict]:
        """Get most recent fixes."""
        recent = self.fixes[-limit:] if self.fixes else []
        return [
            {
                "module": f.target_module,
                "field": f.field_path,
                "type": f.fix_type,
                "cycle": f.cycle,
            }
            for f in reversed(recent)
        ]

    def clear(self):
        """Clear all history."""
        self.fixes.clear()
        self._issue_hash_counts.clear()
        logger.debug("Fix history cleared")
