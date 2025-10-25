import pandas as pd
from typing import Optional

DF: Optional[pd.DataFrame] = None

def set_df(df: pd.DataFrame):
    global DF
    DF = df

def get_df() -> Optional[pd.DataFrame]:
    return DF