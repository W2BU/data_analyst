import pandas as pd
import numpy as numpy
from pathlib import Path

data_file = Path.cwd() / "data" / "ozon_report.csv"
df = pd.read_csv(data_file, skiprows=[0,1,2,3,5])
print(df.head())
