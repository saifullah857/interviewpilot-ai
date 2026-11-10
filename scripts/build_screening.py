"""Rebuilds data/questions/screening/screening.json (MCQ and output questions). Output answers are computed by running the code."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screening_a, screening_b, sq  # noqa: E401

screening_a.define()
screening_b.define()
out = sq.write()
print(len(out), "screening questions written")
