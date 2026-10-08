import streamlit as st
import pandas as pd
import os
import json
from groq import Groq
from openai import OpenAI

# Page Config
st.set_page_config(
    page_title="Ticket Insights & Process Flow AI",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Ticket Data Analytics & Root-Cause AI")
st.markdown("Upload your support ticket Excel file to analyze workcodes, discover high-frequency issue patterns, and generate permanent fix strategies.")

# ---------------------------------------------------------
# Sidebar Configuration & API Setup
# ---------------------------------------------------------
st.sidebar.header("🔑 Model & API Configuration")

# Provider Selection
provider = st.sidebar.selectbox(
    "Select LLM Provider",
    ["Groq (Free API Tier Available)", "OpenAI"]
)

api_key = ""
selected_model = ""

if "Groq" in provider:
    default_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    api_key = st.sidebar.text_input("Groq API Key", value=default_key, type="password", help="Get a free key at console.groq.com")
    
    selected_model = st.sidebar.selectbox(
        "Select Groq Model",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "qwen/qwen3-32b"
        ],
        index=0
    )
    provider_type = "Groq"
else:
    default_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    api_key = st.sidebar.text_input("OpenAI API Key", value=default_key, type="password")
    
    selected_model = st.sidebar.selectbox(
        "Select OpenAI Model",
        [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-oss-120b",
            "gpt-oss-20b"
        ],
        index=0
    )
    provider_type = "OpenAI"

st.sidebar.markdown("---")
st.sidebar.info("💡 **Free Tier Note:** Groq provides a free API tier with high daily request limits. Create a free key at console.groq.com to run without costs.")

# Helper function to query the chosen LLM
def query_llm(prompt: str, system_message: str = "You are an expert L2 support analyst and process optimization engineer.") -> str:
    if not api_key:
        st.error(f"Please enter your {provider_type} API Key in the sidebar or Streamlit Secrets.")
        return ""
    
    try:
        if provider_type == "Groq":
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        else:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error calling {provider_type} API: {str(e)}")
        return ""

