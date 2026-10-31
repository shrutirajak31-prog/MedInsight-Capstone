import torch
import os
import re
import uuid
import shutil
import datetime
import requests
from typing import Dict, List, Optional
from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.nlp_engine import process_document
from backend.schemas import ApiReport, ApiFinding, Source, TestResult
from backend.database import init_db, save_results, get_trends
from backend.llm_engine import generate_explanation
from backend.rag_engine import rag
from backend.qa_engine import answer_patient_question

app = FastAPI(title="MedInsight Backend API", version="1.0.0")

# Enable CORS for local development and UI frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for reports, findings, and reviews
REPORTS_CACHE: Dict[str, ApiReport] = {}
FINDINGS_CACHE: Dict[str, ApiFinding] = {}
REVIEWS_CACHE: Dict[str, dict] = {}

init_db()

def normalize_status(status_str: str) -> str:
    s = (status_str or "").lower()
    if "above" in s or "high" in s:
        return "High"
    if "below" in s or "low" in s:
        return "Low"
    return "Normal"

def parse_num(value_str: str) -> float:
    cleaned = re.sub(r'[^\d.]', '', str(value_str))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def make_definition(source_text: Optional[str], test_name: str) -> str:
    if not source_text:
        return f"{test_name} is a standard biological marker evaluated in diagnostic lab panels."
    first_p = source_text.find(". ")
    if first_p != -1 and first_p < 160:
        return source_text[:first_p + 1].strip()
    return source_text[:140].strip() + "..."

# Router for all endpoints so they work both with and without /api prefix
router = APIRouter()

@router.get("/")
async def root():
    return {"message": "MedInsight API is active and ready.", "docs": "/docs"}

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "MedInsight", "version": "1.0.0"}

# 1. Upload & Analyze
@router.post("/reports/upload", response_model=ApiReport)
async def analyze_report(file: UploadFile = File(...)):
    temp_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        raw_results: List[TestResult] = process_document(temp_path)
        
        findings: List[ApiFinding] = []
        for r in raw_results:
            norm_status = normalize_status(r.status)
            
            # Use XAI source info already retrieved by NLP engine
            source_text = r.xai.source_text if (r.xai and r.xai.source_text) else None
            source_url = r.xai.source_url if (r.xai and r.xai.source_url) else None
            
            if not source_text:
                rag_res = rag.retrieve(r.test_name)
                source_text = rag_res.get("source_text")
                source_url = rag_res.get("source_url")
            
            # Generate patient and doctor explanations
            patient_exp = r.explanation or generate_explanation(
                r.test_name, r.value, r.unit or "", norm_status, source_text or "", mode="patient"
            )
            doctor_exp = generate_explanation(
                r.test_name, r.value, r.unit or "", norm_status, source_text or "", mode="doctor"
            )
            
            f_id = str(uuid.uuid4())
            finding = ApiFinding(
                id=f_id,
                name=r.test_name,
                value=parse_num(r.value),
                unit=r.unit or "",
                referenceRange=r.reference_range or "—",
                status=norm_status,
                explanation=patient_exp,
                patientCopy=patient_exp,
                doctorCopy=doctor_exp,
                math=r.xai.math_proof if (r.xai and r.xai.math_proof) else f"{r.value} vs {r.reference_range}",
                limitation=r.xai.limitation if (r.xai and r.xai.limitation) else "Finding interpretation should be confirmed with clinical context.",
                definition=make_definition(source_text, r.test_name),
                sourceSnippet=source_text,
                sources=[Source(source="MedlinePlus", title=r.test_name, url=source_url or "https://medlineplus.gov", snippet=source_text)]
            )
            findings.append(finding)
            FINDINGS_CACHE[f_id] = finding

        report_id = str(uuid.uuid4())
        abnormal = len([f for f in findings if f.status in ("High", "Low")])
        normal = len([f for f in findings if f.status == "Normal"])
        summary_text = f"Report processed. Found {abnormal} values outside standard reference ranges and {normal} values within range."
        
        report = ApiReport(
            reportId=report_id,
            filename=file.filename,
            status="ready",
            summary=summary_text,
            findings=findings
        )
        
        # Save to cache and SQLite database for trend tracking
        REPORTS_CACHE[report_id] = report
        save_results("demo_user", datetime.date.today().isoformat(), findings)
        
        return report

    except Exception as e:
        print(f"Error during report processing: {e}")
        return ApiReport(
            reportId=str(uuid.uuid4()),
            filename=file.filename,
            status="error",
            summary=f"Analysis encountered an issue: {str(e)}",
            findings=[]
        )
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

