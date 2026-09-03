from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path(os.getenv("POLICYGPT_DB", "policygpt.db"))
    corpus_path: Path = Path(os.getenv("POLICYGPT_CORPUS", "data/policies.json"))
    report_dir: Path = Path(os.getenv("POLICYGPT_REPORT_DIR", "reports"))
    confidence_threshold: float = float(os.getenv("POLICYGPT_CONFIDENCE_THRESHOLD", "0.75"))
    hallucination_threshold: float = float(os.getenv("POLICYGPT_HALLUCINATION_THRESHOLD", "0.25"))


settings = Settings()
