import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Wheat,
  Bug,
  TrendingUp,
  Droplets,
  CloudSun,
  Bot,
  Sprout,
  X,
} from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const { t } = useLanguage();

  const navSections = [
    {
      title: t.sectionMain,
      items: [
        { to: "/dashboard", icon: LayoutDashboard, label: t.dashboard },
      ],
    },
    {
      title: t.sectionAiTools,
      items: [
        { to: "/crop-recommendation", icon: Wheat, label: t.cropRecommendation },
        {
          to: "/fertilizer-recommendation",
          icon: Sprout,
          label: t.fertilizerRecommendation,
        },
        { to: "/disease-detection", icon: Bug, label: t.diseaseDetection },
        { to: "/yield-prediction", icon: TrendingUp, label: t.yieldPrediction },
        { to: "/irrigation", icon: Droplets, label: t.smartIrrigation },
      ],
    },
    {
      title: t.sectionInformation,
      items: [
        { to: "/weather", icon: CloudSun, label: t.weather },
        { to: "/assistant", icon: Bot, label: t.aiAssistant },
      ],
    },
  ];

  const sidebarContent = (
    <nav className="flex h-full flex-col">
      {/* Logo area for mobile */}
      <div className="flex items-center justify-between border-b border-surface-200 px-4 py-4 lg:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white">
            <Sprout className="h-5 w-5" />
          </div>
          <span className="text-lg font-semibold text-surface-900">
            {t.appName}
          </span>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-surface-500 hover:bg-surface-100"
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Nav links */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        {navSections.map((section) => (
          <div key={section.title} className="mb-6">
            <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-surface-400">
              {section.title}
            </p>
            <ul className="space-y-1">
              {section.items.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-primary-50 text-primary-700"
                          : "text-surface-600 hover:bg-surface-100 hover:text-surface-900"
                      }`
                    }
                  >
                    <item.icon className="h-5 w-5 shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </nav>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:top-16 lg:z-30 lg:flex lg:w-60 lg:flex-col border-r border-surface-200 bg-white">
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm"
            onClick={onClose}
          />
          <aside className="fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-xl animate-slide-in">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
