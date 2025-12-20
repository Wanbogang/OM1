import sys
from pathlib import Path

# tambahkan root project ke sys.path agar package 'src' bisa diimport
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
