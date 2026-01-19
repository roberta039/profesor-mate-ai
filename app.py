import streamlit as st
import google.generativeai as genai
from PIL import Image
import tempfile
from gtts import gTTS
from io import BytesIO

# 1. Configurare Pagină
st.set_page_config(page_title="Profesor Liceu AI", page_icon="🎓", layout="wide")

# CSS pentru un aspect mai curat
st.markdown("""
<style>
    .stChatMessage { ensure-font-size: 16px; }
</style>
""", unsafe_allow_html=True)

st.title("🎓 Profesor Liceu - Asistent Virtual")
st.caption("Matematică • Fizică • Chimie • Română | Bazat pe Gemini 1.5 Flash")

# 2. Configurare API Key
# Încearcă să ia cheia din secrets, altfel o cere în sidebar
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Introdu Google API Key:", type="password")

if not api_key:
    st.warning("Te rog introdu cheia API în sidebar pentru a începe.")
    st.stop()

genai.configure(api_key=api_key)

# --- CORECȚIE IMPORTANTĂ: Modelul corect este 1.5-flash ---
FIXED_MODEL_ID = "models/gemini-1.5-flash"

try:
    model = genai.GenerativeModel(
        FIXED_MODEL_ID,
        system_instruction="""Ești un profesor universal (Mate, Fizică, Chimie, Literatură) răbdător și empatic.
        
        REGULĂ STRICTĂ: Predă exact ca la școală (nivel Gimnaziu/Liceu). 
        NU confunda elevul cu detalii despre "aproximări" sau "lumea reală" (frecare, erori) decât dacă problema o cere specific.

        GHID DE COMPORTAMENT:

        1. MATEMATICĂ:
           - Lucrează cu valori exacte. (ex: $\sqrt{2}$ rămâne $\sqrt{2}$, nu 1.41).
           - Nu menționa că $\pi$ e infinit; folosește valorile standard.
           - Folosește LaTeX ($...$) pentru toate formulele.

        2. FIZICĂ/CHIMIE:
           - Presupune automat "condiții ideale" (fără frecare cu aerul, sisteme izolate).
           - Tratează problema exact așa cum apare în culegere.

        3. LIMBA ȘI LITERATURA ROMÂNĂ (CRITIC):
           - Respectă STRICT programa școlară din România și canoanele criticii (G. Călinescu, E. Lovinescu, T. Vianu).
           - ATENȚIE MAJORA: Ion Creangă (Harap-Alb) este Basm Cult, dar specificul lui este REALISMUL (umanizarea fantasticului, oralitatea), nu romantismul.
           - La poezie: Încadrează corect (Romantism - Eminescu, Modernism - Blaga/Arghezi, Simbolism - Bacovia).
           - Structurează răspunsurile ca un eseu de BAC (Ipoteză, Argumente, Concluzie).

        4. STIL DE PREDARE:
           - Explică simplu, cald și prietenos. Evită "limbajul de lemn".
           - Folosește analogii pentru concepte grele (ex: "Curentul e ca debitul apei").
           - La teorie: Definiție -> Exemplu Concret -> Aplicație.
           - La probleme: Explică pașii logici ("Facem asta pentru că..."), nu da doar calculul.

        5. MATERIALE UPLOADATE (Cărți/PDF):
           - Dacă primești o carte, păstrează sensul original în rezumate/traduceri.
        """
    )
except Exception as e:
    st.error(f"Eroare la inițializarea modelului: {e}")
    st.stop()

# 3. Sidebar - Opțiuni și Upload
st.sidebar.header("⚙️ Configurare")
enable_audio = st.sidebar.checkbox("🔊 Activează Vocea (Audio)", value=False)

st.sidebar.divider()
st.sidebar.header("📁 Materiale Ajutătoare")
uploaded_files = st.sidebar.file_uploader("Încarcă o poză cu problema sau un PDF", type=["jpg", "png", "jpeg", "pdf"], accept_multiple_files=True)

# Procesare Fișiere
current_context_files = []

