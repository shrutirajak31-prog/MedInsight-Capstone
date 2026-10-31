import re
import requests
from typing import Optional, List, Dict, Any

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"

def build_grounded_explanation(
    test_name: str,
    value: str,
    unit: str,
    status: str,
    source_text: str,
    mode: str = "patient"
) -> str:
    """
    Produces an instant, clinically accurate, deterministic explanation
    grounded directly in MedlinePlus facts and the test result.
    """
    status_lower = (status or "").lower()
    val_str = f"{value} {unit}".strip()

    # Extract clean sentence from source text if available
    snippet = ""
    if source_text:
        # Find first complete informative sentence
        clean_s = re.sub(r'\s+', ' ', source_text).strip()
        first_period = clean_s.find(". ")
        if first_period != -1 and first_period < 180:
            snippet = clean_s[:first_period + 1].strip()
        else:
            snippet = clean_s[:150].strip() + "..."

    if mode == "doctor":
        if "above" in status_lower or "high" in status_lower:
            deg = "Elevated"
        elif "below" in status_lower or "low" in status_lower:
            deg = "Reduced"
        else:
            deg = "Normal"
        ctx = f" Note: {snippet}" if snippet else ""
        return f"{deg} {test_name} level recorded at {val_str} ({status}).{ctx} Correlate with clinical presentation and consider longitudinal follow-up."
    else:
        if "above" in status_lower or "high" in status_lower:
            status_desc = f"is {val_str}, which is higher than the standard reference range"
            impact = "Elevated levels can occur due to lifestyle, hydration, or metabolic factors and should be reviewed with your doctor."
        elif "below" in status_lower or "low" in status_lower:
            status_desc = f"is {val_str}, which is below the standard reference range"
            impact = "Lower levels may indicate a temporary dip, dietary factors, or physiological variation."
        elif "within" in status_lower or "normal" in status_lower:
            status_desc = f"is {val_str}, which is within the healthy reference range"
            impact = "This indicates healthy physiological balance for this marker."
        else:
            status_desc = f"is recorded at {val_str}"
            impact = "Compare with your baseline and discuss with your clinician."

        desc = f" {snippet}" if snippet else f" {test_name} is an important biological marker evaluated in standard lab panels."
        return f"Your {test_name} {status_desc}.{desc} {impact} Note: This explanation is for patient understanding and does not replace a doctor's evaluation."

def generate_explanation(
    test_name: str,
    value: str,
    unit: str,
    status: str,
    source_text: str,
    mode: str = "patient"
) -> str:
    """
    Generates explanation for report upload.
    Uses high-quality grounded explanation for ultra-fast, zero-delay report processing.
    """
    return build_grounded_explanation(test_name, str(value), unit, status, source_text, mode)

def generate_llm_chat(
    question: str,
    findings_summary: str,
    medline_context: str,
    language: str = "English"
) -> Optional[str]:
    """
    Queries local Ollama Phi-3 with a patient understanding prompt.
    Returns generated plain-language response if available within timeout.
    """
    lang_prompt = f" Respond in {language}." if language and language.lower() != "english" else ""
    
    prompt = f"""<|system|>
You are MedInsight, an empathetic, clear medical communicator helping a patient understand their medical lab report.
Guidelines:
1. Explain in simple, reassuring everyday language that anyone can easily understand.
2. Ground all medical facts in the provided MedlinePlus context.
3. If the test is in CURRENT REPORT FINDINGS, reference their exact numbers and whether it is normal or abnormal.
4. If the test is NOT in the report, clarify that simply.
5. Provide 1 practical healthy habit tip and 1 good question to ask their doctor.
6. Keep response concise (under 120 words) with clear bullet points. Do not give medical diagnoses.{lang_prompt}
<|end|>
<|user|>
CURRENT REPORT FINDINGS:
{findings_summary}

MEDLINEPLUS CONTEXT:
{medline_context}

PATIENT QUESTION:
{question}
<|end|>
<|assistant|>
"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "30m",
        "options": {
            "num_predict": 130,
            "temperature": 0.2,
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=9)
        if response.status_code == 200:
            ans = response.json().get("response", "").strip()
            if ans and len(ans) > 20:
                return ans
    except Exception as e:
        print(f"Ollama chat note: {e}")
        
    return None
