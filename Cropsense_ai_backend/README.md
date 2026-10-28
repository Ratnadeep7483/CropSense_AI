

 CropSense AI — Backend

Backend API for the CropSense AI agricultural recommendation system.  
Built with **FastAPI** and **XGBoost** trained ML models.

---

## Architecture

```
React Frontend (Vite)
        │  HTTP
        ▼
   FastAPI Backend
   ├── Crop service        → XGBoost model
   ├── Fertilizer service  → Preprocessor → XGBoost → Label Encoder
   └── Soil service        → EfficientNet-B2
```

## Folder Structure

```
Cropsense_ai_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, CORS, health endpoints
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── crop.py              # Crop recommendation and lookup endpoints
│   │   ├── fertilizer.py        # POST /api/fertilizer/recommend
│   │   └── soil.py              # POST /api/soil/predict
│   ├── services/
│   │   ├── __init__.py
│   │   ├── crop_service.py      # XGBoost crop model loading + inference
│   │   ├── crop_location_service.py # Dataset-backed location and area lookup
│   │   ├── fertilizer_service.py # XGBoost fertilizer model + preprocessing
│   │   └── soil_service.py      # EfficientNet-B2 soil image inference
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── crop.py              # Pydantic request/response schemas
│   │   ├── fertilizer.py
│   │   └── soil.py
│   └── ml/
│       ├── __init__.py
│       ├── crop/
│       ├── fertilizer/
│       └── soil/
│           ├── efficientnet_b2_soil_best.pth
│           └── soil_classes_97.json
├── scripts/
│   ├── check_models.py          # Model verification script
│   ├── test_crop_api.py
│   └── test_soil_api.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Requirements

- **Python**: 3.11.8 (verified yield-model runtime)
- **scikit-learn**: 1.6.1
- **XGBoost**: 3.4.1

## Installation

### 1. Create Virtual Environment

```bash
cd Cropsense_ai_backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Place Model Files

Copy the trained model files from the ZIP archive into the exact locations:

**Crop Recommendation** → `app/ml/crop/model_artifacts/`

| File | Description |
|------|-------------|
| `crop_xgboost_model.joblib` | Deployed XGBoost classifier |
| `crop_preprocessor.joblib` | Fitted 12-feature preprocessing pipeline |
| `crop_label_encoder.joblib` | Fitted crop-label encoder |

**Fertilizer Recommendation** → `app/ml/fertilizer/`

| File | Description |
|------|-------------|
| `fertilizer_xgboost.json` | Trained XGBoost fertilizer model |
| `fertilizer_model_metadata.json` | Model metadata / configuration |

**Fertilizer Preprocessing** → `app/ml/fertilizer/preprocessing/`

| File | Description |
|------|-------------|
| `fertilizer_feature_config.json` | Feature configuration |
| `fertilizer_label_encoder.joblib` | Fitted LabelEncoder |
| `fertilizer_preprocessor.joblib` | Fitted preprocessing pipeline |

### 4. Verify Models

```bash
python scripts/check_models.py
```

### 5. Run the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Interactive Swagger documentation is available at:

**http://127.0.0.1:8000/docs**

## API Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/model-status` | ML model loading status |

### Crop Recommendation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/crop/location-options` | Get states, state-specific districts, and district-specific seasons from the crop dataset |
| `GET` | `/api/crop/historical-area` | Get exact district/season crop-year-soil records and their model features |
| `POST` | `/api/crop/recommend-from-record` | Resolve one selected training row and predict from its exact 12 features |
| `POST` | `/api/crop/recommend` | Get crop recommendation |
| `POST` | `/api/crop/npk-lookup` | Look up mean historical N, P, and K by exact dataset state, district, and season |
| `POST` | `/api/crop/rainfall-lookup` | Look up a dataset-derived multi-year rainfall mean by exact state, district, and season (rainfall provenance and measurement semantics are unverified) |
| `POST` | `/api/soil/predict` | Classify soil from a JPEG, PNG, or WebP image upload |

