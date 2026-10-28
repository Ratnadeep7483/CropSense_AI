export const en = {
  // App
  appName: "CropSense AI",
  appTagline: "Predictive Intelligence for Smart Agriculture",

  // Navbar
  language: "English",
  notifications: "Notifications",
  profile: "Profile",

  // Sidebar sections
  sectionMain: "MAIN",
  sectionAiTools: "AI TOOLS",
  sectionInformation: "INFORMATION",

  // Sidebar links
  dashboard: "Dashboard",
  cropRecommendation: "Crop Recommendation",
  fertilizerRecommendation: "Fertilizer Recommendation",
  diseaseDetection: "Disease Detection",
  yieldPrediction: "Yield Prediction",
  smartIrrigation: "Smart Irrigation",
  weather: "Weather",
  aiAssistant: "AI Assistant",

  // Landing page
  heroHeadline: "Smart Farming Powered by AI",
  heroSubtext:
    "CropSense AI helps farmers understand crop health, make better crop decisions, manage irrigation and access agricultural guidance in simple language.",
  getStarted: "Get Started",
  askCropSense: "Ask CropSense AI",
  featCropRec: "Crop Recommendation",
  featCropRecDesc:
    "Get AI-powered crop suggestions based on your soil and climate conditions.",
  featDisease: "Disease Detection",
  featDiseaseDesc:
    "Upload a photo of your crop to instantly identify diseases and get treatment advice.",
  featYield: "Yield Prediction",
  featYieldDesc:
    "Estimate your expected crop production using farm and environmental data.",
  featIrrigation: "Smart Irrigation",
  featIrrigationDesc:
    "Get intelligent irrigation recommendations based on weather and crop needs.",
  featWeather: "Weather Insights",
  featWeatherDesc:
    "Access real-time weather data and forecasts for your farming region.",
  featAssistant: "AI Assistant",
  featAssistantDesc:
    "Ask questions about farming in English or Hindi — text or voice.",
  howItHelps: "How CropSense AI Helps Farmers",
  howStep1Title: "Enter Your Farm Details",
  howStep1Desc:
    "Provide information about your soil, crops, and location to get personalized insights.",
  howStep2Title: "Get AI-Powered Insights",
  howStep2Desc:
    "Our AI models analyze your data to provide crop recommendations, disease detection, and more.",
  howStep3Title: "Make Better Decisions",
  howStep3Desc:
    "Use actionable intelligence to improve crop yield, reduce disease, and optimize irrigation.",

  // Dashboard
  greeting: "Good Morning, Farmer 🌱",
  dashboardSubtitle: "Here's your farm intelligence for today.",
  weatherLabel: "Weather",
  cropHealthLabel: "Crop Health",
  irrigationLabel: "Irrigation",
  recommendedCropLabel: "Recommended Crop",
  healthy: "Healthy",
  noDiseaseDetected: "No disease detected",
  tomorrow: "Tomorrow",
  suitability: "Suitability",
  viewRecommendation: "View Recommendation",
  weatherForecast: "Weather Forecast",
  temperature: "Temperature",
  rainfall: "Rainfall",
  humidity: "Humidity",
  askQuestion: "Have a question about your crop?",
  speak: "Speak",
  recentInsights: "Recent Insights",
  insightNoDisease: "No disease detected in recent scan",
  insightIrrigation: "Irrigation recommended tomorrow",
  insightRain: "Rain expected tonight",

  // Disease Detection
  diseaseDetectionTitle: "Crop Disease Detection",
  diseaseDetectionSubtitle:
    "Upload a photo of your crop to identify possible diseases.",
  uploadPlantImage: "Upload Plant Image",
  dragDropText: "Drag & drop your image here",
  chooseImage: "Choose Image",
  useCamera: "Use Camera",
  analyzing: "Analyzing image...",
  disease: "Disease",
  confidence: "Confidence",
  severity: "Severity",
  treatmentRecommendation: "Treatment Recommendation",
  prevention: "Prevention",
  unableToProcess: "Unable to process image. Please try again.",
  analyzeAnother: "Analyze Another",

  // Crop Recommendation
  cropRecTitle: "Crop Recommendation",
  cropRecSubtitle:
    "Choose a dataset-backed location, season, and historical crop record.",
  cropInputHelp:
    "All model inputs are resolved from the selected historical row in the crop training dataset.",
  stateName: "State",
  districtName: "District",
  cropLocationOptionsFailed:
    "Could not load locations from the crop dataset. Check your connection and retry.",
  invalidStateDistrict:
    "Choose a state and a district listed for that state in the training data.",
  invalidCropSeason: "Choose a season category from the model's supported list.",
  locationNotModelSupported:
    "This district appears in the CSV but is not a category in the trained crop model. Choose another district.",
  locationNotModelSupportedShort: "not in crop model",
  seasonName: "Season",
  seasonSelectionHelp:
    "Choose the crop season explicitly. No verified month-to-season or location-specific planting calendar is available; Whole Year is a crop-season category, not a date-based default.",
  historicalAreaTitle: "Historical cultivated area",
  historicalAreaDescription:
    "Choose an exact crop, year, and soil record. Its recorded area and model features remain tied to that dataset row.",
  historicalAreaPrompt:
    "Select a district to view its historical cultivated-area records.",
  historicalAreaSelectSeasonPrompt:
    "Choose a season above to view matching historical cultivated-area records.",
  historicalAreaLoading: "Loading historical cultivated-area records...",
  historicalAreaUnavailable:
    "Could not load historical cultivated-area records. Check your connection and retry.",
  historicalAreaNoSeasonRecords:
    "No historical area records between 1 and 100 acres are available for this location and season.",
  historicalAreaCrop: "Crop",
  historicalAreaRecordLabel:
    "Historical cultivated area · {district} · {crop} · {season}",
  historicalAreaChooseCrop: "Choose a crop",
  historicalAreaChooseRecord: "Choose a historical area...",
  historicalYear: "Historical year",
  selectedHistoricalRecord: "Selected historical record",
  datasetSoilType: "Dataset soil type",
  datasetSoilUnavailable: "Soil type is unavailable for this record.",
  soilMismatchWarning:
    "The selected dataset soil ({datasetSoil}) differs from the image prediction ({imageSoil}). The crop model will use the dataset soil type.",
  soilModelInputNote:
    "Image classification is shown separately and does not change the selected record or the soil value used by the crop model.",
  historicalAreaRecommendationUnavailable:
    "Historical cultivated area for this crop is unavailable.",
  historicalAreaAmbiguous: "Conflicting values",
  historicalAreaMissingValue: "Not available",
  datasetSelectionHelp:
    "No weather service, geocoder, farmer-entered NPK, or available-land value is used.",
  datasetFeatureTitle: "Selected historical row's model features",
  datasetFeatureDescription:
    "The exact selected training row supplies N, P, K, temperature, humidity, rainfall, soil, year, and historical area. Nothing is averaged or substituted.",
  datasetFeatureUnavailable: "This row cannot be used for prediction:",
  datasetTemperature: "Temperature",
  datasetHumidity: "Humidity",
  datasetRainfall: "Rainfall",
  datasetNpkSource: "Dataset NPK source",
  datasetMatchingRows: "matching dataset row(s)",
  datasetRunPrediction: "Run model on selected historical record",
  datasetPredictionTitle: "Your Crop Recommendation",
  cropResultSubtitle: "Based on your selected location, season and soil.",
  datasetReferenceCrop: "Crop label recorded in the dataset",
  datasetPredictionCaveat:
    "This is a classifier output for a selected historical training record, not a validated crop recommendation. The displayed row already has a crop label, and the dataset does not document weather aggregation periods or verify every NPK source. Do not use this output alone to make farming decisions.",

  historicalNpkTitle: "Historical dataset NPK lookup",
  historicalNpkPrompt:
    "Select a state, district, and season to look up historical N, P, and K values.",
  historicalNpkLoading: "Looking up historical NPK values...",
  historicalNpkNotFound:
    "No historical NPK records match this state, district, and season.",
  historicalNpkInvalidData:
    "The NPK lookup did not return valid numeric values for the current selection. Retry the lookup before continuing.",
  historicalNpkUnavailable:
    "The historical NPK dataset is currently unavailable. Please try again later.",
  historicalNpkRequestFailed:
    "Could not retrieve historical NPK values. Check your connection and try again.",
  historicalNpkMatchedRecords: "Matched records",
  historicalNpkNotUsedForPrediction:
    "These reference lookup values are not farmer inputs. The workflow uses year-specific values internally for experimental scoring only; scores are not validated recommendations.",
  historicalRainfallTitle: "Historical dataset rainfall lookup",
  historicalRainfallPrompt:
    "Select a state, district, and season to look up the dataset-derived multi-year rainfall mean.",
  historicalRainfallLoading: "Looking up historical rainfall...",
  historicalRainfallNotFound:
    "No historical rainfall records match this exact state, district, and season.",
  historicalRainfallUnavailable:
    "The historical rainfall dataset is unavailable or contains invalid data. Please try again later.",
  historicalRainfallInvalidData:
    "The rainfall lookup returned invalid values or year metadata for the current selection.",
  historicalRainfallRequestFailed:
    "Could not retrieve historical rainfall. Check your connection and try again.",
  historicalRainfallMean: "Multi-year mean",
  historicalRainfallCoverage: "Observed coverage",
  historicalRainfallYears: "years",
  historicalRainfallRange: "year range",
  historicalRainfallUnverified:
    "This is a dataset-derived mean over years before the target year. Its compatibility with the crop model's training rainfall feature is unverified; it is used only for experimental scoring.",
  historicalWeatherTitle: "Historical seasonal weather",
  historicalWeatherPrompt:
    "Historical weather is available for state/district locations with reviewed identity and coordinate evidence. More districts can be enabled through the project's verification workflow. Choose one of the supported crop seasons.",
  historicalWeatherLoading:
    "Looking up historical temperature and humidity...",
  historicalWeatherUnsupported:
    "Historical weather is available only for verified locations. This state/district selection is not supported.",
  historicalWeatherUnavailable:
    "Historical weather data is currently unavailable for this selection. Please try again later.",
  historicalWeatherInvalidData:
    "The weather lookup returned invalid values or metadata for the current selection.",
  historicalWeatherRequestFailed:
    "Could not retrieve historical weather. Check your connection and try again.",
  historicalWeatherAverages: "Historical seasonal averages",
  historicalWeatherPeriod: "Historical period",
  historicalWeatherUnverified:
    "These are 2010–2019 ERA5 seasonal averages, not a forecast. The workflow uses them for experimental scoring, but compatibility with the crop model's training features is unverified.",
  soilForCrop: "Soil for crop",
  area: "Area",
  availableLandArea: "Total available land area (ha)",
  soilImage: "Soil image",
  soilImagePreviewOnly:
    "Upload a JPEG, PNG, or WebP image (maximum 10 MB) to classify the soil.",
  soilImagePreviewAlt: "Uploaded soil image preview",
  invalidSoilImage: "Choose a valid image file.",
  soilImageTooLarge: "The image must be 10 MB or smaller.",
  classifySoil: "Classify soil",
  classifyingSoil: "Classifying soil image...",
  predictedSoilClass: "Predicted soil class",
  soilCropLinkPending:
    "Soil classifier labels are mapped to crop-model categories, but required prediction inputs are still unavailable.",
  soilClassUnrecognized:
    "The soil classifier returned a missing or unsupported label. Classify the image again; crop prediction cannot use this result.",
  soilClassRequired:
    "Choose a supported soil category or classify a soil image before requesting a crop recommendation.",
  soilNetworkError:
    "Unable to connect to the soil classification service. Check your connection and try again.",
  soilBackendError: "Soil classification failed",
  cropIntegrationsPending: "Crop prediction compatibility review",
  cropPredictionCaveat:
    "This is an unvalidated model output, not a reliability guarantee or farming recommendation. Compatibility of some input sources with training has not been established.",
  cropAreaCompatibilityWarning:
    "Historical crop-specific area and its year are looked up automatically. Missing history blocks only that candidate; values are never guessed.",
  cropWorkflowBlocked: "A reliable crop recommendation is not available yet",
  cropWorkflowCoverage:
    "Historical area is available for {available} of {total} candidate crops; {missing} have no prior-year match and {ambiguous} have conflicting matches. The existing year-specific NPK lookup is unavailable for {npk} candidates; climate inputs are unverified for {climate}.",
  cropWorkflowAction:
    "Model scores are generated only for candidates with complete inputs. Missing historical records or features are not substituted. Scores remain experimental until climate compatibility and candidate-wise ranking are validated.",
  cropWorkflowRanking:
    "Candidate-wise scores are experimental and have not been validated for ranking. No crop prediction was returned.",
  cropWorkflowExperimentalScores: "Experimental model scores (not a ranking)",
  cropWorkflowExperimentalScoreHelp:
    "Raw model outputs only. Do not interpret as validated probabilities or use as a crop recommendation.",
  cropWorkflowScoringBlockers: "Inputs preventing candidate scoring",
  cropWorkflowRecommendationBlockers: "Why no crop recommendation is returned",
  cropWorkflowCandidateDiagnostics: "Candidate-specific historical area diagnostics",
  cropWorkflowLocationUnresolved: "location registered, coordinates unresolved",
  historicalCropAreaValue:
    "{area} acres · year {year}",
  cropWorkflowWeatherStatus:
    "Historical temperature/humidity: {status} ({values}).",
  cropWorkflowRainfallStatus:
    "Pre-target-year historical rainfall: {status} ({value}; source years {years}).",
  cropWorkflowRetrievedUnverified: "retrieved, compatibility unverified",
  cropWorkflowMissingHistory: "no prior record",
  cropWorkflowUnavailable: "unavailable",
  cropWorkflowInvalid: "invalid service response",
  experimentalModelOutput: "Experimental output — reliability not established",
  requiredCropInputs:
    "Choose a state and district.",
  soilType: "Soil Type",
  nitrogen: "Nitrogen (N)",
  phosphorus: "Phosphorus (P)",
  potassium: "Potassium (K)",
  ph: "pH Level",
  temperatureField: "Temperature (°C)",
  humidityField: "Humidity (%)",
  rainfallField: "Rainfall (mm)",
  carbonField: "Carbon (Organic)",
  recommendCrop: "Recommend Crop",
  recommendedCrop: "Recommended Crop",
  whyThisCrop: "Why this crop?",
  suitableSoil: "Suitable soil conditions",
  suitableTemp: "Suitable temperature",
  suitableRainfall: "Suitable rainfall",
  alternativeCrops: "Alternative Crops",
  computing: "Computing recommendation...",
  apiErrorTitle: "Connection Error",
  validationErrorTitle: "Request Validation Error",
  apiErrorMessage:
    "Unable to connect to the CropSense AI prediction service. Please make sure the backend is running.",
  modelNotReady:
    "The prediction model is not yet available. Please contact the administrator.",
  tryAgain: "Try Again",

  // Yield Prediction
  yieldTitle: "Crop Yield Prediction",
  yieldSubtitle:
    "Estimate yield per area from the crop, state, district, and season.",
  crop: "Crop",
  yieldState: "State",
  yieldDistrict: "District",
  yieldSeason: "Season",
  yieldPerArea: "Predicted yield per area",
  fertilizerTitle: "Fertilizer Recommendation",
  fertilizerSubtitle:
    "Enter soil, crop, and environmental details to get a fertilizer recommendation.",
  fertilizerSubmit: "Recommend Fertilizer",
  fertilizerLoading: "Preparing fertilizer recommendation...",
  fertilizerResultLabel: "Recommended fertilizer",
  fertilizerRequestFailed: "Fertilizer recommendation failed. Please try again.",
  fertilizerTemperature: "Temperature (°C)",
  fertilizerMoisture: "Moisture",
  fertilizerRainfall: "Rainfall (mm)",
  fertilizerPh: "PH",
  fertilizerNitrogen: "Nitrogen",
  fertilizerPhosphorous: "Phosphorous",
  fertilizerPotassium: "Potassium",
  fertilizerCarbon: "Carbon",
  fertilizerSoil: "Soil",
  fertilizerCrop: "Crop",
  yieldModelPeriod: "Model trained on records from 1997–2015.",
  farmArea: "Farm Area (acres)",
  fertilizerUsage: "Fertilizer Usage (kg)",
  predictYield: "Predict Yield",
  estimatedYield: "Estimated Yield",
  expectedRange: "Expected Range",
  estimatedProductivity: "Estimated Productivity",
  predicting: "Predicting yield...",

  // Irrigation
  irrigationTitle: "Smart Irrigation",
  irrigationSubtitle:
    "Get intelligent irrigation recommendations based on weather and crop needs.",
  growthStage: "Growth Stage",
  rainProbability: "Rain Probability (%)",
  expectedRainfall: "Expected Rainfall (mm)",
  checkIrrigation: "Check Irrigation",
  irrigationRecommendation: "Irrigation Recommendation",
  doNotIrrigate: "DO NOT IRRIGATE TODAY",
  irrigateToday: "IRRIGATE TODAY",
  reason: "Reason",
  nextRecommendation: "Next Recommendation",
  checking: "Checking irrigation...",

  // Weather
  weatherTitle: "Weather Insights",
  location: "Location",
  wind: "Wind",
  fiveDayForecast: "5-Day Forecast",
  temperatureAndRainfall: "Temperature & Rainfall Trend",

  // Assistant
  assistantTitle: "CropSense AI Assistant",
  assistantSubtitle:
    "Ask anything about your crop, field, weather or plant health.",
  askCropSensePlaceholder: "Ask CropSense...",
  voice: "Voice",
  uploadImage: "Upload Image",
  send: "Send",
  listening: "Listening...",
  tapToStop: "Tap to stop",
  suggestedQuestions: "Suggested Questions",
  sq1: "Why are my tomato leaves turning yellow?",
  sq2: "Which crop should I grow?",
  sq3: "Should I irrigate today?",
  sq4: "What disease is affecting my plant?",

  // Common
  loading: "Loading...",
  error: "Error",
  success: "Success",
  submit: "Submit",
  cancel: "Cancel",
  back: "Back",
  partlyCloudy: "Partly Cloudy",
  sunny: "Sunny",
  rainy: "Rainy",

  // Soil types (must match trained XGBoost model categories)
  soilAcidic: "Acidic",
  soilAlkaline: "Alkaline",
  soilLoamy: "Loamy",
  soilNeutral: "Neutral",
  soilPeaty: "Peaty",
  soilClay: "Clay",
  soilSandy: "Sandy",
  soilBlack: "Black",
  soilRed: "Red",

  // Growth stages
  stageSeedling: "Seedling",
  stageVegetative: "Vegetative",
  stageFlowering: "Flowering",
  stageFruiting: "Fruiting",
  stageHarvest: "Harvest",

  // Footer
  footerText: "© 2026 CropSense AI. Built for smarter farming.",
};

export type Translations = typeof en;
