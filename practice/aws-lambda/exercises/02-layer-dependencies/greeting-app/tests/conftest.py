import sys
from pathlib import Path

# Lambda adds the layer's python/ folder to the import path. Do the same with the
# layer source so unit tests can import it before `sam build`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "layers" / "greeting"))
