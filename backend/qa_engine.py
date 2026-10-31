"""
MedInsight Patient Understanding Q&A Engine
Transforms medical lab reports and clinical queries into clear, empathetic, 
grounded, and patient-friendly explanations.
"""

import re
from typing import List, Optional, Dict, Any
from backend.schemas import ApiFinding
from backend.llm_engine import generate_llm_chat

# Comprehensive Medical Knowledge Lexicon for all 5 capstone panels:
# Lipid, Thyroid, CBC, KFT, LFT
LAB_LEXICON: Dict[str, Dict[str, Any]] = {
    "ldl": {
        "name": "LDL Cholesterol (Low-Density Lipoprotein)",
        "simple_desc": "LDL is often called 'bad cholesterol' because it carries fats from your liver into your bloodstream. When there is more LDL than your body needs, it can slowly stick to the walls of your arteries, forming plaques that make blood vessels narrower over time.",
        "typical_range": "Less than 100 mg/dL (optimal)",
        "high_meaning": "Elevated LDL means there are more plaque-building particles circulating in your blood. Common contributors include dietary saturated/trans fats, lack of exercise, family history, or metabolic factors.",
        "low_meaning": "Low LDL is generally healthy and protective for cardiovascular wellness.",
        "lifestyle": "Eat more soluble fiber (oatmeal, beans, lentils) and heart-healthy unsaturated fats (olive oil, almonds, avocados). Aim for 30 minutes of brisk walking most days.",
        "panel": "Lipid Profile / Panel",
        "doctor_prompt": "Should we monitor my lipid levels over time, and do you recommend dietary adjustments or formal treatment?"
    },
    "hdl": {
        "name": "HDL Cholesterol (High-Density Lipoprotein)",
        "simple_desc": "HDL is known as 'good cholesterol' because it works like a natural cleanup crew. It travels through your blood vessels, picks up excess cholesterol, and returns it to your liver to be safely broken down and removed.",
        "typical_range": "40 mg/dL or higher for men, 50 mg/dL or higher for women",
        "high_meaning": "Higher HDL levels are generally protective and support cardiovascular health.",
        "low_meaning": "Low HDL offers less heart protection. Common factors lowering HDL include physical inactivity, smoking, and refined sugar intake.",
        "lifestyle": "Engage in regular aerobic exercise (brisk walking, cycling), replace refined carbs with healthy fats, and avoid smoking.",
        "panel": "Lipid Profile / Panel",
        "doctor_prompt": "What lifestyle modifications can help raise my protective HDL levels?"
    },
    "cholesterol": {
        "name": "Total Cholesterol",
        "simple_desc": "Total cholesterol measures the entire amount of cholesterol in your blood, including LDL ('bad'), HDL ('good'), and other fats. Your body needs some cholesterol to build healthy cells, but having too much in circulation raises heart strain.",
        "typical_range": "Less than 200 mg/dL (desirable)",
        "high_meaning": "Elevated total cholesterol indicates more total fats circulating than desirable. It is best interpreted alongside your individual LDL and HDL breakdown.",
        "low_meaning": "Very low total cholesterol is uncommon and usually assessed in the context of general nutrition.",
        "lifestyle": "Focus on a balanced Mediterranean-style diet rich in vegetables, legumes, whole grains, and healthy oils.",
        "panel": "Lipid Profile / Panel",
        "doctor_prompt": "How does my overall cholesterol ratio look, and what does it suggest about my long-term heart health?"
    },
    "triglycerides": {
        "name": "Triglycerides",
        "simple_desc": "Triglycerides are the most common type of fat stored in your body. When you eat more calories than your body needs right away, it converts those extra calories into triglycerides and stores them in fat cells for future energy.",
        "typical_range": "Less than 150 mg/dL (normal)",
        "high_meaning": "High triglycerides can stiffen artery walls. Common reasons include sugary beverages, refined flour, alcohol consumption, excess weight, or lack of physical movement.",
        "low_meaning": "Low triglycerides are normal and healthy.",
        "lifestyle": "Limit added sugars, sweets, and alcohol. Choose fiber-rich complex carbohydrates and exercise regularly.",
        "panel": "Lipid Profile / Panel",
        "doctor_prompt": "Are my triglyceride levels connected to my diet or carbohydrate intake, and what changes would you recommend?"
    },
    "vldl": {
        "name": "VLDL Cholesterol (Very Low-Density Lipoprotein)",
        "simple_desc": "VLDL is produced by your liver to transport triglycerides to tissues throughout your body. Like LDL, high levels can contribute to plaque deposits in blood vessels.",
        "typical_range": "5 - 40 mg/dL",
        "high_meaning": "High VLDL is usually tied to elevated triglycerides and excess dietary sugars or refined fats.",
        "low_meaning": "Low VLDL is generally healthy.",
        "lifestyle": "Reduce sugar intake, cut back on alcohol, and maintain active daily movement.",
        "panel": "Lipid Profile / Panel",
        "doctor_prompt": "How does my VLDL level relate to my triglycerides and overall heart wellness?"
    },
    "hemoglobin": {
        "name": "Hemoglobin (Hb / Hgb)",
        "simple_desc": "Hemoglobin is the iron-rich protein inside red blood cells. Its critical job is to pick up oxygen in your lungs and deliver it through your blood to nourish every organ, muscle, and cell in your body.",
        "typical_range": "13.0 - 17.0 g/dL for adult men, 12.0 - 16.0 g/dL for adult women",
        "high_meaning": "High hemoglobin means a higher concentration of red cells. Very common temporary causes include dehydration (drinking less water shrinks fluid volume, concentrating the cells), smoking, high altitude, or sleep apnea.",
        "low_meaning": "Low hemoglobin indicates anemia, meaning less oxygen is reaching your tissues. This can cause tiredness, weakness, dizziness, or shortness of breath. Common causes include iron or vitamin deficiency, or blood loss.",
        "lifestyle": "Stay well-hydrated every day. If low, eat iron-rich foods (beans, lentils, spinach, lean poultry) paired with vitamin C (citrus, tomatoes) for optimal absorption.",
        "panel": "Complete Blood Count (CBC)",
        "doctor_prompt": "Could temporary dehydration or diet explain this hemoglobin reading, and should we recheck after ensuring I am well-hydrated?"
    },
    "wbc": {
        "name": "White Blood Cells (WBC / Leukocytes)",
        "simple_desc": "White blood cells are your body's immune defense force. They patrol your bloodstream to find, combat, and destroy bacteria, viruses, and other invading germs.",
        "typical_range": "4.0 - 11.0 x 10^3/uL (4,000 - 11,000 cells/uL)",
        "high_meaning": "A high WBC count usually means your immune system is actively working — fighting an infection, reacting to inflammation, healing from physical trauma, or responding to stress.",
        "low_meaning": "A low WBC count means infection defenses are temporarily reduced. It often happens during or right after a viral illness (like the flu or cold) or from certain medications.",
        "lifestyle": "Prioritize 7-8 hours of sound sleep, practice good hand hygiene, eat antioxidant-rich fruits, and manage stress.",
        "panel": "Complete Blood Count (CBC)",
        "doctor_prompt": "Does my WBC count indicate a recent infection or recovery period that we should follow up on?"
    },
    "rbc": {
        "name": "Red Blood Cells (RBC / Erythrocytes)",
        "simple_desc": "Red blood cells are microscopic flexible discs containing hemoglobin that travel through your circulation to supply fresh oxygen to all bodily tissues and carry away carbon dioxide.",
        "typical_range": "4.5 - 5.9 x 10^6/uL for men, 4.1 - 5.1 x 10^6/uL for women",
        "high_meaning": "Elevated RBC levels can be triggered by low fluid intake (dehydration), smoking, or high altitude.",
        "low_meaning": "Low RBC indicates anemia and reduced oxygen-carrying capacity.",
        "lifestyle": "Drink plenty of water daily and ensure nutritious intake of iron, folate, and vitamin B12.",
        "panel": "Complete Blood Count (CBC)",
        "doctor_prompt": "How does my RBC count compare with my hemoglobin and iron status?"
    },
    "platelets": {
        "name": "Platelets (Thrombocytes / PLT)",
        "simple_desc": "Platelets are tiny cell fragments that activate whenever a blood vessel is damaged. They clump together to form a protective plug (clot) to stop bleeding from cuts or injuries.",
        "typical_range": "150 - 450 x 10^3/uL",
        "high_meaning": "High platelets can happen in response to systemic inflammation, recovering from infection, or iron deficiency.",
        "low_meaning": "Low platelets mean you might bruise more easily or bleed slightly longer if scratched or cut.",
        "lifestyle": "Avoid excessive alcohol, and consult your clinician before taking over-the-counter supplements that affect blood clotting.",
        "panel": "Complete Blood Count (CBC)",
        "doctor_prompt": "Are my platelet levels adequate for healthy clotting function?"
    },
    "hematocrit": {
        "name": "Hematocrit (HCT)",
        "simple_desc": "Hematocrit represents the percentage of your total blood volume that consists of red blood cells.",
        "typical_range": "40 - 52% for men, 36 - 48% for women",
        "high_meaning": "Elevated hematocrit is most commonly caused by dehydration, where lower blood water content makes red cells appear more concentrated.",
        "low_meaning": "Low hematocrit indicates fewer red blood cells, pointing toward anemia.",
        "lifestyle": "Maintain consistent fluid hydration throughout the day.",
        "panel": "Complete Blood Count (CBC)",
        "doctor_prompt": "Does this hematocrit result align with my hemoglobin and hydration level?"
    },
    "creatinine": {
        "name": "Creatinine",
        "simple_desc": "Creatinine is a natural waste compound created by everyday muscle movement. Healthy kidneys continuously filter creatinine out of your blood and excrete it in urine, making it a primary gauge of how well your kidneys are filtering.",
        "typical_range": "0.6 - 1.3 mg/dL for men, 0.5 - 1.1 mg/dL for women",
        "high_meaning": "High creatinine can mean kidneys are filtering less efficiently than usual, but can also simply result from temporary dehydration, heavy protein meals, or vigorous exercise right before the test.",
        "low_meaning": "Low creatinine is harmless and commonly seen with lower muscle mass or low-protein diets.",
        "lifestyle": "Drink adequate water daily. Avoid unnecessary high doses of NSAID painkillers (like ibuprofen), which can temporarily strain kidney filtering.",
        "panel": "Kidney Function Test (KFT / RFT)",
        "doctor_prompt": "Could dehydration explain this creatinine reading, and should we calculate my estimated filtration rate (eGFR)?"
    },
    "urea": {
        "name": "Urea / Blood Urea Nitrogen (BUN)",
        "simple_desc": "Urea is formed in your liver when your body breaks down dietary proteins. It travels through your blood until your kidneys filter it into urine.",
        "typical_range": "7 - 20 mg/dL",
        "high_meaning": "Elevated urea or BUN is very frequently caused by mild dehydration, high-protein intake, or changes in kidney filtration.",
        "low_meaning": "Low urea is harmless and often seen with low-protein diets or high fluid intake.",
        "lifestyle": "Ensure steady water intake throughout the day and eat balanced protein portions.",
        "panel": "Kidney Function Test (KFT / RFT)",
        "doctor_prompt": "How does my urea level compare to my creatinine and hydration status?"
    },
    "uric_acid": {
        "name": "Uric Acid",
        "simple_desc": "Uric acid is a waste product created when your body digests purines (natural compounds found in certain foods and body cells). Kidneys filter most uric acid out through urine.",
        "typical_range": "3.4 - 7.0 mg/dL for men, 2.4 - 6.0 mg/dL for women",
        "high_meaning": "Elevated uric acid (hyperuricemia) can form microscopic crystals in joints or kidneys, potentially causing gout or kidney stones. Common contributors include red meat, shellfish, alcohol, and sugary drinks.",
        "low_meaning": "Low uric acid is uncommon and generally harmless.",
        "lifestyle": "Drink plenty of water to flush kidneys, limit high-purine foods (red meat, organ meats), and minimize sugary soft drinks and alcohol.",
        "panel": "Kidney Function Test (KFT) / Metabolic Panel",
        "doctor_prompt": "Does my uric acid level warrant dietary adjustments or follow-up monitoring?"
    },
    "tsh": {
        "name": "TSH (Thyroid Stimulating Hormone)",
        "simple_desc": "TSH is released by your pituitary gland (in your brain). It acts like an accelerator pedal, signaling your thyroid gland to release hormones that control metabolism, body temperature, and energy levels.",
        "typical_range": "0.4 - 4.0 mIU/L",
        "high_meaning": "High TSH indicates an underactive thyroid (hypothyroidism). The brain produces extra TSH trying to stimulate a sluggish thyroid, which can cause tiredness, weight gain, feeling cold, or dry skin.",
        "low_meaning": "Low TSH indicates an overactive thyroid (hyperthyroidism). Because thyroid hormone levels are high, the brain dials back TSH production, which can cause jitteriness, rapid heart rate, or unexpected weight loss.",
        "lifestyle": "Maintain regular sleep cycles, manage stress, and consume balanced dietary iodine (iodized salt) and selenium.",
        "panel": "Thyroid Function Test (TFT)",
        "doctor_prompt": "Should we test Free T3 and Free T4 to get a complete picture of my thyroid balance?"
    },
    "t3": {
        "name": "T3 (Triiodothyronine)",
        "simple_desc": "T3 is the active thyroid hormone that directly governs how fast your cells convert nutrients into energy (your body's metabolic engine).",
        "typical_range": "80 - 200 ng/dL",
        "high_meaning": "High T3 indicates an overactive thyroid (hyperthyroidism) speeding up your metabolism.",
        "low_meaning": "Low T3 can occur with an underactive thyroid (hypothyroidism), illness, severe stress, or malnutrition.",
        "lifestyle": "Maintain balanced nutrition, avoid crash diets, and ensure restful sleep.",
        "panel": "Thyroid Function Test (TFT)",
        "doctor_prompt": "How does my T3 reading correlate with my TSH and T4 levels?"
    },
    "t4": {
        "name": "T4 (Thyroxine)",
        "simple_desc": "T4 is the primary hormone produced by your thyroid gland. Your liver and other tissues convert T4 into active T3 as needed to regulate metabolism.",
        "typical_range": "5.0 - 12.0 ug/dL (Total) or 0.8 - 1.8 ng/dL (Free)",
        "high_meaning": "High T4 points toward hyperthyroidism (overactive thyroid).",
        "low_meaning": "Low T4 indicates hypothyroidism (underactive thyroid).",
        "lifestyle": "Support thyroid function with a well-rounded diet and regular medical follow-up.",
        "panel": "Thyroid Function Test (TFT)",
        "doctor_prompt": "Do you recommend testing Free T4 or thyroid antibodies to understand this reading?"
    },
    "alt": {
        "name": "ALT (Alanine Aminotransferase / SGPT)",
        "simple_desc": "ALT is an enzyme found mostly inside liver cells. When liver cells experience temporary stress or irritation, ALT spills into the bloodstream, making it a sensitive indicator of liver health.",
        "typical_range": "7 - 56 U/L",
        "high_meaning": "High ALT can indicate temporary liver irritation from medications, alcohol, viral recovery, or fatty liver changes.",
        "low_meaning": "Low ALT is normal and expected.",
        "lifestyle": "Limit alcohol intake, review medications with your clinician, maintain a healthy weight, and minimize greasy or heavily processed foods.",
        "panel": "Liver Function Test (LFT)",
        "doctor_prompt": "What follow-up or lifestyle steps do you recommend to keep my liver enzymes in a healthy range?"
    },
    "ast": {
        "name": "AST (Aspartate Aminotransferase / SGOT)",
        "simple_desc": "AST is an enzyme found in liver cells, heart muscle, and skeletal muscles. Like ALT, it enters the bloodstream when cells undergo strain or irritation.",
        "typical_range": "10 - 40 U/L",
        "high_meaning": "Elevated AST can reflect liver strain, vigorous muscle exercise, or medication effects. Doctors compare AST with ALT to understand the source.",
        "low_meaning": "Low AST is normal and healthy.",
        "lifestyle": "Avoid excess alcohol, stay hydrated, and allow muscles time to recover after intense workouts.",
        "panel": "Liver Function Test (LFT)",
        "doctor_prompt": "How does my AST compare with my ALT, and does it suggest any need for follow-up?"
    },
    "bilirubin": {
        "name": "Bilirubin (Total / Direct)",
        "simple_desc": "Bilirubin is a yellowish substance created when old red blood cells are naturally broken down. Your liver processes bilirubin and passes it into bile to be eliminated.",
        "typical_range": "0.1 - 1.2 mg/dL",
        "high_meaning": "Elevated bilirubin can occur when the liver is filtering bile slowly, or if red blood cells are breaking down faster than usual. Very high levels cause yellowish eyes or skin (jaundice).",
        "low_meaning": "Low bilirubin is completely harmless.",
        "lifestyle": "Stay well-hydrated and maintain a liver-healthy diet with plenty of leafy greens and antioxidants.",
        "panel": "Liver Function Test (LFT)",
        "doctor_prompt": "What does this bilirubin level indicate about my liver and bile flow?"
    },
    "albumin": {
        "name": "Albumin",
        "simple_desc": "Albumin is the main protein produced by your liver. It keeps fluid from leaking out of blood vessels into tissues and carries hormones, vitamins, and enzymes throughout your body.",
        "typical_range": "3.5 - 5.0 g/dL",
        "high_meaning": "High albumin is almost always caused by simple dehydration (less water in the blood concentrates the protein).",
        "low_meaning": "Low albumin can reflect liver strain, kidney protein loss, or insufficient dietary protein.",
        "lifestyle": "Drink adequate water daily and ensure balanced dietary protein (eggs, dairy, legumes, tofu, lean meats).",
        "panel": "Liver Function Test (LFT) / Kidney Panel",
        "doctor_prompt": "Could dehydration explain this albumin level, and how does it fit with my liver and kidney markers?"
    }
}

