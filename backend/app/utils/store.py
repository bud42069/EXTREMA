
import pandas as pd

DF: pd.DataFrame | None = None

def set_df(df: pd.DataFrame):
    global DF
    DF = df

def get_df() -> pd.DataFrame | None:
    return DF