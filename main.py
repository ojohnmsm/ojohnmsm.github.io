import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Carrega ou inicializa dados
estoque_file = 'estoque.csv'
historico_file = 'historico.csv'


# Funções para carregar e salvar dados
def carregar_estoque():
    estoque_padrao = {
        'Frango': 0, 'Costela': 0, 'Queijo': 0, 'Queijo com Bacon': 0,
        'Carne seca': 0, 'Empadinhas': 0, 'Pizza doce': 0, 'Pizza salgada': 0, 'Guaravita': 0
    }

    if os.path.exists(estoque_file):
        estoque_df = pd.read_csv(estoque_file, index_col=0)
        estoque = estoque_df.iloc[:, 0].to_dict()

        # Garante que todos os novos itens existam no estoque
        for item in estoque_padrao:
            if item not in estoque:
                estoque[item] = estoque_padrao[item]

        return estoque
    else:
        return estoque_padrao


def salvar_estoque():
    estoque_df = pd.DataFrame.from_dict(st.session_state.estoque, orient='index', columns=['Quantidade'])
    estoque_df.to_csv(estoque_file)


def carregar_historico():
    if os.path.exists(historico_file):
        df = pd.read_csv(historico_file)
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date  # Mantém apenas a data
        return df
    else:
        return pd.DataFrame(columns=['Data', 'Tipo', 'Sabor', 'Quantidade'])


def salvar_historico():
    st.session_state.historico.to_csv(historico_file, index=False)


# Inicializa os dados
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_estoque()

if 'historico' not in st.session_state:
    st.session_state.historico = carregar_historico()


# Registrar vendas
def registrar_venda(sabor, quantidade, data):
    if sabor in st.session_state.estoque and st.session_state.estoque[sabor] >= quantidade:
        st.session_state.estoque[sabor] -= quantidade
        novo_registro = pd.DataFrame({
            'Data': [data.date()], 'Tipo': ['Venda'], 'Sabor': [sabor], 'Quantidade': [quantidade]
        })
        st.session_state.historico = pd.concat([st.session_state.historico, novo_registro], ignore_index=True)
        salvar_estoque()
        salvar_historico()
        st.success('Venda registrada com sucesso!')
    else:
        st.error('Estoque insuficiente ou sabor inexistente.')


# Cadastrar produção
def cadastrar_producao(sabor, quantidade, data):
    if sabor not in st.session_state.estoque:
        st.session_state.estoque[sabor] = 0  # Adiciona novo item ao estoque

    st.session_state.estoque[sabor] += quantidade
    novo_registro = pd.DataFrame({
        'Data': [data.date()], 'Tipo': ['Produção'], 'Sabor': [sabor], 'Quantidade': [quantidade]
    })
    st.session_state.historico = pd.concat([st.session_state.historico, novo_registro], ignore_index=True)
    salvar_estoque()
    salvar_historico()
    st.success('Produção cadastrada com sucesso!')


# Função para resetar o estoque e o histórico
def resetar_dados():
    if os.path.exists(estoque_file):
        os.remove(estoque_file)
    if os.path.exists(historico_file):
        os.remove(historico_file)

    # Recarregar os dados zerados na sessão
    st.session_state.estoque = {'Frango': 10, 'Camarão': 8, 'Palmito': 5}
    st.session_state.historico = pd.DataFrame(columns=['Data', 'Tipo', 'Sabor', 'Quantidade'])

    # Salvar os arquivos zerados
    salvar_estoque()
    salvar_historico()

    st.success("Estoque e histórico resetados com sucesso!")


# Botão para resetar os dados
if st.button("🔄 Resetar Estoque e Histórico"):
    resetar_dados()

# Interface do app
st.title('📦 estoques HOJE TEM')

# Estoque atual como tabela
st.header('📊 Estoque Atual')
estoque_df = pd.DataFrame.from_dict(st.session_state.estoque, orient='index', columns=['Quantidade'])
estoque_df = estoque_df[estoque_df['Quantidade'] > 0]  # Mostra apenas itens com 1 ou mais
st.dataframe(estoque_df)

st.divider()

# Registrar venda
st.header('Registrar Venda')
with st.form('form_venda'):
    sabor_venda = st.selectbox('Sabor vendido:', options=list(st.session_state.estoque.keys()))
    quantidade_venda = st.number_input('Quantidade vendida:', min_value=1, step=1)
    data_venda = st.date_input('Data da venda:', value=datetime.now().date())
    if st.form_submit_button('Registrar Venda'):
        registrar_venda(sabor_venda, quantidade_venda, pd.to_datetime(data_venda))

st.divider()

# Cadastrar produção
st.header('Cadastrar Produção')
with st.form('form_producao'):
    novo_sabor = st.text_input('Digite um novo item ou selecione um existente:')
    sabor_producao = st.selectbox('Sabor produzido:', options=list(st.session_state.estoque.keys()))
    sabor_producao = novo_sabor if novo_sabor else sabor_producao  # Usa o novo item, se digitado
    quantidade_producao = st.number_input('Quantidade produzida:', min_value=1, step=1)
    data_producao = st.date_input('Data da produção:', value=datetime.now().date())
    if st.form_submit_button('Registrar Produção'):
        cadastrar_producao(sabor_producao, quantidade_producao, pd.to_datetime(data_producao))

st.divider()

# Histórico e resumo
st.header('📅 Histórico e Resumo das Vendas')

# Converter 'Data' para datetime antes de acessar .dt
st.session_state.historico['Data'] = pd.to_datetime(st.session_state.historico['Data'], errors='coerce')

hoje = datetime.now().date()
inicio_semana = hoje - timedelta(days=hoje.weekday())
mes_atual = hoje.month
ano_atual = hoje.year

# Filtragem corrigida
vendas_semana = st.session_state.historico[
    (st.session_state.historico['Tipo'] == 'Venda') &
    (st.session_state.historico['Data'].dt.date >= inicio_semana)
]

vendas_mes = st.session_state.historico[
    (st.session_state.historico['Tipo'] == 'Venda') &
    (st.session_state.historico['Data'].dt.month == mes_atual) &
    (st.session_state.historico['Data'].dt.year == ano_atual)
]

vendas_ano = st.session_state.historico[
    (st.session_state.historico['Tipo'] == 'Venda') &
    (st.session_state.historico['Data'].dt.year == ano_atual)
]

# Exibir
st.subheader('Vendas na Semana (acumulado)')
st.dataframe(vendas_semana)

st.subheader('Vendas no Mês (acumulado)')
st.dataframe(vendas_mes)

st.subheader('Vendas no Ano (acumulado)')
st.dataframe(vendas_ano)