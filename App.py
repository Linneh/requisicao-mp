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

# ====== SALVAR + LIMPEZA AUTOMÁTICA ======
def salvar_dados(df):
    try:
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        limite = datetime.now() - pd.Timedelta(days=2)

        df = df[~(
            (df["status"] == "APROVADO") &
            (df["impresso"] == "SIM") &
            (df["data"] < limite)
        )]
    except:
        pass

    df.to_csv(DB_PATH, index=False, sep=";")

df_db = carregar_dados()

# ===== FORMATAR STATUS =====
def style_status(x):
    if x == "APROVADO":
        return "🟩 APROVADO"
    elif x == "REPROVADO":
        return "🟥 REPROVADO"
    return "🟨 PENDENTE"


# ===== LOGIN =====
st.title("📦 Requisição MP")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:

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
        senha_atual = st.text_input("Senha atual:", type="password", key="old_pass")
        senha_nova = st.text_input("Nova senha:", type="password", key="new_pass")
        senha_conf = st.text_input("Confirmar nova senha:", type="password", key="conf_pass")

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

st.sidebar.title("📌 Menu")

menus = []
if "mercadinho" in perfil:
    menus += ["Nova Solicitação", "Minhas Solicitações"]
if "almoxarifado" in perfil:
    menus += ["Requisições Pendentes", "Romaneio", "Histórico Completo"]
if user == "aline.silva":
    menus += ["Painel Admin"]
menus += ["Sair"]

menu = st.sidebar.radio("Escolha:", menus)

st.success(f"Bem-vindo(a), {user} — Perfil: {perfil}")


# ===== SAIR =====
if menu == "Sair":
    st.session_state.clear()
    st.rerun()


# ===== NOVA SOLICITAÇÃO =====
if menu == "Nova Solicitação":
    st.header("📝 Nova Solicitação")

    # ------ AQUI É A ÚNICA ALTERAÇÃO ------
    try:
        df_prod = pd.read_excel("Produtos.xlsx")

        cols = [c.strip() for c in df_prod.columns.astype(str)]

        # Caso 1: tem CODIGO e DESCRICAO
        if "CODIGO" in cols and "DESCRICAO" in cols:
            df_prod.columns = cols
            produtos = ["-- SELECIONE --"] + (
                df_prod["CODIGO"].astype(str) + " - " + df_prod["DESCRICAO"].astype(str)
            ).tolist()
        else:
            # Caso 2: usar as duas primeiras colunas da planilha
            if len(cols) >= 2:
                col_cod = cols[0]
                col_desc = cols[1]
                produtos = ["-- SELECIONE --"] + (
                    df_prod[col_cod].astype(str) + " - " + df_prod[col_desc].astype(str)
                ).tolist()
                st.warning(
                    f"Usando colunas '{col_cod}' e '{col_desc}' da planilha Produtos.xlsx "
                    "porque não encontrei as colunas CODIGO e DESCRICAO."
                )
            else:
                produtos = ["-- SELECIONE --"]
                st.error("Planilha Produtos.xlsx não tem colunas suficientes.")
    except Exception as e:
        produtos = ["-- SELECIONE --"]
        st.error(f"Erro ao ler Produtos.xlsx: {e}")
    # ------ FIM DA ALTERAÇÃO ------

    prod = st.selectbox("Produto:", produtos)
    qtd = st.number_input("Quantidade:", min_value=1, step=1)

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
            df_db = df_db.append(novo, ignore_index=True)
            salvar_dados(df_db)
            st.success("✔ Solicitação enviada!")
            st.rerun()


# ===== MINHAS SOLICITAÇÕES =====
if menu == "Minhas Solicitações":
    st.header("📋 Minhas Solicitações")
    minhas = df_db[df_db["solicitante"] == user].copy()
    minhas["status"] = minhas["status"].apply(style_status)
    st.dataframe(minhas)


# ===== REQUISIÇÕES PENDENTES =====
if menu == "Requisições Pendentes":
    st.header("📦 Requisições Pendentes")

    pend = df_db[df_db["status"] == "PENDENTE"].copy()

    if pend.empty:
        st.info("Nenhuma requisição pendente.")
    else:
        for idx, req in pend.iterrows():
            cod = req["codigo"]
            st.write(f"🔹 **{cod}** — {req['item']} — Qtd: {req['quantidade']}")

            col1, col2 = st.columns(2)

            if col1.button(f"Aprovar {cod}"):
                df_db.loc[idx, ["status", "aprovador", "hora_aprovacao"]] = [
                    "APROVADO", user, datetime.now().strftime("%H:%M:%S")
                ]
                salvar_dados(df_db)
                st.rerun()

            if col2.button(f"Reprovar {cod}"):
                df_db.loc[idx, ["status", "motivo_reprovacao"]] = [
                    "REPROVADO", "Motivo não informado"
                ]
                salvar_dados(df_db)
                st.rerun()


# ===== ROMANEIO =====
if menu == "Romaneio":
    st.header("📋 Romaneio")

    aprovadas = df_db[(df_db["status"] == "APROVADO") & (df_db["impresso"] != "SIM")].copy()
    aprovadas["status"] = aprovadas["status"].apply(style_status)
    st.dataframe(aprovadas)

    if st.button("Marcar como Impresso"):
        df_db.loc[df_db["codigo"].isin(aprovadas["codigo"]), "impresso"] = "SIM"
        salvar_dados(df_db)
        st.success("✔ Romaneio atualizado!")
        st.rerun()


# ===== HISTÓRICO COMPLETO =====
if menu == "Histórico Completo":
    st.header("📚 Histórico Geral")
    hist = df_db.copy()
    hist["status"] = hist["status"].apply(style_status)
    st.dataframe(hist)


# ===== PAINEL ADMIN =====
if menu == "Painel Admin":

    if user != "aline.silva":
        st.error("🚫 Você não tem permissão!")
        st.stop()

    st.header("🛠 Gerenciamento de Usuários")

    st.subheader("Cadastrar novo usuário")
    novo_user = st.text_input("Novo Usuário:")
    nova_senha = st.text_input("Senha inicial:")
    novo_perfil = st.selectbox("Perfil:",
                               ["mercadinho", "almoxarifado", "mercadinho e almoxarifado"])

    if st.button("Salvar Novo Usuário"):
        st.session_state.usuarios[novo_user] = {
            "senha": nova_senha,
            "perfil": novo_perfil
        }
        st.success("Usuário cadastrado ✔")

    st.subheader("Alterar Senha de Usuário Existente")
    usuario_sel = st.selectbox("Selecione o usuário", list(st.session_state.usuarios.keys()))
    nova_senha_edit = st.text_input("Nova senha:", key="senha_edit")

    if st.button("Alterar Senha"):
        st.session_state.usuarios[usuario_sel]["senha"] = nova_senha_edit
        st.success("Senha alterada ✔")

