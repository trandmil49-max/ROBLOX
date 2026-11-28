# Thin shim so code running inside Blender can import the face generator.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from faces_gen import ensure_face  # noqa: E402,F401
