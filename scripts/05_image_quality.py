import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wuhan_pilot.image_quality import run_image_proxy


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-communities", type=int, default=None)
    parser.add_argument("--max-per-community", type=int, default=6)
    args = parser.parse_args()
    print(
        run_image_proxy(
            max_communities=args.max_communities,
            max_per_community=args.max_per_community,
        )
    )
