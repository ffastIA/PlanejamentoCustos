# ARQUIVO: otimizador/reporting/plotting.py

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import pandas as pd
from typing import List, Dict, Tuple

# Import relativo
from ..data_models import Turma


def gerar_grafico_turmas_projeto_mes(turmas: List[Turma], meses: List[str], meses_ferias: List[int]) -> str:
    """Gera gráfico de turmas ativas por projeto e mês."""
    from ..utils import calcular_meses_ativos

    projetos = sorted(list(set(t.projeto for t in turmas)))
    dados = {proj: [0] * len(meses) for proj in projetos}

    for t in turmas:
        meses_ativos = calcular_meses_ativos(t.mes_inicio, t.duracao, meses_ferias, len(meses))
        for m in meses_ativos:
            dados[t.projeto][m] += 1

    fig, ax = plt.subplots(figsize=(16, 8))
    bottom = [0] * len(meses)

    for proj in projetos:
        ax.bar(meses, dados[proj], bottom=bottom, label=proj, alpha=0.8)
        bottom = [bottom[i] + dados[proj][i] for i in range(len(meses))]

    for mes_idx in meses_ferias:
        if mes_idx < len(meses):
            ax.axvspan(mes_idx - 0.5, mes_idx + 0.5, color='red', alpha=0.1, zorder=0)

    ax.set_title('Demanda de Turmas por Projeto ao Longo do Tempo', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Mês', fontsize=12, fontweight='bold')
    ax.set_ylabel('Número de Turmas Ativas', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.3, axis='y')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    filepath = 'grafico_turmas_projeto_mes.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[✓] Gráfico de turmas por projeto/mês gerado: {filepath}")
    return filepath


def gerar_grafico_turmas_instrutor_tipologia_projeto(atribuicoes: List[Dict]) -> str:
    """Gera gráfico de turmas por instrutor, habilidade e projeto."""
    dados = defaultdict(lambda: defaultdict(int))

    for atr in atribuicoes:
        instrutor_id = atr['instrutor'].id
        projeto = atr['turma'].projeto
        dados[instrutor_id][projeto] += 1

    instrutores = sorted(dados.keys(), key=lambda x: (x.split('_')[0], int(x.split('_')[1])))
    projetos = sorted(list(set(proj for inst_data in dados.values() for proj in inst_data.keys())))

    fig, ax = plt.subplots(figsize=(16, 10))
    bar_width = 0.8
    bottom = [0] * len(instrutores)

    for proj in projetos:
        valores = [dados[inst].get(proj, 0) for inst in instrutores]
        ax.barh(instrutores, valores, bar_width, left=bottom, label=proj, alpha=0.85)
        bottom = [bottom[i] + valores[i] for i in range(len(instrutores))]

    ax.set_title('Distribuição de Turmas por Instrutor e Projeto', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Número de Turmas', fontsize=12, fontweight='bold')
    ax.set_ylabel('Instrutor', fontsize=12, fontweight='bold')
    ax.legend(loc='upper right', framealpha=0.9)
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()

    filepath = 'grafico_turmas_instrutor_projeto.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[✓] Gráfico de turmas por instrutor/projeto gerado: {filepath}")
    return filepath


def gerar_grafico_carga_por_instrutor(atribuicoes: List[Dict]) -> str:
    """Gera gráfico de carga total por instrutor."""
    carga_por_instrutor = defaultdict(int)

    for atr in atribuicoes:
        carga_por_instrutor[atr['instrutor'].id] += 1

    instrutores = sorted(carga_por_instrutor.keys(), key=lambda x: (x.split('_')[0], int(x.split('_')[1])))
    cargas = [carga_por_instrutor[i] for i in instrutores]

    cores = ['#2ecc71' if inst.startswith('PROG') else '#e74c3c' for inst in instrutores]

    fig, ax = plt.subplots(figsize=(16, 8))
    bars = ax.bar(instrutores, cargas, color=cores, alpha=0.8, edgecolor='black', linewidth=0.5)

    if cargas:
        spread = max(cargas) - min(cargas)
        ax.axhline(y=max(cargas), color='red', linestyle='--', linewidth=2, label=f'Máximo: {max(cargas)}')
        ax.axhline(y=min(cargas), color='blue', linestyle='--', linewidth=2, label=f'Mínimo: {min(cargas)}')
        ax.text(0.02, 0.98, f'Spread: {spread} turmas', transform=ax.transAxes, fontsize=14, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax.set_title('Carga Total por Instrutor (Balanceamento)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Instrutor', fontsize=12, fontweight='bold')
    ax.set_ylabel('Número de Turmas', fontsize=12, fontweight='bold')

    legend_prog = mpatches.Patch(color='#2ecc71', label='Programação', alpha=0.8)
    legend_rob = mpatches.Patch(color='#e74c3c', label='Robótica', alpha=0.8)
    handles, labels = ax.get_legend_handles_labels()
    handles.extend([legend_prog, legend_rob])
    ax.legend(handles=handles, loc='upper left', framealpha=0.9)

    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=90, ha='right')
    plt.tight_layout()

    filepath = 'grafico_carga_instrutor.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[✓] Gráfico de carga por instrutor gerado: {filepath}")
    return filepath


def gerar_grafico_demanda_prog_rob(turmas: List[Turma], meses: List[str], meses_ferias: List[int]) -> Tuple[
    str, pd.DataFrame]:
    """Gera gráfico de demanda mensal por habilidade."""
    from ..utils import calcular_meses_ativos

    dados_prog = [0] * len(meses)
    dados_rob = [0] * len(meses)

    for t in turmas:
        meses_ativos = calcular_meses_ativos(t.mes_inicio, t.duracao, meses_ferias, len(meses))
        for m in meses_ativos:
            if t.habilidade == 'PROG':
                dados_prog[m] += 1
            else:
                dados_rob[m] += 1

    fig, ax = plt.subplots(figsize=(16, 8))

    ax.plot(meses, dados_prog, marker='o', linewidth=2, markersize=8, label='Programação', color='#3498db')
    ax.plot(meses, dados_rob, marker='s', linewidth=2, markersize=8, label='Robótica', color='#e74c3c')

    for mes_idx in meses_ferias:
        if mes_idx < len(meses):
            ax.axvspan(mes_idx - 0.5, mes_idx + 0.5, color='gray', alpha=0.2,
                       label='Férias' if mes_idx == meses_ferias[0] else "")

    ax.set_title('Demanda Mensal: Programação vs. Robótica', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Mês', fontsize=12, fontweight='bold')
    ax.set_ylabel('Número de Turmas Ativas', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    filepath = 'grafico_demanda_prog_rob.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

    df = pd.DataFrame({'Mês': meses, 'Programação': dados_prog, 'Robótica': dados_rob,
                       'Total': [dados_prog[i] + dados_rob[i] for i in range(len(meses))]})

    print(f"[✓] Gráfico de demanda PROG/ROB gerado: {filepath}")
    return filepath, df


def gerar_grafico_fluxo_caixa(fluxo_caixa: Dict[str, Dict[str, float]],
                              meses: List[str]) -> str:
    """
    Gera gráfico de área empilhada do fluxo de caixa por projeto.
    """
    print("\n--- Gerando Gráfico de Fluxo de Caixa ---")

    # Preparar dados
    projetos = sorted(fluxo_caixa.keys())
    dados_grafico = []

    for projeto in projetos:
        custos_mensais = []
        for mes in meses:
            custo = fluxo_caixa[projeto].get(mes, 0.0)
            custos_mensais.append(custo)
        dados_grafico.append(custos_mensais)

    # Criar gráfico
    fig, ax = plt.subplots(figsize=(16, 8))

    # Gráfico de área empilhada
    ax.stackplot(meses, *dados_grafico, labels=projetos, alpha=0.8)

    # Linha do custo total
    custo_total_mensal = [sum(dados_grafico[i][j] for i in range(len(projetos)))
                          for j in range(len(meses))]
    ax.plot(meses, custo_total_mensal, 'k--', linewidth=2,
            label='Custo Total', marker='o', markersize=4)

    # Formatação
    ax.set_title('Fluxo de Caixa Mensal por Projeto', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Mês', fontsize=12, fontweight='bold')
    ax.set_ylabel('Custo (R$)', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', framealpha=0.9)
    ax.grid(True, alpha=0.3, axis='y')

    # Formatar eixo Y com valores monetários
    def format_func(value, tick_number):
        if value >= 1000:
            return f'R$ {value / 1000:.0f}k'
        return f'R$ {value:.0f}'

    ax.yaxis.set_major_formatter(plt.FuncFormatter(format_func))

    # Rotacionar labels do eixo X
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    filepath = 'grafico_fluxo_caixa.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[✓] Gráfico de fluxo de caixa gerado: {filepath}")
    return filepath