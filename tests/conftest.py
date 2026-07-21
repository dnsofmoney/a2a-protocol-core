"""Make the src layout importable when running pytest straight from the repo
(CI and installed environments import the wheel; this is for local dev runs)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
