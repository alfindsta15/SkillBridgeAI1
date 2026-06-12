import os
import warnings
import logging

warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
try:
    from huggingface_hub.utils import disable_progress_bars
    disable_progress_bars()
except ImportError:
    pass

logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.ERROR)

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

print("Loading career profiles raw...")
df = pd.read_csv(
    "data/processed/career_profiles_raw.csv"
)

print("Loading model all-MiniLM-L6-v2...")
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Generating embeddings with averaging...")
unique_careers = df["career"].unique()
unique_embeddings = []

for i, career in enumerate(unique_careers):
    profiles = df[df["career"] == career]["profile"].tolist()
    
    emb = model.encode(
        profiles,
        show_progress_bar=False,
        convert_to_numpy=True
    )
    
    avg_emb = np.mean(emb, axis=0)
    unique_embeddings.append(avg_emb)
    
    if (i + 1) % 50 == 0 or (i + 1) == len(unique_careers):
        print(f"Processed {i + 1}/{len(unique_careers)} careers")

embeddings_array = np.array(unique_embeddings)

np.save(
    "data/embeddings/career_embeddings.npy",
    embeddings_array
)

unique_careers_df = pd.DataFrame({"career": unique_careers})
unique_careers_df.to_csv(
    "data/processed/career_profiles.csv",
    index=False
)

print("Saved embeddings and unique careers list.")
print("Shape:", embeddings_array.shape)