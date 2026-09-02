import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wuhan_pilot.geocode import run_geocode


if __name__ == "__main__":
    print(run_geocode())
