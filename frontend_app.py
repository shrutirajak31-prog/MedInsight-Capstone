import streamlit as st
import requests

st.set_page_config(page_title="Medical Report AI", page_icon=":hospital:", layout="wide")

# Custom CSS for a professional look
st.markdown("""
<style>
    .status-high { color: #b91c1c; font-weight: bold; background-color: #fee2e2; padding: 4px 8px; border-radius: 4px; }
    .status-low { color: #b45309; font-weight: bold; background-color: #fef3c7; padding: 4px 8px; border-radius: 4px; }
    .status-normal { color: #15803d; font-weight: bold; background-color: #dcfce7; padding: 4px 8px; border-radius: 4px; }
    .status-unknown { color: #475569; font-weight: bold; background-color: #f1f5f9; padding: 4px 8px; border-radius: 4px; }
    .xai-box { background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 10px; margin-top: 10px; border-radius: 4px; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

st.title("AI Medical Report Understanding System")
st.markdown("Upload a lab report (PDF) to extract results, flag abnormalities, and generate patient-friendly explanations.")

# Sidebar for API status
with st.sidebar:
    st.header("System Architecture")
    st.markdown("- **NLP Engine:** CRF (F1: 0.919)")
    st.markdown("- **Math Engine:** Deterministic Python")
    st.markdown("- **Knowledge Base:** 449 MedlinePlus Articles")
    st.markdown("- **LLM:** Local Phi-3 via Ollama")
    st.markdown("---")
    st.info("The backend FastAPI server must be running on port 8000 for this UI to work.")

# File uploader
uploaded_file = st.file_uploader("Upload Medical Report (PDF or Image)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    if st.button("Analyze Report", type="primary"):
        with st.spinner("Extracting data, calculating math, and generating explanations..."):
            # Send to FastAPI
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post("http://127.0.0.1:8000/analyze", files=files)
                response.raise_for_status()
                data = response.json()
                
                if data["status"] == "success" and data["results"]:
                    st.success(f"Successfully analyzed {len(data['results'])} test results.")
                    
                    for res in data["results"]:
                        # Determine status color
                        status_class = "status-unknown"
                        if "Above" in res["status"]: status_class = "status-high"
                        elif "Below" in res["status"]: status_class = "status-low"
                        elif "Within" in res["status"]: status_class = "status-normal"
                        
                        with st.expander(f"**{res['test_name']}**: {res['value']} {res['unit']} — {res['status']}", expanded=True):
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.markdown(f"**Result:** {res['value']} {res['unit']}")
                                st.markdown(f"**Reference:** {res['reference_range']}")
                                st.markdown(f"<span class='{status_class}'>{res['status']}</span>", unsafe_allow_html=True)
                                
                            with col2:
                                st.markdown("**Patient Explanation:**")
                                st.write(res["explanation"] if res["explanation"] else "Explanation not generated.")
                                
                            # XAI Panel
                            st.markdown(f"""
                            <div class="xai-box">
                                <strong>Explainable AI (XAI) Evidence:</strong><br>
                                <b>Math Proof:</b> <code>{res['xai']['math_proof']}</code><br>
                                <b>Limitation:</b> {res['xai']['limitation']}<br>
                                <b>Source:</b> <a href="{res['xai']['source_url']}" target="_blank">MedlinePlus Trusted Context</a>
                            </div>
                            """, unsafe_allow_html=True)
                            
                elif data["status"] == "success" and not data["results"]:
                    st.warning("No test results could be extracted from this document.")
                else:
                    st.error(f"Error from backend: {data.get('warnings', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Failed to connect to backend. Is FastAPI running? Error: {e}")