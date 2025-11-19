import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Football Studio Card Analyzer - Profissional
# Implementa a metodologia: mapeamento de valores, classificação
# (alta/média/baixa), detecção de padrões, previsão heurística, sugestão de aposta,
# histórico com inserção manual via botões, exportação e visualização em linhas (9 por linha).

# ----------------------------- Configurações -----------------------------
st.set_page_config(page_title="Football Studio Analyzer - Profissional",
                   layout="wide",
                   initial_sidebar_state="expanded")

st.title("Football Studio Analyzer - Profissional")
st.markdown("Aplicativo em Python (Streamlit) que implementa integralmente a metodologia de análise por valor de cartas, sem alterações nas regras fornecidas.")

# ----------------------------- Constantes -----------------------------
CARD_MAP = {
    'A': 14, 'K': 13, 'Q': 12, 'J': 11,
    '10': 10, '9': 9, '8': 8, '7': 7, '6': 6,
    '5': 5, '4': 4, '3': 3, '2': 2
}

HIGH = set(['A', 'K', 'Q', 'J'])
MEDIUM = set(['10', '9', '8'])
LOW = set(['7', '6', '5', '4', '3', '2'])

MAX_COLS = 9  # resultados por linha
MAX_LINES = 10

# ----------------------------- Utilitários -----------------------------

def card_value(card_label: str) -> int:
    return CARD_MAP.get(str(card_label), 0)


def classify_card(card_label: str) -> str:
    """Classifica a carta como 'alta', 'media' ou 'baixa'."""
    if card_label in HIGH:
        return 'alta'
    if card_label in MEDIUM:
        return 'media'
    return 'baixa'


def pattern_of_sequence(history: pd.DataFrame) -> str:
    """Detecta padrão simples entre repetição, alternância, degrau (duo-duo), quebra/controlada."""
    if history.empty:
        return 'indefinido'

    winners = history['winner'].tolist()
    # repetição: últimos 3 iguais
    if len(winners) >= 3 and winners[-1] == winners[-2] == winners[-3]:
        return 'repetição'

    # alternância: ABAB nos últimos 4
    if len(winners) >= 4 and winners[-1] == winners[-3] and winners[-2] == winners[-4] and winners[-1] != winners[-2]:
        return 'alternância'

    # degrau: duo-duo (A A B B A A)
    if len(winners) >= 6:
        seq = winners[-6:]
        if seq[0] == seq[1] and seq[2] == seq[3] and seq[4] == seq[5] and seq[0] == seq[4] and seq[1] == seq[5]:
            return 'degrau'

    # quebra controlada heurística: presença de cartas baixas seguidas e depois alta
    vals = history['value_class'].tolist()
    if len(vals) >= 3 and vals[-1] == 'alta' and vals[-2] == 'baixa' and vals[-3] == 'baixa':
        return 'quebra controlada'

    return 'indefinido'