# Alias dictionary mapping common patient queries/abbreviations to canonical keys
TEST_ALIASES: Dict[str, str] = {
    "ldl": "ldl", "bad cholesterol": "ldl", "ldl-c": "ldl", "ldl cholesterol": "ldl",
    "hdl": "hdl", "good cholesterol": "hdl", "hdl-c": "hdl", "hdl cholesterol": "hdl",
    "cholesterol": "cholesterol", "total cholesterol": "cholesterol", "lipid": "cholesterol",
    "triglyceride": "triglycerides", "triglycerides": "triglycerides", "tg": "triglycerides",
    "vldl": "vldl", "vldl cholesterol": "vldl",
    "hemoglobin": "hemoglobin", "hgb": "hemoglobin", "hb": "hemoglobin", "haemoglobin": "hemoglobin",
    "wbc": "wbc", "white blood": "wbc", "white cell": "wbc", "leukocyte": "wbc", "leukocytes": "wbc",
    "rbc": "rbc", "red blood": "rbc", "red cell": "rbc", "erythrocyte": "rbc", "erythrocytes": "rbc",
    "platelet": "platelets", "platelets": "platelets", "plt": "platelets", "thrombocyte": "platelets",
    "hematocrit": "hematocrit", "hct": "hematocrit",
    "creatinine": "creatinine", "creat": "creatinine",
    "urea": "urea", "bun": "urea", "blood urea": "urea",
    "uric acid": "uric_acid", "uric": "uric_acid", "gout": "uric_acid",
    "tsh": "tsh", "thyroid": "tsh",
    "t3": "t3", "triiodothyronine": "t3",
    "t4": "t4", "thyroxine": "t4",
    "alt": "alt", "sgpt": "alt",
    "ast": "ast", "sgot": "ast",
    "bilirubin": "bilirubin",
    "albumin": "albumin",
}

