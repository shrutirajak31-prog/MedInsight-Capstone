import json
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class RAGEngine:
    def __init__(self, data_path="backend/data/medlineplus.json", index_path="backend/data/medlineplus.index"):
        # Load the scraped MedlinePlus data
        with open(data_path, "r", encoding="utf-8") as f:
            self.knowledge = json.load(f)
        
        print("Loading embedding model for RAG...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Extract text and metadata
        self.texts = [item["content"] for item in self.knowledge]
        self.test_names = [item["test_name"] for item in self.knowledge]
        self.source_urls = [item.get("source_url", "MedlinePlus") for item in self.knowledge]
        
        if os.path.exists(index_path):
            print("Loading cached FAISS index...")
            self.index = faiss.read_index(index_path)
            print(f"RAG Engine ready with {self.index.ntotal} cached MedlinePlus documents.")
        else:
            print("Building FAISS index...")
            embeddings = self.model.encode(self.texts, convert_to_numpy=True)
            dimension = embeddings.shape[1]
            
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings.astype(np.float32))
            try:
                faiss.write_index(self.index, index_path)
                print("Saved FAISS index to cache.")
            except Exception as e:
                print(f"Could not cache FAISS index: {e}")
            print(f"RAG Engine ready with {len(self.texts)} MedlinePlus documents.")

    def retrieve(self, query: str) -> dict:
        """Finds the most relevant MedlinePlus text for a given test name."""
        query_vector = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vector.astype(np.float32), 1)
        
        if indices[0][0] != -1:
            best_idx = indices[0][0]
            return {
                "source_text": self.texts[best_idx],
                "source_url": self.source_urls[best_idx],
                "matched_test": self.test_names[best_idx],
            }
        return {"source_text": None, "source_url": None, "matched_test": None}

# Create a singleton instance to be imported by the NLP engine
rag = RAGEngine()
