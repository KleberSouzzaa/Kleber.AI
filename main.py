# Título
# Input do chat (campo de texto para o usuário enviar mensagens)
    # Mostra a mensagem que o usuario enviou no chat
    # Pegar a pergunta e enviar para uma IA responder
    # Exibir a resposta da IA na tela

# Biblioteca sugerida. Framework web em Python:
# Streamlit -> apenas com Python ele pode criar o front-end e back-end juntos. Vai ser ela a ser utilizada neste projeto.
# A IA sugerida: Gemini do Google (Generative AI)
# python -m pip install openai streamlit
# para rodar o código localmente: streamlit run main.py

import streamlit as st
import google.generativeai as genai
import os
import datetime # <--- Nova biblioteca para saber a hora!

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Kleber.AI", page_icon="🤖")

def carregar_css(arquivo_css):
    with open(arquivo_css) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

carregar_css("style.css")

# --- 2. FUNÇÕES AUXILIARES ---
def get_avatar(role):
    if role == "user":
        return "user.png" if os.path.exists("user.png") else "👤"
    else:
        return "robo.png" if os.path.exists("robo.png") else "🤖"

# --- 3. CONFIGURAÇÃO INTELIGENTE (DATA E HORA) ---
chave_secreta = st.secrets["GEMINI_KEY"]
genai.configure(api_key=chave_secreta)

# Pega a data e hora atual do seu PC
agora = datetime.datetime.now()
data_hora_texto = agora.strftime("%d/%m/%Y às %H:%M")

# Criamos a "Personalidade" e damos o relógio para ele
instrucoes_sistema = f"""
Você é o Kleber.AI, um assistente corporativo inteligente e prestativo.
INFORMAÇÃO DO SISTEMA: Hoje é dia {data_hora_texto}.
Se o usuário perguntar sobre o clima, avise honestamente que você não tem acesso à internet em tempo real, mas que pode ajudar com outras coisas.
Não invente previsões do tempo.
"""

# Iniciamos o modelo com essas instruções
modelo = genai.GenerativeModel(
    'models/gemini-2.5-flash',
    system_instruction=instrucoes_sistema
)

# --- 4. TÍTULO, TECNOLOGIA E STATUS ---
st.title("🤖 Kleber.AI")
st.markdown("### Assistente Inteligente Corporativo")

# Aqui a gente destaca a tecnologia (Robustez)
st.markdown("**Tecnologia:** Google Gemini 2.5 Flash ⚡")

# Aqui a gente mostra que o sistema está vivo (Funcionalidade)
st.caption(f"🟢 Status: Online | 📅 Data do Sistema: {data_hora_texto}")

st.divider()

if "lista_mensagens" not in st.session_state:
    st.session_state["lista_mensagens"] = []
# --- 5. MOSTRA O HISTÓRICO ---
for mensagem in st.session_state["lista_mensagens"]:
    role_visual = "user" if mensagem["role"] == "user" else "assistant"
    icone = get_avatar(mensagem["role"])
    with st.chat_message(role_visual, avatar=icone):
        st.markdown(mensagem["content"])

# --- 6. NOVA PERGUNTA ---
if texto_usuario := st.chat_input("Pergunte algo ao Kleber.AI..."):
    # Mostra pergunta
    with st.chat_message("user", avatar=get_avatar("user")):
        st.markdown(texto_usuario)
    st.session_state["lista_mensagens"].append({"role": "user", "content": texto_usuario})

    try:
        # Prepara histórico
        historico_google = []
        for msg in st.session_state["lista_mensagens"]:
            role_google = "user" if msg["role"] == "user" else "model"
            historico_google.append({"role": role_google, "parts": [msg["content"]]})

        # Gera resposta
        chat = modelo.start_chat(history=historico_google)
        response = chat.send_message(texto_usuario)
        texto_resposta = response.text

        # Mostra resposta
        with st.chat_message("assistant", avatar=get_avatar("model")):
            st.markdown(texto_resposta)
        st.session_state["lista_mensagens"].append({"role": "model", "content": texto_resposta})

    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")