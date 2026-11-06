"""Demo: seed the ledger and render the dashboard, then print where it is."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.render_dashboard import render  # noqa: E402
from scripts.seed import main as seed_main  # noqa: E402

if __name__ == "__main__":
    seed_main()
    out = render()
    print(f"Open in a browser: {out}")
    print("Tabs: Proofing Table / Scorekeeper / Bursar. Try Tweak — sharper hook.")
