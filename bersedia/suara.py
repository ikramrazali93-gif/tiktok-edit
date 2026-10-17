"""Jana narasi + masa perkataan, guna semula enjin suara projek karung-beras."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "karung-beras"))
import suara  # noqa: E402

suara.ROOT = ROOT
suara.BUILD = ROOT / "build"
suara.LAJU = 1.38   # rentak motivasi lebih laju
suara.JEDA = 0.32
suara.MULA = 0.6

if __name__ == "__main__":
    suara.main()