if uploaded_files:
    for up_file in uploaded_files:
        # IMAGINI: Le trimitem direct ca PIL (mai rapid decât upload_file)
        if "image" in up_file.type:
            img = Image.open(up_file)
            current_context_files.append(img)
            st.sidebar.image(img, caption=up_file.name, use_container_width=True)
        
        # PDF: Trebuie urcate prin API
        elif "pdf" in up_file.type:
            # Folosim hash-ul numelui pentru a nu reîncărca inutil (basic caching)
            if "uploaded_pdfs" not in st.session_state:
                st.session_state.uploaded_pdfs = {}
            
            if up_file.name not in st.session_state.uploaded_pdfs:
                with st.spinner(f"Procesez PDF: {up_file.name}..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(up_file.getvalue())
                        path = tmp.name
                    try:
                        uploaded_ref = genai.upload_file(path, mime_type="application/pdf")
                        st.session_state.uploaded_pdfs[up_file.name] = uploaded_ref
                        st.sidebar.success(f"✅ PDF Încărcat: {up_file.name}")
                    except Exception as e:
                        st.sidebar.error(f"Eroare PDF: {e}")
            
            # Adăugăm referința la context
            if up_file.name in st.session_state.uploaded_pdfs:
                current_context_files.append(st.session_state.uploaded_pdfs[up_file.name])

# 4. Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Afișare istoric
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"]) # Markdown randează LaTeX automat

# 5. Input și Generare
if user_input := st.chat_input("Întreabă profesorul... (ex: 'Rezolvă problema din poză')"):
    
    # 1. Afișăm mesajul utilizatorului
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # 2. Construim payload-ul (Istoric + Fișiere curente + Întrebare nouă)
    # Gemini generate_content e stateless, deci trimitem istoricul relevant manual sau folosim chat session
    # Aici folosim abordarea manuală pentru flexibilitate cu fișierele
    
    payload_content = []
    
    # Adăugăm fișierele (dacă există) la acest prompt curent
    if current_context_files:
        payload_content.extend(current_context_files)
    
    # Adăugăm textul întrebării
    payload_content.append(user_input)

    # Pregătim istoricul chat-ului pentru context (fără fișiere vechi ca să nu consumăm tokeni inutili, doar text)
    history_obj = []
    for msg in st.session_state.messages[:-1]: # Fără ultimul mesaj (care e cel curent)
        role_gemini = "model" if msg["role"] == "assistant" else "user"
        history_obj.append({"role": role_gemini, "parts": [msg["content"]]})

    # Creăm sesiunea de chat
    chat_session = model.start_chat(history=history_obj)

    with st.chat_message("assistant"):
        with st.spinner("Profesorul gândește... 🧠"):
            try:
                # Trimitem mesajul (text + poze/pdf)
                response = chat_session.send_message(payload_content)
                text_response = response.text
                
                # Afișăm răspunsul
                st.markdown(text_response)
                
                # Salvăm în istoric
                st.session_state.messages.append({"role": "assistant", "content": text_response})

                # Generare Audio (Doar dacă e activat)
                if enable_audio and len(text_response) > 0:
                    try:
                        # Curățăm textul pentru audio (scoatem LaTeX și markdown bold)
                        clean_text = text_response.replace("*", "").replace("$", "").replace("#", "")
                        # Limităm lungimea pentru audio ca să nu dureze o veșnicie
                        if len(clean_text) > 1000:
                            clean_text = clean_text[:1000] + "... explicația continuă în text."

                        sound_file = BytesIO()
                        tts = gTTS(text=clean_text, lang='ro')
                        tts.write_to_fp(sound_file)
                        st.audio(sound_file, format='audio/mp3')
                        
                    except Exception as e_audio:
                        st.warning(f"Audio indisponibil momentan.")
            
            except Exception as e:
                st.error(f"A apărut o eroare: {e}")
                # Dacă e eroare de siguranță, informăm elevul
                if "safety" in str(e).lower():
                    st.error("Mesajul a fost blocat de filtrele de siguranță. Încearcă să reformulezi.")
