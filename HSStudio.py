import streamlit as st

st.set_page_config(
    page_title="Dragon Tiger • Leitura Profissional REAL",
    layout="wide"
)

# =============================
# ESTADO
# =============================
if "hist" not in st.session_state:
    st.session_state.hist = []

if "cooldown" not in st.session_state:
    st.session_state.cooldown = 0

# =============================
# FUNÇÕES BÁSICAS
# =============================
def em(x):
    return "🐉" if x == "D" else "🐯" if x == "T" else "🤝"

def sequencia(hist):
    if len(hist) < 2:
        return 1
    u = hist[-1]
    s = 1
    for i in range(len(hist)-2, -1, -1):
        if hist[i] == u:
            s += 1
        else:
            break
    return s

def alternancia(hist):
    if len(hist) < 4:
        return False
    return hist[-1] != hist[-2] != hist[-3] != hist[-4]

def empate_recente(hist, n=2):
    return "E" in hist[-n:]

# =============================
# CÉREBRO REAL (SEM FORÇAR)
# =============================
def analisar(hist):
    # REGRA 0 — SEM DADOS
    if len(hist) < 6:
        return ("Poucos dados", "AGUARDE", "Histórico insuficiente")

    # REGRA 1 — COOLDOWN
    if st.session_state.cooldown > 0:
        st.session_state.cooldown -= 1
        return ("Cooldown ativo", "AGUARDE", "Sistema travado por segurança")

    # REGRA 2 — EMPATE BLOQUEIA
    if empate_recente(hist, 2):
        st.session_state.cooldown = 1
        return ("Empate recente", "AGUARDE", "Empate quebra leitura")

    # REGRA 3 — ALTERNÂNCIA BLOQUEIA
    if alternancia(hist):
        return ("Alternância", "AGUARDE", "Jogo em zigue-zague")

    # REGRA 4 — SEQUÊNCIA
    seq = sequencia(hist)
    ultimo = hist[-1]

    # SEQUÊNCIA LONGA = PROIBIDO
    if seq >= 4:
        st.session_state.cooldown = 1
        return ("Sequência longa", "AGUARDE", "Risco alto de quebra")

    # ÚNICA CONDIÇÃO DE ENTRADA
    if seq == 2 or seq == 3:
        lado = "🐉 Dragão" if ultimo == "D" else "🐯 Tigre"
        return (
            "Continuidade curta LIMPA",
            lado,
            "Entrada permitida (padrão válido)"
        )

    # FALLBACK
    return ("Caos", "AGUARDE", "Sem vantagem estatística")

# =============================
# INTERFACE
# =============================
st.title("🐉🐯 Dragon Tiger — Leitura Profissional (SEM FORÇAR)")

c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("🎯 Inserir Resultado")
    if st.button("🐉 Dragão"):
        st.session_state.hist.append("D")
    if st.button("🐯 Tigre"):
        st.session_state.hist.append("T")
    if st.button("🤝 Empate"):
        st.session_state.hist.append("E")
    if st.button("🔄 Limpar"):
        st.session_state.hist = []
        st.session_state.cooldown = 0

with c2:
    st.subheader("📜 Histórico")
    st.write(" ".join(em(x) for x in st.session_state.hist[-60:]))

# =============================
# ANÁLISE
# =============================
st.divider()
st.subheader("🧠 Diagnóstico REAL")

padrao, sugestao, motivo = analisar(st.session_state.hist)

st.info(f"📌 Padrão: **{padrao}**")
st.write(f"🧾 Motivo: {motivo}")

if sugestao == "AGUARDE":
    st.error("🚫 SUGESTÃO: NÃO ENTRAR")
else:
    st.success(f"🎯 SUGESTÃO: **{sugestao}**")

# =============================
# TRANSPARÊNCIA
# =============================
st.divider()
st.subheader("⚠️ Regras do Sistema")

st.markdown("""
- **AGUARDE é o padrão**
- Só entra em **continuidade curta LIMPA**
- Empate trava o sistema
- Alternância é proibida
- Sequência longa é proibida
- Cooldown impede overtrade
""")

st.caption("Sistema conservador. Não força entrada. Protege banca.")
