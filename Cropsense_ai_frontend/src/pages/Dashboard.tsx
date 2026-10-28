import { Link } from "react-router-dom";
import {
  CloudSun,
  ShieldCheck,
  Droplets,
  Wheat,
  Mic,
  Bot,
  CheckCircle2,
  CloudRain,
  ArrowRight,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useLanguage } from "../contexts/LanguageContext";
import { translateCropName } from "../lib/cropNameTranslation.mjs";
import {
  mockCurrentWeather,
  mockWeatherChart,
  mockCropRecommendation,
} from "../data/mockData";

export default function Dashboard() {
  const { t, language } = useLanguage();
  const recommendedCropName = translateCropName(
    mockCropRecommendation.name,
    language,
  );

  const summaryCards = [
    {
      icon: CloudSun,
      label: t.weatherLabel,
      value: `${mockCurrentWeather.temperature}°C`,
      sub: t.partlyCloudy,
      detail: `${t.humidity}: ${mockCurrentWeather.humidity}%`,
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
    {
      icon: ShieldCheck,
      label: t.cropHealthLabel,
      value: t.healthy,
      sub: t.noDiseaseDetected,
      detail: "",
      color: "text-primary-600",
      bg: "bg-primary-50",
    },
    {
      icon: Droplets,
      label: t.irrigationLabel,
      value: t.tomorrow,
      sub: "6:00 AM",
      detail: "",
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      icon: Wheat,
      label: t.recommendedCropLabel,
      value: mockCropRecommendation.emoji + " " + recommendedCropName,
      sub: `${t.suitability}: ${mockCropRecommendation.suitability}%`,
      detail: "",
      color: "text-emerald-600",
      bg: "bg-emerald-50",
    },
  ];

  const insights = [
    { icon: CheckCircle2, text: t.insightNoDisease, color: "text-primary-500" },
    { icon: Droplets, text: t.insightIrrigation, color: "text-blue-500" },
    { icon: CloudRain, text: t.insightRain, color: "text-amber-500" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
          {t.greeting}
        </h1>
        <p className="mt-1 text-surface-500">{t.dashboardSubtitle}</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryCards.map((card) => (
          <div
            key={card.label}
            className="rounded-2xl border border-surface-100 bg-white p-5 shadow-sm transition-all hover:shadow-md hover:-translate-y-0.5"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-surface-500">
                  {card.label}
                </p>
                <p className="mt-1 text-xl font-bold text-surface-900">
                  {card.value}
                </p>
                <p className="mt-0.5 text-sm text-surface-400">{card.sub}</p>
                {card.detail && (
                  <p className="mt-0.5 text-xs text-surface-400">
                    {card.detail}
                  </p>
                )}
              </div>
              <div className={`rounded-xl p-2.5 ${card.bg}`}>
                <card.icon className={`h-5 w-5 ${card.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Middle Row: Crop Recommendation + Weather Chart */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Crop Recommendation Card */}
        <div className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="mb-4 text-lg font-semibold text-surface-900">
            {t.recommendedCrop}
          </h2>
          <div className="mb-4 text-center">
            <span className="text-5xl">{mockCropRecommendation.emoji}</span>
            <p className="mt-2 text-xl font-bold text-surface-900">
              {recommendedCropName}
            </p>
            <div className="mx-auto mt-2 flex items-center justify-center gap-2">
              <div className="h-2 flex-1 max-w-32 rounded-full bg-surface-100">
                <div
                  className="h-2 rounded-full bg-primary-500 transition-all duration-1000"
                  style={{
                    width: `${mockCropRecommendation.suitability}%`,
                  }}
                />
              </div>
              <span className="text-sm font-semibold text-primary-600">
                {mockCropRecommendation.suitability}%
              </span>
            </div>
          </div>
          <ul className="mb-4 space-y-2">
            {mockCropRecommendation.reasons.map((r) => (
              <li
                key={r}
                className="flex items-center gap-2 text-sm text-surface-600"
              >
                <CheckCircle2 className="h-4 w-4 shrink-0 text-primary-500" />
                {r}
              </li>
            ))}
          </ul>
          <Link
            to="/crop-recommendation"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:text-primary-700"
          >
            {t.viewRecommendation}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Weather Forecast Chart */}
        <div className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm lg:col-span-3">
          <h2 className="mb-4 text-lg font-semibold text-surface-900">
            {t.weatherForecast}
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={mockWeatherChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
              <XAxis
                dataKey="day"
                tick={{ fontSize: 12, fill: "#78716c" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 12, fill: "#78716c" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: "12px",
                  border: "1px solid #e7e5e4",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.05)",
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="temp"
                name={t.temperature}
                stroke="#f59e0b"
                strokeWidth={2.5}
                dot={{ r: 4, fill: "#f59e0b" }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="rainfall"
                name={t.rainfall}
                stroke="#3b82f6"
                strokeWidth={2.5}
                dot={{ r: 4, fill: "#3b82f6" }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Row: AI Assistant + Recent Insights */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* AI Assistant Card */}
        <div className="rounded-2xl border border-primary-100 bg-gradient-to-br from-primary-50 to-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-xl bg-primary-100 p-2.5">
              <Bot className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-surface-900">
                {t.aiAssistant}
              </h2>
              <p className="text-sm text-surface-500">{t.askQuestion}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/assistant"
              className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-primary-700 hover:-translate-y-0.5"
            >
              <Bot className="h-4 w-4" />
              {t.askCropSense}
            </Link>
            <Link
              to="/assistant"
              className="inline-flex items-center gap-2 rounded-xl border border-surface-200 bg-white px-5 py-2.5 text-sm font-semibold text-surface-700 shadow-sm transition-all hover:bg-surface-50 hover:-translate-y-0.5"
            >
              <Mic className="h-4 w-4" />
              {t.speak}
            </Link>
          </div>
        </div>

        {/* Recent Insights */}
        <div className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-surface-900">
            {t.recentInsights}
          </h2>
          <ul className="space-y-3">
            {insights.map((item, i) => (
              <li
                key={i}
                className="flex items-center gap-3 rounded-xl bg-surface-50 p-3.5"
              >
                <item.icon className={`h-5 w-5 shrink-0 ${item.color}`} />
                <span className="text-sm text-surface-700">{item.text}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
