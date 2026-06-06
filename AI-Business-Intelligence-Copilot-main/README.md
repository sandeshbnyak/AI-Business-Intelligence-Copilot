# 🧠 AI Business Intelligence Copilot

A powerful, conversational AI platform for business analytics. Transform your raw data (CSV, Excel, PDF) into actionable insights, professional dashboards, and dynamic visualizations using natural language.

---

## Flowchart
<img width="1024" height="1536" alt="flow-chart" src="https://github.com/user-attachments/assets/2e399c69-75de-4a7c-b5a8-a3280f85e4ab" />

---

<img width="1920" height="1080" alt="Screenshot (112)" src="https://github.com/user-attachments/assets/66d85dfe-d221-46d6-a3ea-3e6eac04c8a7" />

## 🚀 Key Features

### 1. **Conversational Data Intelligence**
- **Chat with your Data:** Ask complex questions like *"Show me the revenue trend for 2023"* or *"Compare profit across regions"* and get instant answers.
- **PDF Research (RAG):** Upload unstructured documents (reports, manuals) and query them using a local FAISS-powered retrieval engine.

### 2. **Advanced Visualization Suite**
- **Dynamic Charting:** Automatically generates **Bar, Line, Pie, and Scatter** charts using Plotly.
- **KPI Indicators:** Specifically optimized to display high-level metrics (e.g., Total Revenue, User Count) as bold, stylized KPI cards.
- **Auto-Responsive Layout:** Visualizations are rendered in a clean, 2-column grid for better dashboard density.

### 3. **Specialized Analytical Engines**
- **Root Cause Analysis (RCA):** Go beyond "what" happened and ask "why?". The engine identifies the primary drivers behind drops or spikes in your metrics.
- **Dashboard Builder:** Trigger the creation of multi-view dashboards with a single query like *"Build a sales dashboard."*
- **Auto Insight Feed:** A proactive feed that scans your data upon upload to surface hidden patterns and "News-style" insights immediately.

### 4. **Premium Web Experience**
- **Modern UI:** Built with Streamlit and enhanced with custom **Inter** typography and a sleek dark-themed design system.
- **Interactive Plotly Charts:** All charts are fully interactive, allowing for hover details and zooming.

---

## 🛠️ Technical Stack

- **Orchestration:** [LangGraph](https://github.com/langchain-ai/langgraph) (State-driven workflow routing)
- **Frontend:** Streamlit (Customized with modern CSS & Inter Font)
- **Backend:** FastAPI
- **LLM Engine:** Groq (Llama 3 family for ultra-fast reasoning)
- **Data Processing:** Pandas
- **Vector Store:** FAISS (for PDF RAG)
- **Visuals:** Plotly Express & Graph Objects

---

## 📥 Installation & Setup

### Prerequisites
- Python 3.9+
- A [Groq API Key](https://console.groq.com/)

### Step 1: Clone & Environment
```bash
git clone <your-repo-url>
cd ai-bi-copilot
python -m venv venv
# Activate on Windows:
.\venv\Scripts\activate
# Activate on Mac/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## 🚦 Running the App

You need to run both the Backend API and the Frontend UI.

**Terminal 1 (Backend API):**
```bash
uvicorn backend.main:app --port 8000 --reload
```

**Terminal 2 (Frontend UI):**
```bash
streamlit run frontend/streamlit_app.py
```

---

## 📂 Project Structure

```text
ai-bi-copilot/
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── services/
│   │   ├── analysis/          # Pandas & Data Processing
│   │   ├── langgraph/         # Workflow Orchestration
│   │   ├── rag/               # PDF Retrieval Engine
│   │   └── visualization/     # Plotly Config & KPI Engine
├── frontend/
│   └── streamlit_app.py       # Premium Web UI
├── data/                      # Local file storage/Vector Store
└── requirements.txt
```

<img width="1920" height="1080" alt="Screenshot (113)" src="https://github.com/user-attachments/assets/05f630ca-a43a-4926-b49d-206f88c40f9b" />

```

<img width="1920" height="1080" alt="Screenshot (114)" src="https://github.com/user-attachments/assets/364e877f-f2cb-4454-9fc7-3bd082de57eb" />

```

<img width="1920" height="1080" alt="Screenshot (115)" src="https://github.com/user-attachments/assets/c5e0b9f0-e7f4-4fca-bd12-1a76d87705c9" />



```



---

## 🤝 Contributing
Contributions are welcome! Feel free to open issues or submit pull requests to enhance the visualization engines or LLM prompts.
