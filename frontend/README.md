# Asterion Frontend

The user interface for the Asterion platform, built on React, TypeScript, and Vite. It provides a visual interface for managing cases, configuring scenarios, running scientific pipelines, visualizing results on Leaflet maps, and auditing evidence logs.

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- npm or yarn

### Installation
1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Build for production:
   ```bash
   npm run build
   ```

---

## 📂 Project Structure

```
frontend/
├── public/                # Static assets
└── src/
    ├── components/        # Reusable UI components
    │   ├── cases/         # Case details tables & cards
    │   ├── confidence/    # Confidence level score cards
    │   ├── evidence/      # Audit trails & verification cards
    │   ├── layout/        # Header, Sidebar, page wrappers
    │   ├── localization/  # Signal-strength & NLLS result details
    │   ├── map/           # Leaflet map visualizations
    │   ├── pipeline/      # Orchestrated pipeline stepper & progress indicators
    │   ├── scenarios/     # Scenario configurators & tables
    │   ├── ui/            # UI primitives (Buttons, Badges, Modals, Pagination)
    │   └── validation/    # Signal bounds audit & checklist cards
    ├── hooks/             # Custom React Hooks & API queries
    │   ├── useCases.ts    # React Query hooks for case management
    │   └── useScenarios.ts # React Query hooks for scenarios configurator
    ├── lib/               # Utilities & Third-party integrations
    │   ├── api.ts         # Axios configuration & interceptors
    │   └── cn.ts          # Tailwind Class merger (clsx + tailwind-merge)
    ├── pages/             # View router page wrappers
    │   ├── CaseDetails.tsx
    │   ├── Cases.tsx
    │   ├── Dashboard.tsx
    │   ├── EvidenceExplorer.tsx
    │   ├── ImportPage.tsx
    │   ├── InvestigationDashboard.tsx
    │   ├── Scenarios.tsx
    │   └── Settings.tsx
    ├── stores/            # Zustand stores for state management
    │   ├── confidenceStore.ts
    │   ├── evidenceStore.ts
    │   ├── localizationStore.ts
    │   ├── pipelineCoordinator.ts # End-to-end pipeline orchestrator
    │   ├── simulationStore.ts
    │   ├── trackingStore.ts
    │   └── validationStore.ts
    ├── types/             # TypeScript types
    │   ├── case.ts
    │   ├── scenario.ts
    │   └── scientific.ts  # Types matching Backend schemas
    ├── App.tsx            # Routes configurations
    ├── index.css          # Styling (Tailwind + CSS Custom Properties)
    └── main.tsx           # Entry point
```

---

## 🛠️ Tech Stack

- **Framework**: React 19 (via Vite)
- **Styling**: Tailwind CSS v4, Lucide React (Icons)
- **State Management**: Zustand (stores for async pipeline steps & global state)
- **Data Fetching**: Axios + TanStack React Query (server-state synchronization)
- **Maps**: Leaflet + React Leaflet (travel path visualization, tower confidence ellipses)
- **Routing**: React Router DOM v7
- **Code Quality**: Oxlint (fast linting), TypeScript (strict type checks)
