import sys
import yfinance as yf
import numpy as np
import pandas as pd
import pickle
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Funções para calcular o Índice de Sharpe e manipular a SELIC
def calcular_sharpe(ticker, selic_rate, period='6mo', considerar_dividendos=True):
    try:
        data = yf.download(ticker, period=period, actions=True)
        if data.empty or len(data['Close']) <= 1:
            raise ValueError(f"Poucos ou nenhum dado disponível para calcular o desvio padrão para o ticker {ticker} com o período '{period}'.")

        data['Return'] = data['Close'].pct_change()
        mean_return = data['Return'].mean()
        std_dev_return = data['Return'].std()
        total_dividendos = data['Dividends'].sum()

        # Índice de Sharpe sem considerar dividendos
        sharpe_ratio_sem_dividendos = (mean_return * 252 - selic_rate) / (std_dev_return * np.sqrt(252))
        
        if considerar_dividendos:
            sharpe_ratio = ((mean_return * 252) + total_dividendos - selic_rate) / (std_dev_return * np.sqrt(252))
        else:
            sharpe_ratio = sharpe_ratio_sem_dividendos
        
        # Avaliar o Índice de Sharpe sem considerar dividendos
        if not considerar_dividendos:
            if sharpe_ratio_sem_dividendos > 1:
                avaliacao = 'Muito Bom'
            elif sharpe_ratio_sem_dividendos > 0.5:
                avaliacao = 'Bom'
            elif sharpe_ratio_sem_dividendos >= 0:
                avaliacao = 'Medíocre'
            else:
                avaliacao = 'Ruim'
        else:
            avaliacao = 'Avaliação não realizada para o Índice de Sharpe com dividendos'

        return sharpe_ratio, total_dividendos, avaliacao, sharpe_ratio_sem_dividendos

    except Exception as e:
        return None, None, f"Erro ao baixar os dados: {e}", None

def salvar_selic(selic_rate):
    with open('selic_rate.pkl', 'wb') as f:
        pickle.dump(selic_rate, f)

def carregar_selic():
    if os.path.exists('selic_rate.pkl'):
        with open('selic_rate.pkl', 'rb') as f:
            return pickle.load(f)
    return 0.105

def salvar_periodo(periodo):
    with open('periodo.pkl', 'wb') as f:
        pickle.dump(periodo, f)

def carregar_periodo():
    if os.path.exists('periodo.pkl'):
        with open('periodo.pkl', 'rb') as f:
            return pickle.load(f)
    return '6mo'

# Função para iniciar a análise
def iniciar_analise():
    tickers = ticker_input.get()
    if not tickers:
        messagebox.showwarning("Erro", "Por favor, insira ao menos um ticker.")
        return

    tickers = [ticker.strip() for ticker in tickers.split(',')]
    resultados = []

    for ticker in tickers:
        sharpe_ratio_com_dividendos, total_dividendos, avaliacao_sem_dividendos, sharpe_ratio_sem_dividendos = calcular_sharpe(ticker, selic_rate, periodo, considerar_dividendos=False)
        sharpe_ratio_com_dividendos, total_dividendos, _, _ = calcular_sharpe(ticker, selic_rate, periodo)

        if sharpe_ratio_sem_dividendos is not None and sharpe_ratio_com_dividendos is not None:
            resultados.append({
                'Ticker': ticker,
                'Índice de Sharpe (Sem Dividendos)': sharpe_ratio_sem_dividendos,
                'Índice de Sharpe (Com Dividendos)': sharpe_ratio_com_dividendos,
                'Dividendos Totais': total_dividendos,
                'Avaliação (Sem Dividendos)': avaliacao_sem_dividendos
            })
        else:
            resultados.append({
                'Ticker': ticker,
                'Índice de Sharpe (Sem Dividendos)': None,
                'Índice de Sharpe (Com Dividendos)': None,
                'Dividendos Totais': None,
                'Avaliação (Sem Dividendos)': avaliacao_sem_dividendos
            })

    df_resultados = pd.DataFrame(resultados)

    # Ordenar os dados pelo Índice de Sharpe (Sem Dividendos)
    df_resultados_sorted = df_resultados.sort_values(by='Índice de Sharpe (Sem Dividendos)', ascending=False, na_position='last')

    # Limpar a tabela antes de adicionar novos dados
    for i in tree.get_children():
        tree.delete(i)

    # Atualizar a tabela com os resultados ordenados
    for i, row in df_resultados_sorted.iterrows():
        tree.insert('', 'end', values=(
            row['Ticker'],
            f"{row['Índice de Sharpe (Sem Dividendos)']:.4f}" if pd.notna(row['Índice de Sharpe (Sem Dividendos)']) else 'N/A',
            f"{row['Índice de Sharpe (Com Dividendos)']:.4f}" if pd.notna(row['Índice de Sharpe (Com Dividendos)']) else 'N/A',
            f"{row['Dividendos Totais']:.2f}" if pd.notna(row['Dividendos Totais']) else 'N/A',
            row['Avaliação (Sem Dividendos)']
        ))

    messagebox.showinfo("Análise Concluída", "A análise foi concluída. Verifique a tabela para os resultados.")

# Função para alterar a taxa SELIC
def alterar_selic():
    global selic_rate
    nova_selic = simpledialog.askfloat("Alterar SELIC", "Digite a nova taxa SELIC (em decimal, ex: 0.105 para 10,5%):", initialvalue=selic_rate, minvalue=0)
    if nova_selic is not None:
        selic_rate = nova_selic
        salvar_selic(nova_selic)
        messagebox.showinfo("Sucesso", f"Taxa SELIC alterada para {nova_selic * 100:.2f}% e salva com sucesso.")

# Função para alterar o período de comparação
def alterar_periodo():
    global periodo
    novo_periodo = simpledialog.askstring("Alterar Período de Comparação", "Digite o novo período de comparação (ex: 1mo, 3mo, 6mo, 1y):", initialvalue=periodo)
    if novo_periodo:
        periodo = novo_periodo
        salvar_periodo(novo_periodo)
        messagebox.showinfo("Sucesso", f"Período de comparação alterado para {novo_periodo} e salvo com sucesso.")

# Configurações iniciais
selic_rate = carregar_selic()
periodo = carregar_periodo()

# Criação da interface Tkinter
root = tk.Tk()
root.title("Análise de Índice de Sharpe")
root.geometry("800x600")

# Layout
frame = tk.Frame(root)
frame.pack(pady=20)

ticker_label = tk.Label(frame, text="Digite os tickers separados por vírgula (ex: PETR4.SA, ITUB4.SA):")
ticker_label.pack()

ticker_input = tk.Entry(frame, width=50)
ticker_input.pack(pady=5)

analisar_button = tk.Button(frame, text="Iniciar Análise", command=iniciar_analise)
analisar_button.pack(pady=10)

selic_button = tk.Button(frame, text="Alterar SELIC", command=alterar_selic)
selic_button.pack(pady=5)

periodo_button = tk.Button(frame, text="Alterar Período de Comparação", command=alterar_periodo)
periodo_button.pack(pady=5)

# Tabela para exibir resultados
columns = ('Ticker', 'Sharpe (Sem Dividendos)', 'Sharpe (Com Dividendos)', 'Dividendos Totais', 'Avaliação (Sem Dividendos)')
tree = ttk.Treeview(frame, columns=columns, show='headings')
tree.pack(pady=20)

for col in columns:
    tree.heading(col, text=col)

root.mainloop()
