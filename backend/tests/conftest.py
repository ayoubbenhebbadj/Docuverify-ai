import os
import sys
from pathlib import Path

# Must run before app.ai_extractor is imported: it reads the provider settings
# (and would otherwise load a developer's real backend/.env).
os.environ["AI_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "test-key"
os.environ["OPENROUTER_MODEL"] = "test-model"
os.environ.pop("OPENROUTER_VISION_MODEL", None)
os.environ.pop("AI_REASONING", None)
os.environ.pop("EXTRACTION_EVIDENCE", None)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