# ---------------------------------------------------------
# Main Application Logic
# ---------------------------------------------------------
uploaded_file = st.file_uploader("Upload Excel File containing Tickets (.xlsx, .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("File uploaded successfully!")
        
        # Show Data Preview
        with st.expander("📄 Raw Data Preview", expanded=False):
            st.dataframe(df.head(10))
            
        st.markdown("---")
        st.subheader("🛠️ Column Mapping")
        st.write("Select which columns correspond to the key ticket fields:")
        
        col1, col2 = st.columns(2)
        with col1:
            workcode_col = st.selectbox("Select 'WorkCode' Column", options=df.columns)
        with col2:
            description_col = st.selectbox("Select 'Error Description / Summary' Column", options=df.columns)
            
        st.markdown("---")
        
        # TAB NAVIGATION
        tab1, tab2, tab3 = st.tabs(["📌 Workcode Metrics", "🔥 Frequent Issue Cluster Analysis", "⚡ Process Flow AI Solutions"])
        
        # ---------------------------------------------------------
        # TAB 1: Workcode Metrics
        # ---------------------------------------------------------
        with tab1:
            st.subheader("Workcode Distribution & Counts")
            
            workcode_counts = df[workcode_col].astype(str).value_counts().reset_index()
            workcode_counts.columns = [workcode_col, "Count"]
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.dataframe(workcode_counts, use_container_width=True)
            with c2:
                st.bar_chart(data=workcode_counts, x=workcode_col, y="Count")
                
        # ---------------------------------------------------------
        # TAB 2: Frequent Issue Cluster Analysis
        # ---------------------------------------------------------
        with tab2:
            st.subheader("Clustering & Frequent Pattern Identification")
            st.write("Extract samples from descriptions to group recurring bugs and symptoms.")
            
            unique_workcodes = ["ALL"] + list(df[workcode_col].astype(str).unique())
            selected_wc = st.selectbox("Filter analysis by Workcode (Optional):", unique_workcodes)
            
            if selected_wc != "ALL":
                filtered_df = df[df[workcode_col].astype(str) == selected_wc]
            else:
                filtered_df = df
                
            sample_size = st.slider("Number of sample tickets to send for AI analysis:", min_value=10, max_value=200, value=50, step=10)
            
            if st.button("🔍 Run Pattern Clustering"):
                descriptions = filtered_df[description_col].dropna().astype(str).head(sample_size).tolist()
                
                if not descriptions:
                    st.warning("No description data available for the selected selection.")
                else:
                    with st.spinner("Analyzing descriptions with LLM to group common patterns..."):
                        prompt = f"""
                        You are analyzing customer ticket descriptions to find repeating operational or software defects.
                        Below is a list of ticket description samples:
                        
                        {json.dumps(descriptions, indent=2)}
                        
                        Perform the following tasks:
                        1. Group similar tickets into 3-5 distinct "Frequent Issue Clusters".
                        2. Provide an estimated count or percentage impact of each cluster within this sample.
                        3. Clearly detail the exact symptom and error description reported by users for each cluster.
                        4. Identify the root cause category (e.g., UI Defect, Backend Timeout, Missing Validation, User Error).
                        
                        Format the response clearly using markdown headings, bullet points, and tables where appropriate.
                        """
                        
                        cluster_results = query_llm(prompt)
                        if cluster_results:
                            st.session_state["cluster_results"] = cluster_results
                            
            if "cluster_results" in st.session_state:
                st.markdown(st.session_state["cluster_results"])

        # ---------------------------------------------------------
        # TAB 3: Process Flow AI Permanent Fixes
        # ---------------------------------------------------------
        with tab3:
            st.subheader("⚡ Permanent Resolution & Process Improvement AI")
            st.write("Generate actionable engineering solutions, preventative SOP updates, and process flow redesigns to permanently eliminate recurring complaints.")
            
            if "cluster_results" not in st.session_state:
                st.info("💡 Please run the 'Pattern Clustering' analysis in Tab 2 first, or click below to analyze a direct sample.")
                
            specific_issue_input = st.text_area(
                "Optional: Describe a specific recurring issue or paste ticket samples manually:",
                placeholder="e.g., Users facing 'Payment Gateway Timeout 504' when placing orders during peak hours."
            )
            
            if st.button("🚀 Generate Permanent Fix Strategy"):
                context_data = ""
                if specific_issue_input:
                    context_data += f"\nManual User Input Issue Context:\n{specific_issue_input}\n"
                if "cluster_results" in st.session_state:
                    context_data += f"\nClustered Issue Context from Data:\n{st.session_state['cluster_results']}\n"
                    
                if not context_data.strip():
                    sample_descs = df[description_col].dropna().astype(str).head(30).tolist()
                    context_data = f"Sample ticket descriptions:\n{json.dumps(sample_descs)}"

                with st.spinner("Generating Process Flow & Permanent Resolution Blueprint..."):
                    solution_prompt = f"""
                    You are a Principal Process Optimization Specialist and Senior Lead Systems Architect.
                    Based on the following ticket issue patterns:
                    
                    {context_data}
                    
                    Provide a comprehensive **Permanent Fix & Complaint Reduction Plan** containing:
                    
                    ### 1. Root Cause Analysis (RCA)
                    - Identify technical defects vs process failures causing these tickets.
                    
                    ### 2. Immediate Workaround / L1-L2 Mitigation
                    - How support agents should temporarily handle or automate these tickets today.
                    
                    ### 3. Permanent System/Code Fixes
                    - Technical code, database, or infrastructure changes required to prevent recurrence entirely.
                    
                    ### 4. Process Flow Redesign (Before vs After)
                    - Outline the current problematic flow.
                    - Detail the optimized, self-healing, or error-preventing **Target Process Flow**.
                    
                    ### 5. Expected Complaint Reduction & Impact
                    - Estimated reduction in volume (%) and operational cost savings.
                    """
                    
                    solution_output = query_llm(solution_prompt)
                    if solution_output:
                        st.markdown(solution_output)
                        
                        st.download_button(
                            label="📥 Download Action Plan (Markdown)",
                            data=solution_output,
                            file_name="Permanent_Fix_Strategy.md",
                            mime="text/markdown"
                        )

    except Exception as e:
        st.error(f"Error processing the file: {str(e)}")
else:
    st.info("⬆️ Please upload an Excel file to start analyzing your ticket workcodes and issue trends.")
