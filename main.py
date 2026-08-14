import streamlit as st
import google.generativeai as genai
import os
import datetime 
import pytz  
from PIL import Image
import uuid
import PyPDF2  # Nossa nova ferramenta de leitura de PDF

# --- 1. CONFIGURAÇÃO VISUAL E CSS ---
st.set_page_config(page_title="Kleber.AI - Metrologia", page_icon="🔬", layout="wide", initial_sidebar_state="auto")

st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            min-width: 280px !important;
            max-width: 280px !important;
        }
        button[kind="primary"] p {
            color: #1A1A1A !important; 
            font-weight: 700 !important;
        }
        button[kind="primary"] div {
            color: #1A1A1A !important;
        }
        [data-testid="stFileUploader"] {
            padding-top: 0px !important;
            padding-bottom: 0px !important;
        }
    </style>
""", unsafe_allow_html=True)

def carregar_css(arquivo_css):
    if os.path.exists(arquivo_css):
        with open(arquivo_css) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

carregar_css("style.css")

def get_avatar(role):
    if role == "user":
        return "user.png" if os.path.exists("user.png") else "👤"
    else:
        return "robo.png" if os.path.exists("robo.png") else "🤖"

# --- 2. MOTOR DE LEITURA DOS MANUAIS (FASE 2) ---
# O @st.cache_data faz o sistema ler os PDFs apenas UMA vez ao abrir o site, 
# guardando na memória para não ficar lento.
@st.cache_data
def carregar_base_conhecimento():
    texto_completo = ""
    pasta_manuais = "manuais"
    
    if os.path.exists(pasta_manuais):
        for arquivo in os.listdir(pasta_manuais):
            if arquivo.endswith(".pdf"):
                caminho = os.path.join(pasta_manuais, arquivo)
                try:
                    with open(caminho, "rb") as f:
                        leitor = PyPDF2.PdfReader(f)
                        for pagina in leitor.pages:
                            texto_extraido = pagina.extract_text()
                            if texto_extraido:
                                texto_completo += texto_extraido + "\n"
                except Exception as e:
                    print(f"Erro ao ler {arquivo}: {e}")
    return texto_completo

# Inicia a leitura silenciosa dos PDFs
base_manuais = carregar_base_conhecimento()

# --- 3. CONFIGURAÇÃO DA API E A NOVA MENTE DO KLEBER ---
chave_secreta = st.secrets["GEMINI_KEY"]
genai.configure(api_key=chave_secreta)

fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.datetime.now(fuso_br)
data_hora_texto = agora.strftime("%d/%m/%Y às %H:%M")

# Aqui blindamos a IA contra alucinações e injetamos os manuais
instrucoes_sistema = f"""
Você é o Kleber.AI, um Especialista Sênior em Metrologia, Qualidade Industrial e Indústria 4.0.
INFORMAÇÃO DO SISTEMA: Hoje é dia {data_hora_texto}.

Você tem acesso exclusivo aos seguintes trechos de manuais técnicos da nossa empresa:
--- INÍCIO DOS MANUAIS OFICIAIS ---
{base_manuais}
--- FIM DOS MANUAIS OFICIAIS ---

DIRETRIZES RÍGIDAS DE ATENDIMENTO:
1. PRIORIDADE MÁXIMA: Quando questionado sobre procedimentos de calibração, operação ou alarmes, busque PRIMEIRO a resposta nos Manuais Oficiais acima.
2. CONHECIMENTO EXTERNO: Se a informação NÃO estiver nos manuais fornecidos (exemplo: sobre máquinas Hommelwerke que não possuem PDF anexado), você tem permissão para usar seu amplo conhecimento prévio de metrologia.
3. TRANSPARÊNCIA: Sempre que você usar conhecimentos de fora dos manuais, inicie a resposta avisando sutilmente (Ex: "Como não temos esse detalhe específico nos manuais anexados, com base nas boas práticas e literatura da área...").
4. ZERO ALUCINAÇÃO: NUNCA invente Códigos G, parâmetros de máquina ou rotinas de setup. Se você não souber a resposta exata, oriente o usuário a não agir para evitar colisões no equipamento e recomende acionar a assistência autorizada.
5. FOTOS DE ALARMES: Sempre que receber a foto de um alarme ou peça, analise cuidadosamente e cruze os dados lidos na tela com sua base de conhecimento para ajudar no diagnóstico.

