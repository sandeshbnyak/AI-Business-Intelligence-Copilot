from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class ChatMessage(BaseModel):
    role: str = Field(description="Role of the sender (user, assistant, system)")
    content: str = Field(description="The message content")

class ChatRequest(BaseModel):
    query: str = Field(description="The user's analytical query")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Previous conversation history")
    
class ChartConfig(BaseModel):
    type: str = Field(description="Chart type: bar, line, pie, etc.")
    data: List[Dict[str, Any]] = Field(description="Data for the chart")
    layout: Dict[str, Any] = Field(description="Layout configuration")

class ChatResponse(BaseModel):
    text: str = Field(description="The AI generated response text answering the query")
    charts: Optional[List[ChartConfig]] = Field(default_factory=list, description="Optional list of Plotly chart configurations to render")
    insight: Optional[str] = Field(None, description="Optional distinct key insight identified by the AI")
