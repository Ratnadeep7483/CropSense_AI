import {
  CloudSun,
  Droplets,
  Wind,
  Thermometer,
  MapPin,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useLanguage } from "../contexts/LanguageContext";
import {
  mockCurrentWeather,
  mockForecast,
  mockWeatherChart,
} from "../data/mockData";

export default function Weather() {
  const { t } = useLanguage();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
          {t.weatherTitle}
        </h1>
        <div className="mt-1 flex items-center gap-1.5 text-surface-500">
          <MapPin className="h-4 w-4" />
          <span>{mockCurrentWeather.location}</span>
        </div>
      </div>

      {/* Current Weather Card */}
      <div className="rounded-2xl border border-surface-100 bg-gradient-to-br from-amber-50 via-white to-blue-50 p-8 shadow-sm">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
          <div className="text-center sm:text-left">
            <div className="mb-1 text-6xl">⛅</div>
          </div>
          <div className="flex-1 text-center sm:text-left">
            <p className="text-5xl font-bold text-surface-900">
              {mockCurrentWeather.temperature}°C
            </p>
            <p className="mt-1 text-lg text-surface-600">{t.partlyCloudy}</p>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-1 md:grid-cols-2">
            <div className="flex items-center gap-2.5 rounded-xl bg-white/70 px-4 py-3 backdrop-blur">
              <Droplets className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-xs text-surface-500">{t.humidity}</p>
                <p className="text-sm font-semibold text-surface-800">
                  {mockCurrentWeather.humidity}%
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2.5 rounded-xl bg-white/70 px-4 py-3 backdrop-blur">
              <CloudSun className="h-5 w-5 text-amber-500" />
              <div>
                <p className="text-xs text-surface-500">{t.rainfall}</p>
                <p className="text-sm font-semibold text-surface-800">
                  {mockCurrentWeather.rainfall} mm
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2.5 rounded-xl bg-white/70 px-4 py-3 backdrop-blur">
              <Wind className="h-5 w-5 text-cyan-500" />
              <div>
                <p className="text-xs text-surface-500">{t.wind}</p>
                <p className="text-sm font-semibold text-surface-800">
                  {mockCurrentWeather.wind} km/h
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2.5 rounded-xl bg-white/70 px-4 py-3 backdrop-blur">
              <Thermometer className="h-5 w-5 text-red-400" />
              <div>
                <p className="text-xs text-surface-500">{t.temperature}</p>
                <p className="text-sm font-semibold text-surface-800">
                  {mockCurrentWeather.temperature}°C
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 5-Day Forecast */}
      <div className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-surface-900">
          {t.fiveDayForecast}
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
          {mockForecast.map((day) => (
            <div
              key={day.day}
              className="flex flex-col items-center rounded-xl border border-surface-100 bg-surface-50 p-4 transition-all hover:shadow-sm hover:-translate-y-0.5"
            >
              <p className="mb-1 text-sm font-medium text-surface-700">
                {day.day}
              </p>
              <span className="mb-1 text-3xl">{day.icon}</span>
              <p className="text-lg font-bold text-surface-900">
                {day.tempHigh}°C
              </p>
              {day.rainfall > 0 && (
                <p className="mt-1 flex items-center gap-1 text-xs text-blue-500">
                  <Droplets className="h-3 w-3" />
                  {day.rainfall} mm
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Temperature & Rainfall Chart */}
      <div className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-surface-900">
          {t.temperatureAndRainfall}
        </h2>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={mockWeatherChart}>
            <defs>
              <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="rainGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
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
            <Area
              type="monotone"
              dataKey="temp"
              name={t.temperature}
              stroke="#f59e0b"
              strokeWidth={2.5}
              fill="url(#tempGrad)"
            />
            <Area
              type="monotone"
              dataKey="rainfall"
              name={t.rainfall}
              stroke="#3b82f6"
              strokeWidth={2.5}
              fill="url(#rainGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
