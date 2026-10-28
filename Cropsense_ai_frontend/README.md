# 🌱 CropSense AI — Smart Farming Powered by AI

**Phase 0 Frontend Prototype** — A professional, responsive frontend for an integrated smart agriculture platform.

CropSense AI helps farmers understand crop health, make better crop decisions, manage irrigation, and access agricultural guidance in Hindi and English.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌾 **Crop Recommendation** | AI-powered crop suggestions based on soil and climate conditions |
| 🔬 **Disease Detection** | Upload crop photos to identify diseases with treatment advice |
| 📈 **Yield Prediction** | Estimate crop production from farm and environmental data |
| 💧 **Smart Irrigation** | Intelligent irrigation recommendations based on weather and crop needs |
| ☁️ **Weather Insights** | Real-time weather data and 5-day forecasts |
| 🤖 **AI Assistant** | Ask farming questions in Hindi or English — text or voice |
| 🌐 **Bilingual UI** | Full Hindi/English language switching |

---

## 🛠 Tech Stack

- **React 19** + **TypeScript**
- **Vite** (build tool)
- **Tailwind CSS v4**
- **Lucide React** (icons)
- **Recharts** (charts & graphs)
- **React Router** (routing)

---

## 📁 Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── Navbar.tsx
│   ├── Sidebar.tsx
│   ├── disease/          # Disease detection components
│   │   ├── ImageUploader.tsx
│   │   ├── ImagePreview.tsx
│   │   └── DiseaseResult.tsx
│   └── assistant/        # Chat assistant components
│       ├── ChatWindow.tsx
│       ├── ChatMessage.tsx
│       ├── ChatInput.tsx
│       ├── VoiceButton.tsx
│       └── SuggestedQuestions.tsx
├── contexts/
│   └── LanguageContext.tsx    # Hindi/English language switching
├── data/
│   └── mockData.ts           # Mock data (swap with real API later)
├── i18n/
│   ├── en.ts                 # English translations
│   └── hi.ts                 # Hindi translations
├── layouts/
│   ├── PublicLayout.tsx       # Landing page layout
│   └── DashboardLayout.tsx   # Dashboard layout with sidebar
├── pages/
│   ├── Landing.tsx
│   ├── Dashboard.tsx
│   ├── DiseaseDetection.tsx
│   ├── CropRecommendation.tsx
│   ├── YieldPrediction.tsx
│   ├── Irrigation.tsx
│   ├── Weather.tsx
│   └── Assistant.tsx
├── lib/
│   └── utils.ts              # Utility functions
├── App.tsx                    # Router setup
├── main.tsx                   # Entry point
└── index.css                  # Global styles
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm 9+

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Cropsense_ai_frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173/`

### Build for Production

```bash
npm run build
npm run preview
```

---

## 📱 Pages & Routes

| Route | Page |
|-------|------|
| `/` | Landing page |
| `/dashboard` | Main dashboard |
| `/disease-detection` | Crop disease detection (image upload) |
| `/crop-recommendation` | Crop recommendation (form input) |
| `/yield-prediction` | Yield prediction (form input) |
| `/irrigation` | Smart irrigation recommendation |
| `/weather` | Weather insights & forecast |
| `/assistant` | AI agriculture chatbot |

---

## 🌐 Language Support

The UI supports full **English ↔ Hindi** switching via the language toggle in the navbar. All text is sourced from translation files (`src/i18n/en.ts` and `src/i18n/hi.ts`) — no hard-coded strings.

---

## 🏗 Architecture — Future Backend Integration

This Phase 0 prototype uses mock data from `src/data/mockData.ts`. The architecture is designed so that real AI/backend services can replace mock data without redesigning the UI:

```
Phase 0:  Frontend → Mock Data
Phase 1:  Frontend → Backend API → AI Models
```

All mock data uses typed interfaces, making the swap to real API responses straightforward.

---

## 📝 Notes

- This is a **frontend-only** prototype — no backend, database, or real AI models
- Smart Irrigation uses farmer-entered data, not IoT/sensors
- The AI Assistant chat uses pre-defined mock responses
- Voice button shows UI state only (no actual speech recognition)

---

## 📄 License

Built for academic demonstration purposes.

© 2026 CropSense AI
