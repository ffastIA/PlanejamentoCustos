# ARQUIVO: otimizador/core/stage_2.py

from collections import defaultdict
from typing import List, Dict, Optional
from ortools.sat.python import cp_model

from ..data_models import Projeto, ParametrosOtimizacao, Turma, Instrutor
from ..utils import calcular_meses_ativos


def otimizar_atribuicao_e_carga(cronograma_flexivel: Dict,
                                projetos: List[Projeto],
                                meses: List[str],
                                meses_ferias: List[int],
                                parametros: ParametrosOtimizacao) -> Optional[Dict]:
    """
    Aloca turmas a instrutores, minimizando o custo total de remuneração.
    """
    print("\n" + "=" * 80)
    print("ESTÁGIO 2: Alocação de Instrutores (Otimização de Custo)")
    print("=" * 80)
    print(f"Capacidade máxima por instrutor: {parametros.capacidade_max_instrutor} turmas/mês")
    print(f"Spread máximo configurado: {parametros.spread_maximo} turmas")
    remuneracao_formatada = f"{parametros.remuneracao_instrutor:,.2f}".replace(',', 'X').replace('.', ',').replace('X',
                                                                                                                   '.')
    print(f"Remuneração por instrutor/mês: R$ {remuneracao_formatada}")

    # 1. Criação de Turmas
    all_turmas = []
    turma_counter = 0
    projetos_dict = {p.nome: p for p in projetos}

    for proj_nome, cronogramas in cronograma_flexivel.items():
        proj_details = projetos_dict.get(proj_nome)
        if not proj_details:
            continue

        for crono in cronogramas:
            habilidade_str = crono.get('habilidade', 'PROG')
            habilidade = 'PROG' if habilidade_str == 'PROG' else 'ROBOTICA'

            for _ in range(crono['num_turmas']):
                turma_id = f'{proj_nome}_{habilidade[:3]}_{turma_counter}'
                all_turmas.append(
                    Turma(turma_id, proj_nome, habilidade, crono['mes_inicio'], proj_details.duracao)
                )
                turma_counter += 1

    print(f"\nTotal de turmas criadas para alocação: {len(all_turmas)}")

    # 2. Criação do Pool de Instrutores
    num_max_instrutores_flex = 80
    all_instrutores = []

    for hab in ['PROG', 'ROBOTICA']:
        for i in range(num_max_instrutores_flex):
            instrutor = Instrutor(
                id=f'{hab}_{i}',
                habilidade=hab,
                capacidade=parametros.capacidade_max_instrutor,
                laboratorio_id=None
            )
            all_instrutores.append(instrutor)

    print(f"Pool de instrutores hipotéticos: {len(all_instrutores)}\n")

    # 3. Construção do Modelo
    model = cp_model.CpModel()
    num_meses = len(meses)

    # Organizar dados
    turmas_por_habilidade = defaultdict(list)
    for t in all_turmas:
        turmas_por_habilidade[t.habilidade].append(t)

    instrutores_por_habilidade = defaultdict(list)
    for i in all_instrutores:
        instrutores_por_habilidade[i.habilidade].append(i)

    # Variáveis de atribuição
    assign = {}
    for habilidade, turmas in turmas_por_habilidade.items():
        for t in turmas:
            instrutores_hab = instrutores_por_habilidade.get(habilidade, [])
            for i in instrutores_hab:
                var_name = f'assign_{t.id[:15]}_{i.id}'
                assign[(t.id, i.id)] = model.NewBoolVar(var_name)

    # Restrição: cada turma tem exatamente um instrutor
    for t_list in turmas_por_habilidade.values():
        for t in t_list:
            opcoes = [assign[(t.id, i.id)] for i in instrutores_por_habilidade[t.habilidade]]
            model.AddExactlyOne(opcoes)

    # Variáveis de atividade mensal
    instrutor_ativo_mes = {}

    for i in all_instrutores:
        for m in range(num_meses):
            carga_mensal = []

            for t in turmas_por_habilidade[i.habilidade]:
                meses_ativos_turma = calcular_meses_ativos(t.mes_inicio, t.duracao, meses_ferias, num_meses)
                if m in meses_ativos_turma:
                    carga_mensal.append(assign[(t.id, i.id)])

            if not carga_mensal:
                continue

            ativo = model.NewBoolVar(f'ativo_{i.id}_{m}')
            instrutor_ativo_mes[(i.id, m)] = ativo

            soma_carga_mensal = sum(carga_mensal)

            # Se carga maior que zero, está ativo
            model.Add(soma_carga_mensal > 0).OnlyEnforceIf(ativo)
            # Se carga igual a zero, não está ativo
            model.Add(soma_carga_mensal == 0).OnlyEnforceIf(ativo.Not())

            # Capacidade máxima
            model.Add(soma_carga_mensal <= i.capacidade)

    # Cálculo do spread
    cargas_totais = []
    instrutores_usados_bool = []

    for i in all_instrutores:
        usado = model.NewBoolVar(f'usado_{i.id}')
        carga_total = model.NewIntVar(0, 300, f'carga_{i.id}')

        turmas_do_instrutor = []
        for t in turmas_por_habilidade[i.habilidade]:
            if assign.get((t.id, i.id)) is not None:
                turmas_do_instrutor.append(assign[(t.id, i.id)])

        if turmas_do_instrutor:
            model.Add(sum(turmas_do_instrutor) == carga_total)
            model.Add(carga_total > 0).OnlyEnforceIf(usado)
            model.Add(carga_total == 0).OnlyEnforceIf(usado.Not())
            cargas_totais.append(carga_total)
            instrutores_usados_bool.append(usado)

    spread_var = model.NewIntVar(0, 300, 'spread_obj')

    if cargas_totais:
        max_carga = model.NewIntVar(0, 300, 'max_carga')
        min_carga_usada = model.NewIntVar(0, 300, 'min_carga_usada')
        model.AddMaxEquality(max_carga, cargas_totais)

        cargas_ajustadas = []
        for idx, carga in enumerate(cargas_totais):
            carga_ajustada = model.NewIntVar(0, 300, f'carga_ajustada_{idx}')
            model.Add(carga_ajustada == carga).OnlyEnforceIf(instrutores_usados_bool[idx])
            model.Add(carga_ajustada == max_carga).OnlyEnforceIf(instrutores_usados_bool[idx].Not())
            cargas_ajustadas.append(carga_ajustada)

        model.AddMinEquality(min_carga_usada, cargas_ajustadas)
        model.Add(spread_var == max_carga - min_carga_usada)
        model.Add(spread_var <= parametros.spread_maximo)
    else:
        model.Add(spread_var == 0)

    # Função objetivo: minimizar custo
    custo_total_var = model.NewIntVar(0, 1000000000, 'custo_total')
    remuneracao = int(parametros.remuneracao_instrutor)

    total_ativacoes = sum(instrutor_ativo_mes.values())
    model.Add(custo_total_var == remuneracao * total_ativacoes)

    model.Minimize(custo_total_var)

    # 4. Resolução
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(parametros.timeout_segundos)
    print("Resolvendo alocação para minimizar custo...")
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"\n[✓] SUCESSO! Status: {solver.StatusName(status)}")

        atribuicoes = []
        for t in all_turmas:
            for i in instrutores_por_habilidade[t.habilidade]:
                if solver.Value(assign.get((t.id, i.id), 0)):
                    atribuicoes.append({'turma': t, 'instrutor': i})
                    break

        carga_por_instrutor = defaultdict(int)
        for atr in atribuicoes:
            carga_por_instrutor[atr['instrutor'].id] += 1

        cargas_ativas_vals = list(carga_por_instrutor.values()) if carga_por_instrutor else [0]
        spread_real = max(cargas_ativas_vals) - min(cargas_ativas_vals) if cargas_ativas_vals else 0

        custo_final = solver.Value(custo_total_var)
        custo_formatado = f"{custo_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        print(f"Custo total previsto: R$ {custo_formatado}")

        return {
            "status": "sucesso",
            "atribuicoes": atribuicoes,
            "custo_total_previsto": custo_final,
            "total_instrutores_flex": len(cargas_ativas_vals),
            "carga_por_instrutor": dict(carga_por_instrutor),
            "spread_carga": spread_real,
            "turmas": all_turmas,
            "instrutores": all_instrutores,
            "capacidade_max": parametros.capacidade_max_instrutor
        }
    else:
        print(f"\n[✗] FALHA na Alocação: {solver.StatusName(status)}")
        print("Sugestões: Aumente o 'Spread máximo', a 'Capacidade por Instrutor' ou o 'Timeout do solver'.")
        return {"status": "falha"}