import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wuhan_pilot.prepare_anjuke import run_prepare


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count-files", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run_prepare(count_files=args.count_files, limit=args.limit)

