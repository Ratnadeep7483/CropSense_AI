> **IMPORTANT DEVELOPMENT RULE:**
> Update this document after every significant implementation, model integration, dataset change, API change, architecture change, testing milestone, or bug fix.

# CropSense AI — Project Progress

## 1. Project Overview

CropSense AI is an academic full-stack prototype for agricultural decision support. It combines a React frontend with a Python FastAPI backend. Crop recommendation remains gated pending feature/artifact compatibility checks; the saved EfficientNet-B0 disease classifier and LightGBM yield model are integrated through the backend and frontend.

The project explicitly does **NOT** use IoT hardware or sensors.

## 2. Current Architecture

```
React Frontend (Vite + TypeScript + Tailwind CSS 4)
        │
        │ HTTP / JSON
        ▼
FastAPI Backend (backend .venv: Python 3.11.8)
        │
   ┌────┴───────────┬────────────┬────────────┬────────────┐
   ▼                ▼            ▼            ▼            ▼
Crop Service   Disease Service  Fertilizer   Soil Service  Yield Service
(XGBoost)      (EfficientNet-B0)(XGBoost)    (EffNet-B2)   (LightGBM)
   └────────────────────┴──────────────┘
        ▼
   JSON Response → React Frontend
```

**Key technologies:**
- Frontend: React 19, Vite 8, TypeScript 6, Tailwind CSS 4, React Router 7, Recharts 3
- Backend runtime used for crop artifacts: FastAPI, Uvicorn, Pydantic 2,
  Python 3.11.8, XGBoost 3.2.0, scikit-learn 1.6.1
- Yield artifact runtime: backend `.venv` Python 3.11.8, LightGBM 4.6.0;
  `lightgbm==4.6.0` is declared in `Cropsense_ai_backend/requirements.txt`.
- The workspace Python 3.13 environment with XGBoost 3.4.1 cannot load the
  deployed crop XGBoost artifact (`input stream corrupted`); use the backend
  `.venv` and do not upgrade/replace packages without a compatibility plan.
- Runtime manifest discrepancy: `Cropsense_ai_backend/requirements.txt` calls
  Python 3.13/XGBoost 3.4.1 the validated runtime, but this verification
  loaded the crop artifacts only in the backend `.venv` (Python 3.11.8,
  XGBoost 3.2.0). Do not treat the manifest's runtime claim as artifact
  compatibility evidence.
- Language support: English + Hindi (i18n)

## 3. Project Scope

| # | Module | Technology | IoT Required |
|---|--------|-----------|:------------:|
| 1 | Crop Recommendation | XGBoost | No |
| 2 | Disease Detection | EfficientNet-B0 image classifier | No |
| 3 | Fertilizer Recommendation | XGBoost + Preprocessing | No |
| 4 | Yield Prediction | LightGBM | No |
| 5 | Smart Irrigation | Saved LightGBM classifier; FastAPI-integrated | No |
| 6 | Weather | Verified-location historical lookup API; frontend page remains mock | No |
| 7 | AI Assistant | NLP/RAG (future) | No |
| 8 | English/Hindi Support | i18n system | No |

**IoT is NOT used in this project.**

## 4. Frontend Status

| Page | Route | Status | Data Source |
|------|-------|--------|-------------|
| Landing | `/` | ✅ Working | Static |
| Dashboard | `/dashboard` | ✅ Working | Mock data |
| Crop Recommendation | `/crop-recommendation` | ⚠️ Context form + historical workflow; recommendation gated | Backend historical lookups |
| Fertilizer Recommendation | `/fertilizer-recommendation` | ✅ Integrated | Existing `POST /api/fertilizer/recommend` client |
| Disease Detection | `/disease-detection` | ✅ Integrated | Saved EfficientNet-B0 via `POST /api/disease/predict` |
| Yield Prediction | `/yield-prediction` | ✅ Integrated | Saved LightGBM model API |
| Smart Irrigation | `/irrigation` | ✅ Direct and weather-assisted FastAPI prediction modes integrated | Unified FastAPI on port 8001 |
| Weather | `/weather` | ✅ Working | Mock data |
| AI Assistant | `/assistant` | ✅ Working | Mock data |

### Frontend Status
- The crop form uses exact state/district/season choices, supports soil-image
  classification, and collects farmer-available area in acres for planning.
  The field is read from the named `farmer_available_area_acres` form property;
  the backend converts it to hectares and keeps it separate from historical
  crop-specific cultivated area. Client validation errors remain on the form,
  distinct from network/connection errors.
- The separate historical workflow returns coverage and experimental model
  scores for candidates with complete inputs, but no crop recommendation.
  Climate-feature compatibility and cross-candidate ranking remain
  unvalidated. The existing production inference endpoint remains unchanged.
- Reference lookup panels remain informational; the workflow does not submit
  farmer-entered NPK, model `area`, crop year, temperature, humidity, or
  rainfall. Farmer acreage is a distinct request/response field and is never
  passed to candidate-wise model feature assembly.
- Candidate-specific area is paired with its historical year; candidates
  without area history are marked individually and do not prevent processing
  other candidates. Area keys now trim/collapse whitespace and case-fold
  state, district, season, crop, and soil labels without fuzzy aliases.
  Strictly pre-target-year filtering, exact location/season requirements,
  conflict handling, and the no-soil-filter rule for cultivated area remain.
  Missing diagnostics distinguish no location/season/crop record from rows
  excluded by the year cutoff and note other-season records without using
  cross-season fallback. For each available candidate, the workflow uses the
  existing year-specific NPK lookup (exact location/season/area-year mean),
  historical weather, and strictly prior-year rainfall lookup to assemble the
  exact 12-column row and call the existing preprocessor/model. NPK source
  provenance is accepted based on the project owner's confirmation; climate
  compatibility and score comparability remain unvalidated. Returned scores
  are explicitly experimental and are not recommendations.
- The historical response includes the selected location/season and separate
  scoring blockers versus final-recommendation blockers. Karnataka/BELGAUM
  weather remains unavailable: the exact registry entry exists, but its
  state-qualified administrative crosswalk is pending and no verified
  coordinate evidence exists. No fallback district or guessed coordinates
  are used.
- The historical-weather UI prompt describes the rule (reviewed exact
  state/district identity plus verified reference coordinates) rather than
  implying only the two current pilot locations are supported. The registry
  is generated by the reviewed LGD/crosswalk/coordinate-evidence workflow;
  the legacy registry-builder entry point now delegates to that workflow so
  it cannot silently replace expanded coverage with a hard-coded two-entry
  list. Existing PUNE and MYSORE pilot records are retained during reviewed
  registry rebuilds.
- To add a district, prepare the review templates, use an official LGD state
  snapshot to approve an exact crosswalk (with documented alias/history
  evidence when names differ), then add independently sourced and reviewed
  district-headquarters coordinates and metadata. Build to a candidate JSON,
  inspect its audit, and only then write the runtime registry. The resolver
  never activates pending, ambiguous, or suspicious records.
- `NAMSAI` remains visible as unsupported in the location selector and is
  rejected by backend validation because it is absent from the fitted
  preprocessor's district categories.
- The shared API client reads `VITE_API_BASE_URL` (default:
  `http://127.0.0.1:8001`).
- Yield Prediction loads category options from the saved model schema and
  submits exactly `Crop`, `State_Name`, `District_Name`, and `Season`; no
  untrained numeric inputs or fabricated yield ranges are submitted/displayed.
  District choices are filtered by the selected state using training-observed
  pairs, and changing state clears the district selection. The target is shown
  as `yield_per_area`; metadata does not specify its physical unit.
- The Smart Irrigation page has direct prediction integration. It imports
  now submits directly to the isolated Flask prediction endpoint. It no longer
  imports or renders `mockIrrigationResult` and no longer uses the mock
  one-second delay. The model result and per-class probabilities are rendered
  from the real API response. The weather-assisted endpoint is not yet wired
  into the page.
- Its current crop/soil/growth choices do not match the Flask contract exactly:
  Crop options are Tomato/Maize/Rice/Wheat, but the saved model requires
  Cotton/Maize/Potato/Rice/Sugarcane/Wheat; soil includes Black/Red options
  in the project i18n but the saved model accepts only Clay/Loamy/Sandy/Silt;
  Seedling/Fruiting are not saved growth-stage categories, which require
  Flowering/Harvest/Sowing/Vegetative. The page must canonicalize or restrict
  these choices to the documented 11-feature contract.
- Yield deployment audit: categorical request validation forbids extra fields,
  trims whitespace, normalizes case, and enforces the CSV-backed pair allowlist.
  The saved LightGBM bundle, metadata, and `crop_final.csv` are required at
  backend startup; missing/invalid files leave yield endpoints at HTTP 503 and
  are logged. Runtime verified with backend `.venv` Python 3.11.8, FastAPI
  0.115.6, Pydantic 2.10.4, LightGBM 4.6.0, and pandas 2.2.3. CORS now accepts
  explicit comma-separated `CORS_ORIGINS`; production must set the frontend's
  `VITE_API_BASE_URL` and matching backend origins. The backend does not
  automatically load `.env` files. No Docker/cloud deployment manifest is
  present; package the saved model, metadata, and CSV together. The
  requirements file is not a complete environment lock: the existing backend
  environment has XGBoost 3.2.0 while requirements specifies 3.4.1, so perform
  a clean deployment install/smoke test rather than assuming the whole
  dependency set is reproduced by the yield runtime check.
- Frontend tests, TypeScript check, and production build pass; Vite reports a
  large JavaScript chunk warning.

## 5. Backend Status

| Component | Status |
|-----------|--------|
| FastAPI application | ✅ Created |
| CORS configuration | ✅ Configured (localhost:5173, 127.0.0.1:5173) |
| Health endpoint (`GET /health`) | ✅ Implemented |
| Model status endpoint (`GET /api/model-status`) | ✅ Implemented |
| Crop recommendation endpoint (`POST /api/crop/recommend`) | ✅ Implemented; unchanged and backend tested |
| Historical farmer workflow (`POST /api/crop/recommend-historical`) | ✅ Automatically retrieves historical weather/rainfall and candidate coverage; accepts farmer acreage for planning; reports scoring/recommendation blockers; recommendation remains gated |
| Historical NPK lookup (`POST /api/crop/npk-lookup`) | ✅ Year-specific lookup implemented |
| Historical rainfall lookup (`POST /api/crop/rainfall-lookup`) | ✅ Implemented; values informational/unverified |
| Historical weather lookup | ✅ Implemented for verified registry locations |
| Yield prediction endpoint (`POST /api/yield/predict`) | ✅ Saved categories and CSV-observed state/district pairs enforced; unsupported pairs return 422 |
| Yield category options (`GET /api/yield/options`) | ✅ Saved categories plus training-observed `districts_by_state` |
| Yield service (LightGBM model + category schema + location pairs) | ✅ Model and audited CSV loaded at startup; model artifact is read-only |
| Smart irrigation health endpoint (`GET /health`) | ✅ Available through unified FastAPI on port 8001 |
| Smart irrigation direct prediction (`POST /api/irrigation/predict`) | ✅ Implemented; exact 11-field JSON contract, categorical validation, finite numeric validation |
| Smart irrigation weather prediction (`POST /api/irrigation/predict-from-weather`) | ✅ Implemented; validates state/district, resolves coordinates, and combines daily weather with caller-supplied soil moisture and categorical fields |
| Crop category and state-district validation | ✅ Implemented and tested |
| Fertilizer recommendation endpoint (`POST /api/fertilizer/recommend`) | ✅ Implemented |
| Plant disease endpoint (`POST /api/disease/predict`) | ✅ Implemented; JPEG/PNG/WebP upload, 10 MB limit |
| Crop service (model loading + inference) | ✅ Implemented |
| Disease service (EfficientNet-B0 loading + image inference) | ✅ Loads once at startup; 38-label index mapping validated |
| Fertilizer service (preprocessing + model loading + inference) | ✅ Implemented |
| Pydantic request/response schemas | ✅ Implemented |
| Swagger documentation (`/docs`) | ✅ Auto-generated |
| Model verification script | ✅ Created |

### 5.1 Irrigation Consolidation

Irrigation is now integrated into the existing FastAPI application:

- FastAPI development/startup runs at `127.0.0.1:8001` and serves every
  crop, fertilizer, disease, soil, yield, weather, and irrigation route.
- The separate Flask entrypoint and Flask-only dependency have been removed
  after successful unified startup verification.
- FastAPI lifespan loads
  `app/ml/irrigation/krishitrust_lightgbm_11_features.joblib` once through
  `app/services/irrigation_service.py`; the exact 11-feature order,
  preprocessing Pipeline, label encoder, and SHA-256 artifact are preserved.
- `app/routes/irrigation.py` exposes
  `GET /api/irrigation/weather`,
  `POST /api/irrigation/predict`, and
  `POST /api/irrigation/predict-from-weather`.
- `app/services/irrigation_weather_service.py` preserves the existing Open-Meteo
  provider URLs, UTC one-calendar-day period, unit checks, archive/forecast
  selection, missing-value rejection, sunshine conversion, and
  `Soil_Moisture: not_mapped` behavior.
- `/api/model-status` now reports `irrigation_model.loaded/error`.
- The frontend uses the shared `VITE_API_BASE_URL` and has no separate
  irrigation base URL or port 8002 dependency.

Verified migration behavior:

- Direct valid POST returns `success=true`, `prediction="Medium"`, and the
  existing three probability values.
- Weather-assisted valid POST returns the same prediction/probability contract
  plus the existing `weather` object and caller-preserved soil moisture.
- Missing, extra, invalid category, boolean, and special-float inputs return
  HTTP 400 JSON errors.
- Weather provider failures return HTTP 502 JSON errors.
- Frontend direct/weather modes, loading/error/result states, and 375px
  responsive layout continue to use the shared port 8001 backend.
- The irrigation result card now displays only the final
  `High`, `Medium`, or `Low` recommendation in direct and weather-assisted
  modes. Class probability rows and predicted-class confidence text are
  removed; weather-assisted measurement details remain in a separate
  weather-input panel. The existing prediction API and response contract are
  unchanged.
- The irrigation form starts with no raw numeric or categorical defaults.
  Direct and weather-assisted modes use empty numeric state and helpful
  placeholders; all dropdowns begin with an unselected placeholder option.
  Existing HTML required-field constraints and frontend request builders
  continue to reject incomplete direct or weather-assisted submissions.
