from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
@dataclass(frozen=True)
class Config:
    db_path: Path
    report_dir: Path
    duplicate_threshold: float

def load_config(root:Path)->Config:
    return Config(Path(os.getenv('OWRP_DB_PATH',root/'data'/'owrp.sqlite')),Path(os.getenv('OWRP_REPORT_DIR',root/'reports')),float(os.getenv('OWRP_DUPLICATE_THRESHOLD','0.72')))
