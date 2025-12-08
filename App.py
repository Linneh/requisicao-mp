import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import zipfile

# ====== CONFIGURAÇÕES ======
BASE_PATH = ""
CSV_PATH = "solicitacoes.csv"
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# ====== USUÁRIOS INICIAIS ======
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {
        "aline.silva": {"senha": "123", "perfil": "mercadinho e almoxarifado"},
        "tacya.oliveira": {"senha": "123", "perfil": "almoxarifado"},
        "emily.eduarda": {"senha": "123", "perfil": "almoxarifado"},
        "taciane.almeida": {"senha": "123", "perfil": "almoxarifado"},
        "ananda.dias": {"senha": "123", "perfil": "almoxarifado"},
        "brenda.costa": {"senha": "123", "perfil": "almoxarifado"},
        "renato.spuza": {"senha": "123", "perfil": "almoxarifado"},
        "luiz.pedrosa": {"senha": "123", "perfil": "almoxarifado"},
        "vaninho.almox": {"senha": "123", "perfil": "almoxarifado"},
        "jaciane.silva": {"senha": "123", "perfil": "mercadinho"},
        "matheus.monaco": {"senha": "123", "perfil": "mercadinho"},
    }

# ====== BANCO DE DADOS ======
def carregar_dados():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=["codigo", "solicitante", "item", "quantidade",
                                     "status", "aprovador", "data", "hora_aprovacao",
                                     "motivo_reprovacao"])
    return pd.read_csv(CSV_PATH, sep=";", encoding="latin1")

def backup_auto():
    agora = datetime.now()
    backup_name = f"backup_{agora.strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(os.path.join(BACKUP_DIR, backup_name), "w") as zf:
        if os.path.exists(CSV_PATH):
            zf.write(CSV_PATH)

    for fname in os.listdir(BACKUP_DIR):
        path = os.path.join(BACKUP_DIR, fname)
        if os.path.getmtime(path) < (agora - timedelta(days=2)).timestamp():
            os.remove(path)

def salvar_db(df):
    df.to_csv(CSV_PATH, index=False, sep=";")
    backup_auto()

df_db = carregar_dados()

# ====== STATUS ======
def style_status(x):
    if x == "APROVADO": return "🟩 APROVADO"
    elif x == "REPROVADO": return "🟥 REPROVADO"
    return "🟨 PENDENTE"

# ===== LOGIN =====
st.title("📦 Requisição MP")

if "user" not in st.session_state or not st.session_state.user:
    tab_login, tab_senha = st.tabs(["🔐 Login", "🔑 Alterar Senha"])

    with tab_login:
        usuario = st.text_input("Usuário:")
        senha = st.text_input("Senha:", type="password")

        if st.button("Entrar"):
            usuario = usuario.strip().lower()
            if usuario in st.session_state.usuarios and \
               st.session_state.usuarios[usuario]["senha"] == senha:
                st.session_state.user = usuario
                st.session_state.perfil = st.session_state.usuarios[usuario]["perfil"]
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos!")

    with tab_senha:
        usuario_alt = st.text_input("Usuário:", key="alter_user")
        senha_atual = st.text_input("Senha atual:", type="password", key="alter_old")
        senha_nova = st.text_input("Nova senha:", type="password", key="alter_new")
        senha_conf = st.text_input("Confirmar nova senha:", type="password", key="alter_conf")

        if st.button("Salvar Nova Senha"):
            usuario_alt = usuario_alt.strip().lower()

            if usuario_alt not in st.session_state.usuarios:
                st.error("Usuário não encontrado!")
            elif st.session_state.usuarios[usuario_alt]["senha"] != senha_atual:
                st.error("Senha atual incorreta!")
            elif senha_nova != senha_conf:
                st.error("As senhas não conferem!")
            else:
                st.session_state.usuarios[usuario_alt]["senha"] = senha_nova
                st.success("Senha alterada ✔")

    st.stop()

# ===== ÁREA LOGADA =====
user = st.session_state.user
perfil = st.session_state.perfil

st.success(f"Bem-vindo(a), {user} — Perfil: {perfil}")

st.sidebar.title("📌 Menu")
menus = []
if "mercadinho" in perfil:
    menus += ["Nova Solicitação", "Minhas Solicitações"]
if "almoxarifado" in perfil:
    menus += ["Requisições Pendentes", "Romaneio", "Histórico Completo"]
menus += ["Sair"]

menu = st.sidebar.radio("Escolha:", menus)

if menu == "Sair":
    st.session_state.clear()
    st.rerun()

# ==== MERCADO ====
if menu == "Nova Solicitação":
    st.header("📝 Nova Solicitação")

    try:
        df_prod = pd.read_excel("Produtos.xlsx")
        produtos = ["-- SELECIONE --"] + (df_prod["CODIGO"].astype(str) + " - " + df_prod["DESCRICAO"]).tolist()
    except:
        produtos = ["-- SELECIONE --"]
        st.warning("⚠ Arquivo Produtos.xlsx não encontrado!")

    prod = st.selectbox("Produto:", produtos)
    qtd = st.number_input("Quantidade:", min_value=1, step=1)

    if st.button("Enviar Solicitação"):
        if prod == "-- SELECIONE --":
            st.warning("Selecione um produto!")
            st.stop()

        novo = {
            "codigo": f"REQ-{len(df_db)+1:04d}",
            "solicitante": user,
            "item": prod,
            "quantidade": qtd,
            "status": "PENDENTE",
            "aprovador": "",
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hora_aprovacao": "",
            "motivo_reprovacao": ""
        }

        df_db.loc[len(df_db)] = novo
        salvar_db(df_db)
        st.success("Solicitação enviada ✔")
        st.rerun()

if menu == "Minhas Solicitações":
    st.dataframe(df_db[df_db["solicitante"] == user])

# ==== ALMOX =====
if menu == "Requisições Pendentes":
    st.header("📦 Requisições Pendentes")
    pend = df_db[df_db["status"] == "PENDENTE"]
    pend["status"] = pend["status"].apply(style_status)
    st.dataframe(pend)

if menu == "Romaneio":
    aprovadas = df_db[df_db["status"] == "APROVADO"].copy()

    if aprovadas.empty:
        st.info("Nenhuma requisição aprovada!")
    else:
        rom = aprovadas[["codigo","item","quantidade","solicitante"]]
        st.download_button("📥 Baixar Romaneio CSV",
                           rom.to_csv(index=False, sep=";"),
                           file_name="romaneio.csv")
        st.success("📄 Romaneio atualizado ✔")

if menu == "Histórico Completo":
    hist = df_db.copy()
    hist["status"] = hist["status"].apply(style_status)
    st.dataframe(hist)


