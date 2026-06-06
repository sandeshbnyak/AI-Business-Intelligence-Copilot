import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.models.api_models import ChatRequest, ChatResponse
from backend.services.analysis.pandas_engine import PandasEngine
from backend.services.llm.groq_client import get_llm_response
import json

app = FastAPI(title="AI BI Copilot API", description="Conversational BI platform API")

# Setup CORS for the Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "AI BI Copilot API is running"}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Endpoint to upload files (CSV, PDF) for analysis.
    """
    uploaded_files = []
    
    for file in files:
        if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx") or file.filename.endswith(".pdf")):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not supported. Upload CSV, Excel, or PDF.")
            
        file_path = os.path.join(DATA_DIR, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(file.filename)
            
            # TODO: Trigger ingestion/processing for this file
            # Phase 2 Data Engine will be hooked up here
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not upload {file.filename}: {str(e)}")
            
    return {"message": f"Successfully uploaded {len(uploaded_files)} files.", "files": uploaded_files}

from backend.services.langgraph.workflow import agent_graph

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main endpoint for asking analytical questions.
    """
    # Initialize the state
    initial_state = {
        "query": request.query,
        "intent": "",
        "target_files": [],
        "context": "",
        "analysis_result": None,
        "charts": [],
        "insight": "",
        "final_response": "",
        "error": ""
    }
    
    try:
        # Run through LangGraph
        result_state = agent_graph.invoke(initial_state)
        
        # Check for error
        if result_state.get("error"):
            return ChatResponse(
                text=f"Error executing query: {result_state['error']}",
                chart=None,
                insight=None
            )
            
        return ChatResponse(
            text=result_state.get("final_response", "I could not generate an answer."),
            charts=result_state.get("charts", []),
            insight=result_state.get("insight")
        )
    except Exception as e:
        return ChatResponse(
            text=f"System error: {str(e)}",
            chart=None,
            insight=None
        )

# Global insights cache so we don't spam the LLM on every page load
INSIGHTS_CACHE = []

@app.get("/insights")
def get_auto_insights():
    """
    Automatically generate an insight feed from the available data.
    Returns cached insights to reduce latency and API calls, unless cache is empty.
    """
    global INSIGHTS_CACHE
    if INSIGHTS_CACHE:
        return {"insights": INSIGHTS_CACHE}
        
    available_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv") or f.endswith(".xlsx")]
    if not available_files:
        return {"insights": []}
        
    # Analyze the first file for automatic insights
    target_file = available_files[0]
    pandas_engine = PandasEngine(DATA_DIR)
    profile = pandas_engine.get_profile(target_file)
    
    if "error" in profile:
        return {"insights": [{"title": "Data Error", "description": "Could not profile uploaded data."}]}
        
    prompt = f"""
    You are an AI Business Analyst. Look at this data profile:
    Columns: {profile.get('columns')}
    Sample: {profile.get('sample_data')}
    
    Identify 3 highly valuable, hypothetical or data-driven insights/trends you might expect from this data.
    Format your response EXACTLY as a JSON list of dictionaries:
    [
        {{"title": "Short catchy title", "description": "1 sentence description."}},
        {{"title": "Another title", "description": "Another description."}}
    ]
    DO NOT wrap in ```json or markdown.
    """
    
    try:
        response = get_llm_response(prompt, temperature=0.7)
        # Attempt to parse json list
        json_str = response.strip()
        if json_str.startswith("```json"): json_str = json_str[7:]
        if json_str.startswith("```"): json_str = json_str[3:]
        if json_str.endswith("```"): json_str = json_str[:-3]
        
        insights = json.loads(json_str.strip())
        if isinstance(insights, list):
            INSIGHTS_CACHE = insights
            return {"insights": insights}
    except Exception as e:
        print(f"Error generating insights: {e}")
        
    return {"insights": []}

@app.post("/clear_cache")
def clear_cache():
    global INSIGHTS_CACHE
    INSIGHTS_CACHE = []
    return {"status": "Cache cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
