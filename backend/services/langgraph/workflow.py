import json
from typing import Dict, Any, List, TypedDict, Literal
from langgraph.graph import StateGraph, START, END

from backend.services.llm.groq_client import get_llm_response
from backend.services.analysis.pandas_engine import PandasEngine
from backend.services.rag.pdf_engine import PDFEngine
import os

# backend/services/langgraph/workflow.py -> 3 levels up is ai-bi-copilot
# 1: dirname = langgraph
# 2: dirname = services
# 3: dirname = backend
# 4: dirname = ai-bi-copilot
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
pandas_engine = PandasEngine(DATA_DIR)
pdf_engine = PDFEngine(DATA_DIR)

# Define the State for the Langgraph
class AgentState(TypedDict):
    query: str
    intent: str
    target_files: List[str]
    context: str # data from pandas/pdf
    analysis_result: Any
    charts: List[Dict[str, Any]]
    insight: str
    final_response: str
    error: str

def parse_and_classify_intent(state: AgentState) -> AgentState:
    """Determine what the user wants to do and which file to use."""
    query = state["query"]
    available_files = os.listdir(DATA_DIR) if os.path.exists(DATA_DIR) else []
    
    print("\n" + "="*50)
    print(f"[NODE: parse_intent] Received query: {query}")
    print(f"[NODE: parse_intent] Available files: {available_files}")
    
    prompt = f"""
    You are an AI Business Intelligence intent classifier. 
    User Query: "{query}"
    Available files in context: {available_files}
    
    Determine:
    1. The intent of the query: 
       - 'data_analysis' for general structured numbers/CSVs.
       - 'document_qa' for PDFs/text.
       - 'root_cause_analysis' if the user asks "why" something happened, asking for the driving factors of a drop/increase.
       - 'build_dashboard' if the user explicitly asks to build or create a dashboard.
       - 'general_chat' for unknown/casual greetings.
    2. Which file(s) are most likely needed to answer this.
    2. Which file(s) are most likely needed to answer this.
    
    Return pure JSON, strictly in this format:
    {{
        "intent": "data_analysis",
        "target_files": ["file1.csv"]
    }}
    IMPORTANT: You must output ONLY valid JSON. Use double quotes for keys and values. Do not output markdown fences or conversational text.
    """
    
    try:
        response = get_llm_response(prompt, temperature=0.0)
        print(f"[NODE: parse_intent] Raw LLM Response:\n{response}")
        
        # Clean up common LLM markdown wrapper issues
        json_str = response.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        
        json_str = json_str.strip()
        
        # Fallback to extract just the JSON object
        start_idx = json_str.find("{")
        end_idx = json_str.rfind("}") + 1
        if start_idx != -1 and end_idx != 0:
            json_str = json_str[start_idx:end_idx]
            
        parsed = json.loads(json_str)
        print(f"[NODE: parse_intent] Parsed JSON Successfully: {parsed}")
        
        state["intent"] = parsed.get("intent", "general_chat")
        state["target_files"] = parsed.get("target_files", [])
    except Exception as e:
        print(f"[NODE: parse_intent] ERROR parsing intent: {str(e)}")
        state["intent"] = "general_chat"
        state["error"] = f"Failed to parse intent. Raw LLM output: '{response}'. Error: {str(e)}"
        
    return state

def route_by_intent(state: AgentState) -> Literal["retrieve_pdf", "process_csv", "root_cause_csv", "build_dashboard_csv", "general_reply"]:
    intent = state.get("intent", "general_chat")
    if intent == "document_qa":
        return "retrieve_pdf"
    elif intent == "root_cause_analysis":
        return "root_cause_csv"
    elif intent == "build_dashboard":
        return "build_dashboard_csv"
    elif intent == "data_analysis":
        return "process_csv"
    else:
        return "general_reply"

from backend.services.visualization.chart_engine import visualization_engine

