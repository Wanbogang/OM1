# Make project root importable during tests
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
