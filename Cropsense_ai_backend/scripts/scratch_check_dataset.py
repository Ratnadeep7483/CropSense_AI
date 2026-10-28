import pandas as pd
from pathlib import Path

csv_path = Path("e:/CropSense_AI/Cropsense_ai_backend/data/Copy of crop_recommendation_45_with_year_area.csv")
df = pd.read_csv(csv_path)

print("Unique states:", len(df["state_names"].unique()))
print("Total rows:", len(df))

belgaum = df[(df["state_names"].str.strip() == "Karnataka") & (df["district_names"].str.strip() == "BELGAUM")]
print("Belgaum rows:", len(belgaum))
print("Belgaum seasons:\n", belgaum.groupby("season_names")["crop_names"].nunique())

print("\nClimate column summary:")
print(df[["temperature", "humidity", "rainfall_mm"]].describe())

belgaum_summer = df[(df["state_names"].str.strip() == "Karnataka") & (df["district_names"].str.strip() == "BELGAUM") & (df["season_names"].str.strip() == "Summer")]
print("\nBelgaum Summer climate:")
print(belgaum_summer[["temperature", "humidity", "rainfall_mm", "crop_year"]].drop_duplicates().head(20))

