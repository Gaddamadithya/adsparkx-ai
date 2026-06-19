import os
import json
import numpy as np
import faiss
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from src import config

class LocalRAGPipeline:
    def __init__(self, db_dir=None):
        self.db_dir = db_dir or config.CHROMA_DB_DIR
        os.makedirs(self.db_dir, exist_ok=True)
        
        self.index_path = os.path.join(self.db_dir, "faiss.index")
        self.metadata_path = os.path.join(self.db_dir, "metadata.json")
        
        self.api_key = config.GEMINI_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            
        self.dimension = 768  # Default fallback, updated dynamically on first embedding
        self.index = None
        self.metadata = []
        
        # Load FAISS index if it exists on disk
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                self.dimension = self.index.d
            except Exception as e:
                print(f"Error loading FAISS database: {e}. Reinitializing.")
                self._reinitialize_db()
        else:
            self._reinitialize_db()

    def _reinitialize_db(self):
        self.index = None
        self.metadata = []

    def get_total_chunks(self) -> int:
        """Returns the total number of indexed chunks."""
        return self.index.ntotal if self.index is not None else 0

    def get_embedding(self, text: str) -> list:
        """Call Gemini Embedding model (default: gemini-embedding-001)."""
        if not self.client:
            # Return a mock normalized vector based on dimension
            import math
            mock_vec = []
            for i in range(self.dimension):
                mock_vec.append(math.sin(i + len(text)) * 0.05)
            vec = np.array(mock_vec, dtype="float32")
            faiss.normalize_L2(vec.reshape(1, -1))
            return vec.tolist()

        response = self.client.models.embed_content(
            model=config.EMBEDDING_MODEL,
            contents=text
        )
        return response.embeddings[0].values

    def parse_pdf(self, file_path: str) -> list:
        """Parses a PDF file page-by-page, returning list of dictionaries with text and page numbers."""
        reader = PdfReader(file_path)
        pages_content = []
        for idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages_content.append({
                    "text": text,
                    "page_number": idx + 1
                })
        return pages_content

    def ingest_directory(self, data_dir="data"):
        """Scans the data directory, parses all TXT, MD, and PDF files, and indexes them in FAISS."""
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            return 0
            
        supported_extensions = ['.txt', '.md', '.pdf']
        files_to_process = [
            f for f in os.listdir(data_dir) 
            if os.path.splitext(f)[1].lower() in supported_extensions
        ]
        
        total_chunks = 0
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE, 
            chunk_overlap=config.CHUNK_OVERLAP
        )

        for filename in files_to_process:
            file_path = os.path.join(data_dir, filename)
            doc_name = filename
            
            if filename.endswith('.pdf'):
                pages_data = self.parse_pdf(file_path)
                for page_data in pages_data:
                    page_text = page_data["text"]
                    page_num = page_data["page_number"]
                    
                    chunks = splitter.split_text(page_text)
                    for chunk_idx, chunk in enumerate(chunks):
                        embedding = self.get_embedding(chunk)
                        
                        # Initialize index on the fly based on the first vector's actual length
                        if self.index is None:
                            self.dimension = len(embedding)
                            self.index = faiss.IndexFlatIP(self.dimension)
                        
                        # Add to FAISS index
                        vector = np.array(embedding, dtype="float32").reshape(1, -1)
                        faiss.normalize_L2(vector)
                        self.index.add(vector)
                        
                        self.metadata.append({
                            "id": f"{doc_name}_p{page_num}_c{chunk_idx}",
                            "source": doc_name,
                            "chunk_index": chunk_idx,
                            "page": str(page_num),
                            "text": chunk
                        })
                        total_chunks += 1
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                chunks = splitter.split_text(content)
                for chunk_idx, chunk in enumerate(chunks):
                    embedding = self.get_embedding(chunk)
                    
                    # Initialize index on the fly based on the first vector's actual length
                    if self.index is None:
                        self.dimension = len(embedding)
                        self.index = faiss.IndexFlatIP(self.dimension)
                    
                    # Add to FAISS index
                    vector = np.array(embedding, dtype="float32").reshape(1, -1)
                    faiss.normalize_L2(vector)
                    self.index.add(vector)
                    
                    self.metadata.append({
                        "id": f"{doc_name}_c{chunk_idx}",
                        "source": doc_name,
                        "chunk_index": chunk_idx,
                        "page": "N/A",
                        "text": chunk
                    })
                    total_chunks += 1
                    
        # Write to disk
        if self.index is not None:
            self.save_database()
        return total_chunks

    def save_database(self):
        """Saves FAISS index and metadata to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=4)

    def reset_database(self):
        """Clears all entries in the FAISS vector database and resets local index files."""
        self._reinitialize_db()
        if os.path.exists(self.index_path):
            try:
                os.remove(self.index_path)
            except Exception:
                pass
        if os.path.exists(self.metadata_path):
            try:
                os.remove(self.metadata_path)
            except Exception:
                pass

    def retrieve_context(self, query: str, top_k: int = 3) -> list:
        """Retrieves top-k relevant document chunks for the query from the FAISS database."""
        if self.index is None or self.index.ntotal == 0:
            return []
            
        query_vector = self.get_embedding(query)
        q_vec = np.array(query_vector, dtype="float32").reshape(1, -1)
        faiss.normalize_L2(q_vec)
        
        # Search index
        scores, indices = self.index.search(q_vec, top_k)
        
        retrieved_items = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            
            # The score from IndexFlatIP with normalized vectors is exactly Cosine Similarity
            similarity_score = float(score)
            
            retrieved_items.append({
                "text": meta["text"],
                "source": meta["source"],
                "page": meta["page"],
                "score": round(max(0.0, min(1.0, similarity_score)), 4)
            })
        return retrieved_items
