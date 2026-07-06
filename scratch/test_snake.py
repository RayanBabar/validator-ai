
import re

def _to_snake(s: str) -> str:
    """Convert camelCase / PascalCase to snake_case."""
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
    return s.lower()

test_keys = ["MVP_weeks", "MVP_features", "MVP_monthly", "mvp_weeks", "mvpWeeks"]
for k in test_keys:
    print(f"{k} -> {_to_snake(k)}")
