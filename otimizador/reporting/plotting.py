# ARQUIVO: otimizador/reporting/plotting.py

import os
from collections import defaultdict
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Import relativo
from ..data_models import Turma
from ..utils import calcular_meses_ativos


def gerar_grafico_turmas_projeto_mes(turmas: List[Turma], meses: List[str], meses_ferias: List[int]) -> str:
    """Gráfico 1: Demanda Consolidada por Projeto ao Longo do Tempo."""
    if not turmas: return ""
    print("\n--- Gerando Gráfico: Demanda Consolidada por Projeto...")
    num_meses = len(meses)
    projetos_unicos = sorted(list(set(t.projeto for t in turmas)))
    cor_map = {proj: plt.colormaps.get_cmap('tab20c')(i) for i, proj in enumerate(projetos_unicos)}

    dados_projeto_mes = {proj: [0] * num_meses for proj in projetos_unicos}
    for t in turmas:
        for m in calcular_meses_ativos(t.mes_inicio, t.duracao, meses_ferias, num_meses):
            dados_projeto_mes[t.projeto][m] += 1

    fig, ax = plt.subplots(figsize=(22, 8))
    bottom = np.zeros(num_meses)
    for proj in projetos_unicos:
        ax.bar(meses, dados_projeto_mes[proj], bottom=bottom, label=proj, color=cor_map.get(proj), edgecolor='black',
               linewidth=0.5)
        bottom += np.array(dados_projeto_mes[proj])

    for m_idx in meses_ferias: ax.axvspan(m_idx - 0.5, m_idx + 0.5, color='gray', alpha=0.2, zorder=0,
                                          label='Férias' if m_idx == meses_ferias[0] else '')

    ax.set_ylabel('Número de Turmas Ativas', fontsize=12, fontweight='bold')
    ax.set_xlabel('Meses', fontsize=12, fontweight='bold')
    ax.set_title('Demanda Consolidada por Projeto ao Longo do Tempo', fontsize=16, fontweight='bold', pad=20)
    ax.legend(title='Projetos', loc='upper left')
    plt.xticks(rotation=45, ha="right")
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    filepath = 'grafico_1_demanda_projeto_tempo.png'
    plt.savefig(filepath, dpi=300)
    plt.close(fig)
    return filepath


