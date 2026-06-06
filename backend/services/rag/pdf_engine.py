import os
import fitz  # PyMuPDF
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Since we don't have an explicit OpenAI API key, we will use a local HuggingFace embedding model for FAISS
# Or we can use Groq to embed if Groq supports it, but standard local embeddings are easier and free.
from langchain_community.embeddings import HuggingFaceEmbeddings

class PDFEngine:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_stores = {} # mapped by filename
        
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return ""
            
    def ingest_pdf(self, filename: str) -> bool:
        """Ingest a PDF, chunk it, and store into a FAISS vector store."""
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path) or not filename.endswith('.pdf'):
            return False
            
        text = self.extract_text_from_pdf(file_path)
        if not text:
            return False
            
        docs = [Document(page_content=text, metadata={"source": filename})]
        chunks = self.text_splitter.split_documents(docs)
        
        # Create Vector Store
        try:
            vector_store = FAISS.from_documents(chunks, self.embeddings)
            self.vector_stores[filename] = vector_store
            
            # Optionally save locally
            vector_str_dir = os.path.join(self.data_dir, f"{filename}_vectorstore")
            vector_store.save_local(vector_str_dir)
            
            return True
        except Exception as e:
            print(f"Error ingesting into FAISS: {e}")
            return False
            
    def retrieve(self, query: str, filename: str, k: int = 4) -> str:
        """Retrieve relevant context for a query given a specific PDF."""
        # Try to load if not in memory
        if filename not in self.vector_stores:
            vector_str_dir = os.path.join(self.data_dir, f"{filename}_vectorstore")
            if os.path.exists(vector_str_dir):
                self.vector_stores[filename] = FAISS.load_local(
                    vector_str_dir, 
                    self.embeddings,
                    allow_dangerous_deserialization=True # required since we are confident in the source
                )
            else:
                success = self.ingest_pdf(filename)
                if not success:
                    return "No context could be loaded for this document."
                    
        vector_store = self.vector_stores[filename]
        docs = vector_store.similarity_search(query, k=k)
        
        context = "\n\n".join([doc.page_content for doc in docs])
        return context

# pdf_engine = PDFEngine(DATA_DIR)
