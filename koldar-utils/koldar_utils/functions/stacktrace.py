import os
import re
import traceback
from pathlib import Path
from typing import List


def filter_django_stack() -> List[str]:
    def filter_pycharm(line: traceback.FrameSummary) -> bool:
        return "JetBrains" not in Path(line.filename).parts

    def filter_python(line: traceback.FrameSummary) -> bool:
        for s in Path(line.filename).parts:
            if s.startswith("Python"):
                return False
        else:
            return True

    def filter_venv(line: traceback.FrameSummary) -> bool:
        for s in Path(line.filename).parts:
            if s.startswith("site-packages"):
                return False
        else:
            return True

    return list(map(
        lambda fs: f"{fs.name} @ {fs.lineno} in file: \"{fs.filename}\"",
        filter(filter_venv,
               filter(filter_python,
                      filter(filter_pycharm, list(traceback.extract_stack())[:-2]
                             )))))