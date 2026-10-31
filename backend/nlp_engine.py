import os
from src.ocr.pdf_extractor import extract_pdf
from src.ocr.easyocr_extractor import extract_image
from src.ner.crf_model import load_crf, predict_record
from src.relation.rules import extract_tuples

from backend.abnormality import check_status
from backend.schemas import TestResult, XAIInfo
from backend.rag_engine import rag
from backend.llm_engine import generate_explanation

# Load the CRF model once globally
CRF_MODEL_PATH = "checkpoints/crf_full.pkl"
print("Loading CRF model into memory...")
crf = load_crf(CRF_MODEL_PATH)

def process_document(file_path: str) -> list[TestResult]:
    # 1. Document Extraction
    if file_path.lower().endswith(".pdf"):
        pages = extract_pdf(file_path)
        source = "pdf"
    else:
        pages = extract_image(file_path)
        source = "ocr"

    # 2. Format for CRF
    record = {
        "words": [],
        "bboxes": [],
        "labels": [],
        "source": source
    }
    
    for page in pages:
        for w in page["words"]:
            record["words"].append(w["text"])
            record["bboxes"].append(w["bbox"])

    # 3. NLP Extraction (CRF)
    predicted_labels = predict_record(crf, record)
    
    # 4. Relation Extraction
    tuples = extract_tuples(record["words"], predicted_labels, record["bboxes"])
    
    results = []
    
    for t in tuples:
        if not t["test"] or not t["value"]:
            continue
            
        # 5. Deterministic Math
        math_res = check_status(t["value"], t["range"] or "")
        
        # 6. RAG Retrieval
        rag_result = rag.retrieve(t["test"])
        
        # 7. XAI Formatting
        xai_info = XAIInfo(
            ocr_confidence=0.95, 
            math_proof=math_res["math_proof"],
            source_text=rag_result["source_text"],
            source_url=rag_result["source_url"],
            limitation=math_res["limitation"]
        )
        
        # 8. LLM Generation
        explanation = generate_explanation(
            test_name=t["test"],
            value=t["value"],
            unit=t["unit"] or "",
            status=math_res["status"],
            source_text=rag_result["source_text"] or ""
        )

        results.append(TestResult(
            test_name=t["test"],
            value=t["value"],
            unit=t["unit"] or "",
            reference_range=t["range"] or "",
            status=math_res["status"],
            xai=xai_info,
            explanation=explanation
        ))
        
    return results