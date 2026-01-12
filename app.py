import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configurare Pagină
st.set_page_config(page_title="Profesor Universal (Auto)", page_icon="🧠")
st.title("🧠 Profesor Universal (Auto-Pilot)")

# 2. Configurare API Key
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Introdu Google API Key:", type="password")

if not api_key:
    st.info("Introdu cheia Google API pentru a începe.")
    st.stop()

# Configurare Google GenAI
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Eroare la configurare cheie: {e}")
    st.stop()

# --- LOGICA DE SELECȚIE AUTOMATĂ (FILTRATĂ) ---
def get_best_model_automatically():
    try:
        all_models = []
        for m in genai.list_models():
            # Verificăm doar modelele care generează conținut
            if 'generateContent' in m.supported_generation_methods:
                name = m.name
                if "gemini" in name:
                    # --- FILTRU DE SIGURANȚĂ ---
                    # Excludem modelele experimentale ciudate care strică sortarea
                    if "robotics" in name: continue  # Nu vrem robotică
                    if "aqa" in name: continue       # Nu vrem modele de test AQA
                    if "embedding" in name: continue # Nu vrem embeddings
                    
                    all_models.append(name)
        
        # Sortăm invers (Z->A și 9->0)
        # Acum că am scos "Robotics", "Pro" (P) va câștiga în fața lui "Flash" (F).
        # Și Gemini 3 va câștiga în fața lui Gemini 2 sau 1.5.
        all_models.sort(reverse=True)
        
        if all_models:
            return all_models[0] # Returnăm Campionul real
        else:
            return "models/gemini-1.5-flash" # Fallback
            
    except Exception as e:
        return "models/gemini-1.5-flash"

# Aflăm modelul suprem
best_model_name = get_best_model_automatically()

# Îl afișăm în stânga
st.sidebar.header("🤖 Status")
st.sidebar.success(f"Model activat:\n**{best_model_name}**")

# Dacă apare Gemini 3 în viitor, sărbătorim!
if "gemini-3" in best_model_name:
    st.sidebar.balloons() 

# --- INITIALIZARE MODEL ---
try:
        model = genai.GenerativeModel(
        best_model_name,
        system_instruction="""Ești un profesor universal (Mate, Fizică, Chimie) răbdător și empatic.
        
        REGULĂ STRICTĂ: Predă exact ca la școală (nivel Gimnaziu/Liceu). 
        NU confunda elevul cu detalii despre "aproximări" sau "lumea reală" decât dacă problema o cere specific.

        Ghid de comportament:
        1. MATEMATICĂ: Lucrează cu valori exacte sau standard. 
           - Dacă rezultatul e $\sqrt{2}$, lasă-l $\sqrt{2}$. Nu spune "care este aproximativ 1.41".
           - Nu menționa că $\pi$ e infinit; folosește valorile din manual fără comentarii suplimentare.
        2. FIZICĂ/CHIMIE: Presupune automat "condiții ideale".
           - Nu menționa frecarea cu aerul, pierderile de căldură sau imperfecțiunile aparatelor de măsură.
           - Tratează problema exact așa cum apare în culegere, într-un univers matematic perfect.
        3. Stilul de predare: Explică simplu, cald și prietenos. Evită limbajul academic rigid ("limbajul de lemn").
        4. Analogii: Folosește comparații din viața reală pentru a explica concepte abstracte (ex: "Voltajul e ca presiunea apei pe o țeavă").
        5. Teorie: Când ești întrebat de teorie, definește conceptul, apoi dă un exemplu concret, apoi explică la ce ne ajută în viața reală.
        6. Rezolvare probleme: Nu da doar rezultatul. Explică pașii logici ("Facem asta pentru că...").
        7. Formule: Folosește LaTeX ($...$) pentru claritate, dar explică ce înseamnă fiecare literă din formulă.
        """
    )
except Exception as e:
    st.error(f"Eroare la inițializarea modelului {best_model_name}: {e}")

# 3. Interfața de Upload
st.sidebar.header("📁 Materiale")
uploaded_file = st.sidebar.file_uploader("Încarcă o poză", type=["jpg", "jpeg", "png"])

img = None
if uploaded_file:
    img = Image.open(uploaded_file)
    st.sidebar.image(img, caption="Imagine încărcată", use_container_width=True)

# 4. Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": f"Salut! Sunt conectat la {best_model_name}. Cu ce te ajut?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 5. Input
if user_input := st.chat_input("Scrie problema..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    inputs = [user_input]
    if img:
        inputs.append(img)

    with st.chat_message("assistant"):
        with st.spinner("Rezolv..."):
            try:
                response = model.generate_content(inputs)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Eroare: {e}")
