"""Reuses the existing EnterpriseSim ``score()`` evaluator, unmodified.

The canonical objective-first scorer for BC-0101 already exists at
``examples/quickstart/run_quickstart.py::score``. Per the experiment brief, this
module does not reimplement or extend it -- in particular it does not invent a
``composition_quality`` scorer, matching the quickstart's own choice to report
objective-only (that rubric metric is model-assisted and explicitly out of scope
here). This module only imports the original function by file path so the
experiment scores against the exact same recipe as the rest of the repo.
"""

from __future__ import annotations

import importlib.util
import pathlib
from typing import Callable

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
QUICKSTART_PATH = REPO_ROOT / "examples" / "quickstart" / "run_quickstart.py"


def _load_quickstart_score() -> Callable[[dict, dict], dict]:
    spec = importlib.util.spec_from_file_location("_quickstart_run", QUICKSTART_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load quickstart module from {QUICKSTART_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.score


#: The real, unmodified ``score()`` from ``examples/quickstart/run_quickstart.py``.
score = _load_quickstart_score()
