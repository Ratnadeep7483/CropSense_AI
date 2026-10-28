import { Link } from "react-router-dom";
import {
  Wheat,
  Bug,
  TrendingUp,
  Droplets,
  CloudSun,
  Bot,
  ArrowRight,
  Sprout,
  ClipboardList,
  Lightbulb,
  BarChart3,
} from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";

export default function Landing() {
  const { t } = useLanguage();

  const features = [
    {
      icon: Wheat,
      title: t.featCropRec,
      desc: t.featCropRecDesc,
      color: "bg-primary-50 text-primary-600",
    },
    {
      icon: Bug,
      title: t.featDisease,
      desc: t.featDiseaseDesc,
      color: "bg-red-50 text-red-600",
    },
    {
      icon: TrendingUp,
      title: t.featYield,
      desc: t.featYieldDesc,
      color: "bg-blue-50 text-blue-600",
    },
    {
      icon: Droplets,
      title: t.featIrrigation,
      desc: t.featIrrigationDesc,
      color: "bg-cyan-50 text-cyan-600",
    },
    {
      icon: CloudSun,
      title: t.featWeather,
      desc: t.featWeatherDesc,
      color: "bg-amber-50 text-amber-600",
    },
    {
      icon: Bot,
      title: t.featAssistant,
      desc: t.featAssistantDesc,
      color: "bg-purple-50 text-purple-600",
    },
  ];

  const steps = [
    {
      icon: ClipboardList,
      title: t.howStep1Title,
      desc: t.howStep1Desc,
      step: "01",
    },
    {
      icon: Lightbulb,
      title: t.howStep2Title,
      desc: t.howStep2Desc,
      step: "02",
    },
    {
      icon: BarChart3,
      title: t.howStep3Title,
      desc: t.howStep3Desc,
      step: "03",
    },
  ];

  return (
    <div className="overflow-hidden">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary-50 via-white to-primary-50">
        {/* Decorative background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-primary-100/50 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-primary-100/40 blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-6xl px-4 py-20 md:px-6 md:py-28 lg:py-36">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            {/* Text */}
            <div className="max-w-xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-primary-100 px-4 py-1.5 text-sm font-medium text-primary-700">
                <Sprout className="h-4 w-4" />
                {t.appTagline}
              </div>
              <h1 className="mb-6 text-4xl font-bold leading-tight text-surface-900 md:text-5xl lg:text-6xl">
                {t.heroHeadline}
              </h1>
              <p className="mb-8 text-lg leading-relaxed text-surface-600">
                {t.heroSubtext}
              </p>
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary-600/25 transition-all hover:bg-primary-700 hover:shadow-xl hover:shadow-primary-600/30 hover:-translate-y-0.5"
                >
                  {t.getStarted}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/assistant"
                  className="inline-flex items-center gap-2 rounded-xl border border-surface-200 bg-white px-6 py-3 text-sm font-semibold text-surface-700 shadow-sm transition-all hover:bg-surface-50 hover:border-surface-300 hover:-translate-y-0.5"
                >
                  <Bot className="h-4 w-4" />
                  {t.askCropSense}
                </Link>
              </div>
            </div>

            {/* Hero Visual */}
            <div className="relative hidden lg:block">
              <div className="relative rounded-2xl bg-gradient-to-br from-primary-100 to-primary-200 p-8 shadow-2xl">
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-xl bg-white/90 p-4 shadow-sm backdrop-blur">
                    <div className="mb-2 text-2xl">🌾</div>
                    <p className="text-sm font-semibold text-surface-800">
                      {t.featCropRec}
                    </p>
                    <p className="mt-1 text-xs text-surface-500">
                      92% {t.suitability}
                    </p>
                  </div>
                  <div className="rounded-xl bg-white/90 p-4 shadow-sm backdrop-blur">
                    <div className="mb-2 text-2xl">🔬</div>
                    <p className="text-sm font-semibold text-surface-800">
                      {t.featDisease}
                    </p>
                    <p className="mt-1 text-xs text-primary-600">
                      ✓ {t.healthy}
                    </p>
                  </div>
                  <div className="rounded-xl bg-white/90 p-4 shadow-sm backdrop-blur">
                    <div className="mb-2 text-2xl">💧</div>
                    <p className="text-sm font-semibold text-surface-800">
                      {t.featIrrigation}
                    </p>
                    <p className="mt-1 text-xs text-surface-500">
                      {t.tomorrow} 6:00 AM
                    </p>
                  </div>
                  <div className="rounded-xl bg-white/90 p-4 shadow-sm backdrop-blur">
                    <div className="mb-2 text-2xl">☁️</div>
                    <p className="text-sm font-semibold text-surface-800">
                      {t.featWeather}
                    </p>
                    <p className="mt-1 text-xs text-surface-500">
                      28°C {t.partlyCloudy}
                    </p>
                  </div>
                </div>
                {/* Decorative plant accent */}
                <div className="absolute -top-6 -right-6 text-5xl opacity-60">
                  🌿
                </div>
                <div className="absolute -bottom-4 -left-4 text-4xl opacity-40">
                  🌱
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-6xl px-4 md:px-6">
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold text-surface-900">
              {t.appName}
            </h2>
            <p className="mx-auto max-w-2xl text-surface-500">
              {t.appTagline}
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className="group rounded-2xl border border-surface-100 bg-white p-6 shadow-sm transition-all hover:shadow-md hover:-translate-y-1"
              >
                <div
                  className={`mb-4 inline-flex rounded-xl p-3 ${f.color}`}
                >
                  <f.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-surface-900">
                  {f.title}
                </h3>
                <p className="text-sm leading-relaxed text-surface-500">
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="bg-surface-50 py-20">
        <div className="mx-auto max-w-6xl px-4 md:px-6">
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold text-surface-900">
              {t.howItHelps}
            </h2>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {steps.map((s) => (
              <div
                key={s.step}
                className="relative rounded-2xl bg-white p-8 shadow-sm"
              >
                <span className="mb-4 block text-4xl font-black text-primary-100">
                  {s.step}
                </span>
                <div className="mb-3 inline-flex rounded-lg bg-primary-50 p-2.5 text-primary-600">
                  <s.icon className="h-5 w-5" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-surface-900">
                  {s.title}
                </h3>
                <p className="text-sm leading-relaxed text-surface-500">
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-700 py-16">
        <div className="mx-auto max-w-4xl px-4 text-center md:px-6">
          <h2 className="mb-4 text-3xl font-bold text-white">
            {t.heroHeadline}
          </h2>
          <p className="mb-8 text-primary-100">
            {t.heroSubtext}
          </p>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-sm font-semibold text-primary-700 shadow-lg transition-all hover:bg-primary-50 hover:-translate-y-0.5"
          >
            {t.getStarted}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-surface-200 bg-white py-8">
        <div className="mx-auto max-w-6xl px-4 text-center md:px-6">
          <div className="flex items-center justify-center gap-2 text-surface-400">
            <Sprout className="h-4 w-4 text-primary-500" />
            <span className="text-sm">{t.footerText}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