def process_csv_node(state: AgentState) -> AgentState:
    """Generates Python code to run on Pandas based on the query."""
    files = state.get("target_files", [])
    if not files:
        state["error"] = "No target file identified for data analysis."
        return state
        
    target_file = files[0]
    profile = pandas_engine.get_profile(target_file)
    
    if "error" in profile:
        state["error"] = profile["error"]
        return state
        
    code_prompt = f"""
    You are a data analyst. Write a python function `analyze(df)` that extracts data from pandas based on this query: "{state['query']}"
    The dataframe profile:
    Columns: {profile.get('columns')}
    Types: {profile.get('dtypes')}
    Sample: {profile.get('sample_data')}
    
    The function MUST return a dictionary mapping keys to values.
    CRITICAL RULES:
    1. DO NOT import matplotlib, seaborn, or plotly. 
    2. DO NOT write code to plot or visualize. You are ONLY extracting data. The application handles plotting elsewhere.
    3. Even if the user asks to "visualize", just return the dictionary of the data they want to see.
    4. If there are too many rows, group them or get the top 10.
    5. If analyzing multiple things (e.g. by region AND by category), return a dictionary of dictionaries, e.g {{'by_region': {{...}}, 'by_category': {{...}}}}
    
    Example: 
    def analyze(df):
        return df.groupby('Region')['Revenue'].sum().to_dict()
        
    Return ONLY the python code, DO NOT wrap it in markdown block quotes (no ```python).
    """
    
    generated_code = get_llm_response(code_prompt, temperature=0.0)
    generated_code = generated_code.replace("```python", "").replace("```", "").strip()
    
    print(f"\n[NODE: process_csv] Generated Python Code:\n{generated_code}")
    
    result = pandas_engine.execute_python_code(target_file, generated_code)
    print(f"[NODE: process_csv] Python Execution Result:\n{result}")
    
    state["analysis_result"] = result
    state["context"] = str(result)
    
    return state

def root_cause_csv_node(state: AgentState) -> AgentState:
    """Specialized node to find the driving factors (Why something happened)."""
    files = state.get("target_files", [])
    if not files:
        state["error"] = "No target file identified for root cause analysis."
        return state
        
    target_file = files[0]
    profile = pandas_engine.get_profile(target_file)
    if "error" in profile:
        state["error"] = profile["error"]
        return state
        
    code_prompt = f"""
    You are an expert Data Scientist performing Root Cause Analysis.
    User asks: "{state['query']}"
    The dataframe profile:
    Columns: {profile.get('columns')}
    Types: {profile.get('dtypes')}
    Sample: {profile.get('sample_data')}
    
    Write a python function `analyze(df)` that identifies the TOP contributing factors to the metric mentioned.
    For example, if the user asks "Why did sales drop?", calculate the total drop, then group by dimension (e.g. Region, Category) to find which specific region/category had the largest negative difference.
    
    Return a python dictionary containing the ranked causes and their contribution. 
    Format example: {{'Root Causes': {{'West Region': -1000, 'Furniture': -500}}}}
    
    DO NOT import plotting libraries. Return ONLY the python code, no markdown wrappers.
    """
    
    generated_code = get_llm_response(code_prompt, temperature=0.0).replace("```python", "").replace("```", "").strip()
    result = pandas_engine.execute_python_code(target_file, generated_code)
    
    state["analysis_result"] = result
    state["context"] = str(result)
    return state

def build_dashboard_csv_node(state: AgentState) -> AgentState:
    """Specialized node to generate a multi-view dashboard dictionary."""
    files = state.get("target_files", [])
    if not files:
        state["error"] = "No target file identified for dashboard building."
        return state
        
    target_file = files[0]
    profile = pandas_engine.get_profile(target_file)
    if "error" in profile:
        state["error"] = profile["error"]
        return state
        
    code_prompt = f"""
    You are an AI Dashboard Builder.
    User asks: "{state['query']}"
    The dataframe profile:
    Columns: {profile.get('columns')}
    Types: {profile.get('dtypes')}
    Sample: {profile.get('sample_data')}
    
    Write a python function `analyze(df)` that extracts at least 3 distinct, valuable views (e.g. Trend over time, Breakdown by Category, Comparison by Region) relevant to the query.
    
    MUST return a nested dictionary. Example:
    {{
        'Trend': df.groupby('Date')['Revenue'].sum().to_dict(),
        'By Region': df.groupby('Region')['Revenue'].sum().to_dict(),
        'By Category': df.groupby('Category')['Revenue'].sum().to_dict()
    }}
    
    DO NOT import plotting libraries. Return ONLY the python code, no markdown wrappers.
    """
    
    generated_code = get_llm_response(code_prompt, temperature=0.0).replace("```python", "").replace("```", "").strip()
    result = pandas_engine.execute_python_code(target_file, generated_code)
    
    state["analysis_result"] = result
    state["context"] = "Generated dashboard data with multiple views."
    return state