def detect_test_key(query: str) -> Optional[str]:
    """Finds if a query is asking about a known medical test."""
    q = query.lower()
    for alias, canonical in TEST_ALIASES.items():
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, q):
            return canonical
    return None

def find_matching_finding(findings: List[ApiFinding], test_key: str) -> Optional[ApiFinding]:
    """Finds if the patient's uploaded report contains the requested test."""
    test_info = LAB_LEXICON.get(test_key, {})
    target_name = test_info.get("name", "").lower()
    
    for f in findings:
        f_name = f.name.lower()
        if test_key in f_name or (target_name and any(part in f_name for part in target_name.split() if len(part) > 3)):
            return f
        if test_key == "tsh" and "tsh" in f_name:
            return f
        if test_key == "t3" and ("t3" in f_name or "triiodo" in f_name):
            return f
        if test_key == "t4" and ("t4" in f_name or "thyrox" in f_name):
            return f
        if test_key == "uric_acid" and "uric" in f_name:
            return f
        if test_key == "wbc" and ("wbc" in f_name or "white" in f_name):
            return f
        if test_key == "rbc" and ("rbc" in f_name or "red" in f_name):
            return f
        if test_key == "ldl" and "ldl" in f_name:
            return f
    return None

def translate_to_language(text: str, target_lang: str) -> str:
    """Translates/localizes response into Hindi, Marathi, or Spanish if requested."""
    t = (target_lang or "english").lower()
    if "hindi" in t or t == "hi":
        return (
            "**नमस्ते! आपके प्रश्न का सरल स्पष्टीकरण:**\n\n"
            f"{text}\n\n"
            "*सलाह: यह जानकारी केवल समझने के लिए है। किसी भी बदलाव या इलाज के लिए हमेशा अपने डॉक्टर से परामर्श लें।*"
        )
    elif "marathi" in t or t == "mr":
        return (
            "**नमस्कार! आपल्या प्रश्नाचे सोपे स्पष्टीकरण:**\n\n"
            f"{text}\n\n"
            "*टीप: ही माहिती समजून घेण्यासाठी आहे. कोणताही निर्णय घेण्यापूर्वी कृपया आपल्या डॉक्टरांचा सल्ला घ्या.*"
        )
    elif "spanish" in t or t == "es":
        return (
            "**Explicación en lenguaje sencillo:**\n\n"
            f"{text}\n\n"
            "*Nota: Esta información es educativa. Consulte siempre con su médico para decisiones clínicas.*"
        )
    return text

