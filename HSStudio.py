import streamlit as st

# ==============================
# CONFIG
# ==============================
st.set_page_config(
    page_title="Dragon Tiger • Leitura Profissional",
    layout="wide"
)

# ==============================
# ESTADO
# ==============================
if "historico" not in st.session_state:
    st.session_state.historico = []

# ==============================
# FUNÇÕES
# ==============================
def emoji(r):
    if r == "D":
        return "🐉"
    if r == "T":
        return "🐯"
    return "🤝"

def sequencia_atual(hist):
    if len(hist) < 2:
        return 1
    ultimo = hist[-1]
    seq = 1
    for i in range(len(hist) - 2, -1, -1):
        if hist[i] == ultimo:
            seq += 1
        else:
            break
    return seq

def detectar_alternancia(hist):
    if len(hist) < 4:
        return False
    return hist[-1] != hist[-2] and hist[-2] != hist[-3] and hist[-3] != hist[-4]

def analisar_jogo(hist):
    if len(hist) < 3:
        return {
            "padrao": "Poucos dados",
            "sugestao": "AGUARDE",
            "explicacao": "Ainda não há histórico suficiente."
        }

    ultimo = hist[-1]
    seq = sequencia_atual(hist)

    # EMPATE
    if ultimo == "E":
        return {
            "padrao": "Empate",
            "sugestao": "AGUARDE",
            "explicacao": "Empate é usado para confundir. Aguarde 1–2 rodadas."
        }

    # ALTERNÂNCIA
    if detectar_alternancia(hist):
        return {
            "padrao": "Alternância",
            "sugestao": "AGUARDE",
            "explicacao": "Alternância constante não gera leitura confiável."
        }

    # CONTINUIDADE CURTA
    if seq == 2 or seq == 3:
        lado = "🐉 Dragão" if ultimo == "D" else "🐯 Tigre"
        return {
            "padrao": "Continuidade curta",
            "sugestao": lado,
            "explicacao": "Sequência curta tende a continuar."
        }

    # QUEBRA
    if seq >= 4:
        lado = "🐯 Tigre" if ultimo == "D" else "🐉 Dragão"
        return {
            "padrao": "Quebra provável",
            "sugestao": lado,
            "explicacao": "Sequência longa. Cassino costuma quebrar."
        }

    return {
        "padrao": "Caos",
        "sugestao": "AGUARDE",
        "explicacao": "Sem padrão confiável no momento."
    }

# ==============================
# INTERFACE
# ==============================
st.title("🐉🐯 Dragon Tiger — Leitura Profissional")

c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("🎯 Inserir Resultado")

    if st.button("🐉 Dragão"):
        st.session_state.historico.append("D")

    if st.button("🐯 Tigre"):
        st.session_state.historico.append("T")

    if st.button("🤝 Empate"):
        st.session_state.historico.append("E")

    if st.button("🔄 Limpar Histórico"):
        st.session_state.historico = []

with c2:
    st.subheader("📜 Histórico")
    st.write(" ".join(emoji(x) for x in st.session_state.historico[-60:]))

# ==============================
# ANÁLISE
# ==============================
st.divider()
st.subheader("🧠 Análise Atual")

resultado = analisar_jogo(st.session_state.historico)

st.info(f"📌 PADRÃO: **{resultado['padrao']}**")
st.write(resultado["explicacao"])

if resultado["sugestao"] == "AGUARDE":
    st.error("🚫 SUGESTÃO: NÃO ENTRAR")
else:
    st.success(f"🎯 SUGESTÃO DE APOSTA: **{resultado['sugestao']}**")

# ==============================
# EDUCATIVO
# ==============================
st.divider()
st.subheader("📘 Regras do Sistema")

st.markdown("""
- ✅ Entrar apenas em **continuidade curta**
- ⚠️ Quebra após **4 ou mais iguais**
- 🚫 Empate bloqueia leitura
- ❌ Alternância não é padrão
- 🛑 Sem padrão = proteger banca
""")

st.caption("Este sistema não promete ganhos. Ele evita erros e protege a banca.")
