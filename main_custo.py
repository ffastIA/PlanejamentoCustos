# ARQUIVO: main.py

import sys
import os
from datetime import datetime

# Importações dos módulos
from otimizador.io import user_input, config_manager
from otimizador.utils import (gerar_lista_meses, converter_projetos_para_modelo,
                              renumerar_instrutores_ativos, analisar_distribuicao_instrutores_por_projeto,
                              calcular_fluxo_caixa_por_projeto)
from otimizador.core import stage_1, stage_2
from otimizador.reporting import plotting, spreadsheets, pdf_generator


def main():
    """
    Função principal que executa todo o pipeline de otimização.
    """
    print("\n" + "=" * 80)
    print("SISTEMA DE OTIMIZAÇÃO DE ALOCAÇÃO DE INSTRUTORES v2.7 (Fluxo de Caixa)")
    print("=" * 80)

    try:
        # 1. Gerenciamento e Obtenção de Configurações
        parametros, projetos_config = config_manager.menu_gerenciar_configuracoes()
        if not (parametros and projetos_config):
            parametros = user_input.obter_parametros_usuario()
            projetos_config = user_input.obter_projetos_usuario()
            salvar = input("Deseja salvar esta configuração? (S/N) [S]: ").strip().upper()
            if salvar in ('', 'S'):
                config_manager.salvar_configuracao(parametros, projetos_config)
        else:
            user_input.exibir_resumo_parametros(parametros)
            user_input.exibir_resumo_projetos(projetos_config)

        # 2. Preparação de Dados
        dt_min = min(datetime.strptime(p.data_inicio, "%d/%m/%Y") for p in projetos_config)
        dt_max = max(datetime.strptime(p.data_termino, "%d/%m/%Y") for p in projetos_config)
        meses = gerar_lista_meses(dt_min.strftime("%d/%m/%Y"), dt_max.strftime("%d/%m/%Y"))
        meses_ferias_idx = [meses.index(m) for m in parametros.meses_ferias if m in meses]

        # 3. Conversão e Otimização
        projetos_modelo = converter_projetos_para_modelo(projetos_config, meses, meses_ferias_idx, parametros)

        resultados_estagio1 = stage_1.otimizar_curva_demanda(projetos_modelo, meses, parametros)
        if not resultados_estagio1:
            print("\n[ERRO] Falha no Estágio 1. Verifique as restrições do projeto.")
            sys.exit(1)

        resultados_estagio2 = stage_2.otimizar_atribuicao_e_carga(
            resultados_estagio1['cronograma'], projetos_modelo, meses, meses_ferias_idx, parametros
        )
        if not resultados_estagio2 or resultados_estagio2["status"] == "falha":
            print("\n[ERRO] Falha no Estágio 2. Tente aumentar o spread ou o timeout.")
            sys.exit(1)

        # 4. Pós-processamento e Relatórios
        resultados_estagio2['atribuicoes'], contagem_instrutores_hab = renumerar_instrutores_ativos(
            resultados_estagio2['atribuicoes'])

        distribuicao_por_projeto = analisar_distribuicao_instrutores_por_projeto(resultados_estagio2['atribuicoes'])

        # Calcular fluxo de caixa
        fluxo_caixa = calcular_fluxo_caixa_por_projeto(
            resultados_estagio2['atribuicoes'],
            meses,
            meses_ferias_idx,
            parametros.remuneracao_instrutor
        )

        print("\n" + "=" * 80 + "\nGERANDO VISUALIZAÇÕES E RELATÓRIOS\n" + "=" * 80)

        df_consolidada_instrutor = spreadsheets.gerar_planilha_consolidada_instrutor(resultados_estagio2['atribuicoes'])
        spreadsheets.gerar_planilha_detalhada(resultados_estagio2['atribuicoes'], meses, meses_ferias_idx)
        df_fluxo_caixa = spreadsheets.gerar_planilha_fluxo_caixa(fluxo_caixa, meses)

        graficos = {
            'projeto_mes': plotting.gerar_grafico_turmas_projeto_mes(resultados_estagio2['turmas'], meses,
                                                                     meses_ferias_idx),
            'instrutor_projeto': plotting.gerar_grafico_turmas_instrutor_tipologia_projeto(
                resultados_estagio2['atribuicoes']),
            'carga_instrutor': plotting.gerar_grafico_carga_por_instrutor(resultados_estagio2['atribuicoes']),
            'fluxo_caixa': plotting.gerar_grafico_fluxo_caixa(fluxo_caixa, meses)
        }
        graficos['prog_rob'], serie_temporal_df = plotting.gerar_grafico_demanda_prog_rob(resultados_estagio2['turmas'],
                                                                                          meses, meses_ferias_idx)

        pdf_generator.gerar_relatorio_pdf(
            projetos_config,
            resultados_estagio1,
            resultados_estagio2,
            graficos,
            serie_temporal_df,
            df_consolidada_instrutor,
            contagem_instrutores_hab,
            distribuicao_por_projeto,
            df_fluxo_caixa
        )

        for path in graficos.values():
            if path and os.path.exists(path): os.remove(path)

        print("\n" + "=" * 80 + "\nPROCESSO CONCLUÍDO COM SUCESSO!\n" + "=" * 80)
        print("Arquivos gerados: Relatorio_Otimizacao_Custo.pdf e planilhas .xlsx")

    except KeyboardInterrupt:
        print("\n\n[!] Operação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()