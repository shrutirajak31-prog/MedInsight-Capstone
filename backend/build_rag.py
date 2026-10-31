import requests
from bs4 import BeautifulSoup
import json
import time
import os

URLS = {
    "TSH": "https://medlineplus.gov/lab-tests/tsh-thyroid-stimulating-hormone-test/",
    "T4": "https://medlineplus.gov/lab-tests/t4-thyroxine-test/",
    "Total Cholesterol": "https://medlineplus.gov/lab-tests/cholesterol-levels/",
    "Triglycerides": "https://medlineplus.gov/lab-tests/triglycerides-test/",
    "LDL Cholesterol": "https://medlineplus.gov/ldlthebadcholesterol.html",
    "HDL Cholesterol": "https://medlineplus.gov/hdlthegoodcholesterol.html",
    "Hemoglobin": "https://medlineplus.gov/lab-tests/hemoglobin-test/",
    "WBC": "https://medlineplus.gov/lab-tests/white-blood-cell-wbc-count/",
    "RBC": "https://medlineplus.gov/lab-tests/red-blood-cell-rbc-count/",
    "Platelets": "https://medlineplus.gov/lab-tests/platelet-tests/",
    "Creatinine": "https://medlineplus.gov/lab-tests/creatinine-test/",
    "BUN (Urea)": "https://medlineplus.gov/lab-tests/bun-blood-urea-nitrogen/",
    "ALT": "https://medlineplus.gov/lab-tests/alt-blood-test/",
    "AST": "https://medlineplus.gov/lab-tests/ast-blood-test/",
    "Albumin": "https://medlineplus.gov/lab-tests/albumin-blood-test/"
}

def scrape_medlineplus():
    knowledge_base = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for test_name, url in URLS.items():
        print(f"Scraping {test_name}...")
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            content_div = soup.find('div', id='mplus-content') or soup.find('article')
            
            if not content_div:
                continue
                
            paragraphs = content_div.find_all(['p', 'li'])
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                # Stop before the references section
                if "Learn how to cite" in text or "References" in text or text.startswith("Available from:"):
                    break
                
                # Only keep meaningful chunks
                if len(text) > 80:
                    knowledge_base.append({
                        "test_name": test_name,
                        "source_url": url,
                        "content": text
                    })
            print(f"  -> Extracted {len(paragraphs)} paragraphs.")
            
        except Exception as e:
            print(f"  -> Error: {e}")
        
        time.sleep(1)
    
    with open("backend/data/medlineplus.json", "w") as f:
        json.dump(knowledge_base, f, indent=2)
        
    print(f"\nDone! Saved {len(knowledge_base)} paragraphs to backend/data/medlineplus.json")

if __name__ == "__main__":
    scrape_medlineplus()