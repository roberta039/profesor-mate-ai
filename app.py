import streamlit as st
import google.generativeai as genai
from PIL import Image
import tempfile # Avem nevoie de asta pentru a manipula PDF-urile temporar

# 1. Configurare Pagină
st.set_page_config(page_title="Profesor Universal (PDF & Vision)", page_icon="📚")
st.title("📚 Profesor Universal")
st.caption("Powered by Gemini 2.5 Flash | Analiză Cărți (PDF) & Probleme (Foto)")

# 2. Configurare API Key
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Introdu Google API Key:", type="password")

if not api_key:
    st.info("Introdu cheia Google API pentru a începe.")
    st.stop()

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Eroare la configurare cheie: {e}")
    st.stop()

# --- INITIALIZARE MODEL ---
FIXED_MODEL_ID = "models/gemini-2.5-flash"

try:
    model = genai.GenerativeModel(
        FIXED_MODEL_ID,
        system_instruction="""Ești un profesor universal (Mate, Fizică, Chimie, Literatură).
        
        SARCINI:
        1. ȘTIINȚE EXACTE (Mate/Fizică): Predă exact ca la școală. Valori exacte, fără aproximări, condiții ideale.
        2. LITERATURĂ/LECTURĂ: Dacă primești un PDF (carte/eseu), fă rezumate structurate, analize de personaje sau extrage ideile principale. Fii un critic literar și un pedagog excelent.
        
        STIL: Răbdător, empatic, clar. Folosește limba română.
        """
    )
except Exception as e:
    st.error(f"Eroare critică: {e}")
    st.stop()

# 3. Interfața de Upload (Modificată pentru PDF)
st.sidebar.header("📁 Materiale")
# Acum acceptăm și PDF
uploaded_file = st.sidebar.file_uploader("Încarcă Poză sau PDF", type=["jpg", "jpeg", "png", "pdf"])

media_content = None # Aici vom stoca fișierul procesat (Poză sau PDF)
file_type = ""

if uploaded_file:
    file_type = uploaded_file.type
    
    if "image" in file_type:
        # Procesare Imagine
        media_content = Image.open(uploaded_file)
        st.sidebar.image(media_content, caption="Imagine încărcată", use_container_width=True)
        
    elif "pdf" in file_type:
        # Procesare PDF (Mai complex)
        st.sidebar.info("📄 PDF Detectat. Se procesează...")
        
        # 1. Salvăm PDF-ul într-un fișier temporar pe disc
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        # 2. Încărcăm fișierul pe serverele Google (File API)
        try:
            with st.spinner("Urc cartea în biblioteca digitală Google..."):
                uploaded_pdf = genai.upload_file(tmp_path, mime_type="application/pdf")
                media_content = uploaded_pdf # Acesta este obiectul pe care îl trimitem la AI
                st.sidebar.success(f"✅ Carte încărcată! ({uploaded_file.name})")
        except Exception as e:
            st.sidebar.error(f"Eroare la upload PDF: {e}")

# 4. Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 5. Input și Logică
if user_input := st.chat_input("Scrie cerința (ex: 'Fă rezumatul cărții')..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # --- CONSTRUIREA MESAJULUI ---
    conversation_payload = []

    # A. Istoric text (context)
    for msg in st.session_state.messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        conversation_payload.append({
            "role": role,
            "parts": [msg["content"]]
        })

    # B. Mesajul curent + Fișierul (dacă există)
    current_parts = [user_input]
    
    if media_content:
        # Verificăm dacă e Poză sau PDF (Google File)
        current_parts.append(media_content)
        
        if "pdf" in file_type:
            display_note = " (Analizez PDF-ul...)"
        else:
            display_note = " (Analizez imaginea...)"
    else:
        display_note = ""

    conversation_payload.append({
        "role": "user",
        "parts": current_parts
    })

    # C. Trimitere
    with st.chat_message("assistant"):
        with st.spinner(f"Profesorul lucrează...{display_note}"):
            try:
                response = model.generate_content(conversation_payload)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Eroare: {e}")
