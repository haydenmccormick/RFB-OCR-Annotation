import pandas as pd
import requests
from tqdm import tqdm

def get_full_path(guid):
    url = f"http://eldrad.cs-i.brandeis.edu:23456/searchapi?file=video&guid={guid}"
    response = requests.get(url)
    data = response.json()
    return data[0]

tqdm.pandas()

df = pd.read_csv("doctr-preds.csv")
df["path"] = df["guid"].progress_apply(get_full_path)
df["ocr_accepted"] = False
df["deleted"] = False
df["annotated"] = False
df["label_adjusted"] = False
df.to_csv("doctr-preds-with-paths.csv", index=False)