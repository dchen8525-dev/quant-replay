from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FactorEvaluation:
    table: pd.DataFrame
    summary: pd.DataFrame
