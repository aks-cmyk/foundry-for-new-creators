"""Seed the Foundry demo ledger from foundry/data/seed.json."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry import ledger  # noqa: E402

DB = ROOT / "foundry" / "data" / "foundry.db"
SEED = ROOT / "foundry" / "data" / "seed.json"


def main():
    conn = ledger.connect(DB)
    result = ledger.load_seed(conn, SEED)
    print(f"Seeded {DB}: {result}")
    print(f"Counts: {ledger.counts(conn)}")


if __name__ == "__main__":
    main()