def analyze_tendency(history: pd.DataFrame) -> dict:
    """Analisa as últimas jogadas e retorna tendência e probabilidades heurísticas."""
    if history.empty:
        return {'pattern': 'indefinido', 'prob_red': 0.0, 'prob_blue': 0.0, 'prob_tie': 0.0, 'suggestion': 'aguardar', 'confidence': 0.0}

    last = history.iloc[-1]
    last_class = last['value_class']
    pattern = pattern_of_sequence(history)

    prob = {'red': 0.0, 'blue': 0.0, 'tie': 0.0}

    if last_class == 'alta':
        repeat_prob = 0.70
        other_prob = (1 - repeat_prob)
        if last['winner'] == 'red':
            prob['red'] = repeat_prob
            prob['blue'] = other_prob * 0.95
        else:
            prob['blue'] = repeat_prob
            prob['red'] = other_prob * 0.95
        prob['tie'] = other_prob * 0.05
        confidence = 0.7
    elif last_class == 'media':
        if pattern == 'repetição':
            base = 0.6
        else:
            base = 0.52
        if last['winner'] == 'red':
            prob['red'] = base
            prob['blue'] = 1 - base - 0.03
        else:
            prob['blue'] = base
            prob['red'] = 1 - base - 0.03
        prob['tie'] = 0.03
        confidence = 0.55
    else:
        break_prob = 0.75
        if last['winner'] == 'red':
            prob['blue'] = break_prob
            prob['red'] = 1 - break_prob - 0.04
        else:
            prob['red'] = break_prob
            prob['blue'] = 1 - break_prob - 0.04
        prob['tie'] = 0.04
        confidence = 0.75

    # Ajustes por padrão
    if pattern == 'repetição':
        if last['winner'] == 'red':
            prob['red'] = min(0.95, prob['red'] + 0.12)
        else:
            prob['blue'] = min(0.95, prob['blue'] + 0.12)
        confidence = max(confidence, 0.75)
    elif pattern == 'alternância':
        if last['winner'] == 'red':
            prob['blue'] = max(prob['blue'], 0.55)
            prob['red'] = 1 - prob['blue'] - prob['tie']
        else:
            prob['red'] = max(prob['red'], 0.55)
            prob['blue'] = 1 - prob['red'] - prob['tie']
        confidence = max(confidence, 0.6)
    elif pattern == 'degrau':
        if len(history) >= 2 and history.iloc[-2]['winner'] == last['winner']:
            if last['winner'] == 'red':
                prob['red'] = max(prob['red'], 0.7)
            else:
                prob['blue'] = max(prob['blue'], 0.7)
            confidence = max(confidence, 0.7)
    elif pattern == 'quebra controlada':
        prob['tie'] = max(prob['tie'], 0.06)
        if last['winner'] == 'red':
            prob['red'] = max(prob['red'], 0.6)
        else:
            prob['blue'] = max(prob['blue'], 0.6)
        confidence = max(confidence, 0.65)

    total = prob['red'] + prob['blue'] + prob['tie']
    if total <= 0:
        prob = {'red': 0.49, 'blue': 0.49, 'tie': 0.02}
        total = 1.0
    for k in prob:
        prob[k] = prob[k] / total

    prob_pct = {k: round(v * 100, 1) for k, v in prob.items()}

    sorted_probs = sorted(prob_pct.items(), key=lambda x: x[1], reverse=True)
    top_label, top_val = sorted_probs[0]
    suggestion = 'aguardar'
    if top_val >= 60 or confidence >= 0.7:
        if top_label == 'red':
            suggestion = 'apostar RED (🔴)'
        elif top_label == 'blue':
            suggestion = 'apostar BLUE (🔵)'
        else:
            suggestion = 'apostar TIE (🟡)'

    return {
        'pattern': pattern,
        'prob_red': prob_pct['red'],
        'prob_blue': prob_pct['blue'],
        'prob_tie': prob_pct['tie'],
        'suggestion': suggestion,
        'confidence': round(confidence * 100, 1)
    }


def manipulation_level(history: pd.DataFrame) -> int:
    """Deriva um nível de manipulação de 1 a 9 usando heurísticas."""
    if history.empty:
        return 1

    vals = history['value_class'].tolist()
    winners = history['winner'].tolist()

    score = 0.0
    low_runs = 0
    run = 0
    for v in vals:
        if v == 'baixa':
            run += 1
        else:
            if run >= 2:
                low_runs += 1
            run = 0
    if run >= 2:
        low_runs += 1

    score += low_runs * 1.2

    alternations = 0
    for i in range(1, len(winners)):
        if winners[i] != winners[i - 1]:
            alternations += 1
    alternation_rate = alternations / max(1, (len(winners) - 1))
    score += alternation_rate * 3.0

    high_count = sum(1 for v in vals if v == 'alta')
    high_rate = high_count / max(1, len(vals))
    score -= high_rate * 2.0

    level = int(min(9, max(1, round(score))))
    return level

# ----------------------------- Inicialização do estado -----------------------------
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['timestamp', 'winner', 'card', 'value', 'value_class'])

# Funções para manipular o histórico

