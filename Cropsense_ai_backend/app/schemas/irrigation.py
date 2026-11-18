from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


IrrigationSoil = Literal["Clay", "Loamy", "Sandy", "Silt"]
IrrigationCrop = Literal["Cotton", "Maize", "Potato", "Rice", "Sugarcane", "Wheat"]
IrrigationGrowthStage = Literal["Flowering", "Harvest", "Sowing", "Vegetative"]
IrrigationSeason = Literal["Kharif", "Rabi", "Zaid"]
IrrigationMulching = Literal["Yes", "No"]
IrrigationPrediction = Literal["High", "Low", "Medium"]


class IrrigationPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Temperature_C: float
    Humidity: float
    Rainfall_mm: float
    Sunlight_Hours: float
    Soil_Type: IrrigationSoil
    Crop_Type: IrrigationCrop
    Crop_Growth_Stage: IrrigationGrowthStage
    Season: IrrigationSeason
    Soil_Moisture: float
    Wind_Speed_kmh: float
    Mulching_Used: IrrigationMulching


class IrrigationWeatherPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: str = Field(min_length=1)
    district: str = Field(min_length=1)
    Soil_Moisture: float
    Soil_Type: IrrigationSoil
    Crop_Type: IrrigationCrop
    Crop_Growth_Stage: IrrigationGrowthStage
    Season: IrrigationSeason
    Mulching_Used: IrrigationMulching


class IrrigationWeatherMeasurement(BaseModel):
    date: str
    timezone: str
    period: str
    source: str
    provider: Literal["archive", "forecast"]
    source_variables: dict[str, str] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    not_mapped: list[str] = Field(default_factory=list)


class IrrigationWeatherResponse(BaseModel):
    Temperature_C: float
    Humidity: float
    Rainfall_mm: float
    Sunlight_Hours: float
    Wind_Speed_kmh: float
    measurement: IrrigationWeatherMeasurement


class IrrigationPredictionResponse(BaseModel):
    success: bool = True
    prediction: IrrigationPrediction
    probabilities: dict[IrrigationPrediction, float]
    weather: IrrigationWeatherResponse | None = None
