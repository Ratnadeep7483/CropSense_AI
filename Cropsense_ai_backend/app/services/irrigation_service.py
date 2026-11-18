from pathlib import Path

import joblib
import pandas as pd


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "ml"
    / "irrigation"
    / "krishitrust_lightgbm_11_features.joblib"
)

FEATURES = [
    "Temperature_C",
    "Humidity",
    "Rainfall_mm",
    "Sunlight_Hours",
    "Soil_Type",
    "Crop_Type",
    "Crop_Growth_Stage",
    "Season",
    "Soil_Moisture",
    "Wind_Speed_kmh",
    "Mulching_Used",
]

CATEGORICAL_VALUES = {
    "Soil_Type": ["Clay", "Loamy", "Sandy", "Silt"],
    "Crop_Type": ["Cotton", "Maize", "Potato", "Rice", "Sugarcane", "Wheat"],
    "Crop_Growth_Stage": ["Flowering", "Harvest", "Sowing", "Vegetative"],
    "Season": ["Kharif", "Rabi", "Zaid"],
    "Mulching_Used": ["No", "Yes"],
}


class IrrigationService:
    def __init__(self) -> None:
        self.model = None
        self.label_encoder = None
        self.is_loaded = False
        self.load_error: str | None = None

    def load_model(self) -> None:
        try:
            bundle = joblib.load(MODEL_PATH)
            model = bundle["model"]
            label_encoder = bundle["label_encoder"]
            if bundle.get("features") != FEATURES:
                raise RuntimeError("Irrigation bundle feature order mismatch.")
            if list(label_encoder.classes_) != ["High", "Low", "Medium"]:
                raise RuntimeError("Irrigation label order mismatch.")
            self.model = model
            self.label_encoder = label_encoder
            self.is_loaded = True
            self.load_error = None
        except Exception as exc:
            self.model = None
            self.label_encoder = None
            self.is_loaded = False
            self.load_error = str(exc)

    def predict(self, payload: dict) -> tuple[str, dict[str, float]]:
        if not self.is_loaded or self.model is None or self.label_encoder is None:
            raise RuntimeError("Irrigation model is unavailable.")
        frame = pd.DataFrame(
            [{name: payload[name] for name in FEATURES}],
            columns=FEATURES,
        )
        encoded_class = int(self.model.predict(frame)[0])
        probability_values = self.model.predict_proba(frame)[0]
        prediction = str(self.label_encoder.inverse_transform([encoded_class])[0])
        probabilities = {
            str(label): float(probability_values[index])
            for index, label in enumerate(self.label_encoder.classes_)
        }
        return prediction, probabilities


irrigation_service = IrrigationService()
