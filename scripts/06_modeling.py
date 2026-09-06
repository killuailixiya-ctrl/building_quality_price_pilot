import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wuhan_pilot.modeling import run_modeling


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-csv", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--target", default="block_price")
    args = parser.parse_args()
    print(run_modeling(args.feature_csv, args.output_dir, args.target))

