# ARQUIVO: otimizador/reporting/spreadsheets.py

import pandas as pd
from collections import defaultdict
from typing import List, Dict


def gerar_planilha_consolidada_instrutor(atribuicoes: List[Dict]) -> pd.DataFrame:
    """Gera planilha consolidada de turmas por instrutor e projeto."""
    dados = defaultdict(lambda: defaultdict(int))

    for atr in atribuicoes:
        instrutor_id = atr['instrutor'].id
        habilidade = atr['instrutor'].habilidade
        projeto = atr['turma'].projeto
        dados[instrutor_id]['Habilidade'] = habilidade
        dados[instrutor_id][projeto] = dados[instrutor_id].get(projeto, 0) + 1

    linhas = []
    for instrutor_id, proj_dict in sorted(dados.items(), key=lambda x: (x[1]['Habilidade'], int(x[0].split('_')[1]))):
        linha = {'Instrutor': instrutor_id, 'Habilidade': proj_dict.pop('Habilidade')}
        linha.update(proj_dict)
        linha['Total'] = sum(v for k, v in proj_dict.items() if k != 'Habilidade')
        linhas.append(linha)

    df = pd.DataFrame(linhas).fillna(0)
    filename = 'Planilha_Consolidada_Instrutor_Projeto.xlsx'
    df.to_excel(filename, index=False, sheet_name='Instrutor x Projeto')
    print(f"[✓] Planilha consolidada gerada: {filename}")
    return df


def gerar_planilha_detalhada(atribuicoes: List[Dict], meses: List[str], meses_ferias: List[int]):
    """Gera planilha detalhada com todas as atribuições."""
    from ..utils import calcular_meses_ativos

    linhas = []
    for atr in atribuicoes:
        turma = atr['turma']
        instrutor = atr['instrutor']
        meses_ativos = calcular_meses_ativos(turma.mes_inicio, turma.duracao, meses_ferias, len(meses))
        meses_str = ', '.join([meses[m] for m in meses_ativos])

        linhas.append({
            'Turma_ID': turma.id,
            'Projeto': turma.projeto,
            'Habilidade': turma.habilidade,
            'Instrutor': instrutor.id,
            'Mês_Início': meses[turma.mes_inicio],
            'Duração': turma.duracao,
            'Meses_Ativos': meses_str
        })

    df = pd.DataFrame(linhas)
    filename = 'Planilha_Detalhada_Atribuicoes.xlsx'
    df.to_excel(filename, index=False, sheet_name='Atribuições Detalhadas')
    print(f"[✓] Planilha detalhada gerada: {filename}")


def gerar_planilha_fluxo_caixa(fluxo_caixa: Dict[str, Dict[str, float]],
                               meses: List[str]) -> pd.DataFrame:
    """
    Gera planilha com fluxo de caixa mensal por projeto.
    """
    print("\n--- Gerando Planilha de Fluxo de Caixa ---")

    # Criar estrutura de dados
    dados = []
    projetos = sorted(fluxo_caixa.keys())

    for projeto in projetos:
        linha = {'Projeto': projeto}
        custo_total_projeto = 0.0

        for mes in meses:
            custo = fluxo_caixa[projeto].get(mes, 0.0)
            linha[mes] = custo
            custo_total_projeto += custo

        linha['TOTAL'] = custo_total_projeto
        dados.append(linha)

    # Adicionar linha de total geral
    linha_total = {'Projeto': 'TOTAL GERAL'}
    for mes in meses:
        total_mes = sum(fluxo_caixa[proj].get(mes, 0.0) for proj in projetos)
        linha_total[mes] = total_mes
    linha_total['TOTAL'] = sum(linha['TOTAL'] for linha in dados)
    dados.append(linha_total)

    df = pd.DataFrame(dados)

    # Salvar planilha
    filename = 'Planilha_Fluxo_Caixa.xlsx'
    df.to_excel(filename, index=False, sheet_name='Fluxo de Caixa')
    print(f"[✓] Planilha de fluxo de caixa gerada: {filename}")

    return df