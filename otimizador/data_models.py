# ARQUIVO: otimizador/data_models.py (CORRIGIDO)

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class ParametrosOtimizacao:
    """
    Parâmetros globais que governam o comportamento da otimização.
    """
    capacidade_max_instrutor: int
    spread_maximo: int
    timeout_segundos: int
    meses_ferias: List[str] = field(default_factory=lambda: ["Jul/26", "Dez/26"])

    remuneracao_instrutor: float = 5000.0

    def __post_init__(self):
        """Validação dos dados após a inicialização."""
        if not isinstance(self.capacidade_max_instrutor, int) or self.capacidade_max_instrutor <= 0:
            raise ValueError("Capacidade máxima do instrutor deve ser um inteiro positivo.")
        if not isinstance(self.spread_maximo, int) or self.spread_maximo < 0:
            raise ValueError("Spread máximo deve ser um inteiro não-negativo.")
        if not isinstance(self.timeout_segundos, int) or self.timeout_segundos <= 0:
            raise ValueError("Timeout do solver deve ser um inteiro positivo.")

        if not isinstance(self.remuneracao_instrutor, (int, float)) or self.remuneracao_instrutor <= 0:
            raise ValueError("A remuneração do instrutor deve ser um valor numérico positivo.")


@dataclass
class ConfiguracaoProjeto:
    """
    Configuração completa de um projeto educacional, conforme inserido pelo usuário ou carregado.
    """
    nome: str
    data_inicio: str
    data_termino: str
    num_turmas: int
    duracao_curso: int
    ondas: int = 1
    percentual_prog: float = 60.0
    turmas_min_por_mes: int = 1
    mes_inicio_idx: int = field(init=False, repr=False, default=0)
    mes_termino_idx: int = field(init=False, repr=False, default=0)

    @property
    def percentual_rob(self) -> float:
        """Calcula o percentual de turmas de robótica."""
        return 100.0 - self.percentual_prog

    def __post_init__(self):
        self._validar_dados()

    def _validar_dados(self):
        if not self.nome or not isinstance(self.nome, str):
            raise ValueError("Nome do projeto não pode ser vazio.")
        if not isinstance(self.num_turmas, int) or self.num_turmas <= 0:
            raise ValueError(f"Número de turmas inválido para {self.nome}")
        if not isinstance(self.duracao_curso, int) or self.duracao_curso <= 0:
            raise ValueError(f"Duração do curso inválida para {self.nome}")
        if not isinstance(self.ondas, int) or self.ondas <= 0:
            raise ValueError(f"Número de ondas inválido para {self.nome}")
        if not (0 <= self.percentual_prog <= 100):
            raise ValueError(f"Percentual de programação inválido para {self.nome}")
        try:
            datetime.strptime(self.data_inicio, "%d/%m/%Y")
            datetime.strptime(self.data_termino, "%d/%m/%Y")
        except ValueError:
            raise ValueError(f"Formato de data inválido para {self.nome}. Use DD/MM/YYYY.")


@dataclass(frozen=True)
class Projeto:
    """
    Representação simplificada de um projeto (ou uma onda) para o modelo de otimização.
    """
    nome: str
    prog: int
    rob: int
    duracao: int
    inicio_min: int
    inicio_max: int
    deadline: int


@dataclass(frozen=True)
class Turma:
    id: str
    projeto: str
    habilidade: str
    mes_inicio: int
    duracao: int


@dataclass(frozen=True)
class Instrutor:
    id: str
    habilidade: str
    capacidade: int
    laboratorio_id: int | None