- The weather-assisted irrigation form no longer exposes a Weather date
  input. Latitude, longitude, categorical inputs, and farmer-entered soil
  moisture remain required where applicable, and the frontend weather request
  builder does not send a `date` field so the backend default date is used.
- The weather-assisted result still displays its complete weather summary and
  values, but the orange weather-period warning is hidden from the
  farmer-facing UI. The limitation remains unresolved: one-day rainfall and
  sunshine measurements have not been verified as compatible with the model's
  training feature periods.
- Weather-assisted irrigation now replaces latitude and longitude inputs with
  dataset-backed State and District dropdowns. The frontend fetches exact
  location options and clears the district when state changes. The backend
  validates the selected state/district pair, geocodes the district within
  that state, and uses the resolved coordinates for the existing default-date
  weather lookup. Invalid pairs return HTTP 400 and geocoding/provider
  failures return HTTP 502. Direct prediction inputs and logic are unchanged.
- Connection diagnosis (2026-11-18): both frontend clients target
  `http://127.0.0.1:8001`; location lookup uses
  `GET /api/crop/location-options`, and prediction routes are registered by
  `app.main`. On first probe neither port 8001 nor 5173 had a listener, which
  caused the exact frontend "Unable to connect to the CropSense AI prediction
  service" error. Once started, location options returned HTTP 200 and both
  direct and weather-assisted predictions returned HTTP 200. The initial
  weather-assisted HTTP 502 was independently traced to Open-Meteo returning
  `Karn\u0101l` / `Karn\u0101l District` for `KARNAL`; exact ASCII label
  comparison rejected the valid Haryana result. Geocoding now normalizes
  diacritics and matches the state and district administrative fields exactly;
  regression tests cover accented names and wrong-state candidates.
- `dev:full` uses `concurrently --kill-others`, so when the backend command
  exits it intentionally terminates Vite as well. A controlled file-change
  reload kept both services available; the attached test process was later
  terminated by its shell lifecycle, which then caused the expected sibling
  shutdown. Uvicorn reload itself was not reproduced as an unexpected exit;
  the script was left unchanged rather than masking an unconfirmed reload
  defect.

## 6. ML Model Status

| Module | Model | Trained | Files Ready | Backend Service | Frontend Connected | End-to-End Tested |
|--------|-------|:-------:|:-----------:|:---------------:|:-----------------:|:-----------------:|
| Crop Recommendation | XGBoost, 45 classes | ✅ | ✅ Present | ✅ Loads in backend `.venv` | ⏸️ Trustworthy recommendation gated | Historical farmer workflow HTTP-tested with real artifacts; no complete recommendation |
| Fertilizer Recommendation | XGBoost | ✅ | ✅ Present | ✅ Working | ✅ Form/API connected | ✅ Browser E2E |
| Disease Detection | EfficientNet-B0, 38 classes | ✅ | ✅ Present | ✅ Loads in backend `.venv` | ✅ Connected | ✅ Synthetic-image API and browser E2E |
| Yield Prediction | LightGBM, `yield_per_area` | ✅ | ✅ Present | ✅ Loads in backend `.venv` | ✅ Connected; browser E2E pending | ✅ API reference/validation tested |
| Smart Irrigation | LightGBM classification bundle | ✅ Trained bundle present | ✅ One `.joblib` bundle present | ✅ Unified FastAPI loads it | ✅ Direct and weather-assisted page modes connected | Port 8001 health/direct/weather prediction and model status verified |
| AI Assistant | NLP/RAG | NOT STARTED | No | NOT STARTED | No | No |

## 7. Model Files

### Crop Recommendation
| File | Location | Status |
|------|----------|--------|
| `crop_xgboost_model.joblib` | `Cropsense_ai_backend/app/ml/crop/model_artifacts/` | ✅ Present |
| `crop_preprocessor.joblib` | `Cropsense_ai_backend/app/ml/crop/model_artifacts/` | ✅ Present (12 raw features) |
| `crop_label_encoder.joblib` | `Cropsense_ai_backend/app/ml/crop/model_artifacts/` | ✅ Present (45 labels) |

### Fertilizer Recommendation
| File | Location | Status |
|------|----------|--------|
| `fertilizer_xgboost.json` | `Cropsense_ai_backend/app/ml/fertilizer/` | ✅ Present (2502.3 KB) |
| `fertilizer_model_metadata.json` | `Cropsense_ai_backend/app/ml/fertilizer/` | ✅ Present (0.9 KB) |
| `fertilizer_feature_config.json` | `Cropsense_ai_backend/app/ml/fertilizer/preprocessing/` | ✅ Present (1.4 KB) |
| `fertilizer_label_encoder.joblib` | `Cropsense_ai_backend/app/ml/fertilizer/preprocessing/` | ✅ Present (0.6 KB) |
| `fertilizer_preprocessor.joblib` | `Cropsense_ai_backend/app/ml/fertilizer/preprocessing/` | ✅ Present (3.5 KB) |

### Disease Detection
| File | Location | Status |
|------|----------|--------|
| `plant_disease_efficientnet_b0.pth` | `Cropsense_ai_backend/app/ml/disease/` | ✅ Existing raw EfficientNet-B0 state dict; loaded read-only |
| `disease_labels.json` | `Cropsense_ai_backend/app/ml/disease/` | ✅ 38 unique labels; list indices map to classifier output indices |

Inference runtime was verified in backend `.venv` with Python 3.11.8,
PyTorch 2.6.0+cpu, and torchvision 0.21.0+cpu. Preprocessing is RGB
conversion, `Resize((224, 224))`, `ToTensor()`,
and normalization with mean `[0.485, 0.456, 0.406]` and std
`[0.229, 0.224, 0.225]`, matching the training preprocessing supplied by the
model owner. The classifier returns the crop and disease parsed from the
indexed `crop___disease` label plus confidence in `[0, 1]`; the disease page
shows only Predicted Disease and Prediction Confidence (%). No model retraining
or artifact changes were made.

### Yield Prediction
| File | Location | Status |
|------|----------|--------|
| `cropsense_yield_tuned_deployment.joblib` | `Cropsense_ai_backend/app/ml/yield/` | ✅ Existing LightGBM bundle; do not retrain or overwrite |
| `model_metadata.json` | `Cropsense_ai_backend/app/ml/yield/` | ✅ Present; feature/target/training metadata |
| `crop_final.csv` | `Cropsense_ai_backend/app/ml/yield/` | ✅ Final training data, 235,123 rows; target formula and category/pair coverage audited below |

The saved bundle and metadata agree on exact feature order `Crop`,
`State_Name`, `District_Name`, `Season` and target `yield_per_area`. The bundle
embeds the category schema (104 crops, 33 states, 646 districts, 6 seasons),
which is the source for per-field API options and category validation; the
audited CSV supplies state/district pairings. Inputs are matched by trimmed,
case-insensitive exact label and converted back to the saved spelling and
category order for inference. The saved nonnegative prediction clipping is
preserved. Training metadata: 235,123 records, 1997–2015. The verified Rice /
Andhra Pradesh / KRISHNA / Kharif example returns approximately `3.0835`.

### Smart Irrigation
| File | Location | Status |
|------|----------|--------|
| `krishitrust_lightgbm_11_features.joblib` | `Cropsense_ai_backend/app/ml/irrigation/` | ✅ Present; read-only package/interface audit passed; backend integration not started |

Read-only verification (2026-11-18) loaded the 4,385,364-byte joblib bundle
under the backend `.venv` with Python 3.11.8 and LightGBM 4.6.0. SHA-256:
`11ABC464BF3AE6CF2A8D97C4E456E485B2C722FE055F1ABD005459A85661C37F`. The
bundle is a dictionary containing `model`, `features`, `target`,
`label_encoder`, `model_name`, `number_of_features`, `class_weight`,
`n_estimators`, `learning_rate`, and `num_leaves`. The `model` is a
scikit-learn Pipeline containing a `ColumnTransformer` preprocessor and
`LGBMClassifier`.

The exact 11 raw feature names, in saved order, are:
`Temperature_C`, `Humidity`, `Rainfall_mm`, `Sunlight_Hours`, `Soil_Type`,
`Crop_Type`, `Crop_Growth_Stage`, `Season`, `Soil_Moisture`,
`Wind_Speed_kmh`, `Mulching_Used`. The target is `Irrigation_Need`.
Preprocessing uses median/mode imputation and scaling for six numeric fields,
plus `OneHotEncoder(handle_unknown="ignore")` for five categorical fields.
The bundle declares `number_of_features=11`, `class_weight="balanced"`,
`n_estimators=500`, `learning_rate=0.05`, and `num_leaves=31`.

Verified categorical domains are Soil: `Clay`, `Loamy`, `Sandy`, `Silt`;
Crop: `Cotton`, `Maize`, `Potato`, `Rice`, `Sugarcane`, `Wheat`; growth
stage: `Flowering`, `Harvest`, `Sowing`, `Vegetative`; Season: `Kharif`,
`Rabi`, `Zaid`; mulching: `No`, `Yes`. The label encoder exposes
`High`, `Low`, `Medium`; the classifier exposes integer classes `0`, `1`,
`2`, and the pipeline expects a pandas DataFrame with the exact feature
names. `pipeline.predict(DataFrame)` returns an encoded integer class,
`label_encoder.inverse_transform(...)` returns the textual level, and
`pipeline.predict_proba(DataFrame)` returns a three-column probability array.
A representative sample returned encoded class `2`, label `Medium`, and
probabilities approximately `[0.00000165, 0.00000395, 0.99999440]`.
No model retraining, overwrite, application integration, or accuracy validation
was performed.

### Yield target and location-pair audit (2026-10-25)

- The exact final training file is present at
  `Cropsense_ai_backend/app/ml/yield/crop_final.csv` (235,123 rows; columns:
  `State_Name`, `District_Name`, `Season`, `Crop`, `Crop_Year`, `Area`,
  `Production`, `yield_per_area`). `yield_per_area` is stored as a
  non-null `float64`; it is not a log value. `Area`, `Production`, and target
  values are non-null for every row; all areas are positive and productions
  nonnegative.
- The notebook's earlier cells 6–7 and 38 explicitly calculate
  `Production / Area`; cell 38 names the result
  `yield_tonnes_per_hectare`. Final tuned training cells 118–121 and export
  cell 131 read `crop_final.csv` and use its precomputed `yield_per_area`.
  Cell 118 assigns the raw target directly to `y_train` and fits the
  regressor on those target values (not on the older `log_yield_target`).
  A read-only audit of all 235,123 final CSV rows found
  `yield_per_area == Production / Area` within floating-point precision
  (235,123/235,123 match within 1e-9; maximum absolute difference
  5.69e-14). Thus the exact target formula is verified as **Production
  divided by Area** in the final training data, not only inferred from the
  intermediate dataset.
