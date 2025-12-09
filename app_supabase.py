import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# ========== SUPABASE CONFIG ==========
SUPABASE_URL = st.secrets["https://bydkiyxmrwqrppikiuie.supabase.co"]
SUPABASE_KEY = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ5ZGtpeXhtcndxcnBwaWtpdWllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyNjExNTAsImV4cCI6MjA4MDgzNzE1MH0.gD6wNKWSglrevuwb-eeBM5S2jeux-3AGkssf47cMmzE"]
supabase: Client = create_client("https://bydkiyxmrwqrppikiuie.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ5ZGtpeXhtcndxcnBwaWtpdWllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyNjExNTAsImV4cCI6MjA4MDgzNzE1MH0.gD6wNKWSglrevuwb-eeBM5S2jeux-3AGkssf47cMmzE")

# ========== FUNÇÕES NO BANCO ==========
def carregar_solicitacoes():
    res = supabase.table("solicitacoes").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def salvar_solicitacao(item, qtd, user):
    df = carregar_solicitacoes()
    cod = f"REQ-{len(df) + 1:04d}"

    supabase.table("solicitacoes").insert({
        "codigo": cod,
        "solicitante": user,
        "item": item,
        "quantidade": int(qtd),
        "status": "PENDENTE",
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "impresso": ""
    }).execute()

def atualizar_status(codigo, status, aprovador, motivo=""):
    supabase.table("solicitacoes").update({
        "status": status,
        "aprovador": aprovador,
        "hora_aprovacao": datetime.now().strftime("%H:%M:%S"),
        "motivo_reprovacao": motivo
    }).eq("codigo", codigo).execute()

def marcar_impresso(lista_codigos):
    supabase.table("solicitacoes").update({"impresso": "SIM"}).in_("codigo", lista_codigos).execute()

def get_produtos():
    res = supabase.table("produtos").select("*").execute()
    df_prod = pd.DataFrame(res.data)
    return ["-- SELECIONE --"] + (df_prod["codigo"] + " - " + df_prod["descricao"]).tolist()


# ========== LOGIN ==========
st.title("📦 Requisição MP Supabase")

if "user" not in st.session_state:
    email = st.text_input("Usuário (email):")
    senha = st.text_input("Senha:", type="password")

    if st.button("Entrar"):
        try:
            auth = supabase.auth.sign_in_with_password({
                "email": email,
                "password": senha
            })
            st.session_state.user = auth.user.email
            st.session_state.perfil = auth.user.user_metadata.get("perfil", "mercadinho")
            st.rerun()
        except:
            st.error("❌ Usuário ou senha incorretos!")
    st.stop()

user = st.session_state.user
perfil = st.session_state.perfil


# ========== MENU ==========
st.sidebar.header("📌 Menu")

menus = []
if "mercadinho" in perfil:
    menus += ["Nova Solicitação", "Minhas Solicitações"]
if "almoxarifado" in perfil:
    menus += ["Requisições Pendentes", "Romaneio", "Histórico Completo"]
if user.startswith("aline"):
    menus += ["Painel Admin"]

menus += ["Sair"]

menu = st.sidebar.radio("Escolha:", menus)

st.success(f"Bem-vindo(a), {user} — Perfil: {perfil}")


# ========== SAIR ==========
if menu == "Sair":
    supabase.auth.sign_out()
    st.session_state.clear()
    st.rerun()


# ========== NOVA SOLICITAÇÃO ==========
if menu == "Nova Solicitação":
    st.header("📝 Nova Solicitação")

    produtos = get_produtos()
    prod = st.selectbox("Produto:", produtos)
    qtd = st.number_input("Quantidade:", min_value=1, step=1)

    if st.button("Enviar Solicitação"):
        if prod == "-- SELECIONE --":
            st.warning("Selecione um produto!")
        else:
            salvar_solicitacao(prod, qtd, user)
            st.success("✔ Solicitação enviada!")
            st.rerun()


# ========== MINHAS SOLICITAÇÕES ==========
if menu == "Minhas Solicitações":
    st.header("📋 Minhas Solicitações")
    df = carregar_solicitacoes()
    mine = df[df["solicitante"] == user]
    st.dataframe(mine)


# ========== APROVAÇÕES ==========
if menu == "Requisições Pendentes":
    st.header("📦 Aguardando Aprovação")
    df = carregar_solicitacoes()
    pend = df[df["status"] == "PENDENTE"]

    if pend.empty:
        st.info("Nenhuma requisição pendente.")
    else:
        for _, req in pend.iterrows():
            cod = req["codigo"]
            st.write(f"🔹 **{cod}** | {req['item']} | Qtd: {req['quantidade']}")

            col1, col2 = st.columns(2)

            if col1.button(f"Aprovar {cod}"):
                atualizar_status(cod, "APROVADO", user)
                st.rerun()

            if col2.button(f"Reprovar {cod}"):
                atualizar_status(cod, "REPROVADO", user, "Motivo não informado")
                st.rerun()


# ========== ROMANEIO ==========
if menu == "Romaneio":
    st.header("📋 Romaneio")

    df = carregar_solicitacoes()
    aprov = df[(df["status"] == "APROVADO") & (df["impresso"] != "SIM")]

    st.dataframe(aprov)

    if st.button("Marcar como Impresso"):
        marcar_impresso(aprov["codigo"].tolist())
        st.success("✔ Romaneio atualizado!")
        st.rerun()


# ========== HISTÓRICO ==========
if menu == "Histórico Completo":
    st.header("📚 Histórico Geral")
    df = carregar_solicitacoes()
    st.dataframe(df)


