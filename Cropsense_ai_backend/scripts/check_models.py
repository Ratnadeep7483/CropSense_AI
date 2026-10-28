#!/usr/bin/env python3
"""
CropSense AI — Model Verification Script.

Checks whether all required model files exist, loads them, and
validates the deployed crop artifact dimensions and class mapping.

Usage:
    cd Cropsense_ai_backend
    python scripts/check_models.py
"""

import json
import sys
from pathlib import Path

# Resolve paths relative to the backend project root
BACKEND_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = BACKEND_ROOT / "app" / "ml"

# ── Required files ───────────────────────────────────────────────
ARTIFACT_DIR = ML_DIR / "crop" / "model_artifacts"
CROP_FILES = [
    ARTIFACT_DIR / "crop_xgboost_model.joblib",
    ARTIFACT_DIR / "crop_preprocessor.joblib",
    ARTIFACT_DIR / "crop_label_encoder.joblib",
]

FERTILIZER_FILES = [
    ML_DIR / "fertilizer" / "fertilizer_xgboost.json",
    ML_DIR / "fertilizer" / "fertilizer_model_metadata.json",
]

PREPROCESSING_FILES = [
    ML_DIR / "fertilizer" / "preprocessing" / "fertilizer_feature_config.json",
    ML_DIR / "fertilizer" / "preprocessing" / "fertilizer_label_encoder.joblib",
    ML_DIR / "fertilizer" / "preprocessing" / "fertilizer_preprocessor.joblib",
]

ALL_FILES = CROP_FILES + FERTILIZER_FILES + PREPROCESSING_FILES


def check_files() -> list[str]:
    """Check if all required files exist. Return list of missing paths."""
    missing = []
    print("\n=== Checking model files ===\n")
    for path in ALL_FILES:
        rel = path.relative_to(BACKEND_ROOT)
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"  [OK] {rel}  ({size_kb:.1f} KB)")
        else:
            print(f"  [FAIL] MISSING: {rel}")
            missing.append(str(rel))
    return missing


def check_crop_model() -> bool:
    """Load the deployed crop artifacts and verify their interface."""
    print("\n=== Crop Recommendation Model ===\n")
    try:
        import joblib

        model = joblib.load(CROP_FILES[0])
        preprocessor = joblib.load(CROP_FILES[1])
        label_encoder = joblib.load(CROP_FILES[2])

        feature_names = list(getattr(preprocessor, "feature_names_in_", []))
        output_features = len(preprocessor.get_feature_names_out())
        class_ids = list(getattr(model, "classes_", []))
        label_classes = list(getattr(label_encoder, "classes_", []))

        if len(feature_names) != 12 or model.n_features_in_ != output_features:
            raise ValueError("Crop model and preprocessor feature dimensions do not match.")
        if len(class_ids) != 45 or len(label_classes) != 45:
            raise ValueError("Crop model and label encoder must each expose 45 classes.")
        if class_ids != list(range(len(label_classes))):
            raise ValueError("Crop model class IDs do not align with label encoder indices.")

        print(
            "  [OK] Deployed crop artifacts loaded "
            f"({len(feature_names)} raw features, {output_features} transformed features, "
            f"{len(label_classes)} crop labels)"
        )
        return True
    except Exception as exc:
        print(f"  [FAIL] Crop artifact check FAILED: {exc}")
        return False


def check_fertilizer_model() -> bool:
    """Load and test the fertilizer recommendation model."""
    print("\n=== Fertilizer Recommendation Model ===\n")
    model_path = FERTILIZER_FILES[0]
    if not model_path.exists():
        print("  [FAIL] Model file not found — skipping.")
        return False

    try:
        import xgboost as xgb

        booster = xgb.Booster()
        booster.load_model(str(model_path))
        print("  [OK] Fertilizer model: LOADED")
        return True
    except Exception as exc:
        print(f"  [FAIL] Fertilizer model load FAILED: {exc}")
        return False


def check_preprocessing() -> bool:
    """Load and verify the fertilizer preprocessing artifacts."""
    print("\n=== Fertilizer Preprocessing ===\n")
    all_ok = True

    # Feature config
    config_path = PREPROCESSING_FILES[0]
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            print(f"  [OK] Feature config: LOADED ({len(config)} keys)")
        except Exception as exc:
            print(f"  [FAIL] Feature config FAILED: {exc}")
            all_ok = False
    else:
        print("  [FAIL] Feature config not found — skipping.")
        all_ok = False

    # Label encoder
    encoder_path = PREPROCESSING_FILES[1]
    if encoder_path.exists():
        try:
            import joblib

            encoder = joblib.load(encoder_path)
            print(f"  [OK] Label encoder: LOADED (type: {type(encoder).__name__})")
        except Exception as exc:
            print(f"  [FAIL] Label encoder FAILED: {exc}")
            all_ok = False
    else:
        print("  [FAIL] Label encoder not found — skipping.")
        all_ok = False

    # Preprocessor
    preprocessor_path = PREPROCESSING_FILES[2]
    if preprocessor_path.exists():
        try:
            import joblib

            preprocessor = joblib.load(preprocessor_path)
            print(
                f"  [OK] Preprocessor: LOADED (type: {type(preprocessor).__name__})"
            )
        except Exception as exc:
            print(f"  [FAIL] Preprocessor FAILED: {exc}")
            all_ok = False
    else:
        print("  [FAIL] Preprocessor not found — skipping.")
        all_ok = False

    return all_ok


def main() -> None:
    print("=" * 60)
    print("  CropSense AI -- Model Verification")
    print("=" * 60)

    missing = check_files()

    if missing:
        print(f"\n[!]  {len(missing)} file(s) missing.")
        print("   Please copy them before running the backend.\n")
    else:
        print("\n[OK] All required files are present.\n")

    crop_ok = check_crop_model()
    fert_ok = check_fertilizer_model()
    preproc_ok = check_preprocessing()

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Crop model:       {'OK' if crop_ok else 'MISSING / FAILED'}")
    print(f"  Fertilizer model: {'OK' if fert_ok else 'MISSING / FAILED'}")
    print(f"  Preprocessor:     {'OK' if preproc_ok else 'MISSING / FAILED'}")
    print("=" * 60)

    if not (crop_ok and fert_ok and preproc_ok):
        print("\n[!]  Some models are not ready. Copy the missing files and re-run.\n")
        sys.exit(1)
    else:
        print("\n[OK] All models loaded and verified successfully!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