- Physical-unit evidence is narrower: the notebook's intermediate target
  name explicitly declares tonnes per hectare, and its formula is the same.
  However, the final CSV headers are simply `Production`, `Area`, and
  `yield_per_area`; neither the CSV nor final LightGBM metadata records the
  units of the numerator/denominator. The Kaggle page identifies data.world
  as the source but provides no field-unit definition
  ([Kaggle dataset](https://www.kaggle.com/datasets/abhinand05/crop-production-in-india));
  its cited community page redirects to the retirement notice
  ([data.world notice](https://data.world/community/goodbye/)). Therefore
  tonnes/hectare is the notebook's declared intended unit, but source-unit
  documentation is still needed to independently verify that physical unit
  for the final CSV. Keep API/UI labels unit-neutral until confirmed.
- The final CSV has 33 states, 646 district labels, and **652 distinct
  state/district pairs**. The yield service loads these pairs at startup and
  canonicalizes them against model categories. `GET /api/yield/options`
  includes a `districts_by_state` mapping in addition to the original
  categories. The frontend filters districts by the chosen state and clears
  a previous district whenever the state changes.
- Pair checks: Andhra Pradesh + KRISHNA is observed and produces the verified
  reference prediction (~3.0835); Assam + KRISHNA is unobserved and now
  returns HTTP 422. Options expose 33 states and 652 state-specific district
  entries.
- Notebook cell 134's saved output checks the known Andhra Pradesh/KRISHNA
  pair; its `"Krishna"` exact-case membership check is false because the
  canonical saved spelling is `KRISHNA`. The complete 652-pair audit above
  uses the final CSV and canonical labels.
- The attached `file_requirements.txt` is a dependency list, not source-unit
  documentation. Remaining uncertainty: authoritative source units for the
  `Area` and `Production` columns. No model or artifact was changed.

## 8. API Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/health` | Health check | ✅ Implemented |
| `GET` | `/api/model-status` | ML model loading status | ✅ Implemented |
| `POST` | `/api/crop/recommend` | Crop recommendation (12 required features) | Backend prediction HTTP-verified; categorical and state-district validation returns 422; frontend inference gated |
| `POST` | `/api/crop/npk-lookup` | Exact state/district/season NPK lookup; optional crop_year 1997–2015 adds same-year features and NPK ranges | ✅ Implemented; NPK mean/range disclosed; legacy no-year response preserved |
| `POST` | `/api/crop/rainfall-lookup` | Dataset-derived historical rainfall lookup | ✅ Implemented; provenance/semantics unverified |
| `POST` | `/api/fertilizer/recommend` | Fertilizer recommendation (10 features) | ✅ Implemented |
| `GET` | `/api/yield/options` | Saved categorical options and training-observed districts by state | ✅ Implemented |
| `POST` | `/api/yield/predict` | `yield_per_area` from the exact four categorical features; rejects unobserved state/district pairs with HTTP 422 | ✅ Implemented and real-artifact tested |

## 9. Frontend ↔ Backend Data Flow

### Crop Recommendation (automatic historical lookups; recommendation gated)
```
User selects state, district, season and classifies soil
    ↓
Frontend sends context only; backend selects target year
    ↓
Backend requests historical seasonal temperature/humidity and exact-key
rainfall aggregated only from years before target year; candidate experiment
looks up prior candidate area/year and candidate-context NPK.
    ↓
Coverage and lookup statuses are returned; no prediction is returned unless
all candidate inputs are trustworthy and scoring/ranking are validated.
```

### Fertilizer Recommendation (INTEGRATED)
```
POST /api/fertilizer/recommend with 10 features
    ↓
FastAPI: validates with Pydantic FertilizerRecommendationRequest
    ↓
FertilizerService: preprocessor.transform() → XGBoost DMatrix → predict → label_encoder.inverse_transform()
    ↓
Response: { success: true, recommended_fertilizer: "Urea" }
```
The form submits all eight numerical inputs plus Soil and Crop through the
existing `fertilizerApi.ts` client, displays loading and API errors, and shows
the decoded `recommended_fertilizer` result. It is available from the sidebar
and supports English and Hindi labels.

### Yield Prediction
```
GET /api/yield/options → category lists from the saved artifact
POST /api/yield/predict with Crop, State_Name, District_Name, Season
    ↓
FastAPI validates the saved category domains and feature order
    ↓
YieldPredictionService builds a categorical DataFrame using the embedded schema
    ↓
Response: { success, predicted_yield_per_area, target, canonical features }
```

## 10. Mock vs Real Components

### REAL (Backend Integrated)
- ✅ Crop Recommendation — 12-feature/45-class artifacts and FastAPI endpoint are present; frontend inference remains gated
- ✅ Fertilizer Recommendation — Form and sidebar route use the backend endpoint
- ✅ Disease Detection — saved EfficientNet-B0 model and label list are loaded at startup; frontend uses multipart API inference and displays disease/confidence only
- ✅ Yield Prediction — Saved LightGBM bundle loaded by FastAPI; frontend uses
  model-backed categorical options and displays the direct `yield_per_area`
  prediction.

### STILL MOCK (Phase-0 Prototypes)
- 🔶 Weather — uses `mockCurrentWeather`, `mockForecast` from `mockData.ts`
- 🔶 AI Assistant — uses `mockChatMessages`, `mockAiResponses` from `mockData.ts`
- 🔶 Dashboard — uses various mock data for summary widgets

## 11. Dataset Status

The local training CSV is
`Cropsense_ai_backend/data/Copy of crop_recommendation_45_with_year_area.csv`
(218,189 rows; years 1997–2015; 14 columns including 12 input features,
`crop_names`, and `npk_source`). The notebook uses a Drive CSV with the same
filename, row count, and columns. Exact content identity with that Drive copy
is not established.

The deployed preprocessor and model agree on 12 raw inputs and 673 transformed
features; the label encoder has 45 classes matching the local dataset's unique
crop labels. Embedded model parameters match the notebook's 800-tree candidate.
However, the notebook's artifact-export cell has a saved `NameError`, and no
trusted hash/manifest links the deployed artifacts to that exact training run.
Artifact lineage and dataset provenance therefore remain unverified.

The fitted preprocessor's district categories differ from the current local
CSV by one category (`NAMSAI` appears once in the CSV but not in the fitted
preprocessor). This discrepancy must be resolved before any claim of exact
dataset/preprocessor identity.

### Latest artifact compatibility verification

- `scripts/check_models.py` passed using the backend `.venv`; the crop model,
  preprocessor, label encoder, and checked fertilizer artifacts loaded.
- The crop preprocessor exposes 12 raw features in the documented order and
  produces 673 transformed features; the XGBoost model and booster both expect
  673 features. The model class IDs are `0–44`; all 45 label-encoder classes
  exactly match the local CSV's crop labels.
- The four fitted categorical feature sets match the local CSV except for the
  district category `NAMSAI`, which is in the CSV but absent from the
  preprocessor. The cause is unknown.
- Loading emitted an XGBoost serialized-model compatibility warning and
  scikit-learn warnings that the pickled estimators were created with 1.6.0
  while the backend environment uses 1.6.1. Loading passed, but these warnings
  are not proof of artifact portability or exact provenance.
- Exact artifact-to-training-run and local-CSV-to-Drive-copy lineage remain
  unverified: the notebook's artifact-export cell has a saved `NameError`, and
  no trusted hashes or manifest tie the deployed files to a specific run.
- **Single next action:** request the original training-run export and its
  artifact/data hashes or manifest from the source owner. If unavailable, treat
  lineage as unrecoverable and seek separate approval for a reproducible,
  versioned training/export run; do not replace the current artifacts.

The NPK lookup with `crop_year` filters the existing CSV to exact state,
district, season, and year. It returns arithmetic NPK means plus min/max ranges
and matched-row count, explicitly disclosing aggregation. It returns
temperature, humidity, and rainfall only when those fields are constant in
the selected group; conflicting values fail rather than select an arbitrary
row. The no-year NPK lookup remains for compatibility.

### Area feature evidence

- Kaggle identifies the source as [Crop Production in India by Abhinand05](https://www.kaggle.com/datasets/abhinand05/crop-production-in-india)
  and credits its content to [data.world / thatzprem/agriculture-india](https://data.world/thatzprem/agriculture-india).
- Kaggle's public file listing names `crop_production.csv`. The source columns
  used for the prior comparison are `State_Name`, `District_Name`, `Crop_Year`,
  `Season`, `Crop`, `Area`, and `Production`. The current training CSV has 14
  columns: `state_names`, `district_names`, `season_names`, `soil_for_crop`,
  `crop_names`, `N`, `P`, `K`, `temperature`, `humidity`, `rainfall_mm`,
  `npk_source`, `crop_year`, and `area`.
- The local CSV contains 218,189 rows. Its numeric `area` column has no missing
  values, 36,291 distinct values, and ranges from 0.04 to 1,020,181. A
  read-only comparison with Kaggle's `crop_production.csv` (246,091 rows)
  matched every local row to source `Area` by normalized
  state/district/season/year/crop keys. All retained values were equal; no
  numeric conversion or transformation was observed.
- Because each source `Area` value is attached to a specific crop, district,
  season, and year record, it represents historical cultivated area for that
  crop in that record—not total available farm area. In 28,001
  location/season/year groups containing multiple crops, crop rows have
  different area values; for example, NICOBARS/Kharif/2000 has Arecanut area
  1,254 and Rice area 102. This verifies the crop-specific association in this
  file.
- Project-provided unit confirmation is hectares (ha). Kaggle's accessible
  metadata does not itself include a field-level unit definition, so the
  numeric unit is not independently verified by the publisher's available
  documentation.
- Kaggle's dataset description and file listing do not specify an area unit or
  provide a field-level data dictionary. The cited data.world community has
  retired, and its page redirects to the retirement notice. Thus the original
  hectare unit is project-confirmed but not independently established by
  currently accessible Kaggle/data.world field documentation. Do not infer or
  convert a different unit from numeric values.
- The notebook lists `area` among eight numeric features and configures those
  features as `"passthrough"` in the `ColumnTransformer`; it does not document
  the feature's semantic definition or unit. The backend preserves the value
  as a numeric request field, places it in the 12-column DataFrame in the
  trained feature order, and passes it to the fitted preprocessor. No backend
  conversion or historical-area substitution occurs. The frontend's intended
  value is farmer-entered total available land (ha); its submit gate remains
  closed.
- **Prediction-time value:** the dataset supplies historical cultivated area
  only for an already specified crop, state, district, season, and year. In
  28,001 location/season/year groups it has different area values for multiple
  crops (for example, NICOBARS/Kharif/2000 has Arecanut area 1,254 and Rice
  area 102). Since the requested crop is not known before recommendation, the
  existing data does not provide one defensible, crop-independent area value
  for that request. No compatible value can be derived before the crop is
  known without inventing a proxy or selecting an arbitrary aggregate.
- **Conclusion:** total available farm area is not interchangeable with
  historical area cultivated for one particular crop. The shared hectare unit
  is insufficient evidence of compatibility. No available source or
  documentation validates feeding the farmer value to this existing model.
- **Smallest safe alternative and next action:** keep the existing 12-feature
  model and artifacts unchanged and leave frontend inference disabled. Do not
  substitute historical area, crop averages, or farmer-entered land without
  validation. Ask the dataset/model owner for the intended prediction-time
  definition and compatibility evidence. If total available land remains the
  intended input and compatibility cannot be established, the existing model
  cannot safely serve that workflow under the current no-retraining constraint.

## 12. Environment

| Component | Version |
|-----------|---------|
| Backend `.venv` Python | 3.11.8 |
| Backend `.venv` LightGBM | 4.6.0 (yield artifact) |
| Backend `.venv` XGBoost | 3.2.0 |
| Backend `.venv` scikit-learn | 1.6.1 |
| Workspace Python (not suitable for crop artifact loading) | 3.13.x / XGBoost 3.4.1 |
| `requirements.txt` declared runtime | Python 3.13.x / XGBoost 3.4.1 (differs from the verified backend `.venv`) |
| FastAPI | ≥ 0.115.0 |
| Node.js | (as installed) |
| Vite | 8.2.x |
| React | 19.2.x |
| TypeScript | 6.0.x |
| Tailwind CSS | 4.3.x |

## 13. Completed Tasks

- [x] Inspect existing frontend structure and all pages
- [x] Create FastAPI backend directory structure
- [x] Create Pydantic schemas (crop + fertilizer)
- [x] Create ML service layer (crop_service + fertilizer_service)
- [x] Create API routes (crop + fertilizer)
- [x] Create FastAPI main.py with CORS and lifespan
- [x] Create requirements.txt with pinned ML versions
- [x] Create backend .gitignore and .env.example
- [x] Create model placeholder instruction files
- [x] Create model verification script (check_models.py)
- [x] Create backend README.md
- [x] Create frontend API abstraction layer (client.ts, cropApi.ts, fertilizerApi.ts)
- [x] Create frontend .env.example
- [x] Add crop recommendation API wrapper and request/result/error handling
      (frontend submission is currently gated; no live crop predictions)
- [x] Add error handling UI for backend connection failures
- [x] Add loading state and duplicate submission prevention
- [x] Create PROJECT_PROGRESS.md
- [x] Create DEVELOPMENT_CHECKLIST.md
- [x] Validate crop API categorical inputs against fitted model categories and reject invalid state-district pairs (HTTP 422)
- [x] Add crop API validation tests for exact/case-normalized labels, unsupported categories, and invalid state-district pairs
- [x] Verify a real backend crop prediction and HTTP 422 responses for invalid soil and invalid state-district inputs (backend only; frontend remains gated)
- [x] Add optional year-specific NPK lookup (1997–2015) returning same-group NPK summaries/ranges, temperature, humidity, and rainfall
- [x] Add focused NPK service/API tests for year validation, missing groups, NPK variation, and same-group feature consistency
- [x] Audit notebook, training CSV, and deployed artifact configuration; document unresolved lineage and category discrepancy
- [x] Inspect the training CSV, notebook, backend schema, and crop form for `area`; establish crop-specific historical area semantics and document the project-confirmed hectare unit and remaining source-metadata caveat
- [x] Compare local `area` values with Kaggle's original `crop_production.csv`; all 218,189 retained rows exactly match source `Area` values by normalized record keys
- [x] Inspect Kaggle metadata and its upstream data.world attribution; accessible metadata does not document the `Area` unit
- [x] Review remaining crop-page/API integration independently of `area`; existing lookup calls and crop recommendation client are present, while submission remains gated
- [x] Add reference-only prior-year crop feature lookup: area uses the latest matching crop/location/season record; NPK values are withheld until `npk_source` provenance is validated
- [x] Connect candidate-wise historical coverage to `POST /api/crop/recommend-historical`; server selects the target year, applies fitted-category/location validation, and returns candidate coverage plus next steps without a prediction
- [x] Remove farmer-entered area from the crop form and send only location, season, soil, and optional existing weather/rainfall lookup values; N, P, K, area, and crop year are not submitted by the frontend
- [x] Add focused backend route/service and frontend request-shape tests; preserve the existing `/api/crop/recommend` endpoint and keep candidate scores out of workflow responses
- [x] Add an isolated candidate-wise scoring experiment using the existing 45-class artifacts; strictly prior area/year pairing, candidate coverage, missing history, NPK trust gating, and model-input validation failures are recorded; no production route or inference gate changed
- [x] Integrate the saved LightGBM yield artifact read-only; verify embedded categories, metadata, exact feature order, and case-insensitive canonical label matching
- [x] Add yield options/prediction endpoints and connect the existing React yield page to its exact four categorical inputs
- [x] Add `lightgbm==4.6.0` to backend requirements to match the saved artifact
- [x] Verify the saved Rice/Andhra Pradesh/KRISHNA/Kharif prediction and reject unsupported categories and extra request fields
- [x] Create a smallest isolated Flask backend for smart irrigation (`irrigation_api.py`)
- [x] Test Flask irrigation health and prediction endpoints
- [x] Integrate Open-Meteo daily weather for the irrigation model

## 14. Pending Tasks

- [x] User manually copies trained model files into `app/ml/` directories
- [x] Run `check_models.py` to verify model file placement
- [ ] End-to-end test: Crop Recommendation form → API → model → response → UI (intentionally blocked until feature compatibility and training lineage are verified)
- [x] Establish that source `Area` is crop/district/season/year-specific historical cultivated area; hectare unit is project-confirmed, while accessible Kaggle metadata lacks a field-level unit definition
- [ ] Decide which `npk_source` categories are acceptable
- [ ] Optional reference-only enhancement: expose year-specific NPK details/ranges in the page; do not connect them to inference without compatibility validation
- [ ] Finish compatible feature preparation using training-data definitions; represent NPK aggregation explicitly and do not present it as an observed row
- [ ] Add/update tests for year-specific feature consistency across API and frontend contracts
- [ ] Obtain the model/data owner's prediction-time definition and validation evidence for `area`; keep inference gated unless it establishes compatibility with farmer-entered total land
- [ ] Enable frontend crop inference only after feature definitions, units, and provenance decisions are complete
- [x] End-to-end test: Fertilizer Recommendation form → API → decoded model result (2026-10-26; browser sample returned HTTP 200 and displayed `Urea`)
- [x] Create Fertilizer Recommendation page with all 10 fields, loading/error/result states, and sidebar route
- [x] Connect frontend page to the existing `POST /api/fertilizer/recommend` API client
- [x] Integrate the saved EfficientNet-B0 disease model and connect the existing disease page to the backend API
- [ ] Validate disease prediction quality and label order against representative held-out real plant images from the training dataset
- [x] Build yield prediction backend service using the saved model
- [x] Browser end-to-end test: Yield Prediction form → category options → API → displayed result (2026-10-25; existing local backend and Vite servers; real browser POST returned 200 and displayed `3.0835`)
- [ ] Obtain authoritative source documentation for `Area` and `Production` units before labeling predictions in physical units; notebook target name declares tonnes/hectare but source-unit documentation is missing
- [x] Enforce final-CSV state/district pairs in yield prediction and filter the frontend district dropdown by selected state
- [x] Build the smallest isolated smart irrigation Flask backend service
- [x] Fix irrigation numeric validation for booleans and NaN/±infinity
- [x] Connect the frontend irrigation page to the Flask direct prediction endpoint
- [x] Add an explicit weather-assisted mode to the irrigation UI while retaining the direct prediction mode; preserve caller `Soil_Moisture`, collect latitude/longitude/optional date, show fetched weather inputs and their units, and disclose the unresolved rainfall/sunlight measurement-period compatibility limitation
- [x] Integrate irrigation service, Pydantic schemas, prediction/weather router, and model status into FastAPI port 8001
- [x] Switch frontend irrigation traffic to the shared FastAPI API base
- [x] Retire port 8002 after unified `dev:full` verification
- [ ] Integrate live weather API
- [ ] Build NLP/RAG AI assistant backend
- [ ] Replace Dashboard mock data with real API summaries
- [ ] Comprehensive testing across all modules
- [ ] Production deployment configuration
- [ ] Choose a deployment platform, configure `CORS_ORIGINS` and frontend `VITE_API_BASE_URL`, and confirm the model, metadata, and `crop_final.csv` are included in the deployed image/package

## 15. Known Issues

| Issue | Severity | Status |
|-------|----------|--------|
| Yield service has no platform-specific deployment manifest or production origin configuration | Medium | CORS is configurable through `CORS_ORIGINS`; deployment still needs a selected platform, production `VITE_API_BASE_URL`, and model/metadata/CSV packaging |
| Irrigation soil-moisture feature has no verified API mapping | Medium | `Soil_Moisture` is still required as caller-supplied input; Open-Meteo soil-moisture or another sensor/service value is not substituted because the model's training meaning/unit is unverified |
| Irrigation rainfall/sunlight compatibility period | Medium | The UI discloses that Open-Meteo rainfall is a one-calendar-day `precipitation_sum` and sunlight is `sunshine_duration` converted from seconds to hours. These periods remain unverified against the model's training feature periods |
| Irrigation direct-mode weather-field regression | Resolved | Direct request assembly now checks only the 11 direct mode fields, so blank weather latitude/longitude/date values no longer block direct prediction |
| Irrigation responsive error/text layout | Resolved for narrow confirmed issue | Mobile irrigation error/result containers use full-width, `min-w-0`, and `break-words`; weather values are formatted to two decimals; mode buttons use no-wrap labels with responsive padding |
| Irrigation frontend contract mismatch | Resolved | `/irrigation` provides direct and weather-assisted modes. Direct prediction uses the exact 11 direct-prediction fields; weather-assisted prediction preserves caller soil moisture and shows sourced weather values |
| Irrigation legacy Flask port 8002 | Resolved | Final `npm run dev:full` verification passed with only FastAPI port 8001; the Flask entrypoint and Flask dependency were removed |
| Irrigation endpoint numeric validation | Resolved | JSON booleans are rejected for all six `/predict` numeric fields and `/predict-from-weather` numeric fields. NaN, ±infinity, and string forms such as `NaN`/`Infinity` return HTTP 400. No physical range limits were added because no documented model range requirements exist |
| Irrigation prediction probability mapping is index-based | Medium | The response maps `predict_proba` columns by `enumerate(label_encoder.classes_)`. Verified current artifact classes `['High', 'Low', 'Medium']` align with classifier classes `[0, 1, 2]`; preserve this alignment check in focused tests rather than assuming arbitrary label/class order |
| Dashboard still uses `mockCropRecommendation` for the crop summary widget | Low | By design (mock remains for unintegrated Dashboard) |
| Crop artifacts fail to load under workspace Python 3.13 / XGBoost 3.4.1 | High | Backend `.venv` Python 3.11.8 / XGBoost 3.2.0 loads them; preserve this runtime |
| Yield physical unit remains unverified | Medium | The final CSV proves `yield_per_area = Production / Area`; notebook cell 38 declares intended tonnes/hectare, but final source fields have no unit metadata and Kaggle/data.world pages provide none. Keep displayed target unit-neutral pending authoritative source documentation |
| Crop artifact training lineage is not proven | High | Notebook export cell fails with `NameError`; no trusted artifact/dataset manifest |
| Fitted crop preprocessor excludes `NAMSAI`, present once in the local CSV | Medium | Difference documented; cause unknown |
| Historical crop workflow cannot yet produce a trustworthy recommendation | High | 21/45 candidates lack prior area history in the real-data run; climate-feature compatibility and candidate-wise score-ranking validity remain unresolved |
| Legacy standalone crop helper is separate from the deployed 12-feature artifacts | Informational | It requires an explicit compatible model path and is not used by the crop API |

## 16. Testing Status

| Test | Status | Notes |
|------|--------|-------|
| 2026-11-18 | Audited only the irrigation frontend page, mock data, shared API client, and frontend API environment example. No code was modified. Found that `Irrigation.tsx` imports `mockIrrigationResult`, submits through `setTimeout`, and never calls HTTP; its result uses `shouldIrrigate/reason/nextTime`, while the Flask API returns `success/prediction/probabilities` and does not return a rule-based boolean. Documented direct contract: 11 exact JSON fields and response shape. Documented weather-assisted contract and 400/502 behavior. Identified current UI field mismatches: legacy rain probability/rainfall fields and missing soil moisture/wind/season; crop/soil/growth selections include values outside saved model domains. Shared `VITE_API_BASE_URL` defaults to port 8001, but Flask uses port 8002. Next: add a dedicated irrigation API client/configuration and replace mock form/result handling without changing the model or weather logic | AI Assistant |-------|
| 2026-11-18 | Fixed irrigation endpoint numeric validation without changing the model, preprocessing, feature order, or weather logic. Updated `Cropsense_ai_backend/irrigation_api.py` so booleans are rejected before numeric conversion and NaN/±infinity/non-finite string forms return HTTP 400 for `/api/irrigation/predict` and `/api/irrigation/predict-from-weather`. Added `Cropsense_ai_backend/scripts/test_irrigation_prediction_validation.py` with 6 focused tests covering valid prediction, boolean rejection for every `/predict` numeric field, NaN, ±infinity, string special floats, and `/predict-from-weather` numeric fields. All 6 endpoint validation tests and all 4 irrigation weather tests passed. No physical numeric ranges were invented or added because no documented model limits support them. Model artifact SHA-256 remains unchanged at `11ABC464BF3AE6CF2A8D97C4E456E485B2C722FE055F1ABD005459A85661C37F` | AI Assistant |-------|
| 2026-11-18 | Completed a read-only audit of the isolated Flask irrigation prediction endpoint and its saved LightGBM integration. Bundle and endpoint agree on the exact 11-feature list and order: `Temperature_C`, `Humidity`, `Rainfall_mm`, `Sunlight_Hours`, `Soil_Type`, `Crop_Type`, `Crop_Growth_Stage`, `Season`, `Soil_Moisture`, `Wind_Speed_kmh`, `Mulching_Used`. Pipeline audit confirmed six numeric/scaled fields, five exact-domain categorical/one-hot fields, `Irrigation_Need` target, 25 transformed features, label classes `High/Low/Medium`, classifier classes `0/1/2`, and aligned probability output. A valid reference POST returned HTTP 200 and `Medium` with probabilities summing to approximately 1. Missing fields, extras, and invalid categories returned 400. Direct edge testing found JSON boolean accepted as numeric `1.0` and infinity/error-producing HTTP 500 instead of HTTP 400; these remain endpoint validation issues. Focused irrigation weather tests 4/4 and historical weather tests 26/26 passed. Model SHA-256 remains `11ABC464BF3AE6CF2A8D97C4E456E485B2C722FE055F1ABD005459A85661C37F`. No model retraining or artifact modification was performed. Next: fix finite/numeric validation and add focused endpoint tests before frontend integration | AI Assistant |-------|
| Backend health endpoint | ✅ Passed | Returns `{"status": "healthy"}` |
| Model status endpoint | ✅ Passed | Reports crop, fertilizer, soil, and yield model states |
| Crop model loading | ✅ Passed in backend `.venv` | Python 3.11.8 / XGBoost 3.2.0 |
| Historical crop workflow | ⏸️ Recommendation gated | Farmer-facing HTTP flow returned 200 and generated experimental scores for 24 candidates with complete rows; scores are not validated for ranking; legacy `/recommend` remains compatible |
| Swagger docs (`/docs`) | ✅ Passed | Returns 200, interactive UI accessible |
| check_models.py | ✅ Passed | Deployed crop artifact dimensions/classes and fertilizer artifacts load; checker does not run crop inference |
| Fertilizer model loading | ✅ Passed | Startup verifies 10 ordered inputs across config/metadata/preprocessor, 44 transformed features across config/metadata/preprocessor/Booster, and ordered label classes across config/metadata/encoder; incompatibility marks the service unavailable |
| Fertilizer inference test | ✅ API tests passed | `scripts/test_fertilizer_api.py`: valid 10-feature sample returns HTTP 200 with `recommended_fertilizer` matching a decoded encoder class; missing field and invalid numeric value return HTTP 422 |
| Fertilizer dataset/artifact audit | ✅ Passed | Read-only audit: `fertilizer_train.csv` (2,238 rows) and `fertilizer_test.csv` (560 rows) match the configured `Fertilizer` target, exact ordered 10-feature input list, and all 10 classes; `Remark` is explicitly excluded. Recomputed held-out metrics match metadata exactly: 556/560 correct, accuracy 0.9928571428571429, macro precision 0.9869343863683486, macro recall 0.9918570980652539, macro F1 0.9891464000934281, weighted F1 0.9928670354130126. CV F1 was not independently recomputed. sklearn warned that artifacts saved with 1.6.0 were loaded with 1.6.1 |
| Disease model loading and inference | ✅ Passed | `scripts/test_disease_api.py` loaded the actual EfficientNet-B0 checkpoint at startup, verified 38 unique labels against the 38-output classifier, checked 224×224 transformed input and exact output-index-to-label/crop/disease mapping, and received HTTP 200 with confidence in range. Invalid image returned HTTP 422. Synthetic image prediction is only an integration smoke test, not an accuracy test |
| Disease frontend/backend connection | ✅ Live integration passed; failure cause identified | Initial `curl http://127.0.0.1:8000/health` returned connection refused because no backend process was listening on port 8000. Frontend fallback is `http://127.0.0.1:8000`; multipart field `image`, `/api/disease/predict`, response keys, and frontend display are consistent. With backend running in the project `.venv`, `/health` returned 200, model status reported disease loaded, CORS preflight from `http://127.0.0.1:5173` and `http://localhost:5173` returned 200, and live multipart POST returned 200. Browser upload of the existing `hero.png` displayed disease and confidence only; the graphic is not a representative plant-leaf sample, so this validates transport/UI integration, not disease prediction quality |
| Fertilizer frontend integration | ✅ Passed | Form submits all 10 fields using `recommendFertilizer`; browser request returned HTTP 200 with `{success: true, recommended_fertilizer: "Urea"}` and displayed `Urea`. Frontend tests 42/42 passed, TypeScript check passed, and production build passed with existing >500 KB chunk warning |
| Yield Prediction API | ✅ Passed | `scripts/test_yield_prediction.py`: 10 tests pass; covers startup/model status, CORS, options, all 652 observed pairs, reference prediction ≈3.0835, and validation/failure behavior |
| Yield startup/runtime diagnosis | ✅ Root cause fixed; live page verified | The original Uvicorn process used `C:\Program Files\Python311\python.exe`, which lacks LightGBM; startup logged `ModuleNotFoundError: No module named 'lightgbm'`, leaving `/api/model-status` false and `/api/yield/options` at 503. Restarted with the backend `.venv` (Python 3.11.8, LightGBM 4.6.0); model status and options now return 200 with all 652 state/district pairs. Browser requests use the correct `http://127.0.0.1:8000` API base; `http://localhost:5173` passes CORS. README startup commands use `.venv`; frontend shows an unavailable placeholder if options fail. Live API prediction and browser form returned the verified Rice / Andhra Pradesh / KRISHNA / Kharif result ≈3.0835 |
| Yield deployment readiness audit | ✅ Focused checks passed; platform deployment remains pending | Request validation rejects unsupported categories/pairs, extras, and malformed input; missing model inputs result in an unavailable service/503; errors are logged without exposing filesystem paths or exception text; OpenAPI documents error envelopes. Backend runtime verified on Python 3.11.8 / FastAPI 0.115.6 / Pydantic 2.10.4 / LightGBM 4.6.0 / pandas 2.2.3. Backend CORS uses explicit `CORS_ORIGINS`; no platform-specific deployment manifests exist |
| Yield target formula and pair audit | ✅ Formula/pairs verified; physical unit partly verified | Final `crop_final.csv` has 235,123 records; target matches `Production / Area` on all rows within 1e-9 (max absolute difference 5.69e-14). Notebook cell 38 names this ratio `yield_tonnes_per_hectare`, which supports intended tonnes/ha, but source units are not independently documented. CSV has 652 distinct state/district pairs; API options and inference now use those observed pairs |
| Yield Prediction browser E2E | ✅ Passed | Earlier browser check submitted Rice / Andhra Pradesh / KRISHNA / Kharif and displayed `3.0835`. Current pair-validation browser check: Andhra Pradesh district list contains KRISHNA; switching to Assam removes KRISHNA and clears the district selection. Live API reports 652 pair entries and rejects Assam/KRISHNA with HTTP 422 |
| Frontend TypeScript check | ✅ Passed | `npx tsc --noEmit` exits 0 |
| Frontend tests | ✅ Passed | 42 tests |
| Frontend build | ✅ Passed | `npm run build`; Vite warns the minified JS chunk exceeds 500 KB |
| Yield frontend typecheck/build | ✅ Passed | `npx tsc --noEmit`, production build, and browser district-filter check pass; Vite retains the existing >500 KB chunk warning |
| NPK lookup service/API | ✅ Passed | 13 focused tests, including year-specific results and validation |
| Crop input validation | ✅ Passed | 5 focused tests and 6 crop-weather contract tests |
| Current crop API validation | ✅ Passed | 6 focused tests; includes HTTP 422 for `NAMSAI`, which is present in the CSV but absent from the fitted district categories |
| Current frontend crop checks | ✅ Passed | TypeScript `--noEmit`, 20 frontend tests, and production build passed; acreage is submitted only as farmer-planning context and results distinguish it from historical area |
| Current crop workflow integration | ✅ HTTP-tested; recommendation gated | Backend retrieves year-specific NPK, prior candidate area/year, historical weather, and pre-target rainfall; response now includes detailed missing-history reasons and separate scoring/recommendation blockers |
| Candidate input assembly tests | ✅ Passed | Exact 12-feature order/types and paired prior area/year tested with the existing preprocessor; available candidates proceed when one lacks history; missing NPK/weather/rainfall blocks that candidate without substitution |
| Latest crop artifact compatibility checks | ✅ Passed with warnings | `check_models.py`; 12 raw → 673 transformed features, 45 classes; XGBoost serialization and scikit-learn 1.6.0→1.6.1 warnings; `NAMSAI` remains absent from fitted district categories |
| Latest crop focused tests | ✅ Passed | `scripts/test_crop_input_validation.py`: 5 tests; `scripts/test_crop_weather_contract.py`: 6 tests |
| Farmer acreage conversion and separation | ✅ Passed | 1- and 5-acre conversions; invalid, zero, negative, nonfinite, boolean, and >100,000-acre values rejected; historical candidate area/year remain separate; legacy request/response contract unchanged |
| Farmer-acre frontend flow | ✅ Passed | Named form extraction, 3/9-acre request payloads and invalid/excessive values tested; English/Hindi labels distinguish planning acres/hectares from historical dataset area; validation is not mislabeled as connection failure |
| Belgaum candidate/weather diagnostics | ✅ Focused | Dataset cutoff coverage is fixed at 24/45 for target years >2015; the same lookup at target year 1999 returns 19/45, so the reported 10/45 was not reproducible with the current dataset/context. Area matching is exact on state/district/season/crop and does not filter soil. Belgaum weather remains gated because reviewed mapping/coordinate evidence is absent |
| Historical-weather location coverage | ✅ Evidence-gated | The UI no longer claims only MYSORE/PUNE are supported. New records require a state-qualified LGD crosswalk, verified district-headquarters coordinate evidence, source record and reviewer metadata via `scripts/resolve_weather_locations.py`; unresolved locations stay disabled. BELGAUM is pending alias/history review: the project LGD snapshot lists Belagavi (district LGD ID 527), but the CSV label `BELGAUM` has no approved crosswalk to it, and no reviewed headquarters coordinate evidence is present |
| Normalized crop-area lookup | ✅ Passed | Karnataka/BELGAUM/Rabi at target year 2026 has 18/45 eligible prior-area matches and 27 candidates with no eligible exact-season record. Label normalization recovers 0 because current dataset/model crop labels already match after normalization. Of the 27, 21 have prior records only in other seasons (not used); 6 have no prior area row anywhere in this state/district |
| Live crop API request checks | ✅ Passed | Valid request 200 with prediction; invalid soil and mismatched state/district 422 |
| Area feature compatibility review | ✅ Completed; serving limitation remains | Notebook passes numeric `area` through unchanged; source values are crop/location/season/year-specific cultivated area and are used only from a prior matching record in the isolated experiment; total farmer-available land is not substituted; production inference remains gated |
| Smart irrigation model bundle | ✅ Package/interface audit passed | Loaded only `krishitrust_lightgbm_11_features.joblib` read-only under backend `.venv` Python 3.11.8 / LightGBM 4.6.0; verified 11 features, categorical domains, target/classes, Pipeline, `predict`, `predict_proba`, and a representative `Medium` result. No accuracy or backend/frontend integration testing was performed |
| Smart irrigation Flask API | ✅ Passed | `irrigation_api.py` loads the saved bundle once at startup. Flask 3.1.3 passed live tests on port 8002: `/health` returned 200, a valid POST returned `prediction="Medium"` with three probabilities, missing fields returned HTTP 400, and invalid numeric input returned HTTP 400. Added `Flask>=3.1.0` to `requirements.txt`; no model/artifact or frontend files changed |
| Smart irrigation weather integration | ✅ Passed | Added Open-Meteo daily weather lookup and combined prediction routes. Mocked unit tests 4/4 passed; live archive lookup for Pune/2024-06-15 returned HTTP 200 and combined prediction returned `Medium`. Temperature, humidity, rainfall, sunshine, and wind units/period mappings were checked; `Soil_Moisture` remains caller-supplied and is not invented or mapped from weather data |
| Smart irrigation model integration audit | ✅ Passed with known validation gaps | Read-only audit verified endpoint/bundle feature lists and order are identical: 11 names in exact saved order; six numeric fields are `float64` after endpoint conversion; five categorical fields use exact saved domains. Preprocessor produced 25 transformed features (6 scaled numeric + 19 one-hot); pipeline returned encoded class `2`, label `Medium`, probability array `[7.28085185265936e-07, 5.679684190615699e-07, 0.9999987039463958]`, probability sum approximately `1`. Valid Flask test-client POST returned 200/Medium, missing and extra fields returned 400, and invalid category returned 400. JSON boolean `true` was incorrectly accepted as numeric `1.0`; infinity produced HTTP 500. No model or source modifications were made |
| Irrigation frontend mock/API contract audit | ✅ Findings documented; no code changed | Inspected only `Cropsense_ai_frontend/src/pages/Irrigation.tsx`, `src/data/mockData.ts`, `src/lib/api/client.ts`, and `.env.example`. The page imports `mockIrrigationResult`, uses a 1-second `setTimeout`, renders `shouldIrrigate/reason/nextTime`, and has no API client or request. Direct Flask contract: `POST /api/irrigation/predict` with exact JSON keys `Temperature_C`, `Humidity`, `Rainfall_mm`, `Sunlight_Hours`, `Soil_Type`, `Crop_Type`, `Crop_Growth_Stage`, `Season`, `Soil_Moisture`, `Wind_Speed_kmh`, `Mulching_Used`; six numeric values and five exact categorical values. Response is `{success, prediction, probabilities}` with `prediction` one of `High/Low/Medium` and probabilities keyed by those labels. Weather-assisted contract: `POST /api/irrigation/predict-from-weather` requires `latitude`, `longitude`, `Soil_Moisture`, `Soil_Type`, `Crop_Type`, `Crop_Growth_Stage`, `Season`, `Mulching_Used`, optional `date`; response is success/prediction/probabilities plus a documented `weather` object. Missing/extra fields and invalid numeric/categorical values return HTTP 400; weather/provider failures return HTTP 502. Shared frontend `VITE_API_BASE_URL` currently defaults to FastAPI port 8001, not Flask port 8002 |
| Irrigation numeric validation regressions | ✅ Passed | Added `scripts/test_irrigation_prediction_validation.py` and verified valid payload prediction, boolean rejection across all six `/predict` numeric fields, NaN rejection, ±infinity rejection, string special-float rejection, and boolean/NaN/infinity rejection in `/predict-from-weather`. 6 focused tests passed. Numeric values are now checked with `math.isfinite` and booleans are rejected before conversion. No documented physical ranges were enforced because none are specified by the model/bundle requirements |
| Smart irrigation frontend direct integration | ✅ Passed | Added dedicated `src/lib/api/irrigationApi.ts` client using `VITE_IRRIGATION_API_BASE_URL` with fallback `http://127.0.0.1:8002`; updated `Irrigation.tsx` to collect 11 exact model fields, call Flask on submit, display API prediction/probabilities, and show connection/validation errors. Added exact-domain/category request assembly and 4 frontend request tests. Frontend tests 54/54, TypeScript check, and production build passed; live Flask CORS preflight and direct POST returned HTTP 200/`Medium` |
| Smart irrigation direct and weather-assisted UI | ✅ Passed | Added separate Direct/Weather-assisted modes without changing direct payload behavior. Weather mode collects latitude, longitude, optional date, exact categorical fields, and caller-entered soil moisture; it calls `POST /api/irrigation/predict-from-weather`, shows sourced provider/date/timezone and unit-labelled values, keeps soil moisture explicitly farmer-entered, and displays rainfall/sunlight compatibility warning. Focused tests 57/57 passed; TypeScript check and production build passed; live weather-assisted POST returned HTTP 200/`Medium` |
| Irrigation weather-assisted UI design audit | ✅ Findings documented; no code changed | Direct and weather-assisted endpoints were compared against the current React page. Smallest safe design retains direct mode unchanged and adds an explicit weather-assisted mode. Weather mode requires latitude/longitude/optional date and caller-supplied `Soil_Moisture`; it must not send manual weather fields or invent soil moisture. UI must show provider/date/timezone, units, and fetched values, plus a clear rainfall/sunshine measurement-period compatibility warning. The backend already exposes this contract and rejects missing/nonfinite/provider data; no model or endpoint changes are needed for UI integration |
| Irrigation end-to-end QA | ✅ Passed focused checks; exact 768/1440 headless capture limited | Frontend 59/59 tests, TypeScript check, production build, and `/irrigation` route HTTP 200 passed. Backend 9/9 tests passed for direct/invalid/weather-assisted paths, caller soil moisture, categories, weather failure, and probability decoding. Live direct valid POST returned 200/`Medium`, live direct boolean returned 400, and live weather-assisted POST returned 200/`Medium`. Malformed API success responses are rejected by the frontend. Remaining: model physical ranges and rainfall/sunlight training-period compatibility |
| Irrigation responsive UI QA | ✅ 375px browser and constrained viewport checks passed | Captured mobile direct, weather-form/result, and offline-error screenshots at 375px. Confirmed both modes and weather summary/warning/error states remain readable without document horizontal overflow. Added full-width/min-width-zero and break-words error/result containers, compact mobile padding, no-wrap mode labels, and two-decimal weather values. The embedded browser constrained 768px/1440px probes to 407px/1008px inner widths; no off-screen elements or horizontal overflow were found. Exact headless 768px/1440px capture could not download Chromium due ECONNRESET/DNS network errors |
| Unified startup/integration test | ✅ Passed | `test_unified_startup.py`: 2/2 passed; verifies `dev:full` is the single startup command, uses FastAPI port 8001 and Vite port 5173, excludes port 8002/`irrigation_api.py`, and verifies `/health`, `/api/model-status`, and direct irrigation through FastAPI |
| Irrigation FastAPI migration steps 1–4 | ✅ Passed | Added FastAPI irrigation service, Pydantic schemas, prediction/weather routes, lifespan loading, and model-status reporting. Direct and weather-assisted endpoints are live on port 8001. Flask port 8002 and frontend configuration remain unchanged by this step. Live `/health`, `/api/model-status`, direct POST, and weather-assisted POST passed; direct/weather reference values returned `Medium` |
| Mock module functionality | ⏳ Pending | Needs manual browser verification |
| English/Hindi toggle | ⏳ Pending | Needs manual browser verification |

## 17. Future Work

- [ ] Validate disease model class order and predictive quality against representative held-out real plant images
- [x] Integrate saved yield prediction model (no retraining)
- [ ] Smart irrigation rule engine
- [ ] Live weather API integration
- [ ] NLP/RAG AI assistant (bilingual English/Hindi)
- [ ] Fertilizer-disease integration (link detection results to fertilizer recommendations)
- [ ] Hindi/English AI assistant with voice support
- [ ] Final system testing and performance optimization
- [ ] Production deployment (Docker, cloud hosting)
- [ ] API rate limiting and authentication
- [ ] Logging and monitoring infrastructure

## 18. Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-11-18 | Diagnosed and hardened the Kerala weather-assisted 502 path. The prior `District geocoding provider request failed` response comes from the `httpx.RequestError` handler, after timeout and HTTP-status failures are handled separately; the original low-level exception was not logged, so its specific transport cause cannot be recovered. Confirmed Kerala/ERNAKULAM resolves to the exact Kerala administrative district and a live `POST /api/irrigation/predict-from-weather` returned HTTP 200 with `Medium` and Open-Meteo weather values. Added one bounded retry for geocoding timeouts, transport errors, and HTTP 429/5xx, and logs the underlying exception on final transport/timeout failure; exact state/district matching and prediction behavior are unchanged. Added Kerala resolution, transient transport/status retry, and final timeout regression tests. Geocoding tests 10/10 and irrigation validation/route tests 9/9 passed; live Kerala weather-assisted prediction passed. No model, prediction logic, location matching, or ports changed | AI Assistant |
| 2026-11-18 | Removed only the orange weather-period warning from the farmer-facing irrigation result. Preserved all weather values, summary metadata, helper behavior, prediction flow, and the documented unresolved compatibility limitation. Updated the focused irrigation UI test to assert the warning is absent and weather values remain rendered. Focused frontend tests passed. No backend, model, weather mapping, or calculation changes | AI Assistant |
| 2026-11-18 | Diagnosed the reported irrigation connection failure. Confirmed frontend URL configuration and FastAPI route registration were aligned; the error string came from `apiFetch` after a probe found no listener on port 8001. Live location lookup and direct prediction returned HTTP 200. Weather prediction initially returned HTTP 502 because Open-Meteo returned accented `Karnāl`/`Karnāl District` for the dataset label `KARNAL`, which strict matching rejected. Normalized diacritics and matched exact state/admin-district names; tests cover accented results and wrong-state rejection. After the fix, live weather-assisted prediction for Haryana/KARNAL returned HTTP 200. Confirmed `dev:full` has `concurrently --kill-others`, which stops Vite when the backend command exits; a controlled source-file reload kept both services alive, so no unconfirmed startup-script change was made. Frontend API-contract test, backend route/location/geocoding tests, frontend suite/build/typecheck passed; model, ports, direct prediction, and unrelated modules unchanged | AI Assistant |
| 2026-11-18 | Completed the unified startup migration verification and final port 8002 retirement. Verified `npm run dev:full` starts the existing FastAPI app on port 8001 and Vite on port 5173, then confirmed `/health`, `/api/model-status`, direct `/api/irrigation/predict`, weather-assisted `/api/irrigation/predict-from-weather`, and `/irrigation` all work after the Flask process is absent. Backend changed files: `app/main.py`, `app/routes/irrigation.py`, `app/schemas/irrigation.py`, `app/services/irrigation_service.py`, `app/services/irrigation_weather_service.py`, `scripts/test_unified_startup.py`, `scripts/test_irrigation_prediction_validation.py`, and `scripts/test_irrigation_weather.py`; removed `irrigation_api.py` and the Flask dependency. Frontend code was not changed in this final migration step. Tests: startup 2/2, irrigation parity 7/7, irrigation weather 4/4, historical weather 26/26, frontend 59/59, TypeScript check, and production build passed. Unified live direct/weather references returned `Medium`; model-status reported irrigation loaded; model SHA-256 remains `11ABC464BF3AE6CF2A8D97C4E456E485B2C722FE055F1ABD005459A85661C37F` | AI Assistant |
| 2026-11-18 | Consolidated smart irrigation into the existing FastAPI application on port 8001. Added `app/services/irrigation_service.py`, `app/services/irrigation_weather_service.py`, `app/schemas/irrigation.py`, and `app/routes/irrigation.py`; registered the router and lifespan/model-status loading in `app/main.py`. Preserved the exact model, feature order, preprocessing, probabilities, HTTP 400/502 validation, caller soil moisture, and weather response mapping. Removed `irrigation_api.py` and the Flask dependency; switched the frontend irrigation API wrapper to shared `VITE_API_BASE_URL` and removed the separate port 8002 environment variable. Verified `/health`, `/api/model-status`, direct prediction, weather-assisted prediction, FastAPI parity tests, frontend tests/build/typecheck, and live browser submissions on port 8001. Model SHA-256 remains unchanged | AI Assistant |
| 2026-11-18 | Planned migration of irrigation from the separate Flask port 8002 process into the existing FastAPI port 8001 application without implementation or model changes. Plan: add an irrigation service loaded once in FastAPI lifespan, Pydantic-compatible schemas/routes for all three existing irrigation weather/prediction contracts, weather helper reuse, FastAPI model-status startup state, direct/combined parity tests, shared-API frontend switch, and only then retirement of Flask 8002. Required preservation: exact 11-feature order, Pipeline/preprocessing, label probabilities, finite/boolean/category validation, HTTP 400/502 contracts, caller soil moisture, weather units/date/source, and existing frontend modes/responsive behavior | AI Assistant |
| 2026-11-18 | Completed irrigation end-to-end QA for direct and weather-assisted modes. Fixed direct request assembly to inspect only the 11 direct fields, preventing blank weather latitude/longitude/date fields from blocking direct submission. Added frontend success/probability response validation. Extended backend focused tests for caller soil-moisture preservation, invalid weather categories, and weather-provider failures. Frontend suite 59/59 passed, backend suite 9/9 passed, TypeScript check and production build passed, `/irrigation` route returned HTTP 200, live direct prediction returned HTTP 200/`Medium`, live boolean direct input returned HTTP 400, and live weather-assisted prediction returned HTTP 200/`Medium`. Remaining: manual responsive screenshots across device widths, authoritative model numeric physical ranges, and rainfall/sunlight training-period compatibility. No model or unrelated module logic changed | AI Assistant |
| 2026-11-18 | Added a separate weather-assisted mode to the existing irrigation UI while preserving direct prediction as the default and unchanged. Updated `Cropsense_ai_frontend/src/lib/api/irrigationApi.ts` with typed `predictIrrigationFromWeather`, added weather payload assembly and a read-only weather summary helper, and updated `Irrigation.tsx` with Direct/Weather-assisted mode controls. Weather mode collects latitude, longitude, optional date, and caller-entered `Soil_Moisture`; it sends no manual temperature/humidity/rainfall/sunlight/wind values and calls `POST /api/irrigation/predict-from-weather`. Results show source/provider/date/timezone and unit-labelled weather values, explicitly state that soil moisture is farmer-entered, and warn that one-day rainfall `precipitation_sum` and sunshine-hours conversion remain unproven against model training feature periods. Added 3 focused weather request/summary tests. Frontend suite now 57/57, TypeScript check and production build pass; live weather-assisted POST returned HTTP 200 and `Medium`. Direct prediction behavior and model/weather backend logic were unchanged; model SHA-256 remains `11ABC464BF3AE6CF2A8D97C4E456E485B2C722FE055F1ABD005459A85661C37F` | AI Assistant |
| 2026-11-18 | Audited only the irrigation UI, direct API client, Flask weather-assisted route, weather service, i18n labels, and existing frontend test convention. No code or model files were changed. Findings: retain direct prediction as the default and add an explicit weather-assisted mode rather than replacing direct mode. Weather mode should collect latitude, longitude, optional date, caller soil moisture, and the existing exact categorical fields; it should call `predict-from-weather` and render/fix the returned temperature, humidity, rainfall, sunshine, wind, units, date, timezone, and provider. It must preserve caller `Soil_Moisture` and never derive it from Open-Meteo or another source. It must visibly disclose that rainfall is one-day `precipitation_sum`, sunshine is seconds converted to hours, and those rainfall/sunshine measurement periods are not proven compatible with the model's training feature periods. Next: implement the mode switch/API wrapper/disclosure and focused request/display tests while preserving direct prediction | AI Assistant |
| 2026-11-18 | Integrated direct smart-irrigation prediction into the existing React page. Added `Cropsense_ai_frontend/src/lib/api/irrigationApi.ts` using dedicated `VITE_IRRIGATION_API_BASE_URL` fallback port 8002, `Cropsense_ai_frontend/src/lib/irrigationRequest.mjs` plus its type declaration for exact 11-feature request assembly, and `Cropsense_ai_frontend/tests/irrigationRequest.test.mjs` with 4 focused tests. Updated `Cropsense_ai_frontend/src/pages/Irrigation.tsx` to collect exact saved categories and six finite numeric fields, remove mock result submission, call `POST /api/irrigation/predict`, display decoded prediction and per-class probabilities, and show API errors. Updated `.env.example` and Flask CORS headers for the two localhost Vite origins; weather endpoints and model artifacts/preprocessing were unchanged. Validation: frontend 54/54 tests, `npx tsc --noEmit`, and `npm run build` passed; live Flask CORS preflight returned 200 and direct POST returned 200/`Medium`. Model SHA-256 remains unchanged. Next: weather-assisted frontend integration only after UI semantics are approved | AI Assistant |
| 2026-11-18 | Integrated live Open-Meteo daily weather with the isolated Flask irrigation backend. Added `irrigation_weather_service.py`, `GET /api/irrigation/weather`, and `POST /api/irrigation/predict-from-weather`; no model or frontend files changed. Mapping uses one UTC calendar day, archive API for past dates and forecast API for today/future dates: `temperature_2m_mean` to `Temperature_C` in °C, `relative_humidity_2m_mean` to `Humidity` in %, `precipitation_sum` to `Rainfall_mm` in mm, `sunshine_duration / 3600` to `Sunlight_Hours`, and `wind_speed_10m_mean` to `Wind_Speed_kmh` in km/h. The provider response is rejected for wrong units, missing fields, or invalid values; no missing weather value is substituted. `Soil_Moisture` is explicitly not mapped or invented and must remain caller-supplied. Mocked weather tests 4/4 passed. Live archive lookup for Pune coordinates and 2024-06-15 returned 25.2 °C, 81%, 3.4 mm, 11.3478 sunshine hours, and 11.3 km/h; combined prediction returned `Medium`. No model accuracy or feature-compatibility claim was made | AI Assistant |
| 2026-11-18 | Created the smallest isolated Flask backend for smart irrigation at `Cropsense_ai_backend/irrigation_api.py` and added `Flask>=3.1.0` to `Cropsense_ai_backend/requirements.txt`. The service loads the existing `krishitrust_lightgbm_11_features.joblib` bundle read-only, exposes `GET /health` and `POST /api/irrigation/predict`, validates exactly 11 required fields, numeric types, and five categorical domains, and returns the decoded `High`/`Low`/`Medium` label plus class probabilities. Live Flask 3.1.3 tests on port 8002 passed: valid prediction returned HTTP 200 and `Medium`; missing fields and invalid numeric input returned HTTP 400. The existing model artifact and FastAPI application were unchanged; no frontend integration was added | AI Assistant |
| 2026-11-18 | Performed a read-only audit of the saved smart-irrigation bundle `Cropsense_ai_backend/app/ml/irrigation/krishitrust_lightgbm_11_features.joblib` only. Verified SHA-256 `11ABC464BF3AE6CF2A8D97C4E456E485B2C722FE055F1ABD005459A85661C37F`, Python 3.11.8/LightGBM 4.6.0 loading, dictionary/package keys, exact 11-feature Pipeline interface, six numeric and five categorical preprocessing fields, categorical domains, target/classes, `predict`/`predict_proba`, and a representative `Medium` sample. Recorded no application integration or model changes | AI Assistant |
| 2026-11-04 | Fixed Hindi display of fertilizer recommendations. Added display-only Hindi translations for all 10 supported fertilizer class names from the existing model metadata; the saved backend recommendation string remains unchanged. The page translates the current result using the active language, without another model request, and shows a localized request-failure message while retaining any backend error detail. Added focused English/Hindi, complete-class-coverage, fallback, and source-name preservation tests. Validation: frontend tests 50/50, TypeScript check, and production build passed (existing large-chunk warning). No model, class metadata, or inference code changed | AI Assistant |
| 2026-11-04 | Fixed Hindi display for plant-disease prediction results. Added display-only Hindi translations for every unique disease name represented by all 38 existing model class labels; the original API prediction/class strings remain unchanged. The result component reads the active language, so disease names, confidence labels, retry/error messages update immediately without another model request. Added focused English/Hindi, unknown-name fallback, full-class coverage, and identifier-preservation tests. Validation: frontend tests 46/46, TypeScript check, and production build passed (existing large-chunk warning). No model, class-label artifact, or inference code changed | AI Assistant |
| 2026-11-04 | Added one-command local development startup: run `npm run dev:full` from `Cropsense_ai_frontend` to launch the existing FastAPI app from `Cropsense_ai_backend/.venv` on port 8001 and the existing Vite `dev` script on port 5173. Added only the `concurrently` development dependency; `--kill-others` stops the sibling server when either process exits, and Vite uses `--strictPort` to match existing CORS origins. Updated the shared API client's fallback, frontend `.env.example`, and backend startup/docs URLs to port 8001 after the reported Windows WinError 10013 on port 8000. Verification: exact combined command started both services; `/health` and frontend returned HTTP 200; model status reported all models loaded; after stopping the command, neither port retained a listener. Frontend tests 42/42, TypeScript check, and production build passed (existing large-chunk warning). No ML models or unrelated modules changed | AI Assistant |
| 2026-11-02 | Diagnosed the Yield Prediction page failure before editing. The running backend used system Python without `lightgbm`, so loading the existing joblib bundle logged `ModuleNotFoundError` and `/api/yield/options` returned 503. Confirmed the model loads under `Cropsense_ai_backend/.venv`; the browser called the configured fallback `http://127.0.0.1:8000`, and CORS allowed `http://localhost:5173`, so neither the API base URL nor CORS caused the failure. Updated backend setup/run commands to use `.venv`, and changed failed frontend option loads to show “Options unavailable” (English/Hindi) instead of “Loading...”. Restarted the backend under `.venv`: model status/options returned 200, CORS preflight returned 200, and live browser flow submitted Rice / Andhra Pradesh / KRISHNA / Kharif and displayed `3.0835`. Tests: yield API 10/10, frontend 42/42, TypeScript check and production build passed. No model artifact was modified | AI Assistant |
| 2026-10-28 | Diagnosed the disease page’s “Unable to connect” report. The initial local probe to the configured API base `http://127.0.0.1:8000` failed with connection refused because no backend was listening; no request reached FastAPI. No route, form field, response-schema, or CORS code mismatch was found: the client posts multipart field `image` to `/api/disease/predict`, and the backend defaults allow both local Vite origins. Started FastAPI with the project `.venv`; model status showed disease model loaded, `/health` returned 200, both local CORS preflights returned 200, and live multipart prediction returned 200. Browser upload reached the API and displayed only Predicted Disease and Prediction Confidence (%). The tested `hero.png` is a UI graphic, not a representative leaf image; this proves connection and rendering only, not disease accuracy. Frontend `npm test` passed 42/42, TypeScript check passed, production build passed with the existing >500 KB chunk warning; `scripts/test_disease_api.py` passed (HTTP 200 and invalid image HTTP 422). No application source or model artifacts changed; this was an operational startup issue. Start backend from `Cropsense_ai_backend` with `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`; start frontend from `Cropsense_ai_frontend` with `npm run dev -- --host 127.0.0.1 --port 5173`. Next: ensure both processes are running and use a representative plant-leaf image for inference-quality evaluation | AI Assistant |
| 2026-10-28 | Integrated the existing `app/ml/disease/plant_disease_efficientnet_b0.pth` and `disease_labels.json` without retraining or modifying either artifact. Added `DiseaseService` with EfficientNet-B0 raw state-dict loading once at startup, 38-class label validation/index mapping, RGB conversion and the specified 224×224 tensor/ImageNet normalization transform; added `POST /api/disease/predict` with multipart image validation and crop/disease/confidence response; registered disease service/status in FastAPI. Replaced mock frontend inference with the existing disease page calling the API and showing only Predicted Disease and Prediction Confidence (%), including English/Hindi labels and API error states. Changed files: backend `app/main.py`, new `app/services/disease_service.py`, `app/routes/disease.py`, `app/schemas/disease.py`, `scripts/test_disease_api.py`; frontend `src/pages/DiseaseDetection.tsx`, `src/components/disease/DiseaseResult.tsx`, new `src/lib/api/diseaseApi.ts`, `src/i18n/en.ts`, `src/i18n/hi.ts`; this file. Checks: backend focused inference/API script passed (HTTP 200, correct class-index label mapping, HTTP 422 invalid image), Python compile passed, frontend 42/42 tests passed, TypeScript check passed, production build passed with existing >500 KB chunk warning, browser upload E2E displayed `healthy` and `20.8%`. Only synthetic images were available for smoke testing; prediction quality and class-order accuracy still need validation on representative held-out real images. Next: test with labelled real plant images from the training/test set and confirm per-class label order/metrics | AI Assistant |
| 2026-10-26 | Completed a read-only fertilizer dataset/artifact consistency audit. Training/test CSVs contain 2,238/560 rows, the `Fertilizer` target, all 10 configured input features in exact order, and all 10 expected classes; extra `Remark` is explicitly excluded. Row counts and classes agree with metadata and the saved encoder. Re-ran the held-out test CSV through the saved preprocessor and XGBoost model: 556/560 correct; accuracy, macro precision/recall/F1, and weighted F1 match metadata exactly. No mismatches found. sklearn emitted its existing 1.6.0-to-1.6.1 artifact-version warnings. No dataset, model, or application files changed. Next: independently reproduce recorded CV F1 from the original cross-validation procedure if metric lineage verification is needed; no retraining or artifact changes are required for the audit | AI Assistant |
| 2026-10-26 | Added the fertilizer recommendation frontend page, route `/fertilizer-recommendation`, and sidebar link. Form includes Temperature, Moisture, Rainfall, PH, Nitrogen, Phosphorous, Potassium, Carbon, Soil, and Crop; calls the existing `fertilizerApi.ts` client, displays loading and API errors, and shows `recommended_fertilizer`. Added English/Hindi copy. Modified files: `Cropsense_ai_frontend/src/pages/FertilizerRecommendation.tsx`, `src/App.tsx`, `src/components/Sidebar.tsx`, `src/i18n/en.ts`, `src/i18n/hi.ts`; this file. Tests/checks: 42 frontend tests passed, `npx tsc --noEmit` passed, `npm run build` passed (existing large-chunk warning); browser E2E with valid sample returned HTTP 200 and displayed `Urea`. No backend or model files changed. Next: include fertilizer page in broader system E2E and verify categorical input labels against intended user-facing categories | AI Assistant |
| 2026-10-26 | Added `Cropsense_ai_backend/scripts/test_fertilizer_api.py` for the existing `POST /api/fertilizer/recommend` route. Covers a valid 10-feature request and response schema/decoded `recommended_fertilizer`, missing-field HTTP 422, and invalid numeric-value HTTP 422. Actual result: 3/3 tests passed; valid sample returned HTTP 200. Existing sklearn 1.6.0-to-1.6.1 artifact warnings appeared during model startup; no failures. Model artifacts/routes unchanged. Next: keep this script as the focused fertilizer API regression suite and run it after fertilizer API/service changes | AI Assistant |
| 2026-10-26 | Added fertilizer startup compatibility validation in `Cropsense_ai_backend/app/services/fertilizer_service.py`: the 10 configured ordered input features must match metadata and fitted preprocessor; the configured/metadata count, preprocessor output dimension, and native Booster must agree on 44 transformed features; ordered label encoder classes must match feature config and metadata. Any failed validation clears loaded components and leaves the service unavailable with a logged load error. Removed raw class-index fallback; label decoding errors now raise `RuntimeError`. Tests: actual artifact load and sample prediction passed (`Urea`); injected 10-feature config mismatch was rejected and service remained unavailable; injected label decode failure raised explicitly; changed module compiled successfully. Existing sklearn 1.6.0-to-1.6.1 pickle compatibility warnings remain. Model files were not modified. Next: add the verified compatibility/failure checks to a maintained automated fertilizer service test suite and run an HTTP-level fertilizer prediction check | AI Assistant |
| 2026-10-25 | Audited yield deployment readiness. Confirmed request schema and pair validation, successful read-only model load, fail-closed 503 behavior when artifacts/data are missing, and 652 pair options. Found localhost-only CORS, internal path/exception leakage in yield errors, OpenAPI error-envelope mismatch, and documentation claiming Python 3.13 despite the verified backend yield runtime being Python 3.11.8. Made CORS configurable through validated explicit `CORS_ORIGINS` (local defaults retained), sanitized client error details while retaining server logs, documented actual HTTP error envelopes, and corrected backend runtime documentation. Clarified backend environment configuration and frontend API URL example. Modified files: `Cropsense_ai_backend/app/main.py`, `app/routes/yield_prediction.py`, `app/schemas/yield_prediction.py`, `scripts/test_yield_prediction.py`, `.env.example`, `requirements.txt`, `README.md`; `Cropsense_ai_frontend/.env.example`; this file. Tests: `scripts/test_yield_prediction.py` 10/10 passed (CORS allow/deny/config parsing, 503 and missing-artifact behavior, generic 500 without detail leakage, OpenAPI error schema, category/pair validation, reference prediction); `compileall` passed. Runtime versions: Python 3.11.8, FastAPI 0.115.6, LightGBM 4.6.0, pandas 2.2.3, Pydantic 2.10.4, Uvicorn 0.34.0. No retraining/model artifact changes. Next: select a deployment platform, supply its exact browser origin and public API base URL, and verify packaged model/metadata/CSV in deployment | AI Assistant |
| 2026-10-25 | Enforced the audited 652 state/district pairs for yield prediction. The service loads pairs from `app/ml/yield/crop_final.csv`, canonicalizes against model categories, and rejects unsupported combinations with HTTP 422. `/api/yield/options` now includes `districts_by_state`; frontend district options update with state selection and clear when state changes. Modified files: `Cropsense_ai_backend/app/services/yield_prediction_service.py`, `app/routes/yield_prediction.py`, `app/schemas/yield_prediction.py`, `scripts/test_yield_prediction.py`; `Cropsense_ai_frontend/src/lib/api/yieldApi.ts`, `src/pages/YieldPrediction.tsx`; this file. Tests: focused backend suite 5/5 passed (including valid Andhra Pradesh/KRISHNA and invalid Assam/KRISHNA); frontend 42/42 tests passed; `npx tsc --noEmit`, `npm run build`, live HTTP 422 check, and browser district filtering/state-change reset passed (existing >500 KB chunk warning). A stale pre-change backend process initially returned the old options shape; restarted it with the backend `.venv` before browser verification. Model and artifacts unchanged. Next: source physical units remain unresolved | AI Assistant |
| 2026-10-25 | Completed yield target and state/district audit using the user-provided `Cropsense_ai_backend/app/ml/yield/crop_final.csv` and notebook cells 6–7, 38, 118–121, 131, 134. CSV has 235,123 rows; target equals `Production / Area` across all rows (tolerance 1e-9; maximum absolute error 5.69e-14). Notebook's earlier intermediate target is named `yield_tonnes_per_hectare`, so that is the declared intended unit, but source data defines no `Area`/`Production` units and metadata does not settle physical units. CSV contains 652 distinct state/district pairs; API category options exactly match all four distinct field sets (104 crops, 33 states, 646 districts, 6 seasons), but options/model contain no pair allowlist. Observed Andhra Pradesh/KRISHNA predicts 3.08347; unobserved Assam/KRISHNA still returns HTTP 200 (1.05068). Changed file: `PROJECT_PROGRESS.md` only. No model/artifact/application code changed. Next: obtain authoritative source-unit documentation and decide whether API must reject unobserved pairs | AI Assistant |
| 2026-10-25 | Continued the yield target/pairing investigation. Notebook outputs distinguish cell 38's intermediate dataset (244,106 input, 240,403 retained, 123 crops; target named `yield_tonnes_per_hectare`) from final cell 131's `crop_final.csv` (235,123 rows, 104 crops) used by LightGBM. The former computes Production/Area; the latter consumes `yield_per_area` without formula/unit derivation. Kaggle identifies data.world as source but offers no field-unit definition; cited data.world page now redirects to community retirement notice. Cell 134 explicitly confirms Andhra Pradesh/KRISHNA only (case-sensitive `"Krishna"` membership false while canonical `KRISHNA` is saved). Artifact/API use independent field categories and contain no pair allowlist; live Assam/KRISHNA HTTP 200 (~1.0507) confirms the endpoint accepts unverified pair combinations. Reviewed attached `file_requirements.txt`; it contains dependency pins only, not data/unit evidence. Changed file: `PROJECT_PROGRESS.md` only. Model/artifact/code unchanged. Next: obtain exact final `crop_final.csv` and source field-unit documentation; then compute training-observed state/district pairs and decide API rejection policy | AI Assistant |
| 2026-10-25 | Audited yield target and location-pair evidence without changing application/model files. Notebook cells 6–7 and 38 calculate `Production / Area`; cell 38 labels a separate intermediate as `yield_tonnes_per_hectare`, and cell 44 excludes Coconut because production units may be inconsistent. Final tuned cells 118–121/131 load Drive `crop_final.csv` and use the precomputed `yield_per_area` without defining its formula/unit; that file and source-unit documentation are absent locally, so physical units are not conclusively established. Final cell 131 saves independent unique category lists, not state/district pairs. `GET /api/yield/options` mirrors those per-field lists; live POST with Assam + KRISHNA returned 200, proving no joint-pair validation. Cell 134's Andhra Pradesh/Krishna check is a single pair, not full coverage. Changed file: `PROJECT_PROGRESS.md` only. Model/artifact and application code unchanged. Next: obtain the exact final training CSV and source units, then compute/approve a joint state/district allowlist and decide API behavior | AI Assistant |
| 2026-10-25 | Step 1 browser integration verification completed using the existing local setup. Commands: backend `Set-Location E:\CropSense_AI\Cropsense_ai_backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`; frontend `Set-Location E:\CropSense_AI\Cropsense_ai_frontend; npm run dev -- --host 127.0.0.1 --port 5173`. Actual results: backend `/health` healthy, `yield_model.loaded=true`, `GET /api/yield/options` returned 104 crops/33 states/646 districts/6 seasons; frontend page loaded in browser, all four category selectors populated, test submission Rice / Andhra Pradesh / KRISHNA / Kharif produced HTTP 200 and displayed `3.0835` with 1997–2015 note. No integration issue reproduced; no application/model changes made. Changed file this step: `PROJECT_PROGRESS.md` only. Next: confirm target physical unit and supported state/district pairings with model/data owner | AI Assistant |
| 2026-10-25 | Integrated the existing saved LightGBM model read-only from `Cropsense_ai_backend/app/ml/yield/cropsense_yield_tuned_deployment.joblib` with metadata `Cropsense_ai_backend/app/ml/yield/model_metadata.json`; exact inputs `Crop`, `State_Name`, `District_Name`, `Season`, target `yield_per_area`. Added `GET /api/yield/options`, `POST /api/yield/predict`, and yield model status; options and input validation use the embedded schema (104 crops, 33 states, 646 districts, 6 seasons), normalizing category case/edge whitespace to canonical saved labels. Connected the existing React page and removed mock result/chart and mismatched numeric fields. Added backend LightGBM 4.6.0 requirement. Modified files: backend `requirements.txt`, `app/main.py`, `app/routes/yield_prediction.py`, `app/schemas/yield_prediction.py`, `app/services/yield_prediction_service.py`, `scripts/test_yield_prediction.py`; frontend `src/lib/api/yieldApi.ts`, `src/pages/YieldPrediction.tsx`, `src/i18n/en.ts`, `src/i18n/hi.ts`; this progress file. Tests: API reference example ~3.0835, category counts/case normalization/invalid inputs; frontend 42 tests, TypeScript check, production build passed. No model retraining or artifact overwrite. Next: browser integration check is completed; confirm target units and supported state/district pairings | AI Assistant |
| 2026-10-21 | Implemented weather-layer Open-Meteo geocoding fallback for unresolved registered locations, with a strict country/state/district administrative match, explicit Karnataka/BELGAUM→Belagavi geocoder metadata rule, rejection of zero/multiple/mismatched results, coordinate validation, 10s geocoding timeout, and persistent 365-day cache of successful matches. Verified live geocoder result: `Belgaum Airport`, country India, state Karnataka, admin2 `Belgaum district`, admin3 `Belagavi`, coordinates 15.85929, 74.61829; returned as a weather-only reference point (not reviewed district-HQ coordinates). Crop/model `BELGAUM` remains unchanged. Focused tests passed: weather 26, location resolution 16, crop-weather contract 6, legacy validation/contract 7; Pylance reports no errors. Recommendation/climate compatibility gates remain unchanged; model artifacts, dataset, 12-feature contract, and legacy endpoint untouched | AI Assistant |
| 2026-10-21 | Historical weather reliability: added two bounded attempts (initial + 1 exponential-backoff retry) for timeouts, transport errors, HTTP 429, and HTTP 5xx; permanent HTTP errors are not retried. Existing 120-second timeout and 30-day cache remain. Focused tests passed: weather 20, historical workflow 11, crop-weather/model contract 6, legacy input/endpoint contract 7; no Pylance errors. BELGAUM remains unavailable: official-domain redirect is evidence for review, but authenticated LGD identity and reviewed headquarters coordinates are still missing; registry alias remains inactive. ERA5 temperatures/humidity are verified as °C/% and Kharif window is explicitly June–October; other season windows are proposals. Rainfall unit field is mm, but source measurement semantics and compatibility of all climate aggregates with training features remain unverified, so candidate scores/recommendations remain gated. No model, artifact, dataset, feature contract, or legacy endpoint changes | AI Assistant |
| 2026-10-21 | External-source review prepared, not approved: the Government of Karnataka legacy `belgaum.nic.in/en/` district URL redirects to the current `belagavi.nic.in/en/` district portal, providing official-domain alias evidence for human review. The live LGD district record/code could not be authenticated in this review; project candidate Belagavi/527/version 2 remains unverified. The district portal gives the DC office postal address but no authoritative coordinates/reference-point record. Recorded actual URLs, evidence limits, and next approval/source authorities in the existing BELGAUM review section. Crosswalk/registry remain pending/unresolved; no application, dataset, model, or artifact changes. Documentation-only; tests not run. | AI Assistant |
| 2026-10-21 | Prepared a BELGAUM weather-evidence review record only. The official Karnataka Belagavi district portal confirms the current district and Deputy Commissioner’s office address, but does not establish the historical BELGAUM alias or publish verified headquarters coordinates. Project LGD candidate Belagavi/527/version 2 remains unauthenticated per the workbook provenance audit; latitude, longitude, reference point, and coordinate evidence remain unset. Crosswalk and weather registry remain pending/unresolved; no alias was activated. No code tests run because changes are review documentation only. | AI Assistant |
| 2026-10-21 | Rechecked Karnataka/BELGAUM weather alias evidence. Mapping remains inactive: the BELGAUM-to-LGD crosswalk is pending; the official snapshot lists Belagavi (ID 527) only as an unverified candidate; BELGAUM's weather registry entry has unresolved status and null coordinates/source records. No weather-only alias or coordinate was added; unresolved weather requests remain blocked and crop/model district remains BELGAUM. Focused tests passed: historical weather 19, location resolution 16, crop-weather/model contract 6, legacy validation/endpoint contract 7. No model, dataset, artifact, or application code changes | AI Assistant |
| 2026-10-21 | Rechecked current historical workflow blockers without changing application behavior. BELGAUM weather mapping remains inactive: the crop-to-LGD crosswalk is pending alias review and the registry has no reviewed coordinates/source record; the LGD snapshot's Belagavi district ID alone is insufficient. Historical area policy remains exact normalized state/district/season/crop with strict prior-year cutoff; 27/45 candidates have no eligible Rabi area and no other-season, future-year, zero, or farmer-area substitution is used. Rainfall is returned, but compatibility with model training inputs remains unverified, so recommendation gates remain enabled. Focused tests passed: historical weather 19, location resolution 16, area lookup 10, legacy contract/input validation 7; frontend 22, TypeScript check, and production build passed (existing chunk-size warning). No model, artifact, dataset, inference, or endpoint changes | AI Assistant |
| 2026-10-21 | Normalized state, district, season, crop, and soil labels in historical feature matching using trimmed/collapsed whitespace and case-folding only; no fuzzy crop aliases or alternate-location matches. Kept strict `< target_year`, exact state/district/season scope, soil-independent area selection, and conflict rejection. Missing diagnostics now distinguish other-season-only history (reported but not used) from absent crop history and target/future exclusions. Real-data Karnataka/BELGAUM/Rabi target-year 2026 result remains 18/45: 0 recovered by normalization, 27 genuinely missing exact-season eligible area; 21 have records in other seasons and 6 have no prior crop-area row anywhere at that location. Tests passed: area lookup 10, candidate experiment 12, workflow 11, legacy validation 7; frontend 22, TypeScript check and production build passed. BELGAUM weather remains blocked pending reviewed administrative identity and coordinate evidence. Model, artifacts, dataset, 12-feature contract, and legacy endpoint unchanged | AI Assistant |
| 2026-10-21 | Expanded the historical-weather location coverage workflow without guessing coordinates. Replaced the hard-coded two-location registry-builder entry point with a wrapper around the reviewed LGD/crosswalk/coordinate-evidence workflow, which preserves existing verified pilots and promotes only fully reviewed exact state/district records. Updated English/Hindi guidance to explain evidence-based coverage and added tests that promote a reviewed location while retaining existing pilot data, keep unresolved locations disabled, and reject unsupported seasons. Karnataka/BELGAUM remains unresolved: the current official LGD snapshot identifies Belagavi (district ID 527), but the exact historic-label crosswalk has not been approved and no reviewed headquarters coordinate evidence is present. Focused backend tests passed: weather 19/19, location resolution 16/16; frontend tests 22/22, TypeScript and production build passed (existing large-chunk warning). No model, dataset, or feature contract changes | AI Assistant |
| 2026-10-21 | Fixed the farmer-area submit blocker: the UI read from `FormData`, but the acres control lacked a `name`, so a visible value became missing; the request builder now converts the form string to a JSON number under the exact backend key. Client validation stays on the form, and HTTP 422 is labeled as request validation rather than connection failure. Added 3/9-acre request/schema regressions. Area coverage root cause verified: exact location/season/crop matching, no soil filter, latest prior record; 24/45 for target years >2015, versus 19/45 at cutoff 1999. The reported 10/45 was not reproduced with the current dataset/context. Missing candidate messages now report unmatched exact keys or excluded target/future years. Belgaum remains unresolved because crosswalk status is pending and no project-verified coordinates exist; improved diagnostic text, no guessed mapping. Response now separates scoring blockers from recommendation blockers and returns context for auditability. Focused backend tests (57 total across workflow, feature lookup, candidate experiment, weather, and legacy contract), frontend tests (22), TypeScript, and production build pass. No dataset/model/legacy endpoint changes | AI Assistant |
| 2026-10-21 | Added required farmer-available acreage in acres to the new historical workflow only, with numeric >0 and <=100,000 validation and full-precision conversion at 0.40468564224 hectares per acre. Response returns acres/hectares separately and each candidate's historical area with its paired year; farmer acreage is never passed into model feature assembly. English/Hindi UI distinguishes planning land from historical cultivated area. Backend tests passed (workflow 9, legacy contract 7, candidate experiment 12); frontend tests 20, TypeScript check, and production build passed. Legacy request/response and exact 12-feature row remain unchanged. Farmer acreage is planning-only and not validated for model inference | AI Assistant |
| 2026-10-21 | Used the project owner's confirmation to trust the existing dataset source verification and integrated the year-specific NPK lookup into isolated candidate-wise scoring. The farmer workflow now submits context only, assembles each available candidate row from location/season/soil, looked-up NPK, historical weather, strictly pre-target-year rainfall, and candidate-specific prior area plus its paired year, then invokes the existing preprocessor and XGBoost model. Real-artifact HTTP test for Karnataka/MYSORE/Kharif/Black returned 200: 24/45 candidates scored, 21 lacked prior area, NPK lookup succeeded for all 24, weather 24.1345°C/79.5757%, rainfall 655.8944 mm (1997–2014). Raw outputs: Arhar/Tur 0.0010167, Bajra 0.0094807, Black pepper 0.0009240, Castor seed 0.0916781, Cowpea(Lobia) 0.0150808, Dry chillies 0.0185807, Dry ginger 0.0065793, Gram 0.0014171, Groundnut 0.0067797, Horse-gram 0.0210697, Jowar 0.0172920, Maize 0.0014971, Moong(Green Gram) 0.0103301, Niger seed 0.0003375, Onion 0.0017527, Peas & beans (Pulses) 0.0005537, Potato 0.0005167, Ragi 0.0017696, Rice 0.3979968, Sesamum 0.0016086, Small millets 0.0001473, Soyabean 0.0688680, Sunflower 0.3380379, Urad 0.0079436. Ranking remains `not_validated`: candidate rows use different historical area/year values, NPK is averaged across matching location/season/year records, and weather/rainfall compatibility with training features has not been validated. No recommendation was returned. Backend tests passed: candidate experiment 12/12, workflow 7/7, historical feature lookup 6/6, rainfall 13/13, NPK 13/13, legacy validation 6/6; frontend tests 19/19, TypeScript and build passed (existing chunk warning). Model, artifacts, dataset, feature contract, and legacy endpoint unchanged | AI Assistant |
| 2026-10-21 | Tightened isolated candidate-experiment tests for complete 12-feature row assembly, exact feature order/types, candidate-specific area/year pairing, missing NPK/weather/rainfall blockers, and partial candidate history. A missing area record for one crop is explicitly marked while other candidates proceed independently. Candidate-wise scoring remains experimental and no ranking is exposed. Focused backend tests passed: candidate experiment 10/10, workflow 6/6, historical feature lookup 6/6, rainfall lookup 13/13, crop validation 6/6. Frontend tests 19/19, TypeScript check and production build passed (existing chunk-size warning). Complete rows and scores were exercised only with verified test fixtures; no real farmer-workflow candidate scores were computed because NPK provenance and climate compatibility remain unverified, some crops lack area history, and ranking is unvalidated. No real crop recommendation was generated. Existing endpoint, model, artifacts, dataset, and feature contract remain unchanged | AI Assistant |
| 2026-10-21 | Connected the separate farmer workflow to backend historical weather and strict pre-target-year rainfall lookup; frontend now submits context only and displays returned weather/rainfall lookup status. Rainfall aggregation excludes target/future years; area/year pairing and candidate NPK lookup remain as before, with NPK source provenance and climate/training compatibility still unverified. Focused backend tests passed: workflow 6/6, rainfall lookup 13/13, candidate experiment 8/8, historical feature lookup 6/6, crop validation 6/6. Frontend tests 19/19, TypeScript check and production build passed (existing chunk-size warning). Real-artifact HTTP request to Karnataka/MYSORE returned 200; weather 24.13°C/79.58% for 2010–2019 and rainfall 655.89 mm for prior dataset years 1997–2014 were retrieved, 24/45 candidates had area history, 24 were NPK-unverified, and 0 candidate scores were produced. No complete 12-feature input or trustworthy crop recommendation was generated; production prediction remains disabled. Existing `/api/crop/recommend`, model, artifacts, dataset, and 12-feature contract were unchanged | AI Assistant |
| 2026-10-21 | Connected prior-year candidate coverage to separate `POST /api/crop/recommend-historical` and the crop form. Farmers provide location/season and soil classification only; target year is server-selected, area/year pairs are candidate-specific and strictly prior, and existing weather/rainfall lookups are passed as optional references. Their training compatibility and candidate NPK provenance remain unverified, while 21/45 candidates lack prior area in the real-data run; therefore no model scores or recommendation are returned. Existing `/api/crop/recommend`, validation, artifacts, dataset, and 12-feature contract remain unchanged. Validation: backend candidate tests 8/8, workflow route tests 3/3, historical feature tests 6/6, legacy crop validation tests 6/6; frontend tests 19/19, TypeScript check and production build passed. Real-data HTTP workflow returned 200 with 24/45 area coverage, 24 NPK-blocked candidates, 24 climate-compatibility blockers, and 0 scores; unchanged legacy endpoint returned HTTP 200 and a model response. No complete trustworthy crop recommendation was tested. Vite retains its existing large-chunk warning | AI Assistant |
| 2026-10-21 | Added an isolated candidate-wise scoring experiment for the existing 45-class crop model. Candidate rows use each crop's latest matching area and its paired `crop_year` strictly before the target year; unverified candidate-specific NPK blocks scoring, and coverage/missing history/validation failures are recorded. Tests cover all 45 classes, target/future exclusion, paired feature rows, unavailable/unverified NPK, and validation failures. Fake-artifact tests exercise the scoring path; real-artifact smoke run found 24/45 prior-area matches and withheld all scores for unverified NPK. Score ranking remains unvalidated; no production endpoint, model artifacts, dataset, or frontend changed | AI Assistant |
| 2026-10-21 | Added `POST /api/crop/historical-features`, a reference-only strict-prior-year lookup. It returns the latest unambiguous crop/location/season area with its matching historical year; NPK requires exact crop/soil/location/season context, but values are withheld and source labels disclosed because notebook/dataset `npk_source` provenance is undocumented. Added focused missing-history, year-filter, pairing, and ambiguity tests. Model, artifacts, prediction request, and frontend gate unchanged; live prediction remains disabled | AI Assistant |
| 2026-10-21 | Reviewed remaining crop UI/API integration without repeating model audits: crop API client and historical NPK/rainfall/verified-weather reference lookups are wired; optional year-specific NPK display could be added as reference-only UI but would not unblock inference. The submit gate remains closed because farmer-entered total land is not validated as the model's crop-specific historical `area`. TypeScript check passed and 17 focused frontend tests passed. No application code or artifacts changed. Single blocker: establish a valid prediction-time `area` meaning | AI Assistant |
| 2026-10-21 | Reconfirmed the focused `area` decision from the local training data and serving code: farmer-entered total hectares are not proven compatible, and the data has no crop-independent value to use before a crop is predicted. Keep frontend inference disabled; next obtain owner validation for the intended serving meaning. No code or artifacts changed | AI Assistant |
| 2026-10-21 | Completed a focused `area` review: documented Kaggle source columns and local CSV columns; prior row comparison confirms local `area` preserves source `Area`; crop-specific values differ within location/season/year groups, so no defensible crop-independent value exists before prediction. Farmer total land in hectares is not established as compatible; publisher metadata does not independently specify the unit. No code, data, or artifacts changed. Keep inference gated; request owner-approved prediction-time semantics and compatibility evidence | AI Assistant |
| 2026-10-21 | Kept crop frontend inference gated because feature-source compatibility remains unresolved; documented farmer-entered total available land in hectares versus historical crop-specific training area; added a focused `NAMSAI` test confirming HTTP 422 from the fitted-category guard. TypeScript check passed, frontend tests 17/17, crop validation tests 6/6. No model artifacts or feature definitions changed. Next: resolve the compatibility/provenance decision for the existing input sources before enabling frontend inference | AI Assistant |
| 2026-10-21 | Rechecked deployed artifacts in backend `.venv`: checker passed; confirmed 12 raw/673 transformed features and 45 CSV-matching crop labels; documented sklearn/XGBoost compatibility warnings, `requirements.txt` runtime mismatch, unresolved `NAMSAI`, and the single next provenance action. Crop input validation (5) and weather contract (6) tests passed; no artifacts or application code changed | AI Assistant |
| 2026-10-21 | Confirmed the area feature is historical cultivated area for each crop/district/season/year record and is copied unchanged from Kaggle source `Area`; project-confirmed unit is hectares, although accessible Kaggle metadata lacks a field-level unit definition. Recommended keeping frontend inference gated and evaluating a separate model without area for farmer-available-land use | AI Assistant |
| 2026-10-21 | Traced local `area` to Kaggle Crop Production in India: all 218,189 local rows exactly match source `Area` by normalized record key; Kaggle credits retired data.world source, but accessible metadata provides no unit; frontend meaning compatibility remains unresolved | AI Assistant |
| 2026-10-21 | Inspected training CSV, notebook, backend schema, and crop form for `area`; numeric field is present throughout but no inspected source defines its unit or proves available land area matches the training meaning; frontend inference remains gated | AI Assistant |
| 2026-10-21 | Added year-specific NPK lookup using exact state/district/season/year groups from the training CSV; returns NPK means with ranges/count plus same-group temperature, humidity, and rainfall; rejects unsupported years, missing groups, and conflicting non-NPK values; 13 focused tests pass | AI Assistant |
| 2026-10-21 | Audited crop notebook, dataset, and artifacts: schema/feature dimensions/classes and 800-tree model parameters align, but exact lineage remains unverified; documented `NAMSAI` category discrepancy; frontend inference remains gated | AI Assistant |
| 2026-10-21 | Added crop API categorical and state-district validation; verified valid and invalid requests against backend endpoint; frontend inference remains gated | AI Assistant |
| 2026-08-28 | Initial full-stack architecture created: FastAPI backend, API layer, Crop Recommendation connected to real API, documentation | AI Assistant |
| 2026-08-29 | Fixed crop inference pipeline: `check_models.py` now uses XGBClassifier + named pandas DataFrame (was using raw Booster + unnamed numpy array). Added Pydantic `Literal` validation for soil types (422 for invalid values like "Sandy Soil"). Added `ValueError` handler in crop route (422 instead of 500). Verified all 7 model files present. Confirmed crop model predicts `Pigeon Peas` for standard test input. Feature order: Temperature, Humidity, Rainfall, PH, Nitrogen, Phosphorous, Potassium, Carbon, Soil. | AI Assistant |
