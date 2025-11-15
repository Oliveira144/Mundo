# streamlit_app_evoluido.py
import streamlit as st
import pandas as pd
import math
from collections import Counter
import numpy as np

st.set_page_config(page_title="Analisador Avançado Football Studio", layout="wide")

# --- Config ---
VALORES_CARTA = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 11, "Q": 12, "K": 13, "A": 14
}
RESULTS = ["Home", "Away", "Draw"]

# --- Utilities de análise ---


def valor_carta(carta):
    return VALORES_CARTA.get(carta, 0)


def vencedor_row(row):
    # aceita tanto linhas com "Carta Home"/"Carta Away" quanto campo "Resultado" (se setado por botões)
    if "Resultado" in row and pd.notna(row["Resultado"]):
        return row["Resultado"]
    if pd.isna(row.get("Carta Home")) or pd.isna(row.get("Carta Away")):
        return None
    h = valor_carta(row["Carta Home"])
    a = valor_carta(row["Carta Away"])
    if h > a:
        return "Home"
    if a > h:
        return "Away"
    return "Draw"


def seq_vencedores_from_df(df):
    winners = []
    for i in range(len(df)):
        w = vencedor_row(df.iloc[i])
        if w is not None:
            winners.append(w)
    return winners


def identifica_streaks_from_winners(winners):
    streaks = []
    if not winners:
        return streaks
    cur = winners[0]
    length = 1
    for w in winners[1:]:
        if w == cur and w != "Draw":
            length += 1
        else:
            if length > 1 and cur != "Draw":
                streaks.append({"vencedor": cur, "tamanho": length})
            cur = w
            length = 1
    if length > 1 and cur != "Draw":
        streaks.append({"vencedor": cur, "tamanho": length})
    return streaks


def alternation_rate(winners):
    if len(winners) < 2:
        return 0.0
    changes = sum(1 for i in range(1, len(winners)) if winners[i] != winners[i-1])
    return changes / (len(winners) - 1)


def entropy_of_distribution(counts):
    total = sum(counts.values())
    if total == 0:
        return 0.0
    ent = 0.0
    for v in counts.values():
        p = v / total
        if p > 0:
            ent -= p * math.log2(p)
    return ent


def recency_weighted_probs(winners, decay=0.06):
    # peso exponencial: item mais recente tem peso 1, antes: exp(-decay * steps_from_end)
    weights = {"Home": 0.0, "Away": 0.0, "Draw": 0.0}
    n = len(winners)
    for i, w in enumerate(winners):
        # steps from end (0 for last)
        s = n - 1 - i
        weight = math.exp(-decay * s)
        weights[w] += weight
    total = sum(weights.values())
    if total == 0:
        return {k: 1/3 for k in weights}
    return {k: weights[k] / total for k in weights}


def simple_frequency_probs(winners):
    c = Counter(winners)
    total = sum(c.values())
    if total == 0:
        return {k: 1/3 for k in RESULTS}
    return {k: c.get(k, 0) / total for k in RESULTS}


def prediction_with_streak_bias(winners, recency_decay=0.06):
    """Combina frequência simples, ponderada por recência, e aplica bias por streak final."""
    base = simple_frequency_probs(winners)
    rec = recency_weighted_probs(winners, decay=recency_decay)

    # combinar (média ponderada)
    combined = {k: (base[k] * 0.4 + rec[k] * 0.6) for k in RESULTS}

    # Viés por continuidade de streak: se houver uma streak atual longa, aumenta probabilidade de continuidade
    if len(winners) >= 1:
        last = winners[-1]
        # conta comprimento do streak final (somente Home/Away)
        streak_len = 1
        for i in range(len(winners) - 2, -1, -1):
            if winners[i] == last and last != "Draw":
                streak_len += 1
            else:
                break
        if last != "Draw" and streak_len >= 2:
            # aplicar multiplicador suave:
            boost = min(0.25, 0.05 * streak_len)  # até +25% máximo
            combined[last] += boost
            # normalizar
            s = sum(combined.values())
            combined = {k: combined[k] / s for k in combined}
    return combined


