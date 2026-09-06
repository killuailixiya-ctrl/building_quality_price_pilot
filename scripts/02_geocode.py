import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wuhan_pilot.geocode import run_geocode


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-api", action="store_true")
    args = parser.parse_args()
    print(run_geocode(use_api=args.use_api))