def generate_chart_node(state: AgentState) -> AgentState:
    """Explicit visualization node that converts analysis results into Plotly charts."""
    result = state.get("analysis_result")
    files = state.get("target_files", [])
    target_file = files[0] if files else "Data"
    
    state["charts"] = []
    
    print("\n[NODE: generate_chart] Evaluating if charts can be generated...")
    
    if isinstance(result, dict) and len(result) > 0 and "error" not in result:
        datasets_to_plot = []
        
        # Check if nested (multiple charts)
        is_nested = any(isinstance(v, (dict, list)) for v in result.values())
        if is_nested:
            print("[NODE: generate_chart] Nested dict detected - generating multiple charts.")
            for name, data_dict in result.items():
                if isinstance(data_dict, (dict, list)) and len(data_dict) > 0:
                    datasets_to_plot.append((f"Analysis of {name} from {target_file}", data_dict))
        elif isinstance(result, dict) and len(result) >= 1:
            datasets_to_plot.append((f"Analysis of {target_file}", result))
            
        for title, data_to_plot in datasets_to_plot:
            chart_prompt = f"Given this data {data_to_plot}, what chart type is best: bar, line, pie, scatter, or kpi? A 'pie' chart is good for percentages/proportions. A 'kpi' is best if the data is just a single number or a single highly important metric. Respond with just the word."
            chart_type = get_llm_response(chart_prompt, max_tokens=10).strip().lower()
            if chart_type not in ["bar", "line", "pie", "scatter", "kpi"]:
                chart_type = "bar"
                
            chart_config = visualization_engine.generate_chart_config(
                df_dict=data_to_plot, 
                chart_type=chart_type, 
                x_col="Category", 
                y_col="Value",
                title=str(title).replace("_", " ").title()
            )
            
            if chart_config:
                state["charts"].append({
                    "type": chart_type,
                    "data": chart_config.get("data", []),
                    "layout": chart_config.get("layout", {})
                })
                print(f"[NODE: generate_chart] Chart generated successfully ({chart_type}) for {title}")
            else:
                print(f"[NODE: generate_chart] Chart config generation failed for {title}")
                
    else:
        print("[NODE: generate_chart] Result is not chartable (either an error, scalar, or not a dict).")
            
    return state

def retrieve_pdf_node(state: AgentState) -> AgentState:
    """Uses FAISS to retrieve context from the PDF."""
    files = state.get("target_files", [])
    if not files:
        state["error"] = "No target file identified for document QA."
        return state
        
    target_file = files[0]
    context = pdf_engine.retrieve(state["query"], target_file)
    state["context"] = context
    state["analysis_result"] = {"retrieved_context": context}
    
    return state

def generate_insights_and_response(state: AgentState) -> AgentState:
    """Synthesizes the final answer using the context retrieved/computed."""
    if state.get("error"):
        state["final_response"] = f"I encountered an error: {state['error']}"
        return state

    prompt = f"""
    You are a helpful AI Business Intelligence Copilot.
    The user asked: "{state['query']}"
    
    Here is the data/context retrieved to answer the question:
    {state.get('context')}
    
    Provide a clear, concise, and professional explanation answering their query based strictly on the provided context. If the context is numbers from a CSV analysis, explain what they mean.
    
    DECISION RECOMMENDATION ENGINE:
    If the data analysis reveals a problem, a negative trend, or a significant drop, you MUST provide a separate 'Recommendations' bulleted section with actionable, concrete business steps to address it.
    If the data shows positive performance, suggest how to capitalize on it.
    """
    
    response = get_llm_response(prompt, temperature=0.7)
    state["final_response"] = response
    state["insight"] = "Analysis complete." # Simplified insight extraction
    
    return state
    
def build_workflow() -> StateGraph:
    """Builds and compiles the LangGraph execution flow."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("parse_intent", parse_and_classify_intent)
    workflow.add_node("process_csv", process_csv_node)
    workflow.add_node("root_cause_csv", root_cause_csv_node)
    workflow.add_node("build_dashboard_csv", build_dashboard_csv_node)
    workflow.add_node("generate_chart", generate_chart_node)
    workflow.add_node("retrieve_pdf", retrieve_pdf_node)
    workflow.add_node("generate_response", generate_insights_and_response)
    
    # Trivial node for general replies
    def general_reply(state: AgentState):
        state["final_response"] = "I can only answer questions related to uploaded CSVs and PDFs."
        return state
    workflow.add_node("general_reply", general_reply)
    
    # Add edges
    workflow.add_edge(START, "parse_intent")
    
    workflow.add_conditional_edges(
        "parse_intent",
        route_by_intent,
        {
            "retrieve_pdf": "retrieve_pdf",
            "process_csv": "process_csv",
            "root_cause_csv": "root_cause_csv",
            "build_dashboard_csv": "build_dashboard_csv",
            "general_reply": "general_reply"
        }
    )
    
    # Chain explicit visualization tool after any CSV processing
    workflow.add_edge("process_csv", "generate_chart")
    workflow.add_edge("root_cause_csv", "generate_chart")
    workflow.add_edge("build_dashboard_csv", "generate_chart")
    
    workflow.add_edge("generate_chart", "generate_response")
    
    workflow.add_edge("retrieve_pdf", "generate_response")
    workflow.add_edge("general_reply", END)
    workflow.add_edge("generate_response", END)
    
    # Compile
    app = workflow.compile()
    return app

# Initialize the global agent graph
agent_graph = build_workflow()
