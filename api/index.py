import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app import app as application
# Vercel expects 'app' or 'application'
app = application
