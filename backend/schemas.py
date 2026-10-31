from pydantic import BaseModel
from typing import List, Optional

class Source(BaseModel):
    source: str
    title: str
    url: Optional[str] = None
    publication: Optional[str] = None
    snippet: Optional[str] = None

class XAIInfo(BaseModel):
    ocr_confidence: float = 0.95
    math_proof: Optional[str] = None
    source_text: Optional[str] = None
    source_url: Optional[str] = None
    limitation: Optional[str] = None

class TestResult(BaseModel):
    test_name: str
    value: str
    unit: Optional[str] = ""
    reference_range: Optional[str] = ""
    status: str = "Unknown"
    xai: Optional[XAIInfo] = None
    explanation: Optional[str] = None

class ApiFinding(BaseModel):
    id: str
    name: str
    value: float
    unit: str
    referenceRange: str
    status: str  # 'Normal' | 'High' | 'Low'
    explanation: Optional[str] = None
    sources: Optional[List[Source]] = None
    sourceSnippet: Optional[str] = None
    
    # Manus / MedInsight XAI specific fields
    patientCopy: Optional[str] = None
    doctorCopy: Optional[str] = None
    math: Optional[str] = None
    limitation: Optional[str] = None
    definition: Optional[str] = None

class ApiReport(BaseModel):
    reportId: str
    filename: str
    status: str
    summary: Optional[str] = None
    findings: Optional[List[ApiFinding]] = None
