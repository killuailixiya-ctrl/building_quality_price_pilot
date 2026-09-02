import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wuhan_pilot.data_inventory import run_inventory


if __name__ == "__main__":
    print(run_inventory())
