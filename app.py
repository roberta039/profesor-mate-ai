import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configurare Pagină
st.set_page_config(page_title="Profesorul de Mate AI", page_icon="📐")
st.title("📐 Proful de Mate - Gemini")

# 2. Logica pentru API Key (Automată + Manuală)
api_key = None

# Verificăm dacă cheia este în "Seiful" Streamlit
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Dacă nu e în seif, o cerem manual în stânga
    api_key = st.sidebar.text_input("Introdu Google API Key:", type="password")
    st.sidebar.warning("Sfat: Adaugă cheia în 'Secrets' pentru conectare automată.")

# Dacă nu avem cheie deloc, oprim aplicația aici
if not api_key:
    st.info("Aștept cheia API pentru a porni...")
    st.stop()

# Configurăm Google AI
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Eroare la configurarea cheii: {e}")
    st.stop()

# 3. Bara Laterală: Setări și Upload
with st.sidebar:
    st.header("⚙️ Setări")
    
    # Lista manuală de modele (pentru siguranță)
    model_options = [
        "gemini-1.5-flash",          # Cel mai rapid și stabil
        "gemini-1.5-pro",            # Mai inteligent, dar mai lent
        "models/gemini-1.5-flash",   # Alternativă de nume
        "gemini-pro-vision"          # Varianta veche
    ]
    
    selected_model_name = st.selectbox("Alege Modelul:", model_options)
    
    st.divider()
    st.header("📸 Materiale")
    uploaded_file = st.file_uploader("Încarcă o poză cu problema", type=["jpg", "jpeg", "png"])
    
    img = None
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Imagine încărcată", use_container_width=True)
        st.success("Imagine gata de analiză!")

# 4. Inițializarea Modelului
try:
    model = genai.GenerativeModel(
        selected_model_name,
        system_instruction="""Ești un profesor de matematică expert, răbdător și prietenos.
        1. Analizează imaginea sau textul primit.
        2. Dacă este o problemă, rezolv-o pas cu pas.
        3. Explică logica din spatele fiecărui pas, nu da doar rezultatul.
        4. Folosește limba română.
        5. Folosește formatare LaTeX pentru formule matematice (încadrate de $).
        """
    )
except Exception as e:
    st.error(f"Eroare la inițializarea modelului: {e}")

# 5. Istoricul Chat-ului
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Salut! Sunt profesorul tău de matematică. Încarcă o poză sau scrie o problemă și o rezolvăm împreună."}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 6. Procesarea Inputului
if user_input := st.chat_input("Scrie aici întrebarea ta..."):
    # Afișăm mesajul utilizatorului
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Pregătim datele pentru AI (Text + Imagine Opțională)
    inputs = [user_input]
    if img:
        inputs.append(img)

    # Generăm răspunsul
    with st.chat_message("assistant"):
        with st.spinner(f"Rezolv folosind {selected_model_name}..."):
            try:
                response = model.generate_content(inputs)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Eroare: {e}")
                st.info("Încearcă să selectezi alt model din meniul din stânga.")
