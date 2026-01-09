import streamlit as st
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# 1. Configurare Pagină
st.set_page_config(page_title="Profesorul de Mate (Gemini)", page_icon="🎓")
st.title("🎓 Proful de Mate - Google Gemini Edition")
st.caption("Rezolvă probleme din poze folosind Gemini 1.5 Flash")

# 2. Configurare API Key (GOOGLE)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Introdu Google API Key:", type="password")
    st.sidebar.markdown("[Obține cheia aici](https://aistudio.google.com/app/apikey)")

if not api_key:
    st.info("Introdu cheia Google API pentru a începe.")
    st.stop()

# 3. Inițializarea Modelului Gemini
# Folosim gemini-1.5-flash care este rapid, gratis și vede poze
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.3
    )
except Exception as e:
    st.error(f"Eroare la conectare: {e}")
    st.stop()

# Funcție helper pentru imagine
def get_image_base64(uploaded_file):
    try:
        return base64.b64encode(uploaded_file.getvalue()).decode()
    except Exception as e:
        st.error(f"Eroare la procesarea imaginii: {e}")
        return None

# 4. Interfața
st.sidebar.header("Încarcă Exercițiul")
uploaded_file = st.sidebar.file_uploader("Poză (JPG/PNG)", type=["jpg", "jpeg", "png"])

image_data = None
if uploaded_file:
    st.sidebar.image(uploaded_file, caption="Imagine încărcată", use_container_width=True)
    image_data = get_image_base64(uploaded_file)
    st.sidebar.success("Imagine pregătită!")

# 5. Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Salut! Încarcă o poză cu o ecuație sau scrie problema și te ajut să o rezolvi."}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 6. Procesare
if user_input := st.chat_input("Scrie aici..."):
    # Afișăm user
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Pregătim mesajul pentru AI
    content_parts = []
    
    # Adăugăm textul utilizatorului
    content_parts.append({"type": "text", "text": user_input})

    # Adăugăm imaginea dacă există
    if image_data:
        content_parts.append({
            "type": "image_url",
            "image_url": f"data:image/jpeg;base64,{image_data}"
        })
        note = " (Analizez și imaginea...)"
    else:
        note = ""

    # Instrucțiunile profesorului
    system_instruction = """Ești un profesor de matematică excelent.
    1. Dacă primești o imagine, identifică problema matematică.
    2. Rezolvă pas cu pas, explicând logica.
    3. Scrie formulele clar (LaTeX).
    4. Răspunde în limba română.
    """
    
    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=content_parts)
    ]

    with st.chat_message("assistant"):
        with st.spinner(f"Profesorul gândește...{note}"):
            try:
                response = llm.invoke(messages)
                st.write(response.content)
                st.session_state.messages.append({"role": "assistant", "content": response.content})
            except Exception as e:
                st.error(f"Eroare: {e}")