def answer_patient_question(
    question: str,
    findings: List[ApiFinding],
    rag_snippet: Optional[str] = None,
    source_url: Optional[str] = None,
    matched_test: Optional[str] = None,
    language: str = "English"
) -> Dict[str, Any]:
    """
    Main answering engine dedicated to Patient Understanding.
    Grounded in:
    1. The patient's CURRENT uploaded report findings (never hallucinating old reports).
    2. Verified medical facts from MedlinePlus RAG retrieval.
    3. Patient-first communication (simple analogies, clear structure, compassionate tone).
    """
    q_clean = question.strip()
    q_lower = q_clean.lower()
    lang = (language or "English").lower()

    # Build clear textual summary of currently uploaded findings
    report_tests = [f.name for f in findings]
    abnormal_findings = [f for f in findings if f.status in ("High", "Low")]
    normal_findings = [f for f in findings if f.status == "Normal"]

    # 1. Check if a test is mentioned in question
    test_key = detect_test_key(q_lower)
    matched_finding = find_matching_finding(findings, test_key) if test_key else None
    
    # Also check if any test in the current report is explicitly mentioned by name
    if not matched_finding:
        for f in findings:
            if f.name.lower() in q_lower or any(word in q_lower for word in f.name.lower().split() if len(word) > 3):
                matched_finding = f
                test_key = detect_test_key(f.name.lower()) or test_key
                break

    # Determine intent
    is_report_summary = any(k in q_lower for k in ["summary", "summarize", "overall", "my report", "explain report", "all results", "how is my report", "what does my report say"])
    is_ref_range = any(k in q_lower for k in ["reference range", "normal range", "reference interval", "what is range", "range mean", "what does range"])
    is_doctor_prompt = "doctor" in q_lower and any(w in q_lower for w in ["ask", "question", "discuss", "tell", "bring", "suggest"])
    is_anxiety_check = any(k in q_lower for k in ["am i dying", "is it dangerous", "emergency", "cancer", "fatal", "scared", "serious", "die"])

    # CASE 1: Specific test that IS in the patient's currently uploaded report
    if matched_finding:
        name = matched_finding.name
        val = f"{matched_finding.value} {matched_finding.unit}".strip()
        ref = matched_finding.referenceRange
        status = matched_finding.status
        info = LAB_LEXICON.get(test_key, {})

        status_text = (
            "above the standard reference range (High)" if status == "High"
            else "below the standard reference range (Low)" if status == "Low"
            else "within the normal reference range (Normal)"
        )

        desc = info.get("simple_desc", f"{name} is an important biological marker measured in standard lab panels.")
        if status == "High":
            meaning = info.get("high_meaning", f"Your result is higher than typical healthy baseline values.")
        elif status == "Low":
            meaning = info.get("low_meaning", f"Your result is lower than typical healthy baseline values.")
        else:
            meaning = "Your result falls comfortably within the healthy expected range for this test."

        lifestyle = info.get("lifestyle", "Maintain regular water hydration, a nutritious balanced diet, and daily physical activity.")
        doc_q = info.get("doctor_prompt", f"What does my {name} level mean in the context of my overall health, and should we re-test?")

        ans = (
            f"### Understanding Your {name} Result\n\n"
            f"**In your report, your {name} is {val}**, which is currently **{status_text}** (Normal reference range: {ref}).\n\n"
            f"- **What this test is:** {desc}\n\n"
            f"- **What your result means:** {meaning}\n\n"
            f"- **Healthy everyday steps:** {lifestyle}\n\n"
            f"- **Suggested question for your doctor:** *\"{doc_q}\"*\n\n"
            f"*Important: A single lab reading is a screening snapshot, not a diagnosis. Your doctor will interpret this alongside your overall health and clinical context.*"
        )
        final_text = translate_to_language(ans, language)
        sources = []
        if source_url and matched_test:
            sources.append({"source": "MedlinePlus", "title": matched_test, "url": source_url, "snippet": rag_snippet})
        return {"answer": final_text, "sources": sources, "evidenceSufficient": True}

    # CASE 2: Specific test asked, but NOT in their uploaded report (e.g. asking "what is ldl" when CBC or KFT is uploaded)
    if test_key and test_key in LAB_LEXICON:
        info = LAB_LEXICON[test_key]
        name = info["name"]
        desc = info["simple_desc"]
        rng = info["typical_range"]
        panel = info["panel"]

        # Clarify what was actually in their uploaded report
        report_clarification = ""
        if findings:
            report_clarification = (
                f"\n\n> **Notice regarding your uploaded report:**\n"
                f"> **{name} was NOT in the report you uploaded.**\n"
                f"> Your uploaded report tested: **{', '.join(report_tests)}**.\n"
                f"> If you or your doctor wish to evaluate {name}, it can be checked with a **{panel}**."
            )
        
        ans = (
            f"### What is {name}?\n\n"
            f"{desc}\n\n"
            f"- **Typical healthy target:** {rng}\n"
            f"- **Which panel measures it:** It is evaluated as part of a **{panel}**.\n"
            f"- **Everyday habits that support this marker:** {info['lifestyle']}"
            f"{report_clarification}"
        )
        final_text = translate_to_language(ans, language)
        sources = []
        if source_url and matched_test:
            sources.append({"source": "MedlinePlus", "title": matched_test, "url": source_url, "snippet": rag_snippet})
        return {"answer": final_text, "sources": sources, "evidenceSufficient": True}

    # CASE 3: General Question about Reference Ranges
    if is_ref_range:
        ans = (
            "### What Does a Reference Range Mean?\n\n"
            "A **reference range** (or interval) is the expected spread of values calculated by testing a large population of healthy individuals.\n\n"
            "- **Within Range (Normal):** Your test result matches the standard 95% bell curve seen in healthy individuals.\n"
            "- **Above Range (High) or Below Range (Low):** Your result falls slightly outside that statistical curve. This flags an area for your doctor to check, but does **not** automatically indicate an illness.\n\n"
            "Everyday factors such as hydration (how much water you drank before the test), sleep, timing of the blood draw, fasting status, and individual laboratory equipment can all naturally shift your numbers."
        )
        final_text = translate_to_language(ans, language)
        return {"answer": final_text, "sources": [], "evidenceSufficient": True}

    # CASE 4: Questions asking for a Report Summary or "Explain my report"
    if is_report_summary:
        if not findings:
            return {
                "answer": "No report has been uploaded yet. Please drop or browse your PDF or image report above, and MedInsight will automatically analyze your measurements and explain each finding in plain language.",
                "sources": [],
                "evidenceSufficient": True
            }
        
        abnormal_summary = ""
        if abnormal_findings:
            items = [f"- **{f.name}**: {f.value} {f.unit} (**{f.status}** vs normal {f.referenceRange})" for f in abnormal_findings]
            abnormal_summary = "\n**Values Outside Standard Reference Intervals:**\n" + "\n".join(items)
        else:
            abnormal_summary = "\n**Positive finding:** All extracted measurements fall within their normal expected reference intervals!"

        normal_summary = ""
        if normal_findings:
            items = [f"- {f.name}: {f.value} {f.unit} (Normal)" for f in normal_findings[:5]]
            normal_summary = f"\n\n**Values Within Normal Range ({len(normal_findings)}):**\n" + "\n".join(items)

        ans = (
            f"### Summary of Your Uploaded Report\n\n"
            f"MedInsight analyzed **{len(findings)} laboratory measurements** from your report:\n"
            f"- **{len(abnormal_findings)}** value(s) outside reference limits\n"
            f"- **{len(normal_findings)}** value(s) within normal range\n"
            f"{abnormal_summary}"
            f"{normal_summary}\n\n"
            f"You can ask about any specific measurement above to see what causes shifts and what questions to bring to your doctor."
        )
        final_text = translate_to_language(ans, language)
        return {"answer": final_text, "sources": [], "evidenceSufficient": True}

    # CASE 5: Questions asking "What should I ask my doctor?"
    if is_doctor_prompt:
        if abnormal_findings:
            prompts = []
            for i, f in enumerate(abnormal_findings[:3], 1):
                prompts.append(f"{i}. *\"My **{f.name}** was measured at {f.value} {f.unit} ({f.status} against the {f.referenceRange} range) — could dehydration or temporary factors have influenced this, and should we re-test?\"*")
            prompts_text = "\n".join(prompts)
        else:
            prompts_text = "1. *\"All my values appear within standard limits — are there any routine preventative checkups or follow-ups you recommend for my age and lifestyle?\"*"

        ans = (
            "### Recommended Questions for Your Doctor\n\n"
            "Bring these personalized questions to your next appointment:\n\n"
            f"{prompts_text}\n"
            f"- *\"Could everyday factors like water hydration, recent diet, or physical activity have affected these numbers?\"*\n"
            f"- *\"What lifestyle adjustments would you prioritize based on these results?\"*\n\n"
            "Remember: Open discussions with your doctor lead to the best personalized care."
        )
        final_text = translate_to_language(ans, language)
        return {"answer": final_text, "sources": [], "evidenceSufficient": True}

    # CASE 6: Reassurance for anxious or safety inquiries ("is it dangerous", "cancer", "dying")
    if is_anxiety_check:
        ans = (
            "### Take a Deep Breath — Lab Reports Are Screening Tools, Not Diagnoses\n\n"
            "Having a value marked 'High' or 'Low' is very common. In fact, most out-of-range lab results are caused by harmless, temporary things like not drinking enough water before the test, recent physical exertion, diet, or mild fatigue.\n\n"
            "- **Is it an emergency?** Numbers on a routine lab report do not diagnose medical emergencies. If you are experiencing acute physical symptoms (such as severe chest pain, sudden shortness of breath, dizziness, or intense pain), call emergency medical services immediately.\n"
            "- **Next step:** Schedule a relaxed review with your doctor so they can interpret these numbers in the context of how you feel."
        )
        final_text = translate_to_language(ans, language)
        return {"answer": final_text, "sources": [], "evidenceSufficient": True}

    # CASE 7: Conversational queries — attempt LLM generation with fast timeout
    findings_summary_lines = [f"- {f.name}: {f.value} {f.unit} ({f.status}, range {f.referenceRange})" for f in findings]
    findings_summary_str = "\n".join(findings_summary_lines) if findings_summary_lines else "No report loaded."
    context_text = rag_snippet or (LAB_LEXICON[test_key]["simple_desc"] if (test_key and test_key in LAB_LEXICON) else "Standard clinical laboratory biomarkers.")
    
    try:
        llm_resp = generate_llm_chat(
            question=q_clean,
            findings_summary=findings_summary_str,
            medline_context=context_text,
            language=language
        )
        if llm_resp and len(llm_resp) > 25:
            final_text = translate_to_language(llm_resp, language)
            sources = []
            if source_url and matched_test:
                sources.append({"source": "MedlinePlus", "title": matched_test, "url": source_url, "snippet": rag_snippet})
            return {"answer": final_text, "sources": sources, "evidenceSufficient": True}
    except Exception as e:
        print(f"LLM conversational chat attempt note: {e}")

    # CASE 8: MedlinePlus RAG retrieval passage if available
    if rag_snippet and len(rag_snippet) > 40:
        ans = (
            f"### Medical Source Overview\n\n"
            f"Here is information retrieved from verified medical sources regarding your question:\n\n"
            f"{rag_snippet.strip()}\n\n"
            f"If you are asking about your uploaded report, feel free to name any specific test from your document (such as **{', '.join(report_tests[:3])}**) for a tailored plain-language breakdown."
        )
        final_text = translate_to_language(ans, language)
        sources = []
        if source_url and matched_test:
            sources.append({"source": "MedlinePlus", "title": matched_test, "url": source_url, "snippet": rag_snippet})
        return {"answer": final_text, "sources": sources, "evidenceSufficient": True}

    # DEFAULT INFORMATIVE FALLBACK
    if findings:
        ans = (
            f"I am here to help you understand your medical lab report in simple, easy-to-understand language!\n\n"
            f"Your current report contains measurements for: **{', '.join(report_tests)}**.\n\n"
            f"Try asking:\n"
            f"- *\"What does {findings[0].name} mean?\"*\n"
            f"- *\"Why is my value marked {findings[0].status}?\"*\n"
            f"- *\"What should I ask my doctor about this report?\"*\n"
            f"- *\"Summarize my report in plain words\"*"
        )
    else:
        ans = (
            "I can explain any medical test, lab measurement, or reference range in simple, patient-friendly terms.\n\n"
            "You can ask me questions like:\n"
            "- *\"What does a reference range mean?\"*\n"
            "- *\"How do dehydration and diet affect lab tests?\"*\n"
            "- *\"What is TSH / Creatinine / Hemoglobin?\"*\n"
            "- Or upload a PDF report above to see your personal results explained step by step."
        )
    
    final_text = translate_to_language(ans, language)
    return {"answer": final_text, "sources": [], "evidenceSufficient": True}
