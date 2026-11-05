#!/usr/bin/env python3
"""
Wrapper mince : execute le pipeline complet Fibre 360.
Equivalent de `python -m fibre360.cli all`.

Usage : python scripts/run_pipeline.py [--n 60000] [--seed 42] [--config ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fibre360.cli import main  # noqa: E402

if __name__ == "__main__":
    main(["all", *sys.argv[1:]])