def compute_manipulation_level(winners):
    """
    Heurística rápida para 1..10 baseada em:
    - maior streak encontrado (quanto maior -> maior nível)
    - alternation rate (muito alta indica manipulação de alternância)
    - empates logo após streaks
    - entropia (baixo entropia = previsível -> manipulação possível)
    Resultado: inteiro 1..10 (1 baixo risco/manipulação, 10 alto)
    """
    if not winners:
        return 1

    streaks = identifica_streaks_from_winners(winners)
    max_streak = max((s["tamanho"] for s in streaks), default=1)
    alt = alternation_rate(winners)
    c = Counter(winners)
    ent = entropy_of_distribution(c)

    # empates após streaks
    empates_pos = 0
    for i in range(len(winners) - 1):
        # se existe streak antes da pos i (simple check: lookback 2)
        if i - 2 >= 0:
            if winners[i-2] == winners[i-1] and winners[i] == "Draw":
                empates_pos += 1

    # score base 0..1
    score = 0.0
    # streak contribution
    score += min(0.35, 0.06 * max_streak)  # mais streak => mais score
    # alternation contribution
    score += min(0.35, alt * 0.7)
    # empates pós-streak
    score += min(0.2, 0.05 * empates_pos)
    # baixa entropia (previsibilidade) aumenta score
    # ent max para 3 outcomes é log2(3)=~1.585
    max_ent = math.log2(3)
    ent_norm = 1 - (ent / max_ent)  # 0 quando alta entropia, 1 quando baixa
    score += min(0.2, ent_norm * 0.4)

    # normalizar p/ 0..1
    score = max(0.0, min(score, 1.0))

    # mapear para 1..10
    level = 1 + int(score * 9)
    return max(1, min(10, level))


def compute_confidence(pred_probs, manip_level):
    """
    Confiança = função do gap entre top1 e soma dos outros, ajustada pelo nível de manipulação.
    Se manipulação alta -> confiança cai.
    Retorna 0..100 (porcentagem)
    """
    probs = list(pred_probs.values())
    top = max(probs)
    gap = top - sorted(probs)[-2]  # diferença entre top e segundo
    # base conf: top * (0.6 + gap*0.4)
    base_conf = top * (0.6 + gap * 0.4)
    # ajuste por manipulação (quanto maior manip_level, mais redução)
    adj = base_conf * (1.0 - (manip_level - 1) / 12.0)
    conf = max(0.0, min(1.0, adj))
    return round(conf * 100, 1)


# --- UI e estado ---

st.title("Analisador Avançado — Football Studio (Versão Evoluída)")

if "dados" not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=["Index", "Rodada", "Carta Home", "Carta Away", "Resultado"])

left, right = st.columns([1, 2])

with left:
    st.subheader("Entrada rápida")
    col1, col2 = st.columns([1, 1])
    with col1:
        # Entrada por cartas (para compatibilidade)
        rodada_num = st.number_input("Número da rodada", min_value=1, step=1, value=1)
        carta_home = st.selectbox("Carta Home", options=list(VALORES_CARTA.keys()), index=0)
        carta_away = st.selectbox("Carta Away", options=list(VALORES_CARTA.keys()), index=1)
        if st.button("Adicionar por Cartas"):
            nova = {
                "Index": len(st.session_state.dados),
                "Rodada": int(rodada_num),
                "Carta Home": carta_home,
                "Carta Away": carta_away,
                "Resultado": None
            }
            st.session_state.dados = pd.concat([st.session_state.dados, pd.DataFrame([nova])], ignore_index=True)
            st.session_state.dados = st.session_state.dados.sort_values("Rodada").reset_index(drop=True)
            st.success("Rodada adicionada (cartas).")
    with col2:
        st.markdown("**Entrada por Botões (rápido)**")
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("🔴 Home"):
                nova = {
                    "Index": len(st.session_state.dados),
                    "Rodada": len(st.session_state.dados) + 1,
                    "Carta Home": None,
                    "Carta Away": None,
                    "Resultado": "Home"
                }
                st.session_state.dados = pd.concat([st.session_state.dados, pd.DataFrame([nova])], ignore_index=True)
                st.session_state.dados = st.session_state.dados.sort_values("Rodada").reset_index(drop=True)
        with b2:
            if st.button("🔵 Away"):
                nova = {
                    "Index": len(st.session_state.dados),
                    "Rodada": len(st.session_state.dados) + 1,
                    "Carta Home": None,
                    "Carta Away": None,
                    "Resultado": "Away"
                }
                st.session_state.dados = pd.concat([st.session_state.dados, pd.DataFrame([nova])], ignore_index=True)
                st.session_state.dados = st.session_state.dados.sort_values("Rodada").reset_index(drop=True)
        with b3:
            if st.button("🟡 Draw"):
                nova = {
                    "Index": len(st.session_state.dados),
                    "Rodada": len(st.session_state.dados) + 1,
                    "Carta Home": None,
                    "Carta Away": None,
                    "Resultado": "Draw"
                }
                st.session_state.dados = pd.concat([st.session_state.dados, pd.DataFrame([nova])], ignore_index=True)
                st.session_state.dados = st.session_state.dados.sort_values("Rodada").reset_index(drop=True)

    st.markdown("---")
    if st.button("Limpar histórico"):
        st.session_state.dados = pd.DataFrame(columns=["Index", "Rodada", "Carta Home", "Carta Away", "Resultado"])
        st.success("Histórico limpo.")

