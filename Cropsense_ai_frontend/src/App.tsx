import { Routes, Route } from "react-router-dom";
import PublicLayout from "./layouts/PublicLayout";
import DashboardLayout from "./layouts/DashboardLayout";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import DiseaseDetection from "./pages/DiseaseDetection";
import CropRecommendation from "./pages/CropRecommendation";
import FertilizerRecommendation from "./pages/FertilizerRecommendation";
import YieldPrediction from "./pages/YieldPrediction";
import Irrigation from "./pages/Irrigation";
import Weather from "./pages/Weather";
import Assistant from "./pages/Assistant";

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Landing />} />
      </Route>
      <Route element={<DashboardLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/disease-detection" element={<DiseaseDetection />} />
        <Route path="/crop-recommendation" element={<CropRecommendation />} />
        <Route
          path="/fertilizer-recommendation"
          element={<FertilizerRecommendation />}
        />
        <Route path="/yield-prediction" element={<YieldPrediction />} />
        <Route path="/irrigation" element={<Irrigation />} />
        <Route path="/weather" element={<Weather />} />
        <Route path="/assistant" element={<Assistant />} />
      </Route>
    </Routes>
  );
}
