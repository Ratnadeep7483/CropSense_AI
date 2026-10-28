import { Bell, Menu, User, Sprout } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import { Link } from "react-router-dom";

interface NavbarProps {
  onMenuToggle?: () => void;
  showMenu?: boolean;
}

export default function Navbar({ onMenuToggle, showMenu = true }: NavbarProps) {
  const { language, setLanguage, t } = useLanguage();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-surface-200 bg-white/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 md:px-6">
        {/* Left */}
        <div className="flex items-center gap-3">
          {showMenu && (
            <button
              onClick={onMenuToggle}
              className="rounded-lg p-2 text-surface-600 hover:bg-surface-100 lg:hidden"
              aria-label="Toggle menu"
            >
              <Menu className="h-5 w-5" />
            </button>
          )}
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white">
              <Sprout className="h-5 w-5" />
            </div>
            <span className="text-lg font-semibold text-surface-900">
              {t.appName}
            </span>
          </Link>
        </div>

        {/* Right */}
        <div className="flex items-center gap-2">
          {/* Language Switcher */}
          <button
            onClick={() => setLanguage(language === "en" ? "hi" : "en")}
            className="rounded-lg border border-surface-200 px-3 py-1.5 text-sm font-medium text-surface-700 transition-colors hover:bg-surface-100"
          >
            {language === "en" ? "हिंदी" : "English"}
          </button>

          {/* Notifications */}
          <button
            className="relative rounded-lg p-2 text-surface-600 transition-colors hover:bg-surface-100"
            aria-label={t.notifications}
          >
            <Bell className="h-5 w-5" />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-primary-500" />
          </button>

          {/* Profile */}
          <button
            className="rounded-lg p-2 text-surface-600 transition-colors hover:bg-surface-100"
            aria-label={t.profile}
          >
            <User className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
