import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ====== CONFIGURAÇÃO DO BANCO ======
DB_PATH = "solicitacoes.csv"

# ====== USUÁRIOS INICIAIS ======
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {
        "aline.silva": {"senha": "123", "perfil": "mercadinho e almoxarifado"}
    }

# ====== BANCO DE DADOS ======
def carregar_dados():
    if not os.path.exists(DB_PATH):
        df = pd.DataFrame(columns=[
            "codigo", "solicitante", "item", "quantidade", "status",
            "aprovador", "data", "hora_aprovacao",
            "motivo_reprovacao", "impresso"
        ])
        df.to_csv(DB_PATH, index=False, sep=";")
    return pd.read_csv(DB_PATH, sep=";", encoding="latin1")

def salvar_dados(df):
    df.to_csv(DB_PATH, index=False, sep=";")

df_db = carregar_dados()

def style_status(x):
    if x == "APROVADO": return "🟩 APROVADO"
    if x == "REPROVADO": return "🟥 REPROVADO"
    return "🟨 PENDENTE"


# ================= LOGIN =================
st.title("📦 Requisição MP")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:

    tab_login, tab_senha = st.tabs(["🔐 Login", "🔑 Alterar Senha"])

    # --- LOGIN ---
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

    # --- ALTERAR SENHA ---
    with tab_senha:
        usuario_alt = st.text_input("Usuário:", key="alter_user")
        senha_atual = st.text_input("Senha atual:", type="password")
        senha_nova = st.text_input("Nova senha:", type="password")
        senha_conf = st.text_input("Confirmar nova senha:", type="password")

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


# ================= ÁREA LOGADA =================
user = st.session_state.user
perfil = st.session_state.perfil

st.success(f"Bem-vindo(a), {user} — Perfil: {perfil}")

st.sidebar.title("📌 Menu")
menus = ["Sair"]

if "mercadinho" in perfil:
    menus.insert(0, "Minhas Solicitações")
    menus.insert(0, "Nova Solicitação")

if "almoxarifado" in perfil:
    menus.insert(0, "Histórico Completo")
    menus.insert(0, "Romaneio")
    menus.insert(0, "Requisições Pendentes")

if user == "aline.silva":
    menus.insert(0, "Painel Admin")

menu = st.sidebar.radio("Escolha:", menus)

if menu == "Sair":
    st.session_state.clear()
    st.rerun()


# ================= NOVA SOLICITAÇÃO =================
if menu == "Nova Solicitação":
    st.header("📝 Nova Solicitação")

    if "produto" not in st.session_state:
        st.session_state["produto"] = "-- SELECIONE --"

    if "quantidade" not in st.session_state:
        st.session_state["quantidade"] = 1

    try:
        df_prod = pd.read_excel("Produtos.xlsx")
        produtos = ["-- SELECIONE --"] + (
            df_prod["CODIGO"].astype(str) + " - " +
            df_prod["DESCRICAO"].astype(str)
        ).tolist()
    except Exception as e:
        produtos = ["-- SELECIONE --"]
        st.error(f"Erro ao carregar Produtos.xlsx: {e}")

    prod = st.selectbox("Produto:", produtos, key="produto")
    qtd = st.number_input("Quantidade:", min_value=1, step=1, key="quantidade")

    if st.button("Enviar Solicitação"):
        if prod == "-- SELECIONE --":
            st.warning("Selecione um produto!")
        else:
            novo = {
                "codigo": f"REQ-{len(df_db)+1:04d}",
                "solicitante": user,
                "item": prod,
                "quantidade": int(qtd),
                "status": "PENDENTE",
                "aprovador": "",
                "data": datetime.now().strftime("%d/%m/%Y"),
                "hora_aprovacao": "",
                "motivo_reprovacao": "",
                "impresso": ""
            }

            df_db = pd.concat([df_db, pd.DataFrame([novo])], ignore_index=True)
            salvar_dados(df_db)

            # 🔹🔹 RESET DO FORMULÁRIO 🔹🔹
            st.session_state["produto"] = "-- SELECIONE --"
            st.session_state["quantidade"] = 1

            st.success("✔ Solicitação enviada!")
            st.rerun()


# ================= MINHAS SOLICITAÇÕES =================
if menu == "Minhas Solicitações":
    st.header("📋 Minhas Solicitações")
    minhas = df_db[df_db["solicitante"] == user].copy()
    minhas["status"] = minhas["status"].apply(style_status)
    st.dataframe(minhas)


# ================= REQUISIÇÕES PENDENTES =================
if menu == "Requisições Pendentes":
    st.header("📦 Requisições Pendentes")
    pend = df_db[df_db["status"] == "PENDENTE"]

    for idx, req in pend.iterrows():
        cod = req["codigo"]
        st.write(f"🔹 {cod} — {req['item']} — Qtd: {req['quantidade']}")

        col1, col2 = st.columns(2)

        if col1.button(f"✓ Aprovar {cod}"):
            df_db.loc[idx, ["status", "aprovador", "hora_aprovacao"]] = [
                "APROVADO", user, datetime.now().strftime("%H:%M:%S")
            ]
            salvar_dados(df_db)
            st.rerun()

        if col2.button(f"✗ Reprovar {cod}"):
            df_db.loc[idx, "status"] = "REPROVADO"
            salvar_dados(df_db)
            st.rerun()


# ================= ROMANEIO =================
if menu == "Romaneio":
    st.header("📋 Romaneio")
    rom = df_db[df_db["status"] == "APROVADO"]

    if rom.empty:
        st.info("Nenhuma requisição aprovada.")
    else:
        st.dataframe(rom)
        if st.button("Marcar como impresso"):
            df_db.loc[df_db["codigo"].isin(rom["codigo"]), "impresso"] = "SIM"
            salvar_dados(df_db)
            st.success("Romaneio atualizado ✔")
            st.rerun()


# ================= HISTÓRICO COMPLETO =================
if menu == "Histórico Completo":
    st.header("📚 Histórico Geral")
    hist = df_db.copy()
    hist["status"] = hist["status"].apply(style_status)
    st.dataframe(hist)


# ================= GERENCIAMENTO DE USUÁRIOS =================
if menu == "Painel Admin":
    st.header("🛠 Painel Administração")
    st.write("Função disponível para alinhe.silva")