Responda de forma técnica, direta e com vocabulário corporativo de engenharia da qualidade.
"""

modelo = genai.GenerativeModel(
    'models/gemini-2.5-flash',
    system_instruction=instrucoes_sistema,
    generation_config=genai.GenerationConfig(temperature=0.2) # Baixamos a temperatura para ele ficar mais técnico e menos criativo
)

# --- 4. GERENCIAMENTO DE HISTÓRICO ---
if "conversas" not in st.session_state:
    id_inicial = str(uuid.uuid4())
    st.session_state["conversas"] = {id_inicial: {"titulo": "Nova Conversa", "mensagens": []}}
    st.session_state["conversa_atual"] = id_inicial

id_atual = st.session_state["conversa_atual"]
mensagens_atuais = st.session_state["conversas"][id_atual]["mensagens"]

def criar_nova_conversa():
    novo_id = str(uuid.uuid4())
    st.session_state["conversas"][novo_id] = {"titulo": "Nova Conversa", "mensagens": []}
    st.session_state["conversa_atual"] = novo_id

def excluir_conversa(id_para_excluir):
    del st.session_state["conversas"][id_para_excluir]
    if len(st.session_state["conversas"]) == 0:
        criar_nova_conversa()
    elif st.session_state["conversa_atual"] == id_para_excluir:
        st.session_state["conversa_atual"] = list(st.session_state["conversas"].keys())[0]

# --- 5. BARRA LATERAL ---
with st.sidebar:
    if os.path.exists("robo.png"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("robo.png", use_container_width=True)

    st.markdown("<h2 style='text-align: center; padding-top: 10px;'>Kleber.AI</h2>", unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center; color: #a1a1aa;'>Assistente de Qualidade</h4>", unsafe_allow_html=True)
    st.write("") 
    
    # Resolvendo o warning do Streamlit trocando o parametro deprecado
    if st.button("➕ Nova Conversa", use_container_width=True, type="primary"):
        criar_nova_conversa()
        st.rerun()
        
    st.divider()
    
    st.markdown("### 🕒 Recentes")
    for id_conv, dados in st.session_state["conversas"].items():
        estilo = "secondary" if id_conv != id_atual else "primary"
        titulo_display = dados['titulo'][:22] + "..." if len(dados['titulo']) > 22 else dados['titulo']
        
        if st.button(f"💬 {titulo_display}", key=f"btn_{id_conv}", use_container_width=True, type=estilo):
            st.session_state["conversa_atual"] = id_conv
            st.rerun()

    st.divider()
    
    st.markdown("### 📎 Diagnóstico Visual")
    foto_upload = st.file_uploader(
        "Anexe foto do alarme ou peça:", 
        type=["png", "jpg", "jpeg"], 
        key=f"uploader_{id_atual}", 
        label_visibility="collapsed"
    )
    if foto_upload:
        st.success("✅ Imagem pronta para envio!")

    st.divider()
    
    with st.expander("⚙️ Gerenciar Conversa Atual"):
        novo_titulo = st.text_input("Renomear:", value=st.session_state["conversas"][id_atual]["titulo"], key=f"rename_{id_atual}")
        if novo_titulo != st.session_state["conversas"][id_atual]["titulo"]:
            st.session_state["conversas"][id_atual]["titulo"] = novo_titulo
            st.rerun() 
            
        if st.button("🗑️ Excluir Conversa", use_container_width=True):
            excluir_conversa(id_atual)
            st.rerun()

# --- 6. RENDERIZA AS MENSAGENS E IMAGENS ---
st.write("")

for mensagem in mensagens_atuais:
    role_visual = "user" if mensagem["role"] == "user" else "assistant"
    with st.chat_message(role_visual, avatar=get_avatar(mensagem["role"])):
        if "imagem" in mensagem and mensagem["imagem"] is not None:
            st.image(mensagem["imagem"], width=250)
        st.markdown(mensagem["content"])

# --- 7. CAMPO DE DIGITAÇÃO E COMUNICAÇÃO ---
if texto_usuario := st.chat_input("Ex: Como realizar a calibração da ponteira no Calypso?"):
    
    imagem_pil = Image.open(foto_upload) if foto_upload else None
    
    with st.chat_message("user", avatar=get_avatar("user")):
        if imagem_pil:
            st.image(imagem_pil, width=250)
        st.markdown(texto_usuario)
    
    st.session_state["conversas"][id_atual]["mensagens"].append({
        "role": "user", 
        "content": texto_usuario,
        "imagem": imagem_pil
    })

    try:
        historico_google = []
        for msg in mensagens_atuais[:-1]:
            role_google = "user" if msg["role"] == "user" else "model"
            partes = []
            if "imagem" in msg and msg["imagem"] is not None:
                partes.append(msg["imagem"])
            partes.append(msg["content"])
            historico_google.append({"role": role_google, "parts": partes})

        chat = modelo.start_chat(history=historico_google)
        
        conteudo_envio = [imagem_pil, texto_usuario] if imagem_pil else texto_usuario

        with st.chat_message("assistant", avatar=get_avatar("model")):
            with st.spinner("Kleber.AI está processando dados e manuais..."):
                response = chat.send_message(conteudo_envio, stream=True)
            
            def gerador_resposta():
                for pedaco in response:
                    yield pedaco.text
                    
            texto_completo = st.write_stream(gerador_resposta)
            
        st.session_state["conversas"][id_atual]["mensagens"].append({
            "role": "model", 
            "content": texto_completo
        })

    except Exception as e:
        st.error(f"Ocorreu um erro técnico: {e}")