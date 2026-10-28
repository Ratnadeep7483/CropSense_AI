
import argparse
import os
import pandas as pd
from xgboost import XGBClassifier


# ============================================================
# Legacy standalone crop model helper.
# The deployed crop API uses the serialized 12-feature artifacts instead.
# XGBOOST INFERENCE
# ============================================================


CROP_CLASSES = [
    "Adzuki Beans",
    "Black gram",
    "Chickpea",
    "Coconut",
    "Coffee",
    "Cotton",
    "Ground Nut",
    "Jute",
    "Kidney Beans",
    "Lentil",
    "Moth Beans",
    "Mung Bean",
    "Peas",
    "Pigeon Peas",
    "Rubber",
    "Sugarcane",
    "Tea",
    "Tobacco",
    "apple",
    "banana",
    "grapes",
    "maize",
    "mango",
    "millet",
    "muskmelon",
    "orange",
    "papaya",
    "pomegranate",
    "rice",
    "watermelon",
    "wheat"
]


SOIL_CATEGORIES = [
    "Acidic Soil",
    "Alkaline Soil",
    "Loamy Soil",
    "Neutral Soil",
    "Peaty Soil"
]


FEATURE_COLUMNS = [
    "Temperature",
    "Humidity",
    "Rainfall",
    "PH",
    "Nitrogen",
    "Phosphorous",
    "Potassium",
    "Carbon",
    "Soil"
]


def get_model_path(model_path):
    """Return the explicitly supplied legacy model path."""
    return os.fspath(model_path)


def load_model(model_path):

    model_path = get_model_path(model_path)

    if not os.path.exists(model_path):

        raise FileNotFoundError(
            "XGBoost model not found:\n"
            + model_path
        )

    model = XGBClassifier(
        enable_categorical=True
    )

    model.load_model(model_path)

    return model


def recommend_crop(
    temperature,
    humidity,
    rainfall,
    ph,
    nitrogen,
    phosphorous,
    potassium,
    carbon,
    soil,
    *,
    model_path,
):

    if soil not in SOIL_CATEGORIES:

        raise ValueError(
            "Invalid soil type: "
            + str(soil)
            + "\nValid soil types:\n"
            + "\n".join(SOIL_CATEGORIES)
        )


    input_data = pd.DataFrame(
        [[
            temperature,
            humidity,
            rainfall,
            ph,
            nitrogen,
            phosphorous,
            potassium,
            carbon,
            soil
        ]],
        columns=FEATURE_COLUMNS
    )


    input_data["Soil"] = pd.Categorical(
        input_data["Soil"],
        categories=SOIL_CATEGORIES
    )


    model = load_model(model_path)


    prediction = model.predict(
        input_data
    )


    crop_id = int(
        prediction[0]
    )


    if crop_id < 0 or crop_id >= len(CROP_CLASSES):

        raise ValueError(
            "Invalid predicted crop ID: "
            + str(crop_id)
        )


    return CROP_CLASSES[crop_id]


def main():
    parser = argparse.ArgumentParser(
        description="Run the legacy standalone crop model helper."
    )
    parser.add_argument(
        "model_path",
        help="Path to a compatible legacy XGBoost JSON model.",
    )
    args = parser.parse_args()

    print("=" * 65)
    print("Legacy crop recommendation helper")
    print("=" * 65)


    recommended_crop = recommend_crop(

        temperature=25.0,

        humidity=70.0,

        rainfall=100.0,

        ph=6.5,

        nitrogen=60.0,

        phosphorous=70.0,

        potassium=70.0,

        carbon=1.5,

        soil="Loamy Soil",

        model_path=args.model_path,
    )


    print()
    print("Recommended Crop:")
    print(recommended_crop)

    print("=" * 65)


if __name__ == "__main__":

    main()
