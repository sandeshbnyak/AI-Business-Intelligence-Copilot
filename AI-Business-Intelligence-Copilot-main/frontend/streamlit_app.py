import streamlit as st
import requests
import json
import plotly.graph_objects as go

API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI BI Copilot", page_icon="🧠", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

/* Global Styles */
.stApp {
    background: #0E1117;
}

html, body, [class*="css"], .stMarkdown {
    font-family: 'Inter', sans-serif !important;
    color: #FFFFFF !important; /* Pure white for readability */
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-image: linear-gradient(180deg, #1E1E2F 0%, #0E1117 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

[data-testid="stSidebar"] h2, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
    color: #FFFFFF !important;
    font-weight: 600;
}

/* Glassmorphism for Chat Messages */
.stChatMessage {
    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 15px !important;
    padding: 15px !important;
    margin-bottom: 15px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.stChatMessage [data-testid="stMarkdownContainer"] p {
    color: #FFFFFF !important;
    font-size: 1.05rem;
    line-height: 1.6;
}

/* Vivid Title with Glow */
h1 {
    font-weight: 800 !important;
    background: linear-gradient(90deg, #00DBDE 0%, #FC00FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0px 5px 15px rgba(0, 219, 222, 0.2);
    letter-spacing: -0.04em !important;
}

/* Style the file uploader box */
[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px dashed rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    padding: 10px;
}
[data-testid="stFileUploader"] section {
    background: transparent !important;
}
[data-testid="stFileUploader"] label {
    color: #00DBDE !important;
}


/* Glowing Info/Success Boxes */
.stAlert {
    background: rgba(0, 219, 222, 0.1) !important;
    border: 1px solid rgba(0, 219, 222, 0.2) !important;
    color: #00DBDE !important;
    backdrop-filter: blur(5px);
}

/* Button Styling */
.stButton>button {
    background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Business Intelligence Copilot")
st.markdown("Ask your data anything and instantly get charts, insights, and decisions.")

# Fetch auto insights
try:
    insights_resp = requests.get(f"{API_URL}/insights", timeout=5)
    if insights_resp.status_code == 200:
        auto_insights = insights_resp.json().get("insights", [])
        if auto_insights:
            with st.expander("✨ Auto Insight Feed", expanded=True):
                cols = st.columns(len(auto_insights))
                for idx, insight in enumerate(auto_insights):
                    with cols[idx]:
                        st.info(f"**{insight.get('title', 'Insight')}**\n\n{insight.get('description', '')}")
except Exception as e:
    pass # API might not be ready

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for file uploads
with st.sidebar:
    st.header("1. Upload Data")
    uploaded_files = st.file_uploader("Upload CSV or PDF", type=["csv", "pdf", "xlsx"], accept_multiple_files=True)
    if st.button("Process Files"):
        if uploaded_files:
            files = [("files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]
            with st.spinner("Uploading & Indexing..."):
                try:
                    response = requests.post(f"{API_URL}/upload", files=files)
                    if response.status_code == 200:
                        st.success(f"Uploaded {len(uploaded_files)} files successfully!")
                        try:
                            requests.post(f"{API_URL}/clear_cache")
                        except:
                            pass
                        st.rerun() # Refresh the insights feed
                    else:
                        st.error(f"Error: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Connection Error: Is the API running? {e}")
        else:
            st.warning("Please select a file first.")

# Main Chat Interface
for msg_idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "charts" in msg and msg["charts"]:
            charts = msg["charts"]
            if len(charts) > 1:
                cols = st.columns(2)
                for chart_idx, chart_data in enumerate(charts):
                    with cols[chart_idx % 2]:
                        try:
                            fig = go.Figure(data=chart_data.get("data", []), layout=chart_data.get("layout", {}))
                            st.plotly_chart(fig, use_container_width=True, key=f"hist_{msg_idx}_{chart_idx}")
                        except Exception as e:
                            st.error(f"Failed to render chart: {e}")
            else:
                for chart_idx, chart_data in enumerate(charts):
                    try:
                        # Render plotly JSON
                        fig = go.Figure(data=chart_data.get("data", []), layout=chart_data.get("layout", {}))
                        st.plotly_chart(fig, use_container_width=True, key=f"hist_{msg_idx}_{chart_idx}")
                    except Exception as e:
                        st.error(f"Failed to render chart: {e}")

# Chat input
if query := st.chat_input("Ask a question about your data (e.g. 'Show revenue trend')"):
    # Add user msg to state and display
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Call backend API
    with st.spinner("Analyzing..."):
        try:
            payload = {
                "query": query,
                "history": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            }
            response = requests.post(f"{API_URL}/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                bot_text = data.get("text", "No response text.")
                bot_charts = data.get("charts", [])
                
                if bot_charts:
                    bot_text += f"\n\n*(Generated {len(bot_charts)} charts)*"
                
                # Add to state
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": bot_text,
                    "charts": bot_charts
                })
                
                # Display
                with st.chat_message("assistant"):
                    st.markdown(bot_text)
                    if bot_charts:
                        if len(bot_charts) > 1:
                            cols = st.columns(2)
                            for chart_idx, bot_chart in enumerate(bot_charts):
                                with cols[chart_idx % 2]:
                                    try:
                                        fig = go.Figure(data=bot_chart.get("data", []), layout=bot_chart.get("layout", {}))
                                        st.plotly_chart(fig, use_container_width=True, key=f"curr_{len(st.session_state.messages)}_{chart_idx}")
                                    except Exception as e:
                                        st.error(f"Chart render error: {e}")
                        else:
                            for chart_idx, bot_chart in enumerate(bot_charts):
                                try:
                                    fig = go.Figure(data=bot_chart.get("data", []), layout=bot_chart.get("layout", {}))
                                    # Use a key that includes the message count to ensure uniqueness during live updates
                                    st.plotly_chart(fig, use_container_width=True, key=f"curr_{len(st.session_state.messages)}_{chart_idx}")
                                except Exception as e:
                                    st.error(f"Chart render error: {e}")
            else:
                st.error(f"API Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Connection Error: {e}")
