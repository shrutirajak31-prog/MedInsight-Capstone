# MedInsight UI Concept Showcase — Implementation Plan

## Product scope

Build a responsive, interactive frontend concept showcase for **MedInsight — AI Medical Report Simplifier: Turning Complex Reports into Clear Health Insights.** The first deliverable is comparison-ready UI, not a production medical-analysis backend. All report, trend, evidence, and account content is clearly labeled as demonstration data until the user's existing Python/FastAPI services are connected.

The source design exploration covered three concepts, but the implemented primary experience now focuses directly on Neon Clinical Glass rather than showing a concept-comparison section in the main workflow:

1. **Neon Clinical Glass** — dark midnight-navy glass laboratory with restrained cyan/electric-blue glow and a floating AI medical orb.
2. **Pearl White + Aurora Glass** — light pearl healthcare product with translucent white cards, ice-blue gradients and mint accents.
3. **Holographic Medical Intelligence** — deep navy/indigo intelligence workspace with holographic cyan/teal layers, document-to-data visualisation and knowledge graph.

The user can switch concept, light/dark appearance, and Patient/Doctor mode without losing the current demo context. The concept switch changes the full visual identity, not only the colors.

## Design direction

### Candidate styles

- **Neon Clinical Glass** — premium dark glassmorphism medical AI lab; probability 0.07.
- **Pearl White + Aurora Glass** — high-trust light-mode healthcare intelligence product; probability 0.08.
- **Holographic Medical Intelligence** — immersive research-grade evidence workspace; probability 0.06.

### Chosen showcase anchor

Use **Neon Clinical Glass** as the selected primary direction because it best balances premium medical trust, futuristic AI identity, and strong capstone presentation impact. The Pearl White + Aurora Glass and Holographic Medical Intelligence concepts remain fully selectable and structurally distinct for comparison.

- **Design Movement:** editorial sci-fi instrumentation blended with calm clinical software.
- **Core Principles:** evidence before decoration; one clear reading path; technical depth in expandable layers; restrained motion that rewards exploration.
- **Color Philosophy:** deep navy and indigo provide trust and focus, while cyan/teal marks active evidence connections and emerald indicates reassuring states. Red/orange remain reserved for clinically meaningful status labels.
- **Layout Paradigm:** asymmetric command-center composition: a persistent left rail, wide report canvas, and a right-side evidence column rather than a centered card grid.
- **Signature Elements:** document-to-structured-data transformation visual; glowing relationship lines between finding/evidence/explanation; compact status pills with text labels and icons.
- **Interaction Philosophy:** progressive disclosure. A user sees the plain-language takeaway first, then expands math proof, limitations, evidence, and original context.
- **Animation:** 180–400ms transitions, soft orbital movement in the hero visual, staged processing progress, hover highlighting for evidence connections, and `prefers-reduced-motion` fallbacks.
- **Typography System:** Plus Jakarta Sans for interface text and headings; IBM Plex Mono for numerical values, evidence metadata, and technical pipeline labels. Use strong numeric hierarchy without sacrificing patient readability.
- **Brand Essence:** an explainable medical report companion for patients, doctors, and capstone reviewers; precise, calm, transparent.
- **Brand Voice:** plain language first, technical detail on demand. Example lines: “See what changed, not just what was flagged.” / “This explanation is grounded in the report and the cited evidence.”
- **Wordmark & Logo:** a minimal medical cross formed from two interlocking brackets, suggesting both a clinical check and a data pipeline; paired with a custom “MedInsight” wordmark treatment.
- **Signature Brand Color:** evidence cyan `#63E6FF`, used only for active links, graph nodes, focus states, and the primary CTA.

## Application architecture

Use a small React + TypeScript + Vite frontend with reusable components and local demo state. Keep backend boundaries explicit so the demo can later be replaced with FastAPI calls.

### Planned source structure

```text
app.config.ts                 # project logo metadata
package.json                  # Vite/React scripts and pinned dependencies
index.html
public/
  manus-routes.json           # route manifest
src/
  main.tsx                    # app bootstrap
  App.tsx                     # concept shell, mode state, demo routing
  styles.css                  # design tokens, theme layers, responsive rules
  data/demoData.ts            # clearly labeled mock report/account/evidence data
  components/
    BrandMark.tsx
    ConceptSwitcher.tsx
    ThemeToggle.tsx
    RoleToggle.tsx
    SidebarNav.tsx
    HeroVisual.tsx
    UploadWorkspace.tsx
    ProcessingPipeline.tsx
    ReportSummary.tsx
    LabResultsTable.tsx
    XaiReportPreview.tsx
    FindingCard.tsx
    TrendChart.tsx
    EvidenceExplorer.tsx
    KnowledgeGraph.tsx
    QaWidget.tsx
    AccountHistory.tsx
    DoctorReview.tsx
    MethodologySection.tsx
    DisclaimerBanner.tsx
    Toast.tsx
  lib/
    formatters.ts
    browserSpeech.ts
```

### Main interaction state

- `activeConcept`: `neon | pearl | holo`
- `themeMode`: `light | dark`; the default is concept-aware, but the user can override it.
- `roleMode`: `patient | doctor`
- `activeSection`: `overview | upload | analysis | trends | evidence | qa | methodology`
- `uploadState`: `empty | processing | success | error`; the UI never claims real processing.
- `expandedFindingId`, `selectedEvidenceId`, `selectedPatientId`, `locale`
- `qaMessages` and `isListening` for the local chat/microphone affordance.

### Screens/sections in the first build

1. **Concept gallery / home dashboard:** concept switcher, hero, CTAs, three feature cards, four-step workflow, trust/source strip.
2. **Upload workspace:** drag/drop and browse interaction, supported formats, selected file preview, pipeline stages, simulated success/error controls.
3. **Analysis dashboard:** patient/doctor wording toggle, summary, lab table, smart status badges, XAI bounding-box report preview, expandable findings, report-context action.
4. **Longitudinal trends:** historical LDL/hemoglobin sample chart, smart alert, report history cards, profile/account context.
5. **Evidence/RAG explorer:** source cards, exact math proof, limitation, source link placeholder only when marked demo, evidence graph, relevance label explicitly described as retrieval relevance rather than medical certainty.
6. **Q&A assistant:** suggested prompts, grounded demo answer, insufficient-evidence state, glossary tooltip, browser voice-to-text affordance, non-diagnostic disclaimer.
7. **Patient/Doctor workspace:** patient saved uploads and trends; doctor patient records, pattern view, and explanation review controls (`Correct`, `Needs review`) with visible feedback state.
8. **Methodology/about:** architecture ribbon, technology chips, team, mentor, institution, and backend integration note.

## Backend integration seam

The demo data module will mirror likely FastAPI contracts so replacement is straightforward:

- `POST /api/reports/upload` → `{ reportId, status, pages, extractedText }`
- `GET /api/reports/:reportId` → report summary, findings, extracted spans, source references
- `GET /api/patients/:patientId/trends?metric=ldl` → time-series values
- `GET /api/evidence/:findingId` → retrieved sources and evidence graph edges
- `POST /api/reports/:reportId/questions` → grounded Q&A response and source refs
- `POST /api/reviews/:findingId` → doctor review verdict and note

The UI will use a single `apiClient` seam later; for now the same data shapes are supplied by `demoData.ts`. No credentials or medical claims are added to the frontend.

## Accessibility and safety

Use text + icon + label for statuses, visible keyboard focus, semantic buttons, labelled inputs, responsive layouts, readable contrast, reduced-motion support, and a persistent disclaimer that the experience explains uploaded information and does not diagnose or replace a clinician. No unsupported medical citations or fabricated publication metadata will be shown as factual.

## Build workflow

1. Create `TODO.md` from the brief's acceptance requirements.
2. Add the Vite/React/TypeScript source, route manifest, and project logo metadata.
3. Register TypeScript diagnostics through Webdev's Sandbox-managed runtime.
4. Start the Vite dev server on the configured port 3000 and verify HTTP readiness.
5. Inspect the responsive UI through the managed Preview screenshot tool at desktop and mobile widths.
6. Run a read-only requirement review over the implemented files, then fix confirmed issues.
7. Commit the intended project files to the canonical repository so the project has a recoverable checkpoint.

## Out of scope for this first pass

- Real authentication, patient privacy controls, persistent database records, or production medical decision support.
- Calling the user's existing FastAPI backend before its endpoint contract is confirmed.
- Actual PDF export, OCR, RAG retrieval, or LLM inference; the UI will expose integration-ready controls and clear demo labels.
