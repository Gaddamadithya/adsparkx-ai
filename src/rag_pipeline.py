import os
from google import genai
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from src import config

class LocalRAGPipeline:
    def __init__(self, db_dir=None):
        self.db_dir = db_dir or config.CHROMA_DB_DIR
        self.api_key = config.GEMINI_API_KEY
        
        # Initialize Gemini Client if key exists
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            
        self.chroma_client = chromadb.PersistentClient(path=self.db_dir)
        # Using cosine distance metric
        self.collection = self.chroma_client.get_or_create_collection(
            name="support_kb",
            metadata={"hnsw:space": "cosine"}
        )

    def get_embedding(self, text: str) -> list:
        """Call Gemini Embedding model text-embedding-004."""
        if not self.client:
            # Return a mock vector of 768 dimensions for fallback/offline testing
            import math
            mock_vec = []
            for i in range(768):
                mock_vec.append(math.sin(i + len(text)) * 0.05)
            return mock_vec

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
        """Scans the data directory, parses all TXT, MD, and PDF files, and indexes them."""
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            return 0
            
        supported_extensions = ['.txt', '.md', '.pdf']
        files_to_process = [
            f for f in os.listdir(data_dir) 
            if os.path.splitext(f)[1].lower() in supported_extensions
        ]
        
        total_chunks = 0
        
        # Splitter config
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE, 
            chunk_overlap=config.CHUNK_OVERLAP
        )

        for filename in files_to_process:
            file_path = os.path.join(data_dir, filename)
            doc_name = filename
            
            if filename.endswith('.pdf'):
                # Handle PDF files page by page to capture metadata
                pages_data = self.parse_pdf(file_path)
                for page_data in pages_data:
                    page_text = page_data["text"]
                    page_num = page_data["page_number"]
                    
                    chunks = splitter.split_text(page_text)
                    for chunk_idx, chunk in enumerate(chunks):
                        embedding = self.get_embedding(chunk)
                        chunk_id = f"{doc_name}_p{page_num}_c{chunk_idx}"
                        
                        self.collection.add(
                            ids=[chunk_id],
                            embeddings=[embedding],
                            metadatas=[{
                                "source": doc_name, 
                                "chunk_index": chunk_idx,
                                "page": str(page_num)
                            }],
                            documents=[chunk]
                        )
                        total_chunks += 1
            else:
                # Handle TXT and MD files
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                chunks = splitter.split_text(content)
                for chunk_idx, chunk in enumerate(chunks):
                    embedding = self.get_embedding(chunk)
                    chunk_id = f"{doc_name}_c{chunk_idx}"
                    
                    self.collection.add(
                        ids=[chunk_id],
                        embeddings=[embedding],
                        metadatas=[{
                            "source": doc_name, 
                            "chunk_index": chunk_idx,
                            "page": "N/A"
                        }],
                        documents=[chunk]
                    )
                    total_chunks += 1
                    
        return total_chunks

    def reset_database(self):
        """Clears all entries in the support_kb vector store collection."""
        try:
            self.chroma_client.delete_collection("support_kb")
        except Exception:
            pass
        self.collection = self.chroma_client.get_or_create_collection(
            name="support_kb",
            metadata={"hnsw:space": "cosine"}
        )

    def retrieve_context(self, query: str, top_k: int = 3) -> list:
        """Retrieves top-k relevant document chunks for the query, calculating confidence scores."""
        query_vector = self.get_embedding(query)
        
        # Verify collection size
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )

        retrieved_items = []
        if results and results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                # Distance represents cosine distance in Chroma when space=cosine.
                # Cosine Distance = 1.0 - Cosine Similarity
                # So Similarity Score = 1.0 - Cosine Distance
                distance = results['distances'][0][i] if results['distances'] else 0.0
                score = 1.0 - distance
                
                retrieved_items.append({
                    "text": results['documents'][0][i],
                    "source": results['metadatas'][0][i]['source'],
                    "page": results['metadatas'][0][i].get('page', 'N/A'),
                    "score": round(max(0.0, min(1.0, score)), 4)
                })
        return retrieved_items
