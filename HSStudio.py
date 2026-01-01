import streamlit as st

st.set_page_config(page_title="Dragon Tiger – Leitura Inteligente", layout="wide")

# =============================
# ESTADO
# =============================
if "historico" not in st.session_state:
    st.session_state.historico = []

# =============================
# FUNÇÕES
# =============================
def analisar_padroes(hist):
    if len(hist) < 3:
        return "SEM LEITURA", "AGUARDE", 0.0

    ultimos = hist[-6:]
    ultimo = hist[-1]

    dragao = ultimos.count("D")
    tigre = ultimos.count("T")
    empate = ultimos.count("E")

    # Detecta sequência
    sequencia = 1
    for i in range(len(hist)-2, -1, -1):
        if hist[i] == ultimo:
            sequencia += 1
        else:
            break

    # Regras reais
    confianca = 0.0

    # Empate trava leitura
    if ultimo == "E":
        return "EMPATE RECENTE", "AGUARDE", 0.0

    # Sequência curta (1 a 3)
    if sequencia <= 3:
        confianca = 0.55
        return "CONTINUAÇÃO CURTA", ultimo, confianca

    # Sequência longa (4+)
    if sequencia >= 4:
        confianca = 0.65
        sugestao = "T" if ultimo == "D" else "D"
        return "POSSÍVEL QUEBRA", sugestao, confianca

    return "SEM PADRÃO CLARO", "AGUARDE", 0.0


def emoji(res):
    return "🐉" if res == "D" else "🐯" if res == "T" else "🤝"

# =============================
# INTERFACE
# =============================
st.title("🐉🐯 Dragon Tiger – Leitura & Sugestão Inteligente")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🎯 Inserir Resultado")

    if st.button("🐉 Dragão"):
        st.session_state.historico.append("D")

    if st.button("🐯 Tigre"):
        st.session_state.historico.append("T")

    if st.button("🤝 Empate"):
        st.session_state.historico.append("E")

    if st.button("🔄 Limpar Histórico"):
        st.session_state.historico = []

with col2:
    st.subheader("📜 Histórico (mais antigo → recente)")
    hist_emojis = [emoji(r) for r in st.session_state.historico]
    st.write(" ".join(hist_emojis[-60:]))

# =============================
# ANÁLISE
# =============================
st.divider()
st.subheader("🧠 Leitura Atual")

padrao, sugestao, confianca = analisar_padroes(st.session_state.historico)

if sugestao == "AGUARDE":
    st.warning(f"⚠️ {padrao} — NÃO ENTRAR")
else:
    cor = "🐉 DRAGÃO" if sugestao == "D" else "🐯 TIGRE"
    st.success(f"📌 PADRÃO: {padrao}")
    st.success(f"🎯 SUGESTÃO: {cor}")
    st.info(f"📊 CONFIANÇA: {int(confianca*100)}%")

# =============================
# ALERTAS
# =============================
st.divider()
st.subheader("🚨 Alertas Importantes")

if len(st.session_state.historico) >= 1 and st.session_state.historico[-1] == "E":
    st.error("Empate recente → Aguarde 1 a 2 rodadas")

if len(st.session_state.historico) >= 4:
    ult = st.session_state.historico[-1]
    seq = 1
    for i in range(len(st.session_state.historico)-2, -1, -1):
        if st.session_state.historico[i] == ult:
            seq += 1
        else:
            break
    if seq >= 4:
        st.error("Sequência longa detectada → risco alto / possível quebra")

# =============================
# RODAPÉ
# =============================
st.divider()
st.caption("⚠️ Este app NÃO garante ganhos. Ele apenas lê comportamento e fluxo.")
