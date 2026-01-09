import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Configurare Pagină
st.set_page_config(page_title="Profesorul de Mate AI (Llama 3.3)", page_icon="🧮")
st.title("🧮 Proful de Mate (Llama 3.3)")
st.caption("Model activ: llama-3.3-70b-versatile (Expert în explicații)")

# 2. Configurare API Key
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Introdu cheia Groq API:", type="password")

if not api_key:
    st.info("Te rog introdu cheia API pentru a începe.")
    st.stop()

# 3. Inițializarea Modelului (Cel mai nou și stabil de la Groq)
try:
    llm = ChatGroq(
        temperature=0.3, 
        groq_api_key=api_key, 
        model_name="llama-3.3-70b-versatile" 
    )
except Exception as e:
    st.error(f"Eroare la conectare: {e}")
    st.stop()

# 4. Definirea Profesorului
system_prompt = """Ești un profesor de matematică de elită.
Obiectivul tău este să faci matematica simplă și clară.

REGULI:
1. Răspunde în limba română.
2. Folosește formatare LaTeX pentru formule (încadrate de $).
   Exemplu: Soluția ecuației $x^2 - 4 = 0$ este $x = \pm 2$.
3. Explică logica din spatele fiecărui pas.
4. Fii răbdător și încurajator.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{question}")
])

chain = prompt | llm | StrOutputParser()

# 5. Interfața de Chat
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Salut! Din păcate, funcția de 'vedere' (poze) este momentan oprită de Groq, dar am primit un upgrade la inteligență (Llama 3.3). Scrie-mi orice problemă și o rezolvăm!"}
    ]

# Afișare istoric
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input utilizator
if user_input := st.chat_input("Scrie problema aici (folosește ^ pentru puteri, ex: x^2)..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    with st.chat_message("assistant"):
        try:
            response = chain.invoke({"question": user_input})
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Eroare: {e}")
