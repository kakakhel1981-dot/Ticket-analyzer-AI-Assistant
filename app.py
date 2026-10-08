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
    # Read key from Streamlit Secrets or environment variable
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
st.sidebar.info("💡 **Free Tier Note:** Groq provides a free API tier with high daily request limits. Create a free key at `console.groq.com` to run without costs.")

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