def gerar_grafico_turmas_instrutor_tipologia_projeto(atribuicoes: List[Dict]) -> str:
    """Gráfico 2: Alocação Detalhada - Instrutor vs. Projeto."""
    if not atribuicoes: return ""
    print("--- Gerando Gráfico: Alocação Detalhada por Instrutor...")

    dados_consolidados = defaultdict(lambda: defaultdict(int))
    instrutores_por_habilidade = defaultdict(list)
    for atr in atribuicoes:
        instrutor_id = atr['instrutor'].id
        projeto = atr['turma'].projeto
        habilidade = atr['instrutor'].habilidade
        dados_consolidados[instrutor_id][projeto] += 1
        if instrutor_id not in instrutores_por_habilidade[habilidade]:
            instrutores_por_habilidade[habilidade].append(instrutor_id)

    projetos_unicos = sorted(list(set(p for inst_data in dados_consolidados.values() for p in inst_data.keys())))
    habilidades = sorted(instrutores_por_habilidade.keys())
    fig, axes = plt.subplots(len(habilidades), 1, figsize=(20, 8 * len(habilidades)), squeeze=False)
    cor_map = plt.colormaps.get_cmap('Pastel1')

    for ax_idx, habilidade in enumerate(habilidades):
        ax = axes[ax_idx, 0]
        instrutores_hab = sorted(instrutores_por_habilidade[habilidade], key=lambda x: int(x.split('_')[-1]))
        if not instrutores_hab: continue

        df = pd.DataFrame(0, index=instrutores_hab, columns=projetos_unicos)
        for inst in instrutores_hab:
            for proj, count in dados_consolidados[inst].items():
                df.loc[inst, proj] = count

        df.plot(kind='bar', stacked=True, ax=ax, colormap=cor_map, edgecolor='black')

        ax.set_ylabel('Número de Turmas', fontsize=11, fontweight='bold')
        ax.set_xlabel(None)
        ax.set_title(f'Alocação de Turmas por Instrutor - {habilidade}', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.legend(title='Projetos', bbox_to_anchor=(1.01, 1), loc='upper left')
        ax.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    filepath = 'grafico_2_alocacao_detalhada.png'
    plt.savefig(filepath, dpi=300)
    plt.close(fig)
    return filepath


def gerar_grafico_demanda_prog_rob(turmas: List[Turma], meses: List[str], meses_ferias: List[int]) -> Tuple[
    str, pd.DataFrame]:
    """Gráfico 3: Demanda Mensal por Habilidade (PROG vs ROB)."""
    if not turmas: return "", pd.DataFrame()
    print("--- Gerando Gráfico: Demanda Mensal por Habilidade...")
    num_meses = len(meses)
    demanda_prog, demanda_rob = [0] * num_meses, [0] * num_meses

    for t in turmas:
        for m in calcular_meses_ativos(t.mes_inicio, t.duracao, meses_ferias, num_meses):
            if t.habilidade == 'PROG':
                demanda_prog[m] += 1
            else:
                demanda_rob[m] += 1

    serie_temporal = pd.DataFrame({'Mês': meses, 'Programação': demanda_prog, 'Robótica': demanda_rob})
    serie_temporal['Total'] = serie_temporal['Programação'] + serie_temporal['Robótica']

    fig, ax = plt.subplots(figsize=(20, 7))
    x = np.arange(num_meses)
    ax.bar(x - 0.2, demanda_prog, 0.4, label='Programação (PROG)', color='steelblue', edgecolor='black')
    ax.bar(x + 0.2, demanda_rob, 0.4, label='Robótica (ROB)', color='coral', edgecolor='black')

    for m_idx in meses_ferias: ax.axvspan(m_idx - 0.5, m_idx + 0.5, color='gray', alpha=0.2, zorder=0)

    ax.set_ylabel('Número de Turmas Ativas', fontsize=12, fontweight='bold')
    ax.set_title('Demanda Mensal por Habilidade (Programação vs. Robótica)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(meses, rotation=45, ha="right")
    ax.legend(fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    filepath = 'grafico_3_demanda_habilidade.png'
    plt.savefig(filepath, dpi=300)
    plt.close(fig)
    return filepath, serie_temporal


def gerar_grafico_carga_por_instrutor(atribuicoes: List[Dict]) -> str:
    """Gráfico 4: Carga Total e Balanceamento por Instrutor (Spread)."""
    if not atribuicoes: return ""
    print("--- Gerando Gráfico: Carga Total e Balanceamento (Spread)...")
    carga = defaultdict(int)
    for atr in atribuicoes: carga[atr['instrutor'].id] += 1

    if not carga: return ""
    cargas = sorted(carga.items(), key=lambda x: (x[0].split('_')[0], int(x[0].split('_')[-1])))
    instrutores, valores = zip(*cargas)

    fig, ax = plt.subplots(figsize=(20, 8))
    cores = ['steelblue' if 'PROG' in i else 'coral' for i in instrutores]
    barras = ax.bar(instrutores, valores, color=cores, edgecolor='black')

    spread = max(valores) - min(valores)
    media = np.mean(valores)
    ax.axhline(y=media, color='green', linestyle='--', label=f'Carga Média: {media:.1f}')

    ax.set_ylabel('Número Total de Turmas Alocadas', fontsize=12, fontweight='bold')
    ax.set_title(f'Carga Total por Instrutor e Balanceamento (Spread = {spread})', fontsize=16, fontweight='bold',
                 pad=20)
    ax.legend()
    plt.xticks(rotation=90, fontsize=9)
    ax.grid(axis='y', linestyle='--', alpha=0.3)

    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='steelblue', edgecolor='black', label='Programação'),
                       Patch(facecolor='coral', edgecolor='black', label='Robótica')]
    ax.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()
    filepath = 'grafico_4_balanceamento_spread.png'
    plt.savefig(filepath, dpi=300)
    plt.close(fig)
    return filepath