# 2. Get Report by ID
@router.get("/reports/{report_id}", response_model=ApiReport)
async def get_report(report_id: str):
    if report_id in REPORTS_CACHE:
        return REPORTS_CACHE[report_id]
    
    # If demo requested or not found, return the most recently uploaded report if available
    if REPORTS_CACHE:
        return list(REPORTS_CACHE.values())[-1]

    return ApiReport(
        reportId=report_id,
        filename="report.pdf",
        status="ready",
        summary="No reports uploaded yet.",
        findings=[]
    )

# 3. Trends Endpoint
@router.get("/patients/{patient_id}/trends")
async def trends(patient_id: str, metric: str = Query("both")):
    return get_trends(patient_id, metric)

# 4. Evidence Endpoint
@router.get("/evidence/{finding_id}")
async def get_evidence(finding_id: str):
    finding = FINDINGS_CACHE.get(finding_id)
    if finding and finding.sources:
        sources_list = [s.model_dump() for s in finding.sources]
    else:
        sources_list = [{
            "source": "MedlinePlus",
            "title": finding.name if finding else "Laboratory Biomarker",
            "url": "https://medlineplus.gov",
            "snippet": finding.sourceSnippet if finding else None
        }]
    
    return {
        "findingId": finding_id,
        "sources": sources_list,
        "edges": [
            {"from": "finding", "to": "evidence", "type": "verified_source"},
            {"from": "evidence", "to": "explanation", "type": "grounded_generation"}
        ]
    }

# 5. Interactive Q&A for Patient Understanding
@router.post("/reports/{report_id}/questions")
async def ask_question(report_id: str, data: dict):
    question = (data.get("question") or "").strip()
    language = data.get("locale") or data.get("language") or "English"
    if not question:
        return {"answer": "Please ask a question about your medical report or any lab test.", "sources": [], "evidenceSufficient": True}
    
    # Retrieve report from cache if available, or fall back to most recent uploaded report
    report = REPORTS_CACHE.get(report_id)
    if not report and REPORTS_CACHE:
        report = list(REPORTS_CACHE.values())[-1]
        
    findings_list = report.findings if report else []

    # Retrieve trusted MedlinePlus context via RAG
    rag_snippet = None
    source_url = None
    matched_test = None
    try:
        rag_res = rag.retrieve(question)
        rag_snippet = rag_res.get("source_text")
        source_url = rag_res.get("source_url")
        matched_test = rag_res.get("matched_test")
    except Exception as e:
        print(f"RAG retrieval notice: {e}")

    # Generate patient understanding answer
    result = answer_patient_question(
        question=question,
        findings=findings_list,
        rag_snippet=rag_snippet,
        source_url=source_url,
        matched_test=matched_test,
        language=language
    )
    
    # Attach source if matched
    if source_url and matched_test:
        result["sources"] = [{
            "source": "MedlinePlus",
            "title": matched_test,
            "url": source_url,
            "snippet": rag_snippet
        }]
        
    return result

# 6. Doctor Review Endpoint
@router.post("/reviews/{finding_id}")
async def review_finding(finding_id: str, data: dict):
    verdict = data.get("verdict", "correct")
    note = data.get("note", "")
    REVIEWS_CACHE[finding_id] = {
        "verdict": verdict,
        "note": note,
        "timestamp": datetime.datetime.now().isoformat()
    }
    print(f"Doctor review saved for {finding_id}: verdict={verdict}, note={note}")
    return {"saved": True, "findingId": finding_id, "verdict": verdict}

# Register all endpoints directly and with /api prefix
app.include_router(router)
app.include_router(router, prefix="/api")