def add_result(winner: str, card_label: str):
    now = datetime.now()
    v = card_value(card_label)
    vc = classify_card(card_label)
    new_row = pd.DataFrame([{
        'timestamp': now,
        'winner': winner,
        'card': card_label,
        'value': v,
        'value_class': vc
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)


def reset_history():
    st.session_state.history = pd.DataFrame(columns=['timestamp', 'winner', 'card', 'value', 'value_class'])

# ----------------------------- Sidebar (controles) -----------------------------
with st.sidebar:
    st.header('Controles')
    st.markdown('Insira manualmente o resultado: selecione cor e carta, depois clique em Adicionar.')
    card_input = st.selectbox('Carta', options=list(CARD_MAP.keys()), index=0)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button('🔴 Adicionar RED'):
            add_result('red', card_input)
    with col2:
        if st.button('🔵 Adicionar BLUE'):
            add_result('blue', card_input)
    with col3:
        if st.button('🟡 Adicionar TIE'):
            add_result('tie', card_input)

    st.write('---')
    st.button('Resetar Histórico', on_click=reset_history)
    st.write('---')
    csv_data = st.session_state.history.to_csv(index=False)
    st.download_button('Exportar histórico (CSV)', data=csv_data, file_name='history_football_studio.csv')
    st.write('---')
    st.markdown('Configurações de exibição:')
    show_timestamps = st.checkbox('Mostrar timestamps', value=False)
    show_confidence_bar = st.checkbox('Mostrar barras de confiança', value=True)

# ----------------------------- Main: Histórico e Visualização -----------------------------
st.subheader('Histórico (inserção manual por botões)')

history = st.session_state.history.copy()

# Limitar a exibição ao máximo permitido
if len(history) > MAX_COLS * MAX_LINES:
    history = history.tail(MAX_COLS * MAX_LINES).reset_index(drop=True)

if history.empty:
    st.info('Sem resultados ainda. Use os botões na barra lateral para inserir resultados.')
else:
    rows = []
    for i in range(0, len(history), MAX_COLS):
        rows.append(history.iloc[i:i + MAX_COLS])

    for r_idx, row_df in enumerate(rows):
        cols = st.columns(MAX_COLS)
        for c_idx in range(MAX_COLS):
            with cols[c_idx]:
                if c_idx < len(row_df):
                    item = row_df.iloc[c_idx]
                    label = ''
                    if item['winner'] == 'red':
                        label = f"🔴 {item['card']} ({item['value_class']})"
                    elif item['winner'] == 'blue':
                        label = f"🔵 {item['card']} ({item['value_class']})"
                    else:
                        label = f"🟡 {item['card']} ({item['value_class']})"
                    if show_timestamps:
                        st.caption(str(item['timestamp']))
                    st.markdown(f"**{label}**")
                else:
                    st.write('')

# ----------------------------- Análise e Previsões -----------------------------
st.subheader('Análise e Previsão')
analysis = analyze_tendency(st.session_state.history)
level = manipulation_level(st.session_state.history)

colA, colB = st.columns([2, 1])
with colA:
    st.markdown('**Padrão detectado:** ' + analysis['pattern'].capitalize())
    st.markdown('**Nível de manipulação estimado (1–9):** ' + str(level))
    st.markdown('**Sugestão:** ' + analysis['suggestion'])
    st.markdown(f"**Confiança do modelo:** {analysis['confidence']} %")

    st.markdown('**Probabilidades estimadas (heurísticas):**')
    st.progress(0)
    pb = st.columns(3)
    with pb[0]:
        st.metric('🔴 RED', f"{analysis['prob_red']} %")
    with pb[1]:
        st.metric('🔵 BLUE', f"{analysis['prob_blue']} %")
    with pb[2]:
        st.metric('🟡 TIE', f"{analysis['prob_tie']} %")

with colB:
    st.markdown('**Resumo das últimas jogadas (últimas 10):**')
    st.dataframe(st.session_state.history.tail(10).reset_index(drop=True))

st.markdown('---')
st.subheader('Interpretação dos sinais (por valor de carta)')
st.markdown('''
- Cartas **A, K, Q, J**: consideradas **ALTAS**. Vitória com alta tende a repetir — aposta na cor vencedora com confiança.
- Cartas **10, 9, 8**: consideradas **MÉDIAS**. Zona de transição — observar sinais antes de apostar.
- Cartas **7–2**: consideradas **BAIXAS**. Alto risco de quebra; geralmente sinalizam instabilidade.
''')

st.subheader('Estratégia operacional (passo a passo)')
st.markdown('''
1. Analise as últimas 3 cartas e categorização (alta/média/baixa).
2. Identifique o padrão ativo: repetição, alternância, degrau, ou quebra controlada.
3. Só entre em aposta quando a sugestão e a confiança estiverem alinhadas (por exemplo, prob >= 60% ou confiança >= 70%).
4. Em casos de cartas baixas, priorize esperar por confirmação de quebra antes de seguir a cor anterior.
5. Use gestão de banca conservadora mesmo com sugestão (stake proporcional ao nível de confiança).
''')

# Ferramentas avançadas
st.markdown('---')
st.header('Ferramentas avançadas')
colx, coly = st.columns(2)
with colx:
    if st.button('Auto-analise (aplicar heurísticas nas últimas 3)'):
        st.write(analysis)
with coly:
    if st.button('Exportar relatório simples (TXT)'):
        # construir texto com quebras de linha corretas
        txt = ""
        txt += "Football Studio Analyzer - Relatório\n"
        txt += f"Gerado em: {datetime.now()}\n"
        txt += f"Padrão: {analysis['pattern']}\n"
        txt += f"Nível de manipulação: {level}\n"
        txt += f"Sugestão: {analysis['suggestion']}\n"
        txt += f"Probabilidades: RED {analysis['prob_red']}%, BLUE {analysis['prob_blue']}%, TIE {analysis['prob_tie']}%\n"
        st.download_button('Baixar relatório', data=txt, file_name='relatorio_football_studio.txt')

st.markdown('---')
st.caption('Este sistema aplica as heurísticas e a metodologia conforme solicitado. As probabilidades são estimativas heurísticas e não garantem lucro. Aposte com responsabilidade.')

# EOF
