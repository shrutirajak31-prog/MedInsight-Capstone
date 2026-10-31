# MedInsight: An Explainable, Evidence-Grounded AI Pipeline for Patient-Centric Medical Report Understanding

## 📌 Overview
Medical laboratory reports contain dense terminology and tabular data that are often difficult for patients to interpret. While Large Language Models (LLMs) can simplify this text, they frequently hallucinate numerical values, misstate reference ranges, and generate unsupported diagnostic claims. 

**MedInsight** is a modular, full-stack AI pipeline that solves this by separating the extraction and mathematical assessment phases from natural language generation. It extracts data from noisy OCR scans using a custom Conditional Random Field (CRF) model, evaluates numerical values using deterministic Python logic, grounds explanations using a MedlinePlus RAG database, and generates patient-friendly explanations using a local LLM with strict safety guardrails.

## ✨ Key Features
* **Robust NLP Extraction:** A CRF model trained to extract Tests, Values, Units, and Reference Ranges, achieving a **0.919 F1-score** on degraded OCR scans.
* **Deterministic Math Engine:** Pure Python logic compares patient values against reference ranges (e.g., `165.0 > 100.0`), completely eliminating LLM hallucination on basic arithmetic.
* **RAG Grounding:** Retrieves context from a FAISS vector database built on 449 paragraphs scraped from MedlinePlus (National Library of Medicine).
* **Privacy-First LLM:** Uses a locally hosted **Phi-3** model via Ollama, ensuring sensitive patient data never leaves the machine.
* **Explainable AI (XAI):** A four-layer provenance mechanism exposing extraction bounding boxes, math proofs, source citations, and interpretation limitations to the user.
* **Dual Modes:** A UI toggle that switches explanations between plain English (Patient Mode) and clinical terminology (Doctor Mode).

## 🏗️ System Architecture

*(Note: If you have uploaded your architecture diagram to the repository, replace the link below with `![Architecture](path/to/fig1.png)`)*

The pipeline flows through the following stages:
1. **Document Ingestion:** Extracts text and bounding boxes using PyMuPDF (digital) or EasyOCR (scanned images).
2. **Information Extraction:** CRF sequence labeling identifies medical entities (`TEST`, `VALUE`, `UNIT`, `REF_RANGE`).
3. **Relation Extraction:** Spatial heuristics group entities into `(Test, Value, Unit, Range)` tuples.
4. **Deterministic Assessment:** Python logic calculates the abnormality status (High, Low, Normal).
5. **Evidence Retrieval (RAG):** FAISS retrieves relevant context from MedlinePlus based on the extracted test name.
6. **Language Generation:** A local Phi-3 LLM generates a patient explanation based *only* on the facts and retrieved context.
7. **Provenance Layer:** Evidence (bounding boxes, math proofs, sources) is attached to the final output.

## 🛠️ Technology Stack
* **Backend:** Python, FastAPI, Uvicorn
* **NLP & Machine Learning:** Scikit-Learn (CRF Suite), Hugging Face Transformers (DistilBERT), Sentence-Transformers
* **Document Processing:** PyMuPDF (Digital PDFs), EasyOCR (Scanned Images)
* **Vector Database:** FAISS (Facebook AI Similarity Search)
* **LLM Runtime:** Ollama (Phi-3 model)
* **Frontend:** React (TypeScript + Vite)
* **Prototyping UI:** Streamlit

## 📂 Repository Structure
```text
├── backend/            # FastAPI server, RAG engine, LLM engine, safety guardrails
├── medinsight/         # React UI code
├── src/                # Core NLP engine (OCR, CRF model, Relation extraction)
├── scripts/            # Data generation, evaluation, and ablation scripts
├── data/               # Dataset generation scripts (Data files ignored in Git)
├── checkpoints/        # Trained CRF models (Ignored in Git)
└── requirements.txt    # Python dependencies

🚀 Installation & Setup
Prerequisites
Python 3.10+

Node.js (v18+)

Ollama installed and running locally.

1. Backend Setup (FastAPI + NLP Pipeline)
bash
# Clone the repository
git clone https://github.com/shrutirajak31-prog/MedInsight-Capstone.git
cd MedInsight-Capstone

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn backend.app:app --reload
The API will be available at http://127.0.0.1:8000.

2. Local LLM Setup (Ollama)
Open a new terminal and pull the Phi-3 model to ensure the RAG pipeline can generate explanations:

bash
ollama run phi3
3. Frontend Setup (React)
Open another terminal and run:

bash
# Navigate to the frontend folder
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
The UI will be available at http://localhost:3000.

💻 Generating the Dataset (Optional)
Because the large dataset and trained model weights (.pkl) are ignored by Git to keep the repository lightweight, you can regenerate the 100 synthetic reports and their degraded scans by running:

bash
python scripts/generate_synthetic_report.py
python scripts/make_scanned_versions.py
python scripts/build_dataset.py
📊 Experimental Results
The NLP pipeline was evaluated on a held-out test set across three input conditions:

Method	           Clean PDF F1	        Clean OCR F1	    Degraded OCR F1
Regex Baseline	     1.000	               0.975	             0.853
CRF (Proposed)	     1.000	               1.000	             0.919
DistilBERT	         0.876	               0.886	             0.714
Relation Extraction: Achieved an exact-match Tuple F1 of 0.889 on degraded OCR.

Ablation Study: Removing contextual features (neighboring tokens) from the CRF dropped the F1-score from 0.919 to 0.866, proving that structural context is the primary driver of OCR robustness.

🔍 Explainable AI (XAI)
We explicitly avoid the "black box" nature of LLMs. MedInsight exposes four layers of evidence for every generated explanation:

Extraction Evidence: Bounding box coordinates and OCR confidence scores.

Numerical Evidence: The exact deterministic math proof (e.g., 0.4 <= 1.6 <= 4.0).

Source Evidence: The exact MedlinePlus paragraph and source URL used for RAG.

Limitations: A disclaimer of what the test cannot establish (e.g., a high CRP does not locate inflammation).

👥 Authors
Lucky Jain - B.Tech Artificial Intelligence and Data Science, NMIMS Navi Mumbai
Shruti Rajak - B.Tech Artificial Intelligence and Data Science, NMIMS Navi Mumbai

📜 License
This project is for academic and research purposes. If you use this work, please cite the corresponding research paper (currently under review):

> L. Jain and S. Rajak, "MedInsight: An Explainable, Evidence-Grounded AI Pipeline for Patient-Centric Medical Report Understanding," *submitted to ICTCS 2026*


