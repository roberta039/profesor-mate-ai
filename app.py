import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configurare Pagină
st.set_page_config(page_title="Profesorul de Mate (Manual)", page_icon="📐")
st.title("📐 Proful de Mate - Selectare Manuală")

# 2. Configurare API Key
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Introdu Google API Key:", type="password")

if not api_key:
    st.info("Introdu cheia Google API.")
    st.stop()

# Configurare Google
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Eroare cheie: {e}")

# 3. SELECTOR MANUAL DE MODEL (Fără auto-detecție)
st.sidebar.header("⚙️ Alege Modelul")
st.sidebar.info("Dacă primul nu merge, încearcă-le pe rând.")

# Aici am scris manual cele mai probabile nume de modele care funcționează
model_options = [
    "gemini-1.5-flash",          # Cel mai rapid și nou
    "gemini-1.5-pro",            # Mai deștept, dar mai lent
    "gemini-pro-vision",         # Varianta veche pentru poze
    "models/gemini-1.5-flash",   # Uneori cere prefixul "models/"
]

selected_model = st.sidebar.selectbox("Model:", model_options)

# Inițializăm modelul ales
model = genai.GenerativeModel(
    selected_model,
    system_instruction="""Ești un profesor de matematică. 
    Rezolvă problema din imagine sau text pas cu pas. 
    Explică în limba română."""
)

# 4. Upload Poză
uploaded_file = st.sidebar.file_uploader("Încarcă Poză", type=["jpg", "jpeg", "png"])
img = None
if uploaded_file:
    img = Image.open(uploaded_file)
    st.sidebar.image(img, caption="Imagine încărcată", use_container_width=True)

# 5. Chat
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Salut! Trimite-mi problema."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if user_input := st.chat_input("Scrie aici..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    inputs = [user_input]
    if img:
        inputs.append(img)

    with st.chat_message("assistant"):
        try:
            with st.spinner(f"Încerc cu modelul {selected_model}..."):
                response = model.generate_content(inputs)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Eroare cu modelul {selected_model}:")
            st.code(e)
            st.warning("👈 Încearcă să selectezi alt model din meniul din stânga!")