with right:
    st.subheader("Histórico (últimas 90 linhas)")
    df_show = st.session_state.dados.copy().tail(90).reset_index(drop=True)
    # preencher coluna Resultado quando for por cartas
    df_show["Resultado"] = df_show.apply(lambda r: r["Resultado"] if pd.notna(r["Resultado"]) else vencedor_row(r), axis=1)
    st.dataframe(df_show[["Rodada", "Carta Home", "Carta Away", "Resultado"]])

# --- Análises ---
winners = seq_vencedores_from_df(st.session_state.dados.assign(Resultado=st.session_state.dados.get("Resultado", None)))
pred_probs = prediction_with_streak_bias(winners)
manip_level = compute_manipulation_level(winners)
confidence = compute_confidence(pred_probs, manip_level)

st.markdown("---")
colA, colB, colC = st.columns([1, 1, 1])
with colA:
    st.metric("Nº de rodadas", len(winners))
with colB:
    st.metric("Nível de Manipulação (1-10)", manip_level)
with colC:
    st.metric("Confiança previsão (%)", f"{confidence}%")

st.subheader("Probabilidades previstas para próxima rodada")
# ordenar por prob
sorted_preds = dict(sorted(pred_probs.items(), key=lambda x: x[1], reverse=True))
for k, v in sorted_preds.items():
    st.write(f"- **{k}** : {round(v*100,1)}%")

# Sugestão de aposta
st.subheader("Sugestão de Aposta")
top = max(pred_probs, key=pred_probs.get)
top_prob = pred_probs[top]
risk = "Alto" if manip_level >= 7 or confidence < 40 else ("Médio" if manip_level >= 4 or confidence < 65 else "Baixo")
if top_prob < 0.34:
    suggestion = "Sem sugestão confiável (probabilidades muito balanceadas)."
else:
    suggestion = f"Sugerido apostar em **{top}** — probabilidade estimada {round(top_prob*100,1)}% — risco: **{risk}**."

st.markdown(suggestion)

# Detalhes analíticos
st.markdown("---")
st.subheader("Detalhes da Análise (explicação)")
st.write("""
- **Como combinamos a previsão:** média entre frequência simples (40%) e frequência ponderada por recência (60%), com um viés adicional para continuidade de streaks recentes.
- **Nível de manipulação (1-10):** heurística baseada em maior streak, taxa de alternância, empates pós-streak e entropia da distribuição. Níveis altos dizem que o padrão é estranho/forçado.
- **Confiança (%):** deriva do gap entre top1 e top2, reduzida conforme aumenta o nível de manipulação.
""")

st.subheader("Métricas brutas")
st.write({
    "frequência simples (%)": {k: round(v*100, 2) for k, v in simple_frequency_probs(winners).items()},
    "ponderada recência (%)": {k: round(v*100, 2) for k, v in recency_weighted_probs(winners).items()},
    "predição combinada (%)": {k: round(v*100, 2) for k, v in pred_probs.items()},
    "alternation_rate": round(alternation_rate(winners), 3),
    "entropia": round(entropy_of_distribution(Counter(winners)), 3),
    "streaks": identifica_streaks_from_winners(winners)
})
