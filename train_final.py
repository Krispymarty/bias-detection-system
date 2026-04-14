import pandas as pd
from pipeline.model import train_model, save_model

print("Loading final_merged_cleaned.csv...")
df = pd.read_csv("data/final_merged_cleaned.csv")

# We expect TARGET and potentially DAYS_BIRTH/AMT_INCOME_TOTAL to exist for engineering
features = [f for f in df.columns if f != "TARGET"]
X_raw = df[features]
y = df["TARGET"]

print("Training production model on selected features...")
bundle = train_model(X_raw, y)

save_path = "pipeline/production_model.joblib"
save_model(bundle, save_path)

print(f"Model successfully trained and saved to {save_path}")
print(f"Captured Columns during Training (for inference alignment):")
print(bundle["training_columns"])
print("\nIncome Bins Captured:")
print(bundle["income_bins"])
