import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional

# Premium Vibrance Palette
VIBRANT_PALETTE = ["#00DBDE", "#FC00FF", "#00f2fe", "#4facfe", "#667eea", "#764ba2", "#ff9a9e", "#fad0c4"]


class VisualizationEngine:
    def __init__(self):
        pass
        
    def generate_chart_config(self, df_dict: Dict[str, Any], chart_type: str, x_col: str, y_col: str, title: str = "") -> Optional[Dict[str, Any]]:
        """
        Generates a Plotly JSON configuration from an aggregated dictionary/dataframe.
        The frontend will render this config natively using streamlit-plotly.
        """
        try:
            # Reconstruct dataframe from result dictionary if possible
            if isinstance(df_dict, dict):
                # Simple single-row dict -> bar chart of keys and values
                if len(df_dict) > 0 and all(isinstance(v, (int, float)) for v in df_dict.values()):
                    df = pd.DataFrame(list(df_dict.items()), columns=[x_col, y_col])
                else:
                    df = pd.DataFrame(df_dict)
                    # Reset index so we can plot string indices
                    if not df.empty and df.index.name is None and str(df.index.dtype) == 'object':
                        df = df.reset_index().rename(columns={"index": x_col})
            elif isinstance(df_dict, list):
                df = pd.DataFrame(df_dict)
            else:
                df = df_dict
                
            # If x_col or y_col is missing in dataframe, try to intelligently assign them
            if x_col not in df.columns or y_col not in df.columns:
                num_cols = df.select_dtypes(include='number').columns.tolist()
                cat_cols = df.select_dtypes(exclude='number').columns.tolist()
                
                # Pick best x
                if x_col not in df.columns:
                    x_col = cat_cols[0] if cat_cols else df.columns[0]
                    
                # Pick best y
                if y_col not in df.columns:
                    # Avoid picking the same column as y
                    if x_col in num_cols:
                        num_cols.remove(x_col)
                    y_col = num_cols[0] if num_cols else df.columns[1] if len(df.columns) > 1 else x_col
                
            if chart_type == "bar":
                fig = px.bar(df, x=x_col, y=y_col, color=x_col, title=title, template="plotly_dark", color_discrete_sequence=VIBRANT_PALETTE)
            elif chart_type == "line":
                fig = px.line(df, x=x_col, y=y_col, title=title, template="plotly_dark", color_discrete_sequence=VIBRANT_PALETTE)
                fig.update_traces(line=dict(width=3, color=VIBRANT_PALETTE[0])) # Ensure line is thick and bold
            elif chart_type == "pie":
                fig = px.pie(df, names=x_col, values=y_col, title=title, template="plotly_dark", color_discrete_sequence=VIBRANT_PALETTE)
            elif chart_type == "scatter":
                fig = px.scatter(df, x=x_col, y=y_col, color=x_col, title=title, template="plotly_dark", color_discrete_sequence=VIBRANT_PALETTE)
            elif chart_type == "kpi":
                val = df[y_col].iloc[0] if y_col in df.columns and len(df) > 0 else 0
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    pass
                fig = go.Figure(go.Indicator(
                    mode="number",
                    value=val,
                    number={'prefix': "$", 'font': {'color': '#00DBDE', 'size': 50}},
                    title={"text": title, 'font': {'color': 'white', 'size': 20}}
                ))
                fig.update_layout(template="plotly_dark")
            else:
                # Default back to bar
                fig = px.bar(df, x=x_col, y=y_col, title=title, template="plotly_dark", color_discrete_sequence=VIBRANT_PALETTE)
                
            fig.update_layout(
                font=dict(family="Inter, sans-serif", size=14, color="#FFFFFF"), # Pure white font
                title_font=dict(size=22, family="Inter, sans-serif", color="white"),
                margin=dict(l=40, r=40, t=80, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#FFFFFF")), # Pure white axes
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color="#FFFFFF"))
            )
            
            # Convert to dict for JSON serialization over the API
            return json.loads(fig.to_json())
            
        except Exception as e:
            print(f"Error generating chart: {e}")
            return None

visualization_engine = VisualizationEngine()