The NPK lookup uses `data/Copy of crop_recommendation_45_with_year_area.csv`.
When multiple rows share the exact state/district/season key, it returns the
arithmetic mean of each NPK field and the number of matched records. A missing
exact key returns HTTP 404. This lookup is separate from crop-model inference.

The location-options, historical-area, and `/recommend-from-record` workflows
use `data/Copy of crop_recommendation_45_with_year_area.csv`. The location and
season selectors are derived from distinct values in this file. The historical
area endpoint returns rows filtered by state, district, and optional exact
season; each record includes its crop, year, soil, area, and the matching NPK
and climate fields. The frontend displays area in acres plus the original
dataset value in hectares. Farmer-available land is not an input.

`/recommend-from-record` accepts only the selected state/district/season/crop/
year/soil key; it does not accept or invent feature values. The backend requires
an exact, unambiguous match and assembles the model's 12 raw fields from that
row. Duplicate rows with identical features are treated as one raw feature
vector; conflicting or missing fields are rejected. NPK and climate values are
not averaged across crops, years, or locations. `npk_source` is returned for
transparency. The training notebook uses the CSV fields as-is and the saved
preprocessor confirms the same 12-feature order, but the dataset does not
document weather aggregation periods or verify all NPK source methods.

This endpoint's classifier output is not a validated agronomic recommendation:
the selected historical row already has a crop label. Candidate-wise scores
from the experimental `/recommend-historical` workflow are not used as a crop
ranking. The legacy `/api/crop/recommend` path and request shape are retained.

Send a multipart form upload using the `image` field. Successful responses
contain `predicted_class` and a `confidence` value from 0 to 1. Uploads are
limited to 10 MB and 40 megapixels.

Run a soil API check with a real soil image:

```bash
python scripts/test_soil_api.py path\to\soil-image.jpg
```

**Request:**
```json
{
    "temperature": 25.0,
    "humidity": 70.0,
    "rainfall": 100.0,
    "ph": 6.5,
    "nitrogen": 60.0,
    "phosphorous": 70.0,
    "potassium": 70.0,
    "carbon": 1.5,
    "soil": "Loamy Soil"
}
```

**Response:**
```json
{
    "success": true,
    "recommended_crop": "Rice"
}
```

### Fertilizer Recommendation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/fertilizer/recommend` | Get fertilizer recommendation |

**Request:**
```json
{
    "temperature": 30.0,
    "moisture": 55.0,
    "rainfall": 120.0,
    "ph": 6.8,
    "nitrogen": 50.0,
    "phosphorous": 40.0,
    "potassium": 45.0,
    "carbon": 1.2,
    "soil": "Loamy Soil",
    "crop": "Rice"
}
```

**Response:**
```json
{
    "success": true,
    "recommended_fertilizer": "Urea"
}
```

## Frontend Configuration

The React frontend must be configured to connect to this backend.

Set the environment variable in the frontend:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

The frontend dev server typically runs on `http://localhost:5173`.

## CORS

The backend allows requests from:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Models not loading | Run `python scripts/check_models.py` to diagnose |
| CORS errors | Ensure the frontend is running on an allowed origin |
| Import errors | Make sure virtual environment is activated |
| Port in use | Change port: `uvicorn app.main:app --port 8001` |

## Implementation Status

### Real (Backend Ready)
- ✅ Crop Recommendation (XGBoost)
- ✅ Fertilizer Recommendation (XGBoost + Preprocessing)

### Mock / Pending
- ⏳ Disease Detection (YOLOv8 — not yet integrated)
- ⏳ Yield Prediction (TBD)
- ⏳ Smart Irrigation (Rule-based — not yet integrated)
- ⏳ Weather (Live API — not yet integrated)
- ⏳ AI Assistant (NLP/RAG — not yet integrated)

## Model Version Control

Trained model files (`.json`, `.joblib`) are **included** in version control.  
If models become large, consider migrating to Git LFS or a model registry.

## Future Integration

| Module | Technology | Status |
|--------|-----------|--------|
| Disease Detection | YOLOv8 | Pending |
| Yield Prediction | TBD | Pending |
| Smart Irrigation | Rule-based | Pending |
| Weather | External API | Pending |
| AI Assistant | NLP / RAG | Pending |
