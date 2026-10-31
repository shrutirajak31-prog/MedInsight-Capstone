# Connecting MedInsight to your FastAPI backend in VS Code

The UI is now complete as a responsive concept showcase. It currently uses clearly labeled demonstration data from `src/data/demoData.ts`, so it does not pretend to run OCR, CRF extraction, RAG retrieval, LLM generation, authentication, or a database. The visual components are already separated by responsibility so the backend can be added incrementally.

## 1. Open the project in VS Code

Open the project folder:

```bash
code /home/ubuntu/medinsight
npm install
npm run dev
```

The UI runs at `http://localhost:3000` in the current configuration. The app expects the FastAPI service to be reachable separately, for example at `http://localhost:8000`.

## 2. Add the API base URL

Create a local `.env.local` file in the frontend project. Do not commit it if your backend URL contains credentials.

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

Restart Vite after changing environment variables. The typed client in `src/lib/apiClient.ts` reads this value and falls back to `/api`.

## 3. Recommended FastAPI contract

The client seam is already written around these routes:

| UI action | Method | Suggested route | Response shape |
| --- | --- | --- | --- |
| Upload a report | `POST` | `/api/reports/upload` | `{ reportId, filename, status, ... }` |
| Read an analysed report | `GET` | `/api/reports/{report_id}` | summary, extracted text, findings, bounding boxes |
| Read a trend | `GET` | `/api/patients/{patient_id}/trends?metric=ldl` | array of `{ date, metric, value, unit }` |
| Load evidence | `GET` | `/api/evidence/{finding_id}` | sources and graph edges |
| Ask a report question | `POST` | `/api/reports/{report_id}/questions` | answer, source refs, evidence sufficiency |
| Doctor review | `POST` | `/api/reviews/{finding_id}` | `{ saved: true }` |

The frontend types are in `src/lib/apiClient.ts`. Extend those types if your backend returns more fields. In particular, the XAI overlay expects each extracted span to eventually provide a `page`, `text`, and normalized `bbox` tuple `[x, y, width, height]`.

## 4. Replace demo data in small steps

Start in `src/App.tsx`:

1. Keep `findings`, `trendData`, `evidenceCards`, and `savedReports` as the temporary fallback.
2. Import `apiClient` and add loading/error state for the selected report.
3. When the upload succeeds, store the returned `reportId` and poll `GET /reports/{report_id}` while the backend status is `processing`.
4. Map the backend response into the existing UI fields. Keep the explicit `demo` label until the response has a real `reportId` and verified sources.
5. Replace the trend chart input with `apiClient.getTrend(patientId, metric)`.
6. Replace evidence cards and the graph edges with `apiClient.getEvidence(findingId)`.
7. Replace the chat demo response with `apiClient.askQuestion(reportId, question, locale)` and display the insufficient-evidence state when `evidenceSufficient` is false.
8. Wire the Doctor `Correct` / `Needs review` buttons to `apiClient.reviewFinding`.

Do not remove the patient-facing disclaimer or turn an elevated result into a diagnosis. Keep the exact comparison math, reference range, limitation, source excerpt, and generated explanation as separate visual layers.

## 5. Enable CORS in FastAPI during local development

Your backend should allow the Vite origin while you develop:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, replace the wildcard-style development settings with your real frontend origin and add authentication/session handling appropriate to your deployment.

## 6. Suggested backend-to-UI mapping

- **PyMuPDF / EasyOCR:** return page text and extracted bounding boxes for `XaiReportPreview`.
- **CRF or NLP information extraction:** return the test name/value/unit/reference span separately from the generated explanation.
- **Rule-based value analysis:** return the status and an explicit comparison string such as `165.0 > 100.0`; do not make the UI infer medical meaning from color alone.
- **FAISS + Sentence Transformers + MedlinePlus/WHO/PubMed:** return verified source metadata and snippets. The UI intentionally does not invent publication details or source URLs.
- **LLM layer:** return plain-language explanation, technical explanation, limitations, safe general lifestyle guidance, and evidence sufficiency as separate fields.
- **Doctor review:** store the verdict, reviewer, timestamp, and optional note rather than silently overwriting the original generated explanation.

## 7. Production hardening before real patient data

Before connecting real reports, add authentication and authorization, encrypted transport, server-side file validation, malware scanning, size/page limits, audit logging, retention/deletion rules, private object storage, rate limits, and a formal review of applicable health-data/privacy requirements. Treat this concept showcase as a frontend prototype, not a clinical decision-support system